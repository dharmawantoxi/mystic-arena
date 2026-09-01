#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lembar preview SYLARA v3 COMBAT FX (lapisan hidup heroes/sylara_fx.py).

Merender Sylara persis seperti jalur HERO lane (canvas ter-cache ->
di-scale -> lapisan hidup 1:1 di atasnya), lalu menyusun banyak
pose/keadaan menjadi satu lembar PNG supaya bisa direview tanpa
menjalankan game.

Dipakai untuk:

  * melihat kualitas busur ayunan limb (trail dari histori posisi nyata),
  * memeriksa timeline tembakan 6 fase + frame IMPACT (lepas tali),
  * memeriksa lifecycle skill Q / W / E / R,
  * memastikan proyektil panah, impact, partikel daun, dan palette
    konsisten,
  * memverifikasi tidak ada efek yang menutupi karakter.

Jalankan:
    SDL_VIDEODRIVER=dummy python3 tools/_shot_sylara_v3_fx.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import math                                              # noqa: E402

import pygame                                            # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes                                            # noqa: E402
from heroes import _ProbeEntity                          # noqa: E402
from heroes import combat_feel as FEEL                   # noqa: E402
from heroes import sylara_fx as F                        # noqa: E402
from heroes._bundle import _NS_sylara as S               # noqa: E402

DT = 1.0 / 60.0
CELL_W, CELL_H = 300, 300
CANVAS = 360
CD = 52


def fresh_hero(x=CELL_W // 2, y=CELL_H // 2 + 40, cd=CD):
    """Unit Sylara minim dengan seluruh atribut yang dibaca renderer + FX."""
    h = _ProbeEntity("sylara", x, y)
    h.direction = h.facing = 1
    h.alive = True
    h.pulse = 1.15
    h.timer = 0
    h.attack_timer = 0
    h.attack_cooldown = cd
    h.range = 130
    h.speed = 1.5
    h.hp = h.max_hp = 470
    h.radius = 16
    h.skill_damage = 95
    h.skill_range = 180
    h.active_skill = None
    h.active_skill_timer = 0
    h._focus_fire_active = False
    h._focus_fire_timer = 0
    h._windrun_active = False
    h._windrun_timer = 0
    h._shackle_active = False
    h._shackle_timer = 0
    h._shackle_target = None
    h._powershot_charging = False
    h._powershot_timer = 0
    h._sy_attack_active = False
    h._sy_attack_progress = 0.0
    h._sy_swing_mode = False
    h.target = None
    h._render_scale = heroes._get_hero_scale("sylara")
    return h


def _render_lane(surface, hero, x, y):
    """Salin jalur HERO lane: canvas ter-cache -> scale -> lapisan hidup."""
    canvas = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)
    c = CANVAS // 2
    S.draw_sylara(canvas, hero, c, c)
    rect = canvas.get_bounding_rect(min_alpha=8)
    if rect.width <= 0 or rect.height <= 0:
        return
    scale = float(getattr(hero, "_render_scale", 1.0) or 1.0)
    sub = canvas.subsurface(rect).copy()
    if abs(scale - 1.0) >= 0.02:
        sub = pygame.transform.smoothscale(
            sub, (max(1, int(rect.width * scale)),
                  max(1, int(rect.height * scale))))
    ax = (c - rect.x) * scale
    ay = (c - rect.y) * scale
    surface.blit(sub, (int(x - ax), int(y - ay)))


def cell(title, steps=0, setup=None, drive=None, label=""):
    """Render satu sel: (surface, hero) setelah ``steps`` langkah FX."""
    s = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA)
    s.fill((22, 30, 26, 255))
    pygame.draw.ellipse(s, (32, 44, 34), (10, CELL_H - 70, CELL_W - 20, 60))
    hero = fresh_hero()
    if setup:
        setup(hero)
    d = F.director_for(hero)
    F.attach(hero)
    for i in range(steps):
        if drive:
            drive(hero, i)
        d.update(DT)
    d.draw_ground(s)
    _render_lane(s, hero, hero.x, hero.y)
    d.draw_front(s)

    font = pygame.font.Font(None, 20)
    s.blit(font.render(title, True, (232, 255, 214)), (8, 6))
    if label:
        s.blit(font.render(label, True, (170, 235, 135)), (8, 26))
    return s


def attack_setup(ap, swing=False, target=True):
    """Pasang hero tepat di progress serangan ``ap``."""
    def _s(h):
        h.attack_timer = max(0, int(round(CD - ap * (CD - 1))))
        h.timer = h.attack_timer
        h._sy_attack_active = True
        h._sy_attack_progress = ap
        h._sy_swing_mode = swing
        h._pose_variant = 1 if swing else 0
        if target:
            dist = 40 if swing else 170
            h.target = _ProbeEntity("sylara", h.x + dist, h.y - 6)
            h.target.alive = True
            h.target.radius = 14
    return _s


def run():
    cells = []

    # ── BARIS 1: timeline tembakan (ANTICIPATION -> RECOVERY) ────────
    for ap, name in ((0.10, "ANTICIPATION"), (0.22, "WINDUP"),
                     (0.45, "DRAW"), (0.56, "RELEASE"),
                     (0.74, "FOLLOW")):
        cells.append(cell("SHOT %s" % name, steps=1,
                          setup=attack_setup(ap),
                          label="ap=%.2f" % ap))

    # ── BARIS 2: sapuan melee berbasis busur ─────────────────────────
    for ap, name in ((0.16, "WIND-UP"), (0.40, "SWING"),
                     (0.55, "IMPACT"), (0.78, "FOLLOW")):
        cells.append(cell("MELEE %s" % name, steps=1,
                          setup=attack_setup(ap, swing=True),
                          label="ap=%.2f  arc" % ap))
    cells.append(cell("MELEE TRAIL (live)", steps=30,
                      setup=attack_setup(0.02, swing=True),
                      drive=lambda h, i: (
                          setattr(h, "attack_timer", max(0, CD - i)),
                          setattr(h, "timer", max(0, CD - i))),
                      label="histori posisi busur"))

    # ── BARIS 3: idle / walk / Q / W ─────────────────────────────────
    cells.append(cell("IDLE", steps=22))
    cells.append(cell("WALK", steps=26,
                      drive=lambda h, i: setattr(h, "x", h.x + 1.4)))
    cells.append(cell("Q FOCUS FIRE (cast)", steps=8,
                      setup=lambda h: setattr(h, "active_skill", "q")))
    cells.append(cell("Q FOCUS FIRE (volley)", steps=40,
                      setup=lambda h: setattr(h, "active_skill", "q")))

    def _w(h):
        h._windrun_active = True
        h._windrun_timer = 180
    cells.append(cell("W WINDRUN (burst)", steps=10, setup=_w))

    # ── BARIS 4: W hold / E / R ──────────────────────────────────────
    cells.append(cell("W WINDRUN (cyclone)", steps=70, setup=_w,
                      drive=lambda h, i: setattr(
                          h, "_windrun_timer",
                          max(0, h._windrun_timer - 1))))

    def _e(h):
        h._shackle_timer = 150
        h._shackle_target = _ProbeEntity("sylara", h.x + 96, h.y - 8)
        h._shackle_target.alive = True
    cells.append(cell("E SHACKLE SHOT", steps=26, setup=_e,
                      drive=lambda h, i: setattr(
                          h, "_shackle_timer",
                          max(0, h._shackle_timer - 1))))
    cells.append(cell("E SHACKLE (vine hold)", steps=70, setup=_e,
                      drive=lambda h, i: setattr(
                          h, "_shackle_timer",
                          max(0, h._shackle_timer - 1))))
    cells.append(cell("R POWERSHOT (charge)", steps=24,
                      setup=lambda h: setattr(h, "_powershot_timer", 60),
                      drive=lambda h, i: setattr(
                          h, "_powershot_timer",
                          max(0, h._powershot_timer - 1))))
    cells.append(cell("R POWERSHOT (gale)", steps=54,
                      setup=lambda h: setattr(h, "_powershot_timer", 60),
                      drive=lambda h, i: setattr(
                          h, "_powershot_timer",
                          max(0, h._powershot_timer - 1))))

    # ── BARIS 5: impact / proyektil / hurt / debug ───────────────────
    cells.append(cell("IMPACT FX (arrow)", steps=6,
                      setup=lambda h: F.notify_projectile_impact(
                          h, h.x + 96, h.y - 10, 0.0, 45, False)))
    cells.append(cell("IMPACT FX (crit)", steps=9,
                      setup=lambda h: F.notify_projectile_impact(
                          h, h.x + 96, h.y - 10, 0.0, 90, True)))

    def _volley(h):
        d = F.director_for(h)
        for i in range(6):
            a = (i - 2.5) * 0.18
            d.projectiles.spawn(
                h.x + 16, h.y - 16,
                h.x + 16 + math.cos(a) * 200,
                h.y - 16 + math.sin(a) * 200,
                speed=520.0, radius=6.0,
                kind="gale" if i % 2 else "arrow")
    cells.append(cell("PROJECTILE SYSTEM", steps=12, setup=_volley))
    cells.append(cell("HURT FLASH", steps=4,
                      setup=lambda h: F.notify_hurt(h, 0.4)))
    F.DEBUG_CHARACTER = True
    cells.append(cell("DEBUG OVERLAY", steps=14,
                      setup=attack_setup(0.50)))
    F.DEBUG_CHARACTER = False

    cols = 5
    rows = int(math.ceil(len(cells) / float(cols)))
    sheet = pygame.Surface((CELL_W * cols, CELL_H * rows), pygame.SRCALPHA)
    sheet.fill((10, 16, 12, 255))
    for i, c in enumerate(cells):
        sheet.blit(c, ((i % cols) * CELL_W, (i // cols) * CELL_H))

    out = os.path.join(ROOT, "docs", "sylara_v3_combat_fx.png")
    pygame.image.save(sheet, out)
    print("tersimpan:", out, sheet.get_size())

    # ── ringkasan lifecycle (tanpa efek abadi) ───────────────────────
    h = fresh_hero()
    d = F.director_for(h)
    F.attach(h)
    for _i in range(200):
        d.update(DT)
    print("partikel setelah 200 frame idle:", d.particles.count())
    F.reset_all()
    print("total partikel setelah reset_all:", F.total_particles())


if __name__ == "__main__":
    FEEL.reset()
    run()
