# Benchmark adegan berat: banyak minion + boss + tower di layar.
import os, sys, time, argparse
os.environ.setdefault("SDL_VIDEODRIVER","dummy"); os.environ.setdefault("SDL_AUDIODRIVER","dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ap = argparse.ArgumentParser()
ap.add_argument("--quality", default="high", choices=["low","medium","high"])
ap.add_argument("--profile", action="store_true")
ap.add_argument("--frames", type=int, default=180)
a = ap.parse_args()

import pygame; pygame.init()
from mobile import perf
perf.install_font_cache(); perf.Quality.apply(a.quality)
screen = pygame.display.set_mode((1280,720))
import _core
from game import Game
g = Game(screen, level_number=1)
# lewati cinematic
g.level_intro = None
g.boss_intro = None
for _ in range(int(os.environ.get("WARM","900"))): g.update(); g.draw()
print("entitas: minion=%d tower=%d hero=%d boss=%s" % (
    len(g.minions), len(g.towers), len(g.heroes),
    getattr(getattr(g,'active_boss',None),'boss_type',None)))

if a.profile:
    import cProfile, pstats, io
    pr = cProfile.Profile(); pr.enable()
    for _ in range(a.frames): g.update(); g.draw()
    pr.disable()
    s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(18)
    print(s.getvalue()[:4000])
else:
    t0 = time.perf_counter()
    for _ in range(a.frames): g.update(); g.draw()
    dt = time.perf_counter()-t0
    print("kualitas %-6s : %.2f ms/frame  (%.1f FPS)" % (a.quality, dt/a.frames*1000, a.frames/dt))
