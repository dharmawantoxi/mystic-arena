#!/usr/bin/env python3
"""Regression test Drakar ORIGINAL-MAX.

Mengunci (semua lewat path shipping bosses.level1.draw_drakar):
  * semua mode render tanpa exception & berisi piksel;
  * bbox solid segaris keluarga (gornak >= 0.72*H drakar, presence W>=170);
  * trail swing menempel kepala kapak (mask-diff vs no-op trail);
  * durasi FX renderer == active_skill_timer AI;
  * animasi kontinu (bukan stepping bucket) & < 2.2 ms/frame;
  * renderer prosedural (tanpa pygame.image.load).
Jalankan: python3 tools/test_drakar_max.py
"""
import inspect
import math
import os
import re
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
NS = L._NS_drakar


def probe(cx=230.0, cy=230.0, **kw):
    b = SimpleNamespace(boss_type="drakar", boss_class="mini", x=float(cx),
                        y=float(cy), direction=1, facing=1, pulse=1.2, timer=0,
                        attack_cooldown=46, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=32,
                        hp=8000, max_hp=8000)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(boss, fn=None, size=460):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    (fn or L.draw_drakar)(s, boss, 230, 230)
    return s


def hb(s):
    r = s.get_bounding_rect(min_alpha=100)
    return r.height, r.width


def atk(progress, direction=1):
    cd = 46
    t = int(round((1.0 - progress) * (cd - 1)))
    b = probe(timer=t, direction=direction)
    b._drk_attack_active = True
    b._drk_attack_dir = direction
    b._drk_previous_timer = t + 1
    return b


def test_all_modes_render():
    walker = probe(pulse=1.0)
    walker._drk_last_x = -2.0
    walker._drk_last_y = 0.0
    cases = [probe(pulse=0.0), probe(pulse=3.3), walker,
             atk(0.1), atk(0.3), atk(0.5), atk(0.62), atk(0.85), atk(0.5, -1),
             probe(active_skill="q", active_skill_timer=45),
             probe(active_skill="w", active_skill_timer=20),
             probe(active_skill="e", active_skill_timer=30),
             probe(active_skill="r", active_skill_timer=30,
                   target=SimpleNamespace(x=320.0, y=230.0, alive=True)),
             probe(rage_active=True), probe(defense_boost=True)]
    for c in cases:
        h, w = hb(render(c))
        assert w > 20 and h > 20, (w, h)


def test_family_size():
    def bb(name, fn):
        b = probe()
        b.boss_type = name
        return hb(render(b, fn=fn))
    gh, gw = bb("gornak", L.draw_gornak)
    mh, mw = bb("morgath", L.draw_morgath)
    dh, dw = bb("drakar", L.draw_drakar)
    ah, aw = bb("abaddon", L.draw_abaddon)
    assert gh >= mh * 1.05, f"gornak H={gh} vs morgath H={mh}"
    assert gh >= dh * 0.72, f"gornak H={gh} vs drakar H={dh}"
    assert gw >= mw * 0.85, f"gornak W={gw} vs morgath W={mw}"
    assert gh <= ah * 1.00, f"gornak H={gh} vs abaddon H={ah}"
    assert gw <= aw * 1.00, f"gornak W={gw} vs abaddon W={aw}"
    assert dw >= 170, f"drakar W={dw} kehilangan presence"
    assert 130 <= dh <= 162, f"drakar H={dh} keluar rentang keluarga"


def test_hurt_flash_and_reactive_shadow():
    # hurt flash: badan lebih terang saat kena hit (paritas gornak/morgath)
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

    # shadow reaktif: mengecil saat lift, dasar tetap menapak tanah
    s0 = pygame.Surface((300, 80), pygame.SRCALPHA)
    NS._draw_shadow(s0, 150, 40, 0)
    r0 = s0.get_bounding_rect(min_alpha=20)
    s1 = pygame.Surface((300, 80), pygame.SRCALPHA)
    NS._draw_shadow(s1, 150, 40, 6)
    r1 = s1.get_bounding_rect(min_alpha=20)
    assert r1.width < r0.width, (r0.width, r1.width)
    assert abs(r1.bottom - r0.bottom) <= 1, (r0.bottom, r1.bottom)
    print(f"hurt flash +{mh - mb:.0f} lum | shadow lift "
          f"W{r0.width}->{r1.width}")


def _red_on_grey_count(a, b, cx, cy, half=44):
    """Piksel yang di render A merah-dominan tapi di B tidak (trail yang
    menimpa bilah kapak abu-abu)."""
    n = 0
    sx, sy = 0, 0
    for yy in range(cy - half, cy + half):
        for xx in range(cx - half, cx + half):
            ra, ga, ba, al = a.get_at((xx, yy))
            if al < 40 or ra - ga < 60:
                continue
            rb, gb, bb, bl = b.get_at((xx, yy))
            if bl >= 40 and rb - gb >= 60:
                continue
            n += 1
            sx += xx
            sy += yy
    return n, (sx / max(1, n), sy / max(1, n))


def test_trail_attached():
    orig = NS._draw_axe_slash_trail
    try:
        for prog in (0.47, 0.52, 0.58):
            with_t = render(atk(prog))
            NS._draw_axe_slash_trail = lambda *a, **k: None
            without = render(atk(prog))
            NS._draw_axe_slash_trail = orig
            g = NS._compute_two_handed_grip(230, 230, 1, 1.2, "attack", prog)
            hx, hy = int(g["axe_head"][0]), int(g["axe_head"][1])
            # (1) bagian trail yang menonjol keluar badan (alpha-diff)
            ma = pygame.mask.from_surface(with_t, 30)
            mb = pygame.mask.from_surface(without, 30)
            mb.invert()
            diff = ma.overlap_mask(mb, (0, 0))
            n_out = diff.count()
            # (2) bagian trail yang menimpa bilah (color-diff)
            n_on, centroid = _red_on_grey_count(with_t, without, hx, hy)
            n = n_out + n_on
            assert n > 40, f"trail terlalu kecil p={prog} ({n}px)"
            if n_on >= n_out:
                d = math.hypot(centroid[0] - hx, centroid[1] - hy)
                assert d < 50, f"centroid trail {d:.0f}px dari kapak p={prog}"
    finally:
        NS._draw_axe_slash_trail = orig


def test_durations_match_ai():
    src_ai = open(os.path.join(ROOT, "bosses", "base_boss.py")).read()
    want = {}
    for fn, key in [("_cast_q_battle_hunger", "q"),
                    ("_cast_w_counter_helix", "w"),
                    ("_cast_e_berserkers_call", "e"),
                    ("_cast_r_culling_blade", "r")]:
        m = re.search(r"def %s.*?active_skill_timer = (\d+)" % fn, src_ai, re.S)
        want[key] = int(m.group(1))
    src = inspect.getsource(L)
    for name, fn in [("q", "_draw_battlehunger_ground"),
                     ("w", "_draw_drk_helix"),
                     ("e", "_draw_berserkerscall_ground"),
                     ("r", "_draw_cullingblade_ground")]:
        m = re.search(r"def %s.*?duration = (\d+)" % fn, src, re.S)
        assert m and int(m.group(1)) == want[name], \
            f"durasi {fn} != AI ({want[name]})"


def test_animation_continuous_and_fast():
    """Animasi harus kontinu (bukan stepping bucket cache): sampel fase
    berdekatan menghasilkan siluet berbeda; dan per-frame tetap murah."""
    def sig_body(mode, phase, prog):
        spr = NS._drk_body_surface(mode, 1, phase, prog)
        m = pygame.mask.from_surface(spr, 100)
        return (m.count(), tuple(int(v) for v in m.centroid()))

    # idle: 24 sampel napas -> kontinu (bucket lama cuma 8; sisa duplikat =
    # kuantisasi sub-pixel napas ke integer)
    ids = {sig_body("idle", 1.0 + i * 0.21, 0.0) for i in range(24)}
    assert len(ids) >= 16, f"idle hanya {len(ids)} state (stepping?)"
    # walk: 24 sampel -> kontinu
    wids = {sig_body("walk", i * 0.26, 0.0) for i in range(24)}
    assert len(wids) >= 18, f"walk hanya {len(wids)} state (stepping?)"
    # helix: spin kontinu (prog*8pi = 4 putaran; sampel 1 putaran penuh)
    hids = {sig_body("helix", 1.2, i / 80.0) for i in range(20)}
    assert len(hids) >= 15, f"helix hanya {len(hids)} state (stepping?)"
    # attack: swing kontinu
    aids = {sig_body("attack", 1.2, i / 24.0) for i in range(24)}
    assert len(aids) >= 18, f"attack hanya {len(aids)} state (stepping?)"

    b = probe()
    render(b)
    N = 40
    t0 = time.perf_counter()
    for i in range(N):
        b.pulse = 1.0 + i * 0.13
        render(b)
    dt = (time.perf_counter() - t0) / N * 1000
    assert dt < 2.2, f"per-frame {dt:.2f} ms (budget mobile)"
    print(f"animasi kontinu: idle {len(ids)}/24, walk {len(wids)}/24, "
          f"helix {len(hids)}/20 state | {dt:.2f} ms/frame")


def test_procedural_only():
    src = inspect.getsource(L)
    assert "pygame.image.load" not in src


if __name__ == "__main__":
    test_all_modes_render()
    print("PASS all modes render")
    test_family_size()
    print("PASS family size")
    test_trail_attached()
    print("PASS trail attached")
    test_durations_match_ai()
    print("PASS durations == AI")
    test_hurt_flash_and_reactive_shadow()
    print("PASS hurt flash + shadow reaktif")
    test_animation_continuous_and_fast()
    test_procedural_only()
    print("PASS procedural + animasi kontinu")
    print("ALL DRAKAR ORIGINAL-MAX TESTS PASSED")
