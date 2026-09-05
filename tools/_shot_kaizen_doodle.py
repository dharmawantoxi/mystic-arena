#!/usr/bin/env python3
"""Render review sheet untuk KAIZEN DOODLE MASTERWORK (native scale).

Rewrite renderer dari pixel-art ke bahasa "buku sketsa" (tinta bergoyang,
isi spidol bercelah kertas, arsiran pensil + skribel, highlight gel-pen,
angin lidah teardrop). Sheet ini digambar pada skala natural penuh supaya
goresan tangan terlihat jelas, bukan menyusut lewat pipeline sprite-cache.
"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame
from types import SimpleNamespace

pygame.init()
pygame.display.set_mode((1, 1))
from heroes import _ProbeEntity
from heroes._bundle import _NS_kaizen as K

# Matikan lapisan hidup supaya hanya rig doodle yang dipotret.
try:
    from heroes import kaizen_fx as _kzfx
    _kzfx.KAIZEN_FX_ENABLED = False
    K._LIVE_MOD = False
except Exception:
    pass

W, H = 1280, 800
screen = pygame.Surface((W, H))
screen.fill((250, 246, 236))          # kertas
title_f = pygame.font.Font(None, 52)
label_f = pygame.font.Font(None, 30)
small_f = pygame.font.Font(None, 20)

screen.blit(title_f.render("KAIZEN — DOODLE MASTERWORK", True,
                           (20, 17, 22)), (40, 26))
screen.blit(small_f.render(
    "sketchbook rewrite • tinta bergoyang + spidol bercelah kertas + "
    "arsiran pensil + highlight gel-pen • 100% code-drawn", True,
    (80, 74, 90)), (42, 84))

panels = (
    ("IDLE", "breath • rim gel-pen"),
    ("WALK", "foot solver • hakama bergerigi"),
    ("ATTACK", "hamon • smear sabit • bintang"),
    ("TORNADO", "funnel doodle • lidah angin"),
)
for i, (label, note) in enumerate(panels):
    x = 28 + i * 312
    panel = pygame.Rect(x, 118, 288, 590)
    pygame.draw.rect(screen, (255, 255, 252), panel, border_radius=12)
    pygame.draw.rect(screen, (20, 17, 22), panel, 2, border_radius=12)
    screen.blit(label_f.render(label, True, (20, 17, 22)), (x + 16, 138))

    native = pygame.Surface((270, 460), pygame.SRCALPHA)
    h = _ProbeEntity("kaizen", 135, 200)
    h.pulse = 1.25
    h.direction = 1
    h.facing = 1
    if i == 0:
        K._draw_swordsman_rim_light(native, 135, 188, h.pulse)
        K._draw_wind_platform(native, 135, 258, h.pulse, None)
        K._draw_kaizen_idle(native, h, 135, 210)
    elif i == 1:
        h.pulse = 2.15
        K._draw_wind_platform(native, 135, 258, h.pulse, None)
        K._draw_kaizen_walk(native, h, 135, 210)
    elif i == 2:
        h._kz_attack_progress = .52
        h._kz_attack_active = True
        h.range = 40
        K._draw_wind_platform(native, 135, 258, h.pulse, None)
        K._draw_kaizen_attack(native, h, 135, 210)
    else:
        h.active_skill = "r"
        h.active_skill_timer = 58
        h.target = SimpleNamespace(x=135, y=200, alive=True)
        K._draw_wind_platform(native, 135, 258, h.pulse, "r")
        K._draw_kaizen_idle(native, h, 135, 210)
        K._draw_tornado(native, h, 135, 210, 58, h.pulse)

    old = screen.get_clip()
    screen.set_clip(panel.inflate(-8, -78))
    screen.blit(native, (x + 152 - 135, 168))
    screen.set_clip(old)
    screen.blit(small_f.render(note, True, (80, 74, 90)),
                (x + 16, panel.bottom - 34))

out = os.path.join(ROOT, "docs", "kaizen_doodle_preview.png")
pygame.image.save(screen, out)
print(out)
