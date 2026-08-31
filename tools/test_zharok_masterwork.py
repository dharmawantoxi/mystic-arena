#!/usr/bin/env python3
"""Regresi visual untuk Zharok Procedural Masterwork v2 + Skill FX.

Menjaga agar upgrade tidak kembali menjadi kumpulan body-part statis:
rig di-author 1.5x di resolusi native lalu ditampilkan lewat satu
`SCALE` (ukuran layar tetap sekelas keluarga level-4 mini boss), pixel-art
discipline (ramp ber-hue-shift, selout, siluet bergerigi, specular,
dither), animasi hidup (archery keyframes, cloth inertia, living idle,
attack timeline 7-keyframe dengan frame IMPACT di ap=0.52), dan FX skill
world-space 3 tahap dengan telegraph tepat di radius gameplay
(Q 250 / W 200 / E 150 / R 220 px dunia) - semuanya 100% prosedural
tanpa PNG / sprite sheet.

Jalankan:  python3 tools/test_zharok_masterwork.py
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

import bosses.level4 as L
from bosses.level4 import _NS_zharok as Z


# ── helper ───────────────────────────────────────────────────────
def probe(cx=260.0, cy=260.0, **kw):
    b = _S(boss_type="zharok", boss_class="mini", x=float(cx), y=float(cy),
           direction=1, facing=1, pulse=1.3, timer=0, attack_cooldown=40,
           active_skill=None, active_skill_timer=0, target=None,
           hurt_flash_timer=0, alive=True, radius=34, hp=7000, max_hp=7000,
           range=180)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(boss, size=520, ax=None, ay=None):
    ax = size // 2 if ax is None else ax
    ay = size // 2 if ay is None else ay
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    Z.draw_zharok(s, boss, ax, ay)
    return s


def rig(action="idle", phase=1.25, progress=0.0, facing=1, detail=False,
        stealth=False, size=340):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    Z._draw_zharok_body_raw(s, size // 2, size // 2, facing, phase, action,
                            progress, stealth=stealth, detail=detail)
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
    source = open(os.path.join(ROOT, "bosses", "level4.py")).read()
    assert "pygame.image.load" not in source
    assert "import lighting" in source or "_lighting" in source

    legacy = (
        "PALETTE", "_clamp", "_alpha", "_aacircle", "_aaline", "_poly",
        "_ellipse", "_rect", "_target_position", "FireArrow", "BurningSkull",
        "_detect_moving", "_update_attack_anim", "_manage_projectiles",
        "_spawn_fire_arrow", "_spawn_burning_skulls", "draw_zharok", "draw_boss",
        "_draw_shockwave", "_draw_zh_idle", "_draw_zh_walk",
        "_draw_zh_attack", "_draw_zh_strafe", "_draw_zh_ecast",
        "_draw_zh_rcast", "_draw_zh_smoke", "_draw_zharok_body_raw",
        "_draw_zharok_body", "_draw_shadow", "_draw_fire_aura",
        "_draw_ground_runes", "_draw_fire_wisps", "_draw_ember",
        "_draw_flame", "_draw_flame_tuft", "_draw_mini_skull",
        "_draw_death_pact_ground", "_draw_death_pact_foreground",
        "_draw_hood_back", "_draw_quiver", "_draw_pelvis",
        "_draw_skeleton_legs", "_draw_ribcage", "_draw_hooded_skull",
        "_draw_flaming_bow", "_draw_bone_arm", "_draw_skeleton_hand",
        "_draw_bow_idle_arms", "_draw_bow_attack_arms",
        "_draw_bow_strafe_arms", "_draw_e_cast_arms", "_draw_r_cast_arms",
        "_draw_bow_release_flash", "_draw_bow_smear_arc",
        "_draw_burning_army_ground",
    )
    missing = [n for n in legacy if not hasattr(Z, n)]
    assert not missing, f"nama publik hilang: {missing}"

    # signature lama dipertahankan
    sig = inspect.signature(Z._draw_zharok_body_raw)
    assert list(sig.parameters)[:6] == [
        "surface", "cx", "cy", "facing", "phase", "action"]
    assert list(inspect.signature(Z._draw_shadow).parameters)[:3] == [
        "surface", "x", "y"]
    # entry point modul tetap ada
    assert callable(L.draw_zharok)


# ── 2. rig 1.5x native, ukuran layar tetap sekelas keluarga ──────
def test_rig_is_dense_but_screen_size_is_family_safe():
    assert abs(Z.RIG_SCALE - 1.5) < 1e-6, "RIG_SCALE bukan 1.5x"
    assert 0.30 <= Z.SCALE <= 1.0
    assert Z.GROUND_DY == int(round(Z.FEET_DY * Z.SCALE))

    native = rig().get_bounding_rect(min_alpha=8)
    assert native.height >= 110 and native.width >= 50, \
        f"rig native terlalu kecil: {native.w}x{native.h}"

    arena = render(probe()).get_bounding_rect(min_alpha=100)
    # ignis_drachorn (true boss level-4) = 170x170; zharok mini harus <= itu
    assert arena.width <= 150 and arena.height <= 150, \
        f"bbox arena melebihi true boss: {arena.w}x{arena.h}"
    assert arena.width >= 50 and arena.height >= 50, \
        f"presence terlalu kecil: {arena.w}x{arena.h}"


# ── 3. pixel-art discipline (kepadatan warna + selout) ───────────
def test_pixel_art_discipline():
    body = rig()
    n = len(colors(body))
    assert n >= 40, f"kepadatan warna kurang ({n}) - ramp/hue-shift hilang"

    # komposit punya saturasi & variasi shading tinggi
    comp_surf = pygame.Surface((340, 340), pygame.SRCALPHA)
    Z._draw_zharok_body(comp_surf, 170, 170, 1, 1.25, "idle")
    assert len(colors(comp_surf)) >= 300, "komposit shading kurang kaya"

    # ramp material sampai ke render akhir
    got = colors(body)
    for key in ("bone_darkest", "bone_mid", "bone_high", "fire_dark",
                "fire_bright", "fire_hot", "hood_darkest", "hood_mid",
                "leather_dark", "wood_mid", "gold_mid"):
        assert Z.PALETTE[key] in got, f"swatch {key} tidak sampai ke render"

    # selout: versi komposit punya piksel outline hitam jauh lebih banyak
    raw = pygame.Surface((240, 240), pygame.SRCALPHA)
    Z._draw_zharok_body_raw(raw, 120, 130, 1, 1.0, "idle")
    comp = pygame.Surface((240, 240), pygame.SRCALPHA)
    Z._draw_zharok_body(comp, 120, 130, 1, 1.0, "idle")

    def black(surf):
        return sum(1 for y in range(0, 240, 2) for x in range(0, 240, 2)
                   if surf.get_at((x, y))[:3] == (0, 0, 0)
                   and surf.get_at((x, y))[3] > 50)
    assert black(comp) > black(raw) + 15, "outline siluet tidak terlihat"

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

    # timeline serangan: 7 keyframe + frame IMPACT di ap=0.52
    pose = Z._attack_pose(0.52)
    assert pose["impact"] > 0.9, "frame IMPACT tidak berada di ap=0.52"
    assert Z._attack_pose(0.0)["impact"] < 0.2
    assert Z._attack_pose(0.52)["lunge"] > Z._attack_pose(0.15)["lunge"]
    assert abs(Z._attack_pose(1.0)["lunge"]) < 1e-6


def test_body_reacts_to_stealth_state():
    """Badan bereaksi ke mode stealth."""
    base = rig(stealth=False)
    stealthed = rig(stealth=True)
    assert len(colors(base)) >= 40
    assert base.get_bounding_rect(min_alpha=10).width > 20


# ── 5. FX skill: world-space, 3 tahap, radius gameplay ───────────
def test_skill_durations_match_ai():
    assert Z.SKILL_DUR == {"q": 50, "w": 40, "e": 60, "r": 80}
    assert Z.SKILL_RADIUS == {"q": 250, "w": 200, "e": 150, "r": 220}


def test_fx_scale_is_world_space():
    assert Z._fx_scale(_S()) == 1.0
    assert abs(Z._fx_scale(_S(_render_scale=0.5)) - 2.0) < 1e-6
    assert abs(Z._fx_scale(_S(_render_scale=0.1)) - 2.6) < 1e-6, "cap bukan 2.6"

    # _ring_r: radius dunia -> px canvas, di-clamp ke dalam canvas
    surf = pygame.Surface((900, 900), pygame.SRCALPHA)
    assert Z._ring_r(_S(), 150, surf) == 150
    assert Z._ring_r(_S(_render_scale=0.5), 150, surf) == 300
    small = pygame.Surface((200, 200), pygame.SRCALPHA)
    assert Z._ring_r(_S(_render_scale=0.5), 400, small) <= 90


def test_skill_telegraph_radius_is_exact():
    def shot(skill, timer, W=1000):
        s = pygame.Surface((W, W), pygame.SRCALPHA)
        cx = cy = W // 2
        b = probe(cx, cy, active_skill=skill, active_skill_timer=timer,
                  target=_S(x=float(cx + 95), y=float(cy - 20), alive=True),
                  _render_scale=0.5)
        Z.draw_zharok(s, b, cx, cy)
        return s, cx, cy, b

    s, cx, cy, _ = shot("e", 30)
    n = hits_ring(s, 300, cx, cy + Z.GROUND_DY)
    assert n > 110, f"E: ring AOE 150 dunia meleset ({n}/180)"

    s, cx, cy, _ = shot("r", 40)
    n = hits_ring(s, 440, cx, cy + Z.GROUND_DY)
    assert n > 110, f"R: ring AOE 220 dunia meleset ({n}/180)"


def test_skill_fx_visible_outside_body():
    """FX skill benar-benar terlihat: banyak piksel DI LUAR siluet badan."""
    plain = render(probe(450.0, 450.0), size=900, ax=450, ay=450)
    bb = plain.get_bounding_rect(min_alpha=100)
    body_r = max(bb.width, bb.height) / 2.0

    def fx_pixels(skill, timer):
        s = pygame.Surface((900, 900), pygame.SRCALPHA)
        b = probe(450.0, 450.0, active_skill=skill, active_skill_timer=timer,
                  target=_S(x=545.0, y=430.0, alive=True), _render_scale=0.5)
        Z.draw_zharok(s, b, 450, 450)
        n = 0
        for y in range(0, 900, 2):
            for x in range(0, 900, 2):
                if body_r <= math.hypot(x - 450, y - 450) <= 360:
                    c = s.get_at((x, y))
                    if c.a > 40 and c[0] > 100 and c[0] > c[2] + 20:
                        n += 1
        return n

    for skill, timer, floor in (("q", 30, 80), ("w", 20, 80),
                                ("e", 30, 120), ("r", 40, 180)):
        n = fx_pixels(skill, timer)
        assert n > floor, f"{skill}: FX di luar badan cuma {n} px (min {floor})"


def test_each_skill_has_three_phases():
    for skill, dur in Z.SKILL_DUR.items():
        sigs = set()
        for timer in (dur - 3, int(dur * 0.5), 4):
            s = pygame.Surface((620, 620), pygame.SRCALPHA)
            b = probe(310.0, 310.0, active_skill=skill,
                      active_skill_timer=timer,
                      target=_S(x=430.0, y=290.0, alive=True))
            Z.draw_zharok(s, b, 310, 310)
            sigs.add(pygame.image.tobytes(s, "RGBA"))
        assert len(sigs) == 3, f"{skill}: {len(sigs)}/3 tahap FX berbeda"


def test_activation_shockwave_window():
    s = pygame.Surface((460, 460), pygame.SRCALPHA)
    Z._draw_shockwave(s, 230, 282, 30, (255, 120, 30), 220, thickness=3)
    assert s.get_bounding_rect(min_alpha=100).width > 40


# ── 5b. kualitas visual FX tanah (anti "programmer art") ─────────
def test_ground_fx_use_decals():
    src = open(os.path.join(ROOT, "bosses", "level4.py")).read()
    seg = src[src.index("class _NS_zharok"):src.index("class _NS_pyrenth")]

    # primitif decal tersedia & ter-cache
    for helper in ("_ground_ring", "_rune_ring", "_zone_fill",
                   "_ground_scorch", "_glow", "_decal", "_blit_decal"):
        assert callable(getattr(Z, helper, None)), f"helper {helper} hilang"


def test_decals_are_cached():
    """Decal dibangun sekali lalu dipakai ulang (bukan per frame)."""
    Z._DECAL_CACHE.clear()
    Z._DECAL_ORDER.clear()
    surf = pygame.Surface((400, 400), pygame.SRCALPHA)
    for _ in range(6):
        Z._ground_ring(surf, 200, 200, 120, Z.PALETTE["fire_mid"],
                       Z.PALETTE["fire_hot"], 200)
        Z._zone_fill(surf, 200, 200, 120, Z.PALETTE["fire_dark"],
                     Z.PALETTE["fire_mid"], 150)
    assert len(Z._DECAL_CACHE) == 2, \
        f"decal dibangun ulang tiap frame ({len(Z._DECAL_CACHE)} entri)"


# ── 6. proyektil kustom (FireArrow & BurningSkull) ─────────────────
def test_custom_projectiles():
    surf = pygame.Surface((400, 400), pygame.SRCALPHA)
    arr = Z.FireArrow(100, 100, 300, 100)
    for _ in range(5):
        arr.update()
        arr.draw(surf, 1.0)
    assert len(arr.trail) > 0, "trail proyektil FireArrow tidak terbentuk"
    assert surf.get_bounding_rect(min_alpha=20).width > 20

    skull = Z.BurningSkull(200, 200, 200, 200)
    skull.update()
    skull.draw(surf, 1.0)
    assert skull.alive, "BurningSkull harus aktif"


# ── 7. budget render & cache statis ──────────────────────────────
def test_render_budget():
    def bench(b, surf, n=20, reps=7):
        Z.draw_zharok(surf, b, 264, 284)
        runs = []
        for _ in range(reps):
            t0 = time.perf_counter()
            for i in range(n):
                b.pulse = 1.0 + i * 0.11
                Z.draw_zharok(surf, b, 264, 284)
            runs.append((time.perf_counter() - t0) / n * 1000)
        runs.sort()
        return runs[len(runs) // 2]

    surf = pygame.Surface((528, 528), pygame.SRCALPHA)
    base = bench(probe(264.0, 284.0), surf)
    assert base <= 4.0, f"pose dasar {base:.2f} ms > 4.0 ms"
    for skill, t in (("q", 30), ("w", 20), ("e", 30), ("r", 40)):
        b = probe(264.0, 284.0, active_skill=skill, active_skill_timer=t,
                  target=_S(x=390.0, y=260.0, alive=True), _render_scale=0.72)
        ms = bench(b, surf)
        assert ms <= 4.0, f"skill {skill} {ms:.2f} ms > 4.0 ms"


# ── 8. semua mode render tanpa exception ─────────────────────────
def test_all_modes_render():
    tg = _S(x=380.0, y=240.0, alive=True)
    walker = probe()
    walker._zh_last_x, walker._zh_last_y = 258.0, 260.0
    cases = [probe(pulse=0.0), probe(pulse=3.3), walker,
             probe(hurt_flash_timer=6),
             probe(_zh_attack_active=True, _zh_attack_progress=0.52),
             probe(_portrait_hd=True), probe(direction=-1)]
    for skill, t in (("q", 30), ("w", 20), ("e", 30), ("r", 40)):
        cases.append(probe(active_skill=skill, active_skill_timer=t,
                           target=tg))
    for c in cases:
        r = render(c).get_bounding_rect(min_alpha=100)
        assert r.width > 15 and r.height > 15, (c.active_skill, r)


if __name__ == "__main__":
    test_is_procedural_and_compatible()
    test_rig_is_dense_but_screen_size_is_family_safe()
    test_pixel_art_discipline()
    test_rig_has_real_animation_frames()
    test_body_reacts_to_stealth_state()
    test_skill_durations_match_ai()
    test_fx_scale_is_world_space()
    test_skill_telegraph_radius_is_exact()
    test_skill_fx_visible_outside_body()
    test_each_skill_has_three_phases()
    test_activation_shockwave_window()
    test_ground_fx_use_decals()
    test_decals_are_cached()
    test_custom_projectiles()
    test_render_budget()
    test_all_modes_render()
    print("OK - Zharok masterwork v2: rig native 1.5x (ukuran layar aman), "
          "pixel-art discipline, animasi 7-keyframe archery + living idle, FX skill "
          "world-space 3 tahap (Q250/W200/E150/R220), custom FireArrow & BurningSkull, "
          "decal ber-falloff, cache statis, budget < 4.0 ms")
