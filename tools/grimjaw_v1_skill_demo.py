#!/usr/bin/env python3
"""Render a review sheet for Grimjaw V1's four flame skills.

This is a review/export tool only.  It calls the same procedural pygame
renderer used by the arena, with the live FX layer disabled so each tile is a
stable canvas preview of Q/W/E/R.  Mirrors tools/vex_v1_skill_demo.py.
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

GJ = _bundle._NS_grimjaw
try:
    from heroes import grimjaw_fx as _grimjaw_fx  # noqa: E402
    _grimjaw_fx.GRIMJAW_FX_ENABLED = False
    GJ._LIVE_MOD = False
except Exception:
    pass


class _PreviewUnit(SimpleNamespace):
    """Small renderer contract used instead of constructing a gameplay hero."""

    def __init__(self, skill, timer, pulse):
        super().__init__(
            x=200.0,
            y=170.0,
            direction=1,
            range=60,
            skill_range=80,
            team="blue",
            target=SimpleNamespace(x=330.0, y=170.0, alive=True),
            active_skill=skill,
            active_skill_timer=timer,
            pulse=pulse,
            timer=0,
            attack_cooldown=40,
            alive=True,
            _portrait_hd=False,
            _gj_attack_active=False,
            _gj_attack_progress=0.0,
            _gj_proj_spawned=False,
            _gj_projectiles=[],
            _render_scale=1.0,
        )


def _font(size, bold=False):
    # Font(None) remains available in stripped-down CI/Android environments.
    return pygame.font.Font(None, size)


def _tile(skill, title, timer, pulse):
    width, height = 440, 320
    tile = pygame.Surface((width, height))
    tile.fill((34, 22, 20))
    pygame.draw.rect(tile, (150, 96, 60), (0, 0, width, height), 2,
                     border_radius=8)
    label = _font(24, True).render(title, True, (255, 220, 170))
    tile.blit(label, (14, 9))
    phase = 1.0 - timer / float(GJ.SKILL_VISUAL_DURATION[skill])
    phase_text = _font(16).render(
        "phase %.2f  |  timer %d" % (phase, timer), True, (190, 160, 140))
    tile.blit(phase_text, (width - phase_text.get_width() - 14, 13))

    scene = pygame.Surface((width, height - 42), pygame.SRCALPHA)
    scene.fill((22, 16, 14, 255))
    # A subtle ground line gives the world-space radius a stable reference.
    pygame.draw.line(scene, (78, 52, 42), (20, 244), (420, 244), 1)
    unit = _PreviewUnit(skill, timer, pulse)
    GJ.draw_grimjaw(scene, unit, unit.x, unit.y - 12)
    tile.blit(scene, (0, 42))
    return tile


def main():
    out_dir = os.path.join(ROOT, "tools", "_out")
    asset_dir = os.path.join(ROOT, "assets", "review")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(asset_dir, exist_ok=True)

    tiles = (
        _tile("q", "Q  BLADE FURY", 60, 0.8),
        _tile("w", "W  HEALING WARD", 30, 1.7),
        _tile("e", "E  CRITICAL STRIKE", 20, 2.5),
        _tile("r", "R  OMNISLASH", 30, 3.3),
    )
    gap = 12
    sheet = pygame.Surface((tiles[0].get_width() * 2 + gap,
                            tiles[0].get_height() * 2 + gap))
    sheet.fill((22, 14, 12))
    sheet.blit(tiles[0], (0, 0))
    sheet.blit(tiles[1], (tiles[0].get_width() + gap, 0))
    sheet.blit(tiles[2], (0, tiles[0].get_height() + gap))
    sheet.blit(tiles[3], (tiles[0].get_width() + gap,
                          tiles[0].get_height() + gap))

    out_path = os.path.join(out_dir, "grimjaw_v1_skill_sheet.png")
    asset_path = os.path.join(asset_dir, "grimjaw_v1_skill_sheet.png")
    pygame.image.save(sheet, out_path)
    pygame.image.save(sheet, asset_path)
    print("saved:", out_path, "size", sheet.get_size())
    print("saved:", asset_path)
    pygame.quit()


if __name__ == "__main__":
    main()
