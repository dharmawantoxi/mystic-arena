#!/usr/bin/env python3
"""A/B sheet untuk pass cahaya bersama (lighting.py + _finish_hd_sprite).

Baris ATAS = tanpa pass cahaya, baris BAWAH = dengan. Selain gambar, sheet
menyertakan angka: berapa piksel yang berubah dan rata-rata delta luminance.
Angka ini penting - pass cahaya yang "kerasa" di mata tapi 0 piksel berarti
tidak terpasang, dan pass yang mengubah >40% piksel berarti merusak desain
asli renderer.

Jalankan:  python3 tools/_shot_lighting_ab.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
import _core                                          # noqa: F401 (shim)
import heroes
from heroes import _ProbeEntity, render_hero, clear_hero_sprite_cache

HEROES = ("kaizen", "thorne", "sylara", "zephyr", "grimjaw", "vex", "gornak")
ZOOM = 3


def render_hero_sprite(name, size=320):
    """Hasil AKHIR jalur hero (crop + smoothscale + HD edge + lighting)."""
    c = size // 2
    canvas = pygame.Surface((size, size), pygame.SRCALPHA)
    h = _ProbeEntity(name, c, c)
    h.pulse = 1.35
    h.direction = 1
    h.team = "blue"
    clear_hero_sprite_cache()
    render_hero(name, canvas, h, c, c)
    rect = canvas.get_bounding_rect(min_alpha=100)
    if rect.width <= 0:
        return pygame.Surface((8, 8), pygame.SRCALPHA), None
    return canvas.subsurface(rect).copy(), rect


def diff_stats(a, b):
    """(piksel berubah, delta luminance rata-rata) antara dua sprite."""
    if a.get_size() != b.get_size():
        n = min(a.get_width(), b.get_width()), min(a.get_height(),
                                                   b.get_height())
        a = a.subsurface((0, 0) + n)
        b = b.subsurface((0, 0) + n)
    changed = 0
    total = 0
    lum = 0
    for y in range(0, a.get_height(), 1):
        for x in range(a.get_width()):
            pa, pb = a.get_at((x, y)), b.get_at((x, y))
            if pa.a < 100 or pb.a < 100:
                continue
            total += 1
            la = 0.299 * pa.r + 0.587 * pa.g + 0.114 * pa.b
            lb = 0.299 * pb.r + 0.587 * pb.g + 0.114 * pb.b
            if abs(la - lb) > 3:
                changed += 1
                lum += abs(la - lb)
    if not changed:
        return 0, 0.0, total
    return changed, lum / changed, total


def main():
    heroes.HD_LIGHTING_ENABLED = False
    before = {n: render_hero_sprite(n) for n in HEROES}
    heroes.HD_LIGHTING_ENABLED = True
    after = {n: render_hero_sprite(n) for n in HEROES}

    f_title = pygame.font.Font(None, 30)
    f_lbl = pygame.font.Font(None, 21)
    f_sm = pygame.font.Font(None, 17)

    # Grid 4 kolom; tiap sel = OFF | ON berdampingan supaya matanya bisa
    # membandingkan tanpa mengingat baris.
    per_row = 4
    Z = ZOOM
    cells = []
    for n in HEROES:
        rb, ra = before[n][1], after[n][1]
        w = max(rb.width, ra.width) * Z + 10
        h = max(rb.height, ra.height) * Z + 6
        cells.append((n, w, h))
    col_w = max(c[1] for c in cells) * 2 + 34
    row_h = max(c[2] for c in cells) + 58
    W = col_w * per_row + 24
    H = row_h * ((len(HEROES) + per_row - 1) // per_row) + 92
    s = pygame.Surface((W, H))
    s.fill((6, 7, 15))
    s.blit(f_title.render(
        "PASS CAHAYA BERSAMA (lighting.py -> heroes._finish_hd_sprite) - "
        "rim kiri-atas, terminator kanan-bawah, band gradien 1 px", True,
        (200, 168, 246)), (16, 14))
    s.blit(f_sm.render(
        "tiap sel: KIRI tanpa pass · KANAN dengan pass (zoom %dx, hasil "
        "akhir jalur hero termasuk outline HD)" % Z, True,
        (150, 128, 178)), (16, 44))

    for i, n in enumerate(HEROES):
        col, row = i % per_row, i // per_row
        x = 12 + col * col_w
        y = 72 + row * row_h
        img_b, img_a = before[n][0], after[n][0]
        cw = max(img_b.get_width(), img_a.get_width()) * Z + 10
        chh = max(img_b.get_height(), img_a.get_height()) * Z + 6
        box = pygame.Rect(x, y, cw * 2 + 14, chh)
        pygame.draw.rect(s, (11, 10, 24), box)
        pygame.draw.rect(s, (70, 45, 105), box, 1)
        for k, (img, rect) in enumerate(((img_b, before[n][1]),
                                         (img_a, after[n][1]))):
            zoomed = pygame.transform.scale(img, (rect.width * Z,
                                                   rect.height * Z))
            s.blit(zoomed, (box.x + 6 + k * (cw + 4), box.y + 3))
        ch, dl, tot = diff_stats(img_b, img_a)
        pct = (100.0 * ch / tot) if tot else 0.0
        s.blit(f_lbl.render(n, True, (232, 216, 255)), (box.x + 2,
                                                        box.bottom + 4))
        s.blit(f_sm.render("OFF | ON  ·  %d/%d px (%.0f%%), dL=%.0f"
                           % (ch, tot, pct, dl), True, (150, 128, 178)),
               (box.x + 2 + 70, box.bottom + 6))

    out = os.path.join(ROOT, "docs", "lighting_ab.png")
    pygame.image.save(s, out)
    print(out)
    print("ukuran sheet:", s.get_size())


if __name__ == "__main__":
    main()
