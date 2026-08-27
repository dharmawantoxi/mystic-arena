#!/usr/bin/env python3
"""Regresi visual untuk contoh upgrade maksimal hero procedural Thorne."""
import inspect
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
from heroes import _ProbeEntity
from heroes._bundle import _NS_thorne as T


def colors(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def render_pose(attack=False):
    surface = pygame.Surface((240, 240), pygame.SRCALPHA)
    hero = _ProbeEntity("thorne", 120, 125)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    if attack:
        hero._th_attack_progress = .52
        hero._th_attack_active = True
        T._draw_thorne_attack(surface, hero, 120, 125)
    else:
        T._draw_thorne_idle(surface, hero, 120, 125)
    return surface


def test_masterwork_is_procedural():
    source = inspect.getsource(T)
    assert "pygame.image.load" not in source
    assert callable(T._draw_thorne_elite)
    assert callable(T._draw_elite_club)
    assert callable(T._draw_elite_quill)
    assert callable(T._draw_thorne_masterwork_details)


def test_material_details_and_pose():
    idle = render_pose(False)
    attack = render_pose(True)
    palette = colors(idle)

    # Exact material swatches prove these layers reached the final render.
    assert T.PALETTE["tusk_light"] in palette      # tusks & claws
    assert T.PALETTE["belly_mid"] in palette       # belly patch
    assert T.PALETTE["gold_light"] in palette      # belt buckle
    assert T.PALETTE["cloth_light"] in palette     # torn war vest
    assert T.PALETTE["quill_tip"] in palette       # quill mane tips
    assert T.PALETTE["armor_shine"] in palette     # club spikes / pauldron

    rect = idle.get_bounding_rect(min_alpha=8)
    assert rect.height >= 100 and rect.width >= 75
    assert pygame.image.tobytes(idle, "RGBA") != pygame.image.tobytes(attack, "RGBA")


def test_portrait_lod_is_distinct():
    ui_source = open(os.path.join(ROOT, "ui_components", "_bundle.py"),
                     encoding="utf-8").read()
    assert "fake._portrait_hd = True" in ui_source

    normal = pygame.Surface((180, 180), pygame.SRCALPHA)
    portrait = pygame.Surface((180, 180), pygame.SRCALPHA)
    T._draw_thorne_elite(normal, 90, 95, 1, .8, "idle", 0.0, False)
    T._draw_thorne_elite(portrait, 90, 95, 1, .8, "idle", 0.0, True)
    assert pygame.image.tobytes(normal, "RGBA") != \
        pygame.image.tobytes(portrait, "RGBA")
    assert len(colors(portrait)) >= len(colors(normal))


def test_rig_has_real_animation_frames():
    """Walk/attack harus mengubah sendi dan siluet, bukan sticker translation."""
    frames = set()
    for i in range(6):
        surface = pygame.Surface((180, 180), pygame.SRCALPHA)
        T._draw_thorne_elite(surface, 90, 95, 1,
                             i * 1.047, "walk", i / 5.0)
        frames.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(frames) == 6

    attacks = set()
    for i in range(6):
        surface = pygame.Surface((220, 200), pygame.SRCALPHA)
        T._draw_thorne_elite(surface, 100, 100, 1,
                             i * .3, "attack", i / 5.0)
        attacks.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(attacks) == 6


if __name__ == "__main__":
    test_masterwork_is_procedural()
    test_material_details_and_pose()
    test_portrait_lod_is_distinct()
    test_rig_has_real_animation_frames()
    print("OK - Thorne procedural: gameplay + portrait LOD dan 12 frame tervalidasi")
