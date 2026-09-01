#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lembar preview VEX v3 COMBAT FX (lapisan hidup heroes/vex_fx.py).

Merender Vex persis seperti jalur HERO lane (canvas ter-cache -> di-scale
-> lapisan hidup 1:1 di atasnya), lalu menyusun banyak pose/keadaan
menjadi satu lembar PNG supaya bisa direview tanpa menjalankan game.

Dipakai untuk:

  * melihat kualitas arc ayunan staff (trail dari histori posisi nyata),
  * memeriksa lifecycle skill Q / W / E / R,
  * memastikan proyektil, impact, partikel, dan warna palette konsisten,
  * memverifikasi tidak ada efek yang menutupi karakter.

Jalankan:
    SDL_VIDEODRIVER=dummy python3 tools/_shot_vex_fx.py
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
from heroes import vex_fx as F                           # noqa: E402
from heroes._bundle import _NS_vex as V                  # noqa: E402

DT = 1.0 / 60.0
CELL_W, CELL_H = 300, 300
CANVAS = 360


def fresh_hero(x=CELL_W // 2, y=CELL_H // 2 + 40, cd=46):
    """Unit Vex minim dengan seluruh atribut yang dibaca renderer + FX."""
    h = _ProbeEntity("vex", x, y)
    h.direction = h.facing = 1
    h.alive = True
    h.pulse = 1.15
    h.timer = 0
    h.attack_timer = 0
    h.attack_cooldown = cd
    h.range = 130
    h.speed = 1.3
    h.hp = h.max_hp = 520
    h.radius = 16
    h.skill_damage = 95
    h.skill_range = 250
    h.target = None
    h._sanity_eclipse_active = False
    h._sanity_eclipse_timer = 0
    h._astral_prison_active = False
    h._astral_prison_timer = 0
    h._astral_prison_target = None
    h._essence_flux_active = False
    h._essence_flux_timer = 0
    h._vx_attack_active = False
    h._vx_attack_progress = 0.0
    h._render_scale = heroes._get_hero_scale("vex")
    return h


def _render_lane(surface, hero, x, y):
    """Salin jalur HERO lane: canvas ter-cache -> scale -> lapisan hidup."""
    canvas = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)
    c = CANVAS // 2
    V.draw_vex(canvas, hero, c, c)
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
    s.fill((26, 30, 44, 255))
    # latar arena sederhana supaya warna efek terbaca
    pygame.draw.ellipse(s, (38, 44, 62), (10, CELL_H - 70, CELL_W - 20, 60))
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
    img = font.render(title, True, (235, 245, 255))
    s.blit(img, (8, 6))
    if label:
        img2 = font.render(label, True, (150, 235, 230))
        s.blit(img2, (8, 26))
    return s


def attack_setup(ap):
    cd = 46

    def _s(h):
        h.attack_timer = max(0, int(round(cd - ap * (cd - 1))))
        h.timer = h.attack_timer
        h._vx_attack_active = True
        h._vx_attack_progress = ap
    return _s


def run():
    cells = []

    # ── BARIS 1: timeline ayunan (ANTICIPATION -> RECOVERY) ──────────
    for ap, name in ((0.12, "ANTICIPATION"), (0.30, "WINDUP"),
                     (0.45, "SWING"), (0.58, "IMPACT"),
                     (0.74, "FOLLOW")):
        cells.append(cell("SWING %s" % name, steps=1,
                          setup=attack_setup(ap),
                          label="ap=%.2f" % ap))

    # ── BARIS 2: idle / walk / skill Q ───────────────────────────────
    cells.append(cell("IDLE", steps=20))
    cells.append(cell("WALK", steps=24,
                      drive=lambda h, i: setattr(h, "x", h.x + 1.4)))
    cells.append(cell("Q ARCANE ORB (cast)", steps=8,
                      setup=lambda h: setattr(h, "active_skill", "q")))
    cells.append(cell("Q ARCANE ORB (release)", steps=26,
                      setup=lambda h: setattr(h, "active_skill", "q")))
    cells.append(cell("Q CONDUIT + ORB", steps=34,
                      setup=lambda h: (
                          setattr(h, "active_skill", "q"),
                          setattr(h, "target", _ProbeEntity(
                              "vex", h.x + 190, h.y - 10)))))

    # ── BARIS 3: W / E / R ───────────────────────────────────────────
    def _w(h, t=180):
        h._sanity_eclipse_timer = t
    cells.append(cell("W SANITY ECLIPSE (rise)", steps=10, setup=_w))
    cells.append(cell("W SANITY ECLIPSE (hold)", steps=70,
                      setup=_w,
                      drive=lambda h, i: setattr(
                          h, "_sanity_eclipse_timer",
                          max(0, h._sanity_eclipse_timer - 1))))

    def _e(h):
        h._astral_prison_timer = 150
        h._astral_prison_target = _ProbeEntity("vex", h.x + 92, h.y - 8)
    cells.append(cell("E ASTRAL PRISON", steps=40, setup=_e,
                      drive=lambda h, i: setattr(
                          h, "_astral_prison_timer",
                          max(0, h._astral_prison_timer - 1))))
    cells.append(cell("E ASTRAL SHATTER", steps=150, setup=_e,
                      drive=lambda h, i: setattr(
                          h, "_astral_prison_timer",
                          max(0, h._astral_prison_timer - 1))))
    cells.append(cell("R ESSENCE FLUX (burst)", steps=30,
                      setup=lambda h: setattr(h, "_essence_flux_timer", 60),
                      drive=lambda h, i: setattr(
                          h, "_essence_flux_timer",
                          max(0, h._essence_flux_timer - 1))))

    # ── BARIS 4: impact / proyektil / hurt / debug ───────────────────
    def _impact(h):
        F.notify_projectile_impact(h, h.x + 96, h.y - 10, 0.0, 60, False)
    cells.append(cell("IMPACT FX (orb hit)", steps=6, setup=_impact))
    cells.append(cell("IMPACT FX (crit)", steps=9,
                      setup=lambda h: F.notify_projectile_impact(
                          h, h.x + 96, h.y - 10, 0.0, 90, True)))

    def _shards(h):
        for i in range(8):
            a = i / 8.0 * math.tau
            F.director_for(h).projectiles.spawn(
                h.x, h.y + 12,
                h.x + math.cos(a) * 140, h.y + 12 + math.sin(a) * 90,
                speed=300.0, radius=5.0, kind="shard")
    cells.append(cell("PROJECTILE SYSTEM", steps=10, setup=_shards))
    cells.append(cell("HURT FLASH", steps=4,
                      setup=lambda h: F.notify_hurt(h, 0.4)))
    F.DEBUG_CHARACTER = True
    cells.append(cell("DEBUG OVERLAY", steps=14, setup=attack_setup(0.50)))
    F.DEBUG_CHARACTER = False

    cols = 5
    rows = int(math.ceil(len(cells) / float(cols)))
    sheet = pygame.Surface((CELL_W * cols, CELL_H * rows), pygame.SRCALPHA)
    sheet.fill((12, 14, 22, 255))
    for i, c in enumerate(cells):
        sheet.blit(c, ((i % cols) * CELL_W, (i // cols) * CELL_H))

    out = os.path.join(ROOT, "docs", "vex_v3_combat_fx.png")
    pygame.image.save(sheet, out)
    print("tersimpan:", out, sheet.get_size())

    # ── ringkasan lifecycle (tanpa efek abadi) ───────────────────────
    h = fresh_hero()
    d = F.director_for(h)
    F.attach(h)
    for i in range(200):
        d.update(DT)
    print("partikel setelah 200 frame idle:", d.particles.count())
    F.reset_all()
    print("total partikel setelah reset_all:", F.total_particles())


if __name__ == "__main__":
    FEEL.reset()
    run()
