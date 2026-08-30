#!/usr/bin/env python3
"""Render review sheets for the Zephyr procedural masterwork v2."""
import math
import os
import sys
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
from heroes import _ProbeEntity
from heroes._bundle import _NS_zephyr as Z

W, H = 1280, 720
screen = pygame.Surface((W, H))
screen.fill((6, 7, 17))
font_title = pygame.font.Font(None, 46)
font_label = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 20)

screen.blit(font_title.render("ZEPHYR — PROCEDURAL MASTERWORK v2", True,
                              (255, 137, 207)), (38, 24))
screen.blit(font_small.render(
    "100% code-drawn • thorn crown / moth wings / living staff / Bedlam", True,
    (195, 143, 188)), (40, 72))

labels = ("THORN CROWN IDLE", "MOTH-WING WALK", "THORN STAFF CAST",
          "BEDLAM ULTIMATE")
for i, label in enumerate(labels):
    x = 30 + i * 310
    panel = pygame.Rect(x, 110, 286, 560)
    pygame.draw.rect(screen, (23, 11, 32), panel, border_radius=12)
    pygame.draw.rect(screen, (132, 52, 132), panel, 2, border_radius=12)
    screen.blit(font_label.render(label, True, (255, 220, 247)), (x + 16, 130))

    native = pygame.Surface((240, 260), pygame.SRCALPHA)
    h = _ProbeEntity("zephyr", 120, 135)
    h.pulse = 1.25
    h.direction = h.facing = 1
    h._portrait_hd = True
    if i == 0:
        Z._draw_fey_rim_light(native, 120, 125, h.pulse)
        Z._draw_fey_platform(native, 120, 175, h.pulse, None)
        Z._draw_zephyr_idle(native, h, 120, 135)
    elif i == 1:
        h.pulse = 2.15
        Z._draw_fey_platform(native, 120, 175, h.pulse, None)
        Z._draw_zephyr_walk(native, h, 120, 135)
    elif i == 2:
        h._zp_attack_progress = .55
        h._zp_attack_active = True
        h.range = 180
        Z._draw_fey_platform(native, 120, 175, h.pulse, None)
        Z._draw_zephyr_attack(native, h, 120, 135)
        Z._draw_cast_flash(native, 120, 135, 1, .55, h.pulse)
    else:
        h.active_skill = "r"
        h.active_skill_timer = 88
        h.target = SimpleNamespace(x=120, y=135, alive=True)
        Z._draw_fey_rim_light(native, 120, 125, h.pulse)
        Z._draw_fey_platform(native, 120, 175, h.pulse, "r")
        Z._draw_zephyr_idle(native, h, 120, 135)
        Z._draw_bedlam(native, h, 120, 135, 88, h.pulse)

    scaled = pygame.transform.scale(native, (480, 520))
    old = screen.get_clip()
    screen.set_clip(panel.inflate(-8, -64))
    screen.blit(scaled, (x + 143 - 240, 162))
    screen.set_clip(old)

notes = (
    "crown • circlet • corset lace",
    "four wing panels • planted boots",
    "pose-driven orb • thorn vine",
    "six fey echoes • spell ribbons",
)
for j, text in enumerate(notes):
    screen.blit(font_small.render(text, True, (191, 128, 183)),
                (40 + j * 310, 686))

out = os.path.join(ROOT, "docs", "zephyr_masterwork_preview.png")
pygame.image.save(screen, out)
print(out)

# A contact sheet proves the new body is a real animation rig rather than
# a detailed static portrait translated around the arena.
SW, SH = 1280, 780
strip = pygame.Surface((SW, SH))
strip.fill((6, 7, 17))
strip.blit(font_title.render("ZEPHYR — PROCEDURAL ANIMATION RIG", True,
                             (255, 137, 207)), (38, 24))
strip.blit(font_small.render(
    "Every frame recalculates crown locks, wing tips, gown panels, hands and staff position",
    True, (195, 143, 188)), (40, 72))

rows = (
    ("IDLE / BREATH", 4, "idle"),
    ("WALK / WING CONTACT", 6, "walk"),
    ("CAST / STAFF RELEASE", 6, "attack"),
)
for row, (label, count, action) in enumerate(rows):
    top = 112 + row * 218
    strip.blit(font_label.render(label, True, (250, 173, 220)), (36, top + 70))
    pygame.draw.line(strip, (104, 45, 110), (35, top + 104),
                     (1240, top + 104), 1)
    for i in range(count):
        native = pygame.Surface((100, 108), pygame.SRCALPHA)
        phase = (i / count) * math.tau
        progress = i / max(1, count - 1)
        Z._draw_zephyr_elite(native, 50, 61, 1, phase, action, progress)
        frame = pygame.transform.scale(native, (160, 173))
        # Leave a generous label gutter at left; the first sprite must not
        # paint over "WALK / WING CONTACT" or "CAST / STAFF RELEASE".
        fx = 250 + i * 170
        strip.blit(frame, (fx, top))
        pygame.draw.circle(strip, (242, 135, 208), (fx + 80, top + 188), 3)

strip_out = os.path.join(ROOT, "docs", "zephyr_animation_strip.png")
pygame.image.save(strip, strip_out)
print(strip_out)

# A dedicated skill sheet replaces the legacy-only visual guide and keeps
# all four gameplay effects inspectable after the rig rewrite.
skill = pygame.Surface((1060, 680))
skill.fill((6, 7, 17))
skill.blit(font_title.render("ZEPHYR — MASTERWORK SKILL VISUALS", True,
                             (255, 137, 207)), (30, 20))
skill.blit(font_small.render(
    "Spell art remains synchronized with the active gameplay timers.", True,
    (195, 143, 188)), (32, 62))

skill_labels = (("Q — BRAMBLE MAZE", "q", 110),
                ("W — SHADOW REALM", "w", 88),
                ("E — CASKET CURSE", "e", 105),
                ("R — BEDLAM", "r", 118))
for i, (label, ability, timer) in enumerate(skill_labels):
    col, row = i % 2, i // 2
    x, y = 28 + col * 514, 101 + row * 270
    card = pygame.Rect(x, y, 490, 238)
    pygame.draw.rect(skill, (20, 10, 29), card)
    pygame.draw.rect(skill, (105, 42, 108), card, 2)
    skill.blit(font_label.render(label, True, (255, 145, 211)), (x + 12, y + 10))
    native = pygame.Surface((245, 118), pygame.SRCALPHA)
    h = _ProbeEntity("zephyr", 82, 78)
    h.pulse = 1.3 + i * .37
    h.direction = h.facing = 1
    h.active_skill = ability
    h.active_skill_timer = timer
    h.target = SimpleNamespace(x=180, y=80, alive=True)
    if ability == "q":
        h._bramble_origin = (180, 80)
    Z.draw_zephyr(native, h, 82, 78)
    rendered = pygame.transform.scale(native, (490, 236))
    old = skill.get_clip()
    skill.set_clip(card.inflate(-4, -42))
    skill.blit(rendered, (x, y + 34))
    skill.set_clip(old)

skill_out = os.path.join(ROOT, "docs", "zephyr_skills_preview.png")
pygame.image.save(skill, skill_out)
print(skill_out)
