#!/usr/bin/env python3
"""Render review sheet untuk contoh upgrade procedural Grimjaw.

Menghasilkan:
  - docs/grimjaw_masterwork_preview.png   (sheet 4 panel pose)
  - docs/grimjaw_animation_strip.png      (contact sheet rig per frame)
  - docs/grimjaw_portrait_preview.png     (portrait LOD Hero Shop)

Jalankan:  python3 tools/_shot_grimjaw_masterwork.py
"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
from heroes import _ProbeEntity
from heroes._bundle import _NS_grimjaw as G

W, H = 1280, 720
screen = pygame.Surface((W, H))
screen.fill((5, 9, 18))
font_title = pygame.font.Font(None, 46)
font_label = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 20)

screen.blit(font_title.render("GRIMJAW — PROCEDURAL MASTERWORK", True,
                              (255, 205, 120)), (38, 24))
screen.blit(font_small.render(
    "100% code-drawn • no external hero sprite • idle / walk / attack / spin",
    True, (181, 161, 132)), (40, 72))

labels = ("IDLE DETAIL", "GROUNDED WALK", "FLAME BLADE SWING",
          "BLADE FURY SPIN")
for i, label in enumerate(labels):
    x = 30 + i * 310
    panel = pygame.Rect(x, 110, 286, 560)
    pygame.draw.rect(screen, (32, 22, 10), panel, border_radius=12)
    pygame.draw.rect(screen, (172, 122, 55), panel, 2, border_radius=12)
    screen.blit(font_label.render(label, True, (255, 236, 218)),
                (x + 16, 130))

    native = pygame.Surface((240, 260), pygame.SRCALPHA)
    h = _ProbeEntity("grimjaw", 120, 135)
    h.pulse = 1.25
    h.direction = 1
    h.facing = 1
    if i == 0:
        G._draw_fire_platform(native, 120, 178, h.pulse, None)
        G._draw_grimjaw_elite(native, 120, 132, 1, h.pulse, "idle",
                              0.0, 0.0, detail=True)
    elif i == 1:
        h.pulse = 2.15
        G._draw_grimjaw_walk(native, h, 120, 135)
    elif i == 2:
        h._gj_attack_progress = .55
        G._draw_grimjaw_attack(native, h, 120, 135)
    else:
        G._draw_fire_platform(native, 120, 178, h.pulse, "q")
        G._draw_grimjaw_body(native, 120, 133, 1, h.pulse, "spin",
                             spin_phase=2.0)
        G._draw_blade_fury_rings(native, 120, 155, h.pulse)

    scaled = pygame.transform.scale(native, (240 * 2, 260 * 2))
    old = screen.get_clip()
    screen.set_clip(panel.inflate(-8, -64))
    screen.blit(scaled, (x + 143 - 240, 162))
    screen.set_clip(old)

notes = (
    "flame mane • blood-strip mask",
    "planted boots • war sash",
    "pose-driven curved blade",
    "spin rig • fury rings",
)
for j, text in enumerate(notes):
    screen.blit(font_small.render(text, True, (185, 151, 115)),
                (40 + j * 310, 686))

out = os.path.join(ROOT, "docs", "grimjaw_masterwork_preview.png")
pygame.image.save(screen, out)
print(out)

# Contact sheet: setiap frame dihitung ulang dari sendi/phase, bukan
# sticker yang digeser.
SW, SH = 1280, 800
strip = pygame.Surface((SW, SH))
strip.fill((5, 9, 18))
strip.blit(font_title.render("GRIMJAW — PROCEDURAL ANIMATION RIG", True,
                             (255, 205, 120)), (38, 24))
strip.blit(font_small.render(
    "Every frame below is recalculated from joints, phase, mane wave and "
    "blade angle", True, (181, 161, 132)), (40, 72))

rows = (
    ("IDLE / BREATH", 4, "idle"),
    ("WALK / CONTACT", 6, "walk"),
    ("ATTACK / SWING", 6, "attack"),
)
for row, (label, count, action) in enumerate(rows):
    top = 112 + row * 222
    strip.blit(font_label.render(label, True, (255, 199, 130)),
               (36, top + 70))
    pygame.draw.line(strip, (145, 94, 42), (35, top + 104),
                     (1240, top + 104), 1)
    for i in range(count):
        native = pygame.Surface((120, 130), pygame.SRCALPHA)
        phase = (i / count) * math.pi * 2
        progress = i / max(1, count - 1)
        G._draw_grimjaw_elite(native, 60, 70, 1, phase, action, progress)
        frame = pygame.transform.scale(native, (156, 169))
        fx = 190 + i * 170
        strip.blit(frame, (fx, top))
        pygame.draw.circle(strip, (235, 175, 95), (fx + 78, top + 192), 3)

strip_out = os.path.join(ROOT, "docs", "grimjaw_animation_strip.png")
pygame.image.save(strip, strip_out)
print(strip_out)

# Portrait LOD Hero Shop: pass detail=True (jahitan, engraving, serat mane).
PW, PH = 640, 720
card = pygame.Surface((PW, PH))
card.fill((5, 9, 18))
card.blit(font_label.render("GRIMJAW — HERO SHOP PORTRAIT LOD", True,
                            (255, 205, 120)), (24, 20))
panel = pygame.Rect(24, 60, PW - 48, PH - 90)
pygame.draw.rect(card, (32, 22, 10), panel, border_radius=12)
pygame.draw.rect(card, (172, 122, 55), panel, 2, border_radius=12)

native = pygame.Surface((200, 220), pygame.SRCALPHA)
G._draw_grimjaw_elite(native, 100, 118, 1, 1.25, "idle", 0.0, 0.0,
                      detail=True)
scaled = pygame.transform.scale(native, (200 * 3, 220 * 3))
old = card.get_clip()
card.set_clip(panel.inflate(-8, -8))
card.blit(scaled, (PW // 2 - 300, 40))
card.set_clip(old)
card.blit(font_small.render(
    "detail pass: mane fibres • mask cracks • sash stitching • embers",
    True, (185, 151, 115)), (24, PH - 26))

portrait_out = os.path.join(ROOT, "docs", "grimjaw_portrait_preview.png")
pygame.image.save(card, portrait_out)
print(portrait_out)
