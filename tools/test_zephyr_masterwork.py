#!/usr/bin/env python3
"""Regresi visual untuk Zephyr Procedural Masterwork.

Memastikan upgrade tidak kembali menjadi kumpulan body-part statis: rig,
staff, sayap, portrait LOD, dan pose harus semuanya dirender dari kode.
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
from heroes._bundle import _NS_zephyr as Z


def colors(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def render_pose(attack=False):
    surface = pygame.Surface((240, 240), pygame.SRCALPHA)
    hero = _ProbeEntity("zephyr", 120, 125)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    if attack:
        hero._zp_attack_progress = .52
        hero._zp_attack_active = True
        hero.range = 180
        Z._draw_zephyr_attack(surface, hero, 120, 125)
    else:
        Z._draw_zephyr_idle(surface, hero, 120, 125)
    return surface


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
    idle = render_pose(False)
    attack = render_pose(True)
    palette = colors(idle)

    # Exact swatches prove material layers reach the final arena render.
    assert Z.PALETTE["wing_shine"] in palette      # moth wing edge
    assert Z.PALETTE["thorn_light"] in palette     # living staff thorns
    assert Z.PALETTE["boot_light"] in palette      # planted ankle boots
    assert Z.PALETTE["gold_light"] in palette      # circlet / belt buckle
    assert Z.PALETTE["jewel_light"] in palette     # staff crystal
    assert Z.PALETTE["hair_tip"] in palette        # thorn crown tips

    rect = idle.get_bounding_rect(min_alpha=8)
    assert rect.height >= 100 and rect.width >= 75
    assert pygame.image.tobytes(idle, "RGBA") != pygame.image.tobytes(attack, "RGBA")


def test_staff_geometry_is_pose_driven():
    """Staff pulls back during wind-up then releases forward with the arm."""
    idle_tip = Z._staff_tip_local(1.2, "idle", 0.0)
    windup_tip = Z._staff_tip_local(1.2, "attack", .35)
    release_tip = Z._staff_tip_local(1.2, "attack", .60)
    assert windup_tip[0] < idle_tip[0] - 5
    assert release_tip[0] > idle_tip[0] + 8

    rest = pygame.Surface((220, 200), pygame.SRCALPHA)
    cast = pygame.Surface((220, 200), pygame.SRCALPHA)
    Z._draw_zephyr_elite(rest, 105, 110, 1, .8, "idle", 0.0)
    Z._draw_zephyr_elite(cast, 105, 110, 1, .8, "attack", .54)
    assert pygame.image.tobytes(rest, "RGBA") != pygame.image.tobytes(cast, "RGBA")


def test_portrait_lod_is_distinct():
    ui_source = open(os.path.join(ROOT, "ui_components", "_bundle.py"),
                     encoding="utf-8").read()
    assert "fake._portrait_hd = True" in ui_source

    normal = pygame.Surface((180, 180), pygame.SRCALPHA)
    portrait = pygame.Surface((180, 180), pygame.SRCALPHA)
    Z._draw_zephyr_elite(normal, 90, 100, 1, .8, "idle", 0.0, False)
    Z._draw_zephyr_elite(portrait, 90, 100, 1, .8, "idle", 0.0, True)
    assert pygame.image.tobytes(normal, "RGBA") != \
        pygame.image.tobytes(portrait, "RGBA")
    assert len(colors(portrait)) >= len(colors(normal))


def test_rig_has_real_animation_frames():
    """Walk/cast update joints, staff and wing tips rather than translation."""
    frames = set()
    for i in range(6):
        surface = pygame.Surface((180, 180), pygame.SRCALPHA)
        Z._draw_zephyr_elite(surface, 90, 100, 1,
                              i * 1.047, "walk", i / 5.0)
        frames.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(frames) == 6

    attacks = set()
    for i in range(6):
        surface = pygame.Surface((220, 200), pygame.SRCALPHA)
        Z._draw_zephyr_elite(surface, 100, 105, 1,
                              i * .3, "attack", i / 5.0)
        attacks.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(attacks) == 6


def test_skill_visuals_render_with_masterwork():
    """Q/W/E/R remain visible after the body rewrite and stay cache-safe."""
    for skill, timer in (("q", 120), ("w", 90), ("e", 90), ("r", 120)):
        hero = _ProbeEntity("zephyr", 130, 130)
        hero.pulse = 1.4
        hero.direction = hero.facing = 1
        hero.active_skill = skill
        hero.active_skill_timer = timer
        hero.target = _ProbeEntity("dummy", 200, 132)
        hero.target.alive = True
        if skill == "q":
            hero._bramble_origin = (200, 132)
        surface = pygame.Surface((360, 280), pygame.SRCALPHA)
        Z.draw_zephyr(surface, hero, 130, 130)
        rect = surface.get_bounding_rect(min_alpha=5)
        assert rect.width > 35 and rect.height > 35, skill


def test_silhouette_outline_exists():
    surface = pygame.Surface((180, 180), pygame.SRCALPHA)
    Z._draw_zephyr_elite(surface, 90, 100, 1, 1.2, "idle", 0.0)
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
    print("OK - Zephyr masterwork: rig, staff pose, portrait LOD, "
          "Q/W/E/R, outline, dan 12 frame animasi tervalidasi")
