#!/usr/bin/env python3
"""Render review sheet untuk Level 2 Procedural Masterwork.

Untuk tiap boss (razak, khalros, gorath, alchemist) menghasilkan satu sheet:
  docs/level2_<nama>_audit.png
berisi strip idle / walk / attack / Q / W / E / R pada KEDUA arah (kiri & kanan),
plus baris portrait HD.

Jalankan:  python3 tools/_shot_level2_masterwork.py
"""
import math
import os
import sys
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import bosses.level2 as L2

ACCENT = (232, 216, 255)
SUB = (150, 128, 178)
NOTE = (122, 104, 150)
PANEL = (11, 10, 24)
PANEL_EDGE = (86, 52, 128)
BG = (6, 7, 15)

NS = {
    "razak": (L2._NS_razak, L2.draw_razak),
    "khalros": (L2._NS_khalros, L2.draw_khalros),
    "gorath": (L2._NS_gorath, L2.draw_gorath),
    "alchemist": (L2._NS_alchemist, L2.draw_alchemist),
}

CELL = 150
COLS = ["IDLE", "WALK", "ATK-wind", "ATK-imp", "Q", "W", "E", "R"]


def probe(name, **kw):
    b = SimpleNamespace(boss_type=name, boss_class="mini", x=0.0, y=0.0,
                        direction=1, facing=1, pulse=1.2, timer=0,
                        attack_cooldown=40, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=34)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def setup(boss, col, ns):
    if col == "WALK":
        boss.pulse = 2.3
    elif col == "ATK-wind":
        setattr(boss, ns_prefix(boss) + "_attack_active", True)
        setattr(boss, ns_prefix(boss) + "_attack_progress", 0.15)
    elif col == "ATK-imp":
        setattr(boss, ns_prefix(boss) + "_attack_active", True)
        setattr(boss, ns_prefix(boss) + "_attack_progress", 0.6)
    elif col in ("Q", "W", "E", "R"):
        boss.active_skill = col.lower()
        boss.active_skill_timer = int(ns.SKILL_DUR[col.lower()] * 0.5)


def ns_prefix(boss):
    return {"razak": "_rz", "khalros": "_kh", "gorath": "_go",
            "alchemist": "_al"}[boss.boss_type]


font_title = pygame.font.Font(None, 40)
font_label = pygame.font.Font(None, 24)
font_small = pygame.font.Font(None, 18)

for name, (ns, fn) in NS.items():
    W = CELL * len(COLS) + 60
    H = CELL * 2 + 220
    sheet = pygame.Surface((W, H))
    sheet.fill(BG)
    sheet.blit(font_title.render(f"{name.upper()} - MASTERWORK", True, ACCENT),
               (24, 12))
    sheet.blit(font_small.render("baris atas: facing kanan (->)  ·  "
                                 "baris bawah: facing kiri (<-)", True, SUB),
               (26, 52))

    for row, facing in enumerate((1, -1)):
        top = 84 + row * (CELL + 40)
        for i, col in enumerate(COLS):
            cx = 40 + i * CELL + CELL // 2
            cy = top + CELL // 2 + 10
            b = probe(name, direction=facing)
            b.x, b.y = float(cx), float(cy)
            setup(b, col, ns)
            rect = pygame.Rect(40 + i * CELL, top, CELL - 8, CELL)
            pygame.draw.rect(sheet, PANEL, rect, border_radius=8)
            pygame.draw.rect(sheet, PANEL_EDGE, rect, 1, border_radius=8)
            fn(sheet, b, cx, cy)
            sheet.blit(font_label.render(col, True, (240, 240, 240)),
                       (rect.x + 6, rect.bottom - 24))

    # baris portrait HD
    top = 84 + 2 * (CELL + 40)
    sheet.blit(font_small.render("PORTRAIT HD (Hero Shop, tanpa aura):",
                                 True, SUB), (26, top - 4))
    for i, col in enumerate(("IDLE", "ATK-imp")):
        cx = 40 + i * CELL + CELL // 2
        cy = top + CELL // 2 + 10
        b = probe(name, direction=1, _portrait_hd=True)
        b.x, b.y = float(cx), float(cy)
        setup(b, col, ns)
        rect = pygame.Rect(40 + i * CELL, top, CELL - 8, CELL)
        pygame.draw.rect(sheet, PANEL, rect, border_radius=8)
        pygame.draw.rect(sheet, PANEL_EDGE, rect, 1, border_radius=8)
        fn(sheet, b, cx, cy)
        sheet.blit(font_label.render("HD:" + col, True, (240, 240, 240)),
                   (rect.x + 6, rect.bottom - 24))

    out = os.path.join(ROOT, "docs", f"level2_{name}_audit.png")
    pygame.image.save(sheet, out)
    print(out)
