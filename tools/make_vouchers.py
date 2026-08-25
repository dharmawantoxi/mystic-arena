# ================================================================
# Generator batch kode voucher TOP UP untuk dev.
#
# Pakai:
#     python tools/make_vouchers.py [jumlah] [--amount GOLD] [--new]
#
# Contoh:
#     python tools/make_vouchers.py 50                 # 50 kode,
#                                                      # nominal default
#     python tools/make_vouchers.py 10 --amount 75000  # 10 kode
#                                                      # @ 75.000 gold
#     python tools/make_vouchers.py 50 --new           # buat batch BARU
#                                                      # (hapus isi lama)
#
# Output: voucher_codes.txt di root project (gitignored!) — file ini
# ikut ter-bundle oleh buildozer saat build APK, sehingga kode pada
# batch aktif yang valid. Bagikan kodenya ke pemain HANYA setelah
# pembayaran terverifikasi.
# ================================================================

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topup_voucher import VOUCHER_FILE, generate, append_codes  # noqa: E402


def main():
    p = argparse.ArgumentParser(description="Generate kode voucher top up")
    p.add_argument("count", nargs="?", type=int, default=100,
                   help="jumlah kode (default 100)")
    p.add_argument("--amount", type=int, default=None,
                   help="nominal gold per kode (default = paket standar)")
    p.add_argument("--new", action="store_true",
                   help="hapus isi file lama, mulai batch baru")
    args = p.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, VOUCHER_FILE)

    codes = generate(args.count)
    n = append_codes(codes, path, amount=args.amount, overwrite=args.new)

    print(f"\n{n} kode voucher ditulis ke {VOUCHER_FILE}\n")
    print("Kirim kode berikut ke pemain SETELAH pembayaran terverifikasi:")
    print("-" * 40)
    for c in codes:
        amt = f"  ({args.amount:,} gold)" if args.amount else ""
        print(f"  {c}{amt}")
    print("-" * 40)
    print("\nPENTING: file ini gitignored — jangan commit!")


if __name__ == "__main__":
    main()
