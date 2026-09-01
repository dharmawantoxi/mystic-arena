#!/usr/bin/env python3
"""Render review sheet untuk contoh upgrade procedural Thorne."""
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
from heroes._bundle import _NS_sylara as S

W, H = 1280, 720
screen = pygame.Surface((W, H))
screen.fill((5, 9, 18))
font_title = pygame.font.Font(None, 46)
font_label = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 20)

screen.blit(font_title.render("SYLARA — PROCEDURAL MASTERWORK", True, (190, 240, 150)), (38, 24))
screen.blit(font_small.render("100% code-drawn • no external hero sprite • idle / walk / attack / ultimate", True, (150, 185, 140)), (40, 72))

labels = ("IDLE DETAIL", "WALK CYCLE", "BOW DRAW", "WINDRUN + POWERSHOT")
for i, label in enumerate(labels):
    x = 30 + i * 310
    panel = pygame.Rect(x, 110, 286, 560)
    pygame.draw.rect(screen, (16, 32, 20), panel, border_radius=12)
    pygame.draw.rect(screen, (96, 156, 84), panel, 2, border_radius=12)
    screen.blit(font_label.render(label, True, (226, 246, 220)), (x + 16, 130))

    native = pygame.Surface((280, 300), pygame.SRCALPHA)
    h = _ProbeEntity("sylara", 140, 155)
    h.pulse = 1.25
    h.direction = 1
    h.facing = 1
    h._portrait_hd = True
    if i == 0:
        S._draw_wind_aura(native, 120, 125, h.pulse)
        S._draw_wind_platform(native, 120, 175, h.pulse, None)
        S._draw_sylara_idle(native, h, 120, 135)
    elif i == 1:
        h.pulse = 2.15
        S._draw_wind_platform(native, 120, 175, h.pulse, None)
        S._draw_sylara_walk(native, h, 120, 135)
    elif i == 2:
        h._sy_attack_progress = .42
        h._sy_attack_active = True
        S._draw_wind_platform(native, 120, 175, h.pulse, None)
        S._draw_sylara_attack(native, h, 120, 135)
    else:
        h.active_skill = "w"
        h.active_skill_timer = 58
        h.target = SimpleNamespace(x=320, y=135, alive=True)
        S._draw_wind_aura(native, 120, 125, h.pulse)
        S._draw_wind_platform(native, 120, 175, h.pulse, "w")
        S._draw_sylara_windrun(native, h, 120, 135, 58)

    scaled = pygame.transform.scale(native, (240 * 2, 260 * 2))
    # Clip the intentionally oversized render inside each review card.
    old = screen.get_clip()
    screen.set_clip(panel.inflate(-8, -64))
    screen.blit(scaled, (x + 143 - 240, 162))
    screen.set_clip(old)

notes = (
    "hood • braid • quiver arrows",
    "boots • cape tatters • gait",
    "recurve bow • nocked arrow",
    "wind streaks • dash stance",
)
for j, text in enumerate(notes):
    screen.blit(font_small.render(text, True, (140, 180, 130)),
                (40 + j * 310, 686))

out = os.path.join(ROOT, "docs", "sylara_masterwork_preview.png")
pygame.image.save(screen, out)
print(out)

# A second sheet proves that this is a real procedural animation rig rather
# than one detailed pose moved as a sticker.
SW, SH = 1280, 780
strip = pygame.Surface((SW, SH))
strip.fill((5, 9, 18))
strip.blit(font_title.render("SYLARA — PROCEDURAL ANIMATION RIG", True,
                             (190, 240, 150)), (38, 24))
strip.blit(font_small.render(
    "Every frame below is recalculated from joints, phase, bow draw and foot contact",
    True, (150, 185, 140)), (40, 72))

rows = (
    ("IDLE / BREATH", 4, "idle"),
    ("WALK / CONTACT", 6, "walk"),
    ("ATTACK / SHOOT", 6, "attack"),
)
for row, (label, count, action) in enumerate(rows):
    top = 112 + row * 218
    strip.blit(font_label.render(label, True, (180, 235, 140)), (36, top + 70))
    pygame.draw.line(strip, (70, 120, 62), (35, top + 104),
                     (1240, top + 104), 1)
    for i in range(count):
        native = pygame.Surface((100, 108), pygame.SRCALPHA)
        phase = (i / count) * math.pi * 2
        progress = i / max(1, count - 1)
        S._draw_sylara_elite(native, 50, 60, 1, phase, action, progress)
        frame = pygame.transform.scale(native, (160, 173))
        fx = 190 + i * 170
        strip.blit(frame, (fx, top))
        pygame.draw.circle(strip, (160, 225, 120), (fx + 80, top + 188), 3)

strip_out = os.path.join(ROOT, "docs", "sylara_animation_strip.png")
pygame.image.save(strip, strip_out)
print(strip_out)
