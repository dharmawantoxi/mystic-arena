"""Headless test untuk sprite kastil HD (assets/castles).

T1: aset ter-load -> Castle.draw pakai sprite (bukan prosedural).
T2: fallback -> kalau aset "hilang", render prosedural tetap jalan.
T3: frame game penuh (update+draw) tidak error, screenshot tersimpan.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()
pygame.display.set_mode((320, 200))  # convert_alpha butuh display aktif

# Urutan penting: _core dulu (entry point game) supaya circular
# import _core <-> _entity terurai seperti saat game dijalankan.
import _core  # noqa: E402
import _entity  # noqa: E402
from _entity import Castle  # noqa: E402

import tempfile  # noqa: E402

OUT = os.path.join(tempfile.gettempdir(), "castle_hd_preview.png")


def dark_bg(w, h):
    bg = pygame.Surface((w, h))
    for y in range(h):
        t = y / h
        pygame.draw.line(bg, (int(8 + t * 14), int(12 + t * 18),
                              int(34 + t * 40)), (0, y), (w, y))
    return bg


# ── T1: aset tersedia -> semua (tim, level) memakai sprite ──────
ok = True
for team in ("blue", "red"):
    for lvl in range(1, 6):
        c = Castle(100, 620, team)
        c.level = lvl
        c._apply_level_stats()
        bg = dark_bg(300, 240)
        c.x, c.y = 150, 190
        c.draw(bg)
        assert c._render_cache_is_asset.get(
            "castle_%s_L%d" % (team, lvl), False), \
            "%s L%d harus memakai sprite HD" % (team, lvl)
        ok = True
print("T1 OK  - 10 sprite HD (blue+red, L1-L5) ter-load & dipakai")

# ── T2: fallback prosedural kalau aset tidak ada ────────────────
_entity._CASTLE_ASSET_DIR = os.path.join(os.path.dirname(
    os.path.abspath(_entity.__file__)), "assets", "castles_TIDAK_ADA")
_entity._CASTLE_ASSET_CACHE.clear()
c = Castle(150, 190, "blue")
c.level = 3
c._apply_level_stats()
bg = dark_bg(300, 240)
c.draw(bg)
assert not c._render_cache_is_asset.get("castle_blue_L3", True), \
    "tanpa aset harus fallback ke render prosedural"
# kembalikan aset
import _entity as _e2  # noqa: E402
_e2._CASTLE_ASSET_DIR = os.path.join(os.path.dirname(
    os.path.abspath(_e2.__file__)), "assets", "castles")
_e2._CASTLE_ASSET_CACHE.clear()
_e2._CASTLE_ASSET_MISSING.clear()
print("T2 OK  - fallback prosedural berfungsi tanpa aset")

# ── T3: frame game penuh + screenshot ──────────────────────────
screen = pygame.display.set_mode((1280, 720))
from _core import Game  # noqa: E402
game = Game(screen, level_number=1)
# Naikkan kedua kastil ke level tinggi biar evolusinya terlihat
for _ in range(4):
    game.blue_base.upgrade()
for _ in range(3):
    game.red_base.upgrade()
for i in range(12):
    game.update()
    game.draw()
pygame.image.save(screen, OUT)
assert os.path.exists(OUT)
print("T3 OK  - 12 frame update+draw bersih, screenshot:", OUT)
print("SEMUA TEST LULUS" if ok else "GAGAL")
