# ================================================================
# Smoke test headless untuk fitur TOP UP HERO GOLD.
#
# Jalankan dari root project:
#     python tools/test_topup.py
#
# Tidak butuh layar/monitor nyata (driver dummy), jadi aman
# dijalankan di CI atau server.
# ================================================================

import os
import sys

# Driver dummy HARUS diset SEBELUM pygame di-import.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import _core  # noqa: E402
from _core import Menu, MenuState, TOPUP_PACKAGES, TOPUP_PAYMENT_METHODS, fmt_idr  # noqa: E402
from topup_currency import (  # noqa: E402
    IDR_PER_UNIT, REGION_CURRENCY,
    detect_currency, convert_idr, format_price,
)


def main():
    pygame.init()
    screen = pygame.display.set_mode((_core.SCREEN_WIDTH,
                                      _core.SCREEN_HEIGHT))
    menu = Menu(screen)

    # ── 0. Idempotensi: buang kode uji yang tersisa di save dari run
    # sebelumnya, supaya redeem di bawah selalu dianggap kode baru.
    # (Tanpa ini, run kedua gagal karena kode sudah "already redeemed".)
    _used = menu.save_data.setdefault("redeemed_codes", [])
    if "MA-111111" in _used or "MA-222222" in _used:
        menu.save_data["redeemed_codes"] = [
            c for c in _used if c not in ("MA-111111", "MA-222222")]
        from _system import SaveManager
        SaveManager.save(menu.save_data)

    # ── 1. Masuk hero shop: tombol + TOP UP harus ada ──
    menu.state = MenuState.HERO_SHOP
    screen.fill((0, 0, 0))
    menu.draw()
    assert "topup_open" in menu.buttons, "tombol TOP UP tidak ada"
    print("OK 1: tombol '+ TOP UP' muncul di Hero Shop")

    # ── 2. Buka dialog: modal + tombol lengkap + currency terdeteksi ──
    menu._on_button_click("topup_open")
    menu.draw()
    assert menu.topup_open and menu.topup_phase == "select"
    for i in range(len(TOPUP_PACKAGES)):
        assert f"topup_pkg_{i}" in menu.buttons, f"paket {i} tidak ada"
    for i in range(len(TOPUP_PAYMENT_METHODS)):
        assert f"topup_method_{i}" in menu.buttons, f"metode {i} tidak ada"
    assert "topup_pay" in menu.buttons
    assert "topup_cancel" in menu.buttons
    # Tombol shop di belakang dialog tidak boleh bisa diklik.
    assert "tab_starter" not in menu.buttons, "dialog top up tidak modal!"
    # Currency auto-deteksi: harus currency yang didukung.
    assert menu.topup_currency in IDR_PER_UNIT, \
        f"currency tak didukung: {menu.topup_currency}"
    assert menu._topup_price_str(10000), "string harga kosong"
    print(f"OK 2: dialog terbuka, modal, currency terdeteksi "
          f"= {menu.topup_currency} ({menu._topup_price_str(10000)})")

    # ── 3. Paket default (satu-satunya) & metode OVO (idx 1) ──
    assert len(TOPUP_PACKAGES) == 1, "seharusnya hanya 1 paket"
    pkg0 = TOPUP_PACKAGES[0]
    assert pkg0["gold"] == 50000 and pkg0["price"] == 10000
    assert pkg0.get("bonus", 0) == 0
    assert menu.topup_pkg_idx == 0
    menu._on_button_click("topup_pkg_0")
    menu._on_button_click("topup_method_1")
    assert menu.topup_pkg_idx == 0
    assert menu.topup_method_idx == 1
    print("OK 3: satu paket tersedia (50.000 gold / Rp 10.000), "
          "metode tersimpan")

    # ── 4. Bayar -> processing; cancel & klik paket harus diabaikan ──
    gold_before = menu.meta_gold
    menu._on_button_click("topup_pay")
    assert menu.topup_phase == "processing"
    menu.draw()
    menu._on_button_click("topup_cancel")  # harus diabaikan
    assert menu.topup_open, "dialog tertutup saat processing!"
    menu._on_button_click("topup_pkg_0")   # klik paket juga diabaikan
    assert menu.topup_pkg_idx == 0
    print("OK 4: cancel & klik paket diabaikan selama processing")

    # ── 5. Jalankan frame sampai pembayaran sukses ──
    for _ in range(60 * 3):
        menu.update()
        if menu.topup_phase == "success":
            break
    assert menu.topup_phase == "success", "pembayaran tidak pernah sukses"
    pkg = TOPUP_PACKAGES[0]
    expected = int(pkg["gold"]) + int(pkg.get("bonus", 0))
    assert menu.meta_gold == gold_before + expected, \
        f"gold salah: {menu.meta_gold} != {gold_before + expected}"
    assert menu.topup_tx_id.startswith("MA-")
    hist = menu.save_data.get("topup_history", [])
    assert hist, "riwayat transaksi kosong"
    assert hist[-1]["method"] == "ovo"
    assert hist[-1]["gold"] == int(pkg["gold"])
    assert hist[-1]["bonus"] == int(pkg.get("bonus", 0))
    assert hist[-1]["price"] == int(pkg["price"])  # base IDR
    assert hist[-1]["cur"] == menu.topup_currency
    assert hist[-1]["price_cur"] > 0
    print(f"OK 5: pembayaran sukses, +{expected:,} gold, riwayat tercatat "
          f"(cur={hist[-1]['cur']}, price_cur={hist[-1]['price_cur']})")

    # ── 6. Save file sudah ter-update ──
    import json
    sm = _core.SaveManager
    slot_file = sm.get_slot_file(sm.get_current_slot())
    with open(slot_file) as f:
        saved = json.load(f)
    assert saved["meta_gold"] == gold_before + expected
    assert saved["topup_history"][-1]["tx"] == menu.topup_tx_id
    print(f"OK 6: save file ter-update -> {slot_file}")

    # ── 7. Layar sukses + tombol BACK ──
    menu.draw()
    assert "topup_back" in menu.buttons
    menu._on_button_click("topup_back")
    assert not menu.topup_open
    menu.draw()
    assert "topup_open" in menu.buttons
    assert "topup_back" not in menu.buttons
    print("OK 7: layar sukses ditampilkan, tombol BACK menutup dialog")

    # ── 8. Cancel saat fase select menutup dialog ──
    menu._on_button_click("topup_open")
    menu.draw()
    menu._on_button_click("topup_cancel")
    assert not menu.topup_open
    print("OK 8: cancel saat fase select menutup dialog")

    # ── 9. Format Rupiah ──
    assert fmt_idr(120000) == "Rp 120.000"
    assert fmt_idr(1000) == "Rp 1.000"
    assert fmt_idr(750000) == "Rp 750.000"
    print("OK 9: format Rupiah (titik ribuan) benar")

    # ── 10. Multi-currency (pemain luar Indonesia) ──
    # 10a. detect_currency selalu return currency yang didukung.
    cur = detect_currency()
    assert cur in IDR_PER_UNIT, f"deteksi gagal: {cur}"
    # 10b. Peta region benar.
    assert REGION_CURRENCY["US"] == "USD"
    assert REGION_CURRENCY["SG"] == "SGD"
    assert REGION_CURRENCY["ID"] == "IDR"
    assert REGION_CURRENCY["JP"] == "JPY"
    # 10c. Konversi + format (Rp 10.000 = harga satu paket).
    assert format_price(10000, "IDR") == "Rp 10.000"
    assert format_price(10000, "USD") == "$0.62"
    assert format_price(10000, "SGD") == "S$0.82"
    assert format_price(10000, "JPY") == "¥93"
    assert format_price(10000, "KRW") == "₩870"
    assert format_price(10000, "VND") == "₫16,129"
    # 10d. Currency tidak dikenal -> fallback USD (tidak crash).
    assert format_price(10000, "XXX") == "$0.62"
    val, cur2 = convert_idr(10000, "EUR")
    assert cur2 == "EUR" and abs(val - 10000 / IDR_PER_UNIT["EUR"]) < 1e-9
    print(f"OK 10: multi-currency OK (deteksi device = {cur})")

    # ── 11. REDEEM CODE (alur voucher manual) ──
    import topup_voucher as tv
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vpath = os.path.join(root, tv.VOUCHER_FILE)
    backup = None
    if os.path.exists(vpath):
        with open(vpath) as f:
            backup = f.read()
    try:
        with open(vpath, "w") as f:
            f.write("# batch test\nMA-111111\nMA-222222=75000\n")

        menu._on_button_click("topup_open")
        menu.draw()
        assert "topup_redeem" in menu.buttons, "baris REDEEM CODE tidak ada"
        menu._on_button_click("topup_redeem")
        assert menu.topup_phase == "redeem"
        menu.draw()
        for k in "0123456789":
            assert f"vpk_{k}" in menu.buttons, f"keypad {k} tidak ada"
        for b in ("vpk_del", "vpk_redeem", "vback"):
            assert b in menu.buttons, f"{b} tidak ada"

        # Input via keypad + keyboard
        for k in "987":
            menu._on_button_click(f"vpk_{k}")
        assert menu.topup_redeem_input == "MA-987"
        menu._on_button_click("vpk_del")
        assert menu.topup_redeem_input == "MA-98"
        menu.handle_key(pygame.K_9)
        menu.handle_key(pygame.K_BACKSPACE)
        assert menu.topup_redeem_input == "MA-98"

        # Format tidak valid (2 digit) -> ditolak, tetap di fase redeem
        menu._on_button_click("vpk_redeem")
        assert menu.topup_phase == "redeem"
        assert menu.topup_redeem_msg, "harus ada pesan error"

        # Kode valid dari allowlist -> gold masuk
        menu._on_button_click("vback")
        menu._on_button_click("topup_redeem")
        gold_b = menu.meta_gold
        for k in "111111":
            menu._on_button_click(f"vpk_{k}")
        menu._on_button_click("vpk_redeem")
        assert menu.topup_phase == "success"
        assert menu.meta_gold == gold_b + 50000
        h = menu.save_data["topup_history"][-1]
        assert h["method"] == "redeem" and h["code"] == "MA-111111"
        assert h["gold"] == 50000
        assert "MA-111111" in menu.save_data["redeemed_codes"]
        print("OK 11a: redeem kode valid, +50,000 gold, riwayat tercatat")

        # Double redeem -> ditolak
        menu.draw()
        menu._on_button_click("topup_back")
        assert not menu.topup_open
        menu._on_button_click("topup_open")
        menu.draw()
        menu._on_button_click("topup_redeem")
        menu.draw()
        for k in "111111":
            menu._on_button_click(f"vpk_{k}")
        menu._on_button_click("vpk_redeem")
        assert menu.topup_phase == "redeem"
        assert "already redeemed" in menu.topup_redeem_msg[0]
        print("OK 11b: double-redeem ditolak")

        # Kode nominal khusus (MA-222222=75000)
        menu._on_button_click("vback")
        menu._on_button_click("topup_redeem")
        menu.draw()
        for k in "222222":
            menu._on_button_click(f"vpk_{k}")
        menu._on_button_click("vpk_redeem")
        assert menu.topup_phase == "success"
        assert menu.meta_gold == gold_b + 50000 + 75000
        print("OK 11c: redeem nominal khusus (+75,000) benar")

        # Generator voucher
        codes = tv.generate(10)
        assert len(set(codes)) == 10
        assert all(tv.is_valid_format(c) for c in codes)
        print("OK 11d: generator voucher + validasi format OK")
    finally:
        if backup is None:
            os.remove(vpath)
        else:
            with open(vpath, "w") as f:
                f.write(backup)

    print("\nSEMUA TES TOP UP LULUS")


if __name__ == "__main__":
    main()
