
import os
import gc
import time
import threading
import statistics
import psutil

from app.encryption.key_manager import generate_dek
from app.encryption.aes import encrypt_file, decrypt_file
from app.encryption.chunked import (
    encrypt_file_chunked,
    decrypt_file_chunked
)


PROCESS = psutil.Process(os.getpid())

SIZES_MB = [10, 50]
TRIALS = 3
CHUNK_SIZE = 1024 * 1024


class MemoryMonitor:
    def __init__(self):
        self.running = False
        self.peak = 0

    def start(self):
        self.running = True
        self.peak = PROCESS.memory_info().rss

        def monitor():
            while self.running:
                current = PROCESS.memory_info().rss
                self.peak = max(self.peak, current)
                time.sleep(0.005)

        self.thread = threading.Thread(target=monitor)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

        current = PROCESS.memory_info().rss
        self.peak = max(self.peak, current)

    def peak_mb(self):
        return self.peak / (1024 * 1024)


def measure(function):
    gc.collect()

    monitor = MemoryMonitor()
    monitor.start()

    start = time.perf_counter()

    try:
        function()
    finally:
        elapsed = time.perf_counter() - start
        monitor.stop()

    return elapsed, monitor.peak_mb()


def create_test_file(path, size_mb):
    remaining = size_mb * 1024 * 1024

    with open(path, "wb") as file:
        while remaining > 0:
            amount = min(1024 * 1024, remaining)
            file.write(os.urandom(amount))
            remaining -= amount


def run_full_file(source, encrypted, decrypted, dek):
    def encrypt():
        with open(source, "rb") as file:
            data = file.read()

        nonce, ciphertext, tag = encrypt_file(data, dek)

        with open(encrypted, "wb") as file:
            file.write(nonce)
            file.write(ciphertext)
            file.write(tag)

    enc_time, enc_ram = measure(encrypt)

    def decrypt():
        with open(encrypted, "rb") as file:
            data = file.read()

        nonce = data[:12]
        tag = data[-16:]
        ciphertext = data[12:-16]

        original = decrypt_file(
            ciphertext,
            dek,
            nonce,
            tag
        )

        with open(decrypted, "wb") as file:
            file.write(original)

    dec_time, dec_ram = measure(decrypt)

    return enc_time, dec_time, enc_ram, dec_ram


def run_chunked(source, encrypted, decrypted, dek):
    enc_time, enc_ram = measure(
        lambda: encrypt_file_chunked(
            source,
            encrypted,
            dek,
            CHUNK_SIZE
        )
    )

    dec_time, dec_ram = measure(
        lambda: decrypt_file_chunked(
            encrypted,
            decrypted,
            dek
        )
    )

    return enc_time, dec_time, enc_ram, dec_ram


def average(results, index):
    return statistics.mean(item[index] for item in results)


def main():
    print("=== SECUREVAULT PERFORMANCE BENCHMARK ===")

    for size in SIZES_MB:
        print(f"\nUkuran file: {size} MB")

        source = f"benchmark_{size}.bin"

        create_test_file(source, size)

        results = {
            "Full-file": [],
            "Chunked": []
        }

        for trial in range(1, TRIALS + 1):
            print(f"\nPercobaan {trial}/{TRIALS}")

            dek_full = generate_dek()
            dek_chunked = generate_dek()

            full = run_full_file(
                source,
                f"full_{size}.enc",
                f"full_{size}_out.bin",
                dek_full
            )

            chunked = run_chunked(
                source,
                f"chunked_{size}.enc",
                f"chunked_{size}_out.bin",
                dek_chunked
            )

            results["Full-file"].append(full)
            results["Chunked"].append(chunked)

            print("Full-file selesai.")
            print("Chunked selesai.")

        print("\n--- RATA-RATA HASIL ---")

        for method, data in results.items():
            print(f"\nMetode: {method}")
            print(f"Waktu enkripsi : {average(data, 0):.4f} detik")
            print(f"Waktu dekripsi : {average(data, 1):.4f} detik")
            print(f"Peak RAM enkripsi: {average(data, 2):.2f} MB")
            print(f"Peak RAM dekripsi: {average(data, 3):.2f} MB")

        # Membersihkan file percobaan
        for path in [
            source,
            f"full_{size}.enc",
            f"full_{size}_out.bin",
            f"chunked_{size}.enc",
            f"chunked_{size}_out.bin"
        ]:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    main()
