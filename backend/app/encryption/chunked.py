
import os
import struct
import secrets
import tempfile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# Format file terenkripsi SecureVault
MAGIC = b"SVCHNK01"

# Header:
# MAGIC (8 byte)
# File size (8 byte)
# Chunk size (4 byte)
# Nonce prefix (4 byte)
# Jumlah chunk (8 byte)
HEADER_FORMAT = ">8sQI4sQ"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1 MB
MAX_CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB


def make_nonce(prefix, index):
    """
    Membuat nonce 12 byte yang unik untuk setiap chunk.
    """
    return prefix + index.to_bytes(8, "big")


def make_aad(header, index):
    """
    Mengikat chunk dengan header dan nomor urutnya.
    """
    return header + index.to_bytes(8, "big")


def encrypt_file_chunked(
    input_path,
    output_path,
    dek,
    chunk_size=DEFAULT_CHUNK_SIZE
):
    """
    Mengenkripsi file langsung dari disk secara bertahap.
    """

    if len(dek) != 32:
        raise ValueError("DEK harus berukuran 32 byte")

    if not 1 <= chunk_size <= MAX_CHUNK_SIZE:
        raise ValueError("Ukuran chunk tidak valid")

    if os.path.abspath(input_path) == os.path.abspath(output_path):
        raise ValueError("File sumber dan tujuan harus berbeda")

    file_size = os.path.getsize(input_path)

    chunk_count = (
        file_size + chunk_size - 1
    ) // chunk_size

    # Prefix acak 4 byte.
    # Nomor chunk menjadi 8 byte terakhir nonce.
    nonce_prefix = secrets.token_bytes(4)

    header = struct.pack(
        HEADER_FORMAT,
        MAGIC,
        file_size,
        chunk_size,
        nonce_prefix,
        chunk_count
    )

    aesgcm = AESGCM(dek)

    output_dir = os.path.dirname(
        os.path.abspath(output_path)
    )

    temp_path = None

    try:
        fd, temp_path = tempfile.mkstemp(
            prefix=".securevault-",
            suffix=".tmp",
            dir=output_dir
        )

        with os.fdopen(fd, "wb") as output_file:
            with open(input_path, "rb") as input_file:

                output_file.write(header)

                for index in range(chunk_count):

                    expected_size = min(
                        chunk_size,
                        file_size - index * chunk_size
                    )

                    plaintext = input_file.read(expected_size)

                    if len(plaintext) != expected_size:
                        raise ValueError(
                            "File sumber berubah atau terpotong"
                        )

                    nonce = make_nonce(
                        nonce_prefix,
                        index
                    )

                    aad = make_aad(header, index)

                    encrypted_chunk = aesgcm.encrypt(
                        nonce,
                        plaintext,
                        aad
                    )

                    output_file.write(encrypted_chunk)

                # Pastikan file sumber tidak bertambah
                # selama proses enkripsi.
                if input_file.read(1):
                    raise ValueError(
                        "Ukuran file sumber berubah"
                    )

                # Manifest authentication.
                # Menggunakan nonce berikutnya setelah chunk terakhir.
                manifest_nonce = make_nonce(
                    nonce_prefix,
                    chunk_count
                )

                manifest_tag = aesgcm.encrypt(
                    manifest_nonce,
                    b"",
                    b"SV-MANIFEST-v1" + header
                )

                output_file.write(manifest_tag)

        os.replace(temp_path, output_path)
        temp_path = None

        return {
            "file_size": file_size,
            "chunk_size": chunk_size,
            "chunk_count": chunk_count
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def decrypt_file_chunked(
    input_path,
    output_path,
    dek
):
    """
    Mendekripsi file chunked secara bertahap.

    Hasil plaintext baru dipublikasikan setelah
    seluruh chunk dan manifest berhasil diverifikasi.
    """

    if len(dek) != 32:
        raise ValueError("DEK harus berukuran 32 byte")

    if os.path.abspath(input_path) == os.path.abspath(output_path):
        raise ValueError("File sumber dan tujuan harus berbeda")

    aesgcm = AESGCM(dek)

    output_dir = os.path.dirname(
        os.path.abspath(output_path)
    )

    temp_path = None

    try:
        with open(input_path, "rb") as input_file:

            header = input_file.read(HEADER_SIZE)

            if len(header) != HEADER_SIZE:
                raise ValueError("Header file tidak lengkap")

            (
                magic,
                file_size,
                chunk_size,
                nonce_prefix,
                chunk_count
            ) = struct.unpack(
                HEADER_FORMAT,
                header
            )

            if magic != MAGIC:
                raise ValueError("Format file tidak dikenali")

            if not 1 <= chunk_size <= MAX_CHUNK_SIZE:
                raise ValueError("Ukuran chunk tidak valid")

            expected_count = (
                file_size + chunk_size - 1
            ) // chunk_size

            if chunk_count != expected_count:
                raise ValueError("Jumlah chunk tidak valid")

            fd, temp_path = tempfile.mkstemp(
                prefix=".securevault-",
                suffix=".tmp",
                dir=output_dir
            )

            total_written = 0

            with os.fdopen(fd, "wb") as output_file:

                for index in range(chunk_count):

                    plaintext_size = min(
                        chunk_size,
                        file_size - total_written
                    )

                    encrypted_size = plaintext_size + 16

                    encrypted_chunk = input_file.read(
                        encrypted_size
                    )

                    if len(encrypted_chunk) != encrypted_size:
                        raise ValueError(
                            "Chunk tidak lengkap"
                        )

                    nonce = make_nonce(
                        nonce_prefix,
                        index
                    )

                    aad = make_aad(header, index)

                    plaintext = aesgcm.decrypt(
                        nonce,
                        encrypted_chunk,
                        aad
                    )

                    output_file.write(plaintext)

                    total_written += len(plaintext)

                # Verifikasi manifest untuk mendeteksi
                # pemotongan atau pengubahan struktur file.
                manifest_tag = input_file.read(16)

                if len(manifest_tag) != 16:
                    raise ValueError("Manifest tidak lengkap")

                if input_file.read(1):
                    raise ValueError("Ada data tambahan pada file")

                manifest_nonce = make_nonce(
                    nonce_prefix,
                    chunk_count
                )

                aesgcm.decrypt(
                    manifest_nonce,
                    manifest_tag,
                    b"SV-MANIFEST-v1" + header
                )

                if total_written != file_size:
                    raise ValueError("Ukuran hasil dekripsi tidak cocok")

        os.replace(temp_path, output_path)
        temp_path = None

        return {
            "file_size": total_written,
            "chunk_count": chunk_count
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

