#!/usr/bin/env python3
"""Render a review sheet for Vex V1's four void skills.

This is a review/export tool only.  It calls the same procedural pygame
renderer used by the arena, with the live FX layer disabled so each tile is a
stable canvas preview of Q/W/E/R.  Mirrors tools/kaizen_skill_demo.py.
"""

from __future__ import annotations

import os
import sys
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((8, 8))

from heroes import _bundle as _bundle  # noqa: E402

VX = _bundle._NS_vex
try:
    from heroes import vex_fx as _vex_fx  # noqa: E402
    _vex_fx.VEX_FX_ENABLED = False
    VX._LIVE_MOD = False
except Exception:
    pass


class _PreviewUnit(SimpleNamespace):
    """Small renderer contract used instead of constructing a gameplay hero."""

    def __init__(self, skill, timer, pulse):
        super().__init__(
            x=140.0,
            y=150.0,
            direction=1,
            range=130,
            team="blue",
            target=SimpleNamespace(x=320.0, y=150.0, alive=True),
            active_skill=skill,
            active_skill_timer=timer,
            pulse=pulse,
            timer=0,
            attack_cooldown=50,
            alive=True,
            _portrait_hd=False,
            _vx_attack_active=False,
            _vx_attack_progress=0.0,
            _vx_projectiles=[],
            _render_scale=1.0,
        )


def _font(size, bold=False):
    # Font(None) remains available in stripped-down CI/Android environments.
    return pygame.font.Font(None, size)


def _tile(skill, title, timer, pulse):
    width, height = 400, 300
    tile = pygame.Surface((width, height))
    tile.fill((20, 16, 34))
    pygame.draw.rect(tile, (96, 74, 150), (0, 0, width, height), 2,
                     border_radius=8)
    label = _font(24, True).render(title, True, (196, 240, 235))
    tile.blit(label, (14, 9))
    phase = 1.0 - timer / float(VX.SKILL_VISUAL_DURATION[skill])
    phase_text = _font(16).render(
        "phase %.2f  |  timer %d" % (phase, timer), True, (150, 170, 190))
    tile.blit(phase_text, (width - phase_text.get_width() - 14, 13))

    scene = pygame.Surface((width, height - 42), pygame.SRCALPHA)
    scene.fill((14, 11, 25, 255))
    # A subtle ground line gives the world-space radius a stable reference.
    pygame.draw.line(scene, (52, 42, 78), (20, 224), (380, 224), 1)
    unit = _PreviewUnit(skill, timer, pulse)
    VX.draw_vex(scene, unit, unit.x, unit.y - 12)
    tile.blit(scene, (0, 42))
    return tile


def main():
    out_dir = os.path.join(ROOT, "tools", "_out")
    asset_dir = os.path.join(ROOT, "assets", "review")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(asset_dir, exist_ok=True)

    tiles = (
        _tile("q", "Q  ARCANE ORB", 16, 0.8),
        _tile("w", "W  SANITY'S ECLIPSE", 26, 1.7),
        _tile("e", "E  ASTRAL IMPRISONMENT", 18, 2.5),
        _tile("r", "R  ESSENCE FLUX", 30, 3.3),
    )
    gap = 12
    sheet = pygame.Surface((tiles[0].get_width() * 2 + gap,
                            tiles[0].get_height() * 2 + gap))
    sheet.fill((12, 10, 22))
    sheet.blit(tiles[0], (0, 0))
    sheet.blit(tiles[1], (tiles[0].get_width() + gap, 0))
    sheet.blit(tiles[2], (0, tiles[0].get_height() + gap))
    sheet.blit(tiles[3], (tiles[0].get_width() + gap,
                          tiles[0].get_height() + gap))

    out_path = os.path.join(out_dir, "vex_v1_skill_sheet.png")
    asset_path = os.path.join(asset_dir, "vex_v1_skill_sheet.png")
    pygame.image.save(sheet, out_path)
    pygame.image.save(sheet, asset_path)
    print("saved:", out_path, "size", sheet.get_size())
    print("saved:", asset_path)
    pygame.quit()


if __name__ == "__main__":
    main()
