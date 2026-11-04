
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_file(file_data, dek):
    """
    Mengenkripsi seluruh isi file menggunakan AES-256-GCM.

    Args:
        file_data: Isi file dalam bentuk bytes.
        dek: Data Encryption Key berukuran 32 byte.

    Returns:
        nonce, ciphertext, auth_tag
    """

    if not isinstance(file_data, bytes):
        raise TypeError("Data file harus berupa bytes")

    if len(dek) != 32:
        raise ValueError("DEK harus berukuran 32 byte")

    # Membuat nonce acak 12 byte
    nonce = secrets.token_bytes(12)

    # Membuat objek AES-GCM
    aesgcm = AESGCM(dek)

    # Mengenkripsi seluruh data
    encrypted_data = aesgcm.encrypt(
        nonce,
        file_data,
        None
    )

    # Memisahkan ciphertext dan authentication tag
    ciphertext = encrypted_data[:-16]
    auth_tag = encrypted_data[-16:]

    return nonce, ciphertext, auth_tag


def decrypt_file(ciphertext, dek, nonce, auth_tag):
    """
    Mendekripsi file menggunakan AES-256-GCM.

    Returns:
        Isi file asli dalam bentuk bytes.
    """

    if len(dek) != 32:
        raise ValueError("DEK harus berukuran 32 byte")

    if len(nonce) != 12:
        raise ValueError("Nonce harus berukuran 12 byte")

    if len(auth_tag) != 16:
        raise ValueError("Authentication tag harus berukuran 16 byte")

    aesgcm = AESGCM(dek)

    # Menggabungkan ciphertext dan authentication tag
    encrypted_data = ciphertext + auth_tag

    # Mendekripsi sekaligus memverifikasi integritas data
    original_data = aesgcm.decrypt(
        nonce,
        encrypted_data,
        None
    )

    return original_data
