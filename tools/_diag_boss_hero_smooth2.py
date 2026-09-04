"""DIAGNOSTIK 2: pisahkan biaya DRAW vs UPDATE, dan telusuri stall gerak.

  python3 tools/_diag_boss_hero_smooth2.py gornak varkul abaddon
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

TYPES = sys.argv[1:] or ["gornak", "varkul", "abaddon"]
FRAMES = 120

g = Game(screen, level_number=1)
g.level_intro = None
g.boss_intro = None
lane = g.map_renderer.get_lane_path("mid")
SURF = pygame.Surface((1280, 720), pygame.SRCALPHA)


def trace_walk(ent, kind, label):
    """Jalan lurus tanpa musuh: catat delta posisi + waktu draw/update."""
    ent.x, ent.y = float(lane[-1][0]), float(lane[-1][1])
    if kind == "boss":
        ent.waypoint_index = len(lane) - 1
        ent.lane_path = lane
        ent.entrance_timer = 0
    t_upd = t_draw = 0.0
    deltas = []
    for i in range(FRAMES):
        t0 = time.perf_counter()
        ent.update([], [], [])
        t1 = time.perf_counter()
        SURF.fill((0, 0, 0, 0))
        ent.draw(SURF)
        t2 = time.perf_counter()
        t_upd += t1 - t0
        t_draw += t2 - t1
        deltas.append((i, round(ent.x, 2), round(ent.y, 2)))
    steps = [((b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2) ** 0.5
             for a, b in zip(deltas, deltas[1:])]
    stall = [i for i, s in enumerate(steps) if s <= 0.02]
    print(f"{label:26s} update {t_upd/FRAMES*1000:6.2f} ms | "
          f"draw {t_draw/FRAMES*1000:7.2f} ms | speed={getattr(ent,'speed',0):.2f} | "
          f"stall {len(stall):3d} frame {stall[:12]}")
    return t_draw / FRAMES * 1000


for t in TYPES:
    print("=" * 96)
    b = Boss(t, lane)
    trace_walk(b, "boss", f"BOSS {t}")
    b2 = Boss(t, lane)
    b2.boss_class = "true"
    trace_walk(b2, "boss", f"TRUE {t}")
    h = Hero(t, "red", x=float(lane[-1][0]), y=float(lane[-1][1]))
    trace_walk(h, "hero", f"HERO {t}")
