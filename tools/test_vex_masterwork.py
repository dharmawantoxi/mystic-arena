#!/usr/bin/env python3
"""Regresi visual untuk Vex Procedural Masterwork.

Memastikan upgrade tidak kembali menjadi kumpulan body-part statis: rig
bone 2D berlapis, void-crown spiky, staff orb pose-driven, portrait LOD,
dan pose (idle/walk/attack) semuanya dirender dari kode tanpa PNG /
sprite sheet / image.load.

Jalankan:  python3 tools/test_vex_masterwork.py
"""
import inspect
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
from heroes import _ProbeEntity
from heroes._bundle import _NS_vex as V


def colors(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def render_pose(action="idle", progress=0.0):
    surface = pygame.Surface((260, 280), pygame.SRCALPHA)
    hero = _ProbeEntity("vex", 130, 140)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    if action == "attack":
        hero._vx_attack_progress = progress
        V._draw_vex_attack(surface, hero, 130, 140)
    elif action == "walk":
        V._draw_vex_walk(surface, hero, 130, 140)
    else:
        V._draw_vex_idle(surface, hero, 130, 140)
    return surface


def test_masterwork_is_procedural():
    source = inspect.getsource(V)
    assert "pygame.image.load" not in source
    assert callable(V._draw_vex_elite)
    assert callable(V._draw_elite_crown)
    assert callable(V._draw_elite_staff)
    assert callable(V._draw_elite_hood)
    assert callable(V._draw_vex_masterwork_details)
    assert callable(V._orb_tip_local)
    assert callable(V._staff_orb_position)
    # Body-part lama sudah benar-benar diganti satu rig.
    for old in ("_draw_cloak", "_draw_lower_robe", "_draw_torso",
                "_draw_idle_arms", "_draw_attack_arms", "_draw_arm_segment",
                "_draw_hand", "_draw_staff", "_draw_head_crown",
                "_draw_body_particles"):
        assert not hasattr(V, old), f"old part still present: {old}"


def test_material_details_and_pose():
    idle = render_pose("idle")
    attack = render_pose("attack", 0.5)
    palette = colors(idle)

    # Exact swatches prove material layers reach the final arena render.
    assert V.PALETTE["void_mid"] in palette      # crown / staff glow
    assert V.PALETTE["void_light"] in palette    # staff orb rim
    assert V.PALETTE["void_hot"] in palette      # eye slit / orb core
    assert V.PALETTE["robe_darkest"] in palette  # hood / robe
    assert V.PALETTE["armor_mid"] in palette     # pauldron plating
    assert V.PALETTE["staff_mid"] in palette     # staff shaft
    assert V.PALETTE["crown_tip"] in palette     # bright crown tips

    rect = idle.get_bounding_rect(min_alpha=8)
    assert rect.height >= 110 and rect.width >= 80
    assert pygame.image.tobytes(idle, "RGBA") != \
        pygame.image.tobytes(attack, "RGBA")


def test_staff_geometry_is_pose_driven():
    """Staff orb pulls back during wind-up then releases forward with the arm."""
    idle_tip = V._orb_tip_local(1.2, "idle", 0.0)
    windup_tip = V._orb_tip_local(1.2, "attack", 0.2)
    release_tip = V._orb_tip_local(1.2, "attack", 0.6)
    # Orb sweeps forward on release: release reaches farther forward (+x).
    assert release_tip[0] > idle_tip[0] + 8
    assert windup_tip[0] < release_tip[0]

    rest = pygame.Surface((240, 240), pygame.SRCALPHA)
    swing = pygame.Surface((240, 240), pygame.SRCALPHA)
    V._draw_vex_elite(rest, 115, 120, 1, 1.0, "idle", 0.0)
    V._draw_vex_elite(swing, 115, 120, 1, 1.0, "attack", 0.6)
    assert pygame.image.tobytes(rest, "RGBA") != \
        pygame.image.tobytes(swing, "RGBA")


def test_portrait_lod_is_distinct():
    ui_source = open(os.path.join(ROOT, "ui_components", "_bundle.py"),
                     encoding="utf-8").read()
    assert "fake._portrait_hd = True" in ui_source

    normal = pygame.Surface((220, 220), pygame.SRCALPHA)
    portrait = pygame.Surface((220, 220), pygame.SRCALPHA)
    V._draw_vex_elite(normal, 110, 110, 1, 1.0, "idle", 0.0, detail=False)
    V._draw_vex_elite(portrait, 110, 110, 1, 1.0, "idle", 0.0, detail=True)
    assert pygame.image.tobytes(normal, "RGBA") != \
        pygame.image.tobytes(portrait, "RGBA")
    assert len(colors(portrait)) >= len(colors(normal))


def test_rig_has_real_animation_frames():
    """Walk/attack mengubah sendi, crown, dan orb - bukan sticker translation."""
    frames = set()
    for i in range(6):
        surface = pygame.Surface((220, 240), pygame.SRCALPHA)
        V._draw_vex_elite(surface, 110, 115, 1,
                          i * 1.047, "walk", 0.0)
        frames.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(frames) == 6

    attacks = set()
    for i in range(6):
        surface = pygame.Surface((260, 250), pygame.SRCALPHA)
        V._draw_vex_elite(surface, 120, 115, 1,
                          i * 0.3, "attack", i / 5.0)
        attacks.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(attacks) == 6


def test_skill_visuals_render_with_masterwork():
    """Q/W/E/R tetap muncul setelah body rewrite dan tetap cache-safe."""
    from heroes import render_hero, clear_hero_sprite_cache
    clear_hero_sprite_cache()
    for skill, timer in (("q", 120), ("w", 90), ("e", 90), ("r", 120)):
        hero = _ProbeEntity("vex", 150, 150)
        hero.pulse = 1.4
        hero.direction = hero.facing = 1
        hero.active_skill = skill
        hero.active_skill_timer = timer
        hero.timer = 0
        hero.target = _ProbeEntity("dummy", 260, 152)
        hero.target.alive = True
        surface = pygame.Surface((360, 300), pygame.SRCALPHA)
        render_hero("vex", surface, hero, 150, 150)
        rect = surface.get_bounding_rect(min_alpha=5)
        assert rect.width > 35 and rect.height > 35, skill


def test_silhouette_outline_exists():
    surface = pygame.Surface((220, 240), pygame.SRCALPHA)
    V._draw_vex_elite(surface, 110, 115, 1, 1.2, "idle", 0.0)
    rect = surface.get_bounding_rect(min_alpha=8)
    dark = 0
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            c = surface.get_at((x, y))
            if c.a > 120 and max(c.r, c.g, c.b) < 24:
                dark += 1
    assert dark > 60


if __name__ == "__main__":
    test_masterwork_is_procedural()
    test_material_details_and_pose()
    test_staff_geometry_is_pose_driven()
    test_portrait_lod_is_distinct()
    test_rig_has_real_animation_frames()
    test_skill_visuals_render_with_masterwork()
    test_silhouette_outline_exists()
    print("OK - Vex masterwork: rig, staff pose, portrait LOD, "
          "Q/W/E/R, outline, dan 12 frame animasi tervalidasi")
