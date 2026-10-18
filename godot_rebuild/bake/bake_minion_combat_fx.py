"""Bake source minion slash arcs and death animations for Godot.

The slash frames come from ``minions._bundle.draw_slash_effects`` after the real
``Minion._spawn_slash_effect`` chooses its angle and radius. Death frames call the
real ``Minion._draw_death_animation``. All Python game sources stay read-only.
"""
from __future__ import annotations

import hashlib
import math
import random
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402

TYPES = ("goblin", "orc", "troll", "undead", "dark_rider")
ANGLE_STEPS = 32
SLASH_LIFE = 12
DEATH_LIFE = 20
CANVAS = (96, 96)
COLUMNS = 16


def _rgba(pygame, np, surface):
    width, height = surface.get_size()
    raw = pygame.image.tostring(surface, "RGBA")
    return np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 4).copy()


def _digest(pygame, surface) -> str:
    return hashlib.sha256(pygame.image.tostring(surface, "RGBA")).hexdigest()


def _minion(minion_cls, minion_type):
    instance = minion_cls(
        minion_type, "blue", "mid", nexus_level=1, lane_path=[(0, 0), (100, 0)]
    )
    instance.x = CANVAS[0] // 2
    instance.y = CANVAS[1] // 2
    instance.target = None
    return instance


def _render_slash(pygame, minion, bundle, angle, life):
    minion.slash_effects.clear()
    minion.target = SimpleNamespace(
        x=minion.x + math.cos(angle), y=minion.y + math.sin(angle)
    )
    minion._spawn_slash_effect()
    slash = dict(minion.slash_effects[-1])
    slash["life"] = life
    surface = pygame.Surface(CANVAS, pygame.SRCALPHA, 32)
    bundle.draw_slash_effects(surface, int(minion.x), int(minion.y), [slash])
    return surface, slash


def _render_death(pygame, minion, life):
    minion.death_anim = life
    surface = pygame.Surface(CANVAS, pygame.SRCALPHA, 32)
    minion._draw_death_animation(surface)
    return surface


def _bake_atlas(pygame, np, minion_cls, bundle, minion_type):
    minion = _minion(minion_cls, minion_type)
    frames = []
    for life in range(SLASH_LIFE, 0, -1):
        for angle_index in range(ANGLE_STEPS):
            angle = math.tau * angle_index / ANGLE_STEPS
            surface, _slash = _render_slash(pygame, minion, bundle, angle, life)
            frames.append(
                (f"slash{life:02d}:{angle_index:02d}", _rgba(pygame, np, surface))
            )
    for life in range(DEATH_LIFE, 0, -1):
        surface = _render_death(pygame, minion, life)
        frames.append((f"death{life:02d}", _rgba(pygame, np, surface)))

    rows = (len(frames) + COLUMNS - 1) // COLUMNS
    sheet = np.zeros((rows * CANVAS[1], COLUMNS * CANVAS[0], 4), dtype=np.uint8)
    table = {}
    for index, (key, pixels) in enumerate(frames):
        col, row = index % COLUMNS, index // COLUMNS
        x, y = col * CANVAS[0], row * CANVAS[1]
        sheet[y : y + CANVAS[1], x : x + CANVAS[0]] = pixels
        table[key] = [x, y, CANVAS[0], CANVAS[1], CANVAS[0] // 2, CANVAS[1] // 2]
    return sheet, table, int(minion.radius)


def _key_cases(pygame, minion_cls, bundle):
    cases = []
    for minion_type in TYPES:
        minion = _minion(minion_cls, minion_type)
        for life in (1, 6, 12):
            for angle_index in (0, 8, 16, 24):
                angle = math.tau * angle_index / ANGLE_STEPS
                surface, slash = _render_slash(pygame, minion, bundle, angle, life)
                cases.append(
                    {
                        "kind": "slash",
                        "type": minion_type,
                        "life": life,
                        "max_life": int(slash["max_life"]),
                        "angle_index": angle_index,
                        "angle": round(float(slash["angle"]), 8),
                        "distance": int(slash["distance"]),
                        "rgba_sha256": _digest(pygame, surface),
                    }
                )
        for life in (1, 11, 20):
            surface = _render_death(pygame, minion, life)
            cases.append(
                {
                    "kind": "death",
                    "type": minion_type,
                    "life": life,
                    "radius": int(minion.radius),
                    "rgba_sha256": _digest(pygame, surface),
                }
            )
    return cases


def main() -> int:
    import numpy as np

    pygame, core, _screen = env.boot()
    from _entity import Minion
    from minions import _bundle as bundle

    if tuple(core.MINION_TYPES) != TYPES:
        raise RuntimeError("Update TYPES to match the source MINION_TYPES order")
    bundle._RENDERING_TO_CACHE = False
    random.seed(0)

    atlases = {}
    for minion_type in TYPES:
        sheet, frames, radius = _bake_atlas(pygame, np, Minion, bundle, minion_type)
        name = f"{minion_type}.png"
        entry = env.write_png(env.ART_DIR / "minion_combat_fx" / name, sheet)
        entry.update(
            {
                "cell": list(CANVAS),
                "columns": COLUMNS,
                "radius": radius,
                "slash_distance": radius + 8,
                "frames": frames,
            }
        )
        atlases[minion_type] = entry
        print(
            f"{minion_type:12s} {entry['bytes']:7d} B  sheet {entry['size']}  "
            f"radius {radius}  frames {len(frames)}"
        )

    env.write_manifest(
        "minion_combat_fx",
        {
            "generator": "godot_rebuild/bake/bake_minion_combat_fx.py",
            "source": (
                "_entity.Minion._spawn_slash_effect/_draw_death_animation; "
                "minions._bundle.draw_slash_effects"
            ),
            "types": list(TYPES),
            "canvas": list(CANVAS),
            "angle_steps": ANGLE_STEPS,
            "slash_life": SLASH_LIFE,
            "death_life": DEATH_LIFE,
            "atlases": atlases,
            "key_cases": _key_cases(pygame, Minion, bundle),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
