"""Headless test untuk memastikan semua starter hero memakai procedural code base.

Semua 6 hero starter (Grimjaw, Sylara, Kaizen, Thorne, Vex, Zephyr):
- Render tanpa ketergantungan pada file gambar eksternal (assets/heroes).
- Render valid di semua state: idle, walk, attack, skills (Q/W/E/R).
- Bekerja baik di pipeline caching render_hero().
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Headless video driver
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from heroes import HERO_RENDERERS, render_hero, clear_hero_sprite_cache
from heroes._bundle import (
    _NS_grimjaw,
    _NS_sylara,
    _NS_kaizen,
    _NS_thorne,
    _NS_vex,
    _NS_zephyr,
)


class MockHero:
    """Mock hero object untuk pengujian rendering."""

    def __init__(self, hero_type, team="blue"):
        self.hero_type = hero_type
        self.team = team
        self.level = 1
        self.radius = 18
        self.color = (50, 150, 255) if team == "blue" else (255, 60, 60)
        self.color_dark = (20, 80, 160) if team == "blue" else (160, 20, 20)
        self.facing = 1
        self.direction = 1
        self.x = 200.0
        self.y = 200.0
        self.pulse = 1.0
        self.timer = 0
        self.attack_timer = 0
        self.attack_cooldown = 45
        self.active_skill = None
        self.active_skill_timer = 0
        self.alive = True
        self.range = 50
        self.name = hero_type.capitalize()


HEROES = ["grimjaw", "sylara", "kaizen", "thorne", "vex", "zephyr"]


def test_renderers_registered():
    """Pastikan semua 6 starter hero terdaftar di HERO_RENDERERS."""
    for h in HEROES:
        assert h in HERO_RENDERERS, f"Hero {h} harus terdaftar di HERO_RENDERERS"
        assert callable(HERO_RENDERERS[h]), f"Renderer {h} harus callable"
    print("T1 OK  - Semua 6 starter hero terdaftar")


def test_codebase_rendering():
    """Uji rendering code base untuk semua state dan hero."""
    surf = pygame.Surface((300, 300), pygame.SRCALPHA)

    for h in HEROES:
        hero = MockHero(h)
        renderer = HERO_RENDERERS[h]

        # 1. Idle state
        surf.fill((0, 0, 0, 0))
        hero.pulse = 1.5
        renderer(surf, hero, 150, 150)
        rect = surf.get_bounding_rect(min_alpha=5)
        assert rect.width > 20 and rect.height > 20, f"{h} idle render kosong"

        # 2. Walk state
        surf.fill((0, 0, 0, 0))
        hero.x += 5.0
        hero.pulse = 2.0
        renderer(surf, hero, 150, 150)
        rect = surf.get_bounding_rect(min_alpha=5)
        assert rect.width > 20 and rect.height > 20, f"{h} walk render kosong"

        # 3. Attack state
        surf.fill((0, 0, 0, 0))
        hero.timer = 40
        hero.attack_timer = 40
        hero._th_attack_active = True
        hero._kz_attack_active = True
        hero._zp_attack_active = True
        renderer(surf, hero, 150, 150)
        rect = surf.get_bounding_rect(min_alpha=5)
        assert rect.width > 20 and rect.height > 20, f"{h} attack render kosong"

        # 4. Skills Q, W, E, R
        for sk in ["q", "w", "e", "r"]:
            surf.fill((0, 0, 0, 0))
            hero.active_skill = sk
            hero.active_skill_timer = 30
            renderer(surf, hero, 150, 150)
            rect = surf.get_bounding_rect(min_alpha=5)
            assert rect.width > 10 and rect.height > 10, f"{h} skill {sk} render kosong"
            hero.active_skill = None
            hero.active_skill_timer = 0

    print("T2 OK  - Semua hero render procedural code base (idle/walk/attack/skills)")


def test_hero_cache_pipeline():
    """Uji pipeline caching render_hero() untuk semua starter hero."""
    clear_hero_sprite_cache()
    surf = pygame.Surface((800, 600), pygame.SRCALPHA)

    for h in HEROES:
        hero = MockHero(h)

        # Draw idle
        render_hero(h, surf, hero, 200, 200)

        # Draw moving
        hero.x += 10.0
        render_hero(h, surf, hero, 210, 200)

        # Draw attack
        hero.timer = 30
        hero.attack_timer = 30
        render_hero(h, surf, hero, 210, 200)

        # Draw skill
        hero.timer = 0
        hero.attack_timer = 0
        hero.active_skill = "q"
        hero.active_skill_timer = 40
        render_hero(h, surf, hero, 210, 200)

    print("T3 OK  - Pipeline render_hero() dengan cache berfungsi sempurna")


def test_no_hero_assets_present():
    """Pastikan folder assets/heroes tidak ada/tidak berisi file."""
    hero_asset_dir = os.path.join(
        os.path.dirname(__file__), "..", "assets", "heroes"
    )
    if os.path.exists(hero_asset_dir):
        files = os.listdir(hero_asset_dir)
        assert len(files) == 0, f"assets/heroes harus kosong, ditemukan: {files}"
    print("T4 OK  - Folder assets/heroes bersih (tidak ada sprite eksternal)")


if __name__ == "__main__":
    test_renderers_registered()
    test_codebase_rendering()
    test_hero_cache_pipeline()
    test_no_hero_assets_present()
    print("\nSEMUA PENGUJIAN CODE BASE HERO BERHASIL (LULUS 100%)")
