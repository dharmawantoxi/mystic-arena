#!/usr/bin/env python3
"""Lembar bukti: FX boss vs keterbacaan karakter (momen terburuk).

Menggambar momen paling parah dari tiap boss yang pernah tertutup cahaya
(gorath / nyzrak / alchemist / ancient_apparition / razak) plus beberapa
pembanding yang sudah sehat.

Jalankan: python3 tools/_shot_boss_white_cover.py
Hasil   : docs/boss_white_cover.png
"""
import importlib
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes  # noqa: E402
from heroes import _ProbeEntity  # noqa: E402
from bosses._boss_index import BOSS_INDEX  # noqa: E402

DT = 1.0 / 60.0
SIZE = 340
CX, CY = 170, 200


def _draw_fn(name):
    mod, fn = BOSS_INDEX[name]
    return getattr(importlib.import_module("bosses." + mod), fn)


def render(name, skill=None, frac=0.0, hurt=0.0):
    fx = heroes._live_fx_module(name)
    if fx is not None:
        try:
            fx.reset_all()
        except Exception:
            pass
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    dur = getattr(fx, "SKILL_DUR", {}).get(skill, 60) if fx else 60
    h = _ProbeEntity(name, float(CX), float(CY))
    h.boss_type = h.hero_type = name
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = 45
    h.timer = 0
    h.hp = h.max_hp = 1200
    h.radius = 16
    h.hurt_flash_timer = 0
    h.skill_damage = 180
    h.skill_range = 180
    for a in ("blink_from_x", "blink_from_y", "mana_void_x", "mana_void_y"):
        setattr(h, a, 0)
    h.active_skill = skill
    h.active_skill_timer = int(dur * (1.0 - frac)) if skill else 0
    h.target = _ProbeEntity("dummy", float(CX + 90), float(CY - 10))
    h.target.alive = True
    if fx is not None:
        try:
            fx.attach(h)
            for _ in range(max(0, dur - h.active_skill_timer)):
                fx.tick(DT)
            if hurt > 0.0:
                d = fx.director_for(h)
                d.on_hurt(0.2)
                fx.tick(0.0001)
                for at in ("hit_flash", "_hit_flash", "flash"):
                    if hasattr(d, at):
                        setattr(d, at, 0.16 * hurt)
        except Exception:
            pass
    _draw_fn(name)(surf, h, CX, CY)
    if fx is not None:
        try:
            fx.reset_all()
        except Exception:
            pass
    return surf


CASES = [
    ("gorath", None, 0.0, 1.0),
    ("gorath", "r", 0.7, 0.0),
    ("nyzrak", None, 0.0, 1.0),
    ("nyzrak", "r", 0.05, 0.0),
    ("alchemist", None, 0.0, 1.0),
    ("alchemist", "r", 0.7, 0.0),
    ("ancient_apparition", "e", 0.3, 0.0),
    ("razak", "r", 0.5, 0.0),
    ("razak", None, 0.0, 1.0),
    ("gornak", "r", 0.3, 0.0),
    ("kunkka", "r", 0.5, 0.0),
    ("zharok", "e", 0.7, 0.0),
]

CW, CH = 300, 330
cols = 4
rows_n = (len(CASES) + cols - 1) // cols
sheet = pygame.Surface((cols * CW + 20, rows_n * CH + 50))
sheet.fill((14, 10, 16))
font = pygame.font.Font(None, 20)
sheet.blit(font.render("BOSS - FX skill & hit flash vs keterbacaan "
                       "karakter (sesudah perbaikan)", True,
                       (240, 220, 255)), (12, 12))
for i, (n, sk, fr, hu) in enumerate(CASES):
    s = render(n, sk, fr, hu)
    x = 10 + (i % cols) * CW
    y = 44 + (i // cols) * CH
    big = pygame.transform.scale(s, (int(SIZE * 2.4), int(SIZE * 2.4)))
    cw, ch = CW - 16, CH - 50
    crop = pygame.Surface((cw, ch))
    crop.fill((0, 0, 0))
    crop.blit(big, (0, 0), ((big.get_width() - cw) // 2,
                            (big.get_height() - ch) // 2 + 30, cw, ch))
    sheet.blit(crop, (x + 8, y + 6))
    lbl = "%s %s" % (n, ("HURT" if hu else "%s %.2f" % (sk.upper(), fr)))
    sheet.blit(font.render(lbl, True, (250, 230, 255)), (x + 8, y + CH - 36))

out = os.path.join(ROOT, "docs", "boss_white_cover.png")
pygame.image.save(sheet, out)
print(out)
