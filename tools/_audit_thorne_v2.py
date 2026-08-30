#!/usr/bin/env python3
"""Audit + preview sheet untuk Thorne renderer masterwork v2.

Mengukur hal yang sebelumnya hanya bisa dinilai mata:
  - skala terukur & ukuran akhir di layar (pipeline heroes/__init__)
  - bbox tiap pose, jumlah warna unik (idle vs portrait LOD)
  - keunikan frame antar siklus (bukan sticker translation)
  - waktu render per pose (budget cache-miss)
  - coverage kipas quill di atas punuk
Menghasilkan:
  - docs/thorne_v2_review.png      (kartu pose besar, 2x)
  - docs/thorne_v2_anim_strip.png  (film strip idle/walk/attack)
  - docs/thorne_v2_ingame.png      (ukuran asli di arena, tim biru/merah)
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

import heroes
from heroes import _ProbeEntity, render_hero, _get_hero_scale
from heroes._bundle import _NS_thorne as T

W_ARMOR = (216, 232, 250)


def colors_of(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def elite_frame(action, phase, progress=0.0, facing=1, warpath=False,
                size=300, anchor=None):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    ax = ay = size // 2 if anchor is None else anchor
    T._draw_thorne_elite(s, ax, ay, facing, phase, action, progress,
                         False, warpath)
    return s


def check(cond, label, extra=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return cond


ok_all = True

# ── 1. skala & ukuran layar ──────────────────────────────────────
scale = _get_hero_scale("thorne")
body = elite_frame("idle", 1.25)
bb = body.get_bounding_rect(min_alpha=8)
ok_all &= check(bb.height >= 100 and bb.width >= 75,
                "bbox idle native", f"{bb.w}x{bb.h}")
screen_h = bb.height * scale
ok_all &= check(60 <= screen_h <= 90,
                "tinggi badan di layar (target ~70px)",
                f"{screen_h:.1f}px scale={scale:.3f}")

# ── 2. keunikan frame (bukan sticker) ────────────────────────────
walk_frames = {pygame.image.tobytes(elite_frame("walk", i * 0.785), "RGBA")
               for i in range(8)}
atk_frames = {pygame.image.tobytes(elite_frame("attack", 0, i / 9.0), "RGBA")
              for i in range(10)}
ok_all &= check(len(walk_frames) == 8, "walk: 8 frame unik", f"{len(walk_frames)}")
# attack: 9 pose unik; frame pertama & terakhir sama = loop closure
ok_all &= check(len(atk_frames) == 9, "attack: pose unik (endpoint = loop)",
                f"{len(atk_frames)}/10")

# ── 3. portrait LOD lebih kaya ───────────────────────────────────
port = pygame.Surface((300, 300), pygame.SRCALPHA)
T._draw_thorne_elite(port, 150, 150, 1, .8, "idle", 0.0, True, False)
norm = elite_frame("idle", .8)
nc, pc = len(colors_of(norm)), len(colors_of(port))
ok_all &= check(pc > nc, "portrait LOD lebih banyak warna", f"{nc} -> {pc}")

# ── 4. palet material sampai ke render final ─────────────────────
pal = T.PALETTE
got = colors_of(norm)
for key in ("tusk_light", "belly_mid", "gold_light", "cloth_light",
            "quill_tip", "armor_shine", "eye_iris", "quill_root",
            "fur_rim", "tusk_mid"):
    ok_all &= check(pal[key] in got, f"swatch {key}", str(pal[key]))

# ── 5. coverage kipas quill di atas punuk ────────────────────────
# hitung px quill-warna (keluarga kuning/oranye/merah) di kuadran atas-kiri
quad = Counter()
for y in range(0, 150):
    for x in range(0, 150):
        c = norm.get_at((x, y))
        if c.a > 200:
            r, g, b = c[:3]
            if r > 130 and g > 60 and g < 230 and b < 140:
                quad["warm"] += 1
ok_all &= check(quad["warm"] > 250, "kipas quill ter-cover (px hangat atas-kiri)",
                str(quad["warm"]))

# ── 6. kaki menapak di dasar + mata terbaca ──────────────────────
feet_row = norm.get_at((150 + 18, 150 + 64))
eye_here = any(norm.get_at((150 + dx, 150 + dy)).a > 200
               for dx in range(9, 17) for dy in range(-44, -38))
ok_all &= check(feet_row.a > 150, "telapak depan menapak y=+64")
ok_all &= check(eye_here, "mata (socket) ada di posisi kepala")

# ── 7. timing (budget cache-miss) ────────────────────────────────
def bench(fn, n=30):
    fn()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n * 1000

t_idle = bench(lambda: T._draw_thorne_elite(norm, 150, 150, 1, 1.1, "idle"))
t_walk = bench(lambda: T._draw_thorne_elite(norm, 150, 150, 1, 1.1, "walk"))
t_atk = bench(lambda: T._draw_thorne_elite(norm, 150, 150, 1, .5, "attack", .5))
t_full = bench(lambda: T.draw_thorne(norm, _ProbeEntity("thorne", 150, 150), 150, 150))
print(f"[i] render ms: idle={t_idle:.2f} walk={t_walk:.2f} "
      f"attack={t_atk:.2f} draw_thorne={t_full:.2f}")

# ── 8. skill FX: world-space, mewah, dan terukur ─────────────────
from types import SimpleNamespace as _NS

def _render_skill(skill, timer, fs=None, W=760):
    s = pygame.Surface((W, W), pygame.SRCALPHA)
    h = _ProbeEntity("thorne", W // 2, W // 2 + 40)
    h.pulse = 1.3
    h.active_skill = skill
    h.active_skill_timer = timer
    h.target = _NS(x=W // 2 + 140, y=W // 2, alive=True)
    if fs:
        h._render_scale = fs
    T.draw_thorne(s, h, W // 2, W // 2 + 40)
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

_gold = lambda c: c.a > 100 and c[0] > 180 and c[1] > 140 and c[2] < 180
_rage = lambda c: c.a > 100 and c[0] > 130 and c[1] < 110 and c[2] < 90
_goo = lambda c: c.a > 100 and c[1] > 90 and c[0] < 120 and c[1] - c[2] > 25
_quill_fx = lambda c: c.a > 100 and c[0] > 170 and c[1] > 130 and c[2] < 190

# W: rune ring + duri harus keluar dari siluet badan, dan world-space
s = _render_skill("w", 60)
ok_all &= check(_count(s, _gold, 55, 100) > 60,
                "W: duri/rune emas di luar badan",
                str(_count(s, _gold, 55, 100)))
s = _render_skill("w", 60, fs=0.5)
ok_all &= check(_count(s, _gold, 110, 210) > 40,
                "W: efek world-space saat di-scale hero",
                str(_count(s, _gold, 110, 210)))

# R: retakan + api + bara di luar badan
s = _render_skill("r", 30)
ok_all &= check(_count(s, _rage, 55, 140) > 60,
                "R: magma/bara merah di luar badan",
                str(_count(s, _rage, 55, 140)))

# E: ring jangkauan tepat di 100 world-px dari pusat
s = _render_skill("e", 50, fs=0.5)
hits = 0
for a in range(0, 360, 2):
    x = int(380 + math.cos(math.radians(a)) * 198)
    y = int(420 + math.sin(math.radians(a)) * 198)
    if _quill_fx(s.get_at((x, y))):
        hits += 1
ok_all &= check(hits > 90, "E: ring jangkauan di ~200px canvas (=100 dunia)",
                f"{hits}/180")

# Q: jalur asam sampai target
s = _render_skill("q", 30)
ok_all &= check(_count(s, _goo, 70, 400) > 25,
                "Q: jalur/splat goo menuju target",
                str(_count(s, _goo, 70, 400)))

# timing skill (budget cache-miss)
for skill, t in (("w", 60), ("e", 35), ("r", 30), ("q", 20)):
    surf = pygame.Surface((760, 760), pygame.SRCALPHA)
    hero = _ProbeEntity("thorne", 380, 420)
    hero.pulse = 1.3
    hero.active_skill = skill
    hero.active_skill_timer = t
    hero.target = _NS(x=520, y=400, alive=True)
    ms = bench(lambda: T.draw_thorne(surf, hero, 380, 420), 20)
    print(f"[i] skill {skill}: {ms:.2f} ms/frame (cache-miss)")

# ═══════════════════════ PREVIEW SHEETS ══════════════════════════
font_title = pygame.font.Font(None, 44)
font_label = pygame.font.Font(None, 30)
font_small = pygame.font.Font(None, 21)

# ── review sheet ──
W, H = 1400, 860
sheet = pygame.Surface((W, H))
sheet.fill((6, 10, 20))
sheet.blit(font_title.render("THORNE v2 - PIXEL MASTERWORK (100% prosedural)",
                             True, (255, 205, 120)), (36, 22))
sheet.blit(font_small.render(
    "rig 1.5x native • ramp hue-shift • selout • tuft silhouette • "
    "quill inertia • foot solver • 7-keyframe attack + impact frame",
    True, (176, 158, 130)), (38, 66))

cards = (
    ("IDLE / BREATHE", dict(action="idle", phase=1.25)),
    ("WALK / CONTACT", dict(action="walk", phase=2.4)),
    ("CLUB SMASH (impact)", dict(action="attack", phase=1.0, progress=.54)),
    ("WARPATH (ultimate R)", dict(action="idle", phase=1.25, warpath=True)),
)
for i, (label, kw) in enumerate(cards):
    x = 28 + i * 340
    panel = pygame.Rect(x, 100, 322, 600)
    pygame.draw.rect(sheet, (30, 21, 10), panel, border_radius=12)
    pygame.draw.rect(sheet, (172, 122, 55), panel, 2, border_radius=12)
    sheet.blit(font_label.render(label, True, (255, 236, 218)), (x + 16, 116))
    native = pygame.Surface((300, 300), pygame.SRCALPHA)
    T._draw_thorne_elite(native, 150, 158, 1, kw.get("phase", 0),
                         kw["action"], kw.get("progress", 0.0),
                         False, kw.get("warpath", False))
    scaled = pygame.transform.scale(native, (300 * 2, 300 * 2))
    clip = panel.inflate(-10, -66)
    old = sheet.get_clip()
    sheet.set_clip(clip)
    sheet.blit(scaled, (x + 161 - 300, 150))
    sheet.set_clip(old)

notes = ("crest kipas 3 lapis • tusks • pauldron",
         "foot solver • debu tapak • quill lag",
         "smear sabit • bintang • serpihan batu",
         "palette rage • bara orbit • mata menyala")
for j, text in enumerate(notes):
    sheet.blit(font_small.render(text, True, (185, 151, 115)),
               (44 + j * 340, 712))
out1 = os.path.join(ROOT, "docs", "thorne_v2_review.png")
pygame.image.save(sheet, out1)
print(out1)

# ── animation strip ──
SW, SH = 1400, 900
strip = pygame.Surface((SW, SH))
strip.fill((6, 10, 20))
strip.blit(font_title.render("THORNE v2 - PROSEDURAL ANIMATION RIG", True,
                             (255, 205, 120)), (36, 22))
strip.blit(font_small.render(
    "setiap frame dihitung ulang dari sendi + fase + inersia quill",
    True, (176, 158, 130)), (38, 66))
rows = (("IDLE / BREATHE", 6, "idle"),
        ("WALK / CONTACT", 8, "walk"),
        ("ATTACK / SMASH", 10, "attack"))
for row, (label, count, action) in enumerate(rows):
    top = 108 + row * 262
    strip.blit(font_label.render(label, True, (255, 199, 130)), (36, top + 66))
    pygame.draw.line(strip, (145, 94, 42), (35, top + 100),
                     (1364, top + 100), 1)
    for i in range(count):
        native = pygame.Surface((170, 190), pygame.SRCALPHA)
        phase = i / count * math.tau
        progress = i / max(1, count - 1)
        T._draw_thorne_elite(native, 85, 100, 1, phase, action, progress)
        frame = pygame.transform.scale(native, (170, 190))
        fx = 200 + i * 122
        strip.blit(frame, (fx, top))
out2 = os.path.join(ROOT, "docs", "thorne_v2_anim_strip.png")
pygame.image.save(strip, out2)
print(out2)

# ── in-game size (ukuran sesungguhnya setelah pipeline hero) ──
GW, GH = 1200, 420
game = pygame.Surface((GW, GH))
game.fill((24, 34, 26))
for gy in range(0, GH, 40):                     # grid lane halus
    pygame.draw.line(game, (30, 42, 32), (0, gy), (GW, gy), 1)
pygame.draw.line(game, (56, 74, 52), (0, 330), (GW, 330), 3)  # lane line
game.blit(font_title.render("UKURAN ASLI DI ARENA (pipeline cache hero + lighting + outline)",
                            True, (255, 220, 150)), (30, 18))
poses = (
    ("idle", 0, 0.0, None), ("walk", 1.9, 0.0, None),
    ("attack", 0, 0.42, None), ("attack", 0, 0.54, None),
    ("warpath idle", 1.25, 0.0, "r"),
)
xpos = 130
for i, (name, ph, prog, skill) in enumerate(poses):
    hero = _ProbeEntity("thorne", xpos, 300)
    hero.pulse = ph
    hero.team = "blue" if i % 2 == 0 else "red"
    if prog:
        hero._th_attack_active = True
        hero._th_attack_progress = prog
        hero.timer = 1  # supaya jalur attacking aktif
        hero._th_prev_timer = 0
    if skill:
        hero.active_skill = skill
        hero.active_skill_timer = 60
    render_hero("thorne", game, hero, xpos, 300)
    game.blit(font_small.render(name, True, (210, 210, 190)),
              (xpos - 40, 330))
    xpos += 210
out3 = os.path.join(ROOT, "docs", "thorne_v2_ingame.png")
pygame.image.save(game, out3)
print(out3)

# ── skill FX sheet: 4 skill x 3 tahap timer ──
KW, KH = 1500, 1160
skills_sheet = pygame.Surface((KW, KH))
skills_sheet.fill((6, 10, 20))
skills_sheet.blit(font_title.render(
    "THORNE v2 - SKILL FX MEWAH (world-space, 100% prosedural)", True,
    (255, 205, 120)), (36, 22))
skills_sheet.blit(font_small.render(
    "Q Viscous Nose • W Bristleback • E Quill Spray • R Warpath — "
    "3 tahap timer per skill", True, (176, 158, 130)), (38, 66))

skill_cards = (
    ("Q - VISCOUS NOSE", "q", (36, 20, 8)),
    ("W - BRISTLEBACK", "w", (26, 22, 8)),
    ("E - QUILL SPRAY", "e", (28, 26, 10)),
    ("R - WARPATH (ULTIMATE)", "r", (30, 12, 10)),
)
stages = ((90, "awal"), (50, "tengah"), (12, "puncak"))
for ci, (label, skill, panel_col) in enumerate(skill_cards):
    col_x = 28 + ci * 368
    for si, (timer, stage) in enumerate(stages):
        y0 = 100 + si * 350
        panel = pygame.Rect(col_x, y0, 348, 330)
        pygame.draw.rect(skills_sheet, panel_col, panel, border_radius=12)
        pygame.draw.rect(skills_sheet, (172, 122, 55), panel, 2,
                         border_radius=12)
        skills_sheet.blit(
            font_small.render(f"{label}  t={timer} ({stage})", True,
                              (255, 236, 218)), (col_x + 14, y0 + 12))
        native = pygame.Surface((560, 560), pygame.SRCALPHA)
        h = _ProbeEntity("thorne", 280, 330)
        h.pulse = 1.3
        h.active_skill = skill
        h.active_skill_timer = timer
        h.target = _NS(x=420, y=300, alive=True)
        h._render_scale = 0.45      # simulasi pipeline hero: fs aktif
        T.draw_thorne(native, h, 280, 330)
        scaled = pygame.transform.scale(native, (336, 336))
        old = skills_sheet.get_clip()
        skills_sheet.set_clip(panel.inflate(-6, -34))
        skills_sheet.blit(scaled, (col_x + 6, y0 + 30))
        skills_sheet.set_clip(old)
out4 = os.path.join(ROOT, "docs", "thorne_v2_skills.png")
pygame.image.save(skills_sheet, out4)
print(out4)

print("SEMUA CEK LOLOS" if ok_all else "ADA CEK GAGAL")
sys.exit(0 if ok_all else 1)
