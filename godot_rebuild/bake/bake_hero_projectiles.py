"""Bake the original pygame hero projectile painter for the Godot prototype.

The source renderer is ``_entity.Hero._draw_projectile``.  This script calls it
for every baked frame and writes only below ``godot_rebuild/``.
"""
from __future__ import annotations

import hashlib
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402

CELL = 64
CELL_SIZES = {
    "sylara": 40,
    "vex_attack": 48,
    "vex_skill": 48,
    "zephyr_basic": 56,
    "zephyr_crit": 64,
    "morgath": 40,
    "ancient_apparition": 48,
    "generic": 48,
}
COLUMNS = 64
DIRECTIONS = 32
MAX_AGE = 72
AGE_COUNT = MAX_AGE + 1
SPECIAL_TYPES = {
    "sylara": "arrow",
    "vex": "orb",
    "zephyr": "bolt",
    "morgath": "lightning",
    "ancient_apparition": "ice_shard",
}
ATLAS_SPECS = {
    "sylara": ("sylara", "arrow", 1, 1),
    "vex_attack": ("vex", "attack", AGE_COUNT, 1),
    "vex_skill": ("vex", "skill", AGE_COUNT, 0),
    "zephyr_basic": ("zephyr", "basic", AGE_COUNT, 1),
    "zephyr_crit": ("zephyr", "crit", AGE_COUNT, 1),
    "morgath": ("morgath", "lightning", AGE_COUNT, 1),
    "ancient_apparition": ("ancient_apparition", "ice_shard", 1, 1),
}
KEY_CASE_TARGETS = {
    "sylara:arrow:age00:dir00",
    "sylara:arrow:age00:dir11",
    "vex:attack:age00:dir00",
    "vex:attack:age36:dir09",
    "vex:attack:age72:dir31",
    "vex:skill:age00:dir00",
    "vex:skill:age36:dir12",
    "vex:skill:age72:dir24",
    "zephyr:basic:age00:dir00",
    "zephyr:basic:age36:dir08",
    "zephyr:basic:age72:dir24",
    "zephyr:crit:age00:dir00",
    "zephyr:crit:age36:dir16",
    "zephyr:crit:age72:dir31",
    "morgath:lightning:age00:dir00",
    "morgath:lightning:age36:dir16",
    "morgath:lightning:age72:dir31",
    "ancient_apparition:ice_shard:age00:dir00",
    "ancient_apparition:ice_shard:age00:dir16",
    "kaizen:generic:normal",
    "kaizen:generic:crit",
    "abaddon:generic:normal",
}


def _case_key(hero_type, variant, age=None, direction=None):
    if age is None:
        return f"{hero_type}:generic:{variant}"
    return f"{hero_type}:{variant}:age{age:02d}:dir{direction:02d}"


def _projectile(hero_type, age, angle, damage, is_crit, cell_size):
    center = cell_size // 2
    return {
        "hero_type": hero_type,
        "x": center,
        "y": center,
        "angle": angle,
        "age": age,
        "damage": damage,
        "is_crit": is_crit,
    }


def _render_rgb(pygame, heroes_mod, hero, projectile, background, seed, cell_size):
    surface = pygame.Surface((cell_size, cell_size))
    surface.fill(background)
    random.seed(seed)
    heroes_mod._reset_hero_render_budget()
    hero._draw_projectile(surface, projectile)
    raw = pygame.image.tostring(surface, "RGB")
    import numpy as np

    return np.frombuffer(raw, dtype=np.uint8).reshape((cell_size, cell_size, 3)).copy()


def _unmatte(black, white, cell_size):
    """Recover a transparent sprite from two renders of the pygame screen painter."""
    import numpy as np

    black_i = black.astype(np.int16)
    white_i = white.astype(np.int16)
    difference = np.clip(white_i - black_i, 0, 255)
    alpha = (255 - difference.min(axis=2)).astype(np.uint8)
    rgba = np.zeros((cell_size, cell_size, 4), dtype=np.uint8)
    rgba[:, :, 3] = alpha
    visible = alpha > 0
    if np.any(visible):
        straight = (
            black_i[visible].astype(np.float64)
            * 255.0
            / alpha[visible, None].astype(np.float64)
        )
        rgba[visible, :3] = np.clip(np.rint(straight), 0, 255).astype(np.uint8)
    if (
        np.any(alpha[0, :])
        or np.any(alpha[-1, :])
        or np.any(alpha[:, 0])
        or np.any(alpha[:, -1])
    ):
        raise ValueError(f"A pygame projectile touches the {cell_size}px bake-cell boundary")
    return rgba


def _bake_frame(
    pygame, heroes_mod, hero, hero_type, age, angle, damage, is_crit, key, cell_size
):
    seed = f"hero-projectile:{key}"
    projectile = _projectile(hero_type, age, angle, damage, is_crit, cell_size)
    black = _render_rgb(pygame, heroes_mod, hero, projectile, (0, 0, 0), seed, cell_size)
    white = _render_rgb(pygame, heroes_mod, hero, projectile, (255, 255, 255), seed, cell_size)
    rgba = _unmatte(black, white, cell_size)
    case = None
    if key in KEY_CASE_TARGETS:
        case = {
            "key": key,
            "hero_type": hero_type,
            "age": age,
            "angle": round(angle, 8),
            "damage": damage,
            "is_crit": is_crit,
            "pygame_rgb_sha256": hashlib.sha256(
                black.tobytes() + white.tobytes()
            ).hexdigest(),
            "rgba_sha256": hashlib.sha256(rgba.tobytes()).hexdigest(),
        }
    return rgba, case


def _atlas_frames(atlas_name, hero_types):
    if atlas_name == "generic":
        generic_types = [hero_type for hero_type in hero_types if hero_type not in SPECIAL_TYPES]
        for hero_type in generic_types:
            for variant, is_crit in (("normal", False), ("crit", True)):
                key = _case_key(hero_type, variant)
                yield hero_type, 0, 0.0, 1, is_crit, key
        return

    hero_type, variant, age_count, damage = ATLAS_SPECS[atlas_name]
    variant_name = variant
    if atlas_name == "zephyr_crit":
        is_crit = True
    else:
        is_crit = False
    for age in range(age_count):
        for direction in range(DIRECTIONS):
            angle = direction * math.tau / DIRECTIONS
            key = _case_key(hero_type, variant_name, age, direction)
            yield hero_type, age, angle, damage, is_crit, key


def bake_atlas(pygame, np, heroes_mod, hero_types, atlas_name, heroes):
    cell_size = CELL_SIZES[atlas_name]
    frames = list(_atlas_frames(atlas_name, hero_types))
    rows = math.ceil(len(frames) / COLUMNS)
    sheet = np.zeros((rows * cell_size, COLUMNS * cell_size, 4), dtype=np.uint8)
    cases = []
    generic_frames = {}

    for index, (hero_type, age, angle, damage, is_crit, key) in enumerate(frames):
        rgba, case = _bake_frame(
            pygame,
            heroes_mod,
            heroes[hero_type],
            hero_type,
            age,
            angle,
            damage,
            is_crit,
            key,
            cell_size,
        )
        x = (index % COLUMNS) * cell_size
        y = (index // COLUMNS) * cell_size
        sheet[y : y + cell_size, x : x + cell_size] = rgba
        if case is not None:
            cases.append(case)
        if atlas_name == "generic":
            generic_frames.setdefault(hero_type, {})["crit" if is_crit else "normal"] = index

    png_path = env.ART_DIR / "hero_projectiles" / f"{atlas_name}.png"
    entry = env.write_png(png_path, sheet)
    if atlas_name == "generic":
        age_frames, directions, variant = 1, 1, "generic"
    else:
        _hero_type, variant, age_frames, _damage = ATLAS_SPECS[atlas_name]
        directions = DIRECTIONS
    entry.update(
        {
            "file": f"{atlas_name}.png",
            "cell": cell_size,
            "columns": COLUMNS,
            "frames": len(frames),
            "age_frames": age_frames,
            "directions": directions,
            "variant": variant,
        }
    )
    if generic_frames:
        entry["hero_frames"] = generic_frames
    print(
        f"{atlas_name:24s} {entry['bytes']:8d} B  "
        f"{entry['size'][0]}x{entry['size'][1]}  frames {len(frames)}"
    )
    return entry, cases


def main() -> int:
    import numpy as np

    pygame, _core, _screen = env.boot()
    import heroes as heroes_mod
    from _entity import Hero, get_all_hero_types

    hero_catalog = get_all_hero_types()
    hero_types = sorted(str(hero_type) for hero_type in hero_catalog)
    heroes = {hero_type: Hero(hero_type, "blue", CELL // 2, CELL // 2) for hero_type in hero_types}
    source_meta = {
        hero_type: {
            "color": [int(channel) for channel in heroes[hero_type].color[:3]],
            "radius": float(heroes[hero_type].radius),
            "style": SPECIAL_TYPES.get(hero_type, "generic"),
        }
        for hero_type in hero_types
    }

    atlases = {}
    key_cases = []
    for atlas_name in (*ATLAS_SPECS.keys(), "generic"):
        entry, cases = bake_atlas(
            pygame,
            np,
            heroes_mod,
            hero_types,
            atlas_name,
            heroes,
        )
        atlases[atlas_name] = entry
        key_cases.extend(cases)

    if {case["key"] for case in key_cases} != KEY_CASE_TARGETS:
        missing = sorted(KEY_CASE_TARGETS - {case["key"] for case in key_cases})
        raise RuntimeError(f"Missing source key cases: {missing}")

    payload = {
        "generator": "godot_rebuild/bake/bake_hero_projectiles.py",
        "source": "_entity.py:4976 Hero._draw_projectile",
        "source_functions": {
            "sylara": "_entity.py:5031 Hero._draw_arrow_projectile",
            "vex": "heroes/vex_fx.py:1787 draw_arcane_orb via _entity.py:5116",
            "zephyr": "heroes/zephyr_fx.py:1994 draw_bolt via _entity.py:5176",
            "morgath": "_entity.py:5214 Hero._draw_lightning_projectile",
            "ancient_apparition": (
                "heroes/ancient_apparition_fx.py:2538 draw_ice_shard "
                "via _entity.py:5245"
            ),
            "generic": "_entity.py:4976 Hero._draw_projectile fallback",
        },
        "pygame": pygame.version.ver,
        "cell": CELL,
        "cell_sizes": CELL_SIZES,
        "columns": COLUMNS,
        "directions": DIRECTIONS,
        "age_range": [0, MAX_AGE],
        "hero_types": hero_types,
        "hero_meta": source_meta,
        "special_types": SPECIAL_TYPES,
        "atlases": atlases,
        "key_cases": key_cases,
    }
    manifest = env.write_manifest("hero_projectiles", payload)
    print(f"Wrote {len(key_cases)} source key cases to {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
