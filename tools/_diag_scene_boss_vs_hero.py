"""Ukur fps adegan penuh: mini/true BOSS aktif vs karakter sama sebagai HERO.

Jalankan:
    python3 tools/_diag_scene_boss_vs_hero.py [level] [tipe...]
"""
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
screen = pygame.display.set_mode((1280, 720))
from mobile import perf  # noqa: E402

perf.install_font_cache()
perf.Quality.apply("high")

import _core  # noqa: E402,F401
from _core import Game  # noqa: E402
from _entity import Hero  # noqa: E402
from bosses.base_boss import Boss  # noqa: E402

LEVEL = int(sys.argv[1]) if len(sys.argv) > 1 else 1
TYPES = sys.argv[2:] or None
FRAMES = 150


def build(level):
    g = Game(screen, level_number=level)
    g.level_intro = None
    g.boss_intro = None
    g.boss_death = None
    for _ in range(250):          # panaskan: wave minion + tower + hero AI
        g.update()
        g.draw()
    return g


def run(g, label):
    ft = []
    for _ in range(FRAMES):
        t0 = time.perf_counter()
        g.update()
        g.draw()
        ft.append((time.perf_counter() - t0) * 1000.0)
    ft.sort()
    mean = sum(ft) / len(ft)
    p95 = ft[int(len(ft) * 0.95)]
    over = sum(1 for f in ft if f > 16.7)
    print(f"{label:38s} mean {mean:6.2f} ms  p95 {p95:6.2f} ms  "
          f"maks {ft[-1]:6.2f}  >16.7ms: {over:3d}/{len(ft)}  "
          f"(~{1000.0/mean:5.1f} fps)")
    return mean


if TYPES is None:
    cfg = Game(screen, level_number=LEVEL).level_config
    TYPES = list(cfg.get("mini_bosses", {}).values())
    tb = cfg.get("true_boss")
    if tb:
        TYPES.append(tb)

print(f"### LEVEL {LEVEL} — {len(TYPES)} karakter diuji")
for t in TYPES:
    g = build(LEVEL)
    lane = g.map_renderer.get_lane_path("mid")
    b = Boss(t, lane)
    b.entrance_timer = 0
    g.active_boss = b
    base_boss = run(g, f"BOSS aktif: {t}")

    g2 = build(LEVEL)
    h = Hero(t, "red", x=700.0, y=360.0)
    g2.ai.heroes.append(h)
    g2.active_boss = None
    base_hero = run(g2, f"HERO (unlock) : {t}")
    print(f"{'':38s}→ selisih {base_boss - base_hero:+6.2f} ms/frame "
          f"({base_boss / max(0.01, base_hero):.2f}x)")
    print("-" * 100)
