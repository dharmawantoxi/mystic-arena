#!/usr/bin/env python3
"""Review sheet for Sylara V1's four wind skills (Q/W/E/R).

Review/export tool only.  Each tile renders the SAME procedural path the
arena uses: ground layer (massa besar, di-squash ke tanah) -> badan ->
aksen depan.  Lapisan hidup 60 fps dimatikan di baris pertama supaya tiap
tile adalah potret canvas yang stabil; baris kedua menampilkan komposit
nyata lewat ``heroes.render_hero()`` (pipeline hero + cache sprite).

Mirrors tools/vex_v1_skill_demo.py / tools/grimjaw_v1_skill_demo.py.

Jalankan:
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    python3 tools/sylara_v1_skill_demo.py
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

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((8, 8))

import heroes  # noqa: E402
from heroes import _bundle as _bundle  # noqa: E402

SY = _bundle._NS_sylara

try:
    from heroes import sylara_fx as _sylara_fx  # noqa: E402
    _sylara_fx.SYLARA_FX_ENABLED = False
    SY._LIVE_MOD = False
except Exception:
    _sylara_fx = None


class _PreviewUnit(SimpleNamespace):
    """Small renderer contract used instead of constructing a real hero."""

    def __init__(self, skill, timer, pulse, live=False):
        super().__init__(
            hero_type="sylara",
            x=200.0,
            y=170.0,
            direction=1,
            facing=1,
            alive=True,
            team="blue",
            level=1,
            hp=470,
            max_hp=470,
            radius=16,
            range=130,
            speed=1.5,
            skill_damage=95,
            skill_range=200,
            attack_cooldown=52,
            attack_timer=0,
            timer=0,
            pulse=pulse,
            active_skill=skill,
            active_skill_timer=timer,
            target=SimpleNamespace(x=360.0, y=182.0, alive=True),
            _focus_fire_active=False,
            _focus_fire_timer=timer if skill == "q" else 0,
            _windrun_active=skill == "w",
            _windrun_timer=timer if skill == "w" else 0,
            _shackle_active=skill == "e",
            _shackle_timer=timer if skill == "e" else 0,
            _shackle_target=None,
            _powershot_charging=skill == "r",
            _powershot_timer=timer if skill == "r" else 0,
            _sy_attack_active=False,
            _sy_attack_progress=0.0,
            _sy_swing_mode=False,
            _sy_projectiles=[],
            _portrait_hd=False,
            _render_scale=1.0,
        )


def _font(size, bold=False):
    try:
        return pygame.font.SysFont("dejavusans", size, bold=bold)
    except Exception:                      # pragma: no cover - CI minimal
        return pygame.font.Font(None, size)


def _tile(skill, title, timer, pulse):
    width, height = 440, 320
    tile = pygame.Surface((width, height))
    tile.fill((26, 34, 26))
    pygame.draw.rect(tile, (96, 150, 88), (0, 0, width, height), 2,
                     border_radius=8)
    label = _font(24, True).render(title, True, (226, 246, 170))
    tile.blit(label, (14, 9))
    phase = 1.0 - timer / float(SY.SKILL_VISUAL_DURATION[skill])
    phase_text = _font(16).render(
        "phase %.2f  |  timer %d" % (phase, timer), True, (170, 196, 160))
    tile.blit(phase_text, (width - phase_text.get_width() - 14, 13))

    scene = pygame.Surface((width, height - 42), pygame.SRCALPHA)
    scene.fill((18, 24, 18, 255))
    # garis tanah = acuan radius dunia (world-space)
    pygame.draw.line(scene, (58, 84, 58), (16, 258), (424, 258), 1)
    unit = _PreviewUnit(skill, timer, pulse)
    SY.draw_sylara(scene, unit, int(unit.x), int(unit.y))
    tile.blit(scene, (0, 42))
    return tile


def _pipeline_strip():
    """Q/W/E/R lewat pipeline hero nyata (canvas sprite + live layer)."""
    try:
        _sylara_fx.SYLARA_FX_ENABLED = True
        SY._LIVE_MOD = None
    except Exception:
        pass
    width, height = 180, 230
    strip = pygame.Surface((width * 4 + 12, height + 28))
    strip.fill((16, 20, 16))
    title = _font(18, True).render(
        "PIPELINE render_hero()  (canvas + cache sprite, live layer aktif)",
        True, (214, 236, 160))
    strip.blit(title, (6, 4))
    for i, (skill, timer) in enumerate((("q", 120), ("w", 90),
                                       ("e", 100), ("r", 30))):
        cell = pygame.Surface((width, height))
        cell.fill((20, 26, 20))
        unit = _PreviewUnit(skill, timer, 1.6, live=True)
        heroes.render_hero("sylara", cell, unit, width // 2, 150)
        lab = _font(15, True).render(skill.upper(), True, (226, 246, 170))
        cell.blit(lab, (8, 6))
        strip.blit(cell, (6 + i * (width + 2), 24))
    return strip


def main():
    out_dir = os.path.join(ROOT, "tools", "_out")
    asset_dir = os.path.join(ROOT, "assets", "review")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(asset_dir, exist_ok=True)

    tiles = (
        _tile("q", "Q  FOCUS FIRE", 96, 0.8),
        _tile("w", "W  WINDRUN", 96, 1.7),
        _tile("e", "E  SHACKLE SHOT", 70, 2.5),
        _tile("r", "R  POWERSHOT", 26, 3.3),
    )
    gap = 12
    sheet = pygame.Surface((tiles[0].get_width() * 2 + gap,
                            tiles[0].get_height() * 2 + gap))
    sheet.fill((18, 24, 18))
    sheet.blit(tiles[0], (0, 0))
    sheet.blit(tiles[1], (tiles[0].get_width() + gap, 0))
    sheet.blit(tiles[2], (0, tiles[0].get_height() + gap))
    sheet.blit(tiles[3], (tiles[0].get_width() + gap,
                          tiles[0].get_height() + gap))

    strip = _pipeline_strip()
    canvas = pygame.Surface((max(sheet.get_width(), strip.get_width()),
                             sheet.get_height() + strip.get_height() + 8))
    canvas.fill((18, 24, 18))
    canvas.blit(sheet, (0, 0))
    canvas.blit(strip, (0, sheet.get_height() + 8))

    out_path = os.path.join(out_dir, "sylara_v1_skill_sheet.png")
    asset_path = os.path.join(asset_dir, "sylara_v1_skill_sheet.png")
    pygame.image.save(canvas, out_path)
    pygame.image.save(canvas, asset_path)
    print("saved:", out_path, "size", canvas.get_size())
    print("saved:", asset_path)
    pygame.quit()


if __name__ == "__main__":
    main()
