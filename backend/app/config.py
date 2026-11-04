
import os
from dotenv import load_dotenv
from sqlalchemy.engine import URL

# Menentukan lokasi folder backend
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

# Membaca file .env dari folder backend
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH, override=True)


class Config:
    # Konfigurasi JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_ACCESS_TOKEN_EXPIRES = 1800

    # Konfigurasi database MySQL
    SQLALCHEMY_DATABASE_URI = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        database=os.getenv("DB_NAME"),
        query={"charset": "utf8mb4"}
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Konfigurasi penyimpanan file
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    # Batas maksimal upload: 100 MB
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
