# Beban realistis: banyak minion bertarung + tower + hero. Profil update & draw.
import os, sys, time, argparse, random
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_DEBUG", "0")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ap = argparse.ArgumentParser()
ap.add_argument("--quality", default="high")
ap.add_argument("--minions", type=int, default=60)
ap.add_argument("--frames", type=int, default=120)
ap.add_argument("--profile", action="store_true")
a = ap.parse_args()

import pygame; pygame.init()
from mobile import perf
perf.install_font_cache(); perf.Quality.apply(a.quality)
screen = pygame.display.set_mode((1280, 720))
import _core
from _entity import Minion, Tower, Hero
from game import Game

g = Game(screen, level_number=1)
g.level_intro = None
g.boss_intro = None

# Tower kluster biru di tengah-top agar jadi medan pertempuran
center_towers = [(600,180),(700,180),(600,280),(700,280),(650,230)]
for (x,y) in center_towers:
    t = Tower(x, y, "blue", "outer", "top")
    t.tower_type = "archer"; t.level = 2; t._apply_level_stats()
    g.towers.append(t)

# Hero
def add_hero(htype, team, x, y):
    h = Hero(htype, team, x, y)
    h.auto_cast_enabled = True
    if team == "blue":
        g.heroes.append(h)
    else:
        g.ai.heroes.append(h)
add_hero("sylara","blue",500,250)
add_hero("vex","blue",550,300)
add_hero("grimjaw","blue",450,220)
add_hero("kaizen","blue",700,300)
add_hero("vex","red",900,200)
add_hero("thorne","red",900,300)
add_hero("kaizen","red",800,250)
add_hero("sylara","red",950,300)

def spawn_mass(n, team, cx, cy, spread=120):
    for _ in range(n):
        mt = random.choice(["goblin","goblin","orc","undead","troll","dark_rider"])
        m = Minion(mt, team, "mid", g.blue_base.level, g.map_renderer.get_lane_path("mid"))
        m.x = float(cx + random.uniform(-spread, spread))
        m.y = float(cy + random.uniform(-spread, spread))
        m.direction = 1 if team=="blue" else -1
        m.is_moving = True
        g.minions.append(m)

spawn_mass(a.minions//2, "red", 850, 240, 90)
spawn_mass(a.minions//2, "blue", 600, 300, 60)

for _ in range(150):
    g.update(); g.draw()
print("entitas: minion=%d tower=%d hero=%d eff=%d boss=%s" % (
    len(g.minions), len(g.towers), len(g.get_all_heroes()),
    len(g.effects.particles) + len(g.effects.floating_texts),
    getattr(getattr(g, 'active_boss', None), 'boss_type', None)))

if a.profile:
    import cProfile, pstats, io
    for name, fn in (("update", g.update), ("draw", g.draw)):
        pr = cProfile.Profile(); pr.enable()
        for _ in range(a.frames): fn()
        pr.disable()
        s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(24)
        print("===== %s =====" % name)
        print(s.getvalue()[:5000])
else:
    for name, fn in (("update", g.update), ("draw", g.draw)):
        t0=time.perf_counter()
        for _ in range(a.frames): fn()
        dt=time.perf_counter()-t0
        print("%-7s %-6s : %.3f ms/frame  eff=%d/%d" % (
            name, a.quality, dt/a.frames*1000,
            len(g.effects.particles), len(g.effects.floating_texts)))
