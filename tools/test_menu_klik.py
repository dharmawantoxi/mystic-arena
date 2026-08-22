# ================================
# tools/test_menu_klik.py
# Uji regresi: menu utama TIDAK boleh crash saat update()/klik.
#
# Bug v30: Menu.update() memanggil self._kena(...) padahal _kena
# hanya didefinisikan sebagai staticmethod di kelas InputHandler.
# Akibatnya game force-close tepat setelah splash selesai.
# Test ini menjalankan jalur yang sama di 16:9 dan 21:9.
#     python tools/test_menu_klik.py
# ================================
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# Paksa mode sentuh supaya create_display memakai rasio layar dari
# pygame.display.Info() -> panel kanan benar-benar dibuat di 21:9.
os.environ["MYSTIC_FORCE_TOUCH"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 1024)
pygame.init()

from mobile import platform_utils as plat   # noqa: E402
from mobile import perf                     # noqa: E402
perf.install_all(is_android=True)


def jalankan(lebar_layar, tinggi_layar):
    """Buat menu, jalankan update + klik tiap tombol, pastikan tidak crash."""
    class _Info:
        current_w = lebar_layar
        current_h = tinggi_layar
    pygame.display.Info = lambda: _Info()

    render = plat.create_display(vsync=True)

    import _core                              # noqa: E402,F401
    from menu import Menu                     # noqa: E402
    from _render import get_font              # noqa: E402
    from mobile import sidepanel as panel_mod # noqa: E402

    side = panel_mod.SidePanel(get_font)
    panel_mod.daftarkan(side)

    menu = Menu(render)
    ok = True

    # ── jalur yang dulu crash: update() memanggil self._kena ──
    for _ in range(3):
        menu.update()

    # ── gambar + panel (seperti di main loop) ──
    for _ in range(2):
        side.draw(plat.get_full_surface(), None, None, 16, paksa_blit=False)
        menu.draw()

    # ── klik tengah setiap tombol: tidak boleh AttributeError ──
    for btn_id, rect in list(menu.buttons.items()):
        try:
            menu.handle_click(rect.center, 1)
        except AttributeError as exc:
            print("  CRASH di tombol %-12s -> %s" % (btn_id, exc))
            ok = False

    print("  panel: %s | tombol diuji: %d | %s"
          % (plat.get_panel_rect(), len(menu.buttons),
             "LULUS" if ok else "GAGAL"))
    return ok


if __name__ == "__main__":
    semua = True
    print("=" * 60)
    print("21:9 (HP lebar, panel kanan)")
    print("=" * 60)
    semua &= jalankan(2436, 1080)

    print("=" * 60)
    print("16:9 (tanpa panel)")
    print("=" * 60)
    semua &= jalankan(1280, 720)

    print("\nHASIL: %s" % ("LULUS. Menu tidak crash." if semua
                           else "GAGAL. Ada tombol menu yang crash."))
    sys.exit(0 if semua else 1)
