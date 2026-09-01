#!/usr/bin/env python3
"""Audit + preview sheet untuk Vex renderer masterwork v2.1.

Mengukur acceptance criteria yang sebelumnya hanya dinilai visual:
  - renderer tetap prosedural (tanpa pygame.image.load / PNG / sprite sheet)
  - native rig ~1.5x lalu dinormalisasi pipeline hero ke tinggi arena wajar
  - bbox pose, warna unik, dan portrait LOD
  - frame walk/attack unik (bukan sticker translation)
  - Q/W/E/R punya FX di luar siluet badan
  - telegraph W/R world-space: radius dunia dikompensasi 1/_render_scale
  - waktu render cache-miss dibanding soft target ~3.5 ms

Menghasilkan:
  - docs/vex_v2_review.png
  - docs/vex_v2_anim_strip.png
  - docs/vex_v2_ingame.png
  - docs/vex_v2_skills.png
"""
from __future__ import annotations

import inspect
import math
import os
import sys
import time
from collections import Counter
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import heroes
from heroes import _ProbeEntity, render_hero, _get_hero_scale
from heroes._bundle import _NS_vex as V


def colors_of(surface: pygame.Surface) -> set[tuple[int, int, int]]:
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def elite_frame(action="idle", phase=1.25, progress=0.0, facing=1,
                size=320, anchor=None, detail=False, skill_state=None):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    ax = ay = size // 2 if anchor is None else anchor
    V._draw_vex_elite(s, ax, ay, facing, phase, action, progress,
                      detail, skill_state)
    return s


def skill_frame(skill: str, timer: int, fs: float = 1.0,
                size: int = 760, target_offset=(145, -20)):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    x, y = size // 2, size // 2 + 40
    h = _ProbeEntity("vex", x, y)
    h.pulse = 1.3
    h.direction = h.facing = 1
    h.active_skill = skill
    h.active_skill_timer = timer
    h.target = SimpleNamespace(x=x + target_offset[0],
                               y=y + target_offset[1], alive=True)
    h._render_scale = fs
    V.draw_vex(s, h, x, y)
    return s, x, y


def check(cond: bool, label: str, extra: str = "") -> bool:
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return bool(cond)


def bench(fn, n=30) -> float:
    fn()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n * 1000.0


def ring_hits(surface: pygame.Surface, cx: int, cy: int, radius_px: int,
              alpha=40) -> int:
    hits = 0
    for a in range(0, 360, 2):
        x = int(cx + math.cos(math.radians(a)) * radius_px)
        y = int(cy + math.sin(math.radians(a)) * radius_px)
        if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
            if surface.get_at((x, y)).a > alpha:
                hits += 1
    return hits


def count_fx_outside_body(skill: str, timer: int, matcher, fs=1.0,
                          size=760, rmin=52, rmax=10**6) -> int:
    s, cx, cy = skill_frame(skill, timer, fs=fs, size=size)
    # Body-only mask at same anchor. Pixels outside mask prove FX is not
    # swallowed inside the silhouette.
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    V._draw_vex_elite(mask, cx, cy, 1, 1.3, "idle", 0.0, False, skill)
    n = 0
    for y in range(0, size, 2):
        for x in range(0, size, 2):
            if math.hypot(x - cx, y - cy) < rmin:
                continue
            if math.hypot(x - cx, y - cy) > rmax:
                continue
            if mask.get_at((x, y)).a <= 8 and matcher(s.get_at((x, y))):
                n += 1
    return n


ok_all = True

# ── 1. prosedural + helpers v2.1 ─────────────────────────────────
source = inspect.getsource(V)
ok_all &= check("pygame.image.load" not in source,
                "renderer prosedural: tidak memakai image.load")
ok_all &= check(".png" not in source.lower(),
                "renderer prosedural: tidak menyebut PNG/sprite sheet")
for name in ("_fx_scale", "_spark_star", "_chevron", "_dashed_ring",
             "_jagged_crack", "_static", "_tuft_points",
             "_draw_arcane_orb_telegraph", "_draw_staff_smear"):
    ok_all &= check(callable(getattr(V, name)), f"helper tersedia {name}")
ok_all &= check(1.45 <= V.RIG_SCALE <= 1.60, "RIG_SCALE ~1.5x", str(V.RIG_SCALE))

# ── 2. ukuran native dan pipeline normalization ──────────────────
body = elite_frame("idle")
bb = body.get_bounding_rect(min_alpha=8)
ok_all &= check(bb.height >= 150 and bb.width >= 95,
                "bbox idle native v2", f"{bb.w}x{bb.h}")
scale = _get_hero_scale("vex")
screen_h = bb.height * scale
ok_all &= check(60 <= screen_h <= 92,
                "tinggi badan di layar tetap normal",
                f"{screen_h:.1f}px scale={scale:.3f}")

# ── 3. warna material + portrait LOD ─────────────────────────────
pal = V.PALETTE
got = colors_of(body)
for key in ("void_darkest", "void_dark", "void_mid", "void_light",
            "void_bright", "void_hot", "staff_light", "armor_shine",
            "armor_rim"):
    ok_all &= check(pal[key] in got, f"swatch {key}", str(pal[key]))
port = elite_frame("idle", detail=True)
nc, pc = len(colors_of(body)), len(colors_of(port))
ok_all &= check(pc >= nc, "portrait LOD tidak kehilangan detail",
                f"{nc} -> {pc}")

# ── 4. frame unik dan attack impact ──────────────────────────────
walk = {pygame.image.tobytes(elite_frame("walk", i * math.tau / 8), "RGBA")
        for i in range(8)}
atk = {pygame.image.tobytes(elite_frame("attack", 0, i / 9.0), "RGBA")
       for i in range(10)}
ok_all &= check(len(walk) == 8, "walk: 8 frame unik", str(len(walk)))
ok_all &= check(len(atk) >= 8, "attack: multi-keyframe + impact unik",
                f"{len(atk)}/10")
impact = elite_frame("attack", progress=V.ATTACK_IMPACT)
pre = elite_frame("attack", progress=max(0.0, V.ATTACK_IMPACT - .18))
ok_all &= check(pygame.image.tobytes(impact, "RGBA") !=
                pygame.image.tobytes(pre, "RGBA"),
                "attack IMPACT frame berbeda")

# ── 5. skill pixels outside silhouette ───────────────────────────
_void = lambda c: c.a > 70 and c[2] > 95 and c[0] < 150
_gold = lambda c: c.a > 70 and c[0] > 170 and c[1] > 120 and c[2] < 120
_astral = lambda c: c.a > 70 and c[2] > 120 and c[0] > 80
_hot = lambda c: c.a > 70 and c[0] > 160 and c[2] > 90
checks = (
    ("q", 20, _void, 18, 45),
    ("w", 50, _void, 55, 55),
    ("e", 30, _astral, 24, 45),
    ("r", 40, lambda c: _hot(c) or _gold(c), 55, 55),
)
for skill, timer, matcher, threshold, rmin in checks:
    n = count_fx_outside_body(skill, timer, matcher, fs=1.0,
                              rmin=rmin, rmax=360)
    ok_all &= check(n >= threshold,
                    f"{skill.upper()}: FX pixel di luar siluet badan",
                    str(n))

# ── 6. telegraph radius world-space ──────────────────────────────
for fs in (1.0, 0.50):
    s, cx, cy = skill_frame("w", 50, fs=fs, size=760)
    n = ring_hits(s, cx, cy, int(60 / fs))
    ok_all &= check(n > 90, f"W ring radius 60 dunia @fs={fs}", f"{n}/180")
# R needs larger canvas because 180/0.5 = 360 px.
s, cx, cy = skill_frame("r", 40, fs=0.50, size=900)
n = ring_hits(s, cx, cy, int(180 / 0.50))
ok_all &= check(n > 90, "R ring radius 180 dunia @fs=0.5", f"{n}/180")
# Q/E target rings stay readable in projected target space.
for skill, timer, r in (("q", 20, 44), ("e", 30, 60)):
    s, cx, cy = skill_frame(skill, timer, fs=0.50, size=760,
                            target_offset=(160, -10))
    tx, ty = cx + int(160 / 0.50), cy + int(-10 / 0.50)
    tx = max(16, min(s.get_width() - 16, tx))
    ty = max(16, min(s.get_height() - 16, ty))
    # search an annulus because target rings pulse/dash.
    ann = 0
    for yy in range(max(0, ty - r - 12), min(s.get_height(), ty + r + 13), 2):
        for xx in range(max(0, tx - r - 12), min(s.get_width(), tx + r + 13), 2):
            d = math.hypot(xx - tx, yy - ty)
            if r - 10 <= d <= r + 12 and s.get_at((xx, yy)).a > 40:
                ann += 1
    ok_all &= check(ann > 18, f"{skill.upper()} target telegraph annulus", str(ann))

# ── 7. cache-miss timing ─────────────────────────────────────────
timing = {}
for skill, timer in (("idle", 0), ("q", 20), ("w", 50), ("e", 30), ("r", 40)):
    surf = pygame.Surface((520, 520), pygame.SRCALPHA)
    h = _ProbeEntity("vex", 260, 260)
    h.pulse = 1.3
    h.direction = h.facing = 1
    h.target = SimpleNamespace(x=360, y=250, alive=True)
    h._render_scale = 0.50
    if skill != "idle":
        h.active_skill = skill
        h.active_skill_timer = timer
    def render_once(h=h, surf=surf):
        surf.fill((0, 0, 0, 0))
        V.draw_vex(surf, h, 260, 260)
    timing[skill] = bench(render_once, 25)
for k, ms in timing.items():
    print(f"[i] Vex {k}: {ms:.2f} ms/frame (cache-miss, soft target ~3.5)")
ok_all &= check(max(timing.values()) <= 4.2,
                "cache-miss timing dekat target 3.5ms",
                f"max={max(timing.values()):.2f}ms")

# ═══════════════════════ PREVIEW SHEETS ══════════════════════════
font_title = pygame.font.Font(None, 44)
font_label = pygame.font.Font(None, 30)
font_small = pygame.font.Font(None, 21)
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)

# ── review sheet ──
W, H = 1400, 860
sheet = pygame.Surface((W, H))
sheet.fill((5, 7, 18))
sheet.blit(font_title.render("VEX v2.1 - PIXEL MASTERWORK (100% prosedural)",
                             True, (232, 244, 255)), (36, 22))
sheet.blit(font_small.render(
    "rig 1.52x native • void/astral hue ramps • selout • jagged cloak • "
    "staff crescent • foot solver • impact smear • skill-reactive glow",
    True, (160, 190, 218)), (38, 66))

cards = (
    ("IDLE / LIVING FLOAT", dict(action="idle", phase=1.25, skill_state=None)),
    ("WALK / FOOT SOLVER", dict(action="walk", phase=2.4, skill_state=None)),
    ("STAFF STRIKE (impact)", dict(action="attack", phase=1.0,
                                  progress=V.ATTACK_IMPACT, skill_state="q")),
    ("ULTIMATE OVERCHARGE", dict(action="idle", phase=1.25, skill_state="r")),
)
for i, (label, kw) in enumerate(cards):
    x0 = 28 + i * 340
    panel = pygame.Rect(x0, 100, 322, 600)
    pygame.draw.rect(sheet, (12, 13, 31), panel, border_radius=12)
    pygame.draw.rect(sheet, (93, 174, 222), panel, 2, border_radius=12)
    sheet.blit(font_label.render(label, True, (236, 248, 255)), (x0 + 16, 116))
    native = pygame.Surface((320, 320), pygame.SRCALPHA)
    V._draw_vex_elite(native, 160, 174, 1, kw.get("phase", 0),
                      kw["action"], kw.get("progress", 0.0), False,
                      kw.get("skill_state"))
    scaled = pygame.transform.scale(native, (640, 640))
    old = sheet.get_clip()
    sheet.set_clip(panel.inflate(-10, -66))
    sheet.blit(scaled, (x0 + 161 - 320, 144))
    sheet.set_clip(old)
notes = ("faceted hood • spec clusters • cyan key light",
         "contact sparks • cloak lag • greave solver",
         "multi-keyframe arc • smear • impact flash",
         "crest/staff/body glow react to skill state")
for j, text in enumerate(notes):
    sheet.blit(font_small.render(text, True, (162, 210, 236)),
               (44 + j * 340, 712))
out1 = os.path.join(ROOT, "docs", "vex_v2_review.png")
pygame.image.save(sheet, out1)
print(out1)

# ── animation strip ──
SW, SH = 1400, 900
strip = pygame.Surface((SW, SH))
strip.fill((5, 7, 18))
strip.blit(font_title.render("VEX v2.1 - PROSEDURAL ANIMATION RIG", True,
                             (232, 244, 255)), (36, 22))
strip.blit(font_small.render(
    "tiap frame dihitung dari rig, foot contact, cloak inertia, dan attack timeline",
    True, (160, 190, 218)), (38, 66))
rows = (("IDLE / BREATH", 6, "idle"),
        ("WALK / CONTACT", 8, "walk"),
        ("ATTACK / STAFF ARC", 10, "attack"))
for row, (label, count, action) in enumerate(rows):
    top = 108 + row * 262
    strip.blit(font_label.render(label, True, (176, 224, 255)), (36, top + 66))
    pygame.draw.line(strip, (54, 96, 130), (35, top + 100),
                     (1364, top + 100), 1)
    for i in range(count):
        native = pygame.Surface((180, 210), pygame.SRCALPHA)
        phase = i / count * math.tau
        progress = i / max(1, count - 1)
        V._draw_vex_elite(native, 90, 118, 1, phase, action, progress)
        frame = pygame.transform.scale(native, (180, 210))
        fx = 192 + i * 123
        strip.blit(frame, (fx, top))
out2 = os.path.join(ROOT, "docs", "vex_v2_anim_strip.png")
pygame.image.save(strip, out2)
print(out2)

# ── in-game size after pipeline normalization ──
GW, GH = 1200, 440
game = pygame.Surface((GW, GH))
game.fill((18, 25, 35))
for gy in range(0, GH, 40):
    pygame.draw.line(game, (22, 33, 46), (0, gy), (GW, gy), 1)
pygame.draw.line(game, (50, 65, 78), (0, 330), (GW, 330), 3)
game.blit(font_title.render(
    "VEX v2.1 - UKURAN ASLI DI ARENA (cache hero + lighting + outline)",
    True, (232, 244, 255)), (30, 18))
poses = (
    ("idle", 1.1, 0.0, None), ("walk", 2.2, 0.0, None),
    ("attack windup", 0, .18, None), ("attack impact", 0, V.ATTACK_IMPACT, None),
    ("essence flux", 1.3, 0.0, "r"),
)
xpos = 130
for i, (name, ph, prog, skill) in enumerate(poses):
    hero = _ProbeEntity("vex", xpos, 300)
    hero.pulse = ph
    hero.direction = hero.facing = 1
    hero.team = "blue" if i % 2 == 0 else "red"
    if prog:
        hero._vx_attack_active = True
        hero._vx_attack_progress = prog
        hero.timer = max(1, int((1 - prog) * 50))
        hero._vx_prev_timer = 0
    if skill:
        hero.active_skill = skill
        hero.active_skill_timer = 50
    render_hero("vex", game, hero, xpos, 300)
    game.blit(font_small.render(name, True, (210, 226, 236)), (xpos - 48, 336))
    xpos += 210
out3 = os.path.join(ROOT, "docs", "vex_v2_ingame.png")
pygame.image.save(game, out3)
print(out3)

# ── skill FX sheet: 4 skill x 3 tahap ──
KW, KH = 1500, 1160
skills_sheet = pygame.Surface((KW, KH))
skills_sheet.fill((5, 7, 18))
skills_sheet.blit(font_title.render(
    "VEX v3.0 - SKILL FX VOID ASTRAL CINEMATIC (world-space, prosedural)", True,
    (232, 244, 255)), (36, 22))
skills_sheet.blit(font_small.render(
    "Q conduit+portal • W gerhana+Mahkota Kristal • E rantai+sangkar kaca • R event horizon+accretion",
    True, (160, 190, 218)), (38, 66))
skill_cards = (
    ("Q - ARCANE ORB", "q", (10, 20, 38), (38, 22, 8)),
    ("W - SANITY'S ECLIPSE", "w", (12, 18, 36), (75, 45, 14)),
    ("E - ASTRAL PRISON", "e", (18, 12, 44), (45, 26, 10)),
    ("R - ESSENCE FLUX", "r", (22, 8, 34), (60, 36, 12)),
)
stages = (("aktivasi", .90), ("steady", .52), ("telegraph", .18))
for ci, (label, skill, panel_col, target) in enumerate(skill_cards):
    col_x = 28 + ci * 368
    dur = V.SKILL_VISUAL_DURATION[skill]
    for si, (stage, frac) in enumerate(stages):
        timer = max(1, int(dur * frac))
        y0 = 100 + si * 350
        panel = pygame.Rect(col_x, y0, 348, 330)
        pygame.draw.rect(skills_sheet, panel_col, panel, border_radius=12)
        pygame.draw.rect(skills_sheet, (93, 174, 222), panel, 2,
                         border_radius=12)
        skills_sheet.blit(font_small.render(f"{label}  {stage}  t={timer}",
                                            True, (236, 248, 255)),
                          (col_x + 14, y0 + 12))
        native = pygame.Surface((560, 560), pygame.SRCALPHA)
        h = _ProbeEntity("vex", 280, 330)
        h.pulse = 1.3
        h.direction = h.facing = 1
        h.active_skill = skill
        h.active_skill_timer = timer
        h.target = SimpleNamespace(x=280 + target[0], y=330 + target[1],
                                   alive=True)
        h._render_scale = 0.45
        V.draw_vex(native, h, 280, 330)
        scaled = pygame.transform.scale(native, (336, 336))
        old = skills_sheet.get_clip()
        skills_sheet.set_clip(panel.inflate(-6, -34))
        skills_sheet.blit(scaled, (col_x + 6, y0 + 30))
        skills_sheet.set_clip(old)
out4 = os.path.join(ROOT, "docs", "vex_v2_skills.png")
pygame.image.save(skills_sheet, out4)
print(out4)

print("SEMUA CEK LOLOS" if ok_all else "ADA CEK GAGAL")
sys.exit(0 if ok_all else 1)
