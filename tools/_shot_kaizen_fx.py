#!/usr/bin/env python3
"""Lembar preview KAIZEN v3 COMBAT FX (lapisan hidup kaizen_fx).

Menghasilkan docs/kaizen_v3_combat_fx.png: grid 3x2 momen tempur —
  1. IDLE + lapisan hidup kosong (baseline bersih)
  2. SWING (trail katana dari histori tip nyata)
  3. IMPACT melee (flash + shockwave + slash fragment + serpihan)
  4. Q Steel Wind (sabit ganda + proyektil sabit angin + streak)
  5. W Wind Wall (tirai mote) + proyektil sedang terbang
  6. R Tornado (badai partikel orbit + silang storm)

100% prosedural; hanya untuk inspeksi visual manusia.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

from heroes import _ProbeEntity, render_hero  # noqa: E402
from heroes import kaizen_fx as F             # noqa: E402

DT = 1.0 / 60.0
CELL_W, CELL_H = 420, 360
COLS, ROWS = 3, 2
BG = (24, 26, 40)
GROUND = (34, 38, 58)


def fresh(x, y):
    h = _ProbeEntity("kaizen", x, y)
    h.facing = h.direction = 1
    h.attack_timer = 0
    h.attack_cooldown = 40
    h.range = 60
    h.hp = h.max_hp = 700
    h._q_stack = 0
    h._is_dashing = False
    h._dash_timer = 0
    h._wind_wall_timer = 0
    h._ulti_active = False
    h._ulti_timer = 0
    return h


def cell(title, setup, frames):
    surf = pygame.Surface((CELL_W, CELL_H))
    surf.fill(BG)
    pygame.draw.rect(surf, GROUND, (0, 250, CELL_W, CELL_H - 250))
    F.reset_all()
    h = fresh(CELL_W // 2, 210)
    d = F.director_for(h)
    setup(h, d)
    for i in range(frames):
        step(h, d, i)
        d.update(DT)
    d.draw_ground(surf)
    render_hero("kaizen", surf, h, int(h.x), int(h.y))
    d.draw_front(surf)
    font = pygame.font.Font(None, 22)
    surf.blit(font.render(title, True, (215, 240, 255)), (10, 8))
    F.reset_all()
    return surf


def step(h, d, i):
    if h.attack_timer > 0:
        h.attack_timer -= 1
        h.timer = h.attack_timer
    h.pulse += 0.1


def s_idle(h, d):
    pass


def s_swing(h, d):
    h.attack_timer = h.timer = 40


def s_impact(h, d):
    class T:
        x, y = h.x + 64.0, h.y - 4.0
    F.notify_melee_impact(h, T(), damage=48, crit=True)


def s_q(h, d):
    class T:
        x, y, radius, alive = h.x + 150.0, h.y, 12, True
    h.target = T()
    h.active_skill = "q"
    h.active_skill_timer = 60
    d.update(DT)


def s_w(h, d):
    h.active_skill = "w"
    h.active_skill_timer = 90
    h._wind_wall_timer = 180


def s_r(h, d):
    h.active_skill = "r"
    h.active_skill_timer = 100
    h._ulti_timer = 90
    h._ulti_active = True


def main():
    sheet = pygame.Surface((CELL_W * COLS, CELL_H * ROWS))
    cells = [
        ("1. IDLE (baseline)", s_idle, 30),
        ("2. SWING trail (progress ~0.55)", s_swing, 23),
        ("3. IMPACT melee crit", s_impact, 5),
        ("4. Q Steel Wind + sabit", s_q, 10),
        ("5. W Wind Wall (tirai mote)", s_w, 40),
        ("6. R Tornado (badai orbit)", s_r, 35),
    ]
    for idx, (title, setup, frames) in enumerate(cells):
        c = cell(title, setup, frames)
        sheet.blit(c, ((idx % COLS) * CELL_W, (idx // COLS) * CELL_H))
    out = os.path.join(ROOT, "docs", "kaizen_v3_combat_fx.png")
    pygame.image.save(sheet, out)
    print(out)


if __name__ == "__main__":
    main()
