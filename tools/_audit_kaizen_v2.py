#!/usr/bin/env python3
"""Audit + preview sheet untuk Kaizen renderer masterwork v2 + skill FX v2.1.

Mengukur hal yang sebelumnya hanya bisa dinilai mata (standar _audit_thorne_v2):
  - skala terukur & ukuran akhir di layar (pipeline heroes/__init__)
  - bbox tiap pose, jumlah warna unik (idle vs portrait LOD)
  - keunikan frame antar siklus (bukan sticker translation)
  - waktu render per pose + skill (budget cache-miss ~3.5 ms)
  - cakupan FX skill DI LUAR siluet badan (efek harus terlihat)
  - radius telegraph TEPAT dalam px dunia (E=100, R=150) pada 2 skala
    — marker angular (tick + bracket), bukan cincin kontinu
  - before/after melawan rig baseline git
Menghasilkan:
  - docs/kaizen_v2_review.png      (kartu pose besar, 2x)
  - docs/kaizen_v2_anim_strip.png  (film strip idle/walk/attack)
  - docs/kaizen_v2_ingame.png      (ukuran asli di arena, tim biru/merah)
  - docs/kaizen_v2_skills.png      (4 skill x 3 tahap timer, world-space)
  - docs/kaizen_v2_before_after.png (rig baseline git vs rig v2)
"""
import math
import os
import subprocess
import sys
import time
from collections import Counter
from types import SimpleNamespace as _NS

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import heroes
from heroes import _ProbeEntity, render_hero, _get_hero_scale
from heroes._bundle import _NS_kaizen as K

# Audit ini menilai FALLBACK CANVAS murni (rig + smear + sabit in-canvas).
# Lapisan hidup 60fps (heroes/kaizen_fx.py) dimatikan supaya draw_kaizen
# tidak meng-attach director dan menekan smear yang justru mau diaudit.
try:
    from heroes import kaizen_fx as _kzfx
    _kzfx.KAIZEN_FX_ENABLED = False
    K._LIVE_MOD = False
except Exception:
    pass

AX, AY = 170, 175          # anchor rig v2 di kartu 340 px (telapak +60)


def colors_of(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def elite_frame(action, phase, progress=0.0, facing=1, gale=False,
                storm=False, size=340, detail=False):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    K._draw_kaizen_elite(s, size // 2, size // 2 + 5, facing, phase, action,
                         progress, detail, gale, storm)
    return s


def check(cond, label, extra=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return cond


ok_all = True

# ── 1. skala & ukuran layar ──────────────────────────────────────
scale = _get_hero_scale("kaizen")
body = elite_frame("idle", 1.25)
bb = body.get_bounding_rect(min_alpha=8)
ok_all &= check(bb.height >= 150 and bb.width >= 120,
                "bbox idle native (rig ~1.5x)", f"{bb.w}x{bb.h}")
screen_h = bb.height * scale
ok_all &= check(55 <= screen_h <= 95,
                "tinggi badan di layar (ternormalisasi pipeline)",
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
port = pygame.Surface((340, 340), pygame.SRCALPHA)
K._draw_kaizen_elite(port, 170, 175, 1, .8, "idle", 0.0, True)
norm = elite_frame("idle", .8)
nc, pc = len(colors_of(norm)), len(colors_of(port))
ok_all &= check(pc > nc, "portrait LOD lebih banyak warna", f"{nc} -> {pc}")

# ── 4. palet material sampai ke render final ─────────────────────
pal = K.PALETTE
got = colors_of(norm)
for key in ("saya_mid", "gold_light", "cloth_high", "steel_shine",
            "scarf_high", "eye_iris", "hair_shine", "wrap_mid",
            "saya_light", "leather_mid"):
    ok_all &= check(pal[key] in got, f"swatch {key}", str(pal[key]))

# ── 5. mata + wajah terbaca (mahkota tidak menutupi) ─────────────
eye_here = any(norm.get_at((170 + dx, 175 + dy)).a > 200
               for dx in range(7, 13) for dy in range(-73, -64))
ok_all &= check(eye_here, "mata terbaca di zona wajah")
foot_here = norm.get_at((170 + 17, 175 + 60))
ok_all &= check(foot_here.a > 150, "telapak depan menapak y=+60")

# ── 6. timing (budget cache-miss ~3.5 ms) ────────────────────────
def bench(fn, n=30):
    fn()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n * 1000

t_idle = bench(lambda: K._draw_kaizen_elite(norm, 170, 175, 1, 1.1, "idle"))
t_walk = bench(lambda: K._draw_kaizen_elite(norm, 170, 175, 1, 1.1, "walk"))
t_atk = bench(lambda: K._draw_kaizen_elite(norm, 170, 175, 1, .5, "attack", .5))
t_full = bench(lambda: K.draw_kaizen(norm, _ProbeEntity("kaizen", 170, 175),
                                     170, 175))
print(f"[i] render ms: idle={t_idle:.2f} walk={t_walk:.2f} "
      f"attack={t_atk:.2f} draw_kaizen={t_full:.2f}")

# ── 7. skill FX: world-space, mewah, dan terukur ─────────────────
def _render_skill(skill, timer, fs=None, W=900):
    s = pygame.Surface((W, W), pygame.SRCALPHA)
    h = _ProbeEntity("kaizen", W // 2, W // 2 + 40)
    h.pulse = 1.3
    h.active_skill = skill
    h.active_skill_timer = timer
    h.target = _NS(x=W // 2 + 140, y=W // 2 + 25, alive=True)
    if fs:
        h._render_scale = fs
    K.draw_kaizen(s, h, W // 2, W // 2 + 40)
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

_windx = lambda c: c.a > 100 and c[2] > 190 and c[1] > 150 and c[0] < 190

# W: rune ring + dinding harus keluar dari siluet badan, dan world-space
s = _render_skill("w", 60)
ok_all &= check(_count(s, _windx, 60, 130) > 40,
                "W: dinding/rune sian di luar badan",
                str(_count(s, _windx, 60, 130)))
s = _render_skill("w", 60, fs=0.5)
ok_all &= check(_count(s, _windx, 60, 230) > 40,
                "W: efek world-space saat di-scale hero",
                str(_count(s, _windx, 60, 230)))

# R: funnel + retakan + puing di luar badan
s = _render_skill("r", 30)
ok_all &= check(_count(s, _windx, 60, 200) > 60,
                "R: funnel/puing sian di luar badan",
                str(_count(s, _windx, 60, 200)))

# E: marker AOE angular mencapai 100 world-px (=200 canvas, fs=0.5)
# Spoke-reach: tick/bracket menandai perimeter walau ada celah antar-tick.
s = _render_skill("e", 30, fs=0.5)
_cx, _cy = 450, 520
reach = []
for a in range(0, 360, 2):
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    f = 0
    for rr in range(40, 260):
        x = int(_cx + ca * rr)
        y = int(_cy + sa * rr)
        if 0 <= x < s.get_width() and 0 <= y < s.get_height() \
                and s.get_at((x, y)).a > 40:
            f = rr
    reach.append(f)
near = sum(1 for r in reach if r >= 190)
ok_all &= check(12 <= near <= 80 and 190 <= max(reach) <= 250,
                "E: marker AOE angular mencapai ~200px canvas (=100 dunia, fs=0.5)",
                f"spokes@{190}={near}/180 max={max(reach) if reach else 0}")

# Q: jalur + splat menuju target
s = _render_skill("q", 30)
ok_all &= check(_count(s, _windx, 60, 400) > 25,
                "Q: jalur dash + splat menuju target",
                str(_count(s, _windx, 60, 400)))

# timing skill (budget cache-miss)
# Di game, 1 render per frame dgn timer yang BERKURANG tiap frame
# (cache bucket HERO_SKILL_QUANT=2 -> ~30 render unik / detik,
# cache-miss tiap bucket). Simulasi yang jujur: loop timer turun,
# ukur rata-rata per render cache-miss.
for skill, dur in (("w", 90), ("e", 60), ("r", 100), ("q", 60)):
    surf = pygame.Surface((900, 900), pygame.SRCALPHA)
    hero = _ProbeEntity("kaizen", 450, 490)
    hero.pulse = 1.3
    hero.active_skill = skill
    hero.target = _NS(x=590, y=465, alive=True)
    times = []
    for t in range(dur, 0, -1):          # 1 render per frame nyata
        hero.active_skill_timer = t
        t0 = time.perf_counter()
        K.draw_kaizen(surf, hero, 450, 490)
        times.append(time.perf_counter() - t0)
    ms = sum(times) / len(times) * 1000
    mx = max(times) * 1000
    ok_all &= check(ms < 3.5, f"skill {skill}: budget <3.5 ms "
                    "(rata2 per frame dgn timer jalan)",
                    f"avg={ms:.2f} ms max={mx:.2f} ms")

# ═══════════════════════ PREVIEW SHEETS ══════════════════════════
font_title = pygame.font.Font(None, 44)
font_label = pygame.font.Font(None, 30)
font_small = pygame.font.Font(None, 21)

# ── review sheet ──
W, H = 1400, 860
sheet = pygame.Surface((W, H))
sheet.fill((6, 10, 20))
sheet.blit(font_title.render("KAIZEN v2 - PIXEL MASTERWORK (100% prosedural)",
                             True, (150, 210, 255)), (36, 22))
sheet.blit(font_small.render(
    "rig 1.5x native • ramp hue-shift • selout • tuft silhouette • "
    "scarf inertia • foot solver • 7-keyframe iai + frame IMPACT + smear",
    True, (130, 158, 190)), (38, 66))

cards = (
    ("IDLE / BREATHE", dict(action="idle", phase=1.25)),
    ("WALK / CONTACT", dict(action="walk", phase=2.4)),
    ("IAI STRIKE (impact)", dict(action="attack", phase=1.0, progress=.52)),
    ("STORM ULT (R)", dict(action="idle", phase=1.25, storm=True)),
)
for i, (label, kw) in enumerate(cards):
    x = 28 + i * 340
    panel = pygame.Rect(x, 100, 322, 600)
    pygame.draw.rect(sheet, (10, 21, 30), panel, border_radius=12)
    pygame.draw.rect(sheet, (55, 122, 172), panel, 2, border_radius=12)
    sheet.blit(font_label.render(label, True, (218, 236, 255)), (x + 16, 116))
    native = pygame.Surface((300, 300), pygame.SRCALPHA)
    K._draw_kaizen_elite(native, 150, 158, 1, kw.get("phase", 0),
                         kw["action"], kw.get("progress", 0.0),
                         False, kw.get("gale", False), kw.get("storm", False))
    scaled = pygame.transform.scale(native, (300 * 2, 300 * 2))
    clip = panel.inflate(-10, -66)
    old = sheet.get_clip()
    sheet.set_clip(clip)
    sheet.blit(scaled, (x + 161 - 300, 150))
    sheet.set_clip(old)

notes = ("ponytail tuft + hachimaki • saya lacquer",
         "foot solver • debu tapak • scarf lag",
         "smear sabit 3-band • bintang IMPACT",
         "mata glow • bead menyala • aura badai")
for j, text in enumerate(notes):
    sheet.blit(font_small.render(text, True, (115, 151, 185)),
               (44 + j * 340, 712))
out1 = os.path.join(ROOT, "docs", "kaizen_v2_review.png")
pygame.image.save(sheet, out1)
print(out1)

# ── animation strip ──
SW, SH = 1400, 900
strip = pygame.Surface((SW, SH))
strip.fill((6, 10, 20))
strip.blit(font_title.render("KAIZEN v2 - PROSEDURAL ANIMATION RIG", True,
                             (150, 210, 255)), (36, 22))
strip.blit(font_small.render(
    "setiap frame dihitung ulang dari sendi + fase + inersia kain/rambut",
    True, (130, 158, 190)), (38, 66))
rows = (("IDLE / BREATHE", 6, "idle"),
        ("WALK / CONTACT", 8, "walk"),
        ("ATTACK / IAI + SMEAR", 10, "attack"))
for row, (label, count, action) in enumerate(rows):
    top = 108 + row * 262
    strip.blit(font_label.render(label, True, (130, 199, 255)), (36, top + 66))
    pygame.draw.line(strip, (42, 94, 145), (35, top + 100),
                     (1364, top + 100), 1)
    for i in range(count):
        native = pygame.Surface((170, 190), pygame.SRCALPHA)
        phase = i / count * math.tau
        progress = i / max(1, count - 1)
        K._draw_kaizen_elite(native, 85, 100, 1, phase, action, progress)
        frame = pygame.transform.scale(native, (170, 190))
        fx = 200 + i * 122
        strip.blit(frame, (fx, top))
out2 = os.path.join(ROOT, "docs", "kaizen_v2_anim_strip.png")
pygame.image.save(strip, out2)
print(out2)

# ── in-game size (ukuran sesungguhnya setelah pipeline hero) ──
GW, GH = 1200, 420
game = pygame.Surface((GW, GH))
game.fill((24, 34, 26))
for gy in range(0, GH, 40):                     # grid lane halus
    pygame.draw.line(game, (30, 42, 32), (0, gy), (GW, gy), 1)
pygame.draw.line(game, (56, 74, 52), (0, 330), (GW, 330), 3)  # lane line
game.blit(font_title.render(
    "UKURAN ASLI DI ARENA (pipeline cache hero + lighting + outline)",
    True, (200, 230, 255)), (30, 18))
poses = (
    ("idle", 0, 0.0, None), ("walk", 1.9, 0.0, None),
    ("attack", 0, 0.42, None), ("attack", 0, 0.54, None),
    ("storm idle", 1.25, 0.0, "r"),
)
xpos = 130
for i, (name, ph, prog, skill) in enumerate(poses):
    hero = _ProbeEntity("kaizen", xpos, 300)
    hero.pulse = ph
    hero.team = "blue" if i % 2 == 0 else "red"
    if prog:
        hero._kz_attack_active = True
        hero._kz_attack_progress = prog
        hero.timer = 1  # supaya jalur attacking aktif
        hero._kz_prev_timer = 0
        hero.range = 40
    if skill:
        hero.active_skill = skill
        hero.active_skill_timer = 60
    render_hero("kaizen", game, hero, xpos, 300)
    game.blit(font_small.render(name, True, (210, 210, 190)),
              (xpos - 40, 338))
    xpos += 210
out3 = os.path.join(ROOT, "docs", "kaizen_v2_ingame.png")
pygame.image.save(game, out3)
print(out3)

# ── skill FX sheet: 4 skill x 3 tahap timer (world-space fs=0.45) ──
KW, KH = 1500, 1160
skills_sheet = pygame.Surface((KW, KH))
skills_sheet.fill((6, 10, 20))
skills_sheet.blit(font_title.render(
    "KAIZEN v2 - SKILL FX MEWAH (world-space, 100% prosedural)", True,
    (150, 210, 255)), (36, 22))
skills_sheet.blit(font_small.render(
    "Q Steel Wind • W Wind Wall • E Sweep • R Tornado — "
    "3 tahap timer per skill, _render_scale=0.45 (canvas hero asli)",
    True, (130, 158, 190)), (38, 66))

skill_cards = (
    ("Q - STEEL WIND / DASH", "q", (12, 22, 34)),
    ("W - WIND WALL", "w", (10, 26, 30)),
    ("E - SWEEP AOE", "e", (10, 24, 32)),
    ("R - TORNADO (ULTIMATE)", "r", (14, 18, 36)),
)
stages = ((85, "telegraph/awal"), (45, "aktivasi"), (12, "puncak"))
for ci, (label, skill, panel_col) in enumerate(skill_cards):
    col_x = 28 + ci * 368
    for si, (timer, stage) in enumerate(stages):
        y0 = 100 + si * 350
        panel = pygame.Rect(col_x, y0, 348, 330)
        pygame.draw.rect(skills_sheet, panel_col, panel, border_radius=12)
        pygame.draw.rect(skills_sheet, (55, 122, 172), panel, 2,
                         border_radius=12)
        skills_sheet.blit(
            font_small.render(f"{label}  t={timer} ({stage})", True,
                              (218, 236, 255)), (col_x + 14, y0 + 12))
        h = _ProbeEntity("kaizen", 310, 350)
        h.pulse = 1.3
        h.active_skill = skill
        h.active_skill_timer = timer
        h.target = _NS(x=450, y=320, alive=True)
        h._render_scale = 0.45      # simulasi pipeline hero: fs aktif
        cw = heroes._canvas_size_for(h)   # canvas cache ASLI di game
        native = pygame.Surface((cw, cw), pygame.SRCALPHA)
        cxy = cw // 2
        h.x, h.y = float(cxy), float(cxy + 40)
        K.draw_kaizen(native, h, cxy, cxy + 40)
        scaled = pygame.transform.scale(native, (336, 336))
        old_clip = skills_sheet.get_clip()
        skills_sheet.set_clip(panel.inflate(-6, -34))
        skills_sheet.blit(scaled, (col_x + 6, y0 + 30))
        skills_sheet.set_clip(old_clip)
out4 = os.path.join(ROOT, "docs", "kaizen_v2_skills.png")
pygame.image.save(skills_sheet, out4)
print(out4)

# ── before/after vs baseline git ──
def load_old_ns():
    old = subprocess.run(
        ["git", "show", "4db4712:heroes/_bundle.py"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    lines = old.splitlines(keepends=True)
    start = next(i for i, l in enumerate(lines)
                 if l.startswith("class _NS_kaizen:"))
    end = next(i for i in range(start + 1, len(lines))
               if lines[i].startswith("class _NS_"))
    src = "".join(lines[start:end])
    ns = {"pygame": pygame, "math": math}
    import heroes._bundle as _b
    ns["_skill_outlined_line"] = _b._skill_outlined_line
    ns["_skill_outlined_circle"] = _b._skill_outlined_circle
    exec(compile(src, "old_kaizen", "exec"), ns)
    return ns["_NS_kaizen"]


BW, BH = 1400, 700
ba = pygame.Surface((BW, BH))
ba.fill((6, 10, 20))
ba.blit(font_title.render(
    "KAIZEN - BEFORE (baseline git)  vs  AFTER (v2 masterwork)",
    True, (150, 210, 255)), (36, 22))
ba.blit(font_small.render(
    "rig lama 1.0x (104x112) vs rig v2 1.5x (~179 px native, detail naik) - "
    "sama-sama 100% prosedural", True, (130, 158, 190)), (38, 66))

Old = None
try:
    Old = load_old_ns()
except Exception as e:  # baseline tidak ada -> lewati sheet
    print(f"[i] before/after dilewati: {e}")

if Old is not None:
    cols = (
        ("OLD - idle", "idle", 1.25, 0.0),
        ("OLD - walk", "walk", 2.4, 0.0),
        ("OLD - attack", "attack", 1.0, 0.52),
        ("V2 - idle", "idle", 1.25, 0.0),
        ("V2 - walk", "walk", 2.4, 0.0),
        ("V2 - attack", "attack", 1.0, 0.52),
    )
    for i, (label, action, phase, prog) in enumerate(cols):
        x = 24 + i * 228
        panel = pygame.Rect(x, 100, 216, 520)
        pygame.draw.rect(ba, (10, 18, 28), panel, border_radius=10)
        pygame.draw.rect(ba, (55, 122, 172), panel, 2, border_radius=10)
        ba.blit(font_small.render(label, True, (218, 236, 255)),
                (x + 12, 112))
        native = pygame.Surface((210, 470), pygame.SRCALPHA)
        # Garis tanah disamakan: rig lama telapak +48 (anchor 280),
        # rig v2 telapak +60 (anchor 268) -> keduanya menapak di y=328.
        ay = 280 if i < 3 else 268
        if i < 3:
            h = _ProbeEntity("kaizen", 105, ay)
            h.pulse = phase
            if action == "attack":
                h._kz_attack_progress = prog
                h._kz_attack_active = True
                h.range = 40
                Old._draw_kaizen_attack(native, h, 105, ay)
            elif action == "walk":
                Old._draw_kaizen_walk(native, h, 105, ay)
            else:
                Old._draw_kaizen_idle(native, h, 105, ay)
        else:
            K._draw_kaizen_elite(native, 105, ay, 1, phase, action,
                                 prog, False)
        old_clip = ba.get_clip()
        ba.set_clip(panel.inflate(-6, -34))
        ba.blit(native, (x + 3, 136))
        ba.set_clip(old_clip)
    ba.blit(font_small.render(
        "kiri: baseline 4db4712   |   kanan: v2 (katana sori+tsuba, "
        "hachimaki, sode, foot solver, smear IMPACT)", True,
        (115, 151, 185)), (24, 640))
    out5 = os.path.join(ROOT, "docs", "kaizen_v2_before_after.png")
    pygame.image.save(ba, out5)
    print(out5)

print("SEMUA CEK LOLOS" if ok_all else "ADA CEK GAGAL")
sys.exit(0 if ok_all else 1)
