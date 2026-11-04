
import os
import base64
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def get_kek():
    """
    Mengambil KEK dari environment variable.
    KEK harus berukuran 32 byte.
    """
    kek_base64 = os.getenv("FILE_KEK_BASE64")

    if not kek_base64:
        raise RuntimeError("FILE_KEK_BASE64 belum diatur di .env")

    try:
        kek = base64.b64decode(kek_base64, validate=True)
    except Exception as exc:
        raise RuntimeError("Format FILE_KEK_BASE64 tidak valid") from exc

    if len(kek) != 32:
        raise RuntimeError("KEK harus berukuran tepat 32 byte")

    return kek


def generate_dek():
    """
    Membuat DEK unik berukuran 256 bit untuk setiap file.
    """
    return AESGCM.generate_key(bit_length=256)


def wrap_dek(dek):
    """
    Mengenkripsi DEK menggunakan KEK.
    Hasil: nonce + ciphertext + authentication tag.
    """
    kek = get_kek()

    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(kek)

    encrypted_dek = aesgcm.encrypt(
        nonce,
        dek,
        b"securevault-dek-v1"
    )

    return nonce + encrypted_dek


def unwrap_dek(encrypted_dek):
    """
    Membuka DEK menggunakan KEK.
    """
    kek = get_kek()

    if len(encrypted_dek) != 60:
        raise ValueError("Data DEK terenkripsi tidak valid")

    nonce = encrypted_dek[:12]
    ciphertext = encrypted_dek[12:]

    aesgcm = AESGCM(kek)

    return aesgcm.decrypt(
        nonce,
        ciphertext,
        b"securevault-dek-v1"
    )
