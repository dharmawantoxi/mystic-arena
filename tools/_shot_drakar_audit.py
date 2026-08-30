#!/usr/bin/env python3
"""Render review sheet untuk Drakar (mini boss level 1) - kondisi KODE SAAT INI.

Menghasilkan:
  - tools/drakar_review_current.png  (idle/walk/attack + Q/W/E/R dari kode HEAD)

Jalankan:  python3 tools/_shot_drakar_audit.py
"""
import math
import os
import sys
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
from bosses import level1

BG = (7, 8, 16)
PANEL = (12, 13, 26)
PANEL_EDGE = (120, 60, 60)
ACCENT = (250, 160, 140)

CANVAS = 300
ANCHOR = (CANVAS // 2, CANVAS // 2 + 20)


def probe(cx=0.0, cy=0.0, **kw):
    b = SimpleNamespace(boss_type="drakar", boss_class="mini", x=float(cx),
                        y=float(cy), direction=1, facing=1, pulse=0.0,
                        timer=0, attack_cooldown=46, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=32,
                        hp=8000, max_hp=8000)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def frame(boss, zoom=2.0):
    surf = pygame.Surface((CANVAS, CANVAS))
    surf.fill((7, 8, 16))
    level1.draw_drakar(surf, boss, *ANCHOR)
    cw, ch = 200, 190
    crop = surf.subsurface(pygame.Rect(ANCHOR[0] - cw // 2,
                                       ANCHOR[1] - 120, cw, ch)).copy()
    return pygame.transform.scale(crop, (int(cw * zoom), int(ch * zoom)))


def body_bbox(boss):
    """Bbox piksel padat (alpha>=100) dari satu render 1x (canvas transparan
    supaya mask berarti; preview frame() pakai canvas opaque)."""
    surf = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)
    level1.draw_drakar(surf, boss, *ANCHOR)
    mask = pygame.mask.from_surface(surf, 100)
    rs = mask.get_bounding_rects()
    if not rs:
        return None
    x0 = min(r.x for r in rs)
    y0 = min(r.y for r in rs)
    x1 = max(r.right for r in rs)
    y1 = max(r.bottom for r in rs)
    return (x1 - x0, y1 - y0)


def attack_boss(progress, direction=1):
    cd = 46
    t = int(round((1.0 - progress) * (cd - 1)))
    b = probe(timer=t, direction=direction)
    b._drk_attack_active = True
    b._drk_attack_dir = direction
    b._drk_previous_timer = t + 1
    b._drk_attack_frame = int(progress * (cd - 1))
    return b


def walk_boss(pulse):
    b = probe(pulse=pulse)
    b._drk_last_x = b.x - 2.0   # supaya _detect_moving() True
    b._drk_last_y = b.y
    return b


def main():
    font = pygame.font.Font(None, 20)
    cols, rows = 6, 4
    pw, ph = 410, 400
    sheet = pygame.Surface((cols * pw + 8, rows * ph + 8))
    sheet.fill(BG)

    panels = [
        ("idle p=0.0", probe(pulse=0.0)),
        ("idle p=1.5", probe(pulse=1.5)),
        ("idle p=3.0", probe(pulse=3.0)),
        ("walk p=0.45", walk_boss(0.45)),
        ("walk p=1.2", walk_boss(1.2)),
        ("walk p=2.1", walk_boss(2.1)),

        ("attack 8% (crouch)", attack_boss(0.08)),
        ("attack 30% (windup)", attack_boss(0.30)),
        ("attack 50% (swing)", attack_boss(0.50)),
        ("attack 62% (impact)", attack_boss(0.62)),
        ("attack 85% (recover)", attack_boss(0.85)),
        ("attack 50% kiri", attack_boss(0.50, direction=-1)),

        ("Q Battle Hunger t=80", probe(active_skill="q",
                                       active_skill_timer=80, pulse=0.7)),
        ("Q t=45 (target ada)", probe(active_skill="q",
                                      active_skill_timer=45, pulse=0.7,
                                      target=SimpleNamespace(x=150.0, y=0.0,
                                                             alive=True))),
        ("Q Battle Hunger t=10", probe(active_skill="q",
                                       active_skill_timer=10, pulse=0.7)),
        ("W Counter Helix t=38", probe(active_skill="w",
                                       active_skill_timer=38, pulse=0.7)),
        ("W Counter Helix t=22", probe(active_skill="w",
                                       active_skill_timer=22, pulse=0.7)),
        ("W Counter Helix t=6", probe(active_skill="w",
                                      active_skill_timer=6, pulse=0.7)),

        ("E Berserker's Call t=55", probe(active_skill="e",
                                          active_skill_timer=55, pulse=0.7)),
        ("E Berserker's Call t=30", probe(active_skill="e",
                                          active_skill_timer=30, pulse=0.7)),
        ("E Berserker's Call t=8", probe(active_skill="e",
                                         active_skill_timer=8, pulse=0.7)),
        ("R Culling Blade t=55", probe(active_skill="r",
                                       active_skill_timer=55, pulse=0.7)),
        ("R Culling Blade t=32", probe(active_skill="r",
                                       active_skill_timer=32, pulse=0.7)),
        ("R Culling Blade t=10", probe(active_skill="r",
                                       active_skill_timer=10, pulse=0.7)),
    ]

    for i, (title, boss) in enumerate(panels):
        col, row = i % cols, i // cols
        x, y = 8 + col * pw, 8 + row * ph
        pygame.draw.rect(sheet, PANEL_EDGE, (x, y, pw - 8, ph - 8), 1)
        pygame.draw.rect(sheet, PANEL, (x + 1, y + 1, pw - 10, ph - 10))
        sheet.blit(font.render(title, True, ACCENT), (x + 8, y + 6))
        img = frame(boss)
        sheet.blit(img, (x + (pw - 8) // 2 - img.get_width() // 2,
                         y + (ph - 8) // 2 - img.get_height() // 2 + 16))

    out = os.path.join(ROOT, "tools", "drakar_review_current.png")
    pygame.image.save(sheet, out)
    print("saved", out)

    bb = body_bbox(probe(pulse=0.7))
    print("bbox padat (alpha>=100) idle: W=%s H=%s" % (bb[0], bb[1]))
    bbw = body_bbox(walk_boss(1.2))
    print("bbox padat walk: W=%s H=%s" % (bbw[0], bbw[1]))
    bba = body_bbox(attack_boss(0.5))
    print("bbox padat attack 50%%: W=%s H=%s" % (bba[0], bba[1]))


if __name__ == "__main__":
    main()
