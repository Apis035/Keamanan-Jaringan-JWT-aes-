
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy import text

from app.config import Config
from app.database import db
from app.models import User, File, RefreshToken
from app.routes import auth_bp

from app.routes.auth import auth_bp
from app.routes.files import files_bp

def create_app():
    # Membuat instance Flask
    app = Flask(__name__)

    # Memuat konfigurasi
    app.config.from_object(Config)

    # Memeriksa konfigurasi JWT
    if not app.config.get("JWT_SECRET_KEY"):
        raise RuntimeError("JWT_SECRET_KEY belum diatur di .env")

    # Mengaktifkan CORS
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["http://localhost:5173"]
            }
        }
    )

    # Inisialisasi database
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Inisialisasi JWT
    jwt = JWTManager(app)

    # Registrasi route autentikasi
    app.register_blueprint(auth_bp)

    # Registrasi route file
    app.register_blueprint(files_bp)

    # Tes backend
    @app.route("/api/health", methods=["GET"])
    def health():
        return {
            "status": "success",
            "message": "SecureVault backend berjalan!"
        }, 200

    # Tes database
    @app.route("/api/health/db", methods=["GET"])
    def database_health():
        try:
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))

            return {
                "status": "success",
                "message": "Database berhasil terhubung!"
            }, 200

        except Exception:
            app.logger.exception("Database connection error")

            return {
                "status": "error",
                "message": "Database belum dapat dihubungkan."
            }, 500

    return app
