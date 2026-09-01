#!/usr/bin/env python3
"""Probe forensik Skill FX Vex v3.0 — verifikasi struktur visual per-skill.

Tanpa mata: tiap fitur dicek lewat sampling piksel presisi (warna band,
posisi ring, band accretion, mata rantai, gerhana, kristal, dsb).
"""
import math
import os
import sys
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from heroes import _ProbeEntity
from heroes._bundle import _NS_vex as V

OK = True


def check(cond, label, extra=""):
    global OK
    print(("[OK ] " if cond else "[FAIL] ") + label + " " + extra)
    OK = OK and bool(cond)


def frame(skill, timer, fs=1.0, size=760, target_offset=(145, -20)):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    x, y = size // 2, size // 2 + 40
    h = _ProbeEntity("vex", x, y)
    h.pulse = 1.3
    h.direction = h.facing = 1
    h.active_skill = skill
    h.active_skill_timer = timer
    h.target = SimpleNamespace(x=x + target_offset[0], y=y + target_offset[1],
                               alive=True)
    h._render_scale = fs
    V.draw_vex(s, h, x, y)
    return s, x, y


def px(s, x, y):
    if 0 <= x < s.get_width() and 0 <= y < s.get_height():
        return s.get_at((int(x), int(y)))
    return pygame.Color(0, 0, 0, 0)


def band_hits(s, match, xs):
    return sum(1 for (x, y) in xs if match(px(s, x, y)))


P = V.PALETTE


def is_col(c, key, tol=26):
    t = P[key]
    return (c.a > 60 and abs(c.r - t[0]) <= tol and
            abs(c.g - t[1]) <= tol and abs(c.b - t[2]) <= tol)


# ── W: ring presisi 60 + gerhana + kristal + dither ─────────────────
s, x, y = frame("w", 50)
rng = 60
ring = [(x + int(math.cos(math.radians(a)) * rng),
         y + int(math.sin(math.radians(a)) * rng)) for a in range(0, 360, 3)]
n_ring = band_hits(s, lambda c: c.a > 70, ring)
check(n_ring >= 100, "W: ring 60px kontinu", f"{n_ring}/120")
# gerhana: corona + occluder di atas portal
gy = y + 56
ec_y = y - 118
check(is_col(px(s, x, ec_y), "shadow", 40) or
      is_col(px(s, x, ec_y), "shadow_deep", 40) or
      px(s, x, ec_y).r < 20,
      "W: occluder gerhana gelap di pusat",
      str(px(s, x, ec_y)))
cor = px(s, x - 17, ec_y)  # rim corona terang
check(cor.a > 70 and cor.g > 70 and cor.b > 80,
      "W: corona rim di tepi gerhana", str(cor))
# kristal: baris luar pada radius ~57
cry = 0
for a in range(0, 360, 6):
    bx = x + math.cos(math.radians(a)) * 57
    by = gy + math.sin(math.radians(a)) * 57 * .34
    c = px(s, bx, by - 10)
    if c.a > 60 and c.b > 60 and c.r < 120:
        cry += 1
check(cry >= 8, "W: mahkota kristal terdeteksi", f"{cry}/60")
# dither disk: ada piksel void_darkest terseparsi di dalam disk
dith = sum(1 for dx_ in range(-30, 31, 3) for dy_ in (-6, 0, 6)
           if is_col(px(s, x + dx_, gy + dy_), "void_darkest", 30))
check(dith >= 5, "W: dither disk ground", str(dith))

# ── R: accretion band + photon ring + rim gold ───────────────────────
s, x, y = frame("r", 40)
rng = 180
gold = [(x + int(math.cos(math.radians(a)) * (rng - 7)),
         y + int(math.sin(math.radians(a)) * (rng - 7))) for a in range(0, 360, 4)]
n_gold = band_hits(s, lambda c: c.a > 70 and c.r > 170 and c.g > 140, gold)
check(n_gold >= 60, "R: rim gold 180px", f"{n_gold}/90")
cy = y - 8
pulse_ = math.sin(1.3 * 5) * .5 + .5
disc_r = int((30 + 14 * pulse_))
core_r = int(16 + 7 * pulse_)
# accretion band depan: titik parametrik gold/magma di bawah core
front = []
for a in (1.0, 1.35, 1.7, math.pi - 1.7):
    front.append(px(s, x + math.cos(a) * disc_r, cy + math.sin(a) * disc_r * .34))
    front.append(px(s, x + math.cos(a) * disc_r * .82,
                    cy + math.sin(a) * disc_r * .3))
n_front = sum(1 for c in front if c.a > 60 and c.r > 150)
check(n_front >= 4, "R: accretion band depan", str(n_front))
# band belakang (atas core) — titik di luar siluet core
back = []
for a in (math.pi + .55, math.pi + .95, math.tau - .95, math.tau - .55):
    if abs(math.cos(a)) * disc_r > core_r + 6:
        back.append(px(s, x + math.cos(a) * disc_r,
                       cy + math.sin(a) * disc_r * .34))
n_back = sum(1 for c in back if c.a > 50 and c.r > 110)
check(n_back >= 2, "R: accretion band belakang", str(n_back))
# core hitam pekat (event horizon)
core = px(s, x, cy)
check(core.a > 180 and core.r < 45 and core.g < 60 and core.b < 70,
      "R: inti black hole gelap", str(core))
# retakan magma keluar dari pusat ground
crack = 0
for a in range(0, 360, 12):
    for r_ in (30, 45, 60):
        c = px(s, x + math.cos(math.radians(a)) * r_,
               gy2 if False else y + 58 + math.sin(math.radians(a)) * r_ * .5)
        if c.a > 70 and c.r > 120 and c.g < 110:
            crack += 1
check(crack >= 3, "R: retakan magma radial", str(crack))

# ── Q: beam kontinu + portal target + iris ───────────────────────────
s, x, y = frame("q", 20)
sx, sy = V._staff_orb_position(x, y, 1, 1.3, "idle", 0.0)
tx, ty = V._target_position(_ProbeEntity("vex", x, y), x, y) if False else (None, None)
# target sebenarnya (ter-clamp oleh _world_to_local):
h = _ProbeEntity("vex", x, y); h._render_scale = 1.0
h.target = SimpleNamespace(x=x + 145, y=y - 20, alive=True)
tx, ty = V._target_position(h, x, y)
beam = 0
for t_ in (.2, .35, .5, .65, .8):
    bx = sx + (tx - sx) * t_
    by = sy + (ty - sy) * t_
    found = any(px(s, bx + dx_, by + dy_).a > 70 and
                px(s, bx + dx_, by + dy_).b > 90
                for dx_ in (-4, 0, 4) for dy_ in (-4, 0, 4))
    beam += found
check(beam >= 4, "Q: conduit beam 5 titik", f"{beam}/5")
# ring portal utama di target
port = 0
for a in range(0, 360, 9):
    c = px(s, tx + math.cos(math.radians(a)) * 22,
           ty + math.sin(math.radians(a)) * 22)
    if c.a > 60:
        port += 1
check(port >= 30, "Q: ring portal target r=22", f"{port}/40")

# ── E: rantai (mata rantai) + sangkar ────────────────────────────────
s, x, y = frame("e", 30)
sx, sy = V._staff_orb_position(x, y, 1, 1.3, "attack", .45)
h = _ProbeEntity("vex", x, y); h._render_scale = 1.0
h.target = SimpleNamespace(x=x + 145, y=y - 20, alive=True)
tx, ty = V._target_position(h, x, y)
dx_, dy_ = tx - sx, ty - sy
dist_ = math.hypot(dx_, dy_) or 1.0
nx_, ny_ = -dy_ / dist_, dx_ / dist_
chain = 0
for t_ in (.2, .4, .6, .8):
    sag = math.sin(t_ * math.pi) * 6
    found = any(px(s, sx + dx_ * t_ + nx_ * (sag + d),
                   sy + dy_ * t_ + ny_ * (sag + d)).a > 60 and
                px(s, sx + dx_ * t_ + nx_ * (sag + d),
                   sy + dy_ * t_ + ny_ * (sag + d)).b > 120
                for d in (-4, -2, 0, 2, 4))
    chain += found
check(chain >= 3, "E: rantai astral di garis tether", f"{chain}/4")
# footprint ring di target r=30
foot = 0
for a in range(0, 360, 9):
    hit = any(px(s, tx + math.cos(math.radians(a)) * r,
                 ty + math.sin(math.radians(a)) * r).a > 60 and
              px(s, tx + math.cos(math.radians(a)) * r,
                 ty + math.sin(math.radians(a)) * r).b > 130
              for r in (29, 30, 31))
    foot += hit
check(foot >= 34, "E: footprint penjara r=30", f"{foot}/40")

# ── E foreground: sangkar kaca di target (timer awal) ────────────────
s, x, y = frame("e", 15)
h = _ProbeEntity("vex", x, y); h._render_scale = 1.0
h.target = SimpleNamespace(x=x + 145, y=y - 20, alive=True)
tx, ty = V._target_position(h, x, y)
env = min(1.0, (1 - 15 / 60.0) * 6.0, (1 - (1 - 15 / 60.0)) * 4.0 + .35)
rad = int(34 * env)
dome = 0
for a in range(15, 166, 15):
    found = any(px(s, tx + math.cos(math.radians(a)) * (rad + d),
                   ty - math.sin(math.radians(a)) * (rad + d)).a > 60 and
                px(s, tx + math.cos(math.radians(a)) * (rad + d),
                   ty - math.sin(math.radians(a)) * (rad + d)).b > 140
                for d in (-2, -1, 0, 1, 2))
    dome += found
check(dome >= 7, "E: kubah sangkar kaca", f"{dome}/11")

# ── determinisme: frame sama -> piksel identik ───────────────────────
s1, _, _ = frame("w", 50)
s2, _, _ = frame("w", 50)
check(pygame.image.tobytes(s1, "RGBA") == pygame.image.tobytes(s2, "RGBA"),
      "Determinisme: render W dua kali identik")

print("\n" + ("SEMUA PROBE LOLOS" if OK else "ADA PROBE GAGAL"))
sys.exit(0 if OK else 1)
