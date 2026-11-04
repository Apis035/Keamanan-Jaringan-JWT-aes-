
from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from sqlalchemy.exc import IntegrityError

from app.database import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

password_hasher = PasswordHasher()


# =========================
# REGISTER
# =========================
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validasi input
    if not name or not email or not password:
        return {
            "status": "error",
            "message": "Nama, email, dan password wajib diisi."
        }, 400

    if len(password) < 8:
        return {
            "status": "error",
            "message": "Password minimal 8 karakter."
        }, 400

    if len(name) > 100 or len(email) > 150:
        return {
            "status": "error",
            "message": "Nama atau email terlalu panjang."
        }, 400

    # Hash password dengan Argon2id
    password_hash = password_hasher.hash(password)

    new_user = User(
        name=name,
        email=email,
        password_hash=password_hash
    )

    try:
        db.session.add(new_user)
        db.session.commit()

        return {
            "status": "success",
            "message": "Registrasi berhasil!",
            "data": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email
            }
        }, 201

    except IntegrityError:
        db.session.rollback()

        return {
            "status": "error",
            "message": "Email sudah terdaftar."
        }, 409

    except Exception:
        db.session.rollback()
        raise


# =========================
# LOGIN
# =========================
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return {
            "status": "error",
            "message": "Email dan password wajib diisi."
        }, 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return {
            "status": "error",
            "message": "Email atau password salah."
        }, 401

    try:
        password_hasher.verify(user.password_hash, password)

    except (VerifyMismatchError, VerificationError):
        return {
            "status": "error",
            "message": "Email atau password salah."
        }, 401

    # Buat JWT access token
    access_token = create_access_token(
        identity=str(user.id)
    )

    return {
        "status": "success",
        "message": "Login berhasil!",
        "access_token": access_token,
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }, 200


# =========================
# CEK USER LOGIN
# =========================
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()

    user = db.session.get(User, int(user_id))

    if not user:
        return {
            "status": "error",
            "message": "Pengguna tidak ditemukan."
        }, 404

    return {
        "status": "success",
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }, 200
