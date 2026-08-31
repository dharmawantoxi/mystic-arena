#!/usr/bin/env python3
"""Regresi visual untuk Drakar Procedural Masterwork v2.

Memastikan upgrade tidak kembali menjadi body-part statis:
  - rig 1.5x (BODY_W/BODY_H = 360x360)
  - FX helper ada (_fx_scale, _spark_star, _chevron, _dashed_ring, _jagged_crack)
  - semua mode render tanpa exception & berisi piksel
  - animasi kontinu (per-frame, bukan bucket stepping)
  - skill FX world-space (radius meningkat dengan _fx_scale)
  - renderer prosedural (tanpa pygame.image.load)

Jalankan:  python3 tools/test_drakar_masterwork.py
"""
import inspect
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

import bosses.level1 as L
NS = L._NS_drakar

ok_all = True

def check(cond, label, extra=""):
    global ok_all
    status = "OK " if cond else "FAIL"
    if not cond:
        ok_all = False
    print(f"[{status}] {label} {extra}")
    return cond


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


def render(boss, fn=None, size=460):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    (fn or L.draw_drakar)(s, boss, 230, 230)
    return s


# === Test 1: rig 1.5x ===
check(NS.BODY_W == 360, "Rig BODY_W == 360 (1.5x)", f"(got {NS.BODY_W})")
check(NS.BODY_H == 360, "Rig BODY_H == 360 (1.5x)", f"(got {NS.BODY_H})")

# === Test 2: semua helper FX ada ===
for name in ("_fx_scale", "_spark_star", "_chevron", "_dashed_ring",
             "_jagged_crack", "_tuft_points", "_mix", "_hash01", "_static"):
    check(hasattr(NS, name), f"Helper {name} ada")

# === Test 3: semua mode render ===
walker = probe(pulse=1.0)
walker._drk_last_x = -2.0
walker._drk_last_y = 0.0
cases = [probe(pulse=0.0), probe(pulse=3.3), walker,
         atk(0.1), atk(0.3), atk(0.5), atk(0.62), atk(0.85), atk(0.5, -1),
         probe(active_skill="q", active_skill_timer=45),
         probe(active_skill="w", active_skill_timer=20),
         probe(active_skill="e", active_skill_timer=30),
         probe(active_skill="r", active_skill_timer=30,
               target=SimpleNamespace(x=320.0, y=230.0, alive=True)),
         probe(rage_active=True), probe(defense_boost=True)]
all_ok = True
for c in cases:
    try:
        s = render(c)
        r = s.get_bounding_rect(min_alpha=100)
        if r.width == 0 or r.height == 0:
            all_ok = False
    except Exception as e:
        all_ok = False
        print(f"  exception: {e}")
check(all_ok, f"Semua {len(cases)} mode render tanpa error & berisi piksel")

# === Test 4: animasi kontinu (bukan bucket cache) ===
s1 = render(probe(pulse=0.0))
s2 = render(probe(pulse=1.0))
s3 = render(probe(pulse=2.0))
px1 = set(s1.get_at((x, y))[:3] for x in range(s1.get_width())
          for y in range(s1.get_height()) if s1.get_at((x, y)).a > 50)
px2 = set(s2.get_at((x, y))[:3] for x in range(s2.get_width())
          for y in range(s2.get_height()) if s2.get_at((x, y)).a > 50)
diff12 = len(px1.symmetric_difference(px2))
check(diff12 > 10, "Animasi kontinu: idle berbeda antar phase", f"(diff={diff12})")

# === Test 5: frame unik antar attack progress ===
frames = []
for p in [0.1, 0.3, 0.5, 0.7]:
    frames.append(render(atk(p)))
unique = 0
for i in range(len(frames)):
    for j in range(i + 1, len(frames)):
        r = frames[i].get_bounding_rect()
        if r.width == 0:
            continue
        diff = 0
        for x in range(r.x, r.x + r.width, 3):
            for y in range(r.y, r.y + r.height, 3):
                c1 = frames[i].get_at((x, y))
                c2 = frames[j].get_at((x, y))
                if abs(c1[0] - c2[0]) + abs(c1[1] - c2[1]) + abs(c1[2] - c2[2]) > 30:
                    diff += 1
        if diff > 5:
            unique += 1
check(unique >= 4, "Attack: >= 4 pasangan frame unik", f"(got {unique})")

# === Test 6: skill FX world-space ===
# Dengan _render_scale=0.5, _fx_scale = 2.0
boss_normal = probe(active_skill="e", active_skill_timer=30)
boss_scaled = probe(active_skill="e", active_skill_timer=30, _render_scale=0.5)
fs_normal = NS._fx_scale(boss_normal)
fs_scaled = NS._fx_scale(boss_scaled)
check(fs_normal == 1.0, f"_fx_scale normal = 1.0 (got {fs_normal})")
check(fs_scaled == 2.0, f"_fx_scale scaled(0.5) = 2.0 (got {fs_scaled})")

# === Test 7: skill rendering dengan _fx_scale ===
s_norm = render(probe(active_skill="q", active_skill_timer=45))
s_fx = render(probe(active_skill="q", active_skill_timer=45, _render_scale=0.5), size=600)
check(s_norm.get_bounding_rect(min_alpha=10).width > 50,
      "Q skill render normal berisi piksel")
check(s_fx.get_bounding_rect(min_alpha=10).width > 50,
      "Q skill render scaled berisi piksel")

# === Test 8: renderer prosedural ===
source = inspect.getsource(NS)
# Strip docstrings/comments to avoid false positive from the text "image.load"
code_lines = [l for l in source.split('\n')
              if not l.strip().startswith('#') and not l.strip().startswith('"""')
              and not l.strip().startswith("'''") and not l.strip().startswith('*')]
code_only = '\n'.join(code_lines)
has_image_load = "pygame.image.load" in code_only or "image.load(" in code_only
check(not has_image_load, "Renderer prosedural (tanpa image.load)")

# === Test 9: palette lengkap ===
required_keys = ["skin_darkest", "blood_mid", "rage_light", "armor_shine",
                 "blade_shine", "gold_mid", "ember_light", "eye_glow"]
for key in required_keys:
    check(key in NS.PALETTE, f"PALETTE['{key}'] ada")

# === Test 10: timing ===
import time
b = probe(pulse=0.0)
t0 = time.perf_counter()
for _ in range(20):
    render(b)
    b.pulse += 0.1
ms = (time.perf_counter() - t0) / 20 * 1000
check(ms < 10, f"Render budget < 10ms/frame (got {ms:.2f}ms)")

# === Summary ===
if ok_all:
    print("\n=== ALL TESTS PASSED ===")
else:
    print("\n=== SOME TESTS FAILED ===")
    sys.exit(1)
