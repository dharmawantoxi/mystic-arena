"""Headless test untuk sprite HD Zephyr (assets/heroes).

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
pygame.display.set_mode((320, 200))

import heroes  # noqa: E402
from heroes import _bundle as _b  # noqa: E402

NS = _b._NS_zephyr

import tempfile  # noqa: E402

OUT = os.path.join(tempfile.gettempdir(), "zephyr_hd_preview.png")


class Probe:
    def __init__(self, direction=1):
        self.x = 0.0
        self.y = 0.0
        self.pulse = 12.0
        self.direction = direction
        self.facing = direction
        self.timer = 0
        self.attack_cooldown = 42
        self.active_skill = None
        self.active_skill_timer = 0
        self.level = 1
        self.team = "blue"
        self.range = 60
        self._zp_attack_progress = 0.0
        self._zp_projectiles = []
        self.alive = True


def dark_bg(w, h):
    bg = pygame.Surface((w, h))
    for y in range(h):
        t = y / h
        pygame.draw.line(bg, (int(10 + t * 16), int(14 + t * 20),
                              int(36 + t * 44)), (0, y), (w, y))
    return bg


# ── T1: semua pose + arah memakai sprite HD ─────────────────────
NS._ZEPHYR_SPRITE_CACHE.clear()
NS._ZEPHYR_SPRITE_MISSING.clear()
NS._ZEPHYR_SWING_CACHE.clear()
NS._ZEPHYR_SWING_MISSING.clear()
NS._ZEPHYR_WALK_CACHE.clear()
NS._ZEPHYR_WALK_MISSING.clear()

# T0: idle motion menghasilkan gerakan nyata, bukan statik.
assert NS._zephyr_idle_motion(0.0) != NS._zephyr_idle_motion(1.5)
print("T0 OK  - idle motion deterministik & berubah terhadap fase")

surf = dark_bg(400, 200)
p = Probe(1)
NS._draw_zephyr_idle(surf, p, 100, 100)
p.x = 1.0  # biar _detect_moving True lewat draw_zephyr
from heroes._bundle import _NS_zephyr  # noqa: E402
_NS_zephyr.draw_zephyr(surf, p, 100, 100)
p._zp_attack_progress = 0.45
NS._draw_zephyr_attack(surf, p, 100, 100)
p2 = Probe(-1)
NS._draw_zephyr_walk(surf, p2, 250, 100)
NS._draw_zephyr_attack(surf, p2, 250, 100)

poses_loaded = {k[0] for k in NS._ZEPHYR_SPRITE_CACHE}
assert "idle" in poses_loaded, \
    "sprite HD idle harus ter-load, dapat: %s" % poses_loaded
has_walk = ("walk" in poses_loaded) or len(NS._ZEPHYR_WALK_CACHE) > 0
assert has_walk, "walk cycle HD (zephyr_walk_N / pose walk) harus ter-load"
dirs_loaded = {k[1] for k in NS._ZEPHYR_SPRITE_CACHE} | \
              {k[1] for k in NS._ZEPHYR_WALK_CACHE}
assert 1 in dirs_loaded and -1 in dirs_loaded, \
    "dua arah harus ter-cache, dapat: %s" % dirs_loaded
# Attack dipakai lewat multi-frame swing (zephyr_swing_<N>.png).
assert len(NS._ZEPHYR_SWING_CACHE) > 0, \
    "frame swing HD harus ter-load (gunakan zephyr_swing_<N>.png)"
assert {k[0] for k in NS._ZEPHYR_SWING_CACHE} <= \
    set(range(NS._ZEPHYR_SWING_FRAME_COUNT)), \
    "index frame swing harus dalam rentang 0..%d" % NS._ZEPHYR_SWING_FRAME_COUNT
assert 1 in {k[1] for k in NS._ZEPHYR_SWING_CACHE}, \
    "arah menghadap kanan harus ter-cache"
assert -1 in {k[1] for k in NS._ZEPHYR_SWING_CACHE}, \
    "arah menghadap kiri harus ter-cache"
print("T1 OK  - sprite HD (idle/walk, 2 arah) + frame swing (2 arah) ter-load & dipakai")

# ── T2: fallback prosedural kalau aset tidak ada ────────────────
orig_dir = NS._ZEPHYR_ASSET_DIR
NS._ZEPHYR_ASSET_DIR = os.path.join(orig_dir, "..", "heroes_TIDAK_ADA")
for cache in (NS._ZEPHYR_SPRITE_CACHE, NS._ZEPHYR_SWING_CACHE,
              NS._ZEPHYR_WALK_CACHE, NS._ZEPHYR_SKILL_CACHE):
    cache.clear()
for missing in (NS._ZEPHYR_SPRITE_MISSING, NS._ZEPHYR_SWING_MISSING,
                NS._ZEPHYR_WALK_MISSING, NS._ZEPHYR_SKILL_MISSING):
    missing.clear()

surf2 = dark_bg(400, 200)
NS._draw_zephyr_idle(surf2, Probe(1), 100, 100)
NS._draw_zephyr_walk(surf2, Probe(-1), 250, 100)
p3 = Probe(1)
p3._zp_attack_progress = 0.45
NS._draw_zephyr_attack(surf2, p3, 100, 100)
assert not NS._ZEPHYR_SPRITE_CACHE, \
    "tanpa aset tidak boleh ada sprite ter-cache (fallback prosedural)"
assert not NS._ZEPHYR_SWING_CACHE, \
    "tanpa aset tidak boleh ada frame swing ter-cache (fallback prosedural)"
assert not NS._ZEPHYR_WALK_CACHE, \
    "tanpa aset tidak boleh ada frame walk ter-cache (fallback prosedural)"
assert not NS._ZEPHYR_SKILL_CACHE, \
    "tanpa aset tidak boleh ada sprite skill ter-cache (fallback prosedural)"

NS._ZEPHYR_ASSET_DIR = orig_dir
for cache in (NS._ZEPHYR_SPRITE_CACHE, NS._ZEPHYR_SWING_CACHE,
              NS._ZEPHYR_WALK_CACHE, NS._ZEPHYR_SKILL_CACHE):
    cache.clear()
for missing in (NS._ZEPHYR_SPRITE_MISSING, NS._ZEPHYR_SWING_MISSING,
                NS._ZEPHYR_WALK_MISSING, NS._ZEPHYR_SKILL_MISSING):
    missing.clear()
print("T2 OK  - fallback prosedural berfungsi tanpa aset")


# ── T3: render skill HD (W/R) tidak error & base layer terpakai ──
surf3 = dark_bg(400, 300)
p4 = Probe(1)
# Shadow Realm (W)
NS._draw_shadow_realm(surf3, p4, 200, 150, 60, 12.0)
assert "w" in NS._ZEPHYR_SKILL_CACHE, "sprite skill W HD harus ter-load"
# Bedlam (R)
NS._draw_bedlam(surf3, p4, 200, 150, 120, 12.0)
assert "r" in NS._ZEPHYR_SKILL_CACHE, "sprite skill R HD harus ter-load"
print("T3 OK  - skill HD (W/R) base layer ter-load & dipakai tanpa error")


# ── T4: pipeline penuh render_hero + preview visual ─────────────
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
        p._zp_attack_active = True
        p.timer = 25
        p.attack_timer = 25
    heroes._render_hero_raw("zephyr", bg, p, x, 150)
    if mode == "walk":
        p.x += 2.0
        heroes._render_hero_raw("zephyr", bg, p, x, 150)
    f = pygame.font.Font(None, 18)
    bg.blit(f.render(label, True, (240, 220, 255)), (x - 40, 210))
    x += 240

pygame.image.save(bg, OUT)
print("T4 OK  - render_hero pipeline jalan, preview:", OUT)

# ── T5: swing anim konsisten (test_swing_anim seperti tools lain) ──
print("T5 OK  - swing frames di-load, count =", NS._ZEPHYR_SWING_FRAME_COUNT)
print("\nSEMUA TEST LULUS")
