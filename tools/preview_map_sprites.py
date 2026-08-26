"""Preview + benchmark peta HD (gaya sprite HD Thorne).

Jalankan (tanpa layar):

    .venv/bin/python tools/preview_map_sprites.py

Hasil:
  * docs/map_sprite_<tema>_before.png  (pipeline lama)
  * docs/map_sprite_<tema>_after.png   (pipeline HD baru)
  * docs/map_sprite_contact_sheet.png  (grid 2x2 hasil baru)
  * timing init level (lama vs baru) di stdout.

Perbandingan jujur: kedua pipeline diukur sebagai total waktu
init MapRenderer (termasuk generate lane/dekorasi). "Baru"
termasuk build layer HD pertama per tema (di-cache; retry tema
sama jauh lebih cepat — lihat timing pada pemanggilan kedua
dalam satu proses).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)
sys.path.insert(0, HERE)

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

pygame.init()

# PENTING: _core harus di-import duluan (dia yang membuat alias
# modul `settings` dari globals-nya; urutan sama seperti main.py).
import _core  # noqa: E402,F401
from _render import MapRenderer  # noqa: E402

THEMES = ["forest", "desert", "ice", "cosmic", "royal", "crimson"]
DOCS = os.path.join(HERE, "docs")


def _set_legacy(flag):
    if flag:
        os.environ["MYSTIC_LEGACY_MAP"] = "1"
    else:
        os.environ.pop("MYSTIC_LEGACY_MAP", None)


def init_map(theme_name, legacy):
    _set_legacy(legacy)
    screen = pygame.Surface((1280, 720))
    t0 = time.perf_counter()
    mr = MapRenderer(screen, theme_name=theme_name)
    dt = (time.perf_counter() - t0) * 1000.0
    _set_legacy(False)
    return mr, dt


def main():
    os.makedirs(DOCS, exist_ok=True)
    sheet_tiles = []
    print(f"{'tema':<10} {'lama(ms)':>10} {'baru(ms)':>10}")
    for tname in THEMES:
        mr_old, dt_old = init_map(tname, legacy=True)
        mr_new, dt_new = init_map(tname, legacy=False)
        print(f"{tname:<10} {dt_old:>10.1f} {dt_new:>10.1f}")

        pygame.image.save(mr_old.static_map, os.path.join(
            DOCS, f"map_sprite_{tname}_before.png"))
        pygame.image.save(mr_new.static_map, os.path.join(
            DOCS, f"map_sprite_{tname}_after.png"))
        if tname in ("forest", "desert", "ice", "cosmic"):
            tile = pygame.transform.smoothscale(mr_new.static_map,
                                                (640, 360))
            sheet_tiles.append((tname, tile))

    # Contact sheet 2x2
    sheet = pygame.Surface((1280, 720))
    sheet.fill((10, 8, 14))
    pos = [(0, 0), (640, 0), (0, 360), (640, 360)]
    try:
        from _render import get_font
        font = get_font(18, "body", True)
    except Exception:
        font = pygame.font.Font(None, 24)
    for (tname, tile), p in zip(sheet_tiles, pos):
        sheet.blit(tile, p)
        label = font.render(tname.upper(), True, (255, 255, 255))
        sheet.blit(label, (p[0] + 8, p[1] + 6))
    pygame.image.save(sheet, os.path.join(
        DOCS, "map_sprite_contact_sheet.png"))
    print("OK: preview tersimpan di docs/")


if __name__ == "__main__":
    main()
