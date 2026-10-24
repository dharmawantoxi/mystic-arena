"""Bake source hero body sprites from ``heroes/__init__.py`` ``render_hero``.

The real ``Hero.draw`` is driven through idle, walking and attack timelines for every
one of the 222 roster heroes. Blue has a source atlas for every hero. The six non-boss
heroes also have a red atlas; red boss-heroes reuse their native boss frames at the
source hero scale instead of storing hundreds of nearly identical sheets.

Level does not change the body, so level 1 represents every level. The name badge, HP
bar, selection ring and live FX remain native overlays. Images are lossless WebP and
identical pose pixels share one atlas rectangle without sharing their anchors.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402
from atlas_pack import pack  # noqa: E402

NON_BOSS = ("grimjaw", "kaizen", "sylara", "thorne", "vex", "zephyr")
_CATALOG = json.loads((env.GODOT / "data/ai/recruitment.json").read_text(encoding="utf-8"))["catalog"]
HEROES = tuple(sorted(_CATALOG))
BOSS_HEROES = tuple(sorted(set(HEROES) - set(NON_BOSS)))
assert len(HEROES) == 222 and len(BOSS_HEROES) == 216
TEAMS = ("blue", "red")
FACINGS = (1, -1)
COLUMNS = 10
PHASES = 8
IDLE_STEPS = 40
SKILL_SAMPLES = 2
SKILL_QUANT = 2
# The six non-boss heroes cannot reuse a boss sheet. These are their real cast
# durations, mirrored by the already ported native skill handlers.
NON_BOSS_SKILL_DURATIONS = {
    "grimjaw": {"q": 180, "w": 90, "e": 60, "r": 90},
    "kaizen": {"q": 60, "w": 90, "e": 60, "r": 100},
    "sylara": {"q": 180, "w": 180, "e": 150, "r": 60},
    "thorne": {"q": 40, "w": 100, "e": 60, "r": 120},
    "vex": {"q": 40, "w": 100, "e": 60, "r": 80},
    "zephyr": {"q": 240, "w": 180, "e": 180, "r": 240},
}


def pose_name(key):
    """``_hero_cache_key`` tuple -> pose name used by the atlas."""
    if key[4] == "skill":
        return f"skill_{key[5]}_{key[6]}"
    if key[4] == "atk":
        return f"atk{key[5]}"
    return ("walk" if key[6] else "idle") + str(key[5])


def _skill_sample_names(heroes_mod, hero_type, hero, skill, count):
    """Evenly spaced source cache-pose names across one real cast timeline."""
    duration = int(hero.active_skill_timer)
    names = []
    for value in range(duration, 0, -1):
        hero.active_skill_timer = value
        key = heroes_mod._hero_cache_key(hero_type, hero)
        assert key[4] == "skill" and key[5] == skill
        name = pose_name(key)
        if name not in names:
            names.append(name)
    if len(names) <= count:
        return names
    return [names[round(step * (len(names) - 1) / (count - 1))] for step in range(count)]


def collect(pygame, heroes_mod, hero_cls, hero_type, team, facing, skill_durations):
    """First sprite each pose key receives in cold-cache runs of the real timelines."""
    surface = pygame.Surface((800, 600), pygame.SRCALPHA)
    seen = {}
    clock = [0]

    def fresh():
        heroes_mod._hero_sprite_cache.clear()
        heroes_mod._hero_skill_cache.clear()
        random.seed(f"{hero_type}:{team}:{facing}:init")
        hero = hero_cls(hero_type, team, 400, 300)
        hero.facing = facing
        hero.attack_timer = 0
        hero.active_skill = None
        hero.active_skill_timer = 0
        return hero

    def grab(hero, tag, wanted):
        random.seed(f"{hero_type}:{team}:{facing}:{tag}")
        # The key is computed before the renderer runs (it may flip ``_moving_cached``).
        key = heroes_mod._hero_cache_key(hero_type, hero)
        heroes_mod._reset_hero_render_budget()
        ticks = clock[0]
        clock[0] += 17
        with env.virtual_ticks(pygame, ticks):
            hero.draw(surface)
        cache, _limit = heroes_mod._cache_for(key)
        entry = cache.get(key)
        if entry is None or not wanted(key):
            return
        pose = pose_name(key)
        if pose not in seen:
            seen[pose] = (entry[0], entry[1], entry[2])

    # A: standing still -> idle poses.
    hero = fresh()
    for step in range(IDLE_STEPS):
        hero.pulse = step * 0.1
        grab(hero, f"idle:{step}", lambda key: key[4] == "idle" and not key[6])
    # B: walking from a cold cache. Renderers detect movement on cache misses, so the
    # moving keys fill on later laps just as they do in the live game.
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

    # Only the six heroes without a boss sheet need separate skill pixels. Boss-heroes
    # resolve their source smart-skill frames through BossArt in both team colours.
    for skill, duration in skill_durations.items():
        hero = fresh()
        for settle in range(3):
            hero.pulse = settle * 0.1
            grab(hero, f"{skill}:settle:{settle}", lambda key: False)
        hero.pulse = 0.0
        hero.active_skill = skill
        hero.active_skill_timer = duration
        candidates = _skill_sample_names(
            heroes_mod, hero_type, hero, skill, SKILL_SAMPLES * 2
        )
        hero.active_skill_timer = duration
        while hero.active_skill_timer > 0:
            grab(
                hero,
                f"{skill}:{hero.active_skill_timer}",
                lambda key, names=candidates, skill=skill: (
                    key[4] == "skill" and key[5] == skill and pose_name(key) in names
                ),
            )
            hero.active_skill_timer -= 1
        valid = [name for name in candidates if name in seen]
        selected = [valid[0], valid[-1]] if len(valid) >= 2 else valid
        for name in candidates:
            if name not in selected:
                seen.pop(name, None)
        assert len(selected) == SKILL_SAMPLES, (
            hero_type,
            team,
            facing,
            skill,
            candidates,
            selected,
        )
    return seen, cooldown


def bake_hero(pygame, np, heroes_mod, hero_cls, hero_type, team):
    per_facing = {}
    cooldown = 0
    for facing in FACINGS:
        per_facing[facing], cooldown = collect(
            pygame,
            heroes_mod,
            hero_cls,
            hero_type,
            team,
            facing,
            NON_BOSS_SKILL_DURATIONS.get(hero_type, {}),
        )

    def order(name):
        if name.startswith("skill_"):
            _prefix, skill, index = name.split("_")
            return ("skill", skill, int(index))
        return (
            name.rstrip("0123456789"),
            "",
            int(name.lstrip("abcdefghijklmnopqrstuvwxyz")),
        )

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
            frames.append((f"{pose}:{facing}", raw.reshape(height, width, 4).copy(), ax, ay))
    sheet, table, cell, unique = pack(frames, COLUMNS)
    # Some renderers never report moving: Godot resolves walk to idle in that case.
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
    return sheet, table, cell, cooldown, has_walk, unique


def skill_families(table):
    """Skill -> sorted baked pose names, independent of facing aliases."""
    grouped = {}
    for key in table:
        pose = key.split(":", 1)[0]
        if not pose.startswith("skill_"):
            continue
        _prefix, skill, _index = pose.split("_")
        grouped.setdefault(skill, set()).add(pose)
    return {
        skill: sorted(poses, key=lambda name: int(name.rsplit("_", 1)[1]))
        for skill, poses in sorted(grouped.items())
    }


def key_cases(heroes_mod, hero_cls):
    """Rows ``[attack_timer, moving, pulse, kind, index]`` from the real cache key."""

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
        random.seed(f"{hero_type}:probe")
        probe = Hero(hero_type, "blue", 400, 300)
        with env.virtual_ticks(pygame, 0):
            top_offset = int(heroes_mod.get_sprite_top_offset(hero_type))
            hero_scale = float(heroes_mod._get_hero_scale(hero_type))
        meta[hero_type] = {
            "name": str(probe.name),
            "radius": int(probe.radius),
            "top_offset": top_offset,
            "hero_scale": hero_scale,
        }
        teams = TEAMS if hero_type in NON_BOSS else ("blue",)
        for team in teams:
            sheet, table, cell, cooldown, has_walk, unique = bake_hero(
                pygame, np, heroes_mod, Hero, hero_type, team
            )
            if "cooldown" in meta[hero_type]:
                assert meta[hero_type]["cooldown"] == cooldown
                assert meta[hero_type]["walk_poses"] == has_walk
            meta[hero_type]["walk_poses"] = has_walk
            name = f"{hero_type}_{team}"
            entry = env.write_webp(env.ART_DIR / "heroes" / f"{name}.webp", sheet)
            entry.update(
                {
                    "cell": cell,
                    "columns": COLUMNS,
                    "frames": table,
                    "cooldown": cooldown,
                    "unique_frames": unique,
                    "skill_quant": SKILL_QUANT,
                    "skills": skill_families(table),
                }
            )
            atlases[name] = entry
            meta[hero_type]["cooldown"] = cooldown
            print(
                f"{name:26s} {entry['bytes']:8d} B  frames {len(table):3d}  "
                f"unique {unique:3d}  cell {cell}  cd {cooldown}",
                flush=True,
            )
    if not partial:
        env.write_manifest(
            "heroes",
            {
                "generator": "godot_rebuild/bake/bake_hero_atlas.py",
                "source": "heroes/__init__.py render_hero via _entity.Hero.draw",
                "format": "webp-lossless-v0",
                "heroes": list(HEROES),
                "non_boss": list(NON_BOSS),
                "shared_red_bosses": list(BOSS_HEROES),
                "teams": list(TEAMS),
                "phases": PHASES,
                "atk_quant": 3,
                "skill_quant": SKILL_QUANT,
                "skill_samples": SKILL_SAMPLES,
                "skill_heroes": list(NON_BOSS),
                "meta": meta,
                "key_cases": key_cases(heroes_mod, Hero),
                "atlases": atlases,
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
