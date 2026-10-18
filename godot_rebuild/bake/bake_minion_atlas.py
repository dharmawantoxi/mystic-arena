"""Bake the source minion sprites into one PNG atlas per (type, team, nexus level).

``minions/_bundle.py::cached_minion_draw`` renders every body once per cache key
``(type, team, level, state, direction, hurt, bleed, death charge, regen, slow)``
and blits the cropped result; the HP bar, slash arcs and slow aura are drawn live.
This bake drives the REAL ``Minion.draw`` for the poses the game reaches, reads the
cropped sprite + anchor back out of the sprite cache, and packs them.

State representatives follow the order the live game first hits each key:
  atk  k : ``attack_anim_timer`` counts 24..1, key ``atk // 2``  -> timer min(24, 2k + 1)
  walk k : ``walk_cycle`` grows 0.25 per tick, key ``int(2 * wc) % 8`` -> wc = k / 2
  idle k : ``anim_time`` grows 1 per tick, key ``int(0.05 * t) % 4`` -> t = 20k
The hurt flash (+90 brightness) is left to the Godot side as a modulate, which keeps
the atlas at 50 frames per sheet.
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402

TYPES = ("goblin", "orc", "troll", "undead", "dark_rider")
TEAMS = ("blue", "red")
LEVELS = (1, 2, 3, 4, 5)
ATK_STATES, WALK_STATES, IDLE_STATES = 13, 8, 4
DIRECTIONS = (1, -1)
COLUMNS = 10
CANVAS = (120, 120)


def state_list():
    return (
        [("atk", i) for i in range(ATK_STATES)]
        + [("walk", i) for i in range(WALK_STATES)]
        + [("idle", i) for i in range(IDLE_STATES)]
    )


def render_frame(pygame, minion_cls, bundle, cache, minion_type, team, level, state, direction):
    cache.clear_sprite_cache()
    minion = minion_cls(
        minion_type, team, "mid", nexus_level=level, lane_path=[(0, 0), (100, 0)]
    )
    minion.x, minion.y = 400.0, 300.0
    minion.direction = direction
    kind, index = state
    if kind == "atk":
        minion.attack_anim_timer = min(24, 2 * index + 1)
    elif kind == "walk":
        minion.is_moving = True
        minion.walk_cycle = index / 2.0
        minion.anim_time = 2 * index
    else:
        minion.anim_time = 20 * index
    random.seed(f"{minion_type}:{team}:{level}:{kind}{index}:{direction}")
    minion.draw(pygame.Surface((800, 600), pygame.SRCALPHA))
    key = bundle._minion_cache_key(minion)
    sprite, ax, ay = cache.get_cached_sprite_cropped(key, *CANVAS, lambda surface: None)
    return sprite, ax, ay


def bake_atlas(pygame, np, minion_type, team, level):
    from _entity import Minion
    from minions import _bundle as bundle
    import sprite_cache as cache

    frames = []
    for state in state_list():
        for direction in DIRECTIONS:
            sprite, ax, ay = render_frame(
                pygame, Minion, bundle, cache, minion_type, team, level, state, direction
            )
            width, height = sprite.get_size()
            pixels = np.frombuffer(pygame.image.tostring(sprite, "RGBA"), dtype=np.uint8)
            frames.append((state, direction, pixels.reshape(height, width, 4), ax, ay))
    cell_w = max(frame[2].shape[1] for frame in frames)
    cell_h = max(frame[2].shape[0] for frame in frames)
    rows = -(-len(frames) // COLUMNS)
    sheet = np.zeros((rows * cell_h, COLUMNS * cell_w, 4), dtype=np.uint8)
    table = {}
    for index, (state, direction, pixels, ax, ay) in enumerate(frames):
        col, row = index % COLUMNS, index // COLUMNS
        x, y = col * cell_w, row * cell_h
        height, width = pixels.shape[:2]
        sheet[y : y + height, x : x + width] = pixels
        table[f"{state[0]}{state[1]}:{direction}"] = [x, y, width, height, int(ax), int(ay)]
    return sheet, table, [cell_w, cell_h]


def key_cases():
    """Rows ``[attack, moving, walk_cycle, anim_time, kind, index]`` produced by the
    REAL ``_minion_cache_key`` so the Godot pose picker can be replayed against it."""
    from _entity import Minion
    from minions import _bundle as bundle

    def probe(attack=0, moving=False, walk=0.0, anim=0):
        minion = Minion("goblin", "blue", "mid", nexus_level=1, lane_path=[(0, 0), (100, 0)])
        minion.attack_anim_timer = attack
        minion.is_moving = moving
        minion.walk_cycle = walk
        minion.anim_time = anim
        kind, index = bundle._minion_cache_key(minion)[3]
        return [attack, int(moving), walk, anim, kind, int(index)]

    rows = [probe(attack=attack) for attack in range(1, 25)]
    rows += [probe(moving=True, walk=step * 0.25) for step in range(0, 49)]
    idle_times = (0, 1, 19, 20, 39, 40, 59, 60, 79, 80, 99, 100, 119, 120, 139, 140)
    rows += [probe(anim=tick) for tick in idle_times + (159, 160, 199, 200, 320, 401)]
    rows.append(probe(attack=3, moving=True, walk=1.5, anim=50))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", action="append")
    parser.add_argument("--team", action="append")
    parser.add_argument("--level", action="append", type=int)
    args = parser.parse_args()
    import numpy as np

    pygame, _core, _screen = env.boot()
    partial = bool(args.type or args.team or args.level)
    atlases = {}
    for minion_type in args.type or TYPES:
        for team in args.team or TEAMS:
            for level in args.level or LEVELS:
                sheet, table, cell = bake_atlas(pygame, np, minion_type, team, level)
                name = f"{minion_type}_{team}_{level}"
                entry = env.write_png(env.ART_DIR / "minions" / f"{name}.png", sheet)
                entry.update({"cell": cell, "columns": COLUMNS, "frames": table})
                atlases[name] = entry
                print(f"{name:16s} {entry['bytes']:7d} B  sheet {entry['size']}  cell {cell}")
    if not partial:
        env.write_manifest(
            "minions",
            {
                "generator": "godot_rebuild/bake/bake_minion_atlas.py",
                "source": "minions/_bundle.py cached_minion_draw via _entity.Minion.draw",
                "canvas": list(CANVAS),
                "attack_anim_max": 24,
                "states": {"atk": ATK_STATES, "walk": WALK_STATES, "idle": IDLE_STATES},
                "types": list(TYPES),
                "teams": list(TEAMS),
                "levels": list(LEVELS),
                "key_cases": key_cases(),
                "atlases": atlases,
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
