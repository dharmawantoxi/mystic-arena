"""DIAGNOSTIK SEMENTARA: bandingkan kelancaran BOSS vs HERO (tipe sama).

Ukur:
  1. biaya draw ms/frame (boss.draw vs hero.draw)
  2. jumlah frame identik berturut-turut (stutter animasi)
  3. konsistensi pergerakan (delta posisi per frame)
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
from _entity import Hero, Minion  # noqa: E402
from bosses.base_boss import Boss  # noqa: E402

TYPES = sys.argv[1:] or ["gornak", "varkul", "abaddon", "morgath", "drakar"]

g = Game(screen, level_number=1)
g.level_intro = None
g.boss_intro = None
lane = g.map_renderer.get_lane_path("mid")

SURF = pygame.Surface((1280, 720), pygame.SRCALPHA)
FRAMES = 90


def frame_diff(a, b):
    """Rata-rata selisih absolut antar dua surface (proxy perubahan pose)."""
    import numpy as np
    aa = pygame.surfarray.array3d(a).astype("int16")
    bb = pygame.surfarray.array3d(b).astype("int16")
    return float(abs(aa - bb).mean())


def measure(entity, label, kind):
    # entitas butuh beberapa musuh supaya menyerang/bergerak
    foes = [Minion("goblin", "blue" if kind == "boss" else "red", "mid")
            for _ in range(3)]
    for f in foes:
        f.x = entity.x + 60
        f.y = entity.y
    towers, bases = [], []
    prev = None
    diffs = []
    poses = []
    t0 = time.perf_counter()
    for i in range(FRAMES):
        if kind == "boss":
            entity.update(foes, towers, bases)
        else:
            entity.update(foes, towers, bases)
        SURF.fill((0, 0, 0, 0))
        entity.draw(SURF)
        snap = SURF.copy()
        if prev is not None:
            diffs.append(frame_diff(prev, snap))
        prev = snap
        poses.append((round(entity.x, 3), round(entity.y, 3)))
    dt = (time.perf_counter() - t0) / FRAMES * 1000.0

    identical = sum(1 for d in diffs if d < 0.001)
    # delta gerak
    steps = []
    for (x0, y0), (x1, y1) in zip(poses, poses[1:]):
        steps.append(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5)
    moved = [s for s in steps if s > 0.01]
    stall = sum(1 for s in steps if s <= 0.01)
    avg_move = sum(moved) / len(moved) if moved else 0.0
    jitter = (max(moved) - min(moved)) if moved else 0.0
    print(f"{label:34s} draw {dt:6.2f} ms/f | frame identik {identical:3d}"
          f"/{len(diffs)} | diff rata2 {sum(diffs)/max(1,len(diffs)):6.2f}"
          f" | stall {stall:3d} | langkah {avg_move:5.2f}px (jit {jitter:4.2f})")
    return dt


print("=== BOSS (jalur Boss.draw, tanpa cache) vs HERO (jalur render_hero, cache) ===")
for t in TYPES:
    try:
        b = Boss(t, lane)
        b.entrance_timer = 0
        measure(b, f"BOSS  {t}", "boss")
    except Exception as exc:
        print(f"BOSS  {t}: ERROR {type(exc).__name__}: {exc}")
    try:
        h = Hero(t, "red", x=900.0, y=400.0)
        measure(h, f"HERO  {t}", "hero")
    except Exception as exc:
        print(f"HERO  {t}: ERROR {type(exc).__name__}: {exc}")
    print("-" * 100)
