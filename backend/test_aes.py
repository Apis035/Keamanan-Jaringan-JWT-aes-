
from app.encryption.key_manager import generate_dek
from app.encryption.aes import encrypt_file, decrypt_file

# Data contoh, seolah-olah isi sebuah file
original_data = b"Ini adalah isi file SecureVault!"

# Membuat DEK
dek = generate_dek()

# Mengenkripsi file
nonce, ciphertext, auth_tag = encrypt_file(
    original_data,
    dek
)

# Mendekripsi file
decrypted_data = decrypt_file(
    ciphertext,
    dek,
    nonce,
    auth_tag
)

print("Data asli:", original_data)
print("Ukuran ciphertext:", len(ciphertext))
print("Ukuran nonce:", len(nonce))
print("Ukuran authentication tag:", len(auth_tag))
print("Apakah data sama:", original_data == decrypted_data)


from cryptography.exceptions import InvalidTag

print("\n--- Pengujian Integritas AES-256-GCM ---")

# Salin ciphertext, lalu ubah satu byte
tampered_ciphertext = bytearray(ciphertext)
tampered_ciphertext[0] ^= 1

try:
    decrypt_file(
        bytes(tampered_ciphertext),
        dek,
        nonce,
        auth_tag
    )

    print("GAGAL: Perubahan data tidak terdeteksi!")

except InvalidTag:
    print("BERHASIL: Perubahan ciphertext berhasil dideteksi!")

# Uji perubahan authentication tag
tampered_tag = bytearray(auth_tag)
tampered_tag[0] ^= 1

try:
    decrypt_file(
        ciphertext,
        dek,
        nonce,
        bytes(tampered_tag)
    )

    print("GAGAL: Perubahan tag tidak terdeteksi!")

except InvalidTag:
    print("BERHASIL: Perubahan authentication tag berhasil dideteksi!")
