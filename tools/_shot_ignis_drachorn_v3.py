#!/usr/bin/env python3
"""Preview generator Ignis Drachorn V3 (renderer + live combat-FX engine).

Menghasilkan:
  * docs/ignis_drachorn_v3_preview.png     - contact sheet pose + 4 skill
  * docs/ignis_drachorn_v3_swing_strip.png - filmstrip ayunan ARK 0..1

Jalankan:
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
      python3 tools/_shot_ignis_drachorn_v3.py
"""
import os
import sys
import time
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import bosses.level4 as L
from heroes import ignis_drachorn_fx as F

NS = L._NS_ignis_drachorn

CELL = 210
PAD = 6
BG = (26, 20, 24)
CX, CY = 105, 132
SKILL_DUR = {"q": 45, "w": 40, "e": 60, "r": 90}


def make_boss(skill=None, timer=0, cd=50):
    """Boss dengan koordinat dunia == koordinat sel supaya FX hidup
    (yang memakai hero.x/y) jatuh tepat di dalam bingkai."""
    return SimpleNamespace(
        boss_type="ignis_drachorn", boss_class="true", x=float(CX),
        y=float(CY), direction=1, facing=1, pulse=1.2, timer=0,
        attack_cooldown=cd, active_skill=skill, active_skill_timer=timer,
        target=SimpleNamespace(x=float(CX + 82), y=float(CY), alive=True,
                               radius=12),
        hurt_flash_timer=0, alive=True, radius=35, hp=9000, max_hp=9000,
        range=150, speed=1.0, attack_range=150)


def label(sheet, text, col, row, font):
    s = font.render(text, True, (255, 214, 160))
    sheet.blit(s, (PAD + col * (CELL + PAD) + 6,
                   PAD + row * (CELL + PAD) + 4))


def render(sheet, boss, col, row, pre_ticks=0):
    for _ in range(pre_ticks):
        F.tick(1.0 / 60.0)
    sub = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    L.draw_ignis_drachorn(sub, boss, CX, CY)
    sheet.blit(sub, (PAD + col * (CELL + PAD), PAD + row * (CELL + PAD)))
    time.sleep(0.001)


def render_skill(sheet, skill, timer, col, row):
    b = make_boss(skill=skill, timer=timer)
    F.notify_skill_cast(b, skill)
    aim_x = CX + 82 if skill in ("q", "w") else CX
    F.notify_skill_impact(b, aim_x, CY, F.WORLD_RADIUS[skill], skill)
    render(sheet, b, col, row, pre_ticks=max(0, SKILL_DUR[skill] - timer))


def contact_sheet():
    font = pygame.font.Font(None, 20)
    cols, rows = 4, 2
    sheet = pygame.Surface((PAD + cols * (CELL + PAD),
                            PAD + rows * (CELL + PAD)))
    sheet.fill(BG)

    F.reset_all()
    render(sheet, make_boss(), 0, 0, pre_ticks=30)
    label(sheet, "IDLE", 0, 0, font)

    walk = make_boss()
    for i in range(8):
        walk.x = CX + i * 0.9
        walk.pulse += 0.2
        render(sheet, walk, 1, 0, pre_ticks=3)
    label(sheet, "WALK", 1, 0, font)

    atk = make_boss()
    atk._ign_attack_manual = True
    atk._ign_attack_active = True
    atk._ign_attack_frame = 24
    for p in (0.30, 0.38, 0.44, 0.48):
        atk._ign_attack_progress = p
        render(sheet, atk, 2, 0, pre_ticks=2)
    label(sheet, "SWING / IMPACT", 2, 0, font)

    rng = make_boss()
    rng.attack_range = 260
    rng._ign_attack_manual = True
    rng._ign_attack_active = True
    for p in (0.34, 0.40, 0.46, 0.52, 0.60):
        rng._ign_attack_progress = p
        render(sheet, rng, 3, 0, pre_ticks=3)
    label(sheet, "FIRE ORB", 3, 0, font)

    for i, (sk, t) in enumerate((("q", 22), ("w", 20), ("e", 30),
                                 ("r", 50))):
        render_skill(sheet, sk, t, i, 1)
        label(sheet, "SKILL " + sk.upper(), i, 1, font)

    out = os.path.join(ROOT, "docs", "ignis_drachorn_v3_preview.png")
    pygame.image.save(sheet, out)
    print("tulis", out)
    F.reset_all()


def swing_strip():
    font = pygame.font.Font(None, 18)
    n = 9
    W, H = 150, 190
    strip = pygame.Surface((n * W, H + 18))
    strip.fill(BG)
    F.reset_all()
    b = make_boss()
    b._ign_attack_manual = True
    b._ign_attack_active = True
    for i in range(n):
        p = i / float(n - 1)
        b._ign_attack_progress = p
        b._ign_attack_frame = int(p * 50)
        sub = pygame.Surface((W, H), pygame.SRCALPHA)
        b.x, b.y = float(W // 2), 118.0
        F.tick(1.0 / 60.0)
        L.draw_ignis_drachorn(sub, b, W // 2, 118)
        strip.blit(sub, (i * W, 0))
        strip.blit(font.render("%.2f %s" % (p, NS.attack_phase(p)),
                               True, (255, 214, 160)), (i * W + 4, H + 2))
        time.sleep(0.001)
    out = os.path.join(ROOT, "docs", "ignis_drachorn_v3_swing_strip.png")
    pygame.image.save(strip, out)
    print("tulis", out)
    F.reset_all()


if __name__ == "__main__":
    contact_sheet()
    swing_strip()
