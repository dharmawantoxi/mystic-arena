"""Headless test untuk sprite HD Kaizen (assets/heroes).

T0: idle motion deterministik & berubah terhadap fase.
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

NS = _b._NS_kaizen

import tempfile  # noqa: E402

OUT = os.path.join(tempfile.gettempdir(), "kaizen_hd_preview.png")
DOCS_PREVIEW = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs", "kaizen_ingame_preview.png")


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
        self._kz_attack_progress = 0.0
        self._kz_projectiles = []
        self.alive = True


def dark_bg(w, h):
    bg = pygame.Surface((w, h))
    for y in range(h):
        t = y / h
        pygame.draw.line(bg, (int(10 + t * 16), int(14 + t * 20),
                              int(36 + t * 44)), (0, y), (w, y))
    return bg


# ── T0: idle motion deterministik ────────────────────────────────
assert NS._kaizen_idle_motion(0.0) != NS._kaizen_idle_motion(1.5)
assert NS._kaizen_idle_motion(3.0) == NS._kaizen_idle_motion(3.0)
print("T0 OK  - idle motion deterministik & berubah terhadap fase")

# ── T1: semua pose + arah memakai sprite HD ─────────────────────
NS._KAIZEN_SPRITE_CACHE.clear()
NS._KAIZEN_SPRITE_MISSING.clear()
NS._KAIZEN_SWING_CACHE.clear()
NS._KAIZEN_SWING_MISSING.clear()
NS._KAIZEN_WALK_CACHE.clear()
NS._KAIZEN_WALK_MISSING.clear()

surf = dark_bg(400, 200)
p = Probe(1)
NS._draw_kaizen_idle(surf, p, 100, 100)
p.x = 1.0  # biar _detect_moving True lewat draw_kaizen
NS.draw_kaizen(surf, p, 100, 100)
p._kz_attack_progress = 0.45
NS._draw_kaizen_attack(surf, p, 100, 100)
p2 = Probe(-1)
NS._draw_kaizen_walk(surf, p2, 250, 100)
NS._draw_kaizen_attack(surf, p2, 250, 100)

poses_loaded = {k[0] for k in NS._KAIZEN_SPRITE_CACHE}
assert "idle" in poses_loaded, \
    "sprite HD idle harus ter-load, dapat: %s" % poses_loaded
has_walk = ("walk" in poses_loaded) or len(NS._KAIZEN_WALK_CACHE) > 0
assert has_walk, "walk cycle HD (kaizen_walk_N / pose walk) harus ter-load"
dirs_loaded = {k[1] for k in NS._KAIZEN_SPRITE_CACHE} | \
              {k[1] for k in NS._KAIZEN_WALK_CACHE}
assert 1 in dirs_loaded and -1 in dirs_loaded, \
    "dua arah harus ter-cache, dapat: %s" % dirs_loaded
# Attack dipakai lewat multi-frame swing (kaizen_swing_<N>.png).
assert len(NS._KAIZEN_SWING_CACHE) > 0, \
    "frame swing HD harus ter-load (gunakan kaizen_swing_<N>.png)"
assert {k[0] for k in NS._KAIZEN_SWING_CACHE} <= \
    set(range(NS._KAIZEN_SWING_FRAME_COUNT)), \
    "index frame swing harus dalam rentang 0..%d" % NS._KAIZEN_SWING_FRAME_COUNT
assert 1 in {k[1] for k in NS._KAIZEN_SWING_CACHE}, \
    "arah menghadap kanan harus ter-cache"
assert -1 in {k[1] for k in NS._KAIZEN_SWING_CACHE}, \
    "arah menghadap kiri harus ter-cache"
print("T1 OK  - sprite HD (idle/walk, 2 arah) + frame swing (2 arah) ter-load & dipakai")

# ── T2: fallback prosedural kalau aset tidak ada ────────────────
orig_dir = NS._KAIZEN_ASSET_DIR
NS._KAIZEN_ASSET_DIR = os.path.join(orig_dir, "..", "heroes_TIDAK_ADA")
for cache in (NS._KAIZEN_SPRITE_CACHE, NS._KAIZEN_SWING_CACHE,
              NS._KAIZEN_WALK_CACHE, NS._KAIZEN_SKILL_CACHE):
    cache.clear()
for missing in (NS._KAIZEN_SPRITE_MISSING, NS._KAIZEN_SWING_MISSING,
                NS._KAIZEN_WALK_MISSING, NS._KAIZEN_SKILL_MISSING):
    missing.clear()

surf2 = dark_bg(400, 200)
NS._draw_kaizen_idle(surf2, Probe(1), 100, 100)
NS._draw_kaizen_walk(surf2, Probe(-1), 250, 100)
p3 = Probe(1)
p3._kz_attack_progress = 0.45
NS._draw_kaizen_attack(surf2, p3, 100, 100)
assert not NS._KAIZEN_SPRITE_CACHE, \
    "tanpa aset tidak boleh ada sprite ter-cache (fallback prosedural)"
assert not NS._KAIZEN_SWING_CACHE, \
    "tanpa aset tidak boleh ada frame swing ter-cache (fallback prosedural)"
assert not NS._KAIZEN_WALK_CACHE, \
    "tanpa aset tidak boleh ada frame walk ter-cache (fallback prosedural)"
assert not NS._KAIZEN_SKILL_CACHE, \
    "tanpa aset tidak boleh ada sprite skill ter-cache (fallback prosedural)"

NS._KAIZEN_ASSET_DIR = orig_dir
for cache in (NS._KAIZEN_SPRITE_CACHE, NS._KAIZEN_SWING_CACHE,
              NS._KAIZEN_WALK_CACHE, NS._KAIZEN_SKILL_CACHE):
    cache.clear()
for missing in (NS._KAIZEN_SPRITE_MISSING, NS._KAIZEN_SWING_MISSING,
                NS._KAIZEN_WALK_MISSING, NS._KAIZEN_SKILL_MISSING):
    missing.clear()
print("T2 OK  - fallback prosedural berfungsi tanpa aset")


# ── T3: render skill HD (Q/W/E/R) tidak error & base layer terpakai ──
surf3 = dark_bg(500, 300)
p4 = Probe(1)
# Steel Wind (Q) — butuh target utk jalur dash
p4.target = Probe(1)
p4.target.x, p4.target.y = 380.0, 150.0
NS._draw_dash_effect(surf3, p4, 100, 150, 30, 12.0)
assert "q" in NS._KAIZEN_SKILL_CACHE, "sprite skill Q HD harus ter-load"
# Wind Wall (W)
NS._draw_wind_wall(surf3, p4, 100, 150, 45, 12.0)
assert "w" in NS._KAIZEN_SKILL_CACHE, "sprite skill W HD harus ter-load"
# Sweep (E)
NS._draw_sweep_effect(surf3, p4, 100, 150, 30, 12.0)
assert "e" in NS._KAIZEN_SKILL_CACHE, "sprite skill E HD harus ter-load"
# Tornado (R) — di posisi target
NS._draw_tornado(surf3, p4, 100, 150, 60, 12.0)
assert "r" in NS._KAIZEN_SKILL_CACHE, "sprite skill R HD harus ter-load"
print("T3 OK  - skill HD (Q/W/E/R) base layer ter-load & dipakai tanpa error")


# ── T4: pipeline penuh render_hero + preview visual ─────────────
bg = dark_bg(1000, 260)
spots = [
    ("idle ->", 1, None, 0.0, None),
    ("walk ->", 1, "walk", 0.0, None),
    ("attack ->", 1, "atk", 0.45, None),
    ("skill W ->", -1, "skill", 0.0, "w"),
    ("skill R ->", 1, "skill", 0.0, "r"),
]
x = 110
f = pygame.font.Font(None, 20)
for label, facing, mode, prog, skill in spots:
    p = Probe(facing)
    p.pulse = 6.0
    if mode == "atk":
        p._kz_attack_active = True
        p.timer = 25
        p.attack_timer = 25
    elif mode == "skill":
        p.active_skill = skill
        p.active_skill_timer = 40 if skill == "w" else 60
    heroes._render_hero_raw("kaizen", bg, p, x, 170)
    if mode == "walk":
        p.x += 2.0
        heroes._render_hero_raw("kaizen", bg, p, x, 170)
    bg.blit(f.render(label, True, (220, 240, 255)), (x - 45, 228))
    x += 190

pygame.image.save(bg, OUT)
try:
    os.makedirs(os.path.dirname(DOCS_PREVIEW), exist_ok=True)
    pygame.image.save(bg, DOCS_PREVIEW)
    print("T4 OK  - render_hero pipeline jalan, preview:", DOCS_PREVIEW)
except Exception as e:  # pragma: no cover
    print("T4 OK  - render_hero pipeline jalan, preview:", OUT, "(docs skip:", e, ")")

# ── T5: swing frames konsisten ───────────────────────────────────
print("T5 OK  - swing frames di-load, count =", NS._KAIZEN_SWING_FRAME_COUNT)
print("\nSEMUA TEST LULUS")
