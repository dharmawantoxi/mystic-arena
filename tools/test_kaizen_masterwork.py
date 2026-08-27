#!/usr/bin/env python3
"""Regresi visual untuk contoh upgrade maksimal hero procedural Kaizen."""
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
from heroes._bundle import _NS_kaizen as K


def colors(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def render_pose(attack=False):
    surface = pygame.Surface((240, 240), pygame.SRCALPHA)
    hero = _ProbeEntity("kaizen", 120, 125)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    if attack:
        hero._kz_attack_progress = .52
        hero._kz_attack_active = True
        hero.range = 40
        K._draw_kaizen_attack(surface, hero, 120, 125)
    else:
        K._draw_kaizen_idle(surface, hero, 120, 125)
    return surface


def test_masterwork_is_procedural():
    source = inspect.getsource(K)
    assert "pygame.image.load" not in source
    assert callable(K._draw_kaizen_elite)
    assert callable(K._draw_elite_katana)
    assert callable(K._draw_saya_back)
    assert callable(K._draw_masterwork_details)


def test_material_details_and_pose():
    idle = render_pose(False)
    attack = render_pose(True)
    palette = colors(idle)

    # Exact material swatches prove these layers reached the final render.
    assert (204, 211, 216) in palette       # tabi socks
    assert (104, 27, 39) in palette         # lacquered saya
    assert K.PALETTE["gold_light"] in palette
    assert K.PALETTE["cloth_high"] in palette

    rect = idle.get_bounding_rect(min_alpha=8)
    assert rect.height >= 100 and rect.width >= 75
    assert pygame.image.tobytes(idle, "RGBA") != pygame.image.tobytes(attack, "RGBA")


if __name__ == "__main__":
    test_masterwork_is_procedural()
    test_material_details_and_pose()
    print("OK - Kaizen masterwork 100% procedural, detail material dan pose tervalidasi")
