#!/usr/bin/env python3
"""Audit + preview sheet untuk Grimjaw renderer masterwork v2.

Mengukur hal yang sebelumnya hanya bisa dinilai mata:
  - skala terukur & ukuran akhir di layar (pipeline heroes/__init__)
  - bbox tiap pose, jumlah warna unik (idle vs portrait LOD)
  - keunikan frame antar siklus (bukan sticker translation)
  - waktu render per pose (budget cache-miss ~3.5 ms)
  - skill Q/W/E/R: world-space (kompensasi 1/_render_scale), mewah, terukur
Menghasilkan:
  - docs/grimjaw_v2_review.png        (kartu pose besar, 2x)
  - docs/grimjaw_v2_anim_strip.png    (film strip idle/walk/attack)
  - docs/grimjaw_v2_ingame.png        (ukuran asli di arena, tim biru/merah)
  - docs/grimjaw_v2_skills.png        (4 skill x 3 tahap timer)
  - docs/grimjaw_v2_before_after.png  (rig lama vs rig v2, dari git baseline)

Jalankan:  /home/user/.venv/bin/python tools/_audit_grimjaw_v2.py
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
from heroes._bundle import _NS_grimjaw as G


def colors_of(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def elite_frame(action, phase, progress=0.0, facing=1, detail=False,
                size=300, anchor=None):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    ax = ay = size // 2 if anchor is None else anchor
    G._draw_grimjaw_elite(s, ax, ay, facing, phase, action, progress,
                          0.0, detail)
    return s


def check(cond, label, extra=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return cond


ok_all = True

# ── 1. skala & ukuran layar ──────────────────────────────────────
scale = _get_hero_scale("grimjaw")
body = elite_frame("idle", 1.25)
bb = body.get_bounding_rect(min_alpha=8)
ok_all &= check(bb.height >= 150 and bb.width >= 70,
                "bbox idle native (rig 1.5x: tinggi ~186, mane ~74)",
                f"{bb.w}x{bb.h}")
screen_h = bb.height * scale
ok_all &= check(60 <= screen_h <= 90,
                "tinggi badan di layar (target ~70px)",
                f"{screen_h:.1f}px scale={scale:.3f}")

# ── 2. keunikan frame (bukan sticker) ────────────────────────────
walk_frames = {pygame.image.tobytes(elite_frame("walk", i * 0.785), "RGBA")
               for i in range(8)}
atk_frames = {pygame.image.tobytes(elite_frame("attack", 0, i / 9.0), "RGBA")
              for i in range(10)}
ok_all &= check(len(walk_frames) == 8, "walk: 8 frame unik",
                f"{len(walk_frames)}")
# Attack Grimjaw BUKAN loop tertutup: frame 0 = stance combat (snap siap
# tempur), frame akhir = kembali ke pose jaga. Ke-10 frame harus unik
# dan frame akhir harus = pose idle (selain combat-glow mata menyala).
ok_all &= check(len(atk_frames) == 10,
                "attack: 10 pose unik (stance->strike->rest)",
                f"{len(atk_frames)}/10")
last = pygame.Surface((300, 300), pygame.SRCALPHA)
G._draw_grimjaw_elite(last, 150, 150, 1, 0, "attack", 1.0, 0.0, False)
idle_ref = elite_frame("idle", 0.0)
ndiff = sum(1 for y in range(300) for x in range(300)
            if last.get_at((x, y)) != idle_ref.get_at((x, y)))
ok_all &= check(ndiff < 120,
                "akhir serang kembali ke pose jaga "
                "(diff hanya combat-glow mata)", f"{ndiff} px")

# ── 3. portrait LOD lebih kaya ───────────────────────────────────
port = pygame.Surface((300, 300), pygame.SRCALPHA)
G._draw_grimjaw_elite(port, 150, 158, 1, .8, "idle", 0.0, 0.0, True)
norm = elite_frame("idle", .8)
nc, pc = len(colors_of(norm)), len(colors_of(port))
ok_all &= check(pc > nc, "portrait LOD lebih banyak warna", f"{nc} -> {pc}")

# ── 4. palet material sampai ke render final ─────────────────────
pal = G.PALETTE
got = colors_of(norm)
for key in ("mask_light", "blood_mid", "gold_mid", "red_mid",
            "fire_mid", "fire_hot", "metal_light", "hair_mid"):
    ok_all &= check(pal[key] in got, f"swatch {key}", str(pal[key]))

# ── 5. coverage mane api di atas kepala ──────────────────────────
warm = 0
for y in range(0, 150):
    for x in range(0, 300):
        c = norm.get_at((x, y))
        if c.a > 200:
            r, g, b = c[:3]
            if r > 130 and g > 40 and b < 120 and r - b > 60:
                warm += 1
ok_all &= check(warm > 400, "mane api ter-cover (px hangat atas)",
                str(warm))

# ── 6. kaki menapak di dasar + mata terbaca ──────────────────────
# (norm di-anchor (150,150) - default elite_frame)
feet_row = norm.get_at((150 + 14, 150 + 68))
eye_here = any(norm.get_at((150 + dx, 150 + dy)).a > 150
               for dx in range(0, 14) for dy in range(-52, -40))
ok_all &= check(feet_row.a > 150, "telapak depan menapak y=+68")
ok_all &= check(eye_here, "mata (mask) ada di posisi kepala")

# ── 7. timing (budget cache-miss ~3.5 ms) ────────────────────────
def bench(fn, n=30):
    # 5x warmup: surface ter-cache (mist/aura/platform/ghost) dibangun
    # sekali, lalu blit murah - budget diukur pada keadaan steady.
    for _ in range(5):
        fn()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n * 1000


def bench_med(fn, n=20, reps=5):
    """Median dari `reps` run - kebal jitter CPU sandbox bersama.

    Dipakai untuk assert budget (satu run acak bisa saja kena
    frekuensi CPU rendah; median mencerminkan beban nyata).
    """
    fn()
    runs = []
    for _ in range(reps):
        t0 = time.perf_counter()
        for _ in range(n):
            fn()
        runs.append((time.perf_counter() - t0) / n * 1000)
    runs.sort()
    return runs[len(runs) // 2]


def pose_render(action, phase, prog):
    def _r():
        G._draw_grimjaw_elite(norm, 150, 158, 1, phase, action, prog)
    return _r

t_idle = bench(pose_render("idle", 1.1, 0.0))
t_walk = bench(pose_render("walk", 1.1, 0.0))
t_atk = bench(pose_render("attack", .5, .5))
probe = _ProbeEntity("grimjaw", 150, 158)
t_full = bench_med(lambda: G.draw_grimjaw(norm, probe, 150, 158), 20, 9)
print(f"[i] render ms: idle={t_idle:.2f} walk={t_walk:.2f} "
      f"attack={t_atk:.2f} draw_grimjaw={t_full:.2f} (median)")
ok_all &= check(t_full <= 3.5,
                "budget cache-miss (draw_grimjaw, termasuk FX ambient)",
                f"{t_full:.2f} ms")

# ── 8. skill FX: world-space, mewah, dan terukur ─────────────────
from types import SimpleNamespace as _NS


def _render_skill(skill, timer, fs=None, W=760):
    s = pygame.Surface((W, W), pygame.SRCALPHA)
    h = _ProbeEntity("grimjaw", W // 2, W // 2 + 40)
    h.pulse = 1.3
    h.active_skill = skill
    h.active_skill_timer = timer
    h.target = _NS(x=W // 2 + 140, y=W // 2, alive=True)
    if fs:
        h._render_scale = fs
    G.draw_grimjaw(s, h, W // 2, W // 2 + 40)
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


# matcher warna sesuai PALETTE v2 (fire_light 248,172,54 / rage_light 240,96,52)
_warm = lambda c: (c.a > 80 and c[0] > 140 and c[0] - c[2] > 70
                   and c[1] < 230)
_heal = lambda c: (c.a > 100 and c[1] > 110 and c[0] < 180
                   and c[1] - c[2] > 30)

# Q: ring AOE 70 dunia harus di 70/fs px canvas (world-space)
s = _render_skill("q", 100, fs=0.5)
hits = total = 0
for a in range(0, 360, 2):                       # 180 sudut
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    ok = False
    for dr in (-1, 0, 1):                        # toleransi lebar ring
        x = int(380 + ca * (140 + dr))
        y = int(420 + sa * (140 + dr))
        if _warm(s.get_at((x, y))):
            ok = True
            break
    total += 1
    hits += 1 if ok else 0
ok_all &= check(hits > 150,
                "Q: ring AOE tepat di 140px canvas (=70 dunia, fs=0.5)",
                f"{hits}/{total}")

# W: rune/ring heal hijau di luar badan, world-space
s = _render_skill("w", 50)
ok_all &= check(_count(s, _heal, 60, 260) > 60,
                "W: rune/ring heal di luar badan",
                str(_count(s, _heal, 60, 260)))
s = _render_skill("w", 50, fs=0.5)
ok_all &= check(_count(s, _heal, 120, 500) > 40,
                "W: efek world-space saat di-scale hero",
                str(_count(s, _heal, 120, 500)))

# E: telegraph api di depan (cone 60 dunia)
s = _render_skill("e", 40)
ok_all &= check(_count(s, _warm, 50, 200) > 40,
                "E: telegraph api di luar badan",
                str(_count(s, _warm, 50, 200)))

# R: slash + ring + marker target
s = _render_skill("r", 45)
ok_all &= check(_count(s, _warm, 55, 300) > 60,
                "R: slash/ring di luar badan",
                str(_count(s, _warm, 55, 300)))

# timing skill (budget cache-miss) - di-render pada ukuran canvas ASLI
# pipeline hero (528x528, skala ~0.40) bukan canvas audit 760, supaya
# angka sesuai beban nyata di arena. Median dari 5 run (anti-jitter).
for skill, t in (("q", 100), ("w", 50), ("e", 40), ("r", 45)):
    surf = pygame.Surface((528, 528), pygame.SRCALPHA)
    hero = _ProbeEntity("grimjaw", 264, 284)
    hero.pulse = 1.3
    hero.active_skill = skill
    hero.active_skill_timer = t
    hero.target = _NS(x=380, y=270, alive=True)
    ms = bench_med(lambda: G.draw_grimjaw(surf, hero, 264, 284), 20, 9)
    print(f"[i] skill {skill}: {ms:.2f} ms/frame (median-of-9, 528x528)")
    ok_all &= check(ms <= 3.5, f"skill {skill} dalam budget",
                    f"{ms:.2f} ms")

# ═══════════════════════ PREVIEW SHEETS ══════════════════════════
font_title = pygame.font.Font(None, 44)
font_label = pygame.font.Font(None, 30)
font_small = pygame.font.Font(None, 21)

# ── review sheet ──
W, H = 1400, 860
sheet = pygame.Surface((W, H))
sheet.fill((6, 10, 20))
sheet.blit(font_title.render("GRIMJAW v2 - PIXEL MASTERWORK (100% prosedural)",
                             True, (255, 205, 120)), (36, 22))
sheet.blit(font_small.render(
    "rig 1.5x native • flame mane 5-layer • mask 5-band • foot solver • "
    "smear sabit • impact star • portrait LOD", True, (176, 158, 130)), (38, 66))

cards = (
    ("IDLE / BREATHE", dict(action="idle", phase=1.25)),
    ("WALK / CONTACT", dict(action="walk", phase=2.4)),
    ("FLAME SLASH (impact)", dict(action="attack", phase=1.0, progress=.55)),
    ("BLADE FURY (Q)", dict(action="spin", phase=1.0, spin=2.0)),
)
for i, (label, kw) in enumerate(cards):
    x = 28 + i * 340
    panel = pygame.Rect(x, 100, 322, 600)
    pygame.draw.rect(sheet, (30, 21, 10), panel, border_radius=12)
    pygame.draw.rect(sheet, (172, 122, 55), panel, 2, border_radius=12)
    sheet.blit(font_label.render(label, True, (255, 236, 218)), (x + 16, 116))
    native = pygame.Surface((300, 300), pygame.SRCALPHA)
    if "spin" in kw:
        G._draw_grimjaw_elite(native, 150, 158, 1, kw.get("phase", 0),
                              kw["action"], 0.0, kw["spin"], False)
    else:
        G._draw_grimjaw_elite(native, 150, 158, 1, kw.get("phase", 0),
                              kw["action"], kw.get("progress", 0.0), 0.0,
                              False)
    scaled = pygame.transform.scale(native, (300 * 2, 300 * 2))
    clip = panel.inflate(-10, -66)
    old = sheet.get_clip()
    sheet.set_clip(clip)
    sheet.blit(scaled, (x + 161 - 300, 150))
    sheet.set_clip(old)

notes = (
    "mane 5 lapis • mask darah",
    "foot solver • debu tapak",
    "smear 12 titik • bintang",
    "spin sweep • bara orbit",
)
for j, text in enumerate(notes):
    sheet.blit(font_small.render(text, True, (185, 151, 115)),
               (44 + j * 340, 712))
out1 = os.path.join(ROOT, "docs", "grimjaw_v2_review.png")
pygame.image.save(sheet, out1)
print(out1)

# ── animation strip ──
SW, SH = 1400, 900
strip = pygame.Surface((SW, SH))
strip.fill((6, 10, 20))
strip.blit(font_title.render("GRIMJAW v2 - PROSEDURAL ANIMATION RIG", True,
                             (255, 205, 120)), (36, 22))
strip.blit(font_small.render(
    "setiap frame dihitung ulang dari sendi + fase + gelombang mane + "
    "sudut bilah", True, (176, 158, 130)), (38, 66))
rows = (("IDLE / BREATHE", 6, "idle"),
        ("WALK / CONTACT", 8, "walk"),
        ("ATTACK / FLAME SLASH", 10, "attack"))
for row, (label, count, action) in enumerate(rows):
    top = 108 + row * 262
    strip.blit(font_label.render(label, True, (255, 199, 130)), (36, top + 66))
    pygame.draw.line(strip, (145, 94, 42), (35, top + 100),
                     (1364, top + 100), 1)
    for i in range(count):
        native = pygame.Surface((170, 190), pygame.SRCALPHA)
        phase = i / count * math.tau
        progress = i / max(1, count - 1)
        G._draw_grimjaw_elite(native, 85, 112, 1, phase, action, progress)
        frame = pygame.transform.scale(native, (170, 190))
        fx = 200 + i * 122
        strip.blit(frame, (fx, top))
out2 = os.path.join(ROOT, "docs", "grimjaw_v2_anim_strip.png")
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
    "UKURAN ASLI DI ARENA (pipeline cache hero + lighting + outline)", True,
    (255, 220, 150)), (30, 18))
poses = (
    ("idle", 0, 0.0, None), ("walk", 1.9, 0.0, None),
    ("attack", 0, 0.42, None), ("attack", 0, 0.55, None),
    ("blade fury", 1.25, 0.0, "q"),
)
xpos = 130
for i, (name, ph, prog, skill) in enumerate(poses):
    hero = _ProbeEntity("grimjaw", xpos, 300)
    hero.pulse = ph
    hero.team = "blue" if i % 2 == 0 else "red"
    if prog:
        hero._gj_attack_active = True
        hero._gj_attack_progress = prog
        hero.timer = 1  # supaya jalur attacking aktif
        hero._gj_prev_timer = 0
    if skill:
        hero.active_skill = skill
        hero.active_skill_timer = 60
    render_hero("grimjaw", game, hero, xpos, 300)
    game.blit(font_small.render(name, True, (210, 210, 190)),
              (xpos - 40, 330))
    xpos += 210
out3 = os.path.join(ROOT, "docs", "grimjaw_v2_ingame.png")
pygame.image.save(game, out3)
print(out3)

# ── skill FX sheet: 4 skill x 3 tahap timer ──
KW, KH = 1500, 1160
skills_sheet = pygame.Surface((KW, KH))
skills_sheet.fill((6, 10, 20))
skills_sheet.blit(font_title.render(
    "GRIMJAW v2 - SKILL FX MEWAH (world-space, 100% prosedural)", True,
    (255, 205, 120)), (36, 22))
skills_sheet.blit(font_small.render(
    "Q Blade Fury • W Healing Ward • E Critical Strike • R Omnislash — "
    "3 tahap timer per skill (durasi visual 180/90/60/90)",
    True, (176, 158, 130)), (38, 66))

# Tahap timer per skill, di dalam SKILL_VISUAL_DURATION (q=180, w=90,
# e=60, r=90) supaya ketiga panel benar-benar beda fase.
skill_cards = (
    ("Q - BLADE FURY", "q", (36, 20, 8), ((140, "awal"), (80, "tengah"), (18, "puncak"))),
    ("W - HEALING WARD", "w", (22, 30, 18), ((70, "awal"), (40, "tengah"), (12, "puncak"))),
    ("E - CRITICAL STRIKE", "e", (34, 22, 12), ((45, "awal"), (30, "tengah"), (8, "puncak"))),
    ("R - OMNISLASH (ULTIMATE)", "r", (30, 12, 10), ((70, "awal"), (40, "tengah"), (12, "puncak"))),
)
for ci, (label, skill, panel_col, stages) in enumerate(skill_cards):
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
        h = _ProbeEntity("grimjaw", 280, 330)
        h.pulse = 1.3
        h.active_skill = skill
        h.active_skill_timer = timer
        h.target = _NS(x=420, y=300, alive=True)
        h._render_scale = 0.45      # simulasi pipeline hero: fs aktif
        G.draw_grimjaw(native, h, 280, 330)
        scaled = pygame.transform.scale(native, (336, 336))
        old = skills_sheet.get_clip()
        skills_sheet.set_clip(panel.inflate(-6, -34))
        skills_sheet.blit(scaled, (col_x + 6, y0 + 30))
        skills_sheet.set_clip(old)
out4 = os.path.join(ROOT, "docs", "grimjaw_v2_skills.png")
pygame.image.save(skills_sheet, out4)
print(out4)

# ── before / after: rig lama (git baseline) vs rig v2 ──
import subprocess


def load_old_ns():
    """Eksekusi _NS_grimjaw versi baseline dari git (tanpa menyimpan file)."""
    old = subprocess.run(
        ["git", "show", "eccbeda:heroes/_bundle.py"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    lines = old.splitlines(keepends=True)
    start = next(i for i, l in enumerate(lines)
                 if l.startswith("class _NS_grimjaw:"))
    end = next(i for i in range(start + 1, len(lines))
               if lines[i].startswith("class _NS_"))
    src = "".join(lines[start:end])
    ns = {"pygame": pygame, "math": math,
          "random": __import__("random")}
    import heroes._bundle as _b
    ns["_skill_outlined_line"] = _b._skill_outlined_line
    ns["_skill_outlined_circle"] = _b._skill_outlined_circle
    exec(compile(src, "old_grimjaw", "exec"), ns)
    return ns["_NS_grimjaw"]


BW, BH = 1400, 700
ba = pygame.Surface((BW, BH))
ba.fill((6, 10, 20))
ba.blit(font_title.render(
    "GRIMJAW — BEFORE (baseline git)  vs  AFTER (v2)", True,
    (255, 205, 120)), (36, 22))
ba.blit(font_small.render(
    "rig lama 1.0x (68px solid) vs rig v2 1.5x (1.5x detail, ~75px layar) — "
    "sama-sama 100% prosedural", True, (176, 158, 130)), (38, 66))

Old = None
try:
    Old = load_old_ns()
except Exception as e:
    # Repo arena di-import dangkal (hanya commit terakhir) - baseline
    # rig v1 (commit eccbeda) tidak ada di history lokal. Sheet
    # before/after dilewati secara informatif, TIDAK dihitung gagal:
    # metrik sebelum/sesudah tetap ter-cover oleh cek rig 1.5x di atas.
    print(f"[i] before/after dilewati (baseline git tidak tersedia "
          f"di history arena): {e}")

if Old is not None:
    cols = (
        ("OLD - idle", "idle", 1.25, 0.0, 0.0),
        ("OLD - attack", "attack", 1.0, 0.55, 0.0),
        ("OLD - spin", "spin", 1.0, 0.0, 2.0),
        ("V2 - idle", "idle", 1.25, 0.0, 0.0),
        ("V2 - attack", "attack", 1.0, 0.55, 0.0),
        ("V2 - spin", "spin", 1.0, 0.0, 2.0),
    )
    for i, (label, action, phase, prog, spin) in enumerate(cols):
        x = 24 + i * 228
        panel = pygame.Rect(x, 100, 216, 520)
        pygame.draw.rect(ba, (28, 20, 10), panel, border_radius=10)
        pygame.draw.rect(ba, (172, 122, 55), panel, 2, border_radius=10)
        ba.blit(font_small.render(label, True, (255, 236, 218)),
                (x + 12, 112))
        native = pygame.Surface((216, 470), pygame.SRCALPHA)
        # Telapak di satu garis tanah: rig lama telapak +48 (anchor 270),
        # rig v2 telapak +68 (anchor 250) -> keduanya menapak y=318.
        ay = 270 if i < 3 else 250
        if i < 3:
            Old._draw_grimjaw_elite(native, 108, ay, 1, phase, action,
                                    prog, spin, False)
        else:
            G._draw_grimjaw_elite(native, 108, ay, 1, phase, action,
                                  prog, spin, False)
        scaled = native
        old_clip = ba.get_clip()
        ba.set_clip(panel.inflate(-6, -34))
        ba.blit(scaled, (x + 3, 136))
        ba.set_clip(old_clip)
    ba.blit(font_small.render(
        "kiri: baseline eccbeda   |   kanan: v2 (mane 5-layer, mask 5-band, "
        "smear, foot solver)", True, (185, 151, 115)), (24, 640))
    out5 = os.path.join(ROOT, "docs", "grimjaw_v2_before_after.png")
    pygame.image.save(ba, out5)
    print(out5)

print("SEMUA CEK LOLOS" if ok_all else "ADA CEK GAGAL")
sys.exit(0 if ok_all else 1)
