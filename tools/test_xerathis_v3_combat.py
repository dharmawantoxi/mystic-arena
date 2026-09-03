#!/usr/bin/env python3
"""Regression test Xerathis V2 (renderer + live combat-FX engine).

Mengunci:
  * lapisan hidup heroes/xerathis_fx.py punya semua API yang dipakai
    pipeline hero/boss (attach/owns/tick/draw_*_layer/notify_*);
  * palette kontrak 9 kunci wajib hadir;
  * proyektil & skill FX spawn, bergerak, dan reset ke 0 setelah match;
  * renderer bosses/level3.draw_xerathis hidup bersama lapisan FX tanpa
    exception;
  * boss AI (base_boss.py) memanggil lapisan FX xerathis;
  * prosedural murni (tanpa pygame.image.load).

Jalankan: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_xerathis_v3_combat.py
"""
import os
import sys
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from heroes import xerathis_fx as F
import bosses.level3 as L


def make_boss(x=100.0, y=100.0, skill=None, timer=0, target=True):
    return SimpleNamespace(
        boss_type="xerathis", boss_class="mini", x=float(x), y=float(y),
        direction=1, facing=1, pulse=1.2, timer=0, attack_cooldown=59,
        active_skill=skill, active_skill_timer=timer,
        target=(SimpleNamespace(x=200.0, y=100.0, alive=True,
                                radius=12) if target else None),
        _render_scale=1.0, hurt_flash_timer=0, alive=True, radius=30,
        hp=9000, max_hp=9000, range=200)


def test_module_api():
    required = [
        "Particle", "ParticleSystem", "SwingTrail", "ImpactFX",
        "XerathisProjectile", "ProjectileSystem", "SkillFX",
        "XerathisFXDirector", "attach", "owns", "tick", "reset_all",
        "total_particles", "stats", "draw_ground_layer", "draw_live_layer",
        "director_for", "projectiles_for", "notify_melee_impact",
        "notify_projectile_impact", "notify_projectile_cast",
        "notify_skill_impact", "notify_skill_cast", "notify_hurt",
        "draw_debug_overlay", "XERATHIS_PALETTE", "DEBUG_CHARACTER",
    ]
    for name in required:
        assert hasattr(F, name), "API hilang: xerathis_fx.%s" % name


def test_palette_contract():
    keys = {"outline", "shadow", "dark", "body", "mid", "light",
            "highlight", "weapon", "fx"}
    assert keys.issubset(F.XERATHIS_PALETTE.keys())


def test_fx_lifecycle_and_reset():
    boss = make_boss()
    assert F.attach(boss)
    assert F.owns(boss)
    F.notify_projectile_cast(boss, boss.x, boss.y)
    F.notify_skill_cast(boss, "q")
    F.notify_skill_impact(boss, 200.0, 100.0, 48, "q")
    for _ in range(8):
        F.tick(1.0 / 60.0)
    surf = pygame.Surface((320, 320), pygame.SRCALPHA)
    F.draw_ground_layer(surf, boss, boss.x, boss.y)
    F.draw_live_layer(surf, boss, boss.x, boss.y)
    assert F.total_particles() > 0 or len(F.projectiles_for(boss)) > 0
    F.reset_all()
    assert F.total_particles() == 0
    assert not F.owns(boss)


def test_renderer_with_live_fx():
    boss = make_boss(skill="r", timer=50)
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    L.draw_xerathis(surf, boss, 230, 230)
    br = surf.get_bounding_rect(min_alpha=64)
    assert br.width > 40 and br.height > 40, (br.width, br.height)


def test_base_boss_integration():
    src = open(os.path.join(ROOT, "bosses", "base_boss.py"), "r").read()
    assert "_xfx.notify_skill_impact" in src
    # KONTRAK BARU: serangan dasar tidak memicu impact FX.
    assert "_xfx.notify_projectile_impact" not in src, \
        "serangan dasar boss masih memicu impact FX xerathis"
    assert callable(getattr(F, "notify_projectile_impact", None)), \
        "API notify_projectile_impact hilang dari xerathis_fx"


def test_procedural_only():
    src = open(os.path.join(ROOT, "heroes", "xerathis_fx.py"), "r").read()
    assert "pygame.image.load" not in src


if __name__ == "__main__":
    test_module_api()
    test_palette_contract()
    test_fx_lifecycle_and_reset()
    test_renderer_with_live_fx()
    test_base_boss_integration()
    test_procedural_only()
    print("ALL XERATHIS V3 COMBAT TESTS PASSED")
