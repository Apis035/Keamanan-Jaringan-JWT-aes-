
import os
import uuid
import tempfile

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.database import db
from app.models.file import File
from app.encryption.key_manager import generate_dek, wrap_dek, unwrap_dek
from app.encryption.chunked import encrypt_file_chunked, decrypt_file_chunked

from flask import send_file

files_bp = Blueprint("files", __name__, url_prefix="/api/files")


@files_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    uploaded_file = request.files.get("file")

    if uploaded_file is None:
        return jsonify({
            "status": "error",
            "message": "File belum dipilih."
        }), 400

    if not uploaded_file.filename:
        return jsonify({
            "status": "error",
            "message": "Nama file tidak valid."
        }), 400

    original_name = secure_filename(uploaded_file.filename)

    if not original_name:
        return jsonify({
            "status": "error",
            "message": "Nama file tidak valid."
        }), 400

    if len(original_name) > 255:
        return jsonify({
            "status": "error",
            "message": "Nama file terlalu panjang."
        }), 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    max_size = current_app.config["MAX_CONTENT_LENGTH"]

    os.makedirs(upload_folder, exist_ok=True)

    # Nama penyimpanan dibuat acak, bukan memakai nama asli.
    storage_name = f"{uuid.uuid4().hex}.svenc"
    encrypted_path = os.path.join(upload_folder, storage_name)

    temp_fd = None
    temp_path = None
    encrypted_created = False

    try:
        # Simpan sementara file asli di folder temporary sistem.
        temp_fd, temp_path = tempfile.mkstemp(
            prefix="securevault-",
            suffix=".tmp"
        )

        file_size = 0

        with os.fdopen(temp_fd, "wb") as temp_file:
            temp_fd = None

            while True:
                chunk = uploaded_file.stream.read(1024 * 1024)

                if not chunk:
                    break

                file_size += len(chunk)

                if file_size > max_size:
                    return jsonify({
                        "status": "error",
                        "message": "Ukuran file melebihi batas 100 MB."
                    }), 413

                temp_file.write(chunk)

        if file_size == 0:
            return jsonify({
                "status": "error",
                "message": "File kosong tidak dapat diunggah."
            }), 400

        # Generate DEK khusus untuk file ini.
        dek = generate_dek()

        # Bungkus DEK menggunakan KEK.
        encrypted_dek = wrap_dek(dek)

        # Enkripsi file menggunakan AES-256-GCM chunked.
        encrypt_file_chunked(
            temp_path,
            encrypted_path,
            dek
        )

        encrypted_created = True

        # Simpan metadata ke database.
        new_file = File(
            user_id=int(get_jwt_identity()),
            original_name=original_name,
            storage_name=storage_name,
            mime_type=uploaded_file.mimetype,
            file_size=file_size,
            storage_format="chunked-v1",
            nonce=None,
            auth_tag=None,
            encrypted_dek=encrypted_dek
        )

        db.session.add(new_file)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "File berhasil dienkripsi dan diunggah.",
            "data": {
                "id": new_file.id,
                "original_name": new_file.original_name,
                "file_size": new_file.file_size,
                "storage_format": new_file.storage_format,
                "created_at": new_file.created_at.isoformat()
            }
        }), 201

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Upload file gagal")

        return jsonify({
            "status": "error",
            "message": "Terjadi kesalahan saat mengunggah file."
        }), 500

    finally:
        if temp_fd is not None:
            os.close(temp_fd)

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        # Jika penyimpanan database gagal, hapus ciphertext
        # agar tidak meninggalkan file tanpa metadata.
        if encrypted_created and os.path.exists(encrypted_path):
            if not File.query.filter_by(
                storage_name=storage_name
            ).first():
                os.remove(encrypted_path)

@files_bp.route("", methods=["GET"])
@jwt_required()
def get_files():
    user_id = int(get_jwt_identity())

    files = (
        File.query
        .filter_by(user_id=user_id)
        .order_by(File.created_at.desc())
        .all()
    )

    file_list = []

    for file in files:
        file_list.append({
            "id": file.id,
            "original_name": file.original_name,
            "mime_type": file.mime_type,
            "file_size": file.file_size,
            "storage_format": file.storage_format,
            "created_at": file.created_at.isoformat()
        })

    return jsonify({
        "status": "success",
        "message": "Daftar file berhasil diambil.",
        "data": file_list
    }), 200

@files_bp.route("/<int:file_id>/download", methods=["GET"])
@jwt_required()
def download_file(file_id):
    user_id = int(get_jwt_identity())

    # Cari file berdasarkan ID dan pemiliknya
    file_record = File.query.filter_by(
        id=file_id,
        user_id=user_id
    ).first()

    if not file_record:
        return jsonify({
            "status": "error",
            "message": "File tidak ditemukan."
        }), 404

    upload_folder = current_app.config["UPLOAD_FOLDER"]

    # Pastikan lokasi file tetap berada dalam folder penyimpanan
    encrypted_path = os.path.realpath(
        os.path.join(upload_folder, file_record.storage_name)
    )

    if os.path.commonpath([
        os.path.realpath(upload_folder),
        encrypted_path
    ]) != os.path.realpath(upload_folder):
        return jsonify({
            "status": "error",
            "message": "Lokasi file tidak valid."
        }), 400

    if not os.path.isfile(encrypted_path):
        return jsonify({
            "status": "error",
            "message": "File fisik tidak ditemukan."
        }), 404

    temp_path = None

    try:
        # Buka DEK menggunakan KEK
        dek = unwrap_dek(file_record.encrypted_dek)

        # Siapkan file sementara untuk hasil dekripsi
        fd, temp_path = tempfile.mkstemp(
            prefix="securevault-download-",
            suffix=".tmp",
            dir=upload_folder
        )
        os.close(fd)

        # Dekripsi file dengan AES-256-GCM chunked
        decrypt_file_chunked(
            encrypted_path,
            temp_path,
            dek
        )

        # Kirim file asli kepada pengguna
        response = send_file(
            temp_path,
            as_attachment=True,
            download_name=file_record.original_name,
            mimetype=file_record.mime_type or "application/octet-stream"
        )

        # Hapus file sementara setelah respons selesai
        response.call_on_close(
            lambda: os.path.exists(temp_path) and os.remove(temp_path)
        )

        return response

    except Exception:
        current_app.logger.exception("Proses download/dekripsi gagal")

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        return jsonify({
            "status": "error",
            "message": "File gagal didekripsi atau tidak dapat diunduh."
        }), 500


@files_bp.route("/<int:file_id>", methods=["DELETE"])
@jwt_required()
def delete_file(file_id):
    user_id = int(get_jwt_identity())

    # Cari file berdasarkan ID dan pemiliknya
    file_record = File.query.filter_by(
        id=file_id,
        user_id=user_id
    ).first()

    if not file_record:
        return jsonify({
            "status": "error",
            "message": "File tidak ditemukan."
        }), 404

    upload_folder = os.path.realpath(
        current_app.config["UPLOAD_FOLDER"]
    )

    encrypted_path = os.path.realpath(
        os.path.join(upload_folder, file_record.storage_name)
    )

    # Pastikan file berada di dalam folder uploads
    if os.path.commonpath([
        upload_folder,
        encrypted_path
    ]) != upload_folder:
        return jsonify({
            "status": "error",
            "message": "Lokasi file tidak valid."
        }), 400

    # Nama sementara untuk proses penghapusan
    tombstone_path = os.path.join(
        upload_folder,
        f".{uuid.uuid4().hex}.deleting"
    )

    moved_file = False

    try:
        # Pindahkan ciphertext sementara agar bisa dipulihkan
        # jika transaksi database gagal.
        if os.path.exists(encrypted_path):
            os.replace(encrypted_path, tombstone_path)
            moved_file = True

        # Hapus metadata, termasuk encrypted_dek
        db.session.delete(file_record)
        db.session.commit()

    except Exception:
        db.session.rollback()

        # Kembalikan ciphertext jika transaksi gagal
        if moved_file and os.path.exists(tombstone_path):
            os.replace(tombstone_path, encrypted_path)

        current_app.logger.exception("Penghapusan file gagal")

        return jsonify({
            "status": "error",
            "message": "File gagal dihapus."
        }), 500

    # Hapus ciphertext secara permanen setelah database berhasil
    if moved_file:
        try:
            os.remove(tombstone_path)

        except OSError:
            current_app.logger.exception(
                "Metadata terhapus, tetapi ciphertext masih tersisa"
            )

            return jsonify({
                "status": "error",
                "message": "Metadata terhapus, tetapi penghapusan fisik belum selesai. Perlu pembersihan manual."
            }), 500

    return jsonify({
        "status": "success",
        "message": "File berhasil dihapus secara permanen.",
        "data": {
            "id": file_id
        }
    }), 200
