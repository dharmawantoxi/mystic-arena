#!/usr/bin/env python3
"""Filmstrip showcase Vhalzun v2 — rig + seluruh lapisan FX hidup.

Menghasilkan tools/vhalzun_showcase.png: grid 4x4 momen kunci
(idle/walk/swing/pulse/q/w/e/r/hurt/death/mirror) dirender lewat
bosses.level5.draw_vhalzun penuh (canvas + heroes.vhalzun_fx).

Jalankan:  SDL_VIDEODRIVER=dummy python3 tools/vhalzun_showcase.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

from types import SimpleNamespace  # noqa: E402

import bosses.level5 as L          # noqa: E402
import heroes.vhalzun_fx as FX     # noqa: E402

CELL_W, CELL_H = 470, 400
CX, CY = 200, 300                  # titik kaki karakter di dalam sel


def probe(**kw):
    b = SimpleNamespace(
        boss_type="vhalzun", hero_type="vhalzun",
        x=200.0, y=300.0, direction=1, pulse=1.2,
        timer=0, attack_cooldown=44, active_skill=None,
        active_skill_timer=0, target=None, hurt_flash_timer=0,
        alive=True, radius=38, hp=9300, max_hp=9300,
        team="red", speed=0.82, damage=78,
        is_enraged=False, ability_active=False, ability_active_timer=0)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


class Tgt:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.alive = True
        self.radius = 16


def snap(label):
    return (label, pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA))


def run_and_capture(cell, b, frames, capture_at):
    """Jalankan frames langkah; tangkap salinan permukaan pada frame di
    capture_at (list frame index)."""
    out = []
    surface = cell[1]
    label = cell[0]
    d = FX.director_for(b)
    for f in range(max(capture_at) + 1):
        L.draw_vhalzun(surface, b, CX, CY)
        FX.tick(1.0 / 60.0)
        if f in capture_at:
            out.append((f"{label}", surface.copy()))
    return out


def main():
    FX.reset_all()
    cols = []

    # ── baris 1: dasar + swing ─────────────────────────────────────
    b = probe()
    cols += run_and_capture(snap("idle"), b, 0, [90])
    b = probe(_vhz_last_x=190.0, _vhz_last_y=300.0, x=204.0)
    cols += run_and_capture(snap("walk"), b, 0, [60])
    b = probe(target=Tgt(250, 300), timer=43, _vhz_prev_timer=0)
    s = snap("swing")
    d = FX.director_for(b)
    for f in range(52):
        b._vhz_attack_manual = True
        b._vhz_attack_progress = min(1.0, f / 44.0)
        L.draw_vhalzun(s[1], b, CX, CY)
        if f == 18:                    # anticipation
            cols.append(("swing-windup", s[1].copy()))
        if f == 26:                    # impact 0.42*44 ~ frame 18.5; aktif
            FX.notify_melee_impact(b, b.target, 78, True)
        FX.tick(1.0 / 60.0)
        if f == 29:                    # puncak trail + percikan
            cols.append(("swing-hit", s[1].copy()))

    # ── baris 2: pulse + Q + W ─────────────────────────────────────
    b = probe(target=Tgt(420, 300), timer=43, _vhz_prev_timer=0)
    s = snap("pulse")
    for f in range(70):
        if f > 20:
            b._vhz_attack_manual = True
            b._vhz_attack_progress = min(1.0, (f - 20) / 40.0)
        L.draw_vhalzun(s[1], b, CX, CY)
        FX.tick(1.0 / 60.0)
        if f == 34:
            cols.append(("pulse-orb", s[1].copy()))

    for key, name in (("q", "skill-q"), ("w", "skill-w")):
        b = probe(active_skill=key, active_skill_timer=99,
                  _vhz_skill=key, _vhz_skill_total=60 if key == "q" else 80,
                  _vhz_skill_progress=0.0, timer=30)
        s = snap(name)
        total = 60 if key == "q" else 80
        FX.notify_skill_cast(b, key)
        for f in range(total + 6):
            b._vhz_skill_progress = min(1.0, f / total)
            L.draw_vhalzun(s[1], b, CX, CY)
            FX.tick(1.0 / 60.0)
            if f == int(total * 0.55):
                cols.append((name, s[1].copy()))

    # ── baris 3: E + R + hurt ──────────────────────────────────────
    b = probe(active_skill="e", active_skill_timer=99, _vhz_skill="e",
              _vhz_skill_total=60, _vhz_skill_progress=0.0, timer=30,
              target=Tgt(430, 300))
    s = snap("skill-e")
    FX.notify_skill_cast(b, "e")
    for f in range(60):
        b._vhz_skill_progress = min(1.0, f / 60.0)
        L.draw_vhalzun(s[1], b, CX, CY)
        FX.tick(1.0 / 60.0)
        if f == 38:
            cols.append(("skill-e", s[1].copy()))

    b = probe(active_skill="r", active_skill_timer=99, _vhz_skill="r",
              _vhz_skill_total=100, _vhz_skill_progress=0.0, timer=30)
    s = snap("skill-r")
    FX.notify_skill_cast(b, "r")
    for f in range(100):
        b._vhz_skill_progress = min(1.0, f / 100.0)
        L.draw_vhalzun(s[1], b, CX, CY)
        FX.tick(1.0 / 60.0)
        if f == 55:
            cols.append(("skill-r", s[1].copy()))

    b = probe(hurt_flash_timer=9, _vhz_prev_timer=0)
    s = snap("hurt")
    for f in range(12):
        b.hurt_flash_timer = max(0, 9 - f)
        L.draw_vhalzun(s[1], b, CX, CY)
        FX.tick(1.0 / 60.0)
        if f == 2:
            cols.append(("hurt", s[1].copy()))

    # ── baris 4: death + mirror ────────────────────────────────────
    b = probe(alive=False, hp=0, _vhz_death_age=0)
    s = snap("death")
    for f in range(70):
        b._vhz_death_age = f
        L.draw_vhalzun(s[1], b, CX, CY)
        FX.tick(1.0 / 60.0)
        if f == 30:
            cols.append(("death", s[1].copy()))

    b = probe(direction=-1)
    cols += run_and_capture(snap("mirror"), b, 0, [70])

    # ── susun grid 4 kolom ─────────────────────────────────────────
    assert len(cols) == 12, len(cols)
    pad = 6
    rows = 3
    grid = pygame.Surface((4 * (CELL_W + pad) + pad,
                           rows * (CELL_H + 30 + pad) + pad), pygame.SRCALPHA)
    grid.fill((24, 20, 30, 255))
    try:
        from _render import get_font
        font = get_font(15)
    except Exception:
        font = pygame.font.Font(None, 18)
    for i, (label, img) in enumerate(cols):
        r, c = divmod(i, 4)
        x = pad + c * (CELL_W + pad)
        y = pad + r * (CELL_H + 30 + pad)
        grid.blit(img, (x, y))
        t = font.render(label, True, (210, 200, 220))
        grid.blit(t, (x + 4, y + CELL_H + 6))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "vhalzun_showcase.png")
    pygame.image.save(grid, out)

    # ── verifikasi numerik tiap panel ──────────────────────────────
    print(f"[SHOWCASE] {out} ({len(cols)} panel)")
    for i, (label, img) in enumerate(cols):
        m = pygame.mask.from_surface(img, 2)
        r = m.get_bounding_rects()
        if r:
            br = r[0].unionall(r)
            cov = sum(len(pp) for pp in m.outline_masks()) if hasattr(
                m, "outline_masks") else -1
            print(f"  {label:<13} bbox={br}")
        else:
            print(f"  {label:<13} KOSONG (bug!)")
    print("SHOWCASE OK")


if __name__ == "__main__":
    main()
