#!/usr/bin/env python3
# ============================================================================
# tools/_shot_grimjaw_v3_combat.py
# ----------------------------------------------------------------------------
# Sheet preview LAPISAN FX HIDUP Grimjaw v3 (heroes/grimjaw_fx.py):
# sprite pipeline (cache) + lapisan layar 1:1 (trail, partikel, projectile,
# impact, skill FX) dalam beberapa adegan kunci. 100% prosedural.
#
# Jalankan:  python3 tools/_shot_grimjaw_v3_combat.py [out.png]
# ============================================================================
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import math
import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import heroes
from heroes import grimjaw_fx as F

W, H = 260, 240
COLS, ROWS = 4, 2
SHEET = pygame.Surface((W * COLS, H * ROWS), pygame.SRCALPHA)
SHEET.fill((26, 24, 30, 255))
# lantai sederhana supaya FX tanah terbaca
pygame.draw.rect(SHEET, (38, 34, 40, 255), (0, 0, SHEET.get_width(),
                                             SHEET.get_height()))
for gx in range(0, SHEET.get_width(), 26):
    pygame.draw.line(SHEET, (46, 42, 48, 255), (gx, 0),
                     (gx, SHEET.get_height()))
for gy in range(0, SHEET.get_height(), 26):
    pygame.draw.line(SHEET, (46, 42, 48, 255), (0, gy),
                     (SHEET.get_width(), gy))

DT = 1.0 / 60.0


class Unit:
    hero_type = "grimjaw"
    team = "blue"
    level = 1

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.facing = 1
        self.direction = 1
        self.pulse = 0.0
        self.radius = 16
        self.range = 60
        self.speed = 1.4
        self.hp = self.max_hp = 800
        self.alive = True
        self.timer = 0
        self.attack_cooldown = 45
        self.attack_timer = 0
        self._gj_attack_active = False
        self._gj_attack_progress = 0.0
        self._gj_crit_active = False
        self._gj_prev_timer = 0
        self._blade_fury_timer = 0
        self._heal_ward_timer = 0
        self._heal_ward_pos = (x, y)
        self._crit_buff_timer = 0
        self._omnislash_timer = 0
        self._omnislash_target = None
        self._moving_cached = False
        self.active_skill = None
        self.active_skill_timer = 0
        self.target = None
        self.color = (200, 96, 34)
        self.color_dark = (90, 40, 20)
        self.skill_damage = 120
        self.skill_range = 76


def snap(col, row, fn, frames=26):
    """Render satu adegan ke sel (col,row): pipeline + lapisan hidup."""
    ox, oy = col * W, row * H
    cell = SHEET.subsurface(pygame.Rect(ox, oy, W, H))
    # Koordinat hero HARUS koordinat di dalam `cell`: lapisan hidup
    # membaca hero.x/hero.y langsung (bukan parameter x,y render).
    u = Unit(W // 2, H - 58)
    fn(u)
    for i in range(frames):
        u.pulse += 0.1
        heroes.render_hero("grimjaw", cell, u, int(u.x), int(u.y))
        F.tick(DT)
        if callable(getattr(u, "_step", None)):
            u._step(i)
    F.reset_all()


def scene_walk(u):
    u._moving_cached = True
    u._step = lambda i: setattr(u, "x", u.x + 1.1)


def make_attack(u):
    def _step(i):
        u._gj_attack_active = True
        u._gj_attack_progress = min(1.0, i / 26.0)
        u.timer = max(0, 45 - i)
        if i == 16:                      # tepat saat bilah mendarat
            F.notify_melee_impact(u, Unit(u.x + 44, u.y), 52, False)
    u._step = _step


def make_attack_crit(u):
    def _step(i):
        u._gj_attack_active = True
        u._gj_crit_active = True
        u._gj_attack_progress = min(1.0, i / 26.0)
        u.timer = max(0, 45 - i)
        if i == 16:
            F.notify_melee_impact(u, Unit(u.x + 44, u.y), 52, True)
    u._step = _step


def scene_q(u):
    u._blade_fury_timer = 180
    d = F.director_for(u)

    def _step(i):
        u._blade_fury_timer = 180 - i
        if i and (180 - i) % 15 == 0:
            d.on_fury_tick(u.x, u.y)
    u._step = _step


def scene_w(u):
    u._heal_ward_timer = 360
    u._heal_ward_pos = (u.x - 10, u.y + 6)

    def _step(i):
        u._heal_ward_timer = 360 - i
    u._step = _step


def scene_e(u):
    tgt = Unit(u.x + 120, u.y - 4)
    u.target = tgt

    def _step(i):
        u._crit_buff_timer = 300
        if i == 3:
            F.director_for(u).on_cast(u.x, u.y + 16, "e")
    u._step = _step


def scene_r(u):
    tgt = Unit(u.x + 92, u.y - 6)
    u.target = tgt
    u._omnislash_target = tgt
    d = F.director_for(u)

    def _step(i):
        u._omnislash_timer = 90 - i
        if i == 2:
            d.on_cast(u.x, u.y + 16, "r")
        if i and (90 - i) % 8 == 0:
            d.on_omni_strike(tgt.x, tgt.y)
    u._step = _step


# ── susun sheet ────────────────────────────────────────────────────────────
snap(0, 0, lambda u: None, frames=18)                    # idle + napas
snap(1, 0, scene_walk, frames=30)                        # jalan + debu
snap(2, 0, make_attack, frames=26)                       # tebasan + trail
snap(3, 0, make_attack_crit, frames=26)                  # tebasan crit + impact
snap(0, 1, scene_q, frames=48)                           # blade fury
snap(1, 1, scene_w, frames=40)                           # healing ward
snap(2, 1, scene_e, frames=46)                           # crit strike + wave
snap(3, 1, scene_r, frames=52)                           # omnislash

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    ROOT, "docs", "grimjaw_v3_combat_sheet.png")
pygame.image.save(SHEET, out)
print("saved:", out, SHEET.get_size())
