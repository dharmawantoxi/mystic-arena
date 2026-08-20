# ================================
# tools/blit_audit.py
# Cari SIAPA yang masih blit surface transparan berukuran besar.
#
# Di HP kelas Cortex-A53, alpha blit ~222 ns/piksel. Anggaran 30 FPS
# hanya ~150.000 piksel alpha per frame. Skrip ini menghitung piksel
# alpha yang di-blit per frame, dikelompokkan per lokasi kode.
#
#     python tools/blit_audit.py [--frames 120] [--quality low]
# ================================
import os, sys, argparse, traceback, collections
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ap = argparse.ArgumentParser()
ap.add_argument("--frames", type=int, default=120)
ap.add_argument("--quality", default="low")
ap.add_argument("--warm", type=int, default=4000)
ap.add_argument("--scene", default="game", choices=["game", "intro", "end"])
a = ap.parse_args()

import pygame; pygame.init()
from mobile import perf
perf.install_font_cache(); perf.Quality.apply(a.quality)
perf.Quality.cheap_alpha = False        # tiru HP: alpha mahal

real = pygame.display.set_mode((1280, 720))

STATS = collections.Counter()
COUNT = collections.Counter()


class SpySurface(pygame.Surface):
    """Surface asli (agar pygame.draw menerimanya) + pencatat blit."""

    def blit(self, source, dest=(0, 0), area=None, special_flags=0):
        try:
            w, h = (area[2], area[3]) if area is not None \
                else source.get_size()
            has_alpha = bool(source.get_flags() & pygame.SRCALPHA) or \
                source.get_alpha() is not None
            if has_alpha and w * h > 5000:
                st = traceback.extract_stack(limit=4)[:-1]
                key = " <- ".join(
                    "%s:%d %s" % (os.path.basename(f.filename), f.lineno,
                                  f.name) for f in reversed(st))
                STATS[key] += w * h
                COUNT[key] += 1
        except Exception:
            pass
        return super().blit(source, dest, area, special_flags)


screen = SpySurface((1280, 720))

import _core
from game import Game
g = Game(screen, level_number=1)
for attr in ("ui", "ui_renderer", "effects", "map_renderer"):
    o = getattr(g, attr, None)
    if o is not None and hasattr(o, "screen"):
        try: o.screen = screen
        except Exception: pass

if a.scene != "intro":
    g.level_intro = None; g.boss_intro = None
for _ in range(a.warm):
    g.update(); g.draw()

STATS.clear(); COUNT.clear()
for _ in range(a.frames):
    g.update(); g.draw()

total = sum(STATS.values()) / a.frames
print("\n═══ ALPHA BLIT BESAR (>5.000 px) — adegan '%s', kualitas %s ═══"
      % (a.scene, a.quality))
print("rata-rata %.0f piksel/frame" % total)
print("anggaran HP untuk 30 FPS: ~150.000 px/frame\n")
print("%-86s %10s %6s %8s" % ("lokasi", "px/frame", "kali", "ms HP"))
for k, v in STATS.most_common(15):
    print("%-86s %10.0f %6.1f %7.1f" %
          (k, v / a.frames, COUNT[k] / a.frames,
           v / a.frames * 222e-9 * 1000))
print("\nTOTAL perkiraan biaya alpha blit di HP: %.0f ms/frame"
      % (total * 222e-9 * 1000))
