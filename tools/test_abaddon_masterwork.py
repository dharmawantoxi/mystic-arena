#!/usr/bin/env python3
"""Regression test Abaddon ORIGINAL-MAX.

Mengunci (semua lewat path shipping bosses.level1.draw_abaddon):
  * semua mode render tanpa exception & berisi piksel;
  * bbox padat segaris keluarga (abaddon >= gornak, presence W>=140);
  * hurt flash menerangkan badan (paritas keluarga);
  * bayangan reaktif mengecil saat lift, dasar menapak;
  * animasi tidak membeku (state berbeda antar fase);
  * per-frame murah untuk mobile (< 1.5 ms);
  * renderer prosedural (tanpa pygame.image.load).
Jalankan: python3 tools/test_abaddon_masterwork.py
"""
import inspect
import os
import sys
import time
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import bosses.level1 as L
NS = L._NS_abaddon


def probe(cx=230.0, cy=230.0, **kw):
    b = SimpleNamespace(boss_type="abaddon", boss_class="mini", x=float(cx),
                        y=float(cy), direction=1, facing=1, pulse=1.2, timer=0,
                        attack_cooldown=50, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=30,
                        hp=9000, max_hp=9000, _ab_attack_active=False)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(boss, fn=None, size=460):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    (fn or L.draw_abaddon)(s, boss, 230, 230)
    return s


def hb(s):
    r = s.get_bounding_rect(min_alpha=100)
    return r.height, r.width


def test_all_modes_render():
    walker = probe(pulse=1.0)
    walker._drk_last_x = -2.0
    walker._drk_last_y = 0.0
    cases = [probe(pulse=0.0), probe(pulse=3.3), walker,
             probe(_ab_attack_active=True, _ab_attack_progress=0.5),
             probe(active_skill="q", active_skill_timer=45),
             probe(active_skill="w", active_skill_timer=20),
             probe(active_skill="e", active_skill_timer=30),
             probe(active_skill="r", active_skill_timer=32,
                   target=SimpleNamespace(x=320.0, y=230.0, alive=True)),
             probe(hurt_flash_timer=6)]
    for c in cases:
        h, w = hb(render(c))
        assert w > 20 and h > 20, (w, h)


def test_family_size():
    def bb(name, fn):
        b = probe()
        b.boss_type = name
        return hb(render(b, fn=fn))
    gh, gw = bb("gornak", L.draw_gornak)
    ah, aw = bb("abaddon", L.draw_abaddon)
    dh, dw = bb("drakar", L.draw_drakar)
    assert ah >= gh, f"abaddon H={ah} harus >= gornak H={gh}"
    assert aw >= gw, f"abaddon W={aw} harus >= gornak W={gw}"
    assert gh >= dh * 0.72, f"gornak H={gh} vs drakar H={dh}"
    assert aw >= 140, f"abaddon W={aw} kehilangan presence"


def test_hurt_flash_and_reactive_shadow():
    base = render(probe(pulse=1.2))
    hit = render(probe(pulse=1.2, hurt_flash_timer=8))

    def mean_lum(s):
        tot = n = 0
        for yy in range(0, 460, 4):
            for xx in range(0, 460, 4):
                r, g, b, a = s.get_at((xx, yy))
                if a > 120:
                    tot += r + g + b
                    n += 1
        return tot / max(1, n)

    mb, mh = mean_lum(base), mean_lum(hit)
    assert mh > mb + 20, f"flash tidak menerangkan badan ({mb:.0f}->{mh:.0f})"

    s0 = pygame.Surface((220, 60), pygame.SRCALPHA)
    NS._draw_shadow(s0, 110, 30, 0)
    r0 = s0.get_bounding_rect(min_alpha=20)
    s1 = pygame.Surface((220, 60), pygame.SRCALPHA)
    NS._draw_shadow(s1, 110, 30, 6)
    r1 = s1.get_bounding_rect(min_alpha=20)
    assert r1.width < r0.width, (r0.width, r1.width)
    assert abs(r1.bottom - r0.bottom) <= 1, (r0.bottom, r1.bottom)
    print(f"hurt flash +{mh - mb:.0f} lum | shadow lift "
          f"W{r0.width}->{r1.width}")


def test_animation_not_frozen_and_fast():
    def sig(boss):
        s = render(boss)
        m = pygame.mask.from_surface(s, 100)
        return (m.count(), tuple(int(v) for v in m.centroid()))

    ids = {sig(probe(pulse=1.0 + i * 0.21)) for i in range(24)}
    assert len(ids) >= 8, f"idle beku? hanya {len(ids)} state"
    wids = set()
    for i in range(24):
        b = probe(pulse=i * 0.26)
        b._drk_last_x = b.x - 2.0
        b._drk_last_y = b.y
        wids.add(sig(b))
    assert len(wids) >= 10, f"walk beku? hanya {len(wids)} state"

    b = probe()
    render(b)
    N = 40
    t0 = time.perf_counter()
    for i in range(N):
        b.pulse = 1.0 + i * 0.13
        render(b)
    dt = (time.perf_counter() - t0) / N * 1000
    assert dt < 1.5, f"per-frame {dt:.2f} ms (budget mobile)"
    print(f"animasi hidup: idle {len(ids)}/24, walk {len(wids)}/24 state | "
          f"{dt:.2f} ms/frame")


def test_procedural_only():
    src = inspect.getsource(L)
    assert "pygame.image.load" not in src


if __name__ == "__main__":
    test_all_modes_render()
    print("PASS all modes render")
    test_family_size()
    print("PASS family size")
    test_hurt_flash_and_reactive_shadow()
    print("PASS hurt flash + shadow reaktif")
    test_animation_not_frozen_and_fast()
    test_procedural_only()
    print("PASS procedural + animasi hidup")
    print("ALL ABADDON ORIGINAL-MAX TESTS PASSED")
