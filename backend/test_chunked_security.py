import shutil
import os

from cryptography.exceptions import InvalidTag

from app.encryption.key_manager import generate_dek
from app.encryption.chunked import (
    encrypt_file_chunked,
    decrypt_file_chunked,
    HEADER_SIZE
)

original = "test_original.bin"
encrypted = "test_security.enc"

tampered = "test_tampered.enc"
truncated = "test_truncated.enc"

dek = generate_dek()

# Membuat file terenkripsi
encrypt_file_chunked(original, encrypted, dek)

print("--- Pengujian keamanan chunked ---")

# TEST 1: Mengubah isi chunk
shutil.copyfile(encrypted, tampered)

with open(tampered, "r+b") as file:
    file.seek(HEADER_SIZE + 10)

    byte = file.read(1)
    file.seek(HEADER_SIZE + 10)

    file.write(bytes([byte[0] ^ 1]))

try:
    decrypt_file_chunked(
        tampered,
        "output_tampered.bin",
        dek
    )
    print("GAGAL: Perubahan chunk tidak terdeteksi")

except InvalidTag:
    print("BERHASIL: Perubahan chunk terdeteksi")

# TEST 2: Memotong file terenkripsi
shutil.copyfile(encrypted, truncated)

with open(truncated, "rb+") as file:
    file.seek(0, os.SEEK_END)
    file.truncate(file.tell() - 10)

try:
    decrypt_file_chunked(
        truncated,
        "output_truncated.bin",
        dek
    )
    print("GAGAL: File terpotong tidak terdeteksi")

except (InvalidTag, ValueError):
    print("BERHASIL: File terpotong terdeteksi")

# Membersihkan file pengujian
for path in [
    encrypted,
    tampered,
    truncated,
    "output_tampered.bin",
    "output_truncated.bin"
]:
    if os.path.exists(path):
        os.remove(path)