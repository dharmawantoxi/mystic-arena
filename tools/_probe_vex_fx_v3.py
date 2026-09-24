#!/usr/bin/env python3
"""Probe forensik renderer VEX V1 — verifikasi struktur visual per-skill.

Sebelum V1, probe ini memvalidasi FX masterwork v3.0 (black hole R, kubah
kaca E, ring portal Q).  Setelah ``heroes/vex_v1.py`` mengambil alih jalur
render (pola Kaizen V1), cek diperbarui ke bahasa pixel-art V1: rig chibi
hooded void-mage, orb staff menyala, kristal teal W, gelembung astral E,
nova teal/hijau R, dan telegraph Q.

Tanpa mata: tiap fitur dicek lewat sampling piksel presisi (warna ramp,
posisi ring, cluster orb, dsb).  Ambang diturunkan dari pengukuran nyata
(≈60% dari hasil sampel referensi) supaya probe tahan tuning artistik kecil
namun tetap menangkap regresi struktural.
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


P = V.PALETTE


def is_col(c, key, tol=26):
    t = P[key]
    return (c.a > 60 and abs(c.r - t[0]) <= tol and
            abs(c.g - t[1]) <= tol and abs(c.b - t[2]) <= tol)


# ── Rig V1: hood ungu + mata teal + orb staff menyala ───────────────
s, x, y = frame(None, 0)
hood = sum(1 for dx in range(-30, 31, 2) for dy in range(-70, -30, 2)
           if (lambda c: c.a > 60 and c.b > 50 and c.r < 110 and c.g < 90)
           (px(s, x + dx, y + dy)))
check(hood >= 100, "RIG: massa hood/robe ungu V1", str(hood))
eyes = sum(1 for dx in range(-14, 15) for dy in range(-34, -24)
           if (lambda c: c.a > 90 and c.g > 150 and c.b > 140)
           (px(s, x + dx, y + dy)))
check(eyes >= 15, "RIG: mata void teal di wajah shadow", str(eyes))
orb = sum(1 for dx in range(10, 40) for dy in range(-55, -25)
          if (lambda c: c.a > 80 and c.g > 130 and c.b > 130)
          (px(s, x + dx, y + dy)))
check(orb >= 80, "RIG: orb arcane menyala di ujung staff", str(orb))

# ── W: ring kristal teal di ground + tick ring ──────────────────────
s, x, y = frame("w", 26)
cry = 0
for a in range(0, 360, 6):
    for rr in (50, 55, 60):
        bx = x + math.cos(math.radians(a)) * rr
        by = y + 44 + math.sin(math.radians(a)) * rr * .5
        c = px(s, bx, by - 8)
        if c.a > 60 and c.g > 90 and c.b > 90:
            cry += 1
            break
check(cry >= 12, "W: mahkota kristal teal terdeteksi", f"{cry}/60")
ring = sum(1 for a in range(0, 360, 4)
           if px(s, x + math.cos(math.radians(a)) * 55,
                 y + 44 + math.sin(math.radians(a)) * 55 * .5).a > 40)
check(ring >= 50, "W: tick ring ground 55px", f"{ring}/90")

# ── E: gelembung astral ungu di target ──────────────────────────────
s, x, y = frame("e", 18)
tx, ty = x + 145, y - 20
purp = 0
for dx in range(-60, 61, 4):
    for dy in range(-80, 41, 4):
        c = px(s, tx + dx, ty + dy)
        if c.a > 50 and c.b > 100 and c.r > 60 and c.g < 170:
            purp += 1
check(purp >= 12, "E: gelembung/penjara astral ungu di target", str(purp))

# ── R: nova teal + bintang hijau di sekitar caster ──────────────────
s, x, y = frame("r", 30)
teal = 0
for a in range(0, 360, 5):
    for rr in range(50, 150, 12):
        c = px(s, x + math.cos(math.radians(a)) * rr,
               y + 4 + math.sin(math.radians(a)) * rr * .45)
        if c.a > 50 and c.g > 120 and c.b > 110:
            teal += 1
            break
check(teal >= 20, "R: cincin nova teal mengembang", f"{teal}/72")
grn = 0
for a in range(0, 360, 8):
    for rr in range(30, 140, 14):
        c = px(s, x + math.cos(math.radians(a)) * rr,
               y + 4 + math.sin(math.radians(a)) * rr * .45)
        if c.a > 50 and c.g > 150 and c.r < 130:
            grn += 1
            break
check(grn >= 6, "R: percikan hijau essence flux", f"{grn}/45")

# ── Q: charge glow di orb + telegraph target ────────────────────────
s, x, y = frame("q", 16)
o_pos = V._staff_orb_position(x, y, 1, 1.3, "attack", 0.5)
ch = 0
for dx in range(-18, 19, 2):
    for dy in range(-18, 19, 2):
        c = px(s, o_pos[0] + dx, o_pos[1] + dy)
        if c.a > 60 and c.g > 160 and c.b > 150:
            ch += 1
check(ch >= 150, "Q: charge glow terang di orb staff", str(ch))
tel = 0
for dx in range(-60, 61, 3):
    for dy in range(-45, 46, 3):
        c = px(s, x + 145 + dx, y - 20 + dy)
        if is_col(c, "void_mid", 40) or is_col(c, "void_light", 30):
            tel += 1
check(tel >= 6, "Q: telegraph void di titik target", str(tel))

# ── Serangan dasar: orb mengayun ke depan saat IMPACT ───────────────
def orb_bright_region(s, x, y, x0, x1, y0, y1):
    n = 0
    for dx in range(x0, x1, 2):
        for dy in range(y0, y1, 2):
            c = px(s, x + dx, y + dy)
            if c.a > 80 and c.g > 130 and c.b > 130:
                n += 1
    return n


s0 = pygame.Surface((760, 760), pygame.SRCALPHA)
V._draw_vex_elite(s0, 380, 420, 1, 0.0, "attack", 0.0, True)
back = orb_bright_region(s0, 380, 420, -40, 5, -80, -30)
s1 = pygame.Surface((760, 760), pygame.SRCALPHA)
V._draw_vex_elite(s1, 380, 420, 1, 0.0, "attack", 0.56, True)
fwd = orb_bright_region(s1, 380, 420, 10, 70, -40, 10)
check(back >= 4, "ATK: orb tertarik ke belakang saat wind-up", str(back))
check(fwd >= 20, "ATK: orb mendorong ke depan saat IMPACT 0.56", str(fwd))

# ── Determinisme: render W dua kali identik ─────────────────────────
sa, _, _ = frame("w", 26)
sb, _, _ = frame("w", 26)
same = all(sa.get_at((i, j)) == sb.get_at((i, j))
           for i in range(0, sa.get_width(), 7)
           for j in range(0, sa.get_height(), 7))
check(same, "Determinisme: render W dua kali identik")

print("-" * 50)
if OK:
    print("SEMUA PROBE LULUS")
else:
    print("ADA PROBE GAGAL")
    sys.exit(1)
