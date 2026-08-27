#!/usr/bin/env python3
"""Render review sheet untuk contoh upgrade procedural Kaizen."""
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

W, H = 1280, 720
screen = pygame.Surface((W, H))
screen.fill((5, 9, 18))
font_title = pygame.font.Font(None, 46)
font_label = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 20)

screen.blit(font_title.render("KAIZEN — PROCEDURAL MASTERWORK", True, (166, 218, 255)), (38, 24))
screen.blit(font_small.render("100% code-drawn • no external hero sprite • idle / walk / attack / ultimate", True, (132, 151, 181)), (40, 72))

labels = ("IDLE DETAIL", "GROUNDED WALK", "KATANA ATTACK", "TORNADO ULTIMATE")
for i, label in enumerate(labels):
    x = 30 + i * 310
    panel = pygame.Rect(x, 110, 286, 560)
    pygame.draw.rect(screen, (10, 17, 32), panel, border_radius=12)
    pygame.draw.rect(screen, (55, 112, 172), panel, 2, border_radius=12)
    screen.blit(font_label.render(label, True, (218, 236, 255)), (x + 16, 130))

    native = pygame.Surface((240, 260), pygame.SRCALPHA)
    h = _ProbeEntity("kaizen", 120, 135)
    h.pulse = 1.25
    h.direction = 1
    h.facing = 1
    if i == 0:
        K._draw_swordsman_rim_light(native, 120, 125, h.pulse)
        K._draw_wind_platform(native, 120, 175, h.pulse, None)
        K._draw_kaizen_idle(native, h, 120, 135)
    elif i == 1:
        h.pulse = 2.15
        K._draw_wind_platform(native, 120, 175, h.pulse, None)
        K._draw_kaizen_walk(native, h, 120, 135)
    elif i == 2:
        h._kz_attack_progress = .52
        h._kz_attack_active = True
        h.range = 40
        K._draw_wind_platform(native, 120, 175, h.pulse, None)
        K._draw_kaizen_attack(native, h, 120, 135)
    else:
        h.active_skill = "r"
        h.active_skill_timer = 58
        h.target = SimpleNamespace(x=120, y=135, alive=True)
        K._draw_wind_platform(native, 120, 175, h.pulse, "r")
        K._draw_kaizen_idle(native, h, 120, 135)
        K._draw_tornado(native, h, 120, 135, 58, h.pulse)

    scaled = pygame.transform.scale(native, (240 * 2, 260 * 2))
    # Clip the intentionally oversized render inside each review card.
    old = screen.get_clip()
    screen.set_clip(panel.inflate(-8, -64))
    screen.blit(scaled, (x + 143 - 240, 162))
    screen.set_clip(old)

notes = (
    "tabi feet • saya • pauldron",
    "obi • embroidery • grounded",
    "hamon • slash arc • highlights",
    "layered procedural wind FX",
)
for j, text in enumerate(notes):
    screen.blit(font_small.render(text, True, (115, 151, 185)),
                (40 + j * 310, 686))

out = os.path.join(ROOT, "docs", "kaizen_masterwork_preview.png")
pygame.image.save(screen, out)
print(out)
