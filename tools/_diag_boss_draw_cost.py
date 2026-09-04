"""Ukur biaya draw tiap boss (langsung, tanpa cache) + bandingkan jalur hero."""
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
from bosses.base_boss import Boss  # noqa: E402
from bosses.boss_data import get_all_boss_types  # noqa: E402

g = Game(screen, level_number=1)
g.level_intro = None
g.boss_intro = None
lane = g.map_renderer.get_lane_path("mid")
SURF = pygame.Surface((1280, 720), pygame.SRCALPHA)
FR = 12

all_types = sorted(get_all_boss_types().keys())
only = sys.argv[1:]
if only:
    all_types = [t for t in all_types if t in only]

rows = []
for t in all_types:
    try:
        b = Boss(t, lane)
        b.entrance_timer = 0
        b.x, b.y = 640.0, 360.0
        for _ in range(3):
            b.update([], [], [])
            b.draw(SURF)
        t0 = time.perf_counter()
        for _ in range(FR):
            b.pulse += 0.05
            b.anim_time += 1
            b.draw(SURF)
        ms = (time.perf_counter() - t0) / FR * 1000.0
        rows.append((ms, t, b.boss_class))
    except Exception as exc:
        rows.append((-1.0, t, f"ERR {type(exc).__name__}: {exc}"[:60]))

rows.sort(reverse=True)
print(f"{'ms/frame':>9}  {'boss':28s} class")
for ms, t, cls in rows[:45]:
    print(f"{ms:9.2f}  {t:28s} {cls}")
print("...")
tot = [r[0] for r in rows if r[0] > 0]
print(f"n={len(tot)}  max={max(tot):.2f}  median={sorted(tot)[len(tot)//2]:.2f}  "
      f"mean={sum(tot)/len(tot):.2f}  >2ms={sum(1 for x in tot if x>2)}  "
      f">1ms={sum(1 for x in tot if x>1)}")
for ms, t, cls in rows:
    if ms < 0:
        print("ERROR", t, cls)
