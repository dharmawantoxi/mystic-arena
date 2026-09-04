#!/usr/bin/env python3
"""Penjaga regresi: FX skill Razak tidak boleh menutupi badannya dengan putih.

Panel: Q/W/E/R pada beberapa fase cast + hit flash. Metrik: piksel sangat
terang (min(r,g,b) >= 235) di dalam bbox badan.
Jalankan: python3 tools/_shot_razak_combat_white.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402
import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes  # noqa: E402
from heroes import _ProbeEntity  # noqa: E402
from heroes import razak_fx as F  # noqa: E402
from bosses.level2 import _NS_razak as R  # noqa: E402

DT = 1.0 / 60.0
BG = (14, 8, 8)


def hero_at(x, y, **kw):
    h = _ProbeEntity("razak", x, y)
    h.boss_type = "razak"
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = 45
    h.timer = 0
    h.hp = h.max_hp = 900
    h.radius = 16
    h.hurt_flash_timer = 0
    for k, v in kw.items():
        setattr(h, k, v)
    return h


def white_metrics(surf, rect):
    if rect.width <= 0:
        return 0, 0.0
    sub = surf.subsurface(rect)
    px = pygame.surfarray.array3d(sub).astype(np.int32)
    al = pygame.surfarray.array_alpha(sub)
    solid = al >= 90
    mn = px.min(axis=2)
    white = int(((mn >= 235) & solid).sum())
    tot = int(solid.sum())
    return white, (100.0 * white / max(1, tot))


def body_rect(cx, cy):
    return pygame.Rect(cx - 34, cy - 62, 68, 78)


def scene_skill(skill, timer):
    size = 320
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2 + 30
    F.reset_all()
    h = hero_at(float(cx), float(cy), active_skill=skill,
                active_skill_timer=timer)
    h.target = _ProbeEntity("dummy", float(cx + 90), float(cy - 10))
    h.target.alive = True
    F.attach(h)
    steps = max(0, F.SKILL_DUR[skill] - timer)
    for _ in range(steps):
        F.tick(DT)
    R.draw_razak(surf, h, cx, cy)
    F.reset_all()
    return surf, body_rect(cx, cy)


def scene_boss_hurt(frames):
    """Lane boss: hurt_flash_timer aktif (flash siluet di canvas)."""
    size = 320
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2 + 30
    F.reset_all()
    h = hero_at(float(cx), float(cy), hurt_flash_timer=frames)
    F.attach(h)
    d = F.director_for(h)
    d.on_hurt(0.2)
    F.tick(0.0001)
    d.hit_flash = 0.16
    R.draw_razak(surf, h, cx, cy)
    F.reset_all()
    return surf, body_rect(cx, cy)


def scene_hit_flash(k):
    size = 320
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2 + 30
    F.reset_all()
    h = hero_at(float(cx), float(cy))
    F.attach(h)
    d = F.director_for(h)
    d.on_hurt(0.2)
    F.tick(0.0001)
    d.hit_flash = 0.16 * k
    R.draw_razak(surf, h, cx, cy)
    F.reset_all()
    return surf, body_rect(cx, cy)


PANELS = []
for sk in ("q", "w", "e", "r"):
    dur = F.SKILL_DUR[sk]
    for frac in (0.02, 0.06, 0.12, 0.3, 0.6):
        t = int(dur * (1.0 - frac))
        PANELS.append(("%s prog~%.2f" % (sk.upper(), frac),
                       (lambda s=sk, tt=t: scene_skill(s, tt))))
PANELS.append(("HIT FLASH k=1.0", lambda: scene_hit_flash(1.0)))
PANELS.append(("HIT FLASH k=0.5", lambda: scene_hit_flash(0.5)))
PANELS.append(("BOSS HURT flash=8", lambda: scene_boss_hurt(8)))
PANELS.append(("BOSS HURT flash=4", lambda: scene_boss_hurt(4)))

rows = []
for name, fn in PANELS:
    surf, rect = fn()
    w, pct = white_metrics(surf, rect)
    rows.append((name, surf, rect, w, pct))
    print("%-22s white px: %5d  (%.1f%% badan)" % (name, w, pct))

CW, CH = 300, 340
cols = 4
rows_n = (len(rows) + cols - 1) // cols
sheet = pygame.Surface((cols * CW + 20, rows_n * CH + 50))
sheet.fill(BG)
font = pygame.font.Font(None, 20)
sheet.blit(font.render("RAZAK - FX skill vs keterbacaan badan", True,
                       (250, 214, 180)), (12, 12))
for i, (name, surf, rect, w, pct) in enumerate(rows):
    x = 10 + (i % cols) * CW
    y = 44 + (i // cols) * CH
    pygame.draw.rect(sheet, (24, 12, 10), (x, y, CW - 8, CH - 8),
                     border_radius=6)
    z = 2.6
    big = pygame.transform.scale(surf, (int(surf.get_width() * z),
                                        int(surf.get_height() * z)))
    cw2, ch2 = CW - 16, CH - 62
    crop = pygame.Surface((cw2, ch2))
    ox = (big.get_width() - cw2) // 2
    oy = (big.get_height() - ch2) // 2 + 20
    crop.blit(big, (0, 0), (ox, oy, cw2, ch2))
    sheet.blit(crop, (x + 8, y + 6))
    sheet.blit(font.render(name, True, (250, 226, 205)), (x + 8, y + CH - 48))
    sheet.blit(font.render("white px: %d (%.1f%%)" % (w, pct), True,
                           (255, 226, 150)), (x + 8, y + CH - 28))

out = os.path.join(ROOT, "docs", "razak_combat_white.png")
pygame.image.save(sheet, out)
print(out)
