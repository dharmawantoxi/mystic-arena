#!/usr/bin/env python3
"""Audit + preview sheet untuk RAZAK renderer masterwork v2.

Mengukur hal yang sebelumnya hanya bisa dinilai mata:
  - skala terukur & ukuran akhir di layar (pipeline heroes/__init__)
  - bbox tiap pose, jumlah warna unik (idle vs portrait LOD)
  - keunikan frame antar siklus (bukan sticker translation)
  - waktu render per pose (budget cache-miss)
  - coverage api / wing membrane
  - world-space skill FX outside body
Menghasilkan:
  - docs/razak_v2_review.png
  - docs/razak_v2_anim_strip.png
  - docs/razak_v2_ingame.png
  - docs/razak_v2_skills.png
"""
import math
import os
import sys
import time
from collections import Counter

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from bosses.level2 import _NS_razak as R
from heroes import _ProbeEntity, render_hero, _get_hero_scale

# Need to register boss renderer manually for render_hero test? Use _ProbeEntity with boss_type razak via BOSS_RENDERERS
# But we will also test elite directly

def colors_of(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}

def elite_frame(action, phase, progress=0.0, facing=1, skill=None, size=300, detail=False):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    ax = ay = size // 2
    R._draw_razak_elite(s, ax, ay, facing, phase, action, progress, detail=detail, active_skill=skill)
    return s

def check(cond, label, extra=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return cond

ok_all = True

# ── 1. skala & ukuran layar ──────────────────────────────────────
# For boss, _get_hero_scale uses BOSS_RENDERERS; razak is boss type
scale = _get_hero_scale("razak")
body = elite_frame("idle", 1.25)
bb = body.get_bounding_rect(min_alpha=8)
ok_all &= check(bb.height >= 100 and bb.width >= 75,
                "bbox idle native", f"{bb.w}x{bb.h}")
screen_h = bb.height * scale
ok_all &= check(60 <= screen_h <= 110,
                "tinggi badan di layar (target ~70px)", f"{screen_h:.1f}px scale={scale:.3f}")

# ── 2. keunikan frame (bukan sticker) ────────────────────────────
walk_frames = {pygame.image.tobytes(elite_frame("walk", i * 0.785), "RGBA") for i in range(8)}
atk_frames = {pygame.image.tobytes(elite_frame("attack", 0, i / 9.0), "RGBA") for i in range(10)}
ok_all &= check(len(walk_frames) == 8, "walk: 8 frame unik", f"{len(walk_frames)}")
ok_all &= check(len(atk_frames) == 9, "attack: pose unik (endpoint = loop)", f"{len(atk_frames)}/10")

# ── 3. portrait LOD lebih kaya ───────────────────────────────────
port = elite_frame("idle", 0.8, detail=True, size=320)
norm = elite_frame("idle", 0.8, size=320)
nc, pc = len(colors_of(norm)), len(colors_of(port))
ok_all &= check(pc > nc, "portrait LOD lebih banyak warna", f"{nc} -> {pc}")

# ── 4. palet material sampai ke render final ─────────────────────
pal = R.PALETTE
got = colors_of(norm)
for key in ("bat_mid", "bat_light", "gob_mid", "fire_mid", "fire_bright", "brass_light", "metal_mid", "bone_light", "blue_mid", "wing_mid"):
    ok_all &= check(pal[key] in got, f"swatch {key}", str(pal[key]))

# ── 5. coverage api di sekitar badan ────────────────────────
quad = Counter()
for y in range(0, 160):
    for x in range(0, 320):
        c = norm.get_at((x, y))
        if c.a > 200:
            r, g, b = c[:3]
            if r > 150 and g > 60 and g < 200 and b < 100:
                quad["warm"] += 1
ok_all &= check(quad["warm"] > 200, "api ter-cover (px hangat)", str(quad["warm"]))

# ── 6. mata terbaca ──────────────────────
eye_here = any(norm.get_at((160 + dx, 160 + dy)).a > 150 for dx in range(18, 30) for dy in range(-8, 2))
ok_all &= check(eye_here, "mata bat ada di posisi kepala")

# ── 7. timing (budget cache-miss) ────────────────────────────────
def bench(fn, n=30):
    fn()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n * 1000

t_idle = bench(lambda: R._draw_razak_elite(pygame.Surface((320,320), pygame.SRCALPHA), 160, 160, 1, 1.1, "idle"))
t_walk = bench(lambda: R._draw_razak_elite(pygame.Surface((320,320), pygame.SRCALPHA), 160, 160, 1, 1.1, "walk"))
t_atk = bench(lambda: R._draw_razak_elite(pygame.Surface((320,320), pygame.SRCALPHA), 160, 160, 1, .5, "attack", .5))
# full draw via draw_razak
def full_draw():
    s = pygame.Surface((400,400), pygame.SRCALPHA)
    b = _ProbeEntity("razak", 200, 200)
    b.pulse=1.1
    b.direction=1
    b.timer=0
    b.attack_cooldown=45
    b.active_skill=None
    b.active_skill_timer=0
    b._render_scale=1.0
    b.x=0; b.y=0
    R.draw_razak(s, b, 200, 200)
t_full = bench(full_draw)
print(f"[i] render ms: idle={t_idle:.2f} walk={t_walk:.2f} attack={t_atk:.2f} draw_razak={t_full:.2f}")

# ── 8. skill FX: world-space, mewah, dan terukur ─────────────────
from types import SimpleNamespace as _NS

def _render_skill(skill, timer, fs=None, W=760):
    s = pygame.Surface((W, W), pygame.SRCALPHA)
    h = _ProbeEntity("razak", W // 2, W // 2 + 40)
    h.pulse = 1.3
    h.active_skill = skill
    h.active_skill_timer = timer
    # target close enough to avoid _world_to_local clamping (max_off ~150)
    # world offset 70 => canvas offset 70/scale
    h.target = _NS(x=70, y=10, alive=True)
    h.x = 0
    h.y = 0
    if fs:
        h._render_scale = fs
    else:
        h._render_scale = 1.0
    h.direction=1
    R.draw_razak(s, h, W // 2, W // 2 + 40)
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

_fire = lambda c: c.a > 80 and c[0] > 100 and c[1] < 180 and c[2] < 100 and c[0] > c[2]
_fire_bright = lambda c: c.a > 80 and c[0] > 180 and c[1] > 60 and c[2] < 100

# Q: napalm ring outside body
s = _render_skill("q", 20)
cnt = _count(s, _fire, 55, 130)
ok_all &= check(cnt > 60, "Q: api napalm di luar badan", str(cnt))
s = _render_skill("q", 20, fs=0.5)
cnt2 = _count(s, _fire, 110, 210)
ok_all &= check(cnt2 > 40, "Q: efek world-space saat di-scale hero", str(cnt2))

# W: flamebreak cone outside
s = _render_skill("w", 30)
cnt = _count(s, _fire, 55, 140)
ok_all &= check(cnt > 60, "W: flame cone di luar badan", str(cnt))

# R: firestorm 180 world px
s = _render_skill("r", 40)
cnt = _count(s, _fire, 55, 200)
ok_all &= check(cnt > 60, "R: firestorm di luar badan", str(cnt))

# R: ring jangkauan tepat di 180 world-px dari pusat -> 180/fs canvas
s = _render_skill("r", 40, fs=1.0)
hits=0
cx=380; gy=420+52
rng=180
for a in range(0,360,3):
    # check with tolerance +-4
    found=False
    for dr in (-4,-2,0,2,4):
        x = int(cx + math.cos(math.radians(a))*(rng+dr))
        y = int(gy + math.sin(math.radians(a))*(rng+dr)*0.35)
        if 0 <= x < s.get_width() and 0 <= y < s.get_height():
            c = s.get_at((x,y))
            if _fire(c) or _fire_bright(c):
                found=True
                break
    if found:
        hits+=1
ok_all &= check(hits > 35, "R: ring jangkauan di ~180px canvas (=180 dunia)", f"{hits}/120")

# Q radius 75 world px at target (target world 70,10 => canvas 450,390 with fs=1)
s = _render_skill("q", 20, fs=1.0)
# compute actual target canvas pos via _world_to_local logic: boss at 0, target 70 => offset 70
# canvas center 380,420, so target canvas = 380+70=450, 420+10=430? but we use W//2=380, W//2+40=420 as base
# So tx = 380+70=450, ty=420+10=430, gy=ty+12=442
tx=450
ty=430+12
rng=75
hits=0
for a in range(0,360,4):
    found=False
    for dr in (-4,-2,0,2,4):
        x = int(tx + math.cos(math.radians(a))*(rng+dr))
        y = int(ty + math.sin(math.radians(a))*(rng+dr)*0.35)
        if 0 <= x < s.get_width() and 0 <= y < s.get_height():
            c = s.get_at((x,y))
            if _fire(c) or _fire_bright(c):
                found=True
                break
    if found:
        hits+=1
ok_all &= check(hits > 20, "Q: ring jangkauan di ~75px world", f"{hits}/90")

# timing skill (budget cache-miss)
for skill, t in (("q", 20), ("w", 30), ("e", 20), ("r", 40)):
    surf = pygame.Surface((760, 760), pygame.SRCALPHA)
    hero = _ProbeEntity("razak", 380, 420)
    hero.pulse = 1.3
    hero.active_skill = skill
    hero.active_skill_timer = t
    hero.target = _NS(x=70, y=10, alive=True)
    hero.x=0; hero.y=0
    hero._render_scale=1.0
    hero.direction=1
    hero.timer=0
    hero.attack_cooldown=45
    ms = bench(lambda: R.draw_razak(surf, hero, 380, 420), 20)
    print(f"[i] skill {skill}: {ms:.2f} ms/frame (cache-miss) budget 3.5ms")
    ok_all &= check(ms < 6.0, f"skill {skill} budget", f"{ms:.2f}ms")

# ═══════════════════════ PREVIEW SHEETS ══════════════════════════
font_title = pygame.font.Font(None, 44)
font_label = pygame.font.Font(None, 30)
font_small = pygame.font.Font(None, 21)

# ── review sheet ──
W, H = 1400, 860
sheet = pygame.Surface((W, H))
sheet.fill((6, 10, 20))
sheet.blit(font_title.render("RAZAK v2 - PIXEL MASTERWORK (Batrider Fire Goblin)", True, (255, 205, 120)), (36, 22))
sheet.blit(font_small.render("rig 1.55x native • ramp hue-shift • selout • tuft jagged wing • inertia • 7-keyframe attack + IMPACT + fire aura", True, (176, 158, 130)), (38, 66))

cards = (
    ("IDLE / HOVER", dict(action="idle", phase=1.25)),
    ("WALK / FLAP", dict(action="walk", phase=2.4)),
    ("MACHETE SMASH (impact)", dict(action="attack", phase=1.0, progress=.54)),
    ("FIRESTORM (ultimate R)", dict(action="idle", phase=1.25, skill="r")),
)
for i, (label, kw) in enumerate(cards):
    x = 28 + i * 340
    panel = pygame.Rect(x, 100, 322, 600)
    pygame.draw.rect(sheet, (30, 21, 10), panel, border_radius=12)
    pygame.draw.rect(sheet, (172, 122, 55), panel, 2, border_radius=12)
    sheet.blit(font_label.render(label, True, (255, 236, 218)), (x + 16, 116))
    native = pygame.Surface((300, 300), pygame.SRCALPHA)
    R._draw_razak_elite(native, 150, 158, 1, kw.get("phase", 0), kw["action"], kw.get("progress", 0.0), False, kw.get("skill", None))
    scaled = pygame.transform.scale(native, (300 * 2, 300 * 2))
    clip = panel.inflate(-10, -66)
    old = sheet.get_clip()
    sheet.set_clip(clip)
    sheet.blit(scaled, (x + 161 - 300, 150))
    sheet.set_clip(old)

notes = ("bat wings tuft • goblin goggles • fuel tanks",
         "flap inertia • sway • ember orbit",
         "smear fire • spark star • shockwave",
         "6 pillars • rune ring • cracks • glow")
for j, text in enumerate(notes):
    sheet.blit(font_small.render(text, True, (185, 151, 115)), (44 + j * 340, 712))
out1 = os.path.join(ROOT, "docs", "razak_v2_review.png")
pygame.image.save(sheet, out1)
print(out1)

# ── animation strip ──
SW, SH = 1400, 900
strip = pygame.Surface((SW, SH))
strip.fill((6, 10, 20))
strip.blit(font_title.render("RAZAK v2 - PROSEDURAL ANIMATION RIG", True, (255, 205, 120)), (36, 22))
strip.blit(font_small.render("setiap frame dihitung ulang dari sendi + fase + inersia wing + napalm trail", True, (176, 158, 130)), (38, 66))
rows = (("IDLE / HOVER", 6, "idle"), ("WALK / FLAP", 8, "walk"), ("ATTACK / SMASH", 10, "attack"))
for row, (label, count, action) in enumerate(rows):
    top = 108 + row * 262
    strip.blit(font_label.render(label, True, (255, 199, 130)), (36, top + 66))
    pygame.draw.line(strip, (145, 94, 42), (35, top + 100), (1364, top + 100), 1)
    for i in range(count):
        native = pygame.Surface((200, 210), pygame.SRCALPHA)
        phase = i / count * math.tau
        progress = i / max(1, count - 1)
        R._draw_razak_elite(native, 100, 110, 1, phase, action, progress)
        frame = pygame.transform.scale(native, (200, 210))
        fx = 200 + i * 122
        strip.blit(frame, (fx, top))
out2 = os.path.join(ROOT, "docs", "razak_v2_anim_strip.png")
pygame.image.save(strip, out2)
print(out2)

# ── in-game size ──
GW, GH = 1200, 420
game = pygame.Surface((GW, GH))
game.fill((24, 34, 26))
for gy in range(0, GH, 40):
    pygame.draw.line(game, (30, 42, 32), (0, gy), (GW, gy), 1)
pygame.draw.line(game, (56, 74, 52), (0, 330), (GW, 330), 3)
game.blit(font_title.render("UKURAN ASLI DI ARENA (pipeline cache hero + lighting + outline)", True, (255, 220, 150)), (30, 18))
poses = (("idle", 0, 0.0, None), ("walk", 1.9, 0.0, None), ("attack", 0, 0.42, None), ("attack", 0, 0.54, None), ("firestorm idle", 1.25, 0.0, "r"))
xpos = 130
for i, (name, ph, prog, skill) in enumerate(poses):
    hero = _ProbeEntity("razak", xpos, 300)
    hero.pulse = ph
    hero.team = "blue" if i % 2 == 0 else "red"
    hero.direction=1
    hero.x=0; hero.y=0
    hero._render_scale = _get_hero_scale("razak")
    if prog:
        hero._razak_attack_active = True
        hero._razak_attack_progress = prog
        hero.timer = 1
        hero._razak_prev_timer = 0
        hero.attack_cooldown=45
    if skill:
        hero.active_skill = skill
        hero.active_skill_timer = 60
    # Use boss renderer directly via R.draw_razak but with hero scale pipeline?
    # For ingame sheet, use render_hero which uses cache + lighting
    from heroes import render_hero as rh
    rh("razak", game, hero, xpos, 300)
    game.blit(font_small.render(name, True, (210, 210, 190)), (xpos - 40, 330))
    xpos += 210
out3 = os.path.join(ROOT, "docs", "razak_v2_ingame.png")
pygame.image.save(game, out3)
print(out3)

# ── skill FX sheet: 4 skill x 3 tahap timer ──
KW, KH = 1500, 1160
skills_sheet = pygame.Surface((KW, KH))
skills_sheet.fill((6, 10, 20))
skills_sheet.blit(font_title.render("RAZAK v2 - SKILL FX MEWAH (world-space, 100% prosedural)", True, (255, 205, 120)), (36, 22))
skills_sheet.blit(font_small.render("Q Sticky Napalm (75) • W Flamebreak (95) • E Firefly Dash • R Firestorm (180) — 3 tahap timer per skill", True, (176, 158, 130)), (38, 66))

skill_cards = (
    ("Q - STICKY NAPALM", "q", (36, 20, 8)),
    ("W - FLAMEBREAK", "w", (26, 22, 8)),
    ("E - FIREFLY DASH", "e", (28, 26, 10)),
    ("R - FIRESTORM (ULTIMATE)", "r", (30, 12, 10)),
)
stages = ((90, "awal"), (50, "tengah"), (12, "puncak"))
for ci, (label, skill, panel_col) in enumerate(skill_cards):
    col_x = 28 + ci * 368
    for si, (timer, stage) in enumerate(stages):
        y0 = 100 + si * 350
        panel = pygame.Rect(col_x, y0, 348, 330)
        pygame.draw.rect(skills_sheet, panel_col, panel, border_radius=12)
        pygame.draw.rect(skills_sheet, (172, 122, 55), panel, 2, border_radius=12)
        skills_sheet.blit(font_small.render(f"{label}  t={timer} ({stage})", True, (255, 236, 218)), (col_x + 14, y0 + 12))
        native = pygame.Surface((560, 560), pygame.SRCALPHA)
        h = _ProbeEntity("razak", 280, 330)
        h.pulse = 1.3
        h.active_skill = skill
        h.active_skill_timer = timer if timer <= R.SKILL_VISUAL_DURATION.get(skill, 40) else R.SKILL_VISUAL_DURATION.get(skill, 40)
        h.target = _NS(x=420, y=300, alive=True)
        h.x=0; h.y=0
        h._render_scale = 0.45
        h.direction=1
        h.timer=0
        h.attack_cooldown=45
        R.draw_razak(native, h, 280, 330)
        scaled = pygame.transform.scale(native, (336, 336))
        old = skills_sheet.get_clip()
        skills_sheet.set_clip(panel.inflate(-6, -34))
        skills_sheet.blit(scaled, (col_x + 6, y0 + 30))
        skills_sheet.set_clip(old)
out4 = os.path.join(ROOT, "docs", "razak_v2_skills.png")
pygame.image.save(skills_sheet, out4)
print(out4)

print("SEMUA CEK LOLOS" if ok_all else "ADA CEK GAGAL")
sys.exit(0 if ok_all else 1)
