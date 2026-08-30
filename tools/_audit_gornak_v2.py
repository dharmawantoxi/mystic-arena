#!/usr/bin/env python3
"""Audit + preview sheet untuk Gornak renderer masterwork v2 + FX v2.1.

Mengukur hal yang sebelumnya hanya bisa dinilai mata:
  - skala terukur & ukuran akhir di layar (pipeline heroes/__init__)
  - bbox tiap pose, jumlah warna unik (idle vs portrait LOD)
  - keunikan frame antar siklus (bukan sticker translation)
  - waktu render per pose (budget cache-miss ~3.5 ms)
  - skill Q/W/E/R: world-space (kompensasi 1/_render_scale), mewah, terukur
    E Counterspell = 100 px dunia, R Mana Void = 180 px dunia di CASTER
Menghasilkan:
  - docs/gornak_v2_review.png
  - docs/gornak_v2_anim_strip.png
  - docs/gornak_v2_ingame.png
  - docs/gornak_v2_skills.png
  - docs/gornak_v2_before_after.png

Jalankan:  /home/user/.venv/bin/python tools/_audit_gornak_v2.py
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

import heroes
from heroes import _ProbeEntity, render_hero, _get_hero_scale
from bosses.level1 import _NS_gornak as G


def colors_of(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def rig_frame(action, phase, progress=0.0, facing=1, detail=False,
              size=300, ax=None, ay=None):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    ax = size // 2 if ax is None else ax
    ay = size // 2 + 26 if ay is None else ay
    G._draw_gnk_rig(s, ax, ay, facing, phase, action, progress, detail)
    if action == "attack" and 0.24 <= progress <= 0.92:
        G._draw_crescent_slash(s, ax, ay, facing, phase, progress)
    return s


def check(cond, label, extra=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return cond


ok_all = True

# ── 1. skala & ukuran layar ──────────────────────────────────────
scale = _get_hero_scale("gornak")
body = rig_frame("idle", 1.25)
bb = body.get_bounding_rect(min_alpha=8)
ok_all &= check(bb.height >= 100 and bb.width >= 96,
                "bbox idle native (paritas keluarga, bukan 1.5x boss)",
                f"{bb.w}x{bb.h}")
screen_h = bb.height * scale
ok_all &= check(50 <= screen_h <= 95,
                "tinggi badan di layar (pipeline menormalkan ~70px)",
                f"{screen_h:.1f}px scale={scale:.3f}")
ok_all &= check(scale <= 1.02, "hero tidak di-upscale", f"{scale:.3f}")

# ── 2. keunikan frame (bukan sticker) ────────────────────────────
walk_frames = {pygame.image.tobytes(rig_frame("walk", i * 0.785), "RGBA")
               for i in range(8)}
atk_frames = {pygame.image.tobytes(rig_frame("attack", 0, i / 9.0), "RGBA")
              for i in range(10)}
ok_all &= check(len(walk_frames) == 8, "walk: 8 frame unik",
                f"{len(walk_frames)}")
ok_all &= check(len(atk_frames) == 10, "attack: 10 pose unik",
                f"{len(atk_frames)}/10")

# ── 3. portrait LOD lebih kaya ───────────────────────────────────
port = rig_frame("idle", 0.8, detail=True)
norm = rig_frame("idle", 0.8, detail=False)
nc, pc = len(colors_of(norm)), len(colors_of(port))
ok_all &= check(pc > nc, "portrait LOD lebih banyak warna", f"{nc} -> {pc}")

# ── 4. palet material sampai ke render final ─────────────────────
pal = G.PALETTE
got = colors_of(norm)
for key in ("magic_hot", "magic_mid", "armor_light", "blade_shine",
            "hair_light", "skin_mid"):
    ok_all &= check(pal[key] in got, f"swatch {key}", str(pal[key]))

# ── 5. kaki menapak + mata ───────────────────────────────────────
# Anchor rig_frame = (150, 176)
ax, ay = 150, 176
ground = ay + G.GROUND_DY
feet_ok = any(norm.get_at((x, ground)).a > 150
              for x in range(ax - 30, ax + 31)
              if 0 <= ground < norm.get_height())
ok_all &= check(feet_ok, "telapak menapak di GROUND_DY")
eye_here = any(norm.get_at((ax + dx, ay + dy)).a > 150
               for dx in range(-6, 10) for dy in range(-48, -28)
               if 0 <= ay + dy < 300)
ok_all &= check(eye_here, "kepala/mata ada di zona atas")

# ── 6. kosakata v2.1 ─────────────────────────────────────────────
for helper in ("_fx_scale", "_spark_star", "_chevron", "_dashed_ring",
               "_jagged_crack", "_tuft_points", "_static", "_dither_dots",
               "_ring_r", "_world_to_local"):
    ok_all &= check(callable(getattr(G, helper, None)), f"helper {helper}")

# ── 7. timing (budget cache-miss ~3.5 ms) ────────────────────────
def bench(fn, n=30):
    for _ in range(5):
        fn()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n * 1000


def bench_med(fn, n=20, reps=5):
    fn()
    runs = []
    for _ in range(reps):
        t0 = time.perf_counter()
        for _ in range(n):
            fn()
        runs.append((time.perf_counter() - t0) / n * 1000)
    runs.sort()
    return runs[len(runs) // 2]


scratch = pygame.Surface((300, 300), pygame.SRCALPHA)


def pose_render(action, phase, prog):
    def _r():
        G._draw_gnk_rig(scratch, 150, 176, 1, phase, action, prog, False)
    return _r


t_idle = bench(pose_render("idle", 1.1, 0.0))
t_walk = bench(pose_render("walk", 1.1, 0.0))
t_atk = bench(pose_render("attack", .5, .5))
probe = _NS(boss_type="gornak", boss_class="mini", x=150.0, y=176.0,
            direction=1, facing=1, pulse=1.3, timer=0, attack_cooldown=38,
            active_skill=None, active_skill_timer=0, target=None,
            hurt_flash_timer=0, alive=True, radius=30, is_retreating=False)
t_full = bench_med(lambda: G.draw_gornak(scratch, probe, 150, 176), 20, 9)
print(f"[i] render ms: idle={t_idle:.2f} walk={t_walk:.2f} "
      f"attack={t_atk:.2f} draw_gornak={t_full:.2f} (median)")
ok_all &= check(t_full <= 3.5,
                "budget cache-miss (draw_gornak, termasuk FX ambient)",
                f"{t_full:.2f} ms")

# ── 8. skill FX: world-space, mewah, dan terukur ─────────────────
def _render_skill(skill, timer, fs=None, W=760):
    s = pygame.Surface((W, W), pygame.SRCALPHA)
    h = _NS(boss_type="gornak", boss_class="mini", x=float(W // 2),
            y=float(W // 2 + 40), direction=1, facing=1, pulse=1.3,
            timer=0, attack_cooldown=38, active_skill=skill,
            active_skill_timer=timer, target=_NS(x=W // 2 + 140,
                                                 y=W // 2, alive=True),
            hurt_flash_timer=0, alive=True, radius=30, range=100)
    if fs is not None:
        h._render_scale = fs
    G.draw_gornak(s, h, W // 2, W // 2 + 40)
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


_magic = lambda c: (c.a > 60 and c[2] > 90 and c[0] > 70
                    and c[2] >= c[1] - 10)


def _hits_ring(s, r_px, cx=380, cy=420):
    hits = total = 0
    for a in range(0, 360, 2):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        ok = False
        for dr in (-2, -1, 0, 1, 2):
            x = int(cx + ca * (r_px + dr))
            y = int(cy + sa * (r_px + dr))
            if 0 <= x < s.get_width() and 0 <= y < s.get_height() \
                    and s.get_at((x, y)).a > 30:
                ok = True
                break
        total += 1
        hits += 1 if ok else 0
    return hits, total


# E: ring AOE 100 dunia
s = _render_skill("e", 40, fs=0.5)
hits, total = _hits_ring(s, 200)
ok_all &= check(hits > 90,
                "E: ring AOE tepat di 200px canvas (=100 dunia, fs=0.5)",
                f"{hits}/{total}")
ok_all &= check(_count(s, _magic, 70, 260) > 40,
                "E: FX di luar siluet badan",
                str(_count(s, _magic, 70, 260)))

# R: ring AOE 180 dunia di CASTER (bukan target)
s = _render_skill("r", 50, fs=0.5)
hits, total = _hits_ring(s, 360)
ok_all &= check(hits > 70,
                "R: ring AOE tepat di 360px canvas (=180 dunia, fs=0.5)",
                f"{hits}/{total}")
ok_all &= check(_count(s, _magic, 70, 400) > 40,
                "R: FX di luar siluet badan (caster)",
                str(_count(s, _magic, 70, 400)))

# Q: jalur bolt di luar badan menuju target
s = _render_skill("q", 16)
ok_all &= check(_count(s, _magic, 50, 280) > 20,
                "Q: bolt/trail di luar badan menuju target",
                str(_count(s, _magic, 50, 280)))

# W: departure/arrival ellipse di tanah
s = _render_skill("w", 8)
ok_all &= check(_count(s, _magic, 10, 120) > 15,
                "W: burst blink di sekitar badan",
                str(_count(s, _magic, 10, 120)))

# timing skill (budget cache-miss) - canvas pipeline-ish 528
for skill, t in (("q", 16), ("w", 8), ("e", 40), ("r", 50)):
    surf = pygame.Surface((528, 528), pygame.SRCALPHA)
    hero = _NS(boss_type="gornak", boss_class="mini", x=264.0, y=284.0,
               direction=1, facing=1, pulse=1.3, timer=0, attack_cooldown=38,
               active_skill=skill, active_skill_timer=t,
               target=_NS(x=380, y=270, alive=True),
               hurt_flash_timer=0, alive=True, radius=30, range=100,
               _render_scale=0.70)
    ms = bench_med(lambda: G.draw_gornak(surf, hero, 264, 284), 20, 9)
    print(f"[i] skill {skill}: {ms:.2f} ms/frame (median-of-9, 528x528)")
    ok_all &= check(ms <= 3.5, f"skill {skill} dalam budget",
                    f"{ms:.2f} ms")

# ═══════════════════════ PREVIEW SHEETS ══════════════════════════
font_title = pygame.font.Font(None, 44)
font_label = pygame.font.Font(None, 30)
font_small = pygame.font.Font(None, 21)
ACCENT = (200, 168, 246)
SUB = (176, 158, 190)
EDGE = (120, 72, 168)

# ── review sheet ──
W, H = 1400, 860
sheet = pygame.Surface((W, H))
sheet.fill((6, 7, 16))
sheet.blit(font_title.render(
    "GORNAK v2 - PIXEL MASTERWORK + SKILL FX v2.1", True, ACCENT), (36, 22))
sheet.blit(font_small.render(
    "100% prosedural • ramp 4-5 band • selout • tuft cape • specular cluster • "
    "dither • FX world-space (_fx_scale cap 2.6) • E=100 / R=180 px dunia",
    True, SUB), (38, 66))

cards = (
    ("IDLE / BREATHE", dict(action="idle", phase=1.25)),
    ("WALK / CONTACT", dict(action="walk", phase=2.4)),
    ("SLASH (impact)", dict(action="attack", phase=1.0, progress=.55)),
    ("R — MANA VOID", dict(skill="r", timer=44)),
)
for i, (label, kw) in enumerate(cards):
    x = 28 + i * 340
    panel = pygame.Rect(x, 100, 322, 600)
    pygame.draw.rect(sheet, (18, 12, 32), panel, border_radius=12)
    pygame.draw.rect(sheet, EDGE, panel, 2, border_radius=12)
    sheet.blit(font_label.render(label, True, (255, 236, 255)), (x + 16, 116))
    native = pygame.Surface((300, 300), pygame.SRCALPHA)
    if "skill" in kw:
        h = _NS(boss_type="gornak", x=150.0, y=168.0, direction=1, facing=1,
                pulse=1.15, timer=0, attack_cooldown=38,
                active_skill=kw["skill"], active_skill_timer=kw["timer"],
                target=_NS(x=210.0, y=154.0, alive=True),
                hurt_flash_timer=0, alive=True, radius=30)
        G.draw_gornak(native, h, 150, 168)
    else:
        G._draw_gnk_rig(native, 150, 168, 1, kw.get("phase", 0),
                        kw["action"], kw.get("progress", 0.0), False)
        if kw["action"] == "attack":
            G._draw_crescent_slash(native, 150, 168, 1, kw.get("phase", 0),
                                   kw.get("progress", 0.0))
    scaled = pygame.transform.scale(native, (300 * 2, 300 * 2))
    clip = panel.inflate(-10, -66)
    old = sheet.get_clip()
    sheet.set_clip(clip)
    sheet.blit(scaled, (x + 161 - 300, 150))
    sheet.set_clip(old)

notes = (
    "napas + mohawk krist • rim ungu",
    "foot solver • debu tapak",
    "smear sabit • bintang IMPACT",
    "ring 180 dunia di CASTER",
)
for j, text in enumerate(notes):
    sheet.blit(font_small.render(text, True, (185, 151, 195)),
               (44 + j * 340, 712))
out1 = os.path.join(ROOT, "docs", "gornak_v2_review.png")
pygame.image.save(sheet, out1)
print(out1)

# ── animation strip ──
SW, SH = 1400, 900
strip = pygame.Surface((SW, SH))
strip.fill((6, 7, 16))
strip.blit(font_title.render("GORNAK v2 - PROSEDURAL ANIMATION RIG", True,
                             ACCENT), (36, 22))
strip.blit(font_small.render(
    "setiap frame dihitung ulang dari sendi + fase + ayunan bilah + sudut jubah",
    True, SUB), (38, 66))
rows = (("IDLE / BREATHE", 6, "idle"),
        ("WALK / CONTACT", 8, "walk"),
        ("ATTACK / SLASH", 10, "attack"))
for row, (label, count, action) in enumerate(rows):
    top = 108 + row * 262
    strip.blit(font_label.render(label, True, ACCENT), (36, top + 66))
    pygame.draw.line(strip, (90, 52, 128), (35, top + 100),
                     (1364, top + 100), 1)
    for i in range(count):
        native = pygame.Surface((170, 190), pygame.SRCALPHA)
        phase = i / count * math.tau
        progress = i / max(1, count - 1)
        G._draw_gnk_rig(native, 85, 112, 1, phase, action, progress)
        if action == "attack":
            G._draw_crescent_slash(native, 85, 112, 1, phase, progress)
        fx = 200 + i * 122
        strip.blit(native, (fx, top))
out2 = os.path.join(ROOT, "docs", "gornak_v2_anim_strip.png")
pygame.image.save(strip, out2)
print(out2)

# ── in-game size ──
GW, GH = 1200, 420
game = pygame.Surface((GW, GH))
game.fill((24, 28, 32))
for gy in range(0, GH, 40):
    pygame.draw.line(game, (30, 36, 40), (0, gy), (GW, gy), 1)
pygame.draw.line(game, (56, 64, 72), (0, 330), (GW, 330), 3)
game.blit(font_title.render(
    "UKURAN ASLI DI ARENA (pipeline cache hero + lighting + outline)", True,
    (230, 210, 255)), (30, 18))
poses = (
    ("idle", 0, 0.0, None), ("walk", 1.9, 0.0, None),
    ("attack", 0, 0.52, None), ("counterspell", 1.25, 0.0, "e"),
    ("mana void", 1.25, 0.0, "r"),
)
xpos = 130
for i, (name, ph, prog, skill) in enumerate(poses):
    hero = _ProbeEntity("gornak", xpos, 300)
    hero.pulse = ph
    hero.team = "blue" if i % 2 == 0 else "red"
    if prog:
        hero._gnk_attack_active = True
        hero._gnk_attack_progress = prog
        hero.timer = 1
        hero._gnk_prev_timer = 0
    if skill:
        hero.active_skill = skill
        hero.active_skill_timer = 40 if skill == "e" else 50
        hero.target = _ProbeEntity("dummy", xpos + 90, 292)
        hero.target.alive = True
    render_hero("gornak", game, hero, xpos, 300)
    game.blit(font_small.render(name, True, (210, 210, 190)),
              (xpos - 40, 330))
    xpos += 210
out3 = os.path.join(ROOT, "docs", "gornak_v2_ingame.png")
pygame.image.save(game, out3)
print(out3)

# ── skill FX sheet: 4 skill x 3 tahap timer ──
KW, KH = 1500, 1160
skills_sheet = pygame.Surface((KW, KH))
skills_sheet.fill((6, 7, 16))
skills_sheet.blit(font_title.render(
    "GORNAK v2.1 - SKILL FX MEWAH (world-space, 100% prosedural)", True,
    ACCENT), (36, 22))
skills_sheet.blit(font_small.render(
    "Q Mana Break • W Blink • E Counterspell (AOE 100) • R Mana Void (AOE 180 "
    "di caster) — 3 tahap timer per skill (durasi 40/25/60/90)",
    True, SUB), (38, 66))

skill_cards = (
    ("Q - MANA BREAK", "q", (28, 16, 36),
     ((32, "telegraph"), (18, "bolt"), (6, "impact"))),
    ("W - BLINK", "w", (20, 18, 36),
     ((20, "depart"), (12, "transit"), (4, "arrive"))),
    ("E - COUNTERSPELL", "e", (16, 22, 40),
     ((48, "telegraph"), (30, "dome"), (8, "steady"))),
    ("R - MANA VOID (ULT)", "r", (30, 12, 40),
     ((70, "telegraph"), (44, "pilar"), (12, "drain"))),
)
for ci, (label, skill, panel_col, stages) in enumerate(skill_cards):
    col_x = 28 + ci * 368
    for si, (timer, stage) in enumerate(stages):
        y0 = 100 + si * 350
        panel = pygame.Rect(col_x, y0, 348, 330)
        pygame.draw.rect(skills_sheet, panel_col, panel, border_radius=12)
        pygame.draw.rect(skills_sheet, EDGE, panel, 2, border_radius=12)
        skills_sheet.blit(
            font_small.render(f"{label}  t={timer} ({stage})", True,
                              (255, 236, 255)), (col_x + 14, y0 + 12))
        native = pygame.Surface((560, 560), pygame.SRCALPHA)
        h = _NS(boss_type="gornak", x=280.0, y=330.0, direction=1, facing=1,
                pulse=1.3, timer=0, attack_cooldown=38,
                active_skill=skill, active_skill_timer=timer,
                target=_NS(x=420.0, y=300.0, alive=True),
                hurt_flash_timer=0, alive=True, radius=30, range=100)
        G.draw_gornak(native, h, 280, 330)
        scaled = pygame.transform.scale(native, (336, 336))
        old = skills_sheet.get_clip()
        skills_sheet.set_clip(panel.inflate(-6, -34))
        skills_sheet.blit(scaled, (col_x + 6, y0 + 30))
        skills_sheet.set_clip(old)
out4 = os.path.join(ROOT, "docs", "gornak_v2_skills.png")
pygame.image.save(skills_sheet, out4)
print(out4)

# ── before / after ──
import subprocess


def load_old_ns():
    old = subprocess.run(
        ["git", "show", "cbfc3fd12cc015b8784529690227b4df09fa7cc5:bosses/level1.py"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    lines = old.splitlines(keepends=True)
    start = next(i for i, l in enumerate(lines)
                 if l.startswith("class _NS_gornak:"))
    end = next(i for i in range(start + 1, len(lines))
               if lines[i].startswith("class _NS_"))
    src = "".join(lines[start:end])
    ns = {"pygame": pygame, "math": math, "random": __import__("random")}
    try:
        import lighting as _lighting_mod
        ns["_lighting"] = _lighting_mod
    except Exception:
        ns["_lighting"] = None
    exec(compile(src, "old_gornak", "exec"), ns)
    return ns["_NS_gornak"]


BW, BH = 1400, 700
ba = pygame.Surface((BW, BH))
ba.fill((6, 7, 16))
ba.blit(font_title.render(
    "GORNAK — BEFORE (baseline git)  vs  AFTER (v2 + FX v2.1)", True,
    ACCENT), (36, 22))
ba.blit(font_small.render(
    "bbox keluarga dikunci (bukan 1.5x boss-path) • kepadatan pixel-art + "
    "telegraph world-space E100/R180", True, SUB), (38, 66))

Old = None
try:
    Old = load_old_ns()
except Exception as e:
    print(f"[i] before/after dilewati: {e}")

if Old is not None:
    cols = (
        ("OLD - idle", "idle", 1.25, 0.0, None),
        ("OLD - attack", "attack", 1.0, 0.55, None),
        ("OLD - R void", "idle", 1.15, 0.0, "r"),
        ("V2 - idle", "idle", 1.25, 0.0, None),
        ("V2 - attack", "attack", 1.0, 0.55, None),
        ("V2 - R void", "idle", 1.15, 0.0, "r"),
    )
    for i, (label, action, phase, prog, skill) in enumerate(cols):
        x = 24 + i * 228
        panel = pygame.Rect(x, 100, 216, 520)
        pygame.draw.rect(ba, (16, 12, 28), panel, border_radius=10)
        pygame.draw.rect(ba, EDGE, panel, 2, border_radius=10)
        ba.blit(font_small.render(label, True, (255, 236, 255)),
                (x + 12, 112))
        native = pygame.Surface((216, 470), pygame.SRCALPHA)
        ay = 250
        NS = Old if i < 3 else G
        if skill:
            h = _NS(boss_type="gornak", x=108.0, y=float(ay), direction=1,
                    facing=1, pulse=phase, timer=0, attack_cooldown=38,
                    active_skill=skill, active_skill_timer=44,
                    target=_NS(x=160.0, y=ay - 10, alive=True),
                    hurt_flash_timer=0, alive=True, radius=30)
            NS.draw_gornak(native, h, 108, ay)
        else:
            NS._draw_gnk_rig(native, 108, ay, 1, phase, action, prog, False)
            if action == "attack" and hasattr(NS, "_draw_crescent_slash"):
                NS._draw_crescent_slash(native, 108, ay, 1, phase, prog)
        old_clip = ba.get_clip()
        ba.set_clip(panel.inflate(-6, -34))
        ba.blit(native, (x + 3, 136))
        ba.set_clip(old_clip)
    ba.blit(font_small.render(
        "kiri: baseline cbfc3fd   |   kanan: v2 (selout, tuft, dither, "
        "specular, FX world-space)", True, (185, 151, 195)), (24, 640))
    out5 = os.path.join(ROOT, "docs", "gornak_v2_before_after.png")
    pygame.image.save(ba, out5)
    print(out5)

print("SEMUA CEK LOLOS" if ok_all else "ADA CEK GAGAL")
sys.exit(0 if ok_all else 1)
