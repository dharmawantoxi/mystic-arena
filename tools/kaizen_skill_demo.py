#!/usr/bin/env python3
"""Render a review sheet for Kaizen V1's four wind skills.

This is a review/export tool only.  It calls the same procedural pygame
renderer used by the arena, with the live FX layer disabled so each tile is a
stable canvas preview of Q/W/E/R.
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

KZ = _bundle._NS_kaizen
try:
    from heroes import kaizen_fx as _kaizen_fx  # noqa: E402
    _kaizen_fx.KAIZEN_FX_ENABLED = False
    KZ._LIVE_MOD = False
except Exception:
    pass


class _PreviewUnit(SimpleNamespace):
    """Small renderer contract used instead of constructing a gameplay hero."""

    def __init__(self, skill, timer, pulse):
        super().__init__(
            x=140.0,
            y=150.0,
            direction=1,
            range=150,
            team="blue",
            target=SimpleNamespace(x=315.0, y=150.0, alive=True),
            active_skill=skill,
            active_skill_timer=timer,
            pulse=pulse,
            timer=0,
            attack_cooldown=45,
            alive=True,
            _portrait_hd=False,
            _kz_attack_active=False,
            _kz_attack_progress=0.0,
            _kz_projectiles=[],
            _render_scale=1.0,
        )


def _font(size, bold=False):
    # Font(None) remains available in stripped-down CI/Android environments.
    return pygame.font.Font(None, size)


def _tile(skill, title, timer, pulse):
    width, height = 400, 300
    tile = pygame.Surface((width, height))
    tile.fill((18, 23, 36))
    pygame.draw.rect(tile, (47, 90, 130), (0, 0, width, height), 2,
                     border_radius=8)
    label = _font(24, True).render(title, True, (190, 235, 255))
    tile.blit(label, (14, 9))
    phase = 1.0 - timer / float(KZ.SKILL_VISUAL_DURATION[skill])
    phase_text = _font(16).render(
        "phase %.2f  |  timer %d" % (phase, timer), True, (140, 170, 198))
    tile.blit(phase_text, (width - phase_text.get_width() - 14, 13))

    scene = pygame.Surface((width, height - 42), pygame.SRCALPHA)
    scene.fill((15, 20, 31, 255))
    # A subtle ground line gives the world-space radius a stable reference.
    pygame.draw.line(scene, (36, 62, 76), (20, 224), (380, 224), 1)
    unit = _PreviewUnit(skill, timer, pulse)
    KZ.draw_kaizen(scene, unit, unit.x, unit.y - 12)
    tile.blit(scene, (0, 42))
    return tile


def main():
    out_dir = os.path.join(ROOT, "tools", "_out")
    asset_dir = os.path.join(ROOT, "assets", "review")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(asset_dir, exist_ok=True)

    tiles = (
        _tile("q", "Q  STEEL WIND / DASH", 20, 0.8),
        _tile("w", "W  WINDWALL", 25, 1.7),
        _tile("e", "E  SWEEP", 20, 2.5),
        _tile("r", "R  TORNADO", 35, 3.3),
    )
    gap = 12
    sheet = pygame.Surface((tiles[0].get_width() * 2 + gap,
                            tiles[0].get_height() * 2 + gap))
    sheet.fill((11, 15, 25))
    sheet.blit(tiles[0], (0, 0))
    sheet.blit(tiles[1], (tiles[0].get_width() + gap, 0))
    sheet.blit(tiles[2], (0, tiles[0].get_height() + gap))
    sheet.blit(tiles[3], (tiles[0].get_width() + gap,
                          tiles[0].get_height() + gap))

    out_path = os.path.join(out_dir, "kaizen_skill_sheet.png")
    asset_path = os.path.join(asset_dir, "kaizen_v1_skill_sheet.png")
    pygame.image.save(sheet, out_path)
    pygame.image.save(sheet, asset_path)
    print("saved:", out_path, "size", sheet.get_size())
    print("saved:", asset_path)
    pygame.quit()


if __name__ == "__main__":
    main()
