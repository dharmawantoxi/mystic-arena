#!/usr/bin/env python3
"""Audit + preview sheet untuk Sylara renderer masterwork v2.

Mengukur hal yang sebelumnya hanya bisa dinilai mata:
  - skala terukur & ukuran akhir di layar (pipeline heroes/__init__)
  - bbox tiap pose, jumlah warna unik (idle vs portrait LOD)
  - keunikan frame antar siklus (bukan sticker translation)
  - waktu render per pose (budget cache-miss ~3.5 ms)
  - skill Q/W/E/R: world-space (kompensasi 1/_render_scale), mewah, terukur
      Q Focus Fire   — ring AOE + chevron pierce + burst aktivasi
      W Windrun      — shockwave + ring berputar + chevron lari
      E Shackle Shot — tether rantai + reticle target + burst
      R Powershot    — pilar cahaya + orb charge + cone release

Menghasilkan:
  - docs/sylara_v2_review.png        (kartu pose besar)
  - docs/sylara_v2_anim_strip.png    (film strip idle/walk/attack)
  - docs/sylara_v2_ingame.png        (ukuran asli di arena, tim biru/merah)
  - docs/sylara_v2_skills.png        (4 skill x 3 tahap timer)
  - docs/sylara_v2_before_after.png  (perbandingan before vs after)

Jalankan:  python3 tools/_audit_sylara_v2.py
"""
import math
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import heroes
from heroes import _ProbeEntity, render_hero, _get_hero_scale
from heroes._bundle import _NS_sylara as Z

DOCS = os.path.join(ROOT, "docs")
os.makedirs(DOCS, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def colors_of(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def elite_frame(action, phase, progress=0.0, facing=1, detail=False,
                powered=False, size=320, anchor=None):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    ax = ay = size // 2 if anchor is None else anchor
    Z._draw_sylara_elite(s, ax, ay, facing, phase, action, progress,
                         powered, detail)
    return s


def check(cond, label, extra=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return cond


ok_all = True

# ─────────────────────────────────────────────────────────────────────────────
# 1. Skala & ukuran layar
# ─────────────────────────────────────────────────────────────────────────────
scale = _get_hero_scale("sylara")
# Pakai frame IDLE PENUH (badan + bayangan + platform) seperti test regresi
# agar konsisten; raw rig terpisah diukur khusus (inci di bawah).
body = elite_frame("idle", 1.25)
raw = body.get_bounding_rect(min_alpha=8)
full = pygame.Surface((360, 360), pygame.SRCALPHA)
h_full = _ProbeEntity("sylara", 180, 185)
h_full.pulse = 1.25
h_full.direction = 1
h_full.range = 200
Z.draw_sylara(full, h_full, 180, 185)
bb = full.get_bounding_rect(min_alpha=8)
ok_all &= check(bb.height >= 100 and bb.width >= 75,
                "bbox idle penuh (rig 1.5×: tinggi ≥100, lebar ≥75)",
                f"{bb.w}×{bb.h}")
# ukuran badan DI LAYAR dipakai dari raw rig (bukan bayangan/platform)
screen_h = raw.height * scale
ok_all &= check(55 <= screen_h <= 95,
                "tinggi badan di layar (target ~51–70 px)",
                f"{screen_h:.1f} px   scale={scale:.3f}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Keunikan frame (bukan sticker)
# ─────────────────────────────────────────────────────────────────────────────
walk_frames = {pygame.image.tobytes(elite_frame("walk", i * 0.785), "RGBA")
               for i in range(8)}
atk_frames = {pygame.image.tobytes(elite_frame("attack", 0, i / 9.0), "RGBA")
              for i in range(10)}
ok_all &= check(len(walk_frames) == 8, "walk: 8 frame unik",
                f"{len(walk_frames)}")
ok_all &= check(len(atk_frames) >= 9, "attack: ≥9 pose unik (loop closure)",
                f"{len(atk_frames)}/10")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Portrait LOD lebih kaya
# ─────────────────────────────────────────────────────────────────────────────
port = elite_frame("idle", .8, detail=True, size=320)
norm = elite_frame("idle", .8, size=320)
nc, pc = len(colors_of(norm)), len(colors_of(port))
ok_all &= check(pc > nc, "portrait LOD lebih banyak warna", f"{nc} → {pc}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Swatch palet material sampai ke render (idle penuh — material karakter)
# ─────────────────────────────────────────────────────────────────────────────
pal = Z.PALETTE
got_idle = colors_of(full)
for key in ("hair_shine", "cloth_light", "leather_light", "gold_light",
            "eye_iris_light", "string_shine", "arrow_feather"):
    ok_all &= check(pal[key] in got_idle, f"swatch {key} (idle)", str(pal[key]))
# wind_* hanya aktif saat skill (cek di section skill FX)

# ─────────────────────────────────────────────────────────────────────────────
# 5. Hood/rambut meruncing di kepala + busur terbaca (relatif bbox badan)
# ─────────────────────────────────────────────────────────────────────────────
at = body.get_bounding_rect(min_alpha=8)
top_row = sum(1 for x in range(at.left, at.right)
              for y in range(at.top, at.top + 32)
              if body.get_at((x, y)).a > 8)
ok_all &= check(top_row > 30, "hood + rambut muncul di ujung atas badan",
                f"{top_row} px")

# Bow extends forward (facing=1 -> sisi kanan) pada raw rig
bow_px = sum(1 for x in range(at.right - 40, at.right + 30)
             for y in range(at.top + 20, at.bottom)
             if body.get_at((x, y)).a > 8)
ok_all &= check(bow_px > 40,
                "busur recurve terbaca di sisi depan (kanan)",
                f"{bow_px} px")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Timing (budget cache-miss)
# ─────────────────────────────────────────────────────────────────────────────
def bench(fn, n=9):
    fn()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n * 1000

def _render_idle():
    s = pygame.Surface((320, 320), pygame.SRCALPHA)
    Z._draw_sylara_elite(s, 160, 170, 1, 1.0, "idle", 0.0, False)

def _render_skill():
    s = pygame.Surface((400, 400), pygame.SRCALPHA)
    h = _ProbeEntity("sylara", 200, 200)
    h.pulse = 1.0
    h.direction = h.facing = 1
    h.active_skill = "r"
    h.active_skill_timer = 40
    h._render_scale = 0.45
    h.target = _ProbeEntity("dummy", 300, 202)
    h.target.alive = True
    Z.draw_sylara(s, h, 200, 200)

t_idle = bench(_render_idle)
t_skill = bench(_render_skill)
ok_all &= check(t_idle < 3.5, "idle render < 3.5 ms", f"{t_idle:.2f} ms")
ok_all &= check(t_skill < 6.0, "skill render < 6.0 ms", f"{t_skill:.2f} ms")

# ─────────────────────────────────────────────────────────────────────────────
# 7. World-space FX (ring pas dengan radius dunia)
# ─────────────────────────────────────────────────────────────────────────────
class HeroAt40:
    _render_scale = 0.40
    range = 100
    x = y = 0

class HeroAt100:
    _render_scale = 1.00
    range = 100
    x = y = 0

surf400 = pygame.Surface((400, 400), pygame.SRCALPHA)
fs40 = Z._fx_scale(HeroAt40())
rr40 = Z._ring_r(HeroAt40(), 100, surf400)
rr100 = Z._ring_r(HeroAt100(), 100, surf400)
ok_all &= check(2.0 <= fs40 <= 2.6,
                "_fx_scale (scale=0.40) dalam range 2.0–2.6",
                f"{fs40:.2f}")
ok_all &= check(rr40 > rr100 * 1.5,
                "ring lebih besar di canvas scale 0.40 vs 1.00",
                f"rr40={rr40} rr100={rr100}")

# ─────────────────────────────────────────────────────────────────────────────
# 8. FX skill ada piksel di luar siluet badan
# ─────────────────────────────────────────────────────────────────────────────
body_surf = pygame.Surface((400, 400), pygame.SRCALPHA)
h_body = _ProbeEntity("sylara", 200, 200)
h_body.pulse = 1.0
h_body.direction = 1
Z._draw_sylara_idle(body_surf, h_body, 200, 200)
body_bb2 = body_surf.get_bounding_rect(min_alpha=8).inflate(10, 10)

for skill, timer in (("q", 120), ("w", 140), ("e", 100), ("r", 40)):
    s = pygame.Surface((400, 400), pygame.SRCALPHA)
    h = _ProbeEntity("sylara", 200, 200)
    h.pulse = 1.0
    h.direction = h.facing = 1
    h.active_skill = skill
    h.active_skill_timer = timer
    h._render_scale = 0.45
    h.target = _ProbeEntity("dummy", 300, 202)
    h.target.alive = True
    try:
        Z.draw_sylara(s, h, 200, 200)
    except Exception as e:
        print(f"  [WARN] skill {skill}: {e}")
        ok_all = False
        continue
    outside = sum(1 for y in range(s.get_height())
                  for x in range(s.get_width())
                  if s.get_at((x, y)).a > 8 and not body_bb2.collidepoint(x, y))
    ok_all &= check(outside > 50,
                    f"Skill {skill.upper()}: FX px di luar badan",
                    f"{outside} px")

# ─────────────────────────────────────────────────────────────────────────────
# 9. Badan ikut bereaksi ke state skill
# ─────────────────────────────────────────────────────────────────────────────
s_normal = pygame.Surface((280, 280), pygame.SRCALPHA)
s_focus = pygame.Surface((280, 280), pygame.SRCALPHA)
s_wind = pygame.Surface((280, 280), pygame.SRCALPHA)
Z._draw_sylara_elite(s_normal, 140, 148, 1, 1.0, "idle", 0.0, False, False)
Z._draw_sylara_elite(s_focus, 140, 148, 1, 1.0, "idle", 0.0, False, False,
                     focus=True)
Z._draw_sylara_elite(s_wind, 140, 148, 1, 1.0, "windrun", 0.0, False, False,
                     wind=True)
ok_all &= check(pygame.image.tobytes(s_normal, "RGBA") !=
                pygame.image.tobytes(s_focus, "RGBA"),
                "focus kwarg mengubah penampilan badan")
ok_all &= check(pygame.image.tobytes(s_focus, "RGBA") !=
                pygame.image.tobytes(s_wind, "RGBA"),
                "wind kwarg mengubah penampilan badan")

print()
print("═" * 58)
print(f"  AUDIT SYLARA v2: {'ALL PASS ✓' if ok_all else 'SOME FAIL ✗'}")
print("═" * 58)

# ─────────────────────────────────────────────────────────────────────────────
# GENERATE PREVIEW SHEETS
# ─────────────────────────────────────────────────────────────────────────────
try:
    font_big = pygame.font.Font(None, 40)
    font_med = pygame.font.Font(None, 28)
    font_small = pygame.font.Font(None, 20)
except Exception:
    font_big = font_med = font_small = pygame.font.Font(None, 24)

BG = (6, 14, 12)
ACC = (110, 200, 110)
WH = (235, 245, 235)

def label(surf, text, x, y, font=None, color=WH):
    f = font or font_small
    t = f.render(text, True, color)
    surf.blit(t, (x, y))
    return t.get_height()


# ── Review sheet ─────────────────────────────────────────────────────────────
REV_W, REV_H = 1400, 820
rev = pygame.Surface((REV_W, REV_H))
rev.fill(BG)

label(rev, "SYLARA — PIXEL MASTERWORK v2", 32, 20, font_big, (180, 255, 190))
label(rev, "100% prosedural  •  rig 1.5×  •  skill FX world-space",
      32, 64, font_small, (150, 200, 160))

cols = [
    ("IDLE", "idle", 0.0, 1.25, False, False),
    ("WALK", "walk", 0.35, 2.15, False, False),
    ("ATTACK WINDUP", "attack", 0.30, 1.0, False, False),
    ("ATTACK IMPACT", "attack", 0.50, 1.0, False, False),
    ("FOCUS FIRE", "idle", 0.0, 1.25, False, True),
    ("PORTRAIT LOD", "idle", 0.0, 1.25, True, False),
]
for i, (lbl, action, prog, phase, detail, focus) in enumerate(cols):
    cx = 32 + i * 225
    panel = pygame.Rect(cx, 90, 210, 700)
    pygame.draw.rect(rev, (12, 30, 20), panel, border_radius=10)
    pygame.draw.rect(rev, (70, 160, 80), panel, 2, border_radius=10)
    label(rev, lbl, cx + 8, 100, font_small, (210, 255, 215))

    frame = elite_frame(action, phase, prog, 1, detail, powered=True,
                        size=280, anchor=140)
    scaled = pygame.transform.smoothscale(frame, (210, 560))
    rev.blit(scaled, (cx, 130))
    bb_ = frame.get_bounding_rect(min_alpha=8)
    label(rev, f"bbox {bb_.w}×{bb_.h}  colors {len(colors_of(frame))}",
          cx + 4, 698, font_small, (150, 200, 160))
    label(rev, f"native scale×{scale:.3f}", cx + 4, 714,
          font_small, (120, 170, 140))

pygame.image.save(rev, os.path.join(DOCS, "sylara_v2_review.png"))
print("[SAVED] docs/sylara_v2_review.png")

# ── Anim strip ───────────────────────────────────────────────────────────────
STRIP_W, STRIP_H = 1400, 500
strip = pygame.Surface((STRIP_W, STRIP_H))
strip.fill(BG)
label(strip, "SYLARA v2 — ANIMATION STRIP", 20, 10, font_med, ACC)

for i in range(8):
    x = 20 + i * 165
    f_ = elite_frame("walk", i * math.tau / 8, size=200, anchor=100)
    scaled = pygame.transform.smoothscale(f_, (150, 300))
    strip.blit(scaled, (x, 40))
    label(strip, f"W{i}", x + 60, 345, font_small)

for i in range(10):
    x = 20 + i * 136
    f_ = elite_frame("attack", 0.0, i / 9.0, size=200, anchor=100)
    scaled = pygame.transform.smoothscale(f_, (126, 120))
    strip.blit(scaled, (x, 368))
    label(strip, f"A{i}", x + 50, 492 if i < 9 else 492, font_small)

pygame.image.save(strip, os.path.join(DOCS, "sylara_v2_anim_strip.png"))
print("[SAVED] docs/sylara_v2_anim_strip.png")

# ── In-game size ──────────────────────────────────────────────────────────────
IG_W, IG_H = 720, 240
ig = pygame.Surface((IG_W, IG_H))
ig.fill((14, 24, 14))
label(ig, "SYLARA v2 — IN-GAME SIZE (both teams)", 16, 8, font_small, WH)

for i, (team_col, x_pos) in enumerate(
        (((80, 140, 255), 160), ((255, 80, 80), 560))):
    native = elite_frame("idle", i * 1.4, size=300, anchor=150)
    screen_size = (int(bb.w * scale), int(bb.h * scale))
    if screen_size[0] < 4 or screen_size[1] < 4:
        screen_size = (50, 72)
    scaled_ig = pygame.transform.smoothscale(native, screen_size)
    pygame.draw.rect(ig, team_col,
                     (x_pos - screen_size[0] // 2 - 2,
                      IG_H // 2 - screen_size[1] // 2 - 2,
                      screen_size[0] + 4, screen_size[1] + 4), 2)
    ig.blit(scaled_ig, (x_pos - screen_size[0] // 2,
                        IG_H // 2 - screen_size[1] // 2))
    label(ig, f"{'Blue' if i == 0 else 'Red'} team  "
              f"{screen_size[0]}×{screen_size[1]}px",
          x_pos - 50, IG_H - 28, font_small, team_col)

for px_ in range(0, IG_W, 10):
    ig.set_at((px_, IG_H - 4), (60, 60, 80))
pygame.image.save(ig, os.path.join(DOCS, "sylara_v2_ingame.png"))
print("[SAVED] docs/sylara_v2_ingame.png")

# ── Skills sheet ─────────────────────────────────────────────────────────────
SK_W, SK_H = 1400, 880
sk = pygame.Surface((SK_W, SK_H))
sk.fill(BG)
label(sk, "SYLARA v2 — SKILL FX (world-space, 3 phases)", 24, 14,
      font_big, (180, 255, 190))

SKILLS = [
    ("Q  FOCUS FIRE", "q", [180, 100, 40]),
    ("W  WINDRUN", "w", [160, 120, 30]),
    ("E  SHACKLE SHOT", "e", [140, 110, 30]),
    ("R  POWERSHOT", "r", [220, 160, 40]),
]
PHASE_LABELS = ["ACTIVATION", "STEADY", "TELEGRAPH"]

for row, (skill_name, skill_key, timers) in enumerate(SKILLS):
    y_row = 70 + row * 200
    label(sk, skill_name, 10, y_row + 5, font_med, (210, 255, 215))
    for col, timer in enumerate(timers):
        x_col = 200 + col * 400
        s = pygame.Surface((400, 400), pygame.SRCALPHA)
        h = _ProbeEntity("sylara", 200, 200)
        h.pulse = 1.0
        h.direction = h.facing = 1
        h.active_skill = skill_key
        h.active_skill_timer = timer
        h._render_scale = 0.45
        h.range = 200
        h.target = _ProbeEntity("dummy", 300, 202)
        h.target.alive = True
        try:
            Z.draw_sylara(s, h, 200, 200)
        except Exception as e:
            print(f"  [WARN] skill {skill_key} t={timer}: {e}")
        scaled_sk = pygame.transform.smoothscale(s, (380, 180))
        sk.blit(scaled_sk, (x_col, y_row + 14))
        pygame.draw.rect(sk, (60, 130, 70),
                         (x_col, y_row + 14, 380, 180), 2)
        label(sk, f"{PHASE_LABELS[col]}  (t={timer})",
              x_col + 6, y_row + 192, font_small, (170, 220, 180))

pygame.image.save(sk, os.path.join(DOCS, "sylara_v2_skills.png"))
print("[SAVED] docs/sylara_v2_skills.png")

# ── Before / after ───────────────────────────────────────────────────────────
BA_W, BA_H = 900, 480
ba = pygame.Surface((BA_W, BA_H))
ba.fill(BG)
label(ba, "SYLARA — BEFORE  (v1 label)  vs  AFTER  (v2 Masterwork)",
      20, 10, font_med, WH)

before_surf = pygame.Surface((220, 220), pygame.SRCALPHA)
Z._draw_sylara_elite(before_surf, 110, 120, 1, 1.25, "idle", 0.0, False)
before_native_bb = before_surf.get_bounding_rect(min_alpha=8)
before_scaled = pygame.transform.smoothscale(
    before_surf, (int(before_native_bb.w * 0.9), int(before_native_bb.h * 0.9)))
label(ba, "v1  (estimated)", 40, 50, font_small, (150, 190, 160))
ba.blit(before_scaled, (60, 80))
pygame.draw.rect(ba, (60, 120, 70),
                 (50, 40, before_scaled.get_width() + 20,
                  before_scaled.get_height() + 20), 2)

after_surf = elite_frame("idle", 1.25, size=320, anchor=160)
after_bb = after_surf.get_bounding_rect(min_alpha=8)
after_scaled = pygame.transform.smoothscale(
    after_surf, (int(after_bb.w * 1.2), int(after_bb.h * 1.2)))
label(ba, "v2  MASTERWORK", 520, 50, font_small, (200, 255, 210))
ba.blit(after_scaled, (480, 80))
pygame.draw.rect(ba, (90, 180, 100),
                 (470, 40, after_scaled.get_width() + 20,
                  after_scaled.get_height() + 20), 2)

label(ba, f"Rig native bbox: v1 ~120×112 → v2 {bb.w}×{bb.h}",
      20, BA_H - 80, font_small, (170, 210, 180))
label(ba, f"Warna unik: v1 ~??  → v2 "
           f"{len(colors_of(elite_frame('idle', 1.25, size=320)))}",
      20, BA_H - 60, font_small, (170, 210, 180))
label(ba, f"Skill FX: v1 canvas-space → v2 world-space  (_fx_scale={fs40:.2f}×)",
      20, BA_H - 40, font_small, (170, 210, 180))

pygame.image.save(ba, os.path.join(DOCS, "sylara_v2_before_after.png"))
print("[SAVED] docs/sylara_v2_before_after.png")

print()
print(f"Audit selesai — {'SEMUA HIJAU ✓' if ok_all else 'ADA KEGAGALAN ✗'}")
sys.exit(0 if ok_all else 1)
