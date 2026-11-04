
from app.database import db
from datetime import datetime, timezone


class File(db.Model):
    __tablename__ = "files"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    original_name = db.Column(db.String(255), nullable=False)
    storage_name = db.Column(db.String(255), unique=True, nullable=False)
    mime_type = db.Column(db.String(150))
    file_size = db.Column(db.BigInteger, nullable=False)

    storage_format = db.Column(
        db.String(30),
        nullable=False,
        default="chunked-v1"
    )

    nonce = db.Column(db.LargeBinary(12), nullable=True)
    auth_tag = db.Column(db.LargeBinary(16), nullable=True)
    encrypted_dek = db.Column(db.LargeBinary, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
