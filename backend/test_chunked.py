
import os
import hashlib

from app.encryption.key_manager import generate_dek
from app.encryption.chunked import (
    encrypt_file_chunked,
    decrypt_file_chunked
)


def calculate_hash(path):
    """Menghitung SHA-256 file secara bertahap."""
    digest = hashlib.sha256()

    with open(path, "rb") as file:
        while True:
            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


# Membuat file uji berukuran 2,5 MB
original_path = "test_original.bin"
encrypted_path = "test_encrypted.enc"
decrypted_path = "test_decrypted.bin"

with open(original_path, "wb") as file:
    file.write(os.urandom(2 * 1024 * 1024))
    file.write(os.urandom(512 * 1024))

# Membuat DEK baru
dek = generate_dek()

# Enkripsi
print("Memulai enkripsi...")

result_encrypt = encrypt_file_chunked(
    original_path,
    encrypted_path,
    dek
)

print("Hasil enkripsi:", result_encrypt)

# Dekripsi
print("\nMemulai dekripsi...")

result_decrypt = decrypt_file_chunked(
    encrypted_path,
    decrypted_path,
    dek
)

print("Hasil dekripsi:", result_decrypt)

# Membandingkan SHA-256 file
original_hash = calculate_hash(original_path)
decrypted_hash = calculate_hash(decrypted_path)

print("\nHash file asli     :", original_hash)
print("Hash file dekripsi :", decrypted_hash)

print(
    "\nApakah file sama:",
    original_hash == decrypted_hash
)
