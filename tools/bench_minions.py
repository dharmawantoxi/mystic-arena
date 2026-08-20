import os,sys,time,random
os.environ.setdefault("SDL_VIDEODRIVER","dummy"); os.environ.setdefault("SDL_AUDIODRIVER","dummy")
sys.path.insert(0,'.')
import pygame; pygame.init()
from mobile import perf; perf.install_font_cache()
scr=pygame.display.set_mode((1280,720))
import _core
from _entity import Minion
from minions import render_minion
from mobile import spritecache

def make(n):
    out=[]
    for i in range(n):
        t = ["goblin","orc","troll","undead","dark_rider"][i%5]
        team = "blue" if i%2 else "red"
        try: m=Minion(t,team,lane="mid")
        except TypeError: m=Minion(t,team)
        m.x=random.randint(100,1100); m.y=random.randint(100,600)
        m.direction=1 if i%3 else -1; m.is_moving=True
        out.append(m)
    return out

for N in (10, 30, 60):
    ms=make(N)
    for mode in ("0","1"):
        os.environ["MYSTIC_SPRITE_CACHE"]=mode
        spritecache.clear()
        for f in range(20):   # pemanasan
            for m in ms: m.anim_time+=1; m.walk_cycle=(m.walk_cycle+1)%40; render_minion(m.minion_type,scr,m,int(m.x),int(m.y))
        t0=time.perf_counter(); F=120
        for f in range(F):
            for m in ms:
                m.anim_time+=1; m.walk_cycle=(m.walk_cycle+1)%40
                render_minion(m.minion_type,scr,m,int(m.x),int(m.y))
        dt=(time.perf_counter()-t0)/F*1000
        print("%3d minion | cache=%s | %6.2f ms/frame  %s" % (N, mode, dt, spritecache.stats() if mode=="1" else ""))
