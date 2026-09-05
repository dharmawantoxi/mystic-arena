# ================================
# tools/bench_hero_cache.py
# Pengukur A/B untuk cache sprite hero.
#
# Kenapa berkas ini ada:
#   Profiling di PC (pygame-ce 2.5.8) menunjukkan lapisan hero =
#   77% dari total waktu draw saat wave besar + banyak hero.
#   Penyebabnya cache sprite hero kepenuhan lalu "thrashing":
#   satu cache-MISS = 4.1 ms sedangkan render langsung cuma 3.1 ms,
#   jadi miss lebih mahal daripada tidak memakai cache sama sekali.
#
#   Alat ini mengukur konfigurasi cache secara BERULANG (default 3
#   putaran) supaya selisih antar konfigurasi tidak tertukar noise.
#
# Contoh:
#   python tools/bench_hero_cache.py
#   python tools/bench_hero_cache.py --heroes 10 --minions 120 --reps 5
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
ap.add_argument("--heroes", type=int, default=10)
ap.add_argument("--minions", type=int, default=120)
ap.add_argument("--reps", type=int, default=3)
ap.add_argument("--frames", type=int, default=120)
ap.add_argument("--warm", type=int, default=240)
ap.add_argument("--seed", type=int, default=1234)
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
import heroes as H  # noqa: E402

random.seed(a.seed)
g = Game(screen, level_number=1)
g.level_intro = None
g.boss_intro = None

_POOL = ["sylara", "vex", "grimjaw", "kaizen", "thorne", "zephyr",
         "abaddon", "alchemist", "razak", "kunkka", "gornak", "varkul"]
HEROES = []
n = a.heroes
for i in range(n):
    h = Hero(_POOL[i % len(_POOL)], "blue" if i < n // 2 else "red",
             480 + i * 40, 240 + i * 15)
    h.auto_cast_enabled = True
    h.hp = 10 ** 9
    h.max_hp = 10 ** 9
    (g.heroes if i < n // 2 else g.ai.heroes).append(h)
    HEROES.append(h)

for team, cx, cy in (("red", 820, 240), ("blue", 560, 300)):
    for _ in range(a.minions // 2):
        mt = random.choice(["goblin", "goblin", "orc", "undead",
                            "troll", "dark_rider"])
        m = Minion(mt, team, "mid", g.blue_base.level,
                   g.map_renderer.get_lane_path("mid"))
        m.x = float(cx + random.uniform(-100, 100))
        m.y = float(cy + random.uniform(-80, 80))
        m.direction = 1 if team == "blue" else -1
        m.is_moving = True
        # Immortal: wave harus BERTAHAN besar selama diukur. Kalau
        # minion mati semua, adegan jadi ringan dan angka tidak
        # menggambarkan "wave besar" yang dikeluhkan pemain.
        m.hp = 10 ** 9
        m.max_hp = 10 ** 9
        g.minions.append(m)


def force_skills():
    """Reset cooldown supaya skill FX muncul terus selama diukur."""
    for h in HEROES:
        for cd in getattr(h, "skill_cooldowns", []) or []:
            try:
                cd.timer = 0
            except Exception:
                pass


scratch = pygame.Surface((1280, 720))


def measure(atk_q, skill_q, cache_max, frames, warm):
    H.HERO_CACHE_ENABLED = True
    H.HERO_ATK_QUANT = atk_q
    H.HERO_SKILL_QUANT = skill_q
    H._HERO_CACHE_MAX = cache_max
    H._hero_sprite_cache.clear()
    for _ in range(warm):
        force_skills()
        g.update()
        g.draw()
    H._hero_cache_stats["hits"] = 0
    H._hero_cache_stats["misses"] = 0
    t = 0.0
    for _ in range(frames):
        force_skills()
        g.update()
        for h in HEROES:
            t0 = time.perf_counter()
            H.render_hero(h.hero_type, scratch, h, int(h.x), int(h.y))
            t += (time.perf_counter() - t0) * 1000.0
    hs = H._hero_cache_stats
    hr = 100.0 * hs["hits"] / max(1, hs["hits"] + hs["misses"])
    px = 0
    for e in H._hero_sprite_cache.values():
        try:
            px += e[0].get_width() * e[0].get_height()
        except Exception:
            pass
    return t / frames, hr, len(H._hero_sprite_cache), px * 4 / 1e6


# (label, atk_quant, skill_quant, cache_max)
CONFIGS = [
    ("baseline  atk2 skill2 cap600", 2, 2, 600),
    ("atk2 skill6  cap600", 2, 6, 600),
    ("atk2 skill8  cap600", 2, 8, 600),
    ("atk2 skill12 cap600", 2, 12, 600),
    ("atk2 skill12 cap400", 2, 12, 400),
    ("atk3 skill12 cap600", 3, 12, 600),
    ("atk4 skill12 cap600", 4, 12, 600),
]

print("hero=%d minion=%d kualitas=%s reps=%d"
      % (len(HEROES), len(g.minions), a.quality, a.reps))
print("%-32s %10s %8s %6s %6s"
      % ("konfigurasi", "ms/frame", "hitrate", "entri", "MB"))
for label, aq, sq, cap in CONFIGS:
    runs = []
    for _ in range(a.reps):
        runs.append(measure(aq, sq, cap, a.frames, a.warm))
    ms = sorted(r[0] for r in runs)[len(runs) // 2]      # median
    hr = sum(r[1] for r in runs) / len(runs)
    en = int(sum(r[2] for r in runs) / len(runs))
    mb = sum(r[3] for r in runs) / len(runs)
    print("%-32s %10.3f %7.1f%% %6d %6.1f" % (label, ms, hr, en, mb))
