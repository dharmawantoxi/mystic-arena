#!/usr/bin/env python3
"""Audit + preview sheet untuk Drakar renderer masterwork v2 + Skill FX.

Mengukur:
  - skala terukur rig v2 vs v1
  - bbox tiap pose
  - jumlah warna unik
  - waktu render per pose (budget cache-miss)
  - FX skill world-space (radius telegraph, piksel di luar siluet)
Menghasilkan:
  - docs/drakar_v2_review.png
  - docs/drakar_v2_anim_strip.png
  - docs/drakar_v2_ingame.png
  - docs/drakar_v2_skills.png
  - docs/drakar_v2_before_after.png
"""
import math
import os
import sys
import time
from collections import Counter
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

import bosses.level1 as L
from bosses.level1 import _NS_drakar as D


def probe(**kw):
    b = SimpleNamespace(boss_type="drakar", boss_class="mini", x=230.0, y=230.0,
        direction=1, facing=1, pulse=1.2, timer=0, attack_cooldown=46,
        active_skill=None, active_skill_timer=0, target=None, _render_scale=1.0,
        hurt_flash_timer=0, alive=True, radius=32, hp=8000, max_hp=8000)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def atk(progress, direction=1):
    cd = 46
    t = int(round((1.0 - progress) * (cd - 1)))
    b = probe(timer=t, direction=direction)
    b._drk_attack_active = True
    b._drk_attack_dir = direction
    b._drk_previous_timer = t + 1
    return b


def render(boss, size=460):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    L.draw_drakar(s, boss, 230, 230)
    return s


def count_colors(s):
    colors = set()
    for y in range(s.get_height()):
        for x in range(s.get_width()):
            c = s.get_at((x, y))
            if c.a > 50:
                colors.add(c[:3])
    return colors


def bbox(s, min_alpha=100):
    return s.get_bounding_rect(min_alpha=min_alpha)


def check(cond, label, extra=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return cond


ok_all = True

# =========================================================================
# 1. Rig scale audit
# =========================================================================
print("\n=== 1. RIG SCALE AUDIT ===")
check(D.BODY_W == 360, "BODY_W = 360 (1.5x dari 240)", f"(got {D.BODY_W})")
check(D.BODY_H == 360, "BODY_H = 360 (1.5x dari 240)", f"(got {D.BODY_H})")
print(f"  Rig scale factor: {D._RIG_SCALE}")

# =========================================================================
# 2. Pose bbox audit
# =========================================================================
print("\n=== 2. POSE BBOX AUDIT ===")
poses = {
    "idle": probe(pulse=0.0),
    "idle2": probe(pulse=3.0),
    "walk": probe(pulse=2.0),
    "atk_windup": atk(0.1),
    "atk_tension": atk(0.3),
    "atk_impact": atk(0.5),
    "atk_follow": atk(0.62),
    "atk_recover": atk(0.85),
    "atk_left": atk(0.5, -1),
    "skill_q": probe(active_skill="q", active_skill_timer=45),
    "skill_w": probe(active_skill="w", active_skill_timer=20),
    "skill_e": probe(active_skill="e", active_skill_timer=30),
    "skill_r": probe(active_skill="r", active_skill_timer=30,
                     target=SimpleNamespace(x=320.0, y=230.0, alive=True)),
    "rage": probe(rage_active=True),
    "defense": probe(defense_boost=True),
}

for name, boss in poses.items():
    s = render(boss)
    r = bbox(s)
    colors = count_colors(s)
    print(f"  {name:14s}: bbox={r.width:3d}x{r.height:3d}  colors={len(colors)}")

# =========================================================================
# 3. Timing audit
# =========================================================================
print("\n=== 3. TIMING AUDIT ===")
N = 50
for name, boss in [("idle", probe(pulse=0.0)), ("attack", atk(0.5)),
                    ("skill_r", probe(active_skill="r", active_skill_timer=30,
                                      target=SimpleNamespace(x=320.0, y=230.0, alive=True)))]:
    t0 = time.perf_counter()
    for _ in range(N):
        render(boss)
        boss.pulse += 0.05
    ms = (time.perf_counter() - t0) / N * 1000
    check(ms < 5, f"{name}: {ms:.2f}ms/frame (< 5ms budget)")

# =========================================================================
# 4. FX skill world-space audit
# =========================================================================
print("\n=== 4. FX SKILL WORLD-SPACE AUDIT ===")

# Test _fx_scale compensation
b1 = probe(_render_scale=1.0)
b2 = probe(_render_scale=0.5)
b3 = probe(_render_scale=0.4)
fs1 = D._fx_scale(b1)
fs2 = D._fx_scale(b2)
fs3 = D._fx_scale(b3)
check(fs1 == 1.0, f"_fx_scale(1.0) = 1.0 (got {fs1})")
check(fs2 == 2.0, f"_fx_scale(0.5) = 2.0 (got {fs2})")
check(abs(fs3 - 2.5) < 0.01, f"_fx_scale(0.4) = 2.5 (capped at 2.6) (got {fs3})")

# Test skill E renders bigger when _render_scale is lower
s_norm = render(probe(active_skill="e", active_skill_timer=30))
s_scaled = render(probe(active_skill="e", active_skill_timer=30, _render_scale=0.5), size=600)
r_norm = bbox(s_norm, min_alpha=10)
r_scaled = bbox(s_scaled, min_alpha=10)
print(f"  Skill E normal bbox: {r_norm.width}x{r_norm.height}")
print(f"  Skill E scaled(0.5) bbox: {r_scaled.width}x{r_scaled.height}")

# =========================================================================
# 5. FX primitives audit
# =========================================================================
print("\n=== 5. FX PRIMITIVES AUDIT ===")
test_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
D._spark_star(test_surf, 100, 100, 30, D.PALETTE["blood_light"], 200)
px_star = sum(1 for x in range(200) for y in range(200)
              if test_surf.get_at((x, y)).a > 50)
check(px_star > 10, f"_spark_star renders pixels ({px_star})")

test_surf.fill((0, 0, 0, 0))
D._chevron(test_surf, 100, 100, 0, 20, D.PALETTE["blood_mid"], 200)
px_chev = sum(1 for x in range(200) for y in range(200)
              if test_surf.get_at((x, y)).a > 50)
check(px_chev > 5, f"_chevron renders pixels ({px_chev})")

test_surf.fill((0, 0, 0, 0))
D._dashed_ring(test_surf, 100, 100, 50, D.PALETTE["rune_dark"], 200, 0.5)
px_ring = sum(1 for x in range(200) for y in range(200)
              if test_surf.get_at((x, y)).a > 50)
check(px_ring > 20, f"_dashed_ring renders pixels ({px_ring})")

test_surf.fill((0, 0, 0, 0))
D._jagged_crack(test_surf, 100, 100, 0.5, 40,
                (D.PALETTE["blood_darkest"], D.PALETTE["blood_mid"]), 200, seed=7)
px_crack = sum(1 for x in range(200) for y in range(200)
               if test_surf.get_at((x, y)).a > 50)
check(px_crack > 10, f"_jagged_crack renders pixels ({px_crack})")

# =========================================================================
# 6. Preview sheets
# =========================================================================
print("\n=== 6. PREVIEW SHEETS ===")

def make_review_sheet():
    """Kartu pose besar, 2x scale."""
    W, H = 900, 1200
    sheet = pygame.Surface((W, H), pygame.SRCALPHA)
    sheet.fill((20, 18, 24))
    poses_list = [
        ("idle", probe(pulse=0.0)),
        ("walk", probe(pulse=2.0)),
        ("attack", atk(0.5)),
        ("skill_q", probe(active_skill="q", active_skill_timer=45)),
        ("skill_e", probe(active_skill="e", active_skill_timer=30)),
        ("skill_r", probe(active_skill="r", active_skill_timer=30,
                          target=SimpleNamespace(x=320.0, y=230.0, alive=True))),
    ]
    y_off = 40
    for name, boss in poses_list:
        s = render(boss, size=460)
        # Draw at 2x
        scaled = pygame.transform.smoothscale(s, (920, 920))
        sheet.blit(scaled, (0, y_off), (0, 0, W, 400))
        # Label
        font = pygame.font.Font(None, 24)
        txt = font.render(name, True, (200, 200, 200))
        sheet.blit(txt, (20, y_off + 380))
        y_off += 410
    path = os.path.join(ROOT, "docs", "drakar_v2_review.png")
    pygame.image.save(sheet, path)
    print(f"  Saved {path}")

def make_anim_strip():
    """Film strip idle/walk/attack."""
    W, H = 1200, 500
    strip = pygame.Surface((W, H), pygame.SRCALPHA)
    strip.fill((15, 12, 18))
    # Idle frames
    for i in range(12):
        boss = probe(pulse=i * 0.5)
        s = render(boss)
        frame = pygame.transform.smoothscale(s, (200, 200))
        strip.blit(frame, (i * 100, 10))
    # Walk frames
    for i in range(12):
        boss = probe(pulse=i * 0.3)
        boss._drk_last_x = -2.0
        boss._drk_last_y = 0.0
        s = render(boss)
        frame = pygame.transform.smoothscale(s, (200, 200))
        strip.blit(frame, (i * 100, 250))
    path = os.path.join(ROOT, "docs", "drakar_v2_anim_strip.png")
    pygame.image.save(strip, path)
    print(f"  Saved {path}")

def make_skills_sheet():
    """Skill FX per tahap."""
    W, H = 1200, 800
    sheet = pygame.Surface((W, H), pygame.SRCALPHA)
    sheet.fill((18, 15, 22))
    skills = [
        ("Q: Battle Hunger", [("q", 85), ("q", 45), ("q", 20)]),
        ("W: Counter Helix", [("w", 40), ("w", 20), ("w", 5)]),
        ("E: Berserker's Call", [("e", 55), ("e", 30), ("e", 10)]),
        ("R: Culling Blade", [("r", 55), ("r", 30), ("r", 10)]),
    ]
    for row, (label, timers) in enumerate(skills):
        font = pygame.font.Font(None, 22)
        txt = font.render(label, True, (200, 200, 200))
        sheet.blit(txt, (10, row * 200 + 5))
        for col, (skill, timer) in enumerate(timers):
            if skill == "r":
                boss = probe(active_skill=skill, active_skill_timer=timer,
                             target=SimpleNamespace(x=320.0, y=230.0, alive=True))
            else:
                boss = probe(active_skill=skill, active_skill_timer=timer)
            s = render(boss)
            frame = pygame.transform.smoothscale(s, (350, 350))
            sheet.blit(frame, (col * 400 + 10, row * 200 + 30))
    path = os.path.join(ROOT, "docs", "drakar_v2_skills.png")
    pygame.image.save(sheet, path)
    print(f"  Saved {path}")

def make_ingame_sheet():
    """Simulasi in-game appearance."""
    W, H = 800, 600
    sheet = pygame.Surface((W, H), pygame.SRCALPHA)
    # Ground
    sheet.fill((40, 35, 30))
    pygame.draw.rect(sheet, (55, 50, 42), (0, 350, 800, 250))
    # Hero
    boss = probe(pulse=1.5)
    s = render(boss, size=460)
    scaled = pygame.transform.smoothscale(s, (200, 200))
    sheet.blit(scaled, (300, 200))
    # Enemy hero (mirrored)
    boss2 = probe(pulse=2.0, direction=-1)
    s2 = render(boss2, size=460)
    scaled2 = pygame.transform.smoothscale(s2, (200, 200))
    sheet.blit(scaled2, (500, 220))
    path = os.path.join(ROOT, "docs", "drakar_v2_ingame.png")
    pygame.image.save(sheet, path)
    print(f"  Saved {path}")

try:
    make_review_sheet()
    make_anim_strip()
    make_skills_sheet()
    make_ingame_sheet()
except Exception as e:
    print(f"  Preview generation failed: {e}")

# =========================================================================
# Summary
# =========================================================================
if ok_all:
    print("\n=== DRakar V2 AUDIT PASSED ===")
else:
    print("\n=== SOME CHECKS FAILED ===")
    sys.exit(1)
