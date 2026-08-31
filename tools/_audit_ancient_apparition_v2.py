#!/usr/bin/env python3
"""Audit + preview sheet untuk Ancient Apparition renderer masterwork v2 + Skill FX.

Mengukur:
  - skala rig native (1.5x) & ukuran akhir di layar (pipeline heroes/)
  - bbox tiap pose, jumlah warna unik (arena vs portrait LOD)
  - keunikan frame antar siklus (bukan sticker translation)
  - waktu render per pose & per skill (budget cache-miss ~3.5 ms)
  - skill Q/W/E/R: world-space (kompensasi 1/_render_scale), mewah, terukur
      Q Ice Vortex   = 80 px dunia di TARGET,
      W Frost Beam   = 65 px dunia di TARGET,
      E Ice Bolt     = 70 px dunia di TARGET,
      R Cold Feet    = 80 px dunia di TARGET
  - piksel FX di LUAR siluet badan (skill benar-benar terlihat)

Menghasilkan:
  - docs/ancient_apparition_v2_review.png
  - docs/ancient_apparition_v2_anim_strip.png
  - docs/ancient_apparition_v2_ingame.png
  - docs/ancient_apparition_v2_skills.png
  - docs/ancient_apparition_v2_before_after.png

Jalankan:  python3 tools/_audit_ancient_apparition_v2.py
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
from bosses.level3 import _NS_ancient_apparition as AA


# ────────────────────────────────────────────────────────────────────
# util
# ────────────────────────────────────────────────────────────────────
def colors_of(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def boss_probe(size=520, ax=None, ay=None, **kw):
    """Entity probe untuk draw_ancient_apparition (jangkar = ax, ay)."""
    ax = size // 2 if ax is None else ax
    ay = size // 2 if ay is None else ay
    b = _NS(boss_type="ancient_apparition", boss_class="true", x=float(ax), y=float(ay),
            direction=1, facing=1, pulse=1.3, timer=0, attack_cooldown=50,
            active_skill=None, active_skill_timer=0, target=None,
            hurt_flash_timer=0, alive=True, radius=40, hp=12000, max_hp=12000,
            range=150)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def rig_frame(action, phase, progress=0.0, facing=1, detail=False,
              size=340, active_skill=None):
    """Rig NATIVE (belum diturunkan ke SCALE) - untuk mengukur kepadatan."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    AA._draw_aa_body_raw(s, size // 2, size // 2, facing, phase, action,
                         progress, detail=detail)
    return s


def check(cond, label, extra=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return bool(cond)


ok_all = True

# ── 1. rig native 1.5x + ukuran layar ─────────────────────────────
scale = _get_hero_scale("ancient_apparition")
body = rig_frame("idle", 1.25)
bb = body.get_bounding_rect(min_alpha=8)
ok_all &= check(bb.height >= 120 and bb.width >= 80,
                "rig NATIVE besar (author 1.5x, kepadatan detail kristal naik)",
                f"{bb.w}x{bb.h}")
ok_all &= check(abs(AA.RIG_SCALE - 1.5) < 1e-6,
                "RIG_SCALE terdokumentasi 1.5x", f"{AA.RIG_SCALE}")

# ukuran akhir DI LAYAR (setelah SCALE)
arena = pygame.Surface((520, 520), pygame.SRCALPHA)
AA.draw_ancient_apparition(arena, boss_probe(), 260, 260)
ab = arena.get_bounding_rect(min_alpha=100)
ok_all &= check(ab.width <= 140 and ab.height <= 150,
                "bbox arena true boss sekelas level 3",
                f"{ab.w}x{ab.h}")
ok_all &= check(ab.width >= 60 and ab.height >= 60,
                "presence true boss memadai (>=60x60)", f"{ab.w}x{ab.h}")
ok_all &= check(0.30 <= AA.SCALE <= 1.0,
                "SCALE tunggal untuk semua jalur", f"{AA.SCALE}")

# tinggi di lane hero (pipeline menormalkan)
lane = pygame.Surface((400, 400), pygame.SRCALPHA)
lh = _ProbeEntity("ancient_apparition", 200, 200)
render_hero("ancient_apparition", lane, lh, 200, 200)
lb = lane.get_bounding_rect(min_alpha=8)
ok_all &= check(50 <= lb.height <= 110,
                "tinggi di lane hero (pipeline auto-normalisasi)",
                f"{lb.w}x{lb.h} scale={scale:.3f}")

# ── 2. keunikan frame (animasi hidup, floating inertia) ───────────
idle_frames = {pygame.image.tobytes(rig_frame("idle", i * 0.52), "RGBA")
               for i in range(8)}
walk_frames = {pygame.image.tobytes(rig_frame("walk", i * 0.785), "RGBA")
               for i in range(8)}
atk_frames = {pygame.image.tobytes(rig_frame("attack", 1.0, i / 9.0), "RGBA")
              for i in range(10)}
ok_all &= check(len(idle_frames) == 8, "idle: 8 frame unik (living idle float)",
                f"{len(idle_frames)}/8")
ok_all &= check(len(walk_frames) == 8, "walk: 8 frame unik (floating glide)",
                f"{len(walk_frames)}/8")
ok_all &= check(len(atk_frames) >= 9, "attack: >=9 pose unik (multi-keyframe)",
                f"{len(atk_frames)}/10")

# frame IMPACT punya siluet berbeda dari tetangganya
imp = rig_frame("attack", 1.0, 0.44)
pre = rig_frame("attack", 1.0, 0.35)
ok_all &= check(pygame.image.tobytes(imp, "RGBA")
                != pygame.image.tobytes(pre, "RGBA"),
                "frame IMPACT (ap=0.44) berbeda dari wind-through")

# ── 3. portrait LOD lebih kaya ───────────────────────────────────
port = rig_frame("idle", 0.8, detail=True)
norm = rig_frame("idle", 0.8, detail=False)
nc, pc = len(colors_of(norm)), len(colors_of(port))
ok_all &= check(pc > nc, "portrait LOD lebih banyak warna", f"{nc} -> {pc}")
ok_all &= check(nc >= 100, "kepadatan warna rig (ramp + hue shift)", f"{nc}")

# ── 4. palet material sampai ke render final ─────────────────────
pal = AA.PALETTE
got = colors_of(norm)
for key in ("ice_mid", "cyan_bright", "frost_dark", "void_deep", "crown_dark"):
    ok_all &= check(pal[key] in got, f"swatch {key}", str(pal[key]))

# ── 5. jangkar tanah + kepala di zona atas ───────────────────────
ax, ay = 170, 170
ground = ay + int(AA.GROUND_DY / AA.SCALE)
plume_ok = any(norm.get_at((x, min(339, ground))).a > 30
               for x in range(ax - 40, ax + 41))
ok_all &= check(plume_ok, "kabut/wisps menapak di garis tanah")
head_ok = any(norm.get_at((ax + dx, ay + dy)).a > 150
              for dx in range(-20, 21) for dy in range(-70, -40))
ok_all &= check(head_ok, "kepala kristal ada di zona atas rig")

# ── 6. kosakata FX v2 hadir ──────────────────────────────────────
for helper in ("_fx_scale", "_ring_r", "_spark_star", "_chevron",
               "_dashed_ring", "_jagged_crack", "_tuft_points", "_static",
               "_dither_dots", "_world_to_local", "_mix", "_hash01"):
    ok_all &= check(callable(getattr(AA, helper, None)), f"helper {helper}")

# nama publik lama tetap ada (kompatibilitas)
LEGACY = ("PALETTE", "HAS_AACIRCLE", "_clamp", "_aacircle", "_aaline",
          "_poly", "_ellipse", "_rect", "_target_position",
          "IceShardProjectile", "IceBoltProjectile", "FrostBeam",
          "_detect_moving", "_update_attack_anim", "_manage_projectiles",
          "_spawn_ice_shard", "_spawn_ice_bolt", "_spawn_frost_beam",
          "draw_apparition", "draw_ancient_apparition", "draw_boss",
          "_draw_aa_idle", "_draw_aa_walk", "_draw_aa_attack",
          "_draw_aa_casting", "_draw_aa_body", "_draw_aa_body_raw",
          "_masterwork_finish", "_draw_ice_skirt", "_draw_ice_torso",
          "_draw_aa_head", "_draw_ice_crown", "_draw_idle_arms",
          "_draw_casting_arms", "_draw_attack_arms",
          "_draw_ice_arm_segment", "_draw_ice_claw",
          "_draw_body_sparkles", "_draw_ice_wisps", "_draw_shadow",
          "_draw_frost_aura", "_draw_ground_frost", "_draw_cast_flash",
          "_draw_ice_vortex_ground", "_draw_ice_vortex",
          "_draw_cold_feet_ground", "_draw_cold_feet_spikes",
          "_handle_skill_projectiles", "_draw_snowflake",
          "_draw_ice_shard", "_draw_frost_crystal_spike")
missing = [n for n in LEGACY if not hasattr(AA, n)]
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
t_idle = bench_med(lambda: AA.draw_ancient_apparition(scratch, pb, 260, 260))
pw = boss_probe(ax=260, ay=260)
pw._aa_last_x, pw._aa_last_y = 258.0, 260.0
t_walk = bench_med(lambda: AA.draw_ancient_apparition(scratch, pw, 260, 260))
pa = boss_probe(ax=260, ay=260, _aa_attack_active=True,
                _aa_attack_progress=0.44)
t_atk = bench_med(lambda: AA.draw_ancient_apparition(scratch, pa, 260, 260))
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
    AA.draw_ancient_apparition(s, h, cx, cy)
    return s, cx, cy


def count_fx(s, cx, cy, rmin=0, rmax=10 ** 6):
    """Piksel es menyala (FX) di annulus [rmin, rmax] dari jangkar."""
    n = 0
    for y in range(0, s.get_height(), 2):
        for x in range(0, s.get_width(), 2):
            d = math.hypot(x - cx, y - cy)
            if rmin <= d <= rmax:
                c = s.get_at((x, y))
                if c.a > 50 and c[2] > 110:
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


# siluet badan pembanding "di luar badan"
plain = pygame.Surface((900, 900), pygame.SRCALPHA)
AA.draw_ancient_apparition(plain, boss_probe(ax=450, ay=450), 450, 450)
body_bb = plain.get_bounding_rect(min_alpha=100)
BODY_R = max(body_bb.width, body_bb.height) / 2.0
print(f"[i] radius siluet badan (arena) ~= {BODY_R:.0f} px")

# Q Ice Vortex: telegraph 80 px dunia di TARGET (fs=0.5 -> 160 px canvas)
s, cx, cy = render_skill("q", 30, fs=0.5, W=900, tdx=95, tdy=-20)
tx, ty = AA._target_position(
    boss_probe(ax=cx, ay=cy, _render_scale=0.5,
               target=_NS(x=float(cx + 95), y=float(cy - 20), alive=True)),
    cx, cy)
hits, total = hits_ring(s, 160, tx, ty)
ok_all &= check(hits > 90,
                "Q: ring AOE tepat 160px canvas (=80 dunia, fs=0.5) di target",
                f"{hits}/{total}")
q_fx = count_fx(s, cx, cy, BODY_R, 320)
ok_all &= check(q_fx > 100, "Q: FX di luar siluet badan (vortex + blizzard)",
                f"{q_fx} px")

# W Frost Beam: beam laser es dari caster ke target
s, cx, cy = render_skill("w", 27, fs=0.5, W=900, tdx=150, tdy=-20)
w_fx = count_fx(s, cx, cy, BODY_R, 320)
ok_all &= check(w_fx > 120, "W: FX di luar siluet badan (beam laser + particles)",
                f"{w_fx} px")

# E Ice Bolt: barrage proyektil kristal es
s, cx, cy = render_skill("e", 30, fs=0.5, W=900, tdx=150, tdy=-20)
e_fx = count_fx(s, cx, cy, BODY_R, 320)
ok_all &= check(e_fx > 100, "E: FX di luar siluet badan (shard volley + sonic booms)",
                f"{e_fx} px")

# R Cold Feet: telegraph 80 px dunia di TARGET (fs=0.5 -> 160 px canvas)
s, cx, cy = render_skill("r", 70, fs=0.5, W=900, tdx=95, tdy=-20)
tx, ty = AA._target_position(
    boss_probe(ax=cx, ay=cy, _render_scale=0.5,
               target=_NS(x=float(cx + 95), y=float(cy - 20), alive=True)),
    cx, cy)
hits, total = hits_ring(s, 160, tx, ty)
ok_all &= check(hits > 90,
                "R: ring AOE tepat 160px canvas (=80 dunia, fs=0.5) di target",
                f"{hits}/{total}")
r_fx = count_fx(s, cx, cy, BODY_R, 400)
ok_all &= check(r_fx > 180, "R: FX di luar siluet badan (glacier spires eruption)",
                f"{r_fx} px")

# world-space: FX ikut membesar saat _render_scale mengecil
a1, _, _ = render_skill("r", 54, fs=1.0, W=1000)
a2, _, _ = render_skill("r", 54, fs=0.5, W=1000)
b1 = a1.get_bounding_rect(min_alpha=30)
b2 = a2.get_bounding_rect(min_alpha=30)
ok_all &= check(b2.width > b1.width * 1.3,
                "FX world-space: mengembang saat _render_scale=0.5",
                f"{b1.width} -> {b2.width}")
ok_all &= check(abs(AA._fx_scale(_NS(_render_scale=0.2)) - 2.6) < 1e-6,
                "cap _fx_scale = 2.6", f"{AA._fx_scale(_NS(_render_scale=0.2))}")

# 3 tahap per skill benar-benar berbeda (aktivasi / steady / telegraph/erupsi)
for skill, dur in AA.SKILL_DUR.items():
    sigs = set()
    for timer in (dur - 4, int(dur * 0.6), 6):
        ss, _, _ = render_skill(skill, timer, W=620)
        sigs.add(pygame.image.tobytes(ss, "RGBA"))
    ok_all &= check(len(sigs) == 3, f"{skill.upper()}: 3 tahap FX berbeda",
                    f"{len(sigs)}/3")

# durasi FX == durasi AI
AI = {"q": 60, "w": 45, "e": 50, "r": 90}
ok_all &= check(AA.SKILL_DUR == AI, "SKILL_DUR == durasi AI level 3",
                str(AA.SKILL_DUR))
ok_all &= check(AA.SKILL_RADIUS == {"q": 80, "w": 65, "e": 70, "r": 80},
                "SKILL_RADIUS == radius gameplay", str(AA.SKILL_RADIUS))

# timing skill
for skill, t in (("q", 36), ("w", 27), ("e", 30), ("r", 54)):
    surf = pygame.Surface((528, 528), pygame.SRCALPHA)
    hero = boss_probe(ax=264, ay=284, active_skill=skill,
                      active_skill_timer=t,
                      target=_NS(x=390.0, y=260.0, alive=True),
                      _render_scale=0.72)
    ms = bench_med(lambda: AA.draw_ancient_apparition(surf, hero, 264, 284), 20, 7)
    print(f"[i] skill {skill}: {ms:.2f} ms/frame (median, 528x528)")
    ok_all &= check(ms <= 3.5, f"skill {skill} dalam budget", f"{ms:.2f} ms")

# tidak ada aset
src = open(os.path.join(ROOT, "bosses", "level3.py")).read()
ok_all &= check("pygame.image.load" not in src,
                "100% prosedural (tanpa pygame.image.load)")


# ═══════════════════════ PREVIEW SHEETS ══════════════════════════
font_title = pygame.font.Font(None, 44)
font_label = pygame.font.Font(None, 30)
font_small = pygame.font.Font(None, 21)
ACCENT = (140, 225, 255)
SUB = (180, 220, 245)
EDGE = (40, 110, 160)


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


# ── 1. review sheet ──
W, H = 1400, 860
sheet = pygame.Surface((W, H))
sheet.fill((6, 10, 18))
sheet.blit(font_title.render(
    "ANCIENT APPARITION v2 - PIXEL MASTERWORK + SKILL FX", True, ACCENT), (36, 22))
sheet.blit(font_small.render(
    "100% prosedural • rig native 1.5x • ramp 5-band hue shift • selout • "
    "siluet kristal es • specular cluster • dither • FX world-space "
    "(_fx_scale cap 2.6) • Q=80 / W=65 / E=70 / R=80 px dunia", True, SUB), (38, 66))

cards = (
    ("IDLE / ASTRAL FLOAT", dict(action="idle", phase=1.25)),
    ("WALK / GLACIAL GLIDE", dict(action="walk", phase=2.4)),
    ("ATTACK (SHARD CAST)", dict(action="attack", phase=1.0, progress=.44)),
    ("R — COLD FEET (GLACIER)", dict(skill="r", timer=54)),
)
for i, (label, kw) in enumerate(cards):
    x = 28 + i * 340
    panel = pygame.Rect(x, 100, 322, 600)
    pygame.draw.rect(sheet, (10, 20, 34), panel, border_radius=12)
    pygame.draw.rect(sheet, EDGE, panel, 2, border_radius=12)
    sheet.blit(font_label.render(label, True, (235, 248, 255)), (x + 16, 116))
    native = pygame.Surface((340, 340), pygame.SRCALPHA)
    if "skill" in kw:
        h = boss_probe(ax=170, ay=190, active_skill=kw["skill"],
                       active_skill_timer=kw["timer"],
                       target=_NS(x=250.0, y=170.0, alive=True))
        AA.draw_ancient_apparition(native, h, 170, 190)
        draw_native(sheet, panel.inflate(-10, -66), native, 1.4, 0, 30)
    else:
        AA._draw_aa_body_raw(native, 170, 190, 1, kw.get("phase", 0),
                             kw["action"], kw.get("progress", 0.0))
        draw_native(sheet, panel.inflate(-10, -66), native, 1.4, 0, 30)

notes = (
    "inti kosmik + mahkota 5 tanduk • kabut permafrost",
    "inersia melayang • 4 orbit kristal mengambang",
    "smear kristal es • proyektil intan menyala",
    "lingkaran 12 menara es meletus di target",
)
for j, text in enumerate(notes):
    sheet.blit(font_small.render(text, True, (160, 210, 240)),
               (44 + j * 340, 712))
sheet.blit(font_small.render(
    f"rig native {bb.w}x{bb.h} px  •  bbox arena {ab.w}x{ab.h} px  •  "
    f"warna arena {nc} / portrait {pc}  •  "
    f"idle {t_idle:.2f} ms / attack {t_atk:.2f} ms (cache-miss)",
    True, (140, 180, 210)), (44, 760))
out1 = os.path.join(ROOT, "docs", "ancient_apparition_v2_review.png")
pygame.image.save(sheet, out1)
print(out1)

# ── 2. animation strip ──
SW, SH = 1400, 900
strip = pygame.Surface((SW, SH))
strip.fill((6, 10, 18))
strip.blit(font_title.render("ANCIENT APPARITION v2 - PROSEDURAL ANIMATION RIG", True,
                             ACCENT), (36, 22))
strip.blit(font_small.render(
    "tiap frame dihitung dari fase float + orbital shard math + living breath; "
    "attack = multi-keyframe dengan frame IMPACT di ap=0.44",
    True, SUB), (38, 66))
rows = (("IDLE / FLOAT", 6, "idle"),
        ("WALK / GLIDE", 8, "walk"),
        ("ATTACK / SHARD CAST", 10, "attack"))
for row, (label, count, action) in enumerate(rows):
    top = 108 + row * 262
    strip.blit(font_label.render(label, True, ACCENT), (36, top + 66))
    pygame.draw.line(strip, (40, 90, 130), (35, top + 100),
                     (1364, top + 100), 1)
    for i in range(count):
        native = pygame.Surface((190, 240), pygame.SRCALPHA)
        phase = i / count * math.tau
        progress = i / max(1, count - 1)
        AA._draw_aa_body_raw(native, 95, 150, 1, phase, action, progress)
        fx = 190 + i * 118
        strip.blit(native, (fx, top - 20))
out2 = os.path.join(ROOT, "docs", "ancient_apparition_v2_anim_strip.png")
pygame.image.save(strip, out2)
print(out2)

# ── 3. in-game size ──
GW, GH = 1200, 420
game = pygame.Surface((GW, GH))
game.fill((16, 22, 32))
for gy in range(0, GH, 40):
    pygame.draw.line(game, (22, 30, 44), (0, gy), (GW, gy), 1)
pygame.draw.line(game, (40, 60, 90), (0, 330), (GW, 330), 3)
game.blit(font_title.render(
    "UKURAN ASLI DI ARENA (pipeline cache hero + lighting + outline)", True,
    (235, 248, 255)), (30, 18))
poses = (
    ("idle", 0, 0.0, None), ("walk", 1.9, 0.0, None),
    ("attack", 0, 0.44, None), ("ice_vortex", 1.25, 0.0, "q"),
    ("cold_feet", 1.25, 0.0, "r"),
)
xpos = 130
for i, (name, ph, prog, skill) in enumerate(poses):
    hero = _ProbeEntity("ancient_apparition", xpos, 300)
    hero.pulse = ph
    hero.team = "blue" if i % 2 == 0 else "red"
    if prog:
        hero._aa_attack_active = True
        hero._aa_attack_progress = prog
        hero.timer = 1
        hero._aa_prev_timer = 0
    if skill:
        hero.active_skill = skill
        hero.active_skill_timer = 30 if skill == "q" else 50
        hero.target = _ProbeEntity("dummy", xpos + 90, 292)
        hero.target.alive = True
    render_hero("ancient_apparition", game, hero, xpos, 300)
    game.blit(font_small.render(name, True, (210, 235, 250)),
              (xpos - 40, 330))
    xpos += 210
out3 = os.path.join(ROOT, "docs", "ancient_apparition_v2_ingame.png")
pygame.image.save(game, out3)
print(out3)

# ── 4. skill FX sheet: 4 skill x 3 tahap ──
KW, KH = 1500, 1160
sk = pygame.Surface((KW, KH))
sk.fill((6, 10, 18))
sk.blit(font_title.render(
    "ANCIENT APPARITION v2 - SKILL FX MEWAH (world-space, 100% prosedural)", True,
    ACCENT), (36, 22))
sk.blit(font_small.render(
    "Q Ice Vortex (AOE 80, 60f) • W Frost Beam (line AOE 65, 45f) • "
    "E Ice Bolt (shard barrage 70, 50f) • R Cold Feet (erupsi 12 menara es 80, 90f) — "
    "tiap skill 3 tahap: AKTIVASI / STEADY / TELEGRAPH/ERUPSI", True, SUB), (38, 66))

skill_cards = (
    ("Q - ICE VORTEX", "q", (10, 22, 36),
     ((56, "aktivasi"), (36, "blizzard tornado"), (6, "dissipation"))),
    ("W - FROST BEAM", "w", (8, 24, 40),
     ((41, "charging orb"), (27, "laser beam fire"), (6, "frost mist"))),
    ("E - ICE BOLT", "e", (12, 20, 38),
     ((46, "shard crest"), (30, "projectile barrage"), (6, "impact burst"))),
    ("R - COLD FEET (ULT)", "r", (14, 26, 44),
     ((86, "telegraph ring"), (54, "12 glacier spires"), (6, "permafrost vapor"))),
)
for ci, (label, skill, panel_col, stages) in enumerate(skill_cards):
    col_x = 28 + ci * 368
    for si, (timer, stage) in enumerate(stages):
        y0 = 100 + si * 350
        panel = pygame.Rect(col_x, y0, 348, 330)
        pygame.draw.rect(sk, panel_col, panel, border_radius=12)
        pygame.draw.rect(sk, EDGE, panel, 2, border_radius=12)
        sk.blit(font_small.render(f"{label}  t={timer} ({stage})", True,
                                  (235, 248, 255)), (col_x + 14, y0 + 12))
        native = pygame.Surface((620, 620), pygame.SRCALPHA)
        h = boss_probe(ax=310, ay=330, active_skill=skill,
                       active_skill_timer=timer,
                       target=_NS(x=440.0, y=300.0, alive=True))
        AA.draw_ancient_apparition(native, h, 310, 330)
        scaled = pygame.transform.scale(native, (336, 336))
        old = sk.get_clip()
        sk.set_clip(panel.inflate(-6, -34))
        sk.blit(scaled, (col_x + 6, y0 + 30))
        sk.set_clip(old)
out4 = os.path.join(ROOT, "docs", "ancient_apparition_v2_skills.png")
pygame.image.save(sk, out4)
print(out4)

# ── 5. before / after (snapshot v1 di tools/_ancient_apparition_v1_snapshot.py) ──
def load_old_ns():
    path = os.path.join(ROOT, "tools", "_ancient_apparition_v1_snapshot.py")
    spec = importlib.util.spec_from_file_location("_ancient_apparition_v1", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._NS_ancient_apparition


BW, BH = 1400, 720
ba = pygame.Surface((BW, BH))
ba.fill((6, 10, 18))
ba.blit(font_title.render(
    "ANCIENT APPARITION — BEFORE (v1)  vs  AFTER (v2 masterwork + skill FX)", True,
    ACCENT), (36, 22))
ba.blit(font_small.render(
    "ukuran layar dikunci sekelas true boss level-3 • yang naik: kepadatan "
    "pixel-art kristal es (rig native 1.5x) + telegraph world-space Q80/W65/E70/R80",
    True, SUB), (38, 66))

Old = None
try:
    Old = load_old_ns()
except Exception as e:
    print(f"[i] before/after dilewati: {e}")

if Old is not None:
    cols = (
        ("v1 - idle", None, None), ("v1 - attack", None, 0.44),
        ("v1 - R cold feet", "r", None),
        ("v2 - idle", None, None), ("v2 - attack", None, 0.44),
        ("v2 - R cold feet", "r", None),
    )
    for i, (label, skill, prog) in enumerate(cols):
        x = 24 + i * 228
        panel = pygame.Rect(x, 100, 216, 540)
        pygame.draw.rect(ba, (10, 20, 32), panel, border_radius=10)
        pygame.draw.rect(ba, EDGE, panel, 2, border_radius=10)
        ba.blit(font_small.render(label, True, (235, 248, 255)), (x + 12, 112))

        native = pygame.Surface((400, 400), pygame.SRCALPHA)
        is_v1 = i < 3
        NS = Old if is_v1 else AA

        if skill == "r":
            h = boss_probe(ax=200, ay=220, active_skill="r",
                           active_skill_timer=54,
                           target=_NS(x=290.0, y=200.0, alive=True))
            NS.draw_ancient_apparition(native, h, 200, 220)
        elif prog is not None:
            if is_v1:
                h = boss_probe(ax=200, ay=220, _aa_attack_active=True,
                               _aa_attack_progress=prog)
                NS.draw_ancient_apparition(native, h, 200, 220)
            else:
                NS._draw_aa_body_raw(native, 200, 220, 1, 1.0, "attack", prog)
        else:
            if is_v1:
                h = boss_probe(ax=200, ay=220)
                NS.draw_ancient_apparition(native, h, 200, 220)
            else:
                NS._draw_aa_body_raw(native, 200, 220, 1, 1.25, "idle", 0.0)

        scaled = pygame.transform.scale(native, (208, 208))
        old = ba.get_clip()
        ba.set_clip(panel.inflate(-6, -40))
        ba.blit(scaled, (x + 4, 180))
        ba.set_clip(old)

out5 = os.path.join(ROOT, "docs", "ancient_apparition_v2_before_after.png")
pygame.image.save(ba, out5)
print(out5)

print("\n" + ("=" * 60))
if ok_all:
    print("ALL AUDIT CHECKS PASSED — ANCIENT APPARITION v2 MASTERWORK")
else:
    print("SOME AUDIT CHECKS FAILED")
    sys.exit(1)
