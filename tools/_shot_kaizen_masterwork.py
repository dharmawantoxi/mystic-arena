#!/usr/bin/env python3
"""Render review sheet untuk contoh upgrade procedural Kaizen (v2 rig).

Diperbarui ke rig masterwork v2 (~1.5x native). Untuk audit terukur +
sheet lengkap (skill FX per tahap, before/after), jalankan
``tools/_audit_kaizen_v2.py``.
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

# Lembar ini mem-preview FALLBACK CANVAS murni: lapisan hidup dimatikan
# supaya draw_kaizen tidak menekan smear/sabit in-canvas yang dipotret.
try:
    from heroes import kaizen_fx as _kzfx
    _kzfx.KAIZEN_FX_ENABLED = False
    K._LIVE_MOD = False
except Exception:
    pass

W, H = 1280, 720
screen = pygame.Surface((W, H))
screen.fill((5, 9, 18))
font_title = pygame.font.Font(None, 46)
font_label = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 20)

screen.blit(font_title.render("KAIZEN v5 — PIXEL MASTERWORK", True,
                              (166, 218, 255)), (38, 24))
screen.blit(font_small.render(
    "100% code-drawn • no external hero sprite • idle / walk / attack / "
    "ultimate (audit terukur: tools/_audit_kaizen_v2.py)", True,
    (132, 151, 181)), (40, 72))

labels = ("IDLE DETAIL", "GROUNDED WALK", "KATANA ATTACK", "TORNADO ULTIMATE")
for i, label in enumerate(labels):
    x = 30 + i * 310
    panel = pygame.Rect(x, 110, 286, 560)
    pygame.draw.rect(screen, (10, 17, 32), panel, border_radius=12)
    pygame.draw.rect(screen, (55, 112, 172), panel, 2, border_radius=12)
    screen.blit(font_label.render(label, True, (218, 236, 255)), (x + 16, 130))

    native = pygame.Surface((340, 380), pygame.SRCALPHA)
    h = _ProbeEntity("kaizen", 170, 200)
    h.pulse = 1.25
    h.direction = 1
    h.facing = 1
    if i == 0:
        K._draw_swordsman_rim_light(native, 170, 188, h.pulse)
        K._draw_wind_platform(native, 170, 258, h.pulse, None)
        K._draw_kaizen_idle(native, h, 170, 196)
    elif i == 1:
        h.pulse = 2.15
        K._draw_wind_platform(native, 170, 258, h.pulse, None)
        K._draw_kaizen_walk(native, h, 170, 196)
    elif i == 2:
        h._kz_attack_progress = .52
        h._kz_attack_active = True
        h.range = 40
        K._draw_wind_platform(native, 170, 258, h.pulse, None)
        K._draw_kaizen_attack(native, h, 170, 196)
    else:
        h.active_skill = "r"
        h.active_skill_timer = 58
        h.target = SimpleNamespace(x=170, y=200, alive=True)
        K._draw_wind_platform(native, 170, 258, h.pulse, "r")
        K._draw_kaizen_idle(native, h, 170, 196)
        K._draw_tornado(native, h, 170, 196, 58, h.pulse)

    scaled = pygame.transform.scale(native, (340 * 2, 380 * 2))
    # Clip the intentionally oversized render inside each review card.
    old = screen.get_clip()
    screen.set_clip(panel.inflate(-8, -64))
    screen.blit(scaled, (x + 170 - 340, 162))
    screen.set_clip(old)

notes = (
    "katana sori+tsuba • saya • hachimaki",
    "foot solver • obi • jubah grounded",
    "hamon • smear sabit • bintang IMPACT",
    "funnel berlapis • rune ring • puing",
)
for j, text in enumerate(notes):
    screen.blit(font_small.render(text, True, (115, 151, 185)),
                (40 + j * 310, 686))

out = os.path.join(ROOT, "docs", "kaizen_masterwork_preview.png")
pygame.image.save(screen, out)
print(out)

# A second sheet proves that this is a real procedural animation rig rather
# than one detailed pose moved as a sticker.
SW, SH = 1280, 780
strip = pygame.Surface((SW, SH))
strip.fill((5, 9, 18))
strip.blit(font_title.render("KAIZEN v5 — PROCEDURAL ANIMATION RIG", True,
                             (166, 218, 255)), (38, 24))
strip.blit(font_small.render(
    "Every frame below is recalculated from joints, phase, cloth and hair "
    "physics", True, (132, 151, 181)), (40, 72))

rows = (
    ("IDLE / BREATH", 4, "idle"),
    ("WALK / CONTACT", 6, "walk"),
    ("ATTACK / ARC", 6, "attack"),
)
for row, (label, count, action) in enumerate(rows):
    top = 112 + row * 218
    strip.blit(font_label.render(label, True, (130, 199, 255)), (36, top + 70))
    pygame.draw.line(strip, (42, 94, 145), (35, top + 104),
                     (1240, top + 104), 1)
    for i in range(count):
        native = pygame.Surface((170, 190), pygame.SRCALPHA)
        phase = (i / count) * math.pi * 2
        progress = i / max(1, count - 1)
        K._draw_kaizen_elite(native, 85, 100, 1, phase, action, progress)
        frame = pygame.transform.scale(native, (160, 179))
        fx = 190 + i * 170
        strip.blit(frame, (fx, top))
        pygame.draw.circle(strip, (95, 175, 235), (fx + 80, top + 188), 3)

strip_out = os.path.join(ROOT, "docs", "kaizen_animation_strip.png")
pygame.image.save(strip, strip_out)
print(strip_out)
