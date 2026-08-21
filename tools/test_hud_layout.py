"""
tools/test_hud_layout.py

Memeriksa tata letak tombol sentuh SEBELUM masuk build.

Dua hal yang diperiksa
──────────────────────
1. UKURAN AREA SENTUH
   Panduan Android: target sentuh minimal 48dp. Di HP uji
   (2436x1080, ~404 dpi, skala 1,5) itu setara ~80 px logis.
   Tombol lama 44x44 hanya ~26dp - memang susah ditekan.

2. TUMPANG TINDIH ANTAR TOMBOL YANG TAMPIL BERSAMAAN
   Area sentuh sengaja dilebarkan 12 px per sisi. Kalau dua tombol
   terlalu berdekatan, area sentuhnya bertumpuk dan ketukan di
   celahnya memicu tombol yang salah - misalnya menekan "MENU"
   padahal maksudnya "NEXT LEVEL" di layar kemenangan.

   Yang diperiksa hanya kombinasi yang benar-benar bisa tampil
   bersamaan; tombol yang saling eksklusif antar-state dilewati.

Jalankan:  python3 tools/test_hud_layout.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_FORCE_TOUCH", "1")

import pygame                                            # noqa: E402

pygame.init()
pygame.display.set_mode((1280, 720))

from mobile import hud as H                              # noqa: E402

# Kelompok tombol yang bisa tampil pada saat yang sama.
BERSAMAAN = [
    ("sedang bermain", ["pause", "debug"]),
    ("layar kemenangan", ["replay", "next_level", "menu", "debug"]),
    ("layar kekalahan", ["replay", "menu", "debug"]),
    ("cinematic", ["skip", "debug"]),
]


def main():
    hud = H.TouchHUD(lambda *a, **k: pygame.font.Font(None, 20))

    print("Ambang area sentuh: %d px logis (~48dp di HP uji)\n" % H.MIN_TAP)
    print("  %-12s %-12s %-12s %s"
          % ("tombol", "terlihat", "area sentuh", "status"))

    gagal = []
    for nama, btn in hud.buttons.items():
        w, h = btn.hit_rect.width, btn.hit_rect.height
        ok = min(w, h) >= H.MIN_TAP
        if not ok:
            gagal.append("%s: area sentuh %dx%d < %d px"
                         % (nama, w, h, H.MIN_TAP))
        print("  %-12s %-12s %-12s %s"
              % (nama, "%dx%d" % (btn.rect.w, btn.rect.h),
                 "%dx%d" % (w, h), "OK" if ok else "TERLALU KECIL"))

    print("\nTumpang tindih antar tombol yang tampil bersamaan:")
    for judul, kelompok in BERSAMAAN:
        bentrok = []
        for i in range(len(kelompok)):
            for j in range(i + 1, len(kelompok)):
                a = hud.buttons.get(kelompok[i])
                b = hud.buttons.get(kelompok[j])
                if a is None or b is None:
                    continue
                if a.hit_rect.colliderect(b.hit_rect):
                    lebar = (a.hit_rect.clip(b.hit_rect).width)
                    bentrok.append("%s <-> %s (%d px)"
                                   % (kelompok[i], kelompok[j], lebar))
        if bentrok:
            gagal.extend("%s: %s" % (judul, b) for b in bentrok)
            print("  %-18s %s" % (judul, ", ".join(bentrok)))
        else:
            print("  %-18s bersih" % judul)

    print()
    if gagal:
        print("HASIL: GAGAL")
        for g in gagal:
            print("  - %s" % g)
        return 1
    print("HASIL: LULUS. Semua tombol >= %d px dan tidak ada yang "
          "bertumpuk." % H.MIN_TAP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
