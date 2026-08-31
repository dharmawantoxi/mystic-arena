#!/usr/bin/env python3
"""Audit + preview sheet untuk Sylara renderer masterwork v2.

Mengukur hal yang sebelumnya hanya bisa dinilai mata:
  - skala terukur & ukuran akhir di layar (pipeline heroes/__init__)
  - bbox tiap pose, jumlah warna unik (idle vs portrait LOD)
  - keunikan frame antar siklus (bukan sticker translation)
  - waktu render per pose (budget cache-miss)
  - FX skill di luar siluet, radius telegraph px dunia
Menghasilkan:
  - docs/sylara_v2_review.png
  - docs/sylara_v2_anim_strip.png
  - docs/sylara_v2_ingame.png
  - docs/sylara_v2_skills.png
  - docs/sylara_v2_before_after.png
"""
import math
import os
import sys
import time
from types import SimpleNamespace as _NS

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from heroes import _ProbeEntity, render_hero, _get_hero_scale, clear_hero_sprite_cache
from heroes._bundle import _NS_sylara as S


def colors_of(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def elite_frame(action, phase, progress=0.0, facing=1, size=320, detail=False):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    ax = ay = size // 2
    S._draw_sylara_elite(s, ax, ay, facing, phase, action, progress,
                         detail=detail)
    return s


def check(cond, label, extra=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return cond


ok_all = True

# ── 1. skala & ukuran layar ──────────────────────────────────────
scale = _get_hero_scale("sylara")
body = elite_frame("idle", 1.25)
bb = body.get_bounding_rect(min_alpha=8)
ok_all &= check(bb.height >= 130 and bb.width >= 70,
                "bbox idle native", f"{bb.w}x{bb.h}")
screen_h = bb.height * scale
ok_all &= check(55 <= screen_h <= 95,
                "tinggi badan di layar (target ~72px)",
                f"{screen_h:.1f}px scale={scale:.3f}")
ok_all &= check(abs(S.RIG_SCALE - 1.52) < 1e-6, "RIG_SCALE 1.52",
                str(S.RIG_SCALE))

# ── 2. keunikan frame (bukan sticker) ────────────────────────────
walk_frames = {pygame.image.tobytes(elite_frame("walk", i * 0.785), "RGBA")
               for i in range(8)}
atk_frames = {pygame.image.tobytes(elite_frame("attack", 0, i / 9.0), "RGBA")
              for i in range(10)}
ok_all &= check(len(walk_frames) == 8, "walk: 8 frame unik", f"{len(walk_frames)}")
ok_all &= check(len(atk_frames) >= 9, "attack: pose unik 7-keyframe",
                f"{len(atk_frames)}/10")

# ── 3. portrait LOD lebih kaya ───────────────────────────────────
port = elite_frame("idle", .8, detail=True)
norm = elite_frame("idle", .8)
nc, pc = len(colors_of(norm)), len(colors_of(port))
ok_all &= check(pc >= nc, "portrait LOD tidak lebih miskin", f"{nc} -> {pc}")
ok_all &= check(nc >= 50, "idle native >= 50 warna", str(nc))

# ── 4. palet material sampai ke render final ─────────────────────
pal = S.PALETTE
got = colors_of(norm)
for key in ("gold_light", "gold_shine", "hair_shine", "hair_high",
            "leather_light", "leather_high", "eye_iris_light",
            "string_shine", "cloak_high", "leaf_gold", "cloth_high"):
    ok_all &= check(pal[key] in got, f"swatch {key}", str(pal[key]))

# ── 5. kaki menapak + mata terbaca ───────────────────────────────
rs = S.RIG_SCALE
cx = cy = 160
feet_row = norm.get_at((cx + int(9 * rs), cy + int(40 * rs)))
eye_here = any(norm.get_at((cx + dx, cy + dy)).a > 150
               for dx in range(4, 24) for dy in range(-80, -45))
ok_all &= check(feet_row.a > 150, "telapak depan menapak y=+61")
ok_all &= check(eye_here, "mata/hood ada di posisi kepala")

# ── 6. timing (budget cache-miss) ────────────────────────────────
def bench(fn, n=20):
    fn()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n * 1000

t_idle = bench(lambda: S._draw_sylara_elite(norm, 160, 160, 1, 1.1, "idle"))
t_walk = bench(lambda: S._draw_sylara_elite(norm, 160, 160, 1, 1.1, "walk"))
t_atk = bench(lambda: S._draw_sylara_elite(norm, 160, 160, 1, .5, "attack", .52))
t_full = bench(lambda: S.draw_sylara(norm, _ProbeEntity("sylara", 160, 160), 160, 160))
print(f"[i] render ms: idle={t_idle:.2f} walk={t_walk:.2f} "
      f"attack={t_atk:.2f} draw_sylara={t_full:.2f}")
ok_all &= check(t_idle < 8.0, "idle cache-miss < 8ms", f"{t_idle:.2f}")

# ── 7. skill FX: world-space, mewah, dan terukur ─────────────────
def _render_skill(skill, timer, fs=None, W=760):
    s = pygame.Surface((W, W), pygame.SRCALPHA)
    h = _ProbeEntity("sylara", W // 2, W // 2 + 40)
    h.pulse = 1.3
    h.active_skill = skill
    h.active_skill_timer = timer
    h.range = 220
    h.skill_range = 200 if skill == "q" else 70
    h.target = _NS(x=W // 2 + 140, y=W // 2, alive=True)
    if fs:
        h._render_scale = fs
    S.draw_sylara(s, h, W // 2, W // 2 + 40)
    return s

def _count(s, matcher, rmin=0, rmax=10**6, cx=None, cy=None):
    cx = s.get_width() // 2 if cx is None else cx
    cy = s.get_height() // 2 + 40 if cy is None else cy
    n = 0
    for y in range(0, s.get_height(), 2):
        for x in range(0, s.get_width(), 2):
            if rmin <= math.hypot(x - cx, y - cy) <= rmax:
                if matcher(s.get_at((x, y))):
                    n += 1
    return n

_wind = lambda c: c.a > 100 and c[1] > 110 and c[1] > c[0] and c[1] > c[2]

s = _render_skill("w", 90)
ok_all &= check(_count(s, _wind, 50, 95) > 40,
                "W: ring/daun di luar badan",
                str(_count(s, _wind, 50, 95)))
s = _render_skill("w", 90, fs=0.5)
ok_all &= check(_count(s, _wind, 95, 170) > 30,
                "W: efek world-space saat di-scale hero",
                str(_count(s, _wind, 95, 170)))

s = _render_skill("q", 90)
ok_all &= check(_count(s, _wind, 55, 180) > 50,
                "Q: fletching/pita angin di luar badan",
                str(_count(s, _wind, 55, 180)))

s = _render_skill("r", 30)
ok_all &= check(_count(s, _wind, 20, 90) > 30,
                "R: gale/daun di sekitar busur",
                str(_count(s, _wind, 20, 90)))

s = _render_skill("e", 80)
ok_all &= check(_count(s, _wind, 40, 220) > 25,
                "E: sulur/daun shackle menuju target",
                str(_count(s, _wind, 40, 220)))

# 3 tahap
for skill, dur in S.SKILL_VISUAL_DURATION.items():
    sigs = {pygame.image.tobytes(_render_skill(skill, t, W=520), "RGBA")
            for t in (dur - 4, int(dur * 0.55), 8)}
    ok_all &= check(len(sigs) == 3, f"{skill}: 3 tahap FX", str(len(sigs)))

ok_all &= check(S._fx_scale(_NS()) == 1.0, "_fx_scale tanpa scale = 1")
ok_all &= check(abs(S._fx_scale(_NS(_render_scale=0.4)) - 2.5) < 1e-6,
                "_fx_scale(0.40)=2.50")

for skill, t in (("w", 90), ("e", 80), ("r", 30), ("q", 90)):
    surf = pygame.Surface((760, 760), pygame.SRCALPHA)
    hero = _ProbeEntity("sylara", 380, 420)
    hero.pulse = 1.3
    hero.active_skill = skill
    hero.active_skill_timer = t
    hero.range = 220
    hero.target = _NS(x=520, y=400, alive=True)
    ms = bench(lambda: S.draw_sylara(surf, hero, 380, 420), 12)
    print(f"[i] skill {skill}: {ms:.2f} ms/frame (cache-miss)")

# ═══════════════════════ PREVIEW SHEETS ══════════════════════════
font_title = pygame.font.Font(None, 44)
font_label = pygame.font.Font(None, 30)
font_small = pygame.font.Font(None, 21)

W, H = 1400, 860
sheet = pygame.Surface((W, H))
sheet.fill((5, 12, 10))
sheet.blit(font_title.render("SYLARA v2 - PIXEL MASTERWORK (100% prosedural)",
                             True, (190, 240, 150)), (36, 22))
sheet.blit(font_small.render(
    "rig 1.52x native • ramp hue-shift • selout • tuft cape • "
    "foot solver • 7-keyframe bow IMPACT + smear",
    True, (150, 185, 140)), (38, 66))

cards = (
    ("IDLE / BREATHE", dict(action="idle", phase=1.25)),
    ("WALK / CONTACT", dict(action="walk", phase=2.4)),
    ("BOW DRAW (impact)", dict(action="attack", phase=1.0, progress=.52)),
    ("WINDRUN (skill W)", dict(action="windrun", phase=1.8)),
)
for i, (label, kw) in enumerate(cards):
    x = 28 + i * 340
    panel = pygame.Rect(x, 100, 322, 600)
    pygame.draw.rect(sheet, (16, 32, 20), panel, border_radius=12)
    pygame.draw.rect(sheet, (96, 156, 84), panel, 2, border_radius=12)
    sheet.blit(font_label.render(label, True, (226, 246, 220)), (x + 16, 116))
    native = pygame.Surface((300, 300), pygame.SRCALPHA)
    S._draw_sylara_elite(native, 150, 158, 1, kw.get("phase", 0),
                         kw["action"], kw.get("progress", 0.0))
    scaled = pygame.transform.scale(native, (300 * 2, 300 * 2))
    clip = panel.inflate(-10, -66)
    old = sheet.get_clip()
    sheet.set_clip(clip)
    sheet.blit(scaled, (x + 161 - 300, 150))
    sheet.set_clip(old)

notes = ("hood runcing • braid • quiver",
         "foot solver • cape tuft • gait",
         "recurve bow • IMPACT burst",
         "dash stance • wind streaks")
for j, text in enumerate(notes):
    sheet.blit(font_small.render(text, True, (140, 180, 130)),
               (44 + j * 340, 712))
out1 = os.path.join(ROOT, "docs", "sylara_v2_review.png")
pygame.image.save(sheet, out1)
print(out1)

SW, SH = 1400, 900
strip = pygame.Surface((SW, SH))
strip.fill((5, 12, 10))
strip.blit(font_title.render("SYLARA v2 - PROSEDURAL ANIMATION RIG", True,
                             (190, 240, 150)), (36, 22))
strip.blit(font_small.render(
    "setiap frame dihitung ulang dari sendi + fase + inersia cape/rambut",
    True, (150, 185, 140)), (38, 66))
rows = (("IDLE / BREATHE", 6, "idle"),
        ("WALK / CONTACT", 8, "walk"),
        ("ATTACK / RELEASE", 10, "attack"))
for row, (label, count, action) in enumerate(rows):
    top = 108 + row * 262
    strip.blit(font_label.render(label, True, (190, 240, 150)), (36, top + 66))
    pygame.draw.line(strip, (70, 120, 70), (35, top + 100),
                     (1364, top + 100), 1)
    for i in range(count):
        native = pygame.Surface((170, 190), pygame.SRCALPHA)
        phase = i / count * math.tau
        progress = i / max(1, count - 1)
        S._draw_sylara_elite(native, 85, 100, 1, phase, action, progress)
        frame = pygame.transform.scale(native, (170, 190))
        fx = 200 + i * 122
        strip.blit(frame, (fx, top))
out2 = os.path.join(ROOT, "docs", "sylara_v2_anim_strip.png")
pygame.image.save(strip, out2)
print(out2)

clear_hero_sprite_cache()
GW, GH = 1200, 420
game = pygame.Surface((GW, GH))
game.fill((18, 32, 22))
for gy in range(0, GH, 40):
    pygame.draw.line(game, (24, 42, 28), (0, gy), (GW, gy), 1)
pygame.draw.line(game, (48, 78, 52), (0, 330), (GW, 330), 3)
game.blit(font_title.render("UKURAN ASLI DI ARENA (pipeline cache hero + lighting + outline)",
                            True, (210, 240, 170)), (30, 18))
poses = (
    ("idle", 0, 0.0, None), ("walk", 1.9, 0.0, None),
    ("draw", 0, 0.42, None), ("impact", 0, 0.52, None),
    ("windrun", 1.25, 0.0, "w"),
)
xpos = 130
for i, (name, ph, prog, skill) in enumerate(poses):
    hero = _ProbeEntity("sylara", xpos, 300)
    hero.pulse = ph
    hero.team = "blue" if i % 2 == 0 else "red"
    hero.range = 220
    if prog:
        hero._sy_attack_active = True
        hero._sy_attack_progress = prog
        hero.timer = 1
        hero._sy_prev_timer = 0
    if skill:
        hero.active_skill = skill
        hero.active_skill_timer = 90
    render_hero("sylara", game, hero, xpos, 300)
    game.blit(font_small.render(name, True, (200, 220, 190)),
              (xpos - 40, 330))
    xpos += 210
out3 = os.path.join(ROOT, "docs", "sylara_v2_ingame.png")
pygame.image.save(game, out3)
print(out3)

KW, KH = 1500, 1160
skills_sheet = pygame.Surface((KW, KH))
skills_sheet.fill((5, 12, 10))
skills_sheet.blit(font_title.render(
    "SYLARA v2 - SKILL FX MEWAH (world-space, 100% prosedural)", True,
    (190, 240, 150)), (36, 22))
skills_sheet.blit(font_small.render(
    "Q Focus Fire • W Windrun • E Shackle Shot • R Powershot — "
    "3 tahap timer per skill", True, (150, 185, 140)), (38, 66))

skill_cards = (
    ("Q - FOCUS FIRE", "q", (12, 28, 16)),
    ("W - WINDRUN", "w", (10, 26, 22)),
    ("E - SHACKLE SHOT", "e", (14, 24, 14)),
    ("R - POWERSHOT", "r", (16, 30, 12)),
)
stages = ((int(S.SKILL_VISUAL_DURATION["q"] * 0.92), "awal"),
          (int(S.SKILL_VISUAL_DURATION["q"] * 0.50), "tengah"),
          (10, "puncak"))
# per-skill stage timers from visual duration
stage_map = {
    "q": ((170, "awal"), (90, "tengah"), (12, "puncak")),
    "w": ((170, "awal"), (90, "tengah"), (12, "puncak")),
    "e": ((140, "awal"), (75, "tengah"), (10, "puncak")),
    "r": ((55, "awal"), (30, "tengah"), (8, "puncak")),
}
for ci, (label, skill, panel_col) in enumerate(skill_cards):
    col_x = 28 + ci * 368
    for si, (timer, stage) in enumerate(stage_map[skill]):
        y0 = 100 + si * 350
        panel = pygame.Rect(col_x, y0, 348, 330)
        pygame.draw.rect(skills_sheet, panel_col, panel, border_radius=12)
        pygame.draw.rect(skills_sheet, (96, 156, 84), panel, 2,
                         border_radius=12)
        skills_sheet.blit(
            font_small.render(f"{label}  t={timer} ({stage})", True,
                              (226, 246, 220)), (col_x + 14, y0 + 12))
        native = pygame.Surface((560, 560), pygame.SRCALPHA)
        h = _ProbeEntity("sylara", 280, 330)
        h.pulse = 1.3
        h.active_skill = skill
        h.active_skill_timer = timer
        h.range = 220
        h.skill_range = 200 if skill == "q" else 70
        h.target = _NS(x=420, y=300, alive=True)
        h._render_scale = 0.45
        S.draw_sylara(native, h, 280, 330)
        scaled = pygame.transform.scale(native, (336, 336))
        old = skills_sheet.get_clip()
        skills_sheet.set_clip(panel.inflate(-6, -34))
        skills_sheet.blit(scaled, (col_x + 6, y0 + 30))
        skills_sheet.set_clip(old)
out4 = os.path.join(ROOT, "docs", "sylara_v2_skills.png")
pygame.image.save(skills_sheet, out4)
print(out4)

# before/after card: native idle vs in-game
ba = pygame.Surface((1100, 520))
ba.fill((5, 12, 10))
ba.blit(font_title.render("SYLARA v2 — NATIVE RIG vs ARENA", True,
                          (190, 240, 150)), (28, 18))
native = elite_frame("idle", 1.25, size=360)
ba.blit(pygame.transform.scale(native, (360, 360)), (40, 90))
ba.blit(font_label.render("native 1.52x", True, (226, 246, 220)), (120, 460))
clear_hero_sprite_cache()
arena = pygame.Surface((360, 360), pygame.SRCALPHA)
arena.fill((18, 32, 22))
h = _ProbeEntity("sylara", 180, 220)
h.pulse = 1.25
render_hero("sylara", arena, h, 180, 220)
ba.blit(arena, (480, 90))
ba.blit(font_label.render("arena (~72 px)", True, (226, 246, 220)), (560, 460))
ba.blit(font_small.render(
    f"bbox native {bb.w}x{bb.h}  •  scale {scale:.3f}  •  {nc} warna idle",
    True, (150, 185, 140)), (40, 490))
out5 = os.path.join(ROOT, "docs", "sylara_v2_before_after.png")
pygame.image.save(ba, out5)
print(out5)

print("SEMUA CEK LOLOS" if ok_all else "ADA CEK GAGAL")
sys.exit(0 if ok_all else 1)
