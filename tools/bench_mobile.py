# ================================
# tools/bench_mobile.py
# Uji cepat: apakah patch performa & HUD sentuh berfungsi,
# dan berapa perbaikan FPS-nya. Jalankan dari root repo:
#     python tools/bench_mobile.py
# ================================
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

pygame.init()

USE_PATCH = "--nopatch" not in sys.argv

from mobile import platform_utils as plat   # noqa: E402
from mobile import perf                     # noqa: E402

if USE_PATCH:
    perf.install_font_cache()

screen = pygame.display.set_mode((plat.LOGICAL_WIDTH, plat.LOGICAL_HEIGHT))

import _core                                # noqa: E402,F401
from game import Game                       # noqa: E402
from _render import get_font                # noqa: E402
from mobile import touch as touch_mod       # noqa: E402
from mobile import hud as hud_mod           # noqa: E402
from mobile import debug as debug_mod       # noqa: E402

game = Game(screen, level_number=1)
hud = hud_mod.TouchHUD(get_font)
touch = touch_mod.TouchManager(use_finger_events=False)
dbg = debug_mod.DebugOverlay(get_font)
dbg.set_mode(debug_mod.MODE_FULL)
clock = pygame.time.Clock()

FRAMES = 240
for _ in range(60):                      # pemanasan
    game.update()
    game.draw()

t0 = time.perf_counter()
for i in range(FRAMES):
    touch.update()
    hud.sync(game, "game", False)
    game.update()
    game.draw()
    hud.draw(screen, i)
    dbg.update(clock, game)
    dbg.draw(screen, clock, game, touch)
    clock.tick(0)
elapsed = time.perf_counter() - t0

print("\n=== HASIL ===")
print("patch font/teks : %s" % ("AKTIF" if USE_PATCH else "MATI"))
print("%d frame dalam %.2fs -> %.1f FPS (headless)"
      % (FRAMES, elapsed, FRAMES / elapsed))
print("ms per frame    : %.2f" % (elapsed / FRAMES * 1000))
print("statistik font  : %s" % perf.font_cache_stats())

# ── uji gesture ──
print("\n=== UJI GESTURE ===")
touch._down(0, (640, 360))
touch.update()
time.sleep(0.5)
touch.update()
acts = [a.kind for a in touch.collect()]
print("tahan 0.5 dtk ->", acts, "(harus ada long_press)")
touch._up(0, (640, 360))
print("lepas          ->", [a.kind for a in touch.collect()])

touch._down(1, (600, 300))
touch._motion(1, (600, 260))
touch._motion(1, (600, 200))
touch._up(1, (600, 200))
print("geser ke atas  ->", [a.kind for a in touch.collect()],
      "(harus ada drag + scroll)")

print("\n=== UJI HUD ===")
hud.sync(game, "game", False)
for name, btn in hud.buttons.items():
    if btn.visible:
        print("  %-12s rect=%s hit=%s" % (name, tuple(btn.rect),
                                          hud.hit_test(btn.rect.center)))
pygame.quit()
