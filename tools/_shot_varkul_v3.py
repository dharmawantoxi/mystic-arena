#!/usr/bin/env python3
"""Preview generator Varkul V3 (renderer + live combat-FX engine).

Menghasilkan:
  * docs/varkul_v3_preview.png     - contact sheet pose + 4 skill
  * docs/varkul_v3_swing_strip.png - filmstrip ayunan ark staff 0..1

Jalankan: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/_shot_varkul_v3.py
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

import bosses.level3 as L
from heroes import varkul_fx as F

CELL = 190
PAD = 6
BG = (24, 26, 40)
CX, CY = 95, 118                     # jangkar gambar di dalam sel
SKILL_TOTAL = {"q": 50, "w": 60, "e": 50, "r": 80}


def make_boss(skill=None, timer=0, cd=42):
    """Boss dengan koordinat dunia == koordinat sel supaya FX hidup
    (yang memakai hero.x/y) jatuh tepat di dalam bingkai."""
    b = SimpleNamespace(
        boss_type="varkul", boss_class="mini", x=float(CX), y=float(CY),
        direction=1, facing=1, pulse=1.2, timer=0, attack_cooldown=cd,
        active_skill=skill, active_skill_timer=timer,
        target=SimpleNamespace(x=float(CX + 78), y=float(CY), alive=True,
                               radius=12),
        hurt_flash_timer=0, alive=True, radius=35,
        hp=7500, max_hp=7500, range=100)
    return b


def render(sheet, boss, col, row, pre_ticks=0):
    # majukan jam FX hidup dulu supaya skill/proyektil terlihat
    for _ in range(pre_ticks):
        F.tick(1.0 / 60.0)
    sub = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    L.draw_varkul(sub, boss, CX, CY)
    sheet.blit(sub, (PAD + col * (CELL + PAD), PAD + row * (CELL + PAD)))
    time.sleep(0.001)


def render_skill(sheet, skill, timer, col, row):
    """Sel skill: picu FX via jalur AI (cast+impact) lalu majukan jam
    sampai fase yang sesuai timer."""
    b = make_boss(skill=skill, timer=timer)
    F.notify_skill_cast(b, skill)
    aim_x = CX + 78 if skill in ("q", "w") else CX
    F.notify_skill_impact(b, aim_x, CY, {"q": 54, "w": 34, "e": 95,
                                         "r": 120}[skill], skill)
    ticks = SKILL_TOTAL[skill] - max(0, timer)
    render(sheet, b, col, row, pre_ticks=max(0, ticks))


def swing_boss(progress):
    """Boss pada progress serangan tertentu (mode probe manual)."""
    b = make_boss()
    b._vk_attack_active = True
    b._vk_attack_frame = int(progress * 42)
    b._vk_attack_progress = progress
    b._vk_attack_phase = L._NS_varkul.attack_phase(progress)
    b._vk_previous_timer = 99
    return b


def main():
    cols, rows = 6, 4
    W = 2 * PAD + cols * (CELL + PAD)
    H = 2 * PAD + rows * (CELL + PAD)
    sheet = pygame.Surface((W, H), pygame.SRCALPHA)
    sheet.fill(BG)

    # ── baris 0: idle | walk | hurt | cast R | windup | impact ──────
    b = make_boss()
    for _ in range(4):
        render(sheet, b, 0, 0)
    bw = make_boss()
    for _ in range(3):
        bw.x += 1.2
        render(sheet, bw, 1, 0)
    bh = make_boss()
    bh.hurt_flash_timer = 6
    render(sheet, bh, 2, 0)
    render_skill(sheet, "r", 30, 3, 0)
    render(sheet, swing_boss(0.24), 4, 0)
    render(sheet, swing_boss(0.52), 5, 0)

    # ── baris 1: filmstrip ayunan ark (progress 0 .. 1) ─────────────
    for i, p in enumerate((0.0, 0.18, 0.32, 0.42, 0.52, 0.72)):
        render(sheet, swing_boss(p), i, 1)

    # ── baris 2: Q Frost Blast (4 fase) | W Frostbite (2 fase) ──────
    for i, timer in enumerate((10, 22, 34, 44)):
        render_skill(sheet, "q", timer, i, 2)
    render_skill(sheet, "w", 12, 4, 2)
    render_skill(sheet, "w", 44, 5, 2)

    # ── baris 3: E Sacrifice (4 fase) | R Chain Frost (2 fase) ──────
    for i, timer in enumerate((8, 20, 34, 46)):
        render_skill(sheet, "e", timer, i, 3)
    render_skill(sheet, "r", 10, 4, 3)
    render_skill(sheet, "r", 44, 5, 3)

    pygame.image.save(sheet, os.path.join(ROOT, "docs",
                                          "varkul_v3_preview.png"))
    print("saved docs/varkul_v3_preview.png", sheet.get_size())
    F.reset_all()

    # ── strip ayunan halus (14 langkah) ─────────────────────────────
    steps = 14
    strip = pygame.Surface((PAD + steps * (CELL + PAD), CELL + 2 * PAD),
                           pygame.SRCALPHA)
    strip.fill(BG)
    for i in range(steps):
        p = i / float(steps - 1)
        sb = swing_boss(p)
        # dorong swing-start supaya trail hidup ikut terlihat
        F.attach(sb)
        d = F.director_for(sb)
        d.on_swing_start(sb.x, sb.y, 1)
        for _ in range(6):
            _g, tip = F.staff_points(sb, sb.x, sb.y, False)
            d.trail.push(tip[0] - (6 - i), tip[1], 1)
        sub = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        L.draw_varkul(sub, sb, CX, CY)
        strip.blit(sub, (PAD + i * (CELL + PAD), PAD))
        time.sleep(0.001)
    pygame.image.save(strip, os.path.join(ROOT, "docs",
                                          "varkul_v3_swing_strip.png"))
    print("saved docs/varkul_v3_swing_strip.png", strip.get_size())
    F.reset_all()


if __name__ == "__main__":
    main()
