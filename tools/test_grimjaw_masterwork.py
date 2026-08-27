#!/usr/bin/env python3
"""Regresi visual untuk Grimjaw Procedural Masterwork.

Memastikan upgrade tidak kembali menjadi kumpulan body-part statis: rig
bone 2D berlapis, flame blade pose-driven, mask putih ber-strip darah,
portrait LOD, dan pose (idle/walk/attack/spin/omnislash) semuanya
dirender dari kode tanpa PNG / sprite sheet / image.load.

Jalankan:  python3 tools/test_grimjaw_masterwork.py
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
from heroes._bundle import _NS_grimjaw as G


def colors(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def render_pose(action="idle", progress=0.0):
    surface = pygame.Surface((260, 260), pygame.SRCALPHA)
    hero = _ProbeEntity("grimjaw", 130, 135)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    if action == "attack":
        hero._gj_attack_progress = progress
        G._draw_grimjaw_attack(surface, hero, 130, 135)
    elif action == "spin":
        G._draw_grimjaw_body(surface, 130, 135, 1, 1.0, "spin",
                             spin_phase=2.0)
    elif action == "walk":
        G._draw_grimjaw_walk(surface, hero, 130, 135)
    else:
        G._draw_grimjaw_idle(surface, hero, 130, 135)
    return surface


def test_masterwork_is_procedural():
    source = inspect.getsource(G)
    assert "pygame.image.load" not in source
    assert callable(G._draw_grimjaw_elite)
    assert callable(G._draw_elite_flame_blade)
    assert callable(G._draw_elite_mask)
    assert callable(G._draw_elite_flame_mane)
    assert callable(G._draw_grimjaw_masterwork_details)
    assert callable(G._blade_angle)
    assert callable(G._blade_tip_local)
    # Body-part lama sudah benar-benar diganti satu rig.
    for old in ("_draw_torso", "_draw_pauldrons", "_draw_head_mask",
                "_draw_hair_back", "_draw_hair_front", "_draw_sword_arm",
                "_draw_left_arm", "_draw_muscular_arm", "_draw_fire_sword",
                "_draw_lower_body_flowing"):
        assert not hasattr(G, old), f"old part still present: {old}"


def test_material_details_and_pose():
    idle = render_pose("idle")
    attack = render_pose("attack", 0.5)
    palette = colors(idle)

    # Exact swatches prove material layers reach the final arena render.
    assert G.PALETTE["mask_light"] in palette       # white mask
    assert G.PALETTE["blood_mid"] in palette        # blood stripes
    assert G.PALETTE["gold_mid"] in palette         # pauldron trim / buckle
    assert G.PALETTE["red_mid"] in palette          # loincloth / chest panel
    assert G.PALETTE["fire_mid"] in palette         # flame blade
    assert G.PALETTE["fire_hot"] in palette         # blade hot core
    assert G.PALETTE["metal_light"] in palette      # boot / pauldron steel
    assert G.PALETTE["hair_mid"] in palette         # fire mane

    rect = idle.get_bounding_rect(min_alpha=8)
    assert rect.height >= 110 and rect.width >= 70
    assert pygame.image.tobytes(idle, "RGBA") != \
        pygame.image.tobytes(attack, "RGBA")


def test_blade_geometry_is_pose_driven():
    """Blade pulls back during wind-up then releases forward with the arm."""
    idle_angle = G._blade_angle(1.2, "idle", 0.0)
    windup_angle = G._blade_angle(1.2, "attack", 0.1)
    release_angle = G._blade_angle(1.2, "attack", 0.65)
    idle_tip = G._blade_tip_local(1.2, "idle", 0.0)
    windup_tip = G._blade_tip_local(1.2, "attack", 0.1)
    release_tip = G._blade_tip_local(1.2, "attack", 0.65)
    # Blade sweeps forward: release reaches farther forward (+x is facing).
    assert release_tip[0] > idle_tip[0] + 8
    assert windup_tip[0] < release_tip[0]
    # Wind-up tucks the blade back/up compared with the forward release.
    assert windup_angle < release_angle

    rest = pygame.Surface((240, 220), pygame.SRCALPHA)
    swing = pygame.Surface((240, 220), pygame.SRCALPHA)
    G._draw_grimjaw_elite(rest, 115, 115, 1, 1.0, "idle", 0.0)
    G._draw_grimjaw_elite(swing, 115, 115, 1, 1.0, "attack", 0.65)
    assert pygame.image.tobytes(rest, "RGBA") != \
        pygame.image.tobytes(swing, "RGBA")


def test_portrait_lod_is_distinct():
    ui_source = open(os.path.join(ROOT, "ui_components", "_bundle.py"),
                     encoding="utf-8").read()
    assert "fake._portrait_hd = True" in ui_source

    normal = pygame.Surface((200, 200), pygame.SRCALPHA)
    portrait = pygame.Surface((200, 200), pygame.SRCALPHA)
    G._draw_grimjaw_elite(normal, 100, 100, 1, 1.0, "idle", 0.0,
                          detail=False)
    G._draw_grimjaw_elite(portrait, 100, 100, 1, 1.0, "idle", 0.0,
                          detail=True)
    assert pygame.image.tobytes(normal, "RGBA") != \
        pygame.image.tobytes(portrait, "RGBA")
    assert len(colors(portrait)) >= len(colors(normal))


def test_rig_has_real_animation_frames():
    """Walk/attack mengubah sendi, mane, dan blade - bukan sticker translation."""
    frames = set()
    for i in range(6):
        surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        G._draw_grimjaw_elite(surface, 100, 100, 1,
                              i * 1.047, "walk", 0.0)
        frames.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(frames) == 6

    attacks = set()
    for i in range(6):
        surface = pygame.Surface((260, 240), pygame.SRCALPHA)
        G._draw_grimjaw_elite(surface, 120, 115, 1,
                              i * 0.3, "attack", i / 5.0)
        attacks.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(attacks) == 6


def test_skill_visuals_render_with_masterwork():
    """Q/W/E/R tetap muncul setelah body rewrite dan tetap cache-safe."""
    from heroes import render_hero, clear_hero_sprite_cache
    clear_hero_sprite_cache()
    for skill, timer in (("q", 120), ("w", 90), ("e", 90), ("r", 120)):
        hero = _ProbeEntity("grimjaw", 150, 150)
        hero.pulse = 1.4
        hero.direction = hero.facing = 1
        hero.active_skill = skill
        hero.active_skill_timer = timer
        hero.timer = 0
        hero.target = _ProbeEntity("dummy", 260, 152)
        hero.target.alive = True
        surface = pygame.Surface((360, 300), pygame.SRCALPHA)
        render_hero("grimjaw", surface, hero, 150, 150)
        rect = surface.get_bounding_rect(min_alpha=5)
        assert rect.width > 35 and rect.height > 35, skill


def test_silhouette_outline_exists():
    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    G._draw_grimjaw_elite(surface, 100, 100, 1, 1.2, "idle", 0.0)
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
    test_blade_geometry_is_pose_driven()
    test_portrait_lod_is_distinct()
    test_rig_has_real_animation_frames()
    test_skill_visuals_render_with_masterwork()
    test_silhouette_outline_exists()
    print("OK - Grimjaw masterwork: rig, blade pose, portrait LOD, "
          "Q/W/E/R, outline, dan 12 frame animasi tervalidasi")
