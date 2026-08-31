#!/usr/bin/env python3
"""Regresi visual untuk Gorath Procedural Masterwork v2 + Skill FX.

Menjaga agar upgrade tidak kembali menjadi kumpulan body-part statis:
rig di-author 1.5x di resolusi native lalu ditampilkan lewat satu
`SCALE` (ukuran layar tetap sekelas keluarga level-2), pixel-art
discipline (ramp ber-hue-shift, selout, siluet bergerigi, specular,
dither), animasi hidup (solver plume, inersia rambut/kain, attack
7-keyframe dengan frame IMPACT), dan FX skill world-space 3 tahap
dengan telegraph tepat di radius gameplay (W 150 / E 85 / R 190 px
dunia) - semuanya 100% prosedural tanpa PNG / sprite sheet.

Jalankan:  python3 tools/test_gorath_masterwork.py
"""
import inspect
import math
import os
import sys
import time
from types import SimpleNamespace as _S

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import bosses.level2 as L
from bosses.level2 import _NS_gorath as G


# ── helper ───────────────────────────────────────────────────────
def probe(cx=260.0, cy=260.0, **kw):
    b = _S(boss_type="gorath", boss_class="mini", x=float(cx), y=float(cy),
           direction=1, facing=1, pulse=1.3, timer=0, attack_cooldown=44,
           active_skill=None, active_skill_timer=0, target=None,
           hurt_flash_timer=0, alive=True, radius=36, hp=9000, max_hp=9000,
           range=58)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(boss, size=520, ax=None, ay=None):
    ax = size // 2 if ax is None else ax
    ay = size // 2 if ay is None else ay
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    G.draw_gorath(s, boss, ax, ay)
    return s


def rig(action="idle", phase=1.25, progress=0.0, facing=1, detail=False,
        rage=False, hunting=False, size=340):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    G._draw_gorath_body_raw(s, size // 2, size // 2, facing, phase, action,
                            progress, rage=rage, hunting=hunting,
                            detail=detail)
    return s


def colors(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def hits_ring(surf, r_px, cx, cy, tol=3):
    n = 0
    for a in range(0, 360, 2):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        for dr in range(-tol, tol + 1):
            x, y = int(cx + ca * (r_px + dr)), int(cy + sa * (r_px + dr))
            if 0 <= x < surf.get_width() and 0 <= y < surf.get_height() \
                    and surf.get_at((x, y)).a > 30:
                n += 1
                break
    return n


# ── 1. prosedural + nama publik utuh ─────────────────────────────
def test_is_procedural_and_compatible():
    source = open(os.path.join(ROOT, "bosses", "level2.py")).read()
    assert "pygame.image.load" not in source
    assert "import lighting" in source

    legacy = ("PALETTE", "_clamp", "_alpha", "_aacircle", "_aaline", "_poly",
              "_ellipse", "_rect", "_target_position", "BloodProjectile",
              "_detect_moving", "_update_attack_anim", "_manage_projectiles",
              "_spawn_projectile", "draw_gorath", "draw_boss",
              "_draw_shockwave", "_draw_gorath_idle", "_draw_gorath_walk",
              "_draw_gorath_attack", "_draw_gorath_body_raw",
              "_draw_gorath_body", "_draw_shadow", "_draw_blood_aura",
              "_draw_ground_blood_pool", "_draw_blood_wisps",
              "_draw_blood_trail", "_draw_blood_splatter",
              "_draw_blood_droplet", "_draw_blood_streak",
              "_draw_blade_swing_arc", "_draw_swing_impact",
              "_draw_bloodrage", "_draw_bloodrite_ground", "_draw_bloodrite",
              "_draw_thirst", "_draw_rupture_ground", "_draw_rupture",
              "_draw_loincloth", "_draw_torso", "_draw_shoulders",
              "_draw_gorath_head", "_draw_spiky_hair", "_draw_idle_arms",
              "_draw_attack_arms", "_draw_arm_segment", "_draw_hand",
              "_draw_curved_blade", "_draw_curved_blade_angled",
              "_draw_body_blood_drips")
    missing = [n for n in legacy if not hasattr(G, n)]
    assert not missing, f"nama publik hilang: {missing}"

    # signature lama dipertahankan
    sig = inspect.signature(G._draw_gorath_body_raw)
    assert list(sig.parameters)[:6] == [
        "surface", "cx", "cy", "facing", "phase", "action"]
    assert list(inspect.signature(G._draw_shadow).parameters) == [
        "surface", "x", "y", "lift"]
    # entry point modul tetap ada
    assert callable(L.draw_gorath)


# ── 2. rig 1.5x native, ukuran layar tetap sekelas keluarga ──────
def test_rig_is_dense_but_screen_size_is_family_safe():
    assert abs(G.RIG_SCALE - 1.5) < 1e-6, "RIG_SCALE bukan 1.5x"
    # satu SCALE untuk semua jalur (boss / lane / portrait)
    assert 0.30 <= G.SCALE <= 1.0
    assert G.GROUND_DY == int(round(G.FEET_DY * G.SCALE))

    native = rig().get_bounding_rect(min_alpha=8)
    assert native.height >= 120 and native.width >= 90, \
        f"rig native terlalu kecil: {native.w}x{native.h}"

    arena = render(probe()).get_bounding_rect(min_alpha=100)
    # alchemist (true boss level-2) = 130x119; gorath mini harus <= itu
    assert arena.width <= 130 and arena.height <= 119, \
        f"bbox arena melebihi true boss: {arena.w}x{arena.h}"
    assert arena.width >= 60 and arena.height >= 60, \
        f"presence terlalu kecil: {arena.w}x{arena.h}"


# ── 3. pixel-art discipline (kepadatan warna + selout) ───────────
def test_pixel_art_discipline():
    body = rig()
    n = len(colors(body))
    assert n >= 120, f"kepadatan warna kurang ({n}) - ramp/hue-shift hilang"

    # ramp material sampai ke render akhir
    got = colors(body)
    for key in ("skin_darkest", "skin_mid", "skin_high", "blood_dark",
                "blood_bright", "bone_light", "metal_light", "leather_dark",
                "hair_mid", "gold_mid"):
        assert G.PALETTE[key] in got, f"swatch {key} tidak sampai ke render"

    # selout: versi komposit punya piksel outline hitam jauh lebih banyak
    raw = pygame.Surface((240, 240), pygame.SRCALPHA)
    G._draw_gorath_body_raw(raw, 120, 130, 1, 1.0, "idle")
    comp = pygame.Surface((240, 240), pygame.SRCALPHA)
    G._draw_gorath_body(comp, 120, 130, 1, 1.0, "idle")

    def black(surf):
        return sum(1 for y in range(0, 240, 2) for x in range(0, 240, 2)
                   if surf.get_at((x, y))[:3] == (0, 0, 0)
                   and surf.get_at((x, y))[3] > 50)
    assert black(comp) > black(raw) + 20, "outline siluet tidak terlihat"

    # portrait LOD menambah micro-detail
    assert len(colors(rig(detail=True))) > len(colors(rig(detail=False)))


# ── 4. animasi hidup (bukan sticker) ─────────────────────────────
def test_rig_has_real_animation_frames():
    idle = {pygame.image.tobytes(rig("idle", i * 0.52), "RGBA")
            for i in range(8)}
    walk = {pygame.image.tobytes(rig("walk", i * 0.785), "RGBA")
            for i in range(8)}
    atk = {pygame.image.tobytes(rig("attack", 1.0, i / 9.0), "RGBA")
           for i in range(10)}
    assert len(idle) == 8, f"idle beku ({len(idle)}/8) - living idle hilang"
    assert len(walk) == 8, f"walk beku ({len(walk)}/8)"
    assert len(atk) >= 9, f"attack kurang keyframe ({len(atk)}/10)"

    # timeline serangan: 7 keyframe + frame IMPACT di ap=0.54
    pose = G._attack_pose(0.54)
    assert pose["impact"] > 0.9, "frame IMPACT tidak berada di ap=0.54"
    assert G._attack_pose(0.0)["impact"] < 0.2
    # lunge memuncak di sekitar impact lalu kembali
    assert G._attack_pose(0.54)["lunge"] > G._attack_pose(0.14)["lunge"]
    assert abs(G._attack_pose(1.0)["lunge"]) < 1e-6

    # solver plume: fase kontak kiri/kanan bergantian
    a = rig("walk", 0.0)
    b = rig("walk", math.pi / 2.2)
    assert pygame.image.tobytes(a, "RGBA") != pygame.image.tobytes(b, "RGBA")


def test_body_reacts_to_skill_state():
    """Badan ikut menyala saat buff aktif (rune dada / mata / bilah)."""
    base = rig(rage=False, hunting=False)
    raged = rig(rage=True)
    hunt = rig(hunting=True)
    assert pygame.image.tobytes(base, "RGBA") != pygame.image.tobytes(raged, "RGBA")
    assert pygame.image.tobytes(base, "RGBA") != pygame.image.tobytes(hunt, "RGBA")


# ── 5. FX skill: world-space, 3 tahap, radius gameplay ───────────
def test_skill_durations_match_ai():
    assert G.SKILL_DUR == {"q": 90, "w": 60, "e": 35, "r": 90}
    assert G.SKILL_RADIUS == {"w": 150, "e": 85, "r": 190}


def test_fx_scale_is_world_space():
    assert G._fx_scale(_S()) == 1.0
    assert abs(G._fx_scale(_S(_render_scale=0.5)) - 2.0) < 1e-6
    assert abs(G._fx_scale(_S(_render_scale=0.1)) - 2.6) < 1e-6, "cap bukan 2.6"

    # _ring_r: radius dunia -> px canvas, di-clamp ke dalam canvas
    surf = pygame.Surface((900, 900), pygame.SRCALPHA)
    assert G._ring_r(_S(), 150, surf) == 150
    assert G._ring_r(_S(_render_scale=0.5), 150, surf) == 300
    small = pygame.Surface((200, 200), pygame.SRCALPHA)
    assert G._ring_r(_S(_render_scale=0.5), 400, small) <= 90


def test_skill_telegraph_radius_is_exact():
    def shot(skill, timer, W=1000):
        s = pygame.Surface((W, W), pygame.SRCALPHA)
        cx = cy = W // 2
        b = probe(cx, cy, active_skill=skill, active_skill_timer=timer,
                  target=_S(x=float(cx + 95), y=float(cy - 20), alive=True),
                  _render_scale=0.5)
        G.draw_gorath(s, b, cx, cy)
        return s, cx, cy, b

    s, cx, cy, _ = shot("w", 40)
    n = hits_ring(s, 300, cx, cy + G.GROUND_DY - 8)
    assert n > 120, f"W: ring AOE 150 dunia meleset ({n}/180)"

    s, cx, cy, b = shot("e", 24)
    tx, ty = G._target_position(b, cx, cy)
    n = hits_ring(s, 170, tx, ty)
    assert n > 120, f"E: ring AOE 85 dunia meleset di target ({n}/180)"

    s, cx, cy, _ = shot("r", 60)
    n = hits_ring(s, 380, cx, cy + G.GROUND_DY)
    assert n > 100, f"R: ring AOE 190 dunia meleset di caster ({n}/180)"


def test_skill_fx_visible_outside_body():
    """FX skill benar-benar terlihat: banyak piksel DI LUAR siluet badan."""
    plain = render(probe(450.0, 450.0), size=900, ax=450, ay=450)
    bb = plain.get_bounding_rect(min_alpha=100)
    body_r = max(bb.width, bb.height) / 2.0

    def fx_pixels(skill, timer):
        s = pygame.Surface((900, 900), pygame.SRCALPHA)
        b = probe(450.0, 450.0, active_skill=skill, active_skill_timer=timer,
                  target=_S(x=545.0, y=430.0, alive=True), _render_scale=0.5)
        G.draw_gorath(s, b, 450, 450)
        n = 0
        for y in range(0, 900, 2):
            for x in range(0, 900, 2):
                if body_r <= math.hypot(x - 450, y - 450) <= 340:
                    c = s.get_at((x, y))
                    if c.a > 60 and c[0] > 110 and c[0] > c[2] + 30:
                        n += 1
        return n

    for skill, timer, floor in (("q", 50, 120), ("w", 40, 120),
                                ("e", 24, 100), ("r", 60, 200)):
        n = fx_pixels(skill, timer)
        assert n > floor, f"{skill}: FX di luar badan cuma {n} px (min {floor})"


def test_each_skill_has_three_phases():
    for skill, dur in G.SKILL_DUR.items():
        sigs = set()
        for timer in (dur - 4, int(dur * 0.6), 6):
            s = pygame.Surface((620, 620), pygame.SRCALPHA)
            b = probe(310.0, 310.0, active_skill=skill,
                      active_skill_timer=timer,
                      target=_S(x=430.0, y=290.0, alive=True))
            G.draw_gorath(s, b, 310, 310)
            sigs.add(pygame.image.tobytes(s, "RGBA"))
        assert len(sigs) == 3, f"{skill}: {len(sigs)}/3 tahap FX berbeda"


def test_activation_shockwave_window():
    """Aktivasi tiap skill = gelombang kejut 12 frame pertama."""
    s = pygame.Surface((460, 460), pygame.SRCALPHA)
    G._draw_shockwave(s, 230, 282, 6, 12, (255, 60, 50), (255, 200, 120))
    assert s.get_bounding_rect(min_alpha=100).width > 40
    s2 = pygame.Surface((460, 460), pygame.SRCALPHA)
    G._draw_shockwave(s2, 230, 282, 13, 12, (255, 60, 50), (255, 200, 120))
    assert s2.get_bounding_rect(min_alpha=100).width <= 2
    src = inspect.getsource(G.draw_gorath)
    assert "_draw_shockwave" in src and "age < 12" in src


# ── 6. cache statis + budget render ──────────────────────────────
def test_static_surfaces_are_cached():
    G._STATIC_SURFACES.clear()
    G._aura_cache = None
    G._shadow_cache = None
    b = probe()
    render(b)
    first = dict(G._STATIC_SURFACES)
    assert first, "tidak ada surface statis yang di-cache"
    assert G._aura_cache is not None and G._shadow_cache is not None
    render(b)
    for key, surf in G._STATIC_SURFACES.items():
        assert surf is first[key], f"surface statis '{key}' dibangun ulang"


def test_render_budget():
    def bench(b, surf, n=20, reps=7):
        G.draw_gorath(surf, b, 264, 284)
        runs = []
        for _ in range(reps):
            t0 = time.perf_counter()
            for i in range(n):
                b.pulse = 1.0 + i * 0.11
                G.draw_gorath(surf, b, 264, 284)
            runs.append((time.perf_counter() - t0) / n * 1000)
        runs.sort()
        return runs[len(runs) // 2]

    surf = pygame.Surface((528, 528), pygame.SRCALPHA)
    base = bench(probe(264.0, 284.0), surf)
    assert base <= 3.5, f"pose dasar {base:.2f} ms > 3.5 ms"
    for skill, t in (("q", 50), ("w", 30), ("e", 20), ("r", 60)):
        b = probe(264.0, 284.0, active_skill=skill, active_skill_timer=t,
                  target=_S(x=390.0, y=260.0, alive=True), _render_scale=0.72)
        ms = bench(b, surf)
        assert ms <= 3.5, f"skill {skill} {ms:.2f} ms > 3.5 ms"


def test_fx_clamped_inside_canvas():
    """FX tidak boleh meluber keluar canvas cache hero (ter-clamp)."""
    W = 300
    s = pygame.Surface((W, W), pygame.SRCALPHA)
    b = probe(150.0, 150.0, active_skill="r", active_skill_timer=60,
              target=_S(x=260.0, y=130.0, alive=True), _render_scale=0.25)
    G.draw_gorath(s, b, 150, 150)
    assert G._ring_r(b, 190, s) <= W // 2 - 10


# ── 7. semua mode render tanpa exception ─────────────────────────
def test_all_modes_render():
    tg = _S(x=380.0, y=240.0, alive=True)
    walker = probe()
    walker._gor_last_x, walker._gor_last_y = 258.0, 260.0
    cases = [probe(pulse=0.0), probe(pulse=3.3), walker,
             probe(hurt_flash_timer=6),
             probe(_gor_attack_active=True, _gor_attack_progress=0.54),
             probe(_portrait_hd=True), probe(direction=-1)]
    for skill, t in (("q", 50), ("w", 30), ("e", 20), ("r", 60)):
        cases.append(probe(active_skill=skill, active_skill_timer=t,
                           target=tg))
    for c in cases:
        r = render(c).get_bounding_rect(min_alpha=100)
        assert r.width > 20 and r.height > 20, (c.active_skill, r)


if __name__ == "__main__":
    test_is_procedural_and_compatible()
    test_rig_is_dense_but_screen_size_is_family_safe()
    test_pixel_art_discipline()
    test_rig_has_real_animation_frames()
    test_body_reacts_to_skill_state()
    test_skill_durations_match_ai()
    test_fx_scale_is_world_space()
    test_skill_telegraph_radius_is_exact()
    test_skill_fx_visible_outside_body()
    test_each_skill_has_three_phases()
    test_activation_shockwave_window()
    test_static_surfaces_are_cached()
    test_render_budget()
    test_fx_clamped_inside_canvas()
    test_all_modes_render()
    print("OK - Gorath masterwork v2: rig native 1.5x (ukuran layar aman), "
          "pixel-art discipline, animasi 7-keyframe + solver plume, FX skill "
          "world-space 3 tahap (W150/E85/R190), cache statis, budget 3.5 ms")
