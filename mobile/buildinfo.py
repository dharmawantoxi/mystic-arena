# ================================
# mobile/buildinfo.py
# Penanda build — supaya SELALU jelas APK mana yang sedang jalan.
#
# Ditampilkan di layar diagnostik dan overlay debug. Kalau nomor di
# HP tidak sama dengan yang ada di repo, berarti APK-nya belum
# diperbarui (bukan perbaikannya yang gagal).
# ================================

import os

# Naikkan setiap kali ada perubahan kode yang dikirim ke perangkat.
BUILD_ID = "v10-castlecache"
BUILD_DATE = "2026-08-21"

_KEY_FILES = (
    "_core.py", "_render.py", "splash_screen.py", "main.py",
    "mobile/perf.py", "mobile/blitwatch.py", "mobile/bootcheck.py",
    "ui_components/_bundle.py",
)


def fingerprint():
    """
    Sidik jari ringan dari ukuran berkas kunci. Berubah otomatis
    setiap kali salah satu berkas diedit -> tidak bisa lupa update.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    total = 0
    found = 0
    for rel in _KEY_FILES:
        try:
            total += os.path.getsize(os.path.join(root, *rel.split("/")))
            found += 1
        except OSError:
            pass
    return "%05X/%d" % (total % 0x100000, found)


def label():
    return "BUILD %s (%s) fp=%s" % (BUILD_ID, BUILD_DATE, fingerprint())
