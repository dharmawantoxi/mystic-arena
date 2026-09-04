import os, sys, cProfile, pstats, io
os.environ.setdefault("SDL_VIDEODRIVER","dummy"); os.environ.setdefault("SDL_AUDIODRIVER","dummy")
sys.path.insert(0, os.getcwd())
import pygame; pygame.init()
screen = pygame.display.set_mode((1280,720))
from mobile import perf
perf.install_font_cache(); perf.Quality.apply("high")
import _core
from _core import Game
from bosses.base_boss import Boss
g = Game(screen, level_number=1); g.level_intro=None; g.boss_intro=None
lane = g.map_renderer.get_lane_path("mid")
SURF = pygame.Surface((1280,720), pygame.SRCALPHA)
TYPES = ["aeralith","okeanora","vraskhan","nexthyrius","kagetsuka","gornak","varkul","abaddon"]
pr = cProfile.Profile(); pr.enable()
for t in TYPES:
    b = Boss(t, lane); b.entrance_timer=0; b.x, b.y = 640.0, 360.0
    for i in range(60):
        b.pulse += 0.05; b.anim_time += 1; b.timer = max(0, b.timer-1)
        b.draw(SURF)
pr.disable()
s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(28)
print(s.getvalue()[:6000])
