"""Pastikan projectile renderer tidak terpanggang ke cache sprite hero.

Bug: list `_sy_projectiles` / `_aa_beams` / dll. ikut di-draw ke canvas
cache di pusat sprite, lalu freeze di sekitar badan hero.

Jalankan: python3 tools/test_renderer_projectiles_not_baked.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((640, 360))

import heroes  # noqa: E402
from heroes import (  # noqa: E402
    _park_renderer_fx,
    _restore_renderer_fx,
    clear_hero_sprite_cache,
    render_hero,
)


class FakeHero:
    def __init__(self, tipe):
        self.hero_type = tipe
        self.attack_cooldown = 40
        self.attack_timer = 0
        self.timer = 0
        self.x = 320.0
        self.y = 180.0
        self.facing = 1
        self.direction = 1
        self.alive = True
        self.hp = 100
        self.max_hp = 100
        self.level = 1
        self.radius = 16
        self.pulse = 0.0
        self.active_skill = None
        self.active_skill_timer = 0
        self.team = "blue"
        self.projectiles = ["gameplay-orb"]
        self.target = None
        self.damage = 10
        self.range = 120
        self.color = (50, 150, 255)
        self.color_dark = (20, 80, 160)


class DummyProj:
    def __init__(self):
        self.alive = True
        self.dead_frames = 0
        self.drawn = 0
        self.updated = 0

    def update(self):
        self.updated += 1

    def draw(self, surface, phase):
        self.drawn += 1
        pygame.draw.circle(surface, (255, 0, 255), (8, 8), 20)


def test_park_skips_underscore_lists_keeps_gameplay():
    hero = FakeHero("sylara")
    dummy = DummyProj()
    hero._sy_projectiles = [dummy]
    hero._aa_beams = [object()]
    hero._vk_chain_orbs = [object()]
    hero._nyz_shards = [object()]
    hero.projectiles = ["gameplay-orb"]

    parked = _park_renderer_fx(hero)
    assert hero._sy_projectiles == []
    assert hero._aa_beams == []
    assert hero._vk_chain_orbs == []
    assert hero._nyz_shards == []
    assert hero.projectiles == ["gameplay-orb"]
    assert hero._skip_renderer_projectiles is True

    _restore_renderer_fx(hero, parked)
    assert hero._sy_projectiles is parked["_sy_projectiles"]
    assert len(hero._sy_projectiles) == 1
    assert hero._sy_projectiles[0] is dummy
    assert hero._skip_renderer_projectiles is False
    print("T1 OK  - park/restore FX renderer, gameplay projectiles utuh")


def test_render_hero_restores_and_does_not_draw_dummy():
    clear_hero_sprite_cache()
    hero = FakeHero("sylara")
    dummy = DummyProj()
    hero._sy_projectiles = [dummy]
    surf = pygame.Surface((640, 360), pygame.SRCALPHA)
    render_hero("sylara", surf, hero, 320, 180)

    assert hero._sy_projectiles is not None
    assert len(hero._sy_projectiles) == 1
    assert hero._sy_projectiles[0] is dummy
    assert dummy.drawn == 0, "dummy renderer projectile ikut tergambar ke canvas cache"
    assert dummy.updated == 0
    assert hero._skip_renderer_projectiles is False
    print("T2 OK  - render_hero tidak menggambar / merusak list renderer")


def test_spawn_during_canvas_does_not_stick():
    clear_hero_sprite_cache()
    hero = FakeHero("sylara")
    dummy = DummyProj()
    hero._sy_projectiles = [dummy]
    # Pose serangan + skill: renderer starter bisa spawn ke list parked.
    hero.attack_timer = 20
    hero.timer = 20
    hero._sy_attack_active = True
    hero._sy_attack_progress = 0.55
    hero.active_skill = "q"
    hero.active_skill_timer = 30
    surf = pygame.Surface((640, 360), pygame.SRCALPHA)
    render_hero("sylara", surf, hero, 320, 180)

    assert len(hero._sy_projectiles) == 1, (
        "spawn saat canvas render menempel ke list asli: %d"
        % len(hero._sy_projectiles)
    )
    assert hero._sy_projectiles[0] is dummy
    print("T3 OK  - spawn di canvas cache tidak bocor ke list asli")


def test_cache_hit_does_not_mutate_fx():
    clear_hero_sprite_cache()
    hero = FakeHero("sylara")
    dummy = DummyProj()
    hero._sy_projectiles = [dummy]
    surf = pygame.Surface((640, 360), pygame.SRCALPHA)
    render_hero("sylara", surf, hero, 320, 180)
    render_hero("sylara", surf, hero, 320, 180)
    assert len(hero._sy_projectiles) == 1
    assert dummy.drawn == 0
    print("T4 OK  - cache hit tidak menyentuh FX renderer")


if __name__ == "__main__":
    test_park_skips_underscore_lists_keeps_gameplay()
    test_render_hero_restores_and_does_not_draw_dummy()
    test_spawn_during_canvas_does_not_stick()
    test_cache_hit_does_not_mutate_fx()
    print("\nSEMUA PENGUJIAN PROJECTILE CACHE LULUS")
