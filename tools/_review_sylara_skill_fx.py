#!/usr/bin/env python3
"""Lembar review visual Skill FX Sylara (zoom 2x + simulasi skala in-game).

Membuat:
  - docs/sylara_skill_fx_review.png    4 skill x 4 fase, zoom 2x (pipeline)
  - docs/sylara_skill_fx_ingame.png    4 skill x 2 fase, lewat render_hero
                                        (cache + smoothscale + outline asli)

Jalankan: SDL_VIDEODRIVER=dummy python3 tools/_review_sylara_skill_fx.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import math
import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import heroes
from heroes import _ProbeEntity, render_hero
from heroes._bundle import _NS_sylara as Z

DOCS = os.path.join(ROOT, "docs")
os.makedirs(DOCS, exist_ok=True)

BG = (8, 12, 18)
ACC = (120, 210, 120)
WH = (235, 245, 235)


def font(sz):
    try:
        return pygame.font.Font(None, sz)
    except Exception:
        return pygame.font.Font(None, 24)


def label(surf, text, x, y, sz=20, color=WH):
    f = font(sz)
    t = f.render(text, True, color)
    surf.blit(t, (x, y))
    return t.get_height()


def make_hero(canvas, skill, timer, tx=300, ty=202):
    h = _ProbeEntity("sylara", canvas // 2, canvas // 2)
    h.pulse = 1.0
    h.direction = h.facing = 1
    h.active_skill = skill
    h.active_skill_timer = timer
    h._render_scale = 0.45
    h.range = 200
    h.skill_range = 200
    h.target = _ProbeEntity("dummy", tx, ty)
    h.target.alive = True
    return h


def render_pipeline(skill, timer, size=400, zoom=2):
    """Persis jalur canvas renderer (sebelum crop/scale pipeline)."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    try:
        Z.draw_sylara(s, make_hero(size, skill, timer), size // 2, size // 2)
    except Exception as e:
        print(f"  [WARN] {skill}/{timer}: {e}")
    return pygame.transform.scale(s, (size * zoom, size * zoom))


def render_ingame(skill, timer, pad_zone=400):
    """Persis yang dikirim ke layar: render_hero (cache+smoothscale+outline)."""
    screen = pygame.Surface((900, 900))
    # tanah gelap sederhana supaya kontras efek kebaca
    screen.fill((16, 22, 20))
    for gx in range(0, 900, 60):
        for gy in range(0, 900, 60):
            pygame.draw.line(screen, (22, 30, 26), (gx, 0), (gx, 900), 1)
            pygame.draw.line(screen, (22, 30, 26), (0, gy), (900, gy), 1)
    h = _ProbeEntity("sylara", 450, 460)
    h.pulse = 1.0
    h.direction = h.facing = 1
    h.active_skill = skill
    h.active_skill_timer = timer
    h.range = 200
    h.skill_range = 200
    h.target = _ProbeEntity("dummy", 620, 470)
    h.target.alive = True
    render_hero("sylara", screen, h, 450, 460)
    crop = screen.subsurface((450 - pad_zone // 2, 460 - pad_zone // 2,
                              pad_zone, pad_zone)).copy()
    return crop


SKILLS = [
    ("Q  FOCUS FIRE", "q", [176, 130, 80, 30]),
    ("W  WINDRUN", "w", [174, 130, 70, 25]),
    ("E  SHACKLE SHOT", "e", [146, 105, 55, 25]),
    ("R  POWERSHOT", "r", [58, 44, 32, 16]),
]
PHASES = ["AKTIVASI", "STEADY A", "STEADY B", "TELEGRAPH"]

# ── Sheet 1: pipeline zoom 2x ────────────────────────────────────────────────
PANEL = 800
PAD = 14
W = 30 + 4 * PANEL + 5 * PAD + 70
H = 90 + 4 * (PANEL + 70) + PAD
sheet = pygame.Surface((W, H))
sheet.fill(BG)
label(sheet, "SYLARA — SKILL FX (pipeline canvas, zoom 2x, _render_scale=0.45)",
      24, 18, 34, (185, 255, 195))
for row, (name, key, timers) in enumerate(SKILLS):
    ry = 78 + row * (PANEL + 74)
    label(sheet, name, 26, ry + 6, 26, (215, 255, 220))
    for col, timer in enumerate(timers):
        px = 30 + PAD + col * (PANEL + PAD) + 70
        sr = render_pipeline(key, timer)
        sheet.blit(sr, (px, ry))
        pygame.draw.rect(sheet, (60, 130, 70), (px, ry, PANEL, PANEL), 2)
        label(sheet, f"{PHASES[col]}  (t={timer})", px + 8, ry + PANEL + 8,
              20, (170, 220, 180))
pygame.image.save(sheet, os.path.join(DOCS, "sylara_skill_fx_review.png"))
print(f"[SAVED] docs/sylara_skill_fx_review.png ({W}x{H})")

# ── Sheet 2: in-game (render_hero asli) ──────────────────────────────────────
PANEL2 = 600
W2 = 30 + 4 * PANEL2 + 5 * PAD + 70
H2 = 90 + 4 * (PANEL2 + 60) + PAD
ig = pygame.Surface((W2, H2))
ig.fill(BG)
label(ig, "SYLARA — SKILL FX IN-GAME (render_hero asli: cache + smoothscale)",
      24, 18, 34, (185, 255, 195))
for row, (name, key, timers) in enumerate(SKILLS):
    ry = 78 + row * (PANEL2 + 64)
    label(ig, name, 26, ry + 6, 26, (215, 255, 220))
    for col, timer in enumerate(timers[:2]):
        px = 30 + PAD + col * (PANEL2 + PAD) + 70
        # crop 400px dunia -> tampil 600px (1.5x) supaya terlihat jelas
        crop = render_ingame(key, timer)
        ig.blit(pygame.transform.scale(crop, (600, 600)), (px, ry))
        pygame.draw.rect(ig, (60, 130, 70), (px, ry, PANEL2, PANEL2), 2)
        label(ig, f"{PHASES[col]}  (t={timer})", px + 8, ry + PANEL2 + 8,
              20, (170, 220, 180))
pygame.image.save(ig, os.path.join(DOCS, "sylara_skill_fx_ingame.png"))
print(f"[SAVED] docs/sylara_skill_fx_ingame.png ({W2}x{H2})")
