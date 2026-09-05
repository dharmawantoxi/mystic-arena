# ================================
# tools/bench_phase.py
# Pemecah waktu frame MENURUT FASE (memakai perf.PHASES yang sudah
# ditanam di dalam Game.draw). bench_wave.py memberi satu angka total;
# alat ini menjawab "bagian MANA yang mahal" — peta, minion, hero,
# efek, atau HUD — sehingga optimasi diarahkan ke penyebabnya, bukan
# ke tebakan.
#
# Contoh:
#   python3 tools/bench_phase.py --quality low --minions 120 --heroes 10
#   python3 tools/bench_phase.py --quality low --boss --level 5
#   python3 tools/bench_phase.py --quality high --minions 0 --heroes 0
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
ap.add_argument("--frames", type=int, default=120)
ap.add_argument("--warm", type=int, default=90)
ap.add_argument("--level", type=int, default=1)
ap.add_argument("--no-skill", action="store_true",
                help="jangan reset cooldown skill (basic attack saja)")
ap.add_argument("--boss", action="store_true",
                help="munculkan boss level ini (kalau ada)")
ap.add_argument("--top", type=int, default=14)
ap.add_argument("--miss-time", action="store_true",
                help="ukur total ms/frame yang dihabiskan di dalam "
                     "_hero_render_sprite (jalur cache-miss sprite hero)")
ap.add_argument("--keep-alive", action="store_true",
                help="pulihkan HP hero tiap frame supaya jumlah hero "
                     "yang digambar tetap (hasil ukur bisa dibandingkan)")
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

random.seed(1234)
g = Game(screen, level_number=a.level)
g.level_intro = None
g.boss_intro = None

for (x, y) in [(600, 180), (700, 180), (600, 280), (700, 280), (650, 230)]:
    t = Tower(x, y, "blue", "outer", "top")
    t.tower_type = "archer"
    t.level = 2
    t._apply_level_stats()
    g.towers.append(t)

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

if a.boss:
    # Boss dimunculkan lewat jalur yang sama dengan game:
    # pending_mini_bosses -> _try_spawn_pending_mini_boss().
    try:
        from levels import get_level_config
        cfg = get_level_config(a.level) or {}
        btype = cfg.get("true_boss")
        if not btype:
            mb = cfg.get("mini_bosses") or {}
            btype = mb.get(sorted(mb)[0]) if mb else None
        if not btype:
            raise RuntimeError("level %d tidak punya boss" % a.level)
        g.pending_mini_bosses.append((1, btype))
        g._try_spawn_pending_mini_boss()
        g.boss_intro = None
        if g.active_boss is not None:
            g.active_boss.x, g.active_boss.y = 700.0, 240.0
            print("[bench_phase] boss aktif: %s" % g.active_boss.name)
    except Exception as exc:
        print("[bench_phase] boss gagal dimunculkan: %s" % exc)


def force_skills():
    if a.no_skill:
        return
    for h in g.get_all_heroes():
        for cd in getattr(h, "skill_cooldowns", []) or []:
            try:
                cd.timer = 0
            except Exception:
                pass


# Pengukur biaya cache-miss di dalam kondisi game sebenarnya. Dipasang
# HANYA kalau diminta, supaya tidak menambah overhead pada pengukuran
# fase biasa.
_MISS_MS = [0.0]
if a.miss_time:
    import heroes as _HM

    _orig_render_sprite = _HM._hero_render_sprite

    def _timed_render_sprite(key, hero_type, hero, renderer):
        _t = time.perf_counter()
        try:
            return _orig_render_sprite(key, hero_type, hero, renderer)
        finally:
            _MISS_MS[0] += time.perf_counter() - _t

    _HM._hero_render_sprite = _timed_render_sprite


def keep_alive():
    if not a.keep_alive:
        return
    for h in g.get_all_heroes():
        h.hp = h.max_hp
        h.alive = True


for _ in range(a.warm):
    force_skills()
    g.update()
    keep_alive()
    g.draw()

# Bersihkan rata-rata supaya masa pemanasan (cache masih dingin) tidak
# mencemari angka yang dilaporkan.
perf.PHASES.avg.clear()
try:
    import heroes as _H
    _H.reset_hero_stats()
except Exception:
    pass

t0 = time.perf_counter()
for _ in range(a.frames):
    force_skills()
    g.update()
    keep_alive()
    g.draw()
t1 = time.perf_counter()

ms = (t1 - t0) * 1000.0 / a.frames
print("")
print("kualitas=%-6s minion=%-4d hero=%-3d (hidup %d) level=%-3d partikel=%d" %
      (a.quality, len(g.minions), len(g.get_all_heroes()),
       len([h for h in g.get_all_heroes() if h.alive]), a.level,
       len(getattr(g.effects, "particles", None) or [])))
print("update+draw : %.2f ms/frame -> %.1f FPS rata-rata" %
      (ms, 1000.0 / ms))
print("")
print("%-12s %9s %7s" % ("fase", "ms/frame", "%"))
tot = sum(perf.PHASES.avg.values())
for name, v in sorted(perf.PHASES.avg.items(),
                      key=lambda kv: -kv[1])[:a.top]:
    print("%-12s %9.3f %6.1f%%" % (name, v,
                                   100.0 * v / tot if tot else 0.0))
print("%-12s %9.3f" % ("TOTAL fase", tot))

if a.miss_time:
    print("biaya cache-miss  : %.3f ms/frame (di dalam _hero_render_sprite)"
          % (_MISS_MS[0] * 1000.0 / a.frames))

# Statistik cache sprite hero: inilah penentu biaya fase e.hero.
# "geom hit" tinggi = kotak crop dipakai ulang (get_bounding_rect tidak
# dipanggil lagi); "deferred" = hero yang render penuhnya ditunda karena
# jatah frame habis.
try:
    import heroes as _H
    cs = _H.hero_cache_stats()
    gs = _H.hero_geom_stats()
    tot_r = cs["hits"] + cs["misses"] + cs["deferred"]
    print("")
    print("cache sprite hero : hit %d  miss %d  tunda %d  (hit rate %.1f%%)"
          % (cs["hits"], cs["misses"], cs["deferred"],
             100.0 * cs["hits"] / tot_r if tot_r else 0.0))
    print("geometri crop     : pose %d  dipakai-ulang %d  diukur %d  "
          "melebar %d  canvas %d"
          % (gs["poses"], gs["hits"], gs["measure"], gs["grow"], gs["canvas"]))
except Exception as exc:
    print("[bench_phase] statistik cache gagal: %s" % exc)
