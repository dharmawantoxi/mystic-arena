"""Bake the source tower, castle and armor-crest sprites.

``_entity.py`` caches a tower body per key ``("tw", type, team, level, face, shoot_b)``
(``face`` = target is to the right, ``shoot_b`` = ``shoot_flash_timer // 3``) and blits
the cropped result. The castle is drawn from a 180x160 canvas (static art, then the
gate-torch flames for level 4+) scaled by 0.85. Armor crests are cached per
``(size, colour, ratio bucket, bright)``. HP/shield bars, level badge and the muzzle
flash are live code and are ported in GDScript, not baked.

Representative timers follow the order the live game first hits each key:
  tower shoot_b 0/1/2/3 -> shoot_flash_timer 0/5/8/10 (it counts down from 8, or 10 for
  the cannon); castle flame flicker ``int((timer * 0.4) % 5)`` 0..4 -> timer 0/3/5/8/10.
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402

TOWER_TYPES = ("archer", "cannon", "ice", "mage")
TEAMS = ("blue", "red")
FACES = (0, 1)
SHOOT_TIMERS = (0, 5, 8, 10)
CASTLE_LEVELS = (1, 2, 3, 4, 5)
CASTLE_TIMERS = (0, 3, 5, 8, 10)
CREST_SIZES = (14, 18)
CREST_BUCKETS = tuple(range(11))
CANVAS = (220, 220)
TOWER_COLUMNS = 4


def pack(np, frames, columns):
    """Uniform-cell sheet: ``frames`` = [(key, pixels HxWx4, ax, ay)]."""
    cell_w = max(f[1].shape[1] for f in frames)
    cell_h = max(f[1].shape[0] for f in frames)
    rows = -(-len(frames) // columns)
    sheet = np.zeros((rows * cell_h, columns * cell_w, 4), dtype=np.uint8)
    table = {}
    for index, (key, pixels, ax, ay) in enumerate(frames):
        x, y = (index % columns) * cell_w, (index // columns) * cell_h
        height, width = pixels.shape[:2]
        sheet[y : y + height, x : x + width] = pixels
        table[key] = [x, y, width, height, int(ax), int(ay)]
    return sheet, table, [cell_w, cell_h]


def pixels_of(pygame, np, surface):
    width, height = surface.get_size()
    raw = np.frombuffer(pygame.image.tostring(surface, "RGBA"), dtype=np.uint8)
    return raw.reshape(height, width, 4)


def tower_sheet(pygame, np, entity, minion_cls, tower_type, team, level):
    frames = []
    for face in FACES:
        for timer in SHOOT_TIMERS:
            entity._TOWER_SPRITE_CACHE.clear()
            tower = entity.Tower(400.0, 300.0, team)
            tower.tower_type = tower_type
            tower.level = level
            tower._apply_level_stats()
            tower.shoot_flash_timer = timer
            if face:
                target = minion_cls("goblin", "red" if team == "blue" else "blue", "mid",
                                    lane_path=[(0, 0), (100, 0)])
                target.x, target.y = 520.0, 300.0
                tower.target = target
            random.seed(f"{tower_type}:{team}:{level}:{face}:{timer}")
            tower._draw_tower_body(pygame.Surface((800, 600), pygame.SRCALPHA), 400.0, 300.0)
            key = ("tw", tower_type, team, level, face, timer // 3)
            sprite, ax, ay = entity._TOWER_SPRITE_CACHE[key]
            frames.append((f"{face}:{timer // 3}", pixels_of(pygame, np, sprite), ax, ay))
    return pack(np, frames, TOWER_COLUMNS)


def castle_sheet(pygame, np, entity, team, level):
    palette = entity._get_palette(team)
    castle = entity.Castle(400.0, 300.0, team)
    castle.level = level
    random.seed(f"castle:{team}:{level}")
    canvas = pygame.Surface((180, 160), pygame.SRCALPHA)
    entity._render_castle_full(canvas, castle, 90, 140, palette)
    scale = 0.85
    new_w, new_h = int(180 * scale), int(160 * scale)
    frames = []
    for index, timer in enumerate(CASTLE_TIMERS):
        castle.timer = timer
        frame = canvas.copy()
        entity._render_dynamic_effects(frame, castle, palette)
        scaled = pygame.transform.smoothscale(frame, (new_w, new_h))
        frames.append((str(index), pixels_of(pygame, np, scaled), new_w // 2, new_h - 35))
    return pack(np, frames, len(CASTLE_TIMERS))


def crest_sheet(pygame, np, entity, core):
    colours = {
        14: {"blue": core.SHIELD_COLOR_BLUE, "red": core.SHIELD_COLOR_RED},
        18: {"blue": core.CASTLE_SHIELD_COLOR_BLUE, "red": core.CASTLE_SHIELD_COLOR_RED},
    }
    frames = []
    for size in CREST_SIZES:
        for team in TEAMS:
            for bucket in CREST_BUCKETS:
                for bright in (0, 1):
                    crest = entity._build_armor_crest(
                        size, tuple(colours[size][team]), bucket / 10.0, bool(bright)
                    )
                    key = f"{size}:{team}:{bucket}:{bright}"
                    frames.append(
                        (key, pixels_of(pygame, np, crest), crest.get_width() // 2,
                         crest.get_height() // 2)
                    )
    return pack(np, frames, 22)


def top_offsets(levels_by_type):
    """``get_<type>_top_y(0, 0, level)``: where the HP bar sits above the tower origin."""
    from towers.archer_tower import get_archer_top_y
    from towers.cannon_tower import get_cannon_top_y
    from towers.ice_tower import get_ice_top_y
    from towers.mage_tower import get_mage_top_y

    functions = {"archer": get_archer_top_y, "cannon": get_cannon_top_y,
                 "ice": get_ice_top_y, "mage": get_mage_top_y}
    return {
        kind: {str(level): int(functions[kind](0, 0, level)) for level in levels}
        for kind, levels in levels_by_type.items()
    }


def entry_of(path, sheet, table, cell, columns):
    entry = env.write_png(path, sheet)
    entry.update({"cell": cell, "columns": columns, "frames": table})
    return entry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=("towers", "castles", "crests"))
    args = parser.parse_args()
    import numpy as np

    pygame, core, _screen = env.boot()
    import _entity as entity
    from _entity import Minion

    levels = {kind: sorted(levels) for kind, levels in core.TOWER_UPGRADE_PATHS.items()}
    towers, castles = {}, {}
    if args.only in (None, "towers"):
        for kind in TOWER_TYPES:
            for team in TEAMS:
                for level in levels[kind]:
                    sheet, table, cell = tower_sheet(pygame, np, entity, Minion, kind, team, level)
                    name = f"{kind}_{team}_{level}"
                    towers[name] = entry_of(env.ART_DIR / "structures" / f"tower_{name}.png",
                                            sheet, table, cell, TOWER_COLUMNS)
                    print(f"tower {name:14s} {towers[name]['bytes']:7d} B  cell {cell}")
    if args.only in (None, "castles"):
        for team in TEAMS:
            for level in CASTLE_LEVELS:
                sheet, table, cell = castle_sheet(pygame, np, entity, team, level)
                name = f"{team}_{level}"
                castles[name] = entry_of(env.ART_DIR / "structures" / f"castle_{name}.png",
                                         sheet, table, cell, len(CASTLE_TIMERS))
                print(f"castle {name:13s} {castles[name]['bytes']:7d} B  cell {cell}")
    crests = {}
    if args.only in (None, "crests"):
        sheet, table, cell = crest_sheet(pygame, np, entity, core)
        crests = entry_of(env.ART_DIR / "structures" / "crests.png", sheet, table, cell, 22)
        print(f"crests {crests['bytes']} B  cell {cell}")
    if args.only is None:
        env.write_manifest(
            "structures",
            {
                "generator": "godot_rebuild/bake/bake_structure_atlas.py",
                "source": "_entity.py Tower._draw_tower_body, Castle.draw, _build_armor_crest",
                "tower_types": list(TOWER_TYPES),
                "tower_levels": {kind: levels[kind] for kind in TOWER_TYPES},
                "tower_top_y": top_offsets({kind: levels[kind] for kind in TOWER_TYPES}),
                "shoot_timers": list(SHOOT_TIMERS),
                "castle": {"levels": list(CASTLE_LEVELS), "timers": list(CASTLE_TIMERS),
                           "scale": 0.85, "size": [153, 136], "anchor": [76, 101]},
                "towers": towers,
                "castles": castles,
                "crests": crests,
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
