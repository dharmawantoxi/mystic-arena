"""Bake the source hero body sprites (``heroes/__init__.py`` ``render_hero`` cache).

``render_hero`` caches one cropped body per key ``(type, team, level, facing, 'idle' | 'atk',
phase | timer // 3, moving | pose variant)``; the name badge, HP bar, selection ring and live
FX are drawn around it by ``Hero.draw`` / ``_live_fx_*``. Level never changes the body (checked:
identical pixels at levels 1, 3, 8 and 15), so level 1 stands for all.

Instead of guessing which value of ``pulse`` or ``attack_timer`` the live game renders first
for a key, this drives the REAL ``Hero.draw`` through the same timeline the game does (the pose
controllers advance every frame): 40 frames of the 0.1-per-tick ``pulse`` still and moving, then
one attack from ``attack_timer = cooldown`` down to 1, for each facing and team, from an empty
cache, and keeps the first sprite each key receives.
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402

# Heroes with a native kit in the Godot rebuild; the rest keep their silhouette marker.
HEROES = ("kaizen", "thorne", "grimjaw", "sylara", "vex", "zephyr", "alchemist")
TEAMS = ("blue", "red")
FACINGS = (1, -1)
COLUMNS = 10
PHASES = 8
IDLE_STEPS = 40


def pose_name(key):
    """``_hero_cache_key`` tuple -> pose name used by the atlas."""
    if key[4] == "atk":
        return f"atk{key[5]}"
    return ("walk" if key[6] else "idle") + str(key[5])


def collect(pygame, heroes_mod, hero_cls, hero_type, team, facing):
    """First sprite each pose key receives in three cold-cache runs of the real timeline."""
    surface = pygame.Surface((800, 600), pygame.SRCALPHA)
    seen = {}

    def fresh():
        heroes_mod._hero_sprite_cache.clear()
        heroes_mod._hero_skill_cache.clear()
        hero = hero_cls(hero_type, team, 400, 300)
        hero.facing = facing
        hero.attack_timer = 0
        return hero

    def grab(hero, tag, wanted):
        random.seed(f"{hero_type}:{team}:{facing}:{tag}")
        # The key is computed before the renderer runs (it may flip ``_moving_cached``).
        key = heroes_mod._hero_cache_key(hero_type, hero)
        heroes_mod._reset_hero_render_budget()  # the live game refills it every frame
        hero.draw(surface)
        cache, _limit = heroes_mod._cache_for(key)
        entry = cache.get(key)
        if entry is None or key[4] == "skill" or not wanted(key):
            return
        pose = pose_name(key)
        if pose not in seen:
            seen[pose] = (entry[0], entry[1], entry[2])

    # A: standing still -> idle poses.
    hero = fresh()
    for step in range(IDLE_STEPS):
        hero.pulse = step * 0.1
        grab(hero, f"idle:{step}", lambda key: key[4] == "idle" and not key[6])
    # B: walking from a cold cache. The renderers only notice movement on a cache miss
    # (``_detect_moving`` runs inside them), so the 'moving' keys fill in on the second lap.
    hero = fresh()
    for step in range(IDLE_STEPS * 3):
        hero.pulse = step * 0.1
        hero.x = 400.0 + step * 2.0
        grab(hero, f"walk:{step}", lambda key: key[4] == "idle" and key[6])
    # C: one attack from standing still, attack_timer = cooldown .. 1.
    hero = fresh()
    for settle in range(3):
        hero.pulse = settle * 0.1
        grab(hero, f"settle:{settle}", lambda key: False)
    hero.pulse = 0.0
    cooldown = int(hero._eff_attack_cd(hero.attack_cooldown))
    hero.attack_timer = cooldown
    while hero.attack_timer > 0:
        grab(hero, f"atk:{hero.attack_timer}", lambda key: key[4] == "atk")
        hero.attack_timer -= 1
    return seen, cooldown


def bake_hero(pygame, np, heroes_mod, hero_cls, hero_type, team):
    per_facing = {}
    cooldown = 0
    for facing in FACINGS:
        per_facing[facing], cooldown = collect(
            pygame, heroes_mod, hero_cls, hero_type, team, facing
        )
    def order(name):
        return (name.rstrip("0123456789"), int(name.lstrip("abcdefghijklmnopqrstuvwxyz")))

    poses = sorted(set(per_facing[1]) | set(per_facing[-1]), key=order)
    frames = []
    for pose in poses:
        for facing in FACINGS:
            available = per_facing[facing]
            if pose not in available:
                # A pose one facing never hit: borrow the nearest pose of the same kind.
                kind, index = pose.rstrip("0123456789"), order(pose)[1]
                same = [name for name in available if name.rstrip("0123456789") == kind]
                pose_used = min(same, key=lambda name: abs(order(name)[1] - index))
            else:
                pose_used = pose
            sprite, ax, ay = available[pose_used]
            width, height = sprite.get_size()
            raw = np.frombuffer(pygame.image.tostring(sprite, "RGBA"), dtype=np.uint8)
            frames.append((f"{pose}:{facing}", raw.reshape(height, width, 4), ax, ay))
    cell_w = max(frame[1].shape[1] for frame in frames)
    cell_h = max(frame[1].shape[0] for frame in frames)
    rows = -(-len(frames) // COLUMNS)
    sheet = np.zeros((rows * cell_h, COLUMNS * cell_w, 4), dtype=np.uint8)
    table = {}
    for index, (key, pixels, ax, ay) in enumerate(frames):
        x, y = (index % COLUMNS) * cell_w, (index // COLUMNS) * cell_h
        height, width = pixels.shape[:2]
        sheet[y : y + height, x : x + width] = pixels
        table[key] = [x, y, width, height, int(ax), int(ay)]
    # Some renderers never report "moving" (alchemist): they have no walk keys at all and the
    # Godot side shows the idle pose while walking. Anything else must be complete.
    has_walk = any(key.startswith("walk") for key in table)
    kinds = ("idle", "walk") if has_walk else ("idle",)
    missing = [
        f"{kind}{n}:{f}"
        for kind in kinds
        for n in range(PHASES)
        for f in FACINGS
        if f"{kind}{n}:{f}" not in table
    ]
    assert not missing, (hero_type, team, missing)
    return sheet, table, [cell_w, cell_h], cooldown, has_walk


def key_cases(heroes_mod, hero_cls):
    """Rows ``[attack_timer, moving, pulse, kind, index]`` from the REAL ``_hero_cache_key``."""

    def probe(timer=0, moving=False, pulse=0.0):
        hero = hero_cls("kaizen", "blue", 400, 300)
        hero.attack_timer = timer
        hero._moving_cached = moving
        hero.pulse = pulse
        key = heroes_mod._hero_cache_key("kaizen", hero)
        kind = "atk" if key[4] == "atk" else ("walk" if key[6] else "idle")
        return [timer, int(moving), pulse, kind, int(key[5])]

    rows = [probe(timer=timer) for timer in range(1, 61)]
    rows += [probe(moving=moving, pulse=step * 0.1) for moving in (False, True) for step in range(0, 90)]
    rows.append(probe(timer=7, moving=True, pulse=1.3))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hero", action="append")
    args = parser.parse_args()
    import numpy as np

    pygame, _core, _screen = env.boot()
    import heroes as heroes_mod
    from _entity import Hero

    partial = bool(args.hero)
    atlases, meta = {}, {}
    for hero_type in args.hero or HEROES:
        probe = Hero(hero_type, "blue", 400, 300)
        meta[hero_type] = {
            "name": str(probe.name),
            "radius": int(probe.radius),
            "top_offset": int(heroes_mod.get_sprite_top_offset(hero_type)),
        }
        for team in TEAMS:
            sheet, table, cell, cooldown, has_walk = bake_hero(
                pygame, np, heroes_mod, Hero, hero_type, team
            )
            meta[hero_type]["walk_poses"] = has_walk
            name = f"{hero_type}_{team}"
            entry = env.write_png(env.ART_DIR / "heroes" / f"{name}.png", sheet)
            entry.update({"cell": cell, "columns": COLUMNS, "frames": table, "cooldown": cooldown})
            atlases[name] = entry
            meta[hero_type]["cooldown"] = cooldown
            print(f"{name:16s} {entry['bytes']:7d} B  frames {len(table)}  cell {cell}  cd {cooldown}")
    if not partial:
        env.write_manifest(
            "heroes",
            {
                "generator": "godot_rebuild/bake/bake_hero_atlas.py",
                "source": "heroes/__init__.py render_hero via _entity.Hero.draw",
                "heroes": list(HEROES),
                "teams": list(TEAMS),
                "phases": PHASES,
                "atk_quant": 3,
                "meta": meta,
                "key_cases": key_cases(heroes_mod, Hero),
                "atlases": atlases,
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
