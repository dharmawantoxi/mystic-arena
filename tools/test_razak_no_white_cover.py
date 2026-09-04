#!/usr/bin/env python3
"""Kontrak: FX Razak tidak boleh menutupi badannya dengan cahaya putih.

Gejala yang dicegah (mini boss level 2):

1. ``glow_surface`` / ``ground_glow_surface`` digambar RGB penuh + alpha
   menurun, lalu di-blit ``BLEND_RGB_ADD`` — mode itu MENGABAIKAN alpha,
   jadi setiap glow menjadi CAKRAM warna solid. Saat Firestorm (R) atau
   skill lain di-cast, cakram-cakram itu menumpuk sampai badan Razak
   tenggelam di bercak putih-kuning.
2. ``_blit_faded(..., additive=True)`` memakai ``set_alpha`` yang juga
   diabaikan mode additive -> glow yang "memudar" tetap penuh.
3. Hit flash lama: cakram ``fire_white`` radius ~76 px di atas badan.

Jalankan: python3 tools/test_razak_no_white_cover.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes  # noqa: E402
from heroes import _ProbeEntity  # noqa: E402
from heroes import razak_fx as F  # noqa: E402
from bosses.level2 import _NS_razak as R  # noqa: E402

DT = 1.0 / 60.0
SIZE = 320
CX, CY = 160, 190
BODY = pygame.Rect(CX - 40, CY - 70, 80, 90)


def _hero(**kw):
    h = _ProbeEntity("razak", float(CX), float(CY))
    h.boss_type = "razak"
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = 45
    h.timer = 0
    h.hp = h.max_hp = 900
    h.radius = 16
    h.hurt_flash_timer = 0
    for k, v in kw.items():
        setattr(h, k, v)
    return h


def _render(skill=None, frac=0.0, live=True, hurt=0.0, **kw):
    F.reset_all()
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    dur = F.SKILL_DUR[skill] if skill else 1
    h = _hero(active_skill=skill,
              active_skill_timer=int(dur * (1.0 - frac)) if skill else 0,
              **kw)
    h.target = _ProbeEntity("dummy", float(CX + 90), float(CY - 10))
    h.target.alive = True
    if live:
        F.attach(h)
        for _ in range(dur - h.active_skill_timer):
            F.tick(DT)
        if hurt > 0.0:
            d = F.director_for(h)
            d.on_hurt(0.2)
            F.tick(0.0001)
            d.hit_flash = 0.16 * hurt
    R.draw_razak(surf, h, CX, CY)
    F.reset_all()
    return surf


def _body_mask():
    """Piksel badan Razak (render bersih, tanpa lapisan FX)."""
    clean = _render(live=False)
    pts = []
    for x in range(BODY.left, BODY.right):
        for y in range(BODY.top, BODY.bottom):
            if clean.get_at((x, y)).a >= 200:
                pts.append((x, y))
    return pts, clean


MASK, CLEAN = _body_mask()
assert len(MASK) > 800, "mask badan terlalu kecil: %d" % len(MASK)


def metrics(surf):
    """(rasio piksel sangat terang, kenaikan luminansi rata-rata)."""
    white = 0
    dl = 0.0
    for (x, y) in MASK:
        c = surf.get_at((x, y))
        b = CLEAN.get_at((x, y))
        if min(c.r, c.g, c.b) >= 200:
            white += 1
        dl += (c.r + c.g + c.b) / 3.0 - (b.r + b.g + b.b) / 3.0
    n = float(len(MASK))
    return 100.0 * white / n, dl / n


FAILED = []


def check(name, cond, detail=""):
    print("%-5s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAILED.append(name)


# ── 1. glow premultiplied ────────────────────────────────────────────
g = F.glow_surface(24, (255, 250, 210), 1.0)
c = g.get_at((25, 25))
check("glow_surface premultiplied (RGB ikut turun bersama alpha)",
      max(c.r, c.g, c.b) <= c.a + 8,
      "pusat rgb=(%d,%d,%d) a=%d" % (c.r, c.g, c.b, c.a))

gg = F.ground_glow_surface(40, (255, 250, 210), 0.35)
c2 = gg.get_at((gg.get_width() // 2, gg.get_height() // 2))
check("ground_glow_surface premultiplied",
      max(c2.r, c2.g, c2.b) <= c2.a + 8,
      "pusat rgb=(%d,%d,%d) a=%d" % (c2.r, c2.g, c2.b, c2.a))

# ── 2. _blit_faded additive benar-benar meredam ──────────────────────
src = F.glow_surface(20, (255, 250, 210), 1.0)
a_full = pygame.Surface((80, 80), pygame.SRCALPHA)
a_dim = pygame.Surface((80, 80), pygame.SRCALPHA)
F._blit_faded(a_full, src, 40, 40, 255, additive=True)
F._blit_faded(a_dim, src, 40, 40, 40, additive=True)
lf = sum(a_full.get_at((40, 40))[:3])
ld = sum(a_dim.get_at((40, 40))[:3])
check("_blit_faded(additive) meredam intensitas", ld < lf * 0.5,
      "penuh=%d redup=%d" % (lf, ld))

# ── 3. skill tidak menutupi badan ────────────────────────────────────
for skill in ("q", "w", "e", "r"):
    worst_w = worst_l = 0.0
    for frac in (0.05, 0.2, 0.35, 0.5, 0.7, 0.9):
        w, dl = metrics(_render(skill, frac))
        worst_w = max(worst_w, w)
        worst_l = max(worst_l, dl)
    check("skill %s tidak memutihkan badan" % skill.upper(),
          worst_w < 8.0 and worst_l < 45.0,
          "putih %.1f%% naik-lum %.1f" % (worst_w, worst_l))

# ── 4. hit flash tidak jadi white-out ────────────────────────────────
for k in (1.0, 0.5):
    w, dl = metrics(_render(hurt=k))
    check("hit flash k=%.1f tidak menutupi badan" % k, w < 6.0,
          "putih %.1f%%" % w)

# Lane boss punya hurt-flash siluetnya sendiri (konvensi level1/level2:
# w = 235 * min(1, flash/8), maks ~8 frame). Itu DIPERTAHANKAN; yang
# dilarang adalah lapisan hidup menambah flash kedua di atasnya.
w_boss_only = metrics(_render(hurt_flash_timer=8))[0]
w_both = metrics(_render(hurt=1.0, hurt_flash_timer=8))[0]
check("hurt lane boss tidak double-flash", w_both <= w_boss_only + 3.0,
      "boss saja %.1f%% vs boss+hidup %.1f%%" % (w_boss_only, w_both))
check("hurt lane boss meluruh cepat (flash=2 sudah tipis)",
      metrics(_render(hurt_flash_timer=2))[0] < 25.0,
      "putih %.1f%%" % metrics(_render(hurt_flash_timer=2))[0])

# ── 5. FX tetap TERLIHAT (bukan sekadar dimatikan) ───────────────────
vis = metrics(_render("r", 0.5))[1]
check("FX R masih memberi cahaya di badan", vis > 3.0, "naik-lum %.1f" % vis)
flash_lum = metrics(_render(hurt=1.0))[1]
check("hit flash masih terbaca", flash_lum > 1.0,
      "naik-lum %.1f" % flash_lum)

print()
if FAILED:
    print("%d GAGAL: %s" % (len(FAILED), ", ".join(FAILED)))
    sys.exit(1)
print("Semua kontrak 'Razak tidak tertutup cahaya putih' lolos")
