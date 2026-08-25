# ================================
# topup_voucher.py
# Redeem code untuk Top Up Hero Gold (alur voucher manual).
#
# ALUR BISNIS (MVP, tanpa backend):
#   1. Pemain bayar (invoice Midtrans/Xendit, transfer, dst).
#   2. Dev verifikasi pembayaran di dashboard gateway.
#   3. Dev kirim 1 kode voucher dari batch (tools/make_vouchers.py)
#      ke pemain (WhatsApp/email).
#   4. Pemain REDEEM kode di game (dialog top up) -> gold masuk.
#
# Nanti (gateway API): ganti validasi di Menu._redeem_submit()
# dengan cek ke webhook/server Anda; struktur kode & riwayat
# transaksi sudah kompatibel.
#
# FORMAT KODE : MA-XXXXXX (4-8 digit; batch default 6 digit)
# ALLOWLIST   : voucher_codes.txt — satu kode per baris.
#               Opsional "MA-123456=75000" untuk nominal khusus.
#               Tanpa file allowlist, semua kode berformat valid
#               diterima (mode demo/testing).
#               File dicari di root project lalu folder saves/.
#               Sengaja TIDAK masuk git (lihat .gitignore) agar
#               batch kode tidak bocor, tapi tetap ikut ter-bundle
#               oleh buildozer saat build APK.
# ================================

import os
import re
import random

VOUCHER_FILE = "voucher_codes.txt"
CODE_PREFIX = "MA-"
MAX_DIGITS = 6
CODE_RE = re.compile(r"^MA-(\d{4,8})$")


def is_valid_format(code):
    """Cek format saja: MA- + 4..8 digit."""
    return bool(CODE_RE.match((code or "").strip().upper()))


def load_vouchers():
    """Baca allowlist -> dict {CODE: gold_atau_None}.

    Return None kalau file tidak ada (mode demo: semua kode
    berformat valid diterima)."""
    root = os.path.dirname(os.path.abspath(__file__))
    saves_dir = "saves"
    try:
        import storage_paths
        saves_dir = getattr(storage_paths, "SAVE_DIR", saves_dir)
    except Exception:
        pass

    for path in (os.path.join(root, VOUCHER_FILE),
                 os.path.join(saves_dir, VOUCHER_FILE)):
        if not os.path.exists(path):
            continue
        result = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    code, amt = line.split("=", 1)
                    try:
                        result[code.strip().upper()] = int(amt.strip())
                    except ValueError:
                        continue
                else:
                    result[line.upper()] = None
        return result or None
    return None


def generate(n=100):
    """Generate n kode unik (6 digit) untuk dev."""
    codes = set()
    while len(codes) < n:
        codes.add(f"MA-{random.randint(10 ** 5, 10 ** 6 - 1):06d}")
    return sorted(codes)


def append_codes(codes, path, amount=None, overwrite=False):
    """Tulis kode ke file allowlist. amount=None -> nominal default
    (paket standar di game). Return jumlah baris yang ditambahkan."""
    if overwrite:
        # hapus isi lama (dev bikin batch baru)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Batch voucher top up - JANGAN commit ke git\n")
    with open(path, "a", encoding="utf-8") as f:
        for c in codes:
            f.write(f"{c}={amount}\n" if amount else f"{c}\n")
    return len(codes)
