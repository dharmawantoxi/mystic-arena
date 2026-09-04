"""Sebaran selisih probe paritas (canvas+blit vs render langsung), 216 tipe.

Memakai state boss pose serangan (pose paling ramai). Gunanya memilih
BOSS_PARITY_TOLERANCE berdasarkan data, bukan tebakan.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
SCREEN = pygame.display.set_mode((1280, 720))
from mobile import perf  # noqa: E402

perf.install_font_cache()
perf.Quality.apply("high")

import heroes  # noqa: E402
import _core  # noqa: E402,F401
from _core import Game  # noqa: E402
from _entity import Minion  # noqa: E402
from bosses.base_boss import Boss  # noqa: E402
from bosses.boss_data import get_all_boss_types  # noqa: E402

GAME = Game(SCREEN, level_number=1)
GAME.reset()
GAME.level_intro = None
GAME.boss_intro = None
LANE = GAME.map_renderer.get_lane_path("mid")

nilai = []
for t in sorted(get_all_boss_types()):
    b = Boss(t, LANE)
    b.entrance_timer = 0
    b.x, b.y = 640.0, 360.0
    foe = Minion("orc", "blue", "mid")
    foe.x, foe.y = b.x - min(120, b.range), b.y
    for _ in range(20):
        foe.hp = foe.max_hp
        b.update([foe], [], [])
    b.timer = max(1, int(b.attack_cooldown * 0.7))
    fn = heroes.BOSS_RENDERERS.get(t)
    if fn is None:
        continue
    for kind in ("idle", "atk", "skill"):
        if kind == "skill":
            b.active_skill = "q"
            b.active_skill_timer = 20
        elif kind == "atk":
            b.timer = max(1, int(b.attack_cooldown * 0.7))
        else:
            b.timer = 0
            b.active_skill = None
        res = heroes._boss_probe_parity(t, b, fn, kind)
        key = (t, kind)
        if key not in heroes._BOSS_PARITY_DIFF:
            print(f"  !! {t}/{kind}: probe None")
            continue
        nilai.append((f"{t}/{kind}", heroes._BOSS_PARITY_DIFF[key],
                      res[1] if res else False))

nilai.sort(key=lambda z: z[1])
print(f"sebaran selisih probe ({len(nilai)} tipe ter-probe):")
for t, d, ok in nilai:
    if d > 0.05 or not ok:
        print(f"  {t:16s} {d:7.3f}  aman_di_cache={ok}")
import statistics
semua = [d for _, d, _ in nilai]
print(f"\n n={len(semua)}  median={statistics.median(semua):.3f}  "
      f"p90={sorted(semua)[int(len(semua)*0.9)]:.3f}  "
      f"p95={sorted(semua)[int(len(semua)*0.95)]:.3f}  maks={semua[-1]:.3f}")
print(" jumlah > 0,45 :", sum(1 for d in semua if d > 0.45))
print(" jumlah 0,2-0,45:", sum(1 for d in semua if 0.2 < d <= 0.45))
print(" jumlah <= 0,2 :", sum(1 for d in semua if d <= 0.2))
