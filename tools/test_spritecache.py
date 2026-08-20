# ================================
# tools/test_spritecache.py
# Uji kebenaran cache sprite: hasil lewat cache HARUS identik
# piksel-per-piksel dengan gambar langsung.
#
#     python tools/test_spritecache.py
# ================================
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["MYSTIC_SPRITE_CACHE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

pygame.init()
from mobile import perf                       # noqa: E402
perf.install_font_cache()
screen = pygame.display.set_mode((1280, 720))

import _core                                  # noqa: E402,F401
from _entity import Minion                    # noqa: E402
from minions import MINION_RENDERERS, render_minion   # noqa: E402
from mobile import spritecache                # noqa: E402

W, H = 400, 400
CX, CY = 200, 220

total = same = diff = 0
laporan = []

for mtype in MINION_RENDERERS:
    for team in ("blue", "red"):
        for direction in (1, -1):
            for moving in (True, False):
                try:
                    m = Minion(mtype, team, lane="mid")
                except TypeError:
                    m = Minion(mtype, team)
                m.x, m.y = CX, CY
                m.direction = direction
                m.is_moving = moving
                m.anim_time = 12
                m.walk_cycle = 6
                m.spawn_anim = 0
                m.attack_anim_timer = 0
                m.hurt_flash_timer = 0
                m.slow_timer = 0

                # (1) gambar langsung
                a = pygame.Surface((W, H), pygame.SRCALPHA)
                MINION_RENDERERS[mtype](a, m, CX, CY)

                # (2) lewat cache (dua kali: miss lalu hit)
                spritecache.clear()
                b = pygame.Surface((W, H), pygame.SRCALPHA)
                render_minion(mtype, b, m, CX, CY)
                c = pygame.Surface((W, H), pygame.SRCALPHA)
                render_minion(mtype, c, m, CX, CY)

                total += 2
                for label, surf in (("miss", b), ("hit", c)):
                    if pygame.image.tobytes(a, "RGBA") == \
                            pygame.image.tobytes(surf, "RGBA"):
                        same += 1
                    else:
                        diff += 1
                        laporan.append("%s/%s/dir%+d/%s [%s]" % (
                            mtype, team, direction,
                            "jalan" if moving else "diam", label))

print("\n=== UJI KESAMAAN PIKSEL CACHE SPRITE ===")
print("kombinasi diuji : %d" % total)
print("identik         : %d" % same)
print("berbeda         : %d" % diff)
if laporan:
    print("kasus berbeda   :")
    for r in laporan[:20]:
        print("   -", r)
    print("\nARTINYA: cache memotong sebagian gambar (bbox kurang besar)")
    print("atau renderer memakai posisi dunia. Perbesar _bbox() di")
    print("mobile/spritecache.py, atau matikan cache untuk tipe ini.")
else:
    print("\nAMAN: cache menghasilkan gambar yang identik.")

print("statistik cache :", spritecache.stats())
pygame.quit()
sys.exit(1 if diff else 0)
