"""Bake animated source boss bodies from ``heroes._boss_render_sprite_fast``.

Every boss receives eight idle phases, walking when its renderer reports movement,
and four evenly spaced attack poses. Bosses with source smart AI also receive two
samples of each Q/W/E/R skill using the real cast durations. The native resolver
chooses the nearest baked keyframe between samples.

The bake drives the real renderer and movement/pose controllers, preserves the source
cache key, and stores lossless WebP with deduplicated pixels. Live FX, auras, HP/name
overlays and gameplay remain outside the atlas.
"""
from __future__ import annotations

import argparse
import ast
import copy
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402
from atlas_pack import pack  # noqa: E402

FACINGS = (-1, 1)
COLUMNS = 10
GAP = 2
MAX_TRIES = 12
PHASES = 8
IDLE_STEPS = 40
ATTACK_SAMPLES = 4
SKILL_SAMPLES = 2


def make_boss(boss_cls, boss_type, facing):
    random.seed(f"{boss_type}:{facing}:init")
    boss = boss_cls(boss_type)
    boss.x, boss.y = 400.0, 300.0
    boss.entrance_timer = 0
    boss.direction = facing
    boss.timer = 0
    boss.active_skill = None
    boss.active_skill_timer = 0
    boss.ability_active = False
    boss.hurt_flash_timer = 0
    boss.is_enraged = False
    boss.rage_active = False
    boss._moving_cached = False
    return boss


def pose_name(key):
    if key[8] == "skill":
        return f"skill_{key[9]}_{key[10]}"
    if key[8] == "atk":
        return f"atk{key[9]}"
    return ("walk" if key[10] else "idle") + str(key[9])


def pose_order(name):
    if name.startswith("skill_"):
        _prefix, skill, index = name.split("_")
        return (f"skill_{skill}", int(index))
    return (name.rstrip("0123456789"), int(name.lstrip("abcdefghijklmnopqrstuvwxyz_")))


def _self_assignment(node, attribute):
    return isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == "self"
        and target.attr == attribute
        for target in node.targets
    )


def smart_skill_durations():
    """Harvest real Q/W/E/R durations from the source smart-AI call graph."""
    tree = ast.parse((env.REPO / "bosses/base_boss.py").read_text(encoding="utf-8"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss")
    methods = {node.name: node for node in cls.body if isinstance(node, ast.FunctionDef)}
    result = {}
    for method in methods.values():
        if not method.name.startswith("_smart_ai_"):
            continue
        boss_type = method.name[len("_smart_ai_") :]
        pending = [method]
        visited = set()
        skills = {}
        while pending:
            current = pending.pop()
            if current.name in visited:
                continue
            visited.add(current.name)
            active = None
            for node in sorted(
                ast.walk(current),
                key=lambda item: (getattr(item, "lineno", -1), getattr(item, "col_offset", -1)),
            ):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    called = node.func.attr
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == "self" and called in methods:
                        pending.append(methods[called])
                if _self_assignment(node, "active_skill"):
                    active = node.value.value if isinstance(node.value, ast.Constant) else None
                elif _self_assignment(node, "active_skill_timer") and active in ("q", "w", "e", "r"):
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
                        skills[active] = node.value.value
        if skills:
            result[boss_type] = dict(sorted(skills.items()))
    return result


def _sample_names(heroes_mod, boss, count, skill=None):
    """Evenly spaced cache-pose names across one real attack/skill timeline."""
    duration = int(boss.timer if skill is None else boss.active_skill_timer)
    names = []
    for value in range(duration, 0, -1):
        if skill is None:
            boss.timer = value
        else:
            boss.active_skill_timer = value
        name = pose_name(heroes_mod._boss_cache_key(boss.boss_type, boss))
        if name not in names:
            names.append(name)
    if len(names) <= count:
        return names
    return [names[round(step * (len(names) - 1) / (count - 1))] for step in range(count)]


def _quantum(heroes_mod, boss, skill=False):
    for value in range(1, 33):
        boss.timer = 0 if skill else value
        boss.active_skill = "q" if skill else None
        boss.active_skill_timer = value if skill else 0
        key = heroes_mod._boss_cache_key(boss.boss_type, boss)
        index = key[10] if skill else key[9]
        if index == 1:
            return value
    raise AssertionError((boss.boss_type, "quantum", skill))


def collect(heroes_mod, boss_cls, draw_fn, boss_type, facing, skill_durations):
    seen = {}
    missed = set()
    clock = [0]

    def fresh():
        heroes_mod.clear_boss_sprite_cache()
        return make_boss(boss_cls, boss_type, facing)

    def grab(boss, tag, wanted):
        key = heroes_mod._boss_cache_key(boss_type, boss)
        ticks = clock[0]
        clock[0] += 17
        try:
            snapshot = copy.deepcopy(vars(boss))
        except Exception:
            snapshot = vars(boss).copy()
        out = None
        for attempt in range(MAX_TRIES):
            if attempt:
                boss.__dict__.clear()
                boss.__dict__.update(copy.deepcopy(snapshot))
            random.seed(f"{boss_type}:{facing}:{tag}:{attempt}")
            heroes_mod._reset_hero_render_budget()
            with env.virtual_ticks(heroes_mod.pygame, ticks):
                out = heroes_mod._boss_render_sprite_fast(boss_type, boss, draw_fn, key[8])
            if out is not None:
                break
        if out is None:
            # Some source poses deliberately reject sprite caching (large/uncacheable FX).
            # Bake the same direct draw path used by Boss.draw instead of inventing a pose.
            boss.__dict__.clear()
            boss.__dict__.update(copy.deepcopy(snapshot))
            pygame = heroes_mod.pygame
            canvas = pygame.Surface((1600, 1600), pygame.SRCALPHA)
            center = 800
            try:
                with env.virtual_ticks(pygame, ticks):
                    draw_fn(canvas, boss, center, center)
                box = canvas.get_bounding_rect(min_alpha=8)
                # Screen-spanning beams/far projectiles are live FX, not body pixels.
                # Keep the source's maximum local body canvas and its world anchor.
                half = int(heroes_mod.BOSS_CANVAS_MAX_HALF)
                local = pygame.Rect(center - half, center - half, half * 2, half * 2)
                cropped = box.clip(local)
                if cropped.width > 0 and cropped.height > 0:
                    out = (
                        canvas.subsurface(cropped).copy(),
                        center - cropped.x,
                        center - cropped.y,
                    )
            except Exception:
                out = None
        if out is None:
            if wanted(key):
                missed.add(pose_name(key))
            return
        if wanted(key):
            pose = pose_name(key)
            if pose not in seen:
                sprite, ax, ay = out
                seen[pose] = (sprite, int(ax), int(ay))

    probe = fresh()
    cooldown = int(probe._eff_attack_cd(probe.attack_cooldown))
    attack_quant = _quantum(heroes_mod, probe)
    skill_quant = _quantum(heroes_mod, probe, skill=True)

    # Standing and walking timelines execute the real per-frame movement/pose controllers.
    boss = fresh()
    for step in range(IDLE_STEPS):
        boss.pulse = step * 0.1
        grab(boss, f"idle:{step}", lambda key: key[8] == "idle" and not key[10])
    boss = fresh()
    for step in range(IDLE_STEPS * 3):
        boss.pulse = step * 0.1
        boss.x = 400.0 + step * 2.0
        grab(boss, f"walk:{step}", lambda key: key[8] == "idle" and key[10])

    boss = fresh()
    for settle in range(3):
        boss.pulse = settle * 0.1
        grab(boss, f"settle:{settle}", lambda key: False)
    boss.pulse = 0.0
    boss.timer = cooldown
    attack_names = _sample_names(heroes_mod, boss, ATTACK_SAMPLES)
    boss.timer = cooldown
    while boss.timer > 0:
        grab(boss, f"atk:{boss.timer}", lambda key: pose_name(key) in attack_names and key[8] == "atk")
        boss.timer -= 1

    for skill, duration in skill_durations.items():
        boss = fresh()
        for settle in range(3):
            boss.pulse = settle * 0.1
            grab(boss, f"{skill}:settle:{settle}", lambda key: False)
        boss.pulse = 0.0
        boss.active_skill = skill
        boss.active_skill_timer = duration
        candidates = _sample_names(heroes_mod, boss, SKILL_SAMPLES * 2, skill=skill)
        boss.active_skill_timer = duration
        while boss.active_skill_timer > 0:
            grab(
                boss,
                f"{skill}:{boss.active_skill_timer}",
                lambda key, names=candidates, skill=skill: (
                    key[8] == "skill" and key[9] == skill and pose_name(key) in names
                ),
            )
            boss.active_skill_timer -= 1
        valid = [name for name in candidates if name in seen]
        # Keep two valid keyframes; empty/clipped endpoint candidates are not required.
        selected = [valid[0], valid[-1]] if len(valid) >= 2 else valid
        for name in candidates:
            if name not in selected:
                seen.pop(name, None)
        missed.difference_update(candidates)
        if len(selected) < SKILL_SAMPLES:
            missed.update(name for name in candidates if name not in selected)
    return seen, cooldown, attack_quant, skill_quant, missed


def bake_boss(np, pygame, heroes_mod, boss_cls, draw_fn, boss_type, durations):
    per_facing = {}
    facts = None
    missed = set()
    for facing in FACINGS:
        collected = collect(heroes_mod, boss_cls, draw_fn, boss_type, facing, durations)
        per_facing[facing] = collected[0]
        missed.update(collected[-1])
        facts = collected[1:-1] + (missed,)
    poses = sorted(set(per_facing[1]) | set(per_facing[-1]), key=pose_order)
    frames = []
    for pose in poses:
        for facing in FACINGS:
            available = per_facing[facing]
            if pose in available:
                pose_used = pose
            else:
                kind, index = pose_order(pose)
                same = [name for name in available if pose_order(name)[0] == kind]
                assert same, (boss_type, facing, pose, "no same-kind fallback")
                pose_used = min(same, key=lambda name: abs(pose_order(name)[1] - index))
            sprite, ax, ay = available[pose_used]
            width, height = sprite.get_size()
            raw = np.frombuffer(pygame.image.tostring(sprite, "RGBA"), dtype=np.uint8)
            frames.append((f"{pose}:{facing}", raw.reshape(height, width, 4).copy(), ax, ay))
    sheet, table, cell, unique = pack(frames, COLUMNS, GAP, tight=True)
    for phase in range(PHASES):
        for facing in FACINGS:
            assert f"idle{phase}:{facing}" in table, (boss_type, phase, facing)
    return sheet, table, cell, unique, facts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--boss", action="append")
    args = parser.parse_args()
    import numpy as np

    pygame, _core, _screen = env.boot()
    import heroes as heroes_mod
    from bosses._boss_index import BOSS_INDEX
    from bosses.base_boss import BOSS_LABEL_TOP, Boss, _get_boss_draw_func

    smart = smart_skill_durations()
    partial = bool(args.boss)
    bosses = {}
    total = 0
    for boss_type in args.boss or sorted(BOSS_INDEX):
        draw_fn = _get_boss_draw_func(boss_type)
        durations = smart.get(boss_type, {})
        sheet, table, cell, unique, facts = bake_boss(
            np, pygame, heroes_mod, Boss, draw_fn, boss_type, durations
        )
        cooldown, attack_quant, skill_quant, unbaked = facts
        attack_names = sorted(
            {key.rsplit(":", 1)[0] for key in table if key.startswith("atk")}, key=pose_order
        )
        baked_skills = {}
        for skill in durations:
            prefix = f"skill_{skill}_"
            names = sorted(
                {key.rsplit(":", 1)[0] for key in table if key.startswith(prefix)}, key=pose_order
            )
            if names:
                baked_skills[skill] = names
        probe = make_boss(Boss, boss_type, -1)
        entry = env.write_webp(env.ART_DIR / "bosses" / f"{boss_type}.webp", sheet)
        entry.update(
            {
                "cell": cell,
                "columns": COLUMNS,
                "frames": table,
                "unique_frames": unique,
                "radius": int(probe.radius),
                "class": probe.boss_class,
                "label_top": int(BOSS_LABEL_TOP.get(boss_type, probe.radius)),
                "cooldown": cooldown,
                "attack_quant": attack_quant,
                "skill_quant": skill_quant,
                "walk_poses": any(name.startswith("walk") for name in table),
                "attack_poses": attack_names,
                "skills": baked_skills,
                "unbaked_poses": sorted(unbaked),
            }
        )
        bosses[boss_type] = entry
        total += entry["bytes"]
        print(
            f"{boss_type:24s} {entry['bytes']:8d} B  frames {len(table):3d}  "
            f"unique {unique:3d}  skills {len(baked_skills)}",
            flush=True,
        )
        if unbaked:
            print(f"WARNING {boss_type} unbaked: {sorted(unbaked)}", flush=True)
    if not partial:
        cases = []
        for direction in (-3, -1, 0, 1, 2, 7):
            boss = make_boss(Boss, "abaddon", -1)
            boss.direction = direction
            cases.append([direction, heroes_mod._boss_cache_key("abaddon", boss)[4]])
        env.write_manifest(
            "bosses",
            {
                "generator": "godot_rebuild/bake/bake_boss_atlas.py",
                "source": "bosses/base_boss.py Boss.draw via heroes._boss_render_sprite_fast",
                "format": "webp-lossless-v0",
                "pose": "8 idle phases + walk + 4 attack samples + source smart skills",
                "phases": PHASES,
                "attack_samples": ATTACK_SAMPLES,
                "skill_samples": SKILL_SAMPLES,
                "smart_bosses": sorted(smart),
                "facings": list(FACINGS),
                "facing_cases": cases,
                "bosses": bosses,
            },
        )
        print(f"bosses {len(bosses)}  {total} B", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
