#!/usr/bin/env python3
"""Audit visual Ancient Apparition v3 (numeric, tanpa mata).

Memeriksa properti visual kunci hasil rewrite langsung dari piksel:
  * siluet: bbox hadir (crown -> skirt), lebar orbit;
  * chunky pixel art: blok 2x2 pada rig (piksel digambar di 1/2 resolusi);
  * wajah glow: piksel terang di area mata;
  * shadow menapak di bawah;
  * attack swing: trail + flash di depan badan;
  * walk: hem berayun (beda piksel antar fase);
  * tidak flicker: render identik dua kali -> hash sama.
"""
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

from heroes import ancient_apparition_fx as F
from bosses.level3 import _NS_ancient_apparition as G

F.reset_all()
BG = (16, 14, 22)
SIZE = 460
C = SIZE // 2


def probe(**kw):
    b = SimpleNamespace(
        boss_type="ancient_apparition", boss_class="true",
        x=float(C), y=float(C), direction=1, facing=1, pulse=1.2,
        timer=0, attack_cooldown=61, active_skill=None,
        active_skill_timer=0, target=None, hurt_flash_timer=0,
        alive=True, radius=30, hp=9000, max_hp=9000)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(b, clear=True):
    s = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    G.draw_apparition(s, b, C, C)
    return s


def region_pixels(s, x0, y0, x1, y1, min_alpha=100):
    n = 0
    for yy in range(int(y0), int(y1)):
        for xx in range(int(x0), int(x1)):
            if s.get_at((xx, yy))[3] >= min_alpha:
                n += 1
    return n


def bright_pixels(s, x0, y0, x1, y1, thresh=200):
    n = 0
    for yy in range(int(y0), int(y1)):
        for xx in range(int(x0), int(x1)):
            r, g, b, a = s.get_at((xx, yy))
            if a > 100 and r + g + b > thresh * 3:
                n += 1
    return n


def main():
    ok = []

    # 1. siluet: crown (atas), torso (tengah), skirt (bawah)
    s = render(probe(pulse=1.2))
    crown = region_pixels(s, C - 20, C - 62, C + 20, C - 44)
    torso = region_pixels(s, C - 20, C - 14, C + 20, C + 8)
    skirt = region_pixels(s, C - 24, C + 8, C + 24, C + 34)
    orbit_w = s.get_bounding_rect(min_alpha=100).width
    ok.append(("crown pixels", crown > 25, crown))
    ok.append(("torso pixels", torso > 120, torso))
    ok.append(("skirt pixels", skirt > 120, skirt))
    ok.append(("orbit/sprite width >= 100", orbit_w >= 100, orbit_w))

    # 2. wajah glow: piksel terang di area mata (y - 25..-29)
    eyes = bright_pixels(s, C - 10, C - 32, C + 10, C - 22, 190)
    ok.append(("eye glow bright pixels", eyes >= 2, eyes))

    # 3. shadow menapak: piksel gelap semi-alpha di bawah (C+52 +- 8)
    shadow = region_pixels(s, C - 40, C + 46, C + 40, C + 62, 20)
    ok.append(("ground shadow present", shadow > 100, shadow))

    # 4. chunky 2x: blok 2x2 seragam pada pita torso tengah
    chunky = 0
    total = 0
    for yy in range(C - 12, C + 4, 2):
        for xx in range(C - 18, C + 18, 2):
            base = s.get_at((xx, yy))
            if base[3] < 200:
                continue
            total += 1
            same = all(s.get_at((xx + dx, yy + dy)) == base
                       for dx in (0, 1) for dy in (0, 1))
            if same:
                chunky += 1
    ratio = chunky / max(1, total)
    ok.append(("chunky 2x block ratio > 0.5", ratio > 0.5,
               round(ratio, 2)))

    # 5. tidak flicker: dua render state sama -> piksel identik.
    #    (partikel lapisan hidup memang bergerak antar frame — itu
    #    bukan flicker — jadi determinisme diuji pada jalur canvas)
    G._LIVE_MOD = False
    try:
        b = probe(pulse=2.4)
        s1 = render(b)
        s2 = render(b)
    finally:
        G._LIVE_MOD = None
    ok.append(("no flicker (identical re-render)",
               pygame.image.tobytes(s1, "RGBA")
               == pygame.image.tobytes(s2, "RGBA"), True))

    # 6. attack swing: trail/flash di depan badan saat jendela swing
    b = probe(_aa_attack_active=True, _aa_attack_progress=0.5)
    b.target = SimpleNamespace(x=C + 110, y=C, alive=True)
    G._LIVE_MOD = False
    try:
        sa = render(b)
    finally:
        G._LIVE_MOD = None
    front_fx = bright_pixels(sa, C + 18, C - 26, C + 64, C + 6, 150)
    ok.append(("swing flash/trail in front", front_fx > 8, front_fx))

    # 7. walk: hem berayun antar fase
    b1 = probe(pulse=0.0)
    b1._aa_last_x = b1.x - 2.0
    b1._aa_last_y = b1.y
    b2 = probe(pulse=1.6)
    b2._aa_last_x = b2.x - 2.0
    b2._aa_last_y = b2.y
    sw1 = render(b1)
    sw2 = render(b2)
    diff = sum(1 for yy in range(C - 60, C + 40, 2)
               for xx in range(C - 40, C + 40, 2)
               if sw1.get_at((xx, yy)) != sw2.get_at((xx, yy)))
    ok.append(("walk hem sway varies", diff > 20, diff))

    F.reset_all()
    print("AUDIT VISUAL ANCIENT APPARITION v3")
    print("==================================")
    fails = 0
    for name, passed, val in ok:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {val}")
        fails += 0 if passed else 1
    if fails:
        print(f"{fails} GAGAL")
        sys.exit(1)
    print("SEMUA PASS")


if __name__ == "__main__":
    main()
