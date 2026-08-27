#!/usr/bin/env python3
"""Render review sheet untuk contoh upgrade procedural Vex.

Menghasilkan:
  - docs/vex_masterwork_preview.png   (sheet 4 panel pose)
  - docs/vex_animation_strip.png      (contact sheet rig per frame)
  - docs/vex_portrait_preview.png     (portrait LOD Hero Shop)

Jalankan:  python3 tools/_shot_vex_masterwork.py
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
from heroes._bundle import _NS_vex as V

W, H = 1280, 720
screen = pygame.Surface((W, H))
screen.fill((5, 9, 18))
font_title = pygame.font.Font(None, 46)
font_label = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 20)

screen.blit(font_title.render("VEX — PROCEDURAL MASTERWORK", True,
                              (140, 235, 230)), (38, 24))
screen.blit(font_small.render(
    "100% code-drawn • no external hero sprite • idle / glide / orb / ultimate",
    True, (141, 161, 172)), (40, 72))

labels = ("IDLE DETAIL", "VOID GLIDE", "ARCANE ORB RELEASE",
          "ESSENCE FLUX (R)")
for i, label in enumerate(labels):
    x = 30 + i * 310
    panel = pygame.Rect(x, 110, 286, 560)
    pygame.draw.rect(screen, (10, 22, 32), panel, border_radius=12)
    pygame.draw.rect(screen, (45, 165, 175), panel, 2, border_radius=12)
    screen.blit(font_label.render(label, True, (219, 255, 250)),
                (x + 16, 130))

    native = pygame.Surface((240, 260), pygame.SRCALPHA)
    h = _ProbeEntity("vex", 120, 135)
    h.pulse = 1.25
    h.direction = 1
    h.facing = 1
    if i == 0:
        V._draw_vex_elite(native, 120, 132, 1, h.pulse, "idle", 0.0,
                          detail=True)
    elif i == 1:
        h.pulse = 2.15
        V._draw_vex_walk(native, h, 120, 135)
    elif i == 2:
        h._vx_attack_progress = .6
        V._draw_vex_attack(native, h, 120, 135)
    else:
        h.active_skill = "r"
        h.active_skill_timer = 58
        h.target = SimpleNamespace(x=120, y=135, alive=True)
        V.draw_vex(native, h, 120, 135)

    scaled = pygame.transform.scale(native, (240 * 2, 260 * 2))
    old = screen.get_clip()
    screen.set_clip(panel.inflate(-8, -64))
    screen.blit(scaled, (x + 143 - 240, 162))
    screen.set_clip(old)

notes = (
    "void crown • shadow hood",
    "tattered robe • back cape",
    "pose-driven staff orb",
    "flux ring • rune trail",
)
for j, text in enumerate(notes):
    screen.blit(font_small.render(text, True, (115, 151, 185)),
                (40 + j * 310, 686))

out = os.path.join(ROOT, "docs", "vex_masterwork_preview.png")
pygame.image.save(screen, out)
print(out)

# Contact sheet: setiap frame dihitung ulang dari sendi/phase, bukan
# sticker yang digeser.
SW, SH = 1280, 800
strip = pygame.Surface((SW, SH))
strip.fill((5, 9, 18))
strip.blit(font_title.render("VEX — PROCEDURAL ANIMATION RIG", True,
                             (140, 235, 230)), (38, 24))
strip.blit(font_small.render(
    "Every frame below is recalculated from joints, phase, crown wave and "
    "staff orb", True, (141, 161, 172)), (40, 72))

rows = (
    ("IDLE / BREATH", 4, "idle"),
    ("GLIDE / SWAY", 6, "walk"),
    ("ATTACK / ORB", 6, "attack"),
)
for row, (label, count, action) in enumerate(rows):
    top = 112 + row * 222
    strip.blit(font_label.render(label, True, (140, 235, 230)),
               (36, top + 70))
    pygame.draw.line(strip, (45, 120, 145), (35, top + 104),
                     (1240, top + 104), 1)
    for i in range(count):
        native = pygame.Surface((120, 140), pygame.SRCALPHA)
        phase = (i / count) * math.pi * 2
        progress = i / max(1, count - 1)
        V._draw_vex_elite(native, 60, 75, 1, phase, action, progress)
        frame = pygame.transform.scale(native, (156, 182))
        fx = 190 + i * 170
        strip.blit(frame, (fx, top))
        pygame.draw.circle(strip, (95, 225, 220), (fx + 78, top + 196), 3)

strip_out = os.path.join(ROOT, "docs", "vex_animation_strip.png")
pygame.image.save(strip, strip_out)
print(strip_out)

# Portrait LOD Hero Shop: pass detail=True (rune, weave, crown rim).
PW, PH = 640, 720
card = pygame.Surface((PW, PH))
card.fill((5, 9, 18))
card.blit(font_label.render("VEX — HERO SHOP PORTRAIT LOD", True,
                            (140, 235, 230)), (24, 20))
panel = pygame.Rect(24, 60, PW - 48, PH - 90)
pygame.draw.rect(card, (10, 22, 32), panel, border_radius=12)
pygame.draw.rect(card, (45, 165, 175), panel, 2, border_radius=12)

native = pygame.Surface((200, 220), pygame.SRCALPHA)
V._draw_vex_elite(native, 100, 118, 1, 1.25, "idle", 0.0, detail=True)
scaled = pygame.transform.scale(native, (200 * 3, 220 * 3))
old = card.get_clip()
card.set_clip(panel.inflate(-8, -8))
card.blit(scaled, (PW // 2 - 300, 40))
card.set_clip(old)
card.blit(font_small.render(
    "detail pass: crown rim • robe weave • rune trace • void embers",
    True, (115, 151, 185)), (24, PH - 26))

portrait_out = os.path.join(ROOT, "docs", "vex_portrait_preview.png")
pygame.image.save(card, portrait_out)
print(portrait_out)
