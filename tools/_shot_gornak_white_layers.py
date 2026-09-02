#!/usr/bin/env python3
"""Penjaga regresi bug "cahaya putih menutupi karakter Gornak".

Akar bug yang dijaga tool ini: surface digambar dengan warna RGB penuh +
alpha samar lalu di-blit dengan ``BLEND_RGB_ADD`` — flag itu MENGABAIKAN
kanal alpha, jadi efek tampil intensitas penuh (lihat aturan PREMULTIPLIED
di ``heroes/gornak_fx.glow_surface``). Panel di bawah membuktikan badan
tetap terbaca di setiap lapisan.

Merender Gornak besar di beberapa konfigurasi lapisan supaya
terlihat lapisan mana yang menghasilkan wash putih:

  A. rig SAJA (badan mentah, tanpa outline, tanpa lighting)
  B. rig + outline (jalur _draw_gnk_rig_at penuh, lighting hidup)
  C. draw_gornak idle penuh (anti-magic field + rune + lighting + live FX)
  D. draw_gornak idle, lighting apply_to_rig dimatikan
  E. draw_gornak idle, anti-magic field dimatikan
  F. draw_gornak dengan hurt_flash_timer=8 (flash hurt)
  G. lane HERO (render_hero + cache + _finish_hd_sprite)

Tiap panel diberi metrik: piksel "putih" (min(r,g,b) >= 235) di dalam
area karakter, dan rasio piksel sangat terang (>= 250).
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import lighting  # noqa: E402
import heroes  # noqa: E402
from heroes import _ProbeEntity  # noqa: E402
from heroes import gornak_fx as F  # noqa: E402
import bosses.level1 as L  # noqa: E402
from bosses.level1 import _NS_gornak as G  # noqa: E402

ZOOM = 5
BG = (20, 14, 28)


def probe_boss(**kw):
    b = _ProbeEntity("gornak", 0.0, 0.0)
    b.pulse = 1.2
    b.direction = b.facing = 1
    b.hurt_flash_timer = 0
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def metrics(surf, rect):
    """Hitung piksel putih/terang di dalam rect sprite."""
    if rect.width <= 0:
        return 0, 0, rect.width * rect.height
    white = bright = 0
    sub = surf.subsurface(rect)
    w, h = sub.get_size()
    px = pygame.surfarray.pixels3d(sub)
    al = pygame.surfarray.pixels_alpha(sub)
    import builtins
    mn = builtins.min
    for ix in range(w):
        for iy in range(h):
            if al[ix][iy] < 40:
                continue
            r, g, b = int(px[ix][iy][0]), int(px[ix][iy][1]), int(px[ix][iy][2])
            m = mn(r, g, b)
            if m >= 235:
                white += 1
            if (r + g + b) // 3 >= 248:
                bright += 1
    del px, al
    return white, bright, rect.width * rect.height


def render_cell(draw_fn, label_txt, note=""):
    size = 240
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2 + 30
    F.reset_all()
    draw_fn(surf, cx, cy)
    rect = surf.get_bounding_rect(min_alpha=8)
    w, br, area = metrics(surf, rect)
    big = pygame.transform.scale(surf, (size * 1, size * 1))
    return big, rect, (w, br, area)


panels = []

# A. rig saja (badan mentah)
def draw_rig_only(surf, cx, cy):
    b = probe_boss()
    buf = pygame.Surface((G.RIG_W, G.RIG_H), pygame.SRCALPHA)
    G._draw_gnk_rig(buf, G.RIG_OX, G.RIG_OY, 1, 1.2, "idle", 0.0, False)
    ox, oy = int(cx) - G.RIG_OX, int(cy) - G.RIG_OY
    surf.blit(buf, (ox, oy))

panels.append(("A. rig SAJA (tanpa lighting/outline)", draw_rig_only))

# B. rig_at penuh (outline + lighting apply_to_rig)
def draw_rig_at(surf, cx, cy):
    b = probe_boss()
    G._draw_gnk_rig_at(surf, cx, cy, 1, 1.2, "idle", 0.0, False)

panels.append(("B. rig + outline + lighting.apply_to_rig", draw_rig_at))

# C. draw_gornak idle penuh
def draw_full(surf, cx, cy):
    b = probe_boss()
    b.x, b.y = float(cx), float(cy)
    G.draw_gornak(surf, b, cx, cy)

panels.append(("C. draw_gornak idle (penuh)", draw_full))

# D. penuh, lighting dimatikan
def draw_no_light(surf, cx, cy):
    b = probe_boss()
    b.x, b.y = float(cx), float(cy)
    saved = L._lighting
    L._lighting = None
    try:
        G.draw_gornak(surf, b, cx, cy)
    finally:
        L._lighting = saved

panels.append(("D. penuh TANPA lighting", draw_no_light))

# E. penuh, anti-magic field dimatikan
def draw_no_aura(surf, cx, cy):
    saved = G._draw_anti_magic_field
    G._draw_anti_magic_field = staticmethod(lambda *a, **k: None)
    try:
        b = probe_boss()
        b.x, b.y = float(cx), float(cy)
        G.draw_gornak(surf, b, cx, cy)
    finally:
        G._draw_anti_magic_field = saved

panels.append(("E. penuh TANPA anti-magic field", draw_no_aura))

# F. penuh + hurt flash maksimum
def draw_hurt(surf, cx, cy):
    b = probe_boss(hurt_flash_timer=8)
    b.x, b.y = float(cx), float(cy)
    G.draw_gornak(surf, b, cx, cy)

panels.append(("F. penuh + hurt_flash_timer=8", draw_hurt))

# G. lane hero (render_hero + cache)
def draw_hero_lane(surf, cx, cy):
    heroes.clear_hero_sprite_cache()
    h = _ProbeEntity("gornak", float(cx), float(cy))
    h.pulse = 1.2
    h.direction = 1
    heroes.render_hero("gornak", surf, h, cx, cy)

panels.append(("G. lane HERO render_hero (cache+_finish_hd)", draw_hero_lane))

rows = []
for name, fn in panels:
    img, rect, (white, bright, area) = render_cell(fn, name)
    rows.append((name, img, rect, white, bright, area))
    print("%-46s bbox=%-24s white>=235: %5d px  avg>=248: %5d px  area %d"
          % (name, rect, white, bright, area))

CW, CH = 252, 300
cols = 4
W = cols * CW + 20
H = ((len(rows) + cols - 1) // cols) * CH + 46
sheet = pygame.Surface((W, H))
sheet.fill(BG)
font = pygame.font.Font(None, 20)
sheet.blit(font.render(
    "GORNAK - isolasi lapisan: siapa yang menutupi karakter dengan cahaya "
    "putih?", True, (232, 206, 250)), (12, 12))
for i, (name, img, rect, white, bright, area) in enumerate(rows):
    x = 10 + (i % cols) * CW
    y = 40 + (i // cols) * CH
    pygame.draw.rect(sheet, (11, 10, 24), (x, y, CW - 8, CH - 8),
                     border_radius=6)
    pygame.draw.rect(sheet, (86, 52, 128), (x, y, CW - 8, CH - 8), 1,
                     border_radius=6)
    zimg = pygame.transform.scale(img, (img.get_width() * 1,
                                        img.get_height() * 1))
    # zoom 1.6x crop tengah supaya detail badan terlihat
    zw, zh = int(zimg.get_width() * 1.15), int(zimg.get_height() * 1.15)
    zimg = pygame.transform.scale(img, (zw, zh))
    sub = zimg.subsurface(
        pygame.Rect(0, 0, zw, zh)).copy() if zw and zh else zimg
    sheet.blit(sub, (x + (CW - 8 - zw) // 2 + 4, y + 6))
    sheet.blit(font.render(name, True, (232, 216, 255)), (x + 8, y + CH - 44))
    sheet.blit(font.render("white px: %d / %d (%.1f%%)" % (
        white, area, 100.0 * white / max(1, area)), True, (255, 226, 150)),
        (x + 8, y + CH - 26))

out = os.path.join(ROOT, "docs", "gornak_white_layers.png")
pygame.image.save(sheet, out)
print(out)
