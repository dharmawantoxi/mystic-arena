#!/usr/bin/env python3
"""Audit + preview sheet untuk Gorath renderer masterwork v2 + Skill FX.

Mengukur hal yang sebelumnya hanya bisa dinilai mata:
  - skala rig native (1.5x) & ukuran akhir di layar (pipeline heroes/)
  - bbox tiap pose, jumlah warna unik (arena vs portrait LOD)
  - keunikan frame antar siklus (bukan sticker translation)
  - waktu render per pose & per skill (budget cache-miss ~3.5 ms)
  - skill Q/W/E/R: world-space (kompensasi 1/_render_scale), mewah, terukur
      W Bloodrite = 150 px dunia, E Thirst = 85 px dunia (di TARGET),
      R Rupture   = 190 px dunia (di CASTER)
  - piksel FX di LUAR siluet badan (skill benar-benar terlihat)

Menghasilkan:
  - docs/gorath_v2_review.png
  - docs/gorath_v2_anim_strip.png
  - docs/gorath_v2_ingame.png
  - docs/gorath_v2_skills.png
  - docs/gorath_v2_before_after.png

Jalankan:  python3 tools/_audit_gorath_v2.py
"""
import importlib.util
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

import heroes
from heroes import _ProbeEntity, render_hero, _get_hero_scale
from bosses.level2 import _NS_gorath as G


# ────────────────────────────────────────────────────────────────────
# util
# ────────────────────────────────────────────────────────────────────
def colors_of(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def boss_probe(size=520, ax=None, ay=None, **kw):
    """Entity probe untuk draw_gorath (jangkar = ax, ay)."""
    ax = size // 2 if ax is None else ax
    ay = size // 2 if ay is None else ay
    b = _NS(boss_type="gorath", boss_class="mini", x=float(ax), y=float(ay),
            direction=1, facing=1, pulse=1.3, timer=0, attack_cooldown=44,
            active_skill=None, active_skill_timer=0, target=None,
            hurt_flash_timer=0, alive=True, radius=36, hp=9000, max_hp=9000,
            range=58)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def rig_frame(action, phase, progress=0.0, facing=1, detail=False,
              size=340, rage=False, hunting=False):
    """Rig NATIVE (belum diturunkan ke SCALE) - untuk mengukur kepadatan."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    G._draw_gorath_body_raw(s, size // 2, size // 2, facing, phase, action,
                            progress, rage=rage, hunting=hunting,
                            detail=detail)
    return s


def check(cond, label, extra=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return bool(cond)


ok_all = True

# ── 1. rig native 1.5x + ukuran layar tetap sekelas keluarga ─────
scale = _get_hero_scale("gorath")
body = rig_frame("idle", 1.25)
bb = body.get_bounding_rect(min_alpha=8)
ok_all &= check(bb.height >= 120 and bb.width >= 90,
                "rig NATIVE besar (author 1.5x, kepadatan detail naik)",
                f"{bb.w}x{bb.h}")
ok_all &= check(abs(G.RIG_SCALE - 1.5) < 1e-6,
                "RIG_SCALE terdokumentasi 1.5x", f"{G.RIG_SCALE}")

# ukuran akhir DI LAYAR (setelah SCALE) harus tetap <= alchemist true boss
arena = pygame.Surface((520, 520), pygame.SRCALPHA)
G.draw_gorath(arena, boss_probe(), 260, 260)
ab = arena.get_bounding_rect(min_alpha=100)
ok_all &= check(ab.width <= 130 and ab.height <= 119,
                "bbox arena <= alchemist true boss (130x119)",
                f"{ab.w}x{ab.h}")
ok_all &= check(ab.width >= 60 and ab.height >= 60,
                "presence mini memadai (>=60x60)", f"{ab.w}x{ab.h}")
ok_all &= check(0.30 <= G.SCALE <= 1.0,
                "SCALE tunggal untuk semua jalur", f"{G.SCALE}")

# tinggi di lane hero (pipeline menormalkan)
lane = pygame.Surface((400, 400), pygame.SRCALPHA)
lh = _ProbeEntity("gorath", 200, 200)
render_hero("gorath", lane, lh, 200, 200)
lb = lane.get_bounding_rect(min_alpha=8)
ok_all &= check(50 <= lb.height <= 100,
                "tinggi di lane hero (pipeline auto-normalisasi)",
                f"{lb.w}x{lb.h} scale={scale:.3f}")

# ── 2. keunikan frame (animasi hidup, bukan sticker) ─────────────
idle_frames = {pygame.image.tobytes(rig_frame("idle", i * 0.52), "RGBA")
               for i in range(8)}
walk_frames = {pygame.image.tobytes(rig_frame("walk", i * 0.785), "RGBA")
               for i in range(8)}
atk_frames = {pygame.image.tobytes(rig_frame("attack", 1.0, i / 9.0), "RGBA")
              for i in range(10)}
ok_all &= check(len(idle_frames) == 8, "idle: 8 frame unik (living idle)",
                f"{len(idle_frames)}/8")
ok_all &= check(len(walk_frames) == 8, "walk: 8 frame unik",
                f"{len(walk_frames)}/8")
ok_all &= check(len(atk_frames) >= 9, "attack: >=9 pose unik (multi-keyframe)",
                f"{len(atk_frames)}/10")

# frame IMPACT punya siluet berbeda dari tetangganya
imp = rig_frame("attack", 1.0, 0.54)
pre = rig_frame("attack", 1.0, 0.46)
ok_all &= check(pygame.image.tobytes(imp, "RGBA")
                != pygame.image.tobytes(pre, "RGBA"),
                "frame IMPACT (ap=0.54) berbeda dari wind-through")

# ── 3. portrait LOD lebih kaya ───────────────────────────────────
port = rig_frame("idle", 0.8, detail=True)
norm = rig_frame("idle", 0.8, detail=False)
nc, pc = len(colors_of(norm)), len(colors_of(port))
ok_all &= check(pc > nc, "portrait LOD lebih banyak warna", f"{nc} -> {pc}")
ok_all &= check(nc >= 120, "kepadatan warna rig (ramp + hue shift)", f"{nc}")

# ── 4. palet material sampai ke render final ─────────────────────
pal = G.PALETTE
got = colors_of(norm)
for key in ("skin_mid", "blood_mid", "bone_light", "metal_light",
            "leather_dark", "hair_mid"):
    ok_all &= check(pal[key] in got, f"swatch {key}", str(pal[key]))

# badan bereaksi ke state skill (rune/mata menyala saat rage)
rage_on = rig_frame("idle", 0.8, rage=True)
ok_all &= check(pygame.image.tobytes(rage_on, "RGBA")
                != pygame.image.tobytes(norm, "RGBA"),
                "badan bereaksi ke state skill (rage glow)")

# ── 5. jangkar tanah + kepala di zona atas ───────────────────────
ax, ay = 170, 170
ground = ay + int(G.GROUND_DY / G.SCALE)      # GROUND_DY di ruang lokal rig
plume_ok = any(norm.get_at((x, min(339, ground))).a > 40
               for x in range(ax - 40, ax + 41))
ok_all &= check(plume_ok, "kabut/plume menapak di garis tanah")
head_ok = any(norm.get_at((ax + dx, ay + dy)).a > 150
              for dx in range(-20, 21) for dy in range(-70, -40))
ok_all &= check(head_ok, "kepala ada di zona atas rig")

# ── 6. kosakata FX v2 hadir ──────────────────────────────────────
for helper in ("_fx_scale", "_ring_r", "_spark_star", "_chevron",
               "_dashed_ring", "_jagged_crack", "_tuft_points", "_static",
               "_dither_dots", "_world_to_local", "_mix", "_hash01"):
    ok_all &= check(callable(getattr(G, helper, None)), f"helper {helper}")

# nama publik lama tetap ada (kompatibilitas)
LEGACY = ("PALETTE", "_clamp", "_aacircle", "_aaline", "_poly", "_ellipse",
          "_rect", "_target_position", "_draw_blood_splatter",
          "_draw_blood_droplet", "_draw_blood_streak", "BloodProjectile",
          "_detect_moving", "_update_attack_anim", "_manage_projectiles",
          "_spawn_projectile", "draw_gorath", "_draw_shockwave",
          "_draw_gorath_idle", "_draw_gorath_walk", "_draw_gorath_attack",
          "_draw_gorath_body_raw", "_draw_gorath_body", "_draw_loincloth",
          "_draw_torso", "_draw_shoulders", "_draw_gorath_head",
          "_draw_spiky_hair", "_draw_idle_arms", "_draw_attack_arms",
          "_draw_arm_segment", "_draw_hand", "_draw_curved_blade",
          "_draw_curved_blade_angled", "_draw_body_blood_drips",
          "_draw_blood_wisps", "_draw_blood_trail", "_draw_shadow",
          "_draw_blood_aura", "_draw_ground_blood_pool",
          "_draw_blade_swing_arc", "_draw_swing_impact", "_draw_bloodrage",
          "_draw_bloodrite_ground", "_draw_bloodrite", "_draw_thirst",
          "_draw_rupture_ground", "_draw_rupture", "draw_boss")
missing = [n for n in LEGACY if not hasattr(G, n)]
ok_all &= check(not missing, "semua nama publik lama dipertahankan",
                f"{len(LEGACY)} nama" if not missing else str(missing))

# ── 7. timing (budget cache-miss ~3.5 ms) ────────────────────────
def bench_med(fn, n=20, reps=7):
    fn()
    runs = []
    for _ in range(reps):
        t0 = time.perf_counter()
        for _ in range(n):
            fn()
        runs.append((time.perf_counter() - t0) / n * 1000)
    runs.sort()
    return runs[len(runs) // 2]


scratch = pygame.Surface((520, 520), pygame.SRCALPHA)
pb = boss_probe(ax=260, ay=260)
t_idle = bench_med(lambda: G.draw_gorath(scratch, pb, 260, 260))
pw = boss_probe(ax=260, ay=260)
pw._gor_last_x, pw._gor_last_y = 258.0, 260.0
t_walk = bench_med(lambda: G.draw_gorath(scratch, pw, 260, 260))
pa = boss_probe(ax=260, ay=260, _gor_attack_active=True,
                _gor_attack_progress=0.54)
t_atk = bench_med(lambda: G.draw_gorath(scratch, pa, 260, 260))
print(f"[i] render ms: idle={t_idle:.2f} walk={t_walk:.2f} attack={t_atk:.2f}")
ok_all &= check(max(t_idle, t_walk, t_atk) <= 3.5,
                "budget cache-miss pose dasar", f"{max(t_idle, t_walk, t_atk):.2f} ms")

# ── 8. skill FX: world-space, mewah, terukur ─────────────────────
def render_skill(skill, timer, fs=None, W=800, tdx=170, tdy=-30):
    s = pygame.Surface((W, W), pygame.SRCALPHA)
    cx, cy = W // 2, W // 2
    h = boss_probe(ax=cx, ay=cy, active_skill=skill, active_skill_timer=timer,
                   target=_NS(x=float(cx + tdx), y=float(cy + tdy),
                              alive=True))
    if fs is not None:
        h._render_scale = fs
    G.draw_gorath(s, h, cx, cy)
    return s, cx, cy


def count_fx(s, cx, cy, rmin=0, rmax=10 ** 6):
    """Piksel darah menyala (FX) di annulus [rmin, rmax] dari jangkar."""
    n = 0
    for y in range(0, s.get_height(), 2):
        for x in range(0, s.get_width(), 2):
            d = math.hypot(x - cx, y - cy)
            if rmin <= d <= rmax:
                c = s.get_at((x, y))
                if c.a > 60 and c[0] > 110 and c[0] > c[2] + 30:
                    n += 1
    return n


def hits_ring(s, r_px, cx, cy, tol=3):
    hits = total = 0
    for a in range(0, 360, 2):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        ok = False
        for dr in range(-tol, tol + 1):
            x = int(cx + ca * (r_px + dr))
            y = int(cy + sa * (r_px + dr))
            if 0 <= x < s.get_width() and 0 <= y < s.get_height() \
                    and s.get_at((x, y)).a > 30:
                ok = True
                break
        total += 1
        hits += 1 if ok else 0
    return hits, total


# siluet badan telanjang (tanpa skill) -> pembanding "di luar badan"
plain = pygame.Surface((900, 900), pygame.SRCALPHA)
G.draw_gorath(plain, boss_probe(ax=450, ay=450), 450, 450)
body_bb = plain.get_bounding_rect(min_alpha=100)
BODY_R = max(body_bb.width, body_bb.height) / 2.0
print(f"[i] radius siluet badan (arena) ~= {BODY_R:.0f} px")

# Q Bloodrage: self-buff, FX jelas DI LUAR siluet badan
s, cx, cy = render_skill("q", 50, fs=0.5, W=900)
q_fx = count_fx(s, cx, cy, BODY_R, 320)
ok_all &= check(q_fx > 120, "Q: FX di luar siluet badan (aura/bara/mahkota)",
                f"{q_fx} px di luar r={BODY_R:.0f}")

# W Bloodrite: ring jangkauan TEPAT 150 px dunia (fs=0.5 -> 300 canvas)
s, cx, cy = render_skill("w", 40, fs=0.5, W=900)
gy = cy + G.GROUND_DY - 8
hits, total = hits_ring(s, 300, cx, gy)
ok_all &= check(hits > 120,
                "W: ring jangkauan tepat 300px canvas (=150 dunia, fs=0.5)",
                f"{hits}/{total}")
w_fx = count_fx(s, cx, cy, BODY_R, 320)
ok_all &= check(w_fx > 120, "W: FX di luar siluet badan", f"{w_fx} px")

# E Thirst: ring AOE 85 px dunia DI TARGET
s, cx, cy = render_skill("e", 24, fs=0.5, W=900, tdx=95, tdy=-20)
# posisi target di ruang gambar = hasil kompensasi _render_scale renderer
tx, ty = G._target_position(
    boss_probe(ax=cx, ay=cy, _render_scale=0.5,
               target=_NS(x=float(cx + 95), y=float(cy - 20), alive=True)),
    cx, cy)
hits, total = hits_ring(s, 170, tx, ty)
ok_all &= check(hits > 120,
                "E: ring AOE tepat 170px canvas (=85 dunia, fs=0.5) di target",
                f"{hits}/{total}")
e_fx = count_fx(s, cx, cy, BODY_R, 320)
ok_all &= check(e_fx > 100, "E: FX di luar siluet badan (beam+telegraph)",
                f"{e_fx} px")

# R Rupture: ring AOE 190 px dunia DI CASTER
s, cx, cy = render_skill("r", 60, fs=0.5, W=1000)
gy = cy + G.GROUND_DY
hits, total = hits_ring(s, 380, cx, gy)
ok_all &= check(hits > 100,
                "R: ring AOE tepat 380px canvas (=190 dunia, fs=0.5) di caster",
                f"{hits}/{total}")
r_fx = count_fx(s, cx, cy, BODY_R, 400)
ok_all &= check(r_fx > 200, "R: FX di luar siluet badan", f"{r_fx} px")

# world-space: FX ikut membesar saat _render_scale mengecil
a1, _, _ = render_skill("r", 60, fs=1.0, W=1000)
a2, _, _ = render_skill("r", 60, fs=0.5, W=1000)
b1 = a1.get_bounding_rect(min_alpha=30)
b2 = a2.get_bounding_rect(min_alpha=30)
ok_all &= check(b2.width > b1.width * 1.4,
                "FX world-space: mengembang saat _render_scale=0.5",
                f"{b1.width} -> {b2.width}")
ok_all &= check(abs(G._fx_scale(_NS(_render_scale=0.2)) - 2.6) < 1e-6,
                "cap _fx_scale = 2.6", f"{G._fx_scale(_NS(_render_scale=0.2))}")

# 3 tahap per skill benar-benar berbeda (aktivasi / steady / telegraph)
for skill, dur in (("q", 90), ("w", 60), ("e", 35), ("r", 90)):
    sigs = set()
    for timer in (dur - 4, int(dur * 0.6), 6):
        ss, _, _ = render_skill(skill, timer, W=620)
        sigs.add(pygame.image.tobytes(ss, "RGBA"))
    ok_all &= check(len(sigs) == 3, f"{skill.upper()}: 3 tahap FX berbeda",
                    f"{len(sigs)}/3")

# durasi FX == durasi AI
AI = {"q": 90, "w": 60, "e": 35, "r": 90}
ok_all &= check(G.SKILL_DUR == AI, "SKILL_DUR == durasi AI base_boss",
                str(G.SKILL_DUR))
ok_all &= check(G.SKILL_RADIUS == {"w": 150, "e": 85, "r": 190},
                "SKILL_RADIUS == radius gameplay", str(G.SKILL_RADIUS))

# timing skill (canvas mirip pipeline)
for skill, t in (("q", 50), ("w", 30), ("e", 20), ("r", 60)):
    surf = pygame.Surface((528, 528), pygame.SRCALPHA)
    hero = boss_probe(ax=264, ay=284, active_skill=skill,
                      active_skill_timer=t,
                      target=_NS(x=390.0, y=260.0, alive=True),
                      _render_scale=0.72)
    ms = bench_med(lambda: G.draw_gorath(surf, hero, 264, 284), 20, 7)
    print(f"[i] skill {skill}: {ms:.2f} ms/frame (median, 528x528)")
    ok_all &= check(ms <= 3.5, f"skill {skill} dalam budget", f"{ms:.2f} ms")

# tidak ada aset
src = open(os.path.join(ROOT, "bosses", "level2.py")).read()
ok_all &= check("pygame.image.load" not in src,
                "100% prosedural (tanpa pygame.image.load)")


# ═══════════════════════ PREVIEW SHEETS ══════════════════════════
font_title = pygame.font.Font(None, 44)
font_label = pygame.font.Font(None, 30)
font_small = pygame.font.Font(None, 21)
ACCENT = (255, 150, 140)
SUB = (196, 150, 148)
EDGE = (150, 40, 40)


def draw_native(target, rect, native, zoom=1.0, dx=0, dy=0):
    if zoom != 1.0:
        native = pygame.transform.scale(
            native, (int(native.get_width() * zoom),
                     int(native.get_height() * zoom)))
    old = target.get_clip()
    target.set_clip(rect)
    target.blit(native, (rect.centerx - native.get_width() // 2 + dx,
                         rect.centery - native.get_height() // 2 + dy))
    target.set_clip(old)


# ── review sheet ──
W, H = 1400, 860
sheet = pygame.Surface((W, H))
sheet.fill((14, 6, 8))
sheet.blit(font_title.render(
    "GORATH v2 - PIXEL MASTERWORK + SKILL FX", True, ACCENT), (36, 22))
sheet.blit(font_small.render(
    "100% prosedural • rig native 1.5x • ramp 5-7 band + hue shift • selout • "
    "siluet bergerigi • specular cluster • dither • FX world-space "
    "(_fx_scale cap 2.6) • W=150 / E=85 / R=190 px dunia", True, SUB), (38, 66))

cards = (
    ("IDLE / FLOAT", dict(action="idle", phase=1.25)),
    ("WALK / PLUME", dict(action="walk", phase=2.4)),
    ("ATTACK (IMPACT)", dict(action="attack", phase=1.0, progress=.54)),
    ("R — RUPTURE", dict(skill="r", timer=44)),
)
for i, (label, kw) in enumerate(cards):
    x = 28 + i * 340
    panel = pygame.Rect(x, 100, 322, 600)
    pygame.draw.rect(sheet, (30, 12, 14), panel, border_radius=12)
    pygame.draw.rect(sheet, EDGE, panel, 2, border_radius=12)
    sheet.blit(font_label.render(label, True, (255, 236, 232)), (x + 16, 116))
    native = pygame.Surface((340, 340), pygame.SRCALPHA)
    if "skill" in kw:
        h = boss_probe(ax=170, ay=190, active_skill=kw["skill"],
                       active_skill_timer=kw["timer"],
                       target=_NS(x=250.0, y=170.0, alive=True))
        G.draw_gorath(native, h, 170, 190)
        draw_native(sheet, panel.inflate(-10, -66), native, 1.5, 0, 30)
    else:
        G._draw_gorath_body_raw(native, 170, 190, 1, kw.get("phase", 0),
                                kw["action"], kw.get("progress", 0.0))
        draw_native(sheet, panel.inflate(-10, -66), native, 1.5, 0, 30)

notes = (
    "napas + rune dada • plume melayang",
    "foot solver kabut • riak darah",
    "smear sabit • bintang IMPACT",
    "ring 190 dunia • rantai darah",
)
for j, text in enumerate(notes):
    sheet.blit(font_small.render(text, True, (205, 151, 145)),
               (44 + j * 340, 712))
sheet.blit(font_small.render(
    f"rig native {bb.w}x{bb.h} px  •  bbox arena {ab.w}x{ab.h} px  •  "
    f"warna arena {nc} / portrait {pc}  •  "
    f"idle {t_idle:.2f} ms / attack {t_atk:.2f} ms (cache-miss)",
    True, (170, 130, 128)), (44, 760))
out1 = os.path.join(ROOT, "docs", "gorath_v2_review.png")
pygame.image.save(sheet, out1)
print(out1)

# ── animation strip ──
SW, SH = 1400, 900
strip = pygame.Surface((SW, SH))
strip.fill((14, 6, 8))
strip.blit(font_title.render("GORATH v2 - PROSEDURAL ANIMATION RIG", True,
                             ACCENT), (36, 22))
strip.blit(font_small.render(
    "tiap frame dihitung ulang dari sendi + fase + inersia rambut/kain + "
    "solver plume; attack = 7 keyframe dengan frame IMPACT di ap=0.54",
    True, SUB), (38, 66))
rows = (("IDLE / FLOAT", 6, "idle"),
        ("WALK / PLUME CONTACT", 8, "walk"),
        ("ATTACK / KUKRI", 10, "attack"))
for row, (label, count, action) in enumerate(rows):
    top = 108 + row * 262
    strip.blit(font_label.render(label, True, ACCENT), (36, top + 66))
    pygame.draw.line(strip, (128, 52, 52), (35, top + 100),
                     (1364, top + 100), 1)
    for i in range(count):
        native = pygame.Surface((190, 240), pygame.SRCALPHA)
        phase = i / count * math.tau
        progress = i / max(1, count - 1)
        G._draw_gorath_body_raw(native, 95, 150, 1, phase, action, progress)
        fx = 190 + i * 118
        strip.blit(native, (fx, top - 20))
out2 = os.path.join(ROOT, "docs", "gorath_v2_anim_strip.png")
pygame.image.save(strip, out2)
print(out2)

# ── in-game size ──
GW, GH = 1200, 420
game = pygame.Surface((GW, GH))
game.fill((26, 22, 24))
for gy in range(0, GH, 40):
    pygame.draw.line(game, (34, 28, 30), (0, gy), (GW, gy), 1)
pygame.draw.line(game, (70, 56, 58), (0, 330), (GW, 330), 3)
game.blit(font_title.render(
    "UKURAN ASLI DI ARENA (pipeline cache hero + lighting + outline)", True,
    (255, 220, 215)), (30, 18))
poses = (
    ("idle", 0, 0.0, None), ("walk", 1.9, 0.0, None),
    ("attack", 0, 0.54, None), ("bloodrite", 1.25, 0.0, "w"),
    ("rupture", 1.25, 0.0, "r"),
)
xpos = 130
for i, (name, ph, prog, skill) in enumerate(poses):
    hero = _ProbeEntity("gorath", xpos, 300)
    hero.pulse = ph
    hero.team = "blue" if i % 2 == 0 else "red"
    if prog:
        hero._gor_attack_active = True
        hero._gor_attack_progress = prog
        hero.timer = 1
        hero._gor_prev_timer = 0
    if skill:
        hero.active_skill = skill
        hero.active_skill_timer = 30 if skill == "w" else 50
        hero.target = _ProbeEntity("dummy", xpos + 90, 292)
        hero.target.alive = True
    render_hero("gorath", game, hero, xpos, 300)
    game.blit(font_small.render(name, True, (220, 208, 200)),
              (xpos - 40, 330))
    xpos += 210
out3 = os.path.join(ROOT, "docs", "gorath_v2_ingame.png")
pygame.image.save(game, out3)
print(out3)

# ── skill FX sheet: 4 skill x 3 tahap ──
KW, KH = 1500, 1160
sk = pygame.Surface((KW, KH))
sk.fill((14, 6, 8))
sk.blit(font_title.render(
    "GORATH v2 - SKILL FX MEWAH (world-space, 100% prosedural)", True,
    ACCENT), (36, 22))
sk.blit(font_small.render(
    "Q Bloodrage (buff, 90f) • W Bloodrite (AOE 150, 60f) • "
    "E Thirst (leap AOE 85, 35f) • R Rupture (AOE 190 di caster, 90f) — "
    "tiap skill 3 tahap: AKTIVASI / STEADY / TELEGRAPH", True, SUB), (38, 66))

skill_cards = (
    ("Q - BLOODRAGE", "q", (36, 12, 14),
     ((86, "aktivasi"), (54, "steady"), (10, "telegraph"))),
    ("W - BLOODRITE", "w", (30, 14, 18),
     ((57, "aktivasi"), (34, "steady"), (8, "erupsi"))),
    ("E - THIRST", "e", (24, 16, 20),
     ((33, "aktivasi"), (20, "steady"), (6, "hentak"))),
    ("R - RUPTURE (ULT)", "r", (40, 10, 14),
     ((86, "aktivasi"), (52, "steady"), (14, "ledakan"))),
)
for ci, (label, skill, panel_col, stages) in enumerate(skill_cards):
    col_x = 28 + ci * 368
    for si, (timer, stage) in enumerate(stages):
        y0 = 100 + si * 350
        panel = pygame.Rect(col_x, y0, 348, 330)
        pygame.draw.rect(sk, panel_col, panel, border_radius=12)
        pygame.draw.rect(sk, EDGE, panel, 2, border_radius=12)
        sk.blit(font_small.render(f"{label}  t={timer} ({stage})", True,
                                  (255, 236, 232)), (col_x + 14, y0 + 12))
        native = pygame.Surface((620, 620), pygame.SRCALPHA)
        h = boss_probe(ax=310, ay=330, active_skill=skill,
                       active_skill_timer=timer,
                       target=_NS(x=440.0, y=300.0, alive=True))
        G.draw_gorath(native, h, 310, 330)
        scaled = pygame.transform.scale(native, (336, 336))
        old = sk.get_clip()
        sk.set_clip(panel.inflate(-6, -34))
        sk.blit(scaled, (col_x + 6, y0 + 30))
        sk.set_clip(old)
out4 = os.path.join(ROOT, "docs", "gorath_v2_skills.png")
pygame.image.save(sk, out4)
print(out4)

# ── before / after (snapshot v1 di tools/_gorath_v1_snapshot.py) ──
def load_old_ns():
    path = os.path.join(ROOT, "tools", "_gorath_v1_snapshot.py")
    spec = importlib.util.spec_from_file_location("_gorath_v1", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._NS_gorath


BW, BH = 1400, 720
ba = pygame.Surface((BW, BH))
ba.fill((14, 6, 8))
ba.blit(font_title.render(
    "GORATH — BEFORE (v1)  vs  AFTER (v2 masterwork + skill FX)", True,
    ACCENT), (36, 22))
ba.blit(font_small.render(
    "ukuran layar dikunci sekelas keluarga level-2 • yang naik: kepadatan "
    "pixel-art (rig native 1.5x) + telegraph world-space W150/E85/R190",
    True, SUB), (38, 66))

Old = None
try:
    Old = load_old_ns()
except Exception as e:                                   # pragma: no cover
    print(f"[i] before/after dilewati: {e}")

if Old is not None:
    cols = (
        ("v1 - idle", None, None), ("v1 - attack", None, 0.54),
        ("v1 - R rupture", "r", None),
        ("v2 - idle", None, None), ("v2 - attack", None, 0.54),
        ("v2 - R rupture", "r", None),
    )
    for i, (label, skill, prog) in enumerate(cols):
        x = 24 + i * 228
        panel = pygame.Rect(x, 100, 216, 540)
        pygame.draw.rect(ba, (28, 12, 14), panel, border_radius=10)
        pygame.draw.rect(ba, EDGE, panel, 2, border_radius=10)
        ba.blit(font_small.render(label, True, (255, 236, 232)), (x + 12, 112))
        native = pygame.Surface((300, 300), pygame.SRCALPHA)
        NS = Old if i < 3 else G
        h = boss_probe(ax=150, ay=160)
        if skill:
            h.active_skill = skill
            h.active_skill_timer = 44
            h.target = _NS(x=230.0, y=140.0, alive=True)
        if prog:
            h._gor_attack_active = True
            h._gor_attack_progress = prog
            h.timer = 40
        NS.draw_gorath(native, h, 150, 160)
        draw_native(ba, panel.inflate(-8, -40), native, 1.35, 0, 10)
    ba.blit(font_small.render(
        "kiri: v1 (tools/_gorath_v1_snapshot.py)   |   kanan: v2 (selout, "
        "tuft, dither, specular, 7-keyframe attack, FX world-space 3 tahap)",
        True, (200, 148, 145)), (24, 660))
    out5 = os.path.join(ROOT, "docs", "gorath_v2_before_after.png")
    pygame.image.save(ba, out5)
    print(out5)

print("SEMUA CEK LOLOS" if ok_all else "ADA CEK GAGAL")
sys.exit(0 if ok_all else 1)
