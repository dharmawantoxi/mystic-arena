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
from heroes._bundle import _NS_thorne as T

W, H = 1280, 720
screen = pygame.Surface((W, H))
screen.fill((5, 9, 18))
font_title = pygame.font.Font(None, 46)
font_label = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 20)

screen.blit(font_title.render("THORNE — PROCEDURAL MASTERWORK", True, (255, 205, 120)), (38, 24))
screen.blit(font_small.render("100% code-drawn • no external hero sprite • idle / walk / attack / ultimate", True, (181, 161, 132)), (40, 72))

labels = ("IDLE DETAIL", "GROUNDED WALK", "CLUB SMASH", "WARPATH ULTIMATE")
for i, label in enumerate(labels):
    x = 30 + i * 310
    panel = pygame.Rect(x, 110, 286, 560)
    pygame.draw.rect(screen, (32, 22, 10), panel, border_radius=12)
    pygame.draw.rect(screen, (172, 122, 55), panel, 2, border_radius=12)
    screen.blit(font_label.render(label, True, (255, 236, 218)), (x + 16, 130))

    native = pygame.Surface((240, 260), pygame.SRCALPHA)
    h = _ProbeEntity("thorne", 120, 135)
    h.pulse = 1.25
    h.direction = 1
    h.facing = 1
    h._portrait_hd = True
    if i == 0:
        T._draw_dust_aura(native, 120, 125, h.pulse)
        T._draw_ground_platform(native, 120, 175, h.pulse, None)
        T._draw_thorne_idle(native, h, 120, 135)
    elif i == 1:
        h.pulse = 2.15
        T._draw_ground_platform(native, 120, 175, h.pulse, None)
        T._draw_thorne_walk(native, h, 120, 135)
    elif i == 2:
        h._th_attack_progress = .52
        h._th_attack_active = True
        T._draw_ground_platform(native, 120, 175, h.pulse, None)
        T._draw_thorne_attack(native, h, 120, 135)
    else:
        h.active_skill = "r"
        h.active_skill_timer = 58
        h.target = SimpleNamespace(x=120, y=135, alive=True)
        T._draw_rage_aura(native, 120, 125, h.pulse)
        T._draw_ground_platform(native, 120, 175, h.pulse, "r")
        T._draw_thorne_idle(native, h, 120, 135)
        T._draw_warpath_effect(native, h, 120, 135, 58, h.pulse)

    scaled = pygame.transform.scale(native, (240 * 2, 260 * 2))
    # Clip the intentionally oversized render inside each review card.
    old = screen.get_clip()
    screen.set_clip(panel.inflate(-8, -64))
    screen.blit(scaled, (x + 143 - 240, 162))
    screen.set_clip(old)

notes = (
    "tusks • quill mane • pauldron",
    "claws • belt • grounded stance",
    "flanged mace • impact sparks",
    "rage cracks • ember ring",
)
for j, text in enumerate(notes):
    screen.blit(font_small.render(text, True, (185, 151, 115)),
                (40 + j * 310, 686))

out = os.path.join(ROOT, "docs", "thorne_masterwork_preview.png")
pygame.image.save(screen, out)
print(out)

# A second sheet proves that this is a real procedural animation rig rather
# than one detailed pose moved as a sticker.
SW, SH = 1280, 780
strip = pygame.Surface((SW, SH))
strip.fill((5, 9, 18))
strip.blit(font_title.render("THORNE — PROCEDURAL ANIMATION RIG", True,
                             (255, 205, 120)), (38, 24))
strip.blit(font_small.render(
    "Every frame below is recalculated from joints, phase, quill flare and foot contact",
    True, (181, 161, 132)), (40, 72))

rows = (
    ("IDLE / BREATH", 4, "idle"),
    ("WALK / CONTACT", 6, "walk"),
    ("ATTACK / SMASH", 6, "attack"),
)
for row, (label, count, action) in enumerate(rows):
    top = 112 + row * 218
    strip.blit(font_label.render(label, True, (255, 199, 130)), (36, top + 70))
    pygame.draw.line(strip, (145, 94, 42), (35, top + 104),
                     (1240, top + 104), 1)
    for i in range(count):
        native = pygame.Surface((100, 108), pygame.SRCALPHA)
        phase = (i / count) * math.pi * 2
        progress = i / max(1, count - 1)
        T._draw_thorne_elite(native, 50, 60, 1, phase, action, progress)
        frame = pygame.transform.scale(native, (160, 173))
        fx = 190 + i * 170
        strip.blit(frame, (fx, top))
        pygame.draw.circle(strip, (235, 175, 95), (fx + 80, top + 188), 3)

strip_out = os.path.join(ROOT, "docs", "thorne_animation_strip.png")
pygame.image.save(strip, strip_out)
print(strip_out)
