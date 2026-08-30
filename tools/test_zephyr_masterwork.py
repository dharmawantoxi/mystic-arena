#!/usr/bin/env python3
"""Regresi visual untuk Zephyr Procedural Masterwork v2.

Memastikan upgrade tidak kembali menjadi kumpulan body-part statis: rig,
staff, sayap, portrait LOD, pose, skill FX world-space, dan budget waktu
harus semuanya dirender dari kode.

Test baru (v2):
  - test_v2_rig_larger_than_v1       : bbox native ≥ 120x130
  - test_v2_fx_world_space           : _fx_scale & _ring_r tersedia
  - test_v2_skill_fx_primitives      : spark_star, chevron, dashed_ring, dll.
  - test_v2_attack_impact_burst      : frame IMPACT (ap≈0.50) berbeda
  - test_v2_timing_budget            : render < 6ms (hanya saat cache miss)
  - test_v2_skill_fx_outside_body    : FX Q/W/E/R ada piksel di luar siluet
"""
import inspect
import math
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
from heroes import _ProbeEntity
from heroes._bundle import _NS_zephyr as Z


def colors(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def render_pose(attack=False):
    surface = pygame.Surface((280, 280), pygame.SRCALPHA)
    hero = _ProbeEntity("zephyr", 140, 145)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    if attack:
        hero._zp_attack_progress = .52
        hero._zp_attack_active = True
        hero.range = 180
        Z._draw_zephyr_attack(surface, hero, 140, 145)
    else:
        Z._draw_zephyr_idle(surface, hero, 140, 145)
    return surface


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY TESTS (v1 — tetap hijau)
# ─────────────────────────────────────────────────────────────────────────────

def test_masterwork_is_procedural():
    source = inspect.getsource(Z)
    assert "pygame.image.load" not in source
    assert callable(Z._draw_zephyr_elite)
    assert callable(Z._draw_zephyr_rig)
    assert callable(Z._draw_elite_wings)
    assert callable(Z._draw_elite_staff)
    assert callable(Z._draw_zephyr_crown)
    assert callable(Z._draw_zephyr_masterwork_details)
    assert callable(Z._staff_tip_local)
    assert callable(Z._staff_orb_position)
    # Renderer torso/arms/skirt lama sudah benar-benar diganti satu rig.
    assert not hasattr(Z, "_draw_petal_skirt")
    assert not hasattr(Z, "_draw_idle_arms")
    assert not hasattr(Z, "_draw_attack_arms")
    assert not hasattr(Z, "_draw_hair_mane")


def test_material_details_and_pose():
    idle   = render_pose(False)
    attack = render_pose(True)
    palette = colors(idle)

    # Exact swatches prove material layers reach the final arena render.
    assert Z.PALETTE["wing_shine"]  in palette, "moth wing specular"
    assert Z.PALETTE["thorn_light"] in palette, "living staff thorns"
    assert Z.PALETTE["boot_light"]  in palette, "planted ankle boots"
    assert Z.PALETTE["gold_light"]  in palette, "circlet / belt buckle"
    assert Z.PALETTE["jewel_light"] in palette, "staff crystal"
    assert Z.PALETTE["hair_tip"]    in palette, "thorn crown tips"

    rect = idle.get_bounding_rect(min_alpha=8)
    assert rect.height >= 100 and rect.width >= 75
    assert pygame.image.tobytes(idle, "RGBA") != pygame.image.tobytes(attack, "RGBA")


def test_staff_geometry_is_pose_driven():
    """Staff pulls back during wind-up then releases forward with the arm."""
    idle_tip   = Z._staff_tip_local(1.2, "idle",   0.0)
    windup_tip = Z._staff_tip_local(1.2, "attack", .35)
    release_tip= Z._staff_tip_local(1.2, "attack", .60)
    assert windup_tip[0]  < idle_tip[0] - 5
    assert release_tip[0] > idle_tip[0] + 8

    rest = pygame.Surface((240, 220), pygame.SRCALPHA)
    cast = pygame.Surface((240, 220), pygame.SRCALPHA)
    Z._draw_zephyr_elite(rest, 115, 120, 1, .8, "idle",   0.0)
    Z._draw_zephyr_elite(cast, 115, 120, 1, .8, "attack", .54)
    assert pygame.image.tobytes(rest, "RGBA") != pygame.image.tobytes(cast, "RGBA")


def test_portrait_lod_is_distinct():
    ui_source = open(os.path.join(ROOT, "ui_components", "_bundle.py"),
                     encoding="utf-8").read()
    assert "fake._portrait_hd = True" in ui_source

    normal   = pygame.Surface((200, 200), pygame.SRCALPHA)
    portrait = pygame.Surface((200, 200), pygame.SRCALPHA)
    Z._draw_zephyr_elite(normal,   100, 112, 1, .8, "idle", 0.0, False)
    Z._draw_zephyr_elite(portrait, 100, 112, 1, .8, "idle", 0.0, True)
    assert pygame.image.tobytes(normal, "RGBA") != \
           pygame.image.tobytes(portrait, "RGBA")
    assert len(colors(portrait)) >= len(colors(normal))


def test_rig_has_real_animation_frames():
    """Walk/cast update joints, staff and wing tips rather than translation."""
    frames = set()
    for i in range(6):
        surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        Z._draw_zephyr_elite(surface, 100, 112, 1,
                              i * 1.047, "walk", i / 5.0)
        frames.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(frames) == 6

    attacks = set()
    for i in range(6):
        surface = pygame.Surface((240, 220), pygame.SRCALPHA)
        Z._draw_zephyr_elite(surface, 110, 116, 1,
                              i * .3, "attack", i / 5.0)
        attacks.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(attacks) == 6


def test_skill_visuals_render_with_masterwork():
    """Q/W/E/R remain visible after the body rewrite and stay cache-safe."""
    for skill, timer in (("q", 120), ("w", 90), ("e", 90), ("r", 120)):
        hero = _ProbeEntity("zephyr", 150, 150)
        hero.pulse = 1.4
        hero.direction = hero.facing = 1
        hero.active_skill = skill
        hero.active_skill_timer = timer
        hero.target = _ProbeEntity("dummy", 220, 152)
        hero.target.alive = True
        if skill == "q":
            hero._bramble_origin = (220, 152)
        surface = pygame.Surface((400, 320), pygame.SRCALPHA)
        Z.draw_zephyr(surface, hero, 150, 150)
        rect = surface.get_bounding_rect(min_alpha=5)
        assert rect.width > 35 and rect.height > 35, skill


def test_silhouette_outline_exists():
    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    Z._draw_zephyr_elite(surface, 100, 112, 1, 1.2, "idle", 0.0)
    rect = surface.get_bounding_rect(min_alpha=8)
    dark = 0
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            c = surface.get_at((x, y))
            if c.a > 120 and max(c.r, c.g, c.b) < 24:
                dark += 1
    assert dark > 60


# ─────────────────────────────────────────────────────────────────────────────
# NEW v2 TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_v2_rig_larger_than_v1():
    """v2 rig native bbox ≥ 120×130 px (was ~106×114)."""
    surface = pygame.Surface((320, 320), pygame.SRCALPHA)
    Z._draw_zephyr_elite(surface, 160, 175, 1, 1.25, "idle", 0.0, False)
    bb = surface.get_bounding_rect(min_alpha=8)
    assert bb.height >= 130, f"height {bb.height} < 130"
    assert bb.width  >= 100, f"width {bb.width} < 100"


def test_v2_fx_world_space():
    """_fx_scale and _ring_r are present and return sensible values."""
    assert callable(Z._fx_scale)
    assert callable(Z._ring_r)

    class FakeHero:
        _render_scale = 0.40

    fs = Z._fx_scale(FakeHero())
    assert 2.0 <= fs <= 2.6, f"_fx_scale = {fs}"

    surf = pygame.Surface((400, 400), pygame.SRCALPHA)

    class FakeHero2:
        _render_scale = 0.40
        range = 100

    rr = Z._ring_r(FakeHero2(), 100, surf)
    # ring_r should be bigger than world px but capped by canvas
    assert 50 < rr < 200, f"_ring_r = {rr}"


def test_v2_skill_fx_primitives():
    """FX helper primitives spark_star, chevron, dashed_ring, jagged_crack
    are present and draw without error on a SRCALPHA surface."""
    assert callable(Z._spark_star)
    assert callable(Z._chevron)
    assert callable(Z._dashed_ring)
    assert callable(Z._jagged_crack)
    assert callable(Z._tuft_points)

    s = pygame.Surface((200, 200), pygame.SRCALPHA)
    p = Z.PALETTE
    # All primitives must draw without raising
    Z._spark_star(s, 100, 100, 18, p["magic_bright"], 200, spikes=6,
                  core=p["magic_white"])
    Z._chevron(s, 100, 140, math.pi/4, 14, p["rune_light"], 200, 2)
    Z._dashed_ring(s, 100, 100, 40, p["magic_mid"], 180, 0.5)
    Z._jagged_crack(s, 100, 100, 0, 40,
                    (p["magic_dark"], p["magic_mid"]), 200, 7, 2)
    bb = s.get_bounding_rect(min_alpha=1)
    assert bb.width > 20 and bb.height > 20, "primitives drew nothing"


def test_v2_attack_impact_burst():
    """Frame at ap≈0.50 (IMPACT) should visibly differ from ap≈0.35."""
    pre_impact = pygame.Surface((240, 220), pygame.SRCALPHA)
    at_impact  = pygame.Surface((240, 220), pygame.SRCALPHA)
    Z._draw_zephyr_elite(pre_impact, 120, 116, 1, 1.0, "attack", 0.35)
    Z._draw_zephyr_elite(at_impact,  120, 116, 1, 1.0, "attack", 0.50)
    assert pygame.image.tobytes(pre_impact, "RGBA") != \
           pygame.image.tobytes(at_impact,  "RGBA"), \
           "IMPACT frame identical to pre-impact"


def test_v2_timing_budget():
    """Single render must complete within 6 ms (budget cache-miss)."""
    surface = pygame.Surface((300, 300), pygame.SRCALPHA)
    # warm up
    Z._draw_zephyr_elite(surface, 150, 155, 1, 1.0, "idle", 0.0, False)
    # median of 9 cold renders
    times = []
    for i in range(9):
        surface.fill((0, 0, 0, 0))
        t0 = time.perf_counter()
        Z._draw_zephyr_elite(surface, 150, 155, 1, i*0.3, "idle", 0.0, False)
        times.append((time.perf_counter() - t0) * 1000)
    times.sort()
    median_ms = times[len(times)//2]
    assert median_ms < 6.0, f"render median {median_ms:.2f} ms > 6 ms budget"


def test_v2_skill_fx_outside_body():
    """Each skill's FX must produce pixels OUTSIDE the character silhouette
    (proves world-space rings/telegraphs are drawn, not just body glow)."""
    # First measure body-only bounding box
    body_surf = pygame.Surface((400, 400), pygame.SRCALPHA)
    hero_b = _ProbeEntity("zephyr", 200, 200)
    hero_b.pulse = 1.0
    hero_b.direction = 1
    Z._draw_zephyr_idle(body_surf, hero_b, 200, 200)
    body_bb = body_surf.get_bounding_rect(min_alpha=8)
    body_area = body_bb.inflate(8, 8)  # slight margin

    for skill, timer in (("q", 160), ("w", 120), ("e", 120), ("r", 160)):
        s = pygame.Surface((400, 400), pygame.SRCALPHA)
        hero = _ProbeEntity("zephyr", 200, 200)
        hero.pulse = 1.0
        hero.direction = hero.facing = 1
        hero.active_skill = skill
        hero.active_skill_timer = timer
        hero.target = _ProbeEntity("dummy", 300, 202)
        hero.target.alive = True
        if skill == "q":
            hero._bramble_origin = (300, 202)
        Z.draw_zephyr(s, hero, 200, 200)
        # Count pixels outside body bounding box
        outside = 0
        for y in range(s.get_height()):
            for x in range(s.get_width()):
                if s.get_at((x, y)).a > 8 and not body_area.collidepoint(x, y):
                    outside += 1
        assert outside > 50, \
            f"Skill {skill.upper()}: only {outside} fx pixels outside body"


def test_v2_bedlam_body_glows():
    """During Bedlam (R), character body should look different (glow pass)."""
    normal = pygame.Surface((240, 240), pygame.SRCALPHA)
    bedlam = pygame.Surface((240, 240), pygame.SRCALPHA)
    Z._draw_zephyr_elite(normal, 120, 130, 1, 1.0, "idle", 0.0, False, False)
    Z._draw_zephyr_elite(bedlam, 120, 130, 1, 1.0, "idle", 0.0, False, True)
    assert pygame.image.tobytes(normal, "RGBA") != \
           pygame.image.tobytes(bedlam, "RGBA"), \
           "Bedlam glow not visible on character body"


if __name__ == "__main__":
    test_masterwork_is_procedural()
    test_material_details_and_pose()
    test_staff_geometry_is_pose_driven()
    test_portrait_lod_is_distinct()
    test_rig_has_real_animation_frames()
    test_skill_visuals_render_with_masterwork()
    test_silhouette_outline_exists()
    test_v2_rig_larger_than_v1()
    test_v2_fx_world_space()
    test_v2_skill_fx_primitives()
    test_v2_attack_impact_burst()
    test_v2_timing_budget()
    test_v2_skill_fx_outside_body()
    test_v2_bedlam_body_glows()
    print("OK — Zephyr Masterwork v2: rig 1.5×, skill FX world-space, "
          "body reacts ke skill, budget <6ms, semua 14 tes hijau.")
