from app.encryption.key_manager import (
    generate_dek,
    wrap_dek,
    unwrap_dek
)

# Membuat DEK
dek_asli = generate_dek()

# Melindungi DEK dengan KEK
dek_terenkripsi = wrap_dek(dek_asli)

# Membuka kembali DEK
dek_hasil = unwrap_dek(dek_terenkripsi)

print("Panjang DEK:", len(dek_asli))
print("Panjang DEK terenkripsi:", len(dek_terenkripsi))
print("Apakah DEK sama:", dek_asli == dek_hasil)