#!/usr/bin/env python3
"""Regresi untuk HD readability pass hero procedural."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import heroes


def test_post_scale_edge():
    src = pygame.Surface((8, 8), pygame.SRCALPHA)
    src.fill((0, 0, 0, 0))
    pygame.draw.rect(src, (120, 210, 255, 255), (2, 2, 4, 4))

    blue, pad = heroes._finish_hd_sprite(src, "blue")
    red, red_pad = heroes._finish_hd_sprite(src, "red")

    assert pad == red_pad == 1
    assert blue.get_size() == red.get_size() == (10, 10)
    # Isi sprite tidak berubah dan outline ada tepat di luarnya.
    assert blue.get_at((3, 3)) == src.get_at((2, 2))
    assert blue.get_at((2, 3)).a > 0
    assert blue.get_at((2, 3)) != red.get_at((2, 3))


def test_hd_size_and_cached_anchor():
    assert heroes.HERO_GLOBAL_SCALE >= 0.75
    heroes.clear_hero_sprite_cache()
    hero = heroes._ProbeEntity("grimjaw", 100, 100)
    dst = pygame.Surface((220, 220), pygame.SRCALPHA)

    heroes.render_hero("grimjaw", dst, hero, 100, 100)
    first = dst.copy()
    dst.fill((0, 0, 0, 0))
    heroes.render_hero("grimjaw", dst, hero, 100, 100)

    assert first.get_bounding_rect(min_alpha=8).height >= 50
    assert dst.get_bounding_rect(min_alpha=8) == first.get_bounding_rect(min_alpha=8)
    assert heroes.hero_cache_stats()["hits"] == 1


if __name__ == "__main__":
    test_post_scale_edge()
    test_hd_size_and_cached_anchor()
    print("OK - hero procedural lebih besar, tepi HD tajam, dan anchor cache stabil")
