#!/usr/bin/env python3
"""Render review sheet untuk Gornak Procedural Masterwork.

Menghasilkan:
  - docs/gornak_masterwork_preview.png  (4 pose utama + barisan 1x ukuran arena)
  - docs/gornak_animation_strip.png      (contact sheet rig per frame)
  - docs/gornak_portrait_preview.png     (portrait LOD Hero Shop)

Jalankan:  python3 tools/_shot_gornak_masterwork.py
"""
import math
import os
import sys
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
from bosses.level1 import _NS_gornak as G

ACCENT = (200, 168, 246)
SUB = (150, 128, 178)
NOTE = (122, 104, 150)
PANEL = (11, 10, 24)
PANEL_EDGE = (86, 52, 128)
BG = (6, 7, 15)

# Crop di sekitar jangkar: kaki (GROUND_DY) sampai pucuk mohawk muat semua.
CROP_W, CROP_H = 118, 138
CANVAS = 190
ANCHOR = (CANVAS // 2, CANVAS // 2 + 24)   # (x, y) dunia di dalam canvas


def probe(cx=0.0, cy=0.0, **kw):
    """Objek minimal berisi atribut yang dibaca renderer gornak.

    ``cx, cy`` wajib sama dengan titik yang dipakai draw_gornak supaya efek
    yang mengikuti target (_target_position) jatuh di dalam panel.
    """
    b = SimpleNamespace(boss_type="gornak", boss_class="mini", x=float(cx),
                        y=float(cy), direction=1, facing=1, pulse=0.0,
                        timer=0, attack_cooldown=38, active_skill=None,
                        active_skill_timer=0, target=None,
                        _render_scale=1.0, hurt_flash_timer=0, alive=True,
                        radius=30)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def frame(boss, zoom=2.0, bg=PANEL, full=False, rig_only=None):
    """Render lalu crop + zoom nearest (tetap tajam, tidak di-blur)."""
    surf = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)
    if rig_only is not None:
        action, phase, ap = rig_only
        cx, cy = ANCHOR
        boss.x, boss.y = float(cx), float(cy)
        G._draw_gnk_rig(surf, cx, cy, boss.direction, phase, action, ap,
                        bool(getattr(boss, "_portrait_hd", False)))
        if action == "attack":
            G._draw_crescent_slash(surf, cx, cy, boss.direction, phase, ap)
    else:
        cx, cy = ANCHOR
        boss.x, boss.y = float(cx), float(cy)
        if not full:
            surf.fill(bg + (255,))
        G.draw_gornak(surf, boss, cx, cy)
    left = cx - CROP_W // 2
    top = cy - CROP_H // 2 - 8
    rect = pygame.Rect(left, top, CROP_W, CROP_H).clip(surf.get_rect())
    out = surf.subsurface(rect)
    if full:
        out = out.copy()
    return pygame.transform.scale(out, (rect.width * zoom, rect.height * zoom)) \
        if zoom != 1 else out.copy()


font_title = pygame.font.Font(None, 46)
font_label = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 20)

# ══════════════════════════════════════════════════════════════════
# Sheet 1 - empat pose utama + barisan ukuran arena sebenarnya
# ══════════════════════════════════════════════════════════════════
W, H = 1280, 880
screen = pygame.Surface((W, H))
screen.fill(BG)
screen.blit(font_title.render("GORNAK — PROCEDURAL MASTERWORK", True, ACCENT),
            (38, 18))
screen.blit(font_small.render(
    "100% code-drawn • tanpa PNG / sprite sheet • bone rig 2D berlapis + "
    "outline gelap 1 px • twin blade pose-driven", True, SUB), (40, 66))

cases = []
cases.append(("IDLE", probe(pulse=1.25), 2.4))
cases.append(("WALK CYCLE", probe(pulse=2.35), 2.4))
b = probe(pulse=1.15, timer=22)
b._gnk_attack_active = True
b._gnk_attack_progress = 0.52
cases.append(("ATTACK — SLASH ARC", b, 2.4))
b = probe(pulse=1.15, active_skill="r", active_skill_timer=44)
b.target = SimpleNamespace(x=float(ANCHOR[0] + 44), y=float(ANCHOR[1] - 14),
                           alive=True)
cases.append(("R — MANA VOID", b, 2.4))

PX, PY, PW_, PH_ = 26, 100, 296, 466
notes = ("kaki menapak di garis\nbayangan; tiap bagian\npunya batas sendiri",
         "langkah dihitung dari\nlutut & mata kaki,\nbukan sticker digeser",
         "bilah, slash, dan grip\nberasal dari sendi yang\nsama -> tak pernah lepas",
         "void tetap di target;\nbadan tidak tertutup\nefek tanah")
for i, (label, boss, zoom) in enumerate(cases):
    rect = pygame.Rect(PX + i * 310, PY, PW_, PH_)
    pygame.draw.rect(screen, PANEL, rect, border_radius=12)
    pygame.draw.rect(screen, PANEL_EDGE, rect, 2, border_radius=12)
    img = frame(boss, zoom=zoom)
    screen.blit(img, (rect.x + (rect.width - img.get_width()) // 2,
                      rect.y + 18))
    screen.blit(font_label.render(label, True, (232, 216, 255)),
                (rect.x + 14, rect.bottom - 30))
    for k, line in enumerate(notes[i].split("\n")):
        screen.blit(font_small.render(line, True, NOTE),
                    (rect.x + 14, rect.bottom + 12 + k * 15))

# ── Barisan 1x: ukuran sebenarnya di lane (HP bar & label seperti game) ──
STRIPO = 664
pygame.draw.rect(screen, (24, 27, 22), (26, STRIPO, 1228, 196),
                 border_radius=10)
screen.blit(font_small.render(
    "UKURAN ASLI 1x DI ARENA — bayangan, HP bar, dan label digambar pada "
    "posisi yang sama seperti Boss.draw()", True, ACCENT), (44, STRIPO + 10))
mini = [("idle", {}), ("walk", {"pulse": 2.4}),
        ("attack", {"pulse": 1.0, "timer": 22, "atk": 0.52}),
        ("Q", {"active_skill": "q", "active_skill_timer": 14}),
        ("W", {"active_skill": "w", "active_skill_timer": 5}),
        ("E", {"active_skill": "e", "active_skill_timer": 40}),
        ("R", {"active_skill": "r", "active_skill_timer": 34}),
        ("hurt", {"hurt_flash_timer": 5})]
for i, (name, kw) in enumerate(mini):
    cx = 100 + i * 152
    cy = STRIPO + 132
    args = {k: v for k, v in kw.items() if k not in ("atk", "pulse")}
    b = probe(cx, cy, pulse=kw.get("pulse", 1.3), **args)
    if "atk" in kw:
        b._gnk_attack_active = True
        b._gnk_attack_progress = kw["atk"]
    if name in ("Q", "R"):
        b.target = SimpleNamespace(x=cx + 108.0, y=cy - 8.0, alive=True)
    pygame.draw.ellipse(screen, (0, 0, 0), (cx - 35, cy + 25, 70, 12))
    G.draw_gornak(screen, b, cx, cy)
    bx, by = cx - 30, cy - 45
    pygame.draw.rect(screen, (40, 0, 0), (bx, by, 60, 8))
    pygame.draw.rect(screen, (100, 220, 100), (bx, by, 42, 8))
    pygame.draw.rect(screen, (255, 200, 50), (bx, by, 60, 8), 1)
    lbl = font_small.render("BOSS: Gornak", True, (255, 220, 100))
    screen.blit(lbl, lbl.get_rect(center=(cx, cy - 55)))
    screen.blit(font_label.render(name, True, (240, 240, 240)),
                (cx - 22, STRIPO + 168))

out = os.path.join(ROOT, "docs", "gornak_masterwork_preview.png")
pygame.image.save(screen, out)
print(out)

# ══════════════════════════════════════════════════════════════════
# Sheet 2 - contact sheet: setiap frame dihitung ulang dari sendi
# ══════════════════════════════════════════════════════════════════
SW, SH = 1280, 800
strip = pygame.Surface((SW, SH))
strip.fill(BG)
strip.blit(font_title.render("GORNAK — PROCEDURAL ANIMATION RIG", True,
                             ACCENT), (38, 18))
strip.blit(font_small.render(
    "Setiap frame dihitung ulang dari sendi, phase, ayunan bilah, dan sudut "
    "jubah - tidak ada satu pun bagian yang hanya digeser", True, SUB),
    (40, 66))

rows = (("IDLE / BREATH", 5, "idle"),
        ("WALK / STRIDE", 5, "walk"),
        ("ATTACK / SLASH", 5, "attack"))
CELL = 150
for row, (label, count, action) in enumerate(rows):
    top = 106 + row * 224
    strip.blit(font_label.render(label, True, ACCENT), (34, top + 96))
    pygame.draw.line(strip, (74, 52, 108), (34, top + 132), (SW - 34, top + 132),
                     1)
    for i in range(count):
        phase = (i / count) * math.tau
        ph = phase * 2.0 if action == "walk" else phase
        if action == "attack":
            progress = (0.02, 0.16, 0.44, 0.58, 0.82)[i]
        else:
            progress = 0.0
        b = probe(pulse=ph)
        img = frame(b, zoom=1, rig_only=(action, ph, progress))
        fx = 208 + i * (CELL + 12)
        pygame.draw.rect(strip, PANEL, (fx - 6, top - 6, CELL + 12, CELL + 12))
        strip.blit(img, (fx, top))
        strip.blit(font_small.render(
            ("p=%.2f" % progress) if action == "attack" else
            ("φ=%.2f" % ph), True, NOTE), (fx + 4, top + CELL - 18))

strip_out = os.path.join(ROOT, "docs", "gornak_animation_strip.png")
pygame.image.save(strip, strip_out)
print(strip_out)

# ══════════════════════════════════════════════════════════════════
# Sheet 3 - portrait LOD Hero Shop (detail pass, tanpa aura & rune tanah)
# ══════════════════════════════════════════════════════════════════
PW, PH = 640, 720
card = pygame.Surface((PW, PH))
card.fill(BG)
card.blit(font_label.render("GORNAK — HERO SHOP PORTRAIT LOD", True, ACCENT),
          (24, 18))
panel = pygame.Rect(24, 56, PW - 48, PH - 106)
pygame.draw.rect(card, PANEL, panel, border_radius=12)
pygame.draw.rect(card, PANEL_EDGE, panel, 2, border_radius=12)

buf = pygame.Surface((G.RIG_W, G.RIG_H), pygame.SRCALPHA)
G._draw_gnk_rig(buf, G.RIG_OX, G.RIG_OY + 4, 1, 1.25, "idle", 0.0, True)
Z = 5
big = pygame.transform.scale(buf, (G.RIG_W * Z, G.RIG_H * Z))
edge = big.copy()
edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
blit_at = (panel.centerx - G.RIG_OX * Z, panel.centery + 14 - (G.RIG_OY + 4) * Z)
for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
    card.blit(edge, (blit_at[0] + dx, blit_at[1] + dy))
card.blit(big, blit_at)
card.blit(font_small.render(
    "pass portrait: serat mohawk • grain kulit • jahitan loincloth • "
    "ukiran pelat baja • garis hamon bilah • tato rune", True, NOTE),
    (26, PH - 40))
card.blit(font_small.render(
    "aura & rune tanah sengaja DIBUANG di portrait agar auto-crop terisi "
    "wajah dan material, bukan lingkaran efek", True, NOTE), (26, PH - 22))

portrait_out = os.path.join(ROOT, "docs", "gornak_portrait_preview.png")
pygame.image.save(card, portrait_out)
print(portrait_out)
