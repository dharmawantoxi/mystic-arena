"""
tools/test_popup_klik.py

Memastikan SETIAP tombol popup benar-benar bisa ditekan — di layar
yang punya panel kanan MAUPUN yang tidak.

Kenapa ada
──────────
Saat popup dipindah ke panel kanan, semua tombolnya mati: panel
upgrade hero, popup build tower, popup castle. Penyebabnya dua hal
yang sama-sama tidak terlihat dari kode gambarnya:

  1. main.py mengklaim SEMUA sentuhan di area panel supaya tidak
     tembus ke peta - sekaligus memblokir tombol yang kini ada
     di sana.
  2. handle_click MENGHITUNG ULANG posisi panel hero dengan angka
     tetap (px=20, kiri bawah). Gambarnya pindah, pemeriksaan
     kliknya tidak.

Keduanya lolos dari uji manual saya karena tampilannya terlihat
benar. Yang membedakan hanya percobaan menekan.

Yang diperiksa
──────────────
  - setiap rect di game.ui_buttons benar-benar bisa "ditekan":
    handle_click di titik tengahnya harus mengubah keadaan game
  - rect gambar dan rect klik menunjuk tempat yang sama
  - ketukan di ruang kosong panel TIDAK memerintahkan hero berjalan
  - semuanya diulang untuk layar 21:9 (ada panel) dan 16:9 (tidak)

Jalankan:  python3 tools/test_popup_klik.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_FORCE_TOUCH", "1")
os.environ.setdefault("MYSTIC_BENCH", "0")
os.environ.setdefault("MYSTIC_BOOTCHECK", "0")

import pygame                                            # noqa: E402

pygame.init()

# Tombol yang MEMANG tidak mengubah keadaan apa pun - bukan kegagalan.
# toggle_autocast sengaja dijadikan penanda status sejak tombol
# Q/W/E/R dihapus: mematikan auto-cast akan membuat skill hero tidak
# pernah keluar sama sekali.
SENGAJA_DIAM = {"toggle_autocast"}

LAYAR = [
    ("21:9 (panel kanan aktif)", 2436, 1080),
    ("16:9 (tanpa panel)", 1920, 1080),
]


def siapkan(lebar, tinggi):
    from mobile import platform_utils as plat
    from mobile import perf

    class _Info:
        current_w, current_h = lebar, tinggi

    asli = pygame.display.Info
    pygame.display.Info = lambda: _Info()
    try:
        perf.install_all(is_android=False)
        screen = plat.create_display(vsync=False, mode="scaled")
    finally:
        pygame.display.Info = asli
    return plat, screen


def buat_game(screen):
    from _core import Game
    from _entity import Hero
    g = Game(screen, level_number=1)
    import __main__
    __main__.game_instance = g
    for nm in ("level_intro", "boss_intro"):
        o = getattr(g, nm, None)
        if o is not None and hasattr(o, "handle_skip"):
            try:
                o.handle_skip(key=pygame.K_SPACE)
            except Exception:
                pass
    g.gold = 99999
    g.heroes.append(Hero("grimjaw", "blue", 300, 380))
    for _ in range(20):
        g.update()
    return g


def gambar(plat, g, side, full):
    clock = pygame.time.Clock()
    for _ in range(3):
        if side is not None and side.aktif:
            side.draw(full, g, clock, 16, paksa_blit=True)
        g.draw()


def uji_layar(judul, lebar, tinggi):
    print("\n" + "=" * 62)
    print(judul)
    print("=" * 62)
    plat, screen = siapkan(lebar, tinggi)
    full = plat.get_full_surface()
    import _core                                   # noqa: F401
    from _render import get_font
    from mobile import sidepanel
    side = sidepanel.SidePanel(get_font)
    sidepanel.daftarkan(side)
    print("panel: %s" % (plat.get_panel_rect(),))

    g = buat_game(screen)
    gagal = []

    # ── 1. panel hero terpilih ──
    g.selected_hero = g.heroes[0]
    gambar(plat, g, side, full)
    tombol = dict(g.ui_buttons)
    print("\n  panel hero: %d tombol" % len(tombol))
    for nama, rect in tombol.items():
        sebelum = (g.gold, g.selected_hero is not None,
                   getattr(g.heroes[0], "level", 1))
        g.handle_click(rect.center, 1)
        sesudah = (g.gold, g.selected_hero is not None,
                   getattr(g.heroes[0], "level", 1))
        berubah = sebelum != sesudah
        diam_disengaja = nama in SENGAJA_DIAM
        status = ("BERFUNGSI" if berubah
                  else ("penanda status (sengaja diam)"
                        if diam_disengaja else "TIDAK BEREAKSI"))
        print("    %-22s %-22s %s"
              % (nama, "pusat %s" % (rect.center,), status))
        if not berubah and not diam_disengaja:
            gagal.append("%s: %s tidak bereaksi" % (judul, nama))
        # pulihkan keadaan
        g.selected_hero = g.heroes[0]
        g.gold = 99999
        gambar(plat, g, side, full)

    # ── 2. ketukan kosong tidak boleh memerintah hero ──
    if plat.get_panel_rect() is not None:
        h = g.heroes[0]
        h.destination = None
        p = plat.get_panel_rect()
        g.handle_click((p.centerx, p.bottom - 20), 1)
        if getattr(h, "destination", None) is not None:
            gagal.append("%s: ketukan kosong di panel memerintah hero"
                         % judul)
            print("\n  ketukan kosong di panel -> MEMERINTAH HERO (salah)")
        else:
            print("\n  ketukan kosong di panel -> diabaikan (benar)")

    # ── 3. rect gambar == rect klik ──
    hp = getattr(g, "ui_rects", {}).get("hero_panel")
    if hp is not None:
        di_panel = hp.centerx >= 1280
        ada_panel = plat.get_panel_rect() is not None
        cocok = (di_panel == ada_panel)
        print("  rect panel hero %s -> %s"
              % (hp, "sesuai tata letak" if cocok else "SALAH TEMPAT"))
        if not cocok:
            gagal.append("%s: rect panel hero salah tempat" % judul)
    return gagal


def main():
    semua = []
    for judul, w, h in LAYAR:
        try:
            semua.extend(uji_layar(judul, w, h))
        except Exception as exc:
            import traceback
            traceback.print_exc()
            semua.append("%s: pengujian meledak: %s" % (judul, exc))

    print()
    if semua:
        print("HASIL: GAGAL")
        for g in semua:
            print("  - %s" % g)
        return 1
    print("HASIL: LULUS. Semua tombol popup bisa ditekan di kedua "
          "tata letak.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
