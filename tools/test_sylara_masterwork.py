#!/usr/bin/env python3
"""Regresi visual untuk upgrade maksimal hero procedural Sylara."""
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
from heroes._bundle import _NS_sylara as S


def colors(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def render_pose(attack=False):
    surface = pygame.Surface((240, 240), pygame.SRCALPHA)
    hero = _ProbeEntity("sylara", 120, 125)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    if attack:
        hero._sy_attack_progress = .42
        hero._sy_attack_active = True
        hero.range = 220
        S._draw_sylara_attack(surface, hero, 120, 125)
    else:
        S._draw_sylara_idle(surface, hero, 120, 125)
    return surface


def test_masterwork_is_procedural():
    source = inspect.getsource(S)
    assert "pygame.image.load" not in source
    assert callable(S._draw_sylara_elite)
    assert callable(S._draw_sylara_rig)
    assert callable(S._draw_elite_bow)
    assert callable(S._draw_elite_arrow)
    assert callable(S._draw_sylara_masterwork_details)
    # rig lama (torso/quiver/hood terpisah) sudah dihapus, bukan disisakan
    assert not hasattr(S, "_draw_head_hood")
    assert not hasattr(S, "_draw_idle_arms")
    assert not hasattr(S, "_draw_bow_idle")


def test_material_details_and_pose():
    idle = render_pose(False)
    attack = render_pose(True)
    palette = colors(idle)

    # Exact material swatches prove these layers reached the final render.
    assert S.PALETTE["gold_light"] in palette        # gesper sabuk
    assert S.PALETTE["hair_shine"] in palette        # kilau rambut
    assert S.PALETTE["leather_light"] in palette     # boot / sarung tangan
    assert S.PALETTE["eye_iris_light"] in palette    # mata hijau
    assert S.PALETTE["string_shine"] in palette      # tali busur

    rect = idle.get_bounding_rect(min_alpha=8)
    assert rect.height >= 100 and rect.width >= 75
    assert pygame.image.tobytes(idle, "RGBA") != pygame.image.tobytes(attack, "RGBA")


def test_bow_geometry_is_pose_driven():
    """Nock bergerak mundur mengikuti tarikan; busur bukan sticker."""
    rest = S._bow_nock((16, -6), .2, 0.0)
    drawn = S._bow_nock((16, -6), .2, 1.0)
    assert drawn[0] < rest[0] - 8

    slack = pygame.Surface((200, 200), pygame.SRCALPHA)
    taut = pygame.Surface((200, 200), pygame.SRCALPHA)
    S._draw_elite_bow(slack, lambda dx, dy: (int(100 + dx), int(100 + dy)),
                      1, (16, -6), .2, 0.0, 1.0)
    S._draw_elite_bow(taut, lambda dx, dy: (int(100 + dx), int(100 + dy)),
                      1, (16, -6), .2, 1.0, 1.0)
    assert pygame.image.tobytes(slack, "RGBA") != pygame.image.tobytes(taut, "RGBA")
    # anak panah hanya muncul saat tali ditarik
    assert S.PALETTE["arrow_feather"] in colors(taut)
    assert S.PALETTE["arrow_feather"] not in colors(slack)


def test_portrait_lod_is_distinct():
    ui_source = open(os.path.join(ROOT, "ui_components", "_bundle.py"),
                     encoding="utf-8").read()
    assert "fake._portrait_hd = True" in ui_source

    normal = pygame.Surface((180, 180), pygame.SRCALPHA)
    portrait = pygame.Surface((180, 180), pygame.SRCALPHA)
    S._draw_sylara_elite(normal, 90, 90, 1, .8, "idle", 0.0, detail=False)
    S._draw_sylara_elite(portrait, 90, 90, 1, .8, "idle", 0.0, detail=True)
    assert pygame.image.tobytes(normal, "RGBA") != \
        pygame.image.tobytes(portrait, "RGBA")
    assert len(colors(portrait)) >= len(colors(normal))


def test_rig_has_real_animation_frames():
    """Walk/attack harus mengubah sendi dan siluet, bukan sticker translation."""
    frames = set()
    for i in range(6):
        surface = pygame.Surface((180, 180), pygame.SRCALPHA)
        S._draw_sylara_elite(surface, 90, 90, 1, i * 1.047, "walk", i / 5.0)
        frames.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(frames) == 6

    attacks = set()
    for i in range(6):
        surface = pygame.Surface((220, 200), pygame.SRCALPHA)
        S._draw_sylara_elite(surface, 100, 100, 1, i * .3, "attack", i / 5.0)
        attacks.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(attacks) == 6

    # windrun adalah pose tersendiri, bukan idle yang digeser
    idle = pygame.Surface((180, 180), pygame.SRCALPHA)
    dash = pygame.Surface((180, 180), pygame.SRCALPHA)
    S._draw_sylara_elite(idle, 90, 90, 1, 1.2, "idle", 0.0)
    S._draw_sylara_elite(dash, 90, 90, 1, 1.2, "windrun", 0.0)
    assert pygame.image.tobytes(idle, "RGBA") != pygame.image.tobytes(dash, "RGBA")


def test_silhouette_outline_exists():
    """Outline gelap 1 px ala sprite referensi membungkus rig."""
    surface = pygame.Surface((180, 180), pygame.SRCALPHA)
    S._draw_sylara_elite(surface, 90, 90, 1, 1.2, "idle", 0.0)
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
    test_bow_geometry_is_pose_driven()
    test_portrait_lod_is_distinct()
    test_rig_has_real_animation_frames()
    test_silhouette_outline_exists()
    print("OK - Sylara procedural: gameplay + portrait LOD, busur pose-driven, "
          "12 frame animasi dan outline siluet tervalidasi")
