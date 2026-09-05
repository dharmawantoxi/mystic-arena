# ================================
# tools/bench_fx_layers.py
# Biaya lapisan FX hidup hero (heroes/*_fx.py), dipecah per modul dan
# per lapisan (tanah vs atas).
#
# Kenapa alat ini ada: profil fase (tools/bench_phase.py) menunjukkan
# e.hero memakan ~74% waktu frame, dan di dalamnya lapisan FX hidup
# lebih besar daripada sprite hero itu sendiri. Alat ini menunjuk modul
# mana yang paling mahal, jadi optimasi FX diarahkan ke penyebabnya.
#
# Contoh:
#   python3 tools/bench_fx_layers.py --quality low --heroes 10
#   MYSTIC_FX_GROUND=0 python3 tools/bench_fx_layers.py --quality low
# ================================
import os
import sys
import time
import random
import argparse
os.environ.setdefault("SDL_VIDEODRIVER","dummy"); os.environ.setdefault("SDL_AUDIODRIVER","dummy"); os.environ.setdefault("MYSTIC_DEBUG", "0")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ap = argparse.ArgumentParser()
ap.add_argument("--quality", default="low",
                choices=["low", "medium", "high"])
ap.add_argument("--heroes", type=int, default=10)
ap.add_argument("--minions", type=int, default=120)
ap.add_argument("--frames", type=int, default=300)
ap.add_argument("--warm", type=int, default=150)
ap.add_argument("--no-skill", action="store_true")
a = ap.parse_args()
import pygame; pygame.init()
from mobile import perf
perf.install_font_cache(); perf.Quality.apply(a.quality)
screen=pygame.display.set_mode((1280,720))
import _core
from _entity import Minion, Tower, Hero
from game import Game
random.seed(7)
g=Game(screen,level_number=1); g.level_intro=None; g.boss_intro=None
_POOL=["sylara","vex","grimjaw","kaizen","thorne","zephyr","abaddon","alchemist","razak","kunkka"]
for i in range(a.heroes // 2):
    h=Hero(_POOL[i%10],"blue",480+i*22,240+i*18); h.auto_cast_enabled=True; g.heroes.append(h)
for i in range(a.heroes - a.heroes // 2):
    h=Hero(_POOL[(i+5)%10],"red",860+i*22,220+i*18); h.auto_cast_enabled=True; g.ai.heroes.append(h)
for _ in range(a.minions // 2):
    for team,cx in (("red",820),("blue",560)):
        m=Minion(random.choice(["goblin","orc","undead"]),team,"mid",g.blue_base.level,g.map_renderer.get_lane_path("mid"))
        m.x=float(cx+random.uniform(-100,100)); m.y=float(240+random.uniform(-90,90)); m.is_moving=True; g.minions.append(m)

import heroes as H
T={}
for ht in list(H._LIVE_FX_HEROES):
    mod=H._live_fx_module(ht)
    if mod is None: continue
    for nm,tag in (("draw_ground_layer","ground"),("draw_live_layer","live")):
        fn=getattr(mod,nm,None)
        if fn is None or getattr(fn,"_wrapped_fxtime",False): continue
        def mk(fn,ht,tag):
            def w(*a,**k):
                t=time.perf_counter(); r=fn(*a,**k)
                k2=(ht,tag); T[k2]=T.get(k2,0.0)+time.perf_counter()-t
                return r
            w._wrapped_fxtime=True
            return w
        setattr(mod,nm,mk(fn,ht,tag))

def force_skills():
    if a.no_skill:
        return
    for h in g.get_all_heroes():
        for cd in getattr(h,"skill_cooldowns",[]) or []:
            try: cd.timer=0
            except Exception: pass
for _ in range(a.warm):
    force_skills(); g.update()
    for h in g.get_all_heroes(): h.hp=h.max_hp; h.alive=True
    g.draw()
T.clear()
FR = a.frames
for _ in range(FR):
    force_skills(); g.update()
    for h in g.get_all_heroes(): h.hp=h.max_hp; h.alive=True
    g.draw()
tot=sum(T.values())*1000.0/FR
print("")
print("kualitas=%s  hero hidup=%d  minion=%d" %
      (a.quality, len([h for h in g.get_all_heroes() if h.alive]),
       len(g.minions)))
print("total lapisan FX hero: %.3f ms/frame" % tot)
print("fase e.hero          : %.3f ms/frame" % perf.PHASES.avg.get("e.hero", 0.0))
print("%-22s %9s %9s %9s" % ("modul","ground","live","total"))
agg={}
for (ht,tag),v in T.items():
    a=agg.setdefault(ht,{"ground":0.0,"live":0.0})
    a[tag]+=v*1000.0/FR
for ht,a in sorted(agg.items(), key=lambda kv:-(kv[1]["ground"]+kv[1]["live"])):
    print("%-22s %9.3f %9.3f %9.3f" % (ht,a["ground"],a["live"],a["ground"]+a["live"]))
