# ================================
# mobile/ - lapisan Android (touch, performa, debug)
# ================================
#
# Paket ini SENGAJA dibuat terpisah dari kode game lama supaya:
#   1. Kode desktop lama tetap jalan tanpa perubahan.
#   2. Semua hal khusus Android terkumpul di satu tempat.
#
# Urutan pakai di main.py:
#     from mobile import platform_utils, perf, touch, hud, debug
#     perf.install_all()            # patch cache font/teks (paling awal!)
#     screen = platform_utils.create_display()
#     ...
# ================================

__all__ = ["platform_utils", "perf", "touch", "hud", "debug"]
