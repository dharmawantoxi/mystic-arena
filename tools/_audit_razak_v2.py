#!/usr/bin/env python3
"""Audit + preview sheet untuk Razak renderer masterwork v2 + Skill FX.

Mengukur hal yang sebelumnya hanya bisa dinilai mata:
  - skala rig native (1.5x) & ukuran akhir di layar (pipeline heroes/)
  - bbox tiap pose, jumlah warna unik
  - keunikan frame antar siklus (bukan sticker translation)
  - waktu render per pose & per skill (budget cache-miss ~3.5 ms)
  - skill Q/W/E/R: world-space (kompensasi 1/_render_scale), mewah,
    terukur:
      Q Sticky Napalm =  75 px dunia (di TARGET),
      W Flamebreak    =  95 px dunia (di TARGET),
      E Firefly       =  80 px dunia (AOE pendaratan, di CASTER),
      R Firestorm     = 180 px dunia (di CASTER - AI memukul sekitar
                        DIRI, bukan target)
  - piksel FX di LUAR siluet badan (skill benar-benar terlihat)

Menghasilkan:
  - docs/razak_v2_review.png
  - docs/razak_v2_anim_strip.png
  - docs/razak_v2_ingame.png
  - docs/razak_v2_skills.png
  - docs/razak_v2_before_after.png

Jalankan:  python3 tools/_audit_razak_v2.py
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
from bosses.level2 import _NS_razak as R


# ────────────────────────────────────────────────────────────────────
# util
# ────────────────────────────────────────────────────────────────────
def colors_of(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def boss_probe(size=520, ax=None, ay=None, **kw):
    """Entity probe untuk draw_razak (jangkar = ax, ay)."""
    ax = size // 2 if ax is None else ax
    ay = size // 2 if ay is None else ay
    b = _NS(boss_type="razak", boss_class="mini", x=float(ax), y=float(ay),
            direction=1, facing=1, pulse=1.3, timer=0, attack_cooldown=45,
            active_skill=None, active_skill_timer=0, target=None,
            hurt_flash_timer=0, alive=True, radius=34, hp=6200, max_hp=6200,
            range=55)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def rig_frame(action, phase, progress=0.0, facing=1, size=340):
    """Rig NATIVE (belum diturunkan ke SCALE) - untuk mengukur kepadatan."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    R._draw_razak_full_raw(s, size // 2, size // 2, facing, phase, action,
                           progress)
    return s


def check(cond, label, extra=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return bool(cond)


ok_all = True

# ── 1. rig native 1.5x + ukuran layar tetap sekelas keluarga ─────
scale = _get_hero_scale("razak")
body = rig_frame("idle", 1.25)
bb = body.get_bounding_rect(min_alpha=8)
ok_all &= check(bb.height >= 75 and bb.width >= 110,
                "rig NATIVE besar (author 1.5x, kepadatan detail naik)",
                f"{bb.w}x{bb.h}")
ok_all &= check(abs(R.RIG_SCALE - 1.5) < 1e-6,
                "RIG_SCALE terdokumentasi 1.5x", f"{R.RIG_SCALE}")

# ukuran akhir DI LAYAR (setelah SCALE) harus tetap <= alchemist true boss
arena = pygame.Surface((520, 520), pygame.SRCALPHA)
R.draw_razak(arena, boss_probe(), 260, 260)
ab = arena.get_bounding_rect(min_alpha=100)
ok_all &= check(ab.width <= 130 and ab.height <= 119,
                "bbox arena <= alchemist true boss (130x119)",
                f"{ab.w}x{ab.h}")
ok_all &= check(ab.width >= 60 and ab.height >= 60,
                "presence mini memadai (>=60x60)", f"{ab.w}x{ab.h}")
ok_all &= check(0.30 <= R.SCALE <= 1.0,
                "SCALE tunggal untuk semua jalur", f"{R.SCALE}")

# tinggi di lane hero (pipeline menormalkan)
lane = pygame.Surface((400, 400), pygame.SRCALPHA)
lh = _ProbeEntity("razak", 200, 200)
render_hero("razak", lane, lh, 200, 200)
lb = lane.get_bounding_rect(min_alpha=8)
ok_all &= check(50 <= lb.height <= 130,
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

# dash punya afterimage + pose sendiri
dash = rig_frame("dash", 1.0)
ok_all &= check(pygame.image.tobytes(dash, "RGBA")
                != pygame.image.tobytes(body, "RGBA"),
                "pose dash berbeda dari idle")

# ── 3. kepadatan warna rig (ramp + hue shift) ────────────────────
nc = len(colors_of(body))
ok_all &= check(nc >= 120, "kepadatan warna rig (ramp + hue shift)", f"{nc}")

# ── 4. palet material sampai ke render final ─────────────────────
pal = R.PALETTE
got = colors_of(body)
for key in ("gob_mid", "bat_mid", "wing_dark", "brass_mid",
            "leather_dark", "blue_mid", "bone_light", "metal_mid"):
    ok_all &= check(pal[key] in got, f"swatch {key}", str(pal[key]))

# ── 5. jangkar + kepala goblin di zona atas ──────────────────────
ax, ay = 170, 170
head_ok = any(body.get_at((ax + dx, ay + dy)).a > 150
              for dx in range(-20, 21) for dy in range(-72, -40))
ok_all &= check(head_ok, "kepala goblin ada di zona atas rig")
wing_ok = any(body.get_at((ax + dx, ay)).a > 40
              for dx in list(range(-62, -46)) + list(range(46, 63)))
ok_all &= check(wing_ok, "bentang sayap penuh (+-46..62 px)")

# ── 6. kosakata FX v2 hadir ──────────────────────────────────────
for helper in ("_fx_scale", "_ring_r", "_spark_star", "_chevron",
               "_dashed_ring", "_jagged_crack", "_tuft_points", "_static",
               "_dither_dots", "_world_to_local", "_mix", "_hash01"):
    ok_all &= check(callable(getattr(R, helper, None)), f"helper {helper}")

# nama publik lama tetap ada (kompatibilitas)
LEGACY = ("PALETTE", "_clamp", "_aacircle", "_aaline", "_poly", "_ellipse",
          "_rect", "_target_position", "_draw_flame", "_draw_ember",
          "_draw_fire_ground_patch", "NapalmProjectile", "NapalmPatch",
          "_detect_moving", "_update_attack_anim", "_manage_projectiles",
          "_manage_projectiles_no_patches", "_spawn_napalm", "draw_razak",
          "_draw_shockwave", "_draw_razak_idle", "_draw_razak_walk",
          "_draw_razak_attack", "_draw_razak_dashing",
          "_draw_razak_full_raw", "_draw_razak_full", "_draw_bat_wings",
          "_draw_bat_wings_front", "_draw_bat_body", "_draw_bat_head",
          "_draw_goblin_rider", "_draw_goblin_torso", "_draw_goblin_head",
          "_draw_fuel_tanks", "_draw_goblin_idle_arms",
          "_draw_goblin_gun_arms", "_draw_goblin_attack_arms",
          "_draw_goblin_arm", "_draw_flame_gun", "_draw_machete_held",
          "_draw_machete_swinging", "_draw_fire_wisps", "_draw_shadow",
          "_draw_fire_aura", "_draw_machete_swing_arc",
          "_draw_sticky_napalm", "_draw_flamebreak",
          "_draw_firestorm_ground", "_draw_firestorm", "draw_boss")
missing = [n for n in LEGACY if not hasattr(R, n)]
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
t_idle = bench_med(lambda: R.draw_razak(scratch, pb, 260, 260))
pw = boss_probe(ax=260, ay=260)
pw._razak_last_x, pw._razak_last_y = 258.0, 260.0
t_walk = bench_med(lambda: R.draw_razak(scratch, pw, 260, 260))
pa = boss_probe(ax=260, ay=260, _razak_attack_active=True,
                _razak_attack_progress=0.54)
t_atk = bench_med(lambda: R.draw_razak(scratch, pa, 260, 260))
print(f"[i] render ms: idle={t_idle:.2f} walk={t_walk:.2f} attack={t_atk:.2f}")
ok_all &= check(max(t_idle, t_walk, t_atk) <= 3.5,
                "budget cache-miss pose dasar",
                f"{max(t_idle, t_walk, t_atk):.2f} ms")

# ── 8. skill FX: world-space, mewah, terukur ─────────────────────
def render_skill(skill, timer, fs=None, W=800, tdx=170, tdy=-30):
    s = pygame.Surface((W, W), pygame.SRCALPHA)
    cx, cy = W // 2, W // 2
    h = boss_probe(ax=cx, ay=cy, active_skill=skill, active_skill_timer=timer,
                   target=_NS(x=float(cx + tdx), y=float(cy + tdy),
                              alive=True))
    if fs is not None:
        h._render_scale = fs
    R.draw_razak(s, h, cx, cy)
    return s, cx, cy


def count_fx(s, cx, cy, rmin=0, rmax=10 ** 6):
    """Piksel api menyala (FX) di annulus [rmin, rmax] dari jangkar."""
    n = 0
    for y in range(0, s.get_height(), 2):
        for x in range(0, s.get_width(), 2):
            d = math.hypot(x - cx, y - cy)
            if rmin <= d <= rmax:
                c = s.get_at((x, y))
                if c.a > 60 and c[0] > 140 and c[0] > c[2] + 40:
                    n += 1
    return n


def hits_ring(s, r_px, cx, cy, tol=4):
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
R.draw_razak(plain, boss_probe(ax=450, ay=450), 450, 450)
body_bb = plain.get_bounding_rect(min_alpha=100)
BODY_R = max(body_bb.width, body_bb.height) / 2.0
print(f"[i] radius siluet badan (arena) ~= {BODY_R:.0f} px")

# Q Sticky Napalm: ring telegraph TEPAT 75 px dunia DI TARGET
s, cx, cy = render_skill("q", 30, fs=0.5, W=900, tdx=95, tdy=-20)
bq = boss_probe(ax=cx, ay=cy, _render_scale=0.5,
                target=_NS(x=float(cx + 95), y=float(cy - 20), alive=True))
tx, ty = R._target_position(bq, cx, cy)
hits, total = hits_ring(s, 150, tx, ty)
ok_all &= check(hits > 120,
                "Q: ring telegraph tepat 150px canvas (=75 dunia, fs=0.5)"
                " di target", f"{hits}/{total}")
q_fx = count_fx(s, cx, cy, BODY_R, 400)
ok_all &= check(q_fx > 120, "Q: FX di luar siluet badan (jalur+splat)",
                f"{q_fx} px di luar r={BODY_R:.0f}")

# W Flamebreak: ring telegraph TEPAT 95 px dunia DI TARGET
s, cx, cy = render_skill("w", 30, fs=0.5, W=900, tdx=95, tdy=-20)
tx, ty = R._target_position(bq, cx, cy)
hits, total = hits_ring(s, 190, tx, ty)
ok_all &= check(hits > 120,
                "W: ring telegraph tepat 190px canvas (=95 dunia, fs=0.5)"
                " di target", f"{hits}/{total}")
w_fx = count_fx(s, cx, cy, BODY_R, 400)
ok_all &= check(w_fx > 120, "W: FX di luar siluet badan (kerucut api)",
                f"{w_fx} px")

# E Firefly: ring pendaratan TEPAT 80 px dunia DI CASTER
s, cx, cy = render_skill("e", 20, fs=0.5, W=900)
gy = cy + R.GROUND_DY
hits, total = hits_ring(s, 160, cx, gy)
ok_all &= check(hits > 120,
                "E: ring pendaratan tepat 160px canvas (=80 dunia, fs=0.5)",
                f"{hits}/{total}")
e_fx = count_fx(s, cx, cy, BODY_R, 400)
ok_all &= check(e_fx > 80, "E: FX di luar siluet badan (dash trail+ring)",
                f"{e_fx} px")

# R Firestorm: ring ultimate TEPAT 180 px dunia DI CASTER
s, cx, cy = render_skill("r", 60, fs=0.5, W=1000)
gy = cy + R.GROUND_DY
hits, total = hits_ring(s, 360, cx, gy)
ok_all &= check(hits > 100,
                "R: ring AOE tepat 360px canvas (=180 dunia, fs=0.5)"
                " di caster", f"{hits}/{total}")
r_fx = count_fx(s, cx, cy, BODY_R, 450)
ok_all &= check(r_fx > 200, "R: FX di luar siluet badan (pilar+erupsi)",
                f"{r_fx} px")

# world-space: FX ikut membesar saat _render_scale mengecil
a1, _, _ = render_skill("r", 60, fs=1.0, W=1000)
a2, _, _ = render_skill("r", 60, fs=0.5, W=1000)
b1 = a1.get_bounding_rect(min_alpha=30)
b2 = a2.get_bounding_rect(min_alpha=30)
ok_all &= check(b2.width > b1.width * 1.4,
                "FX world-space: mengembang saat _render_scale=0.5",
                f"{b1.width} -> {b2.width}")
ok_all &= check(abs(R._fx_scale(_NS(_render_scale=0.2)) - 2.6) < 1e-6,
                "cap _fx_scale = 2.6", f"{R._fx_scale(_NS(_render_scale=0.2))}")

# 3 tahap per skill benar-benar berbeda (aktivasi / steady / telegraph)
for skill, dur in (("q", 40), ("w", 50), ("e", 35), ("r", 90)):
    sigs = set()
    for timer in (dur - 4, int(dur * 0.6), 6):
        ss, _, _ = render_skill(skill, timer, W=620)
        sigs.add(pygame.image.tobytes(ss, "RGBA"))
    ok_all &= check(len(sigs) == 3, f"{skill.upper()}: 3 tahap FX berbeda",
                    f"{len(sigs)}/3")

# durasi FX == durasi AI
AI = {"q": 40, "w": 50, "e": 35, "r": 90}
ok_all &= check(R.SKILL_DUR == AI, "SKILL_DUR == durasi AI base_boss",
                str(R.SKILL_DUR))
ok_all &= check(R.SKILL_RADIUS == {"q": 75, "w": 95, "e": 80, "r": 180},
                "SKILL_RADIUS == radius gameplay", str(R.SKILL_RADIUS))

# timing skill (canvas mirip pipeline)
for skill, t in (("q", 25), ("w", 30), ("e", 20), ("r", 60)):
    surf = pygame.Surface((528, 528), pygame.SRCALPHA)
    hero = boss_probe(ax=264, ay=284, active_skill=skill,
                      active_skill_timer=t,
                      target=_NS(x=390.0, y=260.0, alive=True),
                      _render_scale=0.72)
    ms = bench_med(lambda: R.draw_razak(surf, hero, 264, 284), 20, 7)
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
ACCENT = (255, 178, 96)
SUB = (208, 164, 128)
EDGE = (168, 84, 30)


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
sheet.fill((16, 8, 5))
sheet.blit(font_title.render(
    "RAZAK v2 - PIXEL MASTERWORK + SKILL FX", True, ACCENT), (36, 22))
sheet.blit(font_small.render(
    "100% prosedural • rig native 1.5x • ramp 4-6 band + hue shift • selout • "
    "siluet bergerigi • specular cluster • dither • FX world-space "
    "(_fx_scale cap 2.6) • Q=75 / W=95 / E=80 / R=180 px dunia", True, SUB),
    (38, 66))

cards = (
    ("IDLE / HOVER", dict(action="idle", phase=1.25)),
    ("WALK / WING-BEAT", dict(action="walk", phase=2.4)),
    ("ATTACK (IMPACT)", dict(action="attack", phase=1.0, progress=.54)),
    ("R — FIRESTORM", dict(skill="r", timer=44)),
)
for i, (label, kw) in enumerate(cards):
    x = 28 + i * 340
    panel = pygame.Rect(x, 100, 322, 600)
    pygame.draw.rect(sheet, (34, 16, 8), panel, border_radius=12)
    pygame.draw.rect(sheet, EDGE, panel, 2, border_radius=12)
    sheet.blit(font_label.render(label, True, (255, 240, 224)), (x + 16, 116))
    native = pygame.Surface((340, 340), pygame.SRCALPHA)
    if "skill" in kw:
        h = boss_probe(ax=170, ay=190, active_skill=kw["skill"],
                       active_skill_timer=kw["timer"],
                       target=_NS(x=250.0, y=170.0, alive=True))
        R.draw_razak(native, h, 170, 190)
        draw_native(sheet, panel.inflate(-10, -66), native, 1.5, 0, 30)
    else:
        R._draw_razak_full_raw(native, 170, 190, 1, kw.get("phase", 0),
                               kw["action"], kw.get("progress", 0.0))
        draw_native(sheet, panel.inflate(-10, -66), native, 1.5, 0, 30)

notes = (
    "napas + gauge + pilot flame",
    "wing-beat solver • ekor inersia",
    "smear sabit api • bintang IMPACT",
    "ring 180 dunia • 8 pilar api",
)
for j, text in enumerate(notes):
    sheet.blit(font_small.render(text, True, (214, 166, 122)),
               (44 + j * 340, 712))
sheet.blit(font_small.render(
    f"rig native {bb.w}x{bb.h} px  •  bbox arena {ab.w}x{ab.h} px  •  "
    f"warna arena {nc}  •  "
    f"idle {t_idle:.2f} ms / attack {t_atk:.2f} ms (cache-miss)",
    True, (176, 138, 104)), (44, 760))
out1 = os.path.join(ROOT, "docs", "razak_v2_review.png")
pygame.image.save(sheet, out1)
print(out1)

# ── animation strip ──
SW, SH = 1400, 900
strip = pygame.Surface((SW, SH))
strip.fill((16, 8, 5))
strip.blit(font_title.render("RAZAK v2 - PROSEDURAL ANIMATION RIG", True,
                             ACCENT), (36, 22))
strip.blit(font_small.render(
    "tiap frame dihitung ulang dari sendi + fase + inersia ekor/syal + "
    "wing-beat solver; attack = 7 keyframe dengan frame IMPACT di ap=0.54",
    True, SUB), (38, 66))
rows = (("IDLE / HOVER", 6, "idle"),
        ("WALK / WING-BEAT", 8, "walk"),
        ("ATTACK / MACHETE API", 10, "attack"))
for row, (label, count, action) in enumerate(rows):
    top = 108 + row * 262
    strip.blit(font_label.render(label, True, ACCENT), (36, top + 66))
    pygame.draw.line(strip, (128, 66, 30), (35, top + 100),
                     (1364, top + 100), 1)
    for i in range(count):
        native = pygame.Surface((190, 240), pygame.SRCALPHA)
        phase = i / count * math.tau
        progress = i / max(1, count - 1)
        R._draw_razak_full_raw(native, 95, 130, 1, phase, action, progress)
        fx = 190 + i * 118
        strip.blit(native, (fx, top - 20))
out2 = os.path.join(ROOT, "docs", "razak_v2_anim_strip.png")
pygame.image.save(strip, out2)
print(out2)

# ── in-game size ──
GW, GH = 1200, 420
game = pygame.Surface((GW, GH))
game.fill((26, 22, 24))
for gy2 in range(0, GH, 40):
    pygame.draw.line(game, (34, 28, 30), (0, gy2), (GW, gy2), 1)
pygame.draw.line(game, (70, 56, 58), (0, 330), (GW, 330), 3)
game.blit(font_title.render(
    "UKURAN ASLI DI ARENA (pipeline cache hero + lighting + outline)", True,
    (255, 226, 200)), (30, 18))
poses = (
    ("idle", 0, 0.0, None), ("walk", 1.9, 0.0, None),
    ("attack", 0, 0.54, None), ("napalm", 1.25, 0.0, "q"),
    ("firestorm", 1.25, 0.0, "r"),
)
xpos = 130
for i, (name, ph, prog, skill) in enumerate(poses):
    hero = _ProbeEntity("razak", xpos, 300)
    hero.pulse = ph
    hero.team = "blue" if i % 2 == 0 else "red"
    if prog:
        hero._razak_attack_active = True
        hero._razak_attack_progress = prog
        hero.timer = 1
        hero._razak_prev_timer = 0
    if skill:
        hero.active_skill = skill
        hero.active_skill_timer = 25 if skill == "q" else 50
        hero.target = _ProbeEntity("dummy", xpos + 90, 292)
        hero.target.alive = True
    render_hero("razak", game, hero, xpos, 300)
    game.blit(font_small.render(name, True, (220, 208, 200)),
              (xpos - 40, 330))
    xpos += 210
out3 = os.path.join(ROOT, "docs", "razak_v2_ingame.png")
pygame.image.save(game, out3)
print(out3)

# ── skill FX sheet: 4 skill x 3 tahap ──
KW, KH = 1500, 1160
sk = pygame.Surface((KW, KH))
sk.fill((16, 8, 5))
sk.blit(font_title.render(
    "RAZAK v2 - SKILL FX MEWAH (world-space, 100% prosedural)", True,
    ACCENT), (36, 22))
sk.blit(font_small.render(
    "Q Sticky Napalm (75 dunia, 40f) • W Flamebreak (95 dunia, 50f) • "
    "E Firefly (dash AOE 80, 35f) • R Firestorm (AOE 180 di caster, 90f) — "
    "tiap skill 3 tahap: AKTIVASI / STEADY / TELEGRAPH", True, SUB), (38, 66))

skill_cards = (
    ("Q - STICKY NAPALM", "q", (40, 16, 8),
     ((37, "aktivasi"), (24, "steady"), (7, "impact"))),
    ("W - FLAMEBREAK", "w", (34, 18, 10),
     ((47, "aktivasi"), (30, "steady"), (9, "padam"))),
    ("E - FIREFLY", "e", (28, 18, 12),
     ((33, "hentak"), (20, "steady"), (6, "reda"))),
    ("R - FIRESTORM (ULT)", "r", (44, 14, 6),
     ((86, "aktivasi"), (52, "steady"), (14, "erupsi"))),
)
for ci, (label, skill, panel_col, stages) in enumerate(skill_cards):
    col_x = 28 + ci * 368
    for si, (timer, stage) in enumerate(stages):
        y0 = 100 + si * 350
        panel = pygame.Rect(col_x, y0, 348, 330)
        pygame.draw.rect(sk, panel_col, panel, border_radius=12)
        pygame.draw.rect(sk, EDGE, panel, 2, border_radius=12)
        sk.blit(font_small.render(f"{label}  t={timer} ({stage})", True,
                                  (255, 240, 224)), (col_x + 14, y0 + 12))
        native = pygame.Surface((620, 620), pygame.SRCALPHA)
        h = boss_probe(ax=310, ay=330, active_skill=skill,
                       active_skill_timer=timer,
                       target=_NS(x=440.0, y=300.0, alive=True))
        R.draw_razak(native, h, 310, 330)
        scaled = pygame.transform.scale(native, (336, 336))
        old = sk.get_clip()
        sk.set_clip(panel.inflate(-6, -34))
        sk.blit(scaled, (col_x + 6, y0 + 30))
        sk.set_clip(old)
out4 = os.path.join(ROOT, "docs", "razak_v2_skills.png")
pygame.image.save(sk, out4)
print(out4)

# ── before / after (snapshot v1 di tools/_razak_v1_snapshot.py) ──
def load_old_ns():
    path = os.path.join(ROOT, "tools", "_razak_v1_snapshot.py")
    spec = importlib.util.spec_from_file_location("_razak_v1", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._NS_razak


BW, BH = 1400, 720
ba = pygame.Surface((BW, BH))
ba.fill((16, 8, 5))
ba.blit(font_title.render(
    "RAZAK — BEFORE (v1)  vs  AFTER (v2 masterwork + skill FX)", True,
    ACCENT), (36, 22))
ba.blit(font_small.render(
    "ukuran layar dikunci sekelas keluarga level-2 • yang naik: kepadatan "
    "pixel-art (rig native 1.5x) + telegraph world-space Q75/W95/E80/R180",
    True, SUB), (38, 66))

Old = None
try:
    Old = load_old_ns()
except Exception as e:                                   # pragma: no cover
    print(f"[i] before/after dilewati: {e}")

if Old is not None:
    cols = (
        ("v1 - idle", None, None), ("v1 - attack", None, 0.54),
        ("v1 - R firestorm", "r", None),
        ("v2 - idle", None, None), ("v2 - attack", None, 0.54),
        ("v2 - R firestorm", "r", None),
    )
    for i, (label, skill, prog) in enumerate(cols):
        x = 24 + i * 228
        panel = pygame.Rect(x, 100, 216, 540)
        pygame.draw.rect(ba, (32, 14, 8), panel, border_radius=10)
        pygame.draw.rect(ba, EDGE, panel, 2, border_radius=10)
        ba.blit(font_small.render(label, True, (255, 240, 224)), (x + 12, 112))
        native = pygame.Surface((300, 300), pygame.SRCALPHA)
        NSns = Old if i < 3 else R
        h = boss_probe(ax=150, ay=160)
        if skill:
            h.active_skill = skill
            h.active_skill_timer = 44
            h.target = _NS(x=230.0, y=140.0, alive=True)
        if prog:
            h._razak_attack_active = True
            h._razak_attack_progress = prog
            h.timer = 40
        NSns.draw_razak(native, h, 150, 160)
        draw_native(ba, panel.inflate(-8, -40), native, 1.35, 0, 10)
    ba.blit(font_small.render(
        "kiri: v1 (tools/_razak_v1_snapshot.py)   |   kanan: v2 (selout, "
        "tuft, dither, specular, 7-keyframe attack, FX world-space 3 tahap)",
        True, (206, 156, 116)), (24, 660))
    out5 = os.path.join(ROOT, "docs", "razak_v2_before_after.png")
    pygame.image.save(ba, out5)
    print(out5)

print("SEMUA CEK LOLOS" if ok_all else "ADA CEK GAGAL")
sys.exit(0 if ok_all else 1)
