"""Smoke test loop game NYATA saat pertarungan boss (update + draw).

Melengkapi tools/test_boss_hero_smooth_parity.py: di sini boss dijalankan
lewat Game.update()/Game.draw() sungguhan — jadi governor FX, frustum
culling, wave/minion/tower, dan pembersihan cache saat reset ikut teruji.

Jalankan (bandingkan sebelum/sesudah cache sprite boss):
    python3 tools/_diag_boss_scene_smoke.py
    MYSTIC_BOSS_CACHE=0 python3 tools/_diag_boss_scene_smoke.py
    python3 tools/_diag_boss_scene_smoke.py 1:gornak 30:nyrethzalv
"""
import os
import statistics
import sys
import time

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

FRAMES = 600
PASANGAN = [(1, "gornak"), (10, "thalgryn"), (30, "nyrethzalv"),
            (54, "nyxaris")]
if len(sys.argv) > 1:
    PASANGAN = []
    for arg in sys.argv[1:]:
        lvl, tipe = arg.split(":", 1)
        PASANGAN.append((int(lvl), tipe))

ON = os.environ.get("MYSTIC_BOSS_CACHE", "1") != "0"
print(f"=== loop game nyata, {FRAMES} frame per level "
      f"(cache sprite boss {'NYALA' if ON else 'MATI'}) ===")

for level, tipe in PASANGAN:
    g = Game(SCREEN, level_number=level)
    g.reset()
    # Cinematic intro menjeda gameplay (Game.update return lebih awal),
    # jadi dilewati supaya boss benar-benar bertarung selama diukur.
    g.level_intro = None
    g.boss_intro = None
    g.boss_death = None
    for _ in range(200):
        g.update()
        g.draw()

    heroes.clear_boss_sprite_cache()
    lane = g.map_renderer.get_lane_path("mid")
    b = Boss(tipe, lane)
    b.entrance_timer = 0            # entrance menggambar cinematic sendiri
    g.active_boss = b
    g.boss_intro = None
    g.boss_death = None
    for i in range(5):
        m = Minion("orc", "blue", "mid")
        m.x, m.y = b.x - 130 - i * 20, b.y + (i % 3) * 16
        g.minions.append(m)

    biaya = []
    error = None
    frame_skill = 0
    unsafe_awal = len(heroes._BOSS_UNSAFE)
    try:
        for f in range(FRAMES):
            g.level_intro = None
            g.boss_death = None
            if f % 50 == 0:                     # pasok target baru
                m = Minion("orc", "blue", "mid")
                m.x, m.y = g.active_boss.x - 140, g.active_boss.y
                g.minions.append(m)
            t0 = time.perf_counter()
            g.update()
            g.draw()
            biaya.append((time.perf_counter() - t0) * 1000)
            if getattr(g.active_boss, "active_skill", None):
                frame_skill += 1
            if g.active_boss is None or not g.active_boss.alive:
                b = Boss(tipe, lane)
                b.entrance_timer = 0
                g.active_boss = b
                g.boss_intro = None
    except Exception:
        import traceback
        error = traceback.format_exc().splitlines()[-1]

    biaya.sort()
    st = heroes.boss_cache_stats()
    berat = sum(1 for x in biaya if x > 16.7)
    print(f"level {level:2d} {tipe:12s} "
          f"mean {statistics.mean(biaya):5.2f} ms  "
          f"p95 {biaya[int(len(biaya) * 0.95)]:5.2f}  "
          f"maks {biaya[-1]:6.2f}  >16.7ms {berat:3d}/{FRAMES} | "
          f"skill {frame_skill}f | cache {st['hit_rate']} "
          f"{heroes.boss_cache_bytes():.1f}MB | "
          f"pose jalur langsung baru {len(heroes._BOSS_UNSAFE) - unsafe_awal}"
          + (f" | ERROR {error}" if error else " | tanpa error"))
