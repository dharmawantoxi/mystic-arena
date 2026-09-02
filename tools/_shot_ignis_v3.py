#!/usr/bin/env python3
"""Render review sheet untuk Ignis Drachorn V3 (combat FX + anim rewrite).

Menghasilkan:
  - docs/ignis_v3_preview.png       (idle / walk / filmstrip ayunan / pose skill)
  - docs/ignis_v3_fx_sheet.png      (lapisan hidup: melee, ranged, skill q/w/e/r)
  - docs/ignis_v3_elder_form.png    (Elder Dragon Form skill R, dua arah hadap)

Jalankan:  python3 tools/_shot_ignis_v3.py
"""
import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from types import SimpleNamespace  # noqa: E402

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import bosses.level4 as L  # noqa: E402
from heroes import ignis_drachorn_fx as fx  # noqa: E402

DOCS = os.path.join(ROOT, "docs")


# ── helper unit dummy ────────────────────────────────────────────────
def make_unit(skill=None, skill_t=0, timer=0, rng=55, direction=1,
              x=300.0, y=300.0, tx=470.0):
    return SimpleNamespace(
        boss_type="ignis_drachorn", boss_class="true",
        x=x, y=y, direction=direction, facing=direction, pulse=1.3,
        timer=timer, attack_cooldown=42,
        active_skill=skill, active_skill_timer=skill_t,
        target=SimpleNamespace(x=tx, y=y, alive=True, radius=14),
        hurt_flash_timer=0, alive=True, radius=45,
        hp=25000, max_hp=25000, range=rng, attack_range=rng)


# ── 1. preview renderer (tanpa lapisan hidup) ────────────────────────
def sheet_preview(path):
    CW, CH = 200, 220

    def cell(fn):
        s = pygame.Surface((CW, CH), pygame.SRCALPHA)
        s.fill((26, 22, 30, 255))
        fn(s, CW // 2, CH // 2 + 20)
        return s

    cells = []
    b = make_unit(x=0.0, y=0.0, tx=170.0)
    for i in range(3):
        b.pulse = 1.0 + i * 0.7
        cells.append(("idle%d" % i,
                      cell(lambda s, x, y, u=b: L.draw_ignis_drachorn(s, u, x, y))))

    bw = make_unit(x=1.0, y=0.0, tx=170.0)
    for i in range(3):
        bw.pulse = 1.0 + i * 0.6
        bw.x += 3
        cells.append(("walk%d" % i,
                      cell(lambda s, x, y, u=bw: L.draw_ignis_drachorn(s, u, x, y))))

    ba = make_unit(timer=42, x=0.0, y=0.0, tx=170.0)
    for i in range(36):
        surf = pygame.Surface((CW, CH), pygame.SRCALPHA)
        surf.fill((26, 22, 30, 255))
        L.draw_ignis_drachorn(surf, ba, CW // 2, CH // 2 + 20)
        if i in (1, 5, 10, 15, 18, 24):
            cells.append(("atk%.2f" % getattr(ba, "_ign_attack_progress", 0.0), surf))
        ba.timer = max(0, ba.timer - 1)
        ba.pulse += 0.05

    for sk, dur in (("q", 45), ("w", 40), ("e", 60), ("r", 90)):
        bs = make_unit(sk, dur, x=0.0, y=0.0, tx=170.0)
        surf = None
        for _ in range(int(dur * 0.5)):
            surf = pygame.Surface((CW, CH), pygame.SRCALPHA)
            surf.fill((26, 22, 30, 255))
            L.draw_ignis_drachorn(surf, bs, CW // 2, CH // 2 + 20)
            bs.active_skill_timer -= 1
            bs.pulse += 0.05
        cells.append((sk.upper(), surf))

    cols = 6
    rows = (len(cells) + cols - 1) // cols
    sheet = pygame.Surface((cols * CW, rows * CH))
    sheet.fill((16, 14, 18))
    font = pygame.font.Font(None, 18)
    for i, (name, c) in enumerate(cells):
        x, y = (i % cols) * CW, (i // cols) * CH
        sheet.blit(c, (x, y))
        sheet.blit(font.render(name, True, (255, 220, 160)), (x + 4, y + 4))
    pygame.image.save(sheet, path)
    print("saved", path, sheet.get_size())


# ── 2. lapisan FX hidup ──────────────────────────────────────────────
def sheet_fx(path):
    CW, CH, AX, AY = 300, 260, 110, 170

    def cell(label, setup, frames):
        fx.reset_all()
        random.seed(7)
        b = make_unit(timer=40)
        b.pulse = 0.0
        surf = pygame.Surface((CW, CH), pygame.SRCALPHA)
        for i in range(frames):
            b.pulse += 0.12
            setup(b, i)
            surf.fill((24, 20, 28, 255))
            L.draw_ignis_drachorn(surf, b, AX, AY)
            fx.tick(1 / 60.0)
        surf.blit(pygame.font.Font(None, 16).render(label, True, (230, 210, 190)), (6, 4))
        return surf

    cells = []

    def melee(b, i):
        b.timer = 40 - (i % 40)

    for n in (13, 18, 21, 24):
        cells.append(cell("melee f%d" % n, melee, n))

    def ranged(b, i):
        b.attack_range = 180
        b.timer = 40 - (i % 40)

    for n in (16, 26, 34, 44):
        cells.append(cell("ranged f%d" % n, ranged, n))

    for key, dur in (("q", 45), ("w", 40), ("e", 60), ("r", 90)):
        def skill(b, i, k=key, d=dur):
            b.active_skill = k
            b.active_skill_timer = max(0, d - i)
            if b.active_skill_timer == 0:
                b.active_skill = None
        for frac in (0.25, 0.5, 0.75, 1.15):
            n = max(3, int(dur * frac))
            cells.append(cell("%s f%d" % (key.upper(), n), skill, n))

    cols = 4
    rows = (len(cells) + cols - 1) // cols
    sheet = pygame.Surface((cols * CW, rows * CH))
    sheet.fill((18, 15, 22))
    for i, c in enumerate(cells):
        sheet.blit(c, ((i % cols) * CW, (i // cols) * CH))
    pygame.image.save(sheet, path)
    print("saved", path, sheet.get_size(), "cells", len(cells))


# ── 3. Elder Dragon Form ─────────────────────────────────────────────
def sheet_elder(path):
    CW, CH = 300, 280
    cells = []
    for tm, d in ((80, 1), (60, 1), (40, 1), (40, -1)):
        fx.reset_all()
        b = make_unit("r", tm, timer=40, direction=d)
        b.pulse = 0.0
        s = pygame.Surface((CW, CH), pygame.SRCALPHA)
        for _ in range(30):
            b.pulse += 0.12
            b.active_skill_timer = tm
            s.fill((24, 20, 28, 255))
            L.draw_ignis_drachorn(s, b, 150, 180)
            fx.tick(1 / 60.0)
        s.blit(pygame.font.Font(None, 16).render(
            "R t=%d dir=%d" % (tm, d), True, (230, 210, 190)), (6, 4))
        cells.append(s)
    sheet = pygame.Surface((CW * 4, CH))
    sheet.fill((18, 15, 22))
    for i, c in enumerate(cells):
        sheet.blit(c, (i * CW, 0))
    sheet = pygame.transform.scale(sheet, (CW * 8, CH * 2))
    pygame.image.save(sheet, path)
    print("saved", path, sheet.get_size())


if __name__ == "__main__":
    sheet_preview(os.path.join(DOCS, "ignis_v3_preview.png"))
    sheet_fx(os.path.join(DOCS, "ignis_v3_fx_sheet.png"))
    sheet_elder(os.path.join(DOCS, "ignis_v3_elder_form.png"))
