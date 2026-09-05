# ================================
# tools/bench_hero_miss.py
# Biaya SATU cache-miss render hero, dipecah per tahap.
#
# Kenapa alat ini ada: bench_phase/bench_wave memberi ms/frame total,
# dan selisih 1 ms hilang di dalam noise antar-run. Alat ini mengukur
# langsung fungsi yang diubah (_hero_render_sprite) sehingga efek
# optimasi jalur miss terlihat jelas, bukan terkubur.
#
# Contoh:
#   python3 tools/bench_hero_miss.py --quality low
#   MYSTIC_HERO_GEOM=0 python3 tools/bench_hero_miss.py --quality low
# ================================
import os
import sys
import time
import argparse

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ap = argparse.ArgumentParser()
ap.add_argument("--quality", default="low",
                choices=["low", "medium", "high"])
ap.add_argument("--iters", type=int, default=24)
a = ap.parse_args()

import pygame  # noqa: E402
pygame.init()
from mobile import perf  # noqa: E402
perf.install_font_cache()
perf.Quality.apply(a.quality)
screen = pygame.display.set_mode((1280, 720))
import _core  # noqa: E402,F401
from _entity import Hero  # noqa: E402
import heroes as H  # noqa: E402

TYPES = ["sylara", "vex", "grimjaw", "kaizen", "thorne", "zephyr",
         "abaddon", "alchemist", "razak", "kunkka", "gornak", "varkul"]
heroes = []
for t in TYPES:
    try:
        heroes.append(Hero(t, "blue", 640, 360))
    except Exception:
        pass

# ── pecah biaya per tahap ──
T = {"render": 0.0, "bbox": 0.0, "finish": 0.0, "n": 0.0}
_o_call = H._call_renderer_on_canvas
def _call(renderer, canvas, entity, x, y):
    t = time.perf_counter()
    r = _o_call(renderer, canvas, entity, x, y)
    T["render"] += time.perf_counter() - t
    return r
_o_fin = H._finish_hd_sprite
def _fin(sprite, team="blue"):
    t = time.perf_counter()
    r = _o_fin(sprite, team)
    T["finish"] += time.perf_counter() - t
    return r
_o_ss = pygame.transform.smoothscale
def _ss(s, size):
    t = time.perf_counter()
    r = _o_ss(s, size)
    T["scale"] = T.get("scale", 0.0) + time.perf_counter() - t
    return r
H._call_renderer_on_canvas = _call
H._finish_hd_sprite = _fin
H.pygame.transform.smoothscale = _ss

# Pemanasan: biarkan ukuran canvas dipelajari dulu (satu putaran penuh).
for i in range(len(heroes)):
    h = heroes[i]
    H.clear_hero_geom_cache()
    for ph in range(4):
        h.pulse = ph * 0.31
        H._hero_render_sprite((h.hero_type, "blue", 1, 1, "idle", ph),
                              h.hero_type, h,
                              H.HERO_RENDERERS.get(h.hero_type)
                              or H.BOSS_RENDERERS.get(h.hero_type))

# Ukur: kunci SELALU baru (kondisi nyata pose skill) tetapi ukuran
# canvas sudah dipelajari - persis kondisi di dalam game.
for k in list(T):
    T[k] = 0.0
t0 = time.perf_counter()
for i in range(a.iters * len(heroes)):
    h = heroes[i % len(heroes)]
    h.pulse = (i * 0.017) % 1.0
    key = (h.hero_type, "blue", 1, 1, "skill", i)
    r = H._hero_render_sprite(key, h.hero_type, h,
                              H.HERO_RENDERERS.get(h.hero_type)
                              or H.BOSS_RENDERERS.get(h.hero_type))
    if r is not False and r is not None:
        T["n"] += 1
t1 = time.perf_counter()

n = max(1.0, T["n"])
print("")
print("kualitas=%s   %d render penuh (kunci selalu baru)" %
      (a.quality, int(n)))
print("  TOTAL          %8.3f ms per miss" % ((t1 - t0) * 1000.0 / n))
for k in ("render", "scale", "finish"):
    print("    %-10s %8.3f ms" % (k, T.get(k, 0.0) * 1000.0 / n))
sisa = (t1 - t0) - sum(T.get(k, 0.0) for k in ("render", "scale", "finish"))
print("    %-10s %8.3f ms  (get_bounding_rect + crop + alokasi)"
      % ("lainnya", sisa * 1000.0 / n))
halves = sorted((H._HERO_CANVAS_HALF.items()
                 if H._HERO_CANVAS_HALF else
                 [("-", H._canvas_size_for(h) // 2) for h in heroes]),
                key=lambda kv: kv[1])
if halves:
    print("  canvas dipelajari: terkecil %d px, terbesar %d px "
          "(dulu selalu %d-%d px)"
          % (halves[0][1] * 2, halves[-1][1] * 2,
             min(H._canvas_size_for(h) for h in heroes),
             max(H._canvas_size_for(h) for h in heroes)))
