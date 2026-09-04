#!/usr/bin/env python3
"""Kontrak lintas-boss: FX tidak boleh menutupi karakter dengan cahaya.

Menyapu SEMUA mini boss & true boss yang punya lapisan FX hidup
(`heroes/_LIVE_FX_PATHS` ∩ `bosses/_boss_index.BOSS_INDEX`) dan mengukur,
untuk setiap skill Q/W/E/R pada 6 titik waktu plus momen kena damage:

* **white%**  — rasio piksel sangat terang (min(r,g,b) >= 200) di dalam
  siluet badan;
* **lum+**    — kenaikan luminansi rata-rata di siluet dibanding render
  bersih (tanpa lapisan FX).

Gejala yang dicegah (semua akar masalahnya sama):

1. ``pygame.BLEND_RGB_ADD`` **mengabaikan kanal alpha**. Glow yang
   digambar RGB penuh + alpha menurun jadi CAKRAM warna solid saat
   di-blit additive. Ini membuat Razak/Gorath/Nyzrak/Alchemist/Ancient
   Apparition tertelan bola putih saat skill di-cast.
2. ``set_alpha`` pada jalur additive juga tidak berefek — glow yang
   "memudar" tetap ditambahkan penuh.
3. Hit flash berupa cakram putih besar tepat di atas badan.
4. Poligon FX yang berpusat di caster (bintang ledakan, panel kubah,
   aura cincin) digambar PADAT, bukan sebagai cangkang.

Ambang sengaja longgar (white < 12%, lum+ < 60) supaya FX tetap boleh
terang & ekspresif — yang dilarang adalah karakternya hilang.

Jalankan: python3 tools/test_boss_no_white_cover.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import importlib  # noqa: E402

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes  # noqa: E402
from heroes import _ProbeEntity  # noqa: E402
from bosses._boss_index import BOSS_INDEX  # noqa: E402

DT = 1.0 / 60.0
SIZE = 340
CX, CY = 170, 200
FRACS = (0.05, 0.15, 0.3, 0.5, 0.7, 0.9)

#: Ambang: di atas ini karakter dianggap tertutup FX.
MAX_WHITE_PCT = 12.0
MAX_LUM_GAIN = 60.0

#: Boss yang siluetnya memang banyak piksel terang (baju/salju putih);
#: nilai dasarnya diukur dari render BERSIH lalu dijadikan garis dasar.
_BASELINE_CACHE = {}


def _draw_fn(name):
    mod, fn = BOSS_INDEX[name]
    return getattr(importlib.import_module("bosses." + mod), fn)


def _hero(name, **kw):
    h = _ProbeEntity(name, float(CX), float(CY))
    h.boss_type = name
    h.hero_type = name
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = 45
    h.timer = 0
    h.hp = h.max_hp = 1200
    h.radius = 16
    h.hurt_flash_timer = 0
    h.skill_damage = 180
    h.skill_range = 180
    for attr in ("blink_from_x", "blink_from_y",
                 "mana_void_x", "mana_void_y"):
        setattr(h, attr, 0)
    for k, v in kw.items():
        setattr(h, k, v)
    return h


def _render(name, skill=None, frac=0.0, live=True, hurt=0.0):
    fx = heroes._live_fx_module(name) if live else None
    if fx is not None:
        try:
            fx.reset_all()
        except Exception:
            pass
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    dur = getattr(fx, "SKILL_DUR", {}).get(skill, 60) if fx else 60
    h = _hero(name, active_skill=skill,
              active_skill_timer=int(dur * (1.0 - frac)) if skill else 0)
    h.target = _ProbeEntity("dummy", float(CX + 90), float(CY - 10))
    h.target.alive = True
    if fx is not None:
        try:
            fx.attach(h)
            for _ in range(max(0, dur - h.active_skill_timer)):
                fx.tick(DT)
            if hurt > 0.0:
                d = fx.director_for(h)
                d.on_hurt(0.2)
                fx.tick(0.0001)
                for attr in ("hit_flash", "_hit_flash", "flash"):
                    if hasattr(d, attr):
                        setattr(d, attr, 0.16 * hurt)
        except Exception:
            pass
    _draw_fn(name)(surf, h, CX, CY)
    if fx is not None:
        try:
            fx.reset_all()
        except Exception:
            pass
    return surf


def _baseline(name):
    """(titik badan, render bersih, white% bawaan sprite)."""
    if name in _BASELINE_CACHE:
        return _BASELINE_CACHE[name]
    clean = _render(name, live=False)
    pts = []
    for x in range(CX - 45, CX + 45):
        for y in range(CY - 80, CY + 25):
            if clean.get_at((x, y)).a >= 200:
                pts.append((x, y))
    own = 0
    for p in pts:
        c = clean.get_at(p)
        if min(c.r, c.g, c.b) >= 200:
            own += 1
    own_pct = 100.0 * own / max(1, len(pts))
    _BASELINE_CACHE[name] = (pts, clean, own_pct)
    return _BASELINE_CACHE[name]


def measure(name, surf):
    pts, clean, own_pct = _baseline(name)
    if not pts:
        return 0.0, 0.0
    white = 0
    dl = 0.0
    for p in pts:
        c = surf.get_at(p)
        b = clean.get_at(p)
        if min(c.r, c.g, c.b) >= 200:
            white += 1
        dl += (c.r + c.g + c.b) / 3.0 - (b.r + b.g + b.b) / 3.0
    n = float(len(pts))
    # kurangi piksel terang milik sprite itu sendiri (mis. baju putih
    # Xerathis / salju Varkul) supaya yang diukur murni kontribusi FX.
    return max(0.0, 100.0 * white / n - own_pct), dl / n


FAILED = []
ROWS = []


def check(name, cond, detail=""):
    print("%-5s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAILED.append(name)


TARGETS = sorted(n for n in heroes._LIVE_FX_PATHS if n in BOSS_INDEX)
print("Menyapu %d boss ber-lapisan FX hidup\n" % len(TARGETS))

for name in TARGETS:
    pts, _clean, own = _baseline(name)
    if len(pts) < 600:
        print("SKIP  %-20s siluet terlalu kecil (%d px)" % (name, len(pts)))
        continue
    worst_w = worst_l = 0.0
    worst_at = ""
    for skill in ("q", "w", "e", "r"):
        for frac in FRACS:
            w, dl = measure(name, _render(name, skill, frac))
            if w > worst_w or dl > worst_l:
                if w >= worst_w and dl >= worst_l:
                    worst_at = "%s@%.2f" % (skill.upper(), frac)
            worst_w = max(worst_w, w)
            worst_l = max(worst_l, dl)
    hw, hl = measure(name, _render(name, hurt=1.0))
    worst_w = max(worst_w, hw)
    worst_l = max(worst_l, hl)
    if hw >= worst_w:
        worst_at = "HURT"
    ROWS.append((name, worst_w, worst_l, worst_at))
    check("%-20s tidak tertutup FX" % name,
          worst_w < MAX_WHITE_PCT and worst_l < MAX_LUM_GAIN,
          "putih %4.1f%% lum+%5.1f (%s)" % (worst_w, worst_l, worst_at))

# ── helper primitif: pastikan glow premultiplied di modul yang diperbaiki
print()
for name in ("razak", "gorath", "nyzrak", "alchemist",
             "ancient_apparition", "gornak"):
    mod = heroes._live_fx_module(name)
    if mod is None or not hasattr(mod, "glow_surface"):
        continue
    g = mod.glow_surface(24, (255, 250, 210), 1.0)
    c = g.get_at((g.get_width() // 2, g.get_height() // 2))
    check("%-20s glow_surface premultiplied" % name,
          max(c.r, c.g, c.b) <= c.a + 8,
          "rgb%d a%d" % (max(c.r, c.g, c.b), c.a))

print()
print("%-22s %8s %8s  %s" % ("boss", "putih%", "lum+", "momen terburuk"))
for name, w, dl, at in sorted(ROWS, key=lambda r: -r[1]):
    print("%-22s %7.1f%% %8.1f  %s" % (name, w, dl, at))

print()
if FAILED:
    print("%d GAGAL: %s" % (len(FAILED), ", ".join(f.strip() for f in FAILED)))
    sys.exit(1)
print("Semua boss lolos kontrak 'FX tidak menutupi karakter'")
