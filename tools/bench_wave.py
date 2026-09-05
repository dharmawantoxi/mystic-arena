# ================================
# tools/bench_wave.py
# Benchmark "wave besar" - meniru keluhan pemain Android:
#   banyak minion sekaligus + banyak hero + skill FX bermunculan
#   + basic attack bertubi-tubi.
#
# Bedanya dengan bench_combat.py:
#   * jumlah minion bisa diatur besar (wave sesungguhnya)
#   * hero dipaksa auto-cast + cooldown di-reset supaya SKILL FX
#     benar-benar muncul (bukan cuma basic attack)
#   * melaporkan ms/frame TERPISAH untuk update dan draw, plus
#     p95 frame time (hentakan), bukan cuma rata-rata
#
# Contoh:
#   python tools/bench_wave.py --minions 120 --heroes 10 --frames 240
#   python tools/bench_wave.py --minions 120 --profile
# ================================
import os
import sys
import time
import random
import argparse

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_DEBUG", "0")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ap = argparse.ArgumentParser()
ap.add_argument("--quality", default="low",
                choices=["low", "medium", "high"])
ap.add_argument("--minions", type=int, default=120)
ap.add_argument("--heroes", type=int, default=10)
ap.add_argument("--frames", type=int, default=240)
ap.add_argument("--profile", action="store_true")
ap.add_argument("--warm", type=int, default=180)
a = ap.parse_args()

import pygame  # noqa: E402
pygame.init()
from mobile import perf  # noqa: E402
perf.install_font_cache()
perf.Quality.apply(a.quality)
screen = pygame.display.set_mode((1280, 720))
import _core  # noqa: E402,F401
from _entity import Minion, Tower, Hero  # noqa: E402
from game import Game  # noqa: E402

g = Game(screen, level_number=1)
g.level_intro = None
g.boss_intro = None

# Kluster tower supaya pertempuran terpusat (seperti saat wave nyampe base)
for (x, y) in [(600, 180), (700, 180), (600, 280), (700, 280), (650, 230)]:
    t = Tower(x, y, "blue", "outer", "top")
    t.tower_type = "archer"
    t.level = 2
    t._apply_level_stats()
    g.towers.append(t)

# Hero: campur tipe yang punya live-FX berat + ringan
_POOL = ["sylara", "vex", "grimjaw", "kaizen", "thorne", "zephyr",
         "abaddon", "alchemist", "razak", "kunkka", "gornak", "varkul"]


def add_hero(htype, team, x, y):
    h = Hero(htype, team, x, y)
    h.auto_cast_enabled = True
    if team == "blue":
        g.heroes.append(h)
    else:
        g.ai.heroes.append(h)


n = a.heroes
for i in range(n // 2):
    add_hero(_POOL[i % len(_POOL)], "blue", 480 + i * 22, 240 + i * 18)
for i in range(n - n // 2):
    add_hero(_POOL[(i + 5) % len(_POOL)], "red", 860 + i * 22, 220 + i * 18)


def spawn_mass(cnt, team, cx, cy, spread=110):
    for _ in range(cnt):
        mt = random.choice(["goblin", "goblin", "orc", "undead",
                            "troll", "dark_rider"])
        m = Minion(mt, team, "mid", g.blue_base.level,
                   g.map_renderer.get_lane_path("mid"))
        m.x = float(cx + random.uniform(-spread, spread))
        m.y = float(cy + random.uniform(-spread, spread))
        m.direction = 1 if team == "blue" else -1
        m.is_moving = True
        g.minions.append(m)


spawn_mass(a.minions // 2, "red", 820, 240, 100)
spawn_mass(a.minions // 2, "blue", 560, 300, 80)


def force_skills():
    """Reset cooldown skill supaya FX skill muncul terus-menerus."""
    for h in g.get_all_heroes():
        for cd in getattr(h, "skill_cooldowns", []) or []:
            try:
                cd.timer = 0
            except Exception:
                pass
        getattr(h, "skill_cooldowns", None)


def pct(samples, p):
    if not samples:
        return 0.0
    s = sorted(samples)
    return s[min(len(s) - 1, int(len(s) * p))]


for _ in range(a.warm):
    force_skills()
    g.update()
    g.draw()

print("kualitas=%s minion=%d tower=%d hero=%d"
      % (a.quality, len(g.minions), len(g.towers),
         len(g.get_all_heroes())))

if a.profile:
    import cProfile
    import pstats
    import io
    for name, fn in (("update", g.update), ("draw", g.draw)):
        pr = cProfile.Profile()
        pr.enable()
        for _ in range(a.frames):
            fn()
        pr.disable()
        s = io.StringIO()
        pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(26)
        print("===== %s =====" % name)
        print(s.getvalue()[:6000])
else:
    # Pemanasan kedua supaya cache sprite terisi sebelum diukur.
    for _ in range(60):
        force_skills()
        g.update()
        g.draw()

    up, dn, tot = [], [], []
    for _ in range(a.frames):
        force_skills()
        t0 = time.perf_counter()
        g.update()
        t1 = time.perf_counter()
        g.draw()
        t2 = time.perf_counter()
        up.append((t1 - t0) * 1000.0)
        dn.append((t2 - t1) * 1000.0)
        tot.append((t2 - t0) * 1000.0)

    print("partikel=%d teks_melayang=%d proyektil=%d"
          % (len(g.effects.particles), len(g.effects.floating_texts),
             sum(len(getattr(h, "projectiles", []) or [])
                 for h in g.get_all_heroes())))
    print("update : avg %6.2f ms  p95 %6.2f ms"
          % (sum(up) / len(up), pct(up, 0.95)))
    print("draw   : avg %6.2f ms  p95 %6.2f ms"
          % (sum(dn) / len(dn), pct(dn, 0.95)))
    print("total  : avg %6.2f ms  p95 %6.2f ms  -> %.1f FPS rata-rata"
          % (sum(tot) / len(tot), pct(tot, 0.95), 1000.0 / (sum(tot) / len(tot))))
