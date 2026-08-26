"""Headless test untuk sprite HD Thorne (assets/heroes).

T1: aset ter-load -> pose idle/walk/attack (dua arah) memakai sprite HD.
T2: fallback -> kalau aset "hilang", render prosedural lama tetap jalan.
T3: pipeline penuh render_hero (ukur+scale+cache) tidak error dan
    screenshot preview tersimpan untuk inspeksi visual.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((320, 200))  # convert_alpha butuh display aktif

import heroes  # noqa: E402
from heroes import _bundle as _b  # noqa: E402
from heroes.thorne import draw_thorne  # noqa: E402  (jalur impor lama)

NS = _b._NS_thorne

import tempfile  # noqa: E402

OUT = os.path.join(tempfile.gettempdir(), "thorne_hd_preview.png")


class Probe:
    """Objek mirip Hero secukupnya untuk renderer thorne."""

    def __init__(self, direction=1):
        self.x = 0.0
        self.y = 0.0
        self.pulse = 12.0
        self.direction = direction
        self.facing = direction
        self.timer = 0
        self.attack_cooldown = 45
        self.active_skill = None
        self.active_skill_timer = 0
        self.level = 1
        self.team = "blue"
        self.range = 60
        self._th_attack_progress = 0.0
        self._th_projectiles = []
        self.alive = True


def dark_bg(w, h):
    bg = pygame.Surface((w, h))
    for y in range(h):
        t = y / h
        pygame.draw.line(bg, (int(10 + t * 16), int(14 + t * 20),
                              int(36 + t * 44)), (0, y), (w, y))
    return bg


# ── T1: semua pose + arah memakai sprite HD ─────────────────────
NS._THORNE_SPRITE_CACHE.clear()
NS._THORNE_SPRITE_MISSING.clear()

surf = dark_bg(400, 200)
p = Probe(1)
NS._draw_thorne_idle(surf, p, 100, 100)
p.x = 1.0  # biar _detect_moving True lewat draw_thorne
draw_thorne(surf, p, 100, 100)  # entry point publik namespace
p._th_attack_progress = 0.45
NS._draw_thorne_attack(surf, p, 100, 100)
p2 = Probe(-1)
NS._draw_thorne_walk(surf, p2, 250, 100)
NS._draw_thorne_attack(surf, p2, 250, 100)

poses_loaded = {k[0] for k in NS._THORNE_SPRITE_CACHE}
assert poses_loaded == {"idle", "walk", "attack"}, \
    "sprite HD harus ter-load untuk idle/walk/attack, dapat: %s" % poses_loaded
dirs_loaded = {k[1] for k in NS._THORNE_SPRITE_CACHE}
assert dirs_loaded == {1, -1}, "dua arah harus ter-cache, dapat: %s" % dirs_loaded
print("T1 OK  - sprite HD (idle/walk/attack, 2 arah) ter-load & dipakai")

# ── T2: fallback prosedural kalau aset tidak ada ────────────────
orig_dir = NS._THORNE_ASSET_DIR
NS._THORNE_ASSET_DIR = os.path.join(orig_dir, "..", "heroes_TIDAK_ADA")
NS._THORNE_SPRITE_CACHE.clear()
NS._THORNE_SPRITE_MISSING.clear()

surf2 = dark_bg(400, 200)
NS._draw_thorne_idle(surf2, Probe(1), 100, 100)
NS._draw_thorne_walk(surf2, Probe(-1), 250, 100)
p3 = Probe(1)
p3._th_attack_progress = 0.45
NS._draw_thorne_attack(surf2, p3, 100, 100)
assert not NS._THORNE_SPRITE_CACHE, \
    "tanpa aset tidak boleh ada sprite ter-cache (fallback prosedural)"

NS._THORNE_ASSET_DIR = orig_dir
NS._THORNE_SPRITE_CACHE.clear()
NS._THORNE_SPRITE_MISSING.clear()
print("T2 OK  - fallback prosedural berfungsi tanpa aset")

# ── T3: pipeline penuh render_hero + preview visual ─────────────
bg = dark_bg(760, 240)
spots = [
    ("idle  ->", 1, None, 0.0),
    ("walk  ->", 1, "walk", 0.0),
    ("attack->", 1, "atk", 0.45),
]
x = 120
for label, facing, mode, prog in spots:
    p = Probe(facing)
    if mode == "atk":
        # Lewati deteksi serangan asli draw_thorne:
        # _th_attack_active + timer naik -> progress = (cd-timer)/(cd-1)
        p._th_attack_active = True
        p.timer = 25
        p.attack_timer = 25
    # pakai jalur render mentah (ukur + scale + blit) seperti in-game
    heroes._render_hero_raw("thorne", bg, p, x, 150)
    if mode == "walk":
        # panggilan kedua dgn x berubah -> _detect_moving True -> walk
        p.x += 2.0
        heroes._render_hero_raw("thorne", bg, p, x, 150)
    f = pygame.font.Font(None, 18)
    bg.blit(f.render(label, True, (220, 220, 255)), (x - 40, 210))
    x += 240

pygame.image.save(bg, OUT)
print("T3 OK  - render_hero pipeline jalan, preview:", OUT)
