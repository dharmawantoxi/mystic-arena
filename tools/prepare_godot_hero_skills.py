#!/usr/bin/env python3
"""Export the hero_skills/ closed world to the active Godot project.

Python remains the oracle. The exporter parses both source files, the generated
HeroSkillKit.gd, the playable hero/boss catalogs and the real BaseSkill helper
methods. It writes a fail-closed data contract and a Python-oracle fixture for
the native GDScript parity suite. `--check` compares deterministic bytes and
rejects a stale generated kit or changed source hash without writing anything.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
SOURCE_DIR = ROOT / "hero_skills"
CONTRACT = PROJECT / "data/hero_skills.json"
FIXTURE = PROJECT / "tests/fixtures/hero_skills_parity.json"
KIT_PATH = PROJECT / "scripts/entities/generated/HeroSkillKit.gd"
SOURCE_FILES = ("__init__.py", "_bundle.py")
TOOL_FILES = (
    "tools/gen_hero_skill_kit.py",
    "tools/prepare_godot_entities.py",
    "tools/prepare_godot_hero_skills.py",
)
SKILL_KEYS = ("q", "w", "e", "r")
sys.path.insert(0, str(ROOT / "tools"))
import gen_hero_skill_kit as kit_gen  # noqa: E402
import prepare_godot_entities as entity_prep  # noqa: E402


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _jsonable(value, float_digits: int | None = None):
    if isinstance(value, tuple):
        return [_jsonable(item, float_digits) for item in value]
    if isinstance(value, (list, set, frozenset)):
        return [_jsonable(item, float_digits) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item, float_digits) for key, item in value.items()}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise AssertionError(f"Non-finite hero skill value: {value!r}")
        if float_digits is not None:
            return round(value, float_digits)
    return value


def _text(value: dict, float_digits: int | None = None) -> str:
    return (
        json.dumps(
            _jsonable(value, float_digits),
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
            sort_keys=True,
        )
        + "\n"
    )


def _source_digest() -> tuple[str, dict[str, str]]:
    digest = hashlib.sha256()
    files = {}
    for name in SOURCE_FILES:
        data = (SOURCE_DIR / name).read_bytes()
        files[name] = _sha256_bytes(data)
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(data)
    return digest.hexdigest(), files


def _init_assignments() -> dict:
    tree = ast.parse((SOURCE_DIR / "__init__.py").read_text(encoding="utf-8"))
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                out[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                continue
    return out


def _literal(classes: dict, class_name: str, name: str):
    return ast.literal_eval(classes[class_name]["consts"][name].value)


def _base_contract(classes: dict) -> dict:
    base = classes["BaseSkill"]
    cooldown_fields: dict[str, str] = {}
    cooldown_max_fields: dict[str, str] = {}
    trigger_shake: dict[str, float] = {}
    trigger_sound_volume: dict[str, float] = {}
    for key in SKILL_KEYS:
        check = base["methods"][f"_check_{key}_cooldown"]
        value = next(
            node.value.left
            for node in ast.walk(check)
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Compare)
        )
        if not isinstance(value, ast.Attribute):
            raise AssertionError(f"Unexpected cooldown check for {key}")
        cooldown_fields[key] = value.attr
        trigger = base["methods"][f"_trigger_{key}_cooldown"]
        trigger_shake[key] = float(ast.literal_eval(trigger.args.defaults[0]))
        assignment = next(
            node for node in trigger.body if isinstance(node, ast.Assign)
        )
        if not isinstance(assignment.targets[0], ast.Attribute) or not isinstance(
            assignment.value, ast.Attribute
        ):
            raise AssertionError(f"Unexpected cooldown trigger for {key}")
        cooldown_max_fields[key] = assignment.value.attr
        volume = next(
            keyword.value
            for node in ast.walk(trigger)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "_play_skill_sound"
            for keyword in node.keywords
            if keyword.arg == "volume"
        )
        trigger_sound_volume[key] = float(ast.literal_eval(volume))
    fallback = ast.literal_eval(base["methods"]["_skill_range"].args.defaults[-1])
    return {
        "require_target": _literal(classes, "BaseSkill", "REQUIRE_TARGET"),
        "target_range_slack": float(_literal(classes, "BaseSkill", "TARGET_RANGE_SLACK")),
        "default_visual_duration": _literal(classes, "BaseSkill", "_DEFAULT_VISUAL_DURATION"),
        "skill_range_fallback": float(fallback),
        "cooldown_fields": cooldown_fields,
        "cooldown_max_fields": cooldown_max_fields,
        "trigger_shake": trigger_shake,
        "trigger_sound_volume": trigger_sound_volume,
        "skill_sound": "hero_skill",
        "skill_sound_team": "blue",
    }


def _method_inventory(classes: dict) -> dict:
    out = {}
    for class_name, cls in sorted(classes.items()):
        methods = {}
        for name, node in sorted(cls["methods"].items(), key=lambda item: item[1].lineno):
            args = [arg.arg for arg in node.args.args]
            methods[name] = {"args": args, "arity": max(0, len(args) - 1), "lineno": node.lineno}
        out[class_name] = methods
    return out


def build_contract() -> dict:
    if sorted(path.name for path in SOURCE_DIR.glob("*.py")) != sorted(SOURCE_FILES):
        raise AssertionError("hero_skills source set changed; update the closed-world exporter")
    source_sha256, source_files = _source_digest()
    classes = kit_gen.load_bundle()
    if len(classes) != 8:
        raise AssertionError(f"Unexpected hero skill class count: {len(classes)}")
    registry = kit_gen.registry_of(classes["BossHeroSkills"])
    if len(registry) != 66:
        raise AssertionError(f"Unexpected boss-hero recipe count: {len(registry)}")
    recipes = {key: dict(recipe) for key, recipe in sorted(registry.items())}
    recipe_methods = sorted({name for recipe in recipes.values() for name in recipe.values()})
    missing_methods = [
        name for name in recipe_methods if name not in classes["BossHeroSkills"]["methods"]
    ]
    if missing_methods:
        raise AssertionError(f"Registry references missing methods: {missing_methods}")

    visual_by_class, default_visual = kit_gen.visual_durations(classes)
    visual_by_kind = {
        class_name.replace("Skills", "").lower(): {**default_visual, **override}
        for class_name, override in sorted(visual_by_class.items())
    }
    boss_visual = _literal(classes, "BossHeroSkills", "BOSS_HERO_VISUAL_DURATION")

    generated_text, state_keys, generated_recipes = kit_gen.emit_all()
    if generated_recipes != len(registry):
        raise AssertionError("Generated dispatch recipe count disagrees with the source registry")
    expected_kit = entity_prep.kits()["HeroSkillKit.gd"]
    if not KIT_PATH.is_file() or KIT_PATH.read_text(encoding="utf-8") != expected_kit:
        raise AssertionError("Stale HeroSkillKit.gd; run tools/prepare_godot_entities.py")
    kit_text = KIT_PATH.read_text(encoding="utf-8")
    kit_sha256 = _sha256_bytes(kit_text.encode("utf-8"))
    static_functions = len(re.findall(r"(?m)^static func ", kit_text))

    init = _init_assignments()
    base_modules = init["_BASE_HERO_MODULES"]
    starters = [str(row[0]) for row in base_modules]
    if sorted(starters) != sorted(kit_gen.STARTERS):
        raise AssertionError("Starter registry disagrees with the transpiler")
    core = json.loads((PROJECT / "data/core_data.json").read_text(encoding="utf-8"))
    bosses = json.loads((PROJECT / "data/bosses.json").read_text(encoding="utf-8"))
    hero_types = sorted(core["heroes"])
    boss_types = sorted(bosses["bosses"])
    handler_map = {str(row[0]): str(row[2]) for row in base_modules}
    for boss_type in boss_types:
        handler_map[boss_type] = "BossHeroSkills"
    if set(handler_map) != set(hero_types):
        raise AssertionError("Skill handlers do not cover the playable hero catalog exactly")
    if not set(recipes).issubset(set(boss_types)):
        raise AssertionError("Boss-hero recipes reference non-boss hero types")

    bridge_text = (PROJECT / "scripts/core/BattleUnit.gd").read_text(encoding="utf-8")
    bridge_methods = sorted(set(re.findall(r"(?m)^func (kit_[a-z0-9_]+)\(", bridge_text)))
    if not bridge_methods:
        raise AssertionError("BattleUnit kit_* bridge is missing")

    base = _base_contract(classes)
    contract = {
        "schema": 1,
        "source": "hero_skills/",
        "source_sha256": source_sha256,
        "source_files": source_files,
        "tooling_sha256": {name: _sha256(ROOT / name) for name in TOOL_FILES},
        "generated_kit": {
            "path": "res://scripts/entities/generated/HeroSkillKit.gd",
            "sha256": kit_sha256,
            "lines": kit_text.count("\n"),
            "static_functions": static_functions,
        },
        "counts": {
            "source_files": len(SOURCE_FILES),
            "classes": len(classes),
            "starters": len(starters),
            "recipes": len(recipes),
            "recipe_methods": len(recipe_methods),
            "hero_handlers": len(handler_map),
            "boss_types": len(boss_types),
            "state_keys": len(state_keys),
            "methods": sum(len(row) for row in _method_inventory(classes).values()),
            "kit_static_functions": static_functions,
        },
        "starters": starters,
        "skill_keys": list(SKILL_KEYS),
        "base_modules": _jsonable(base_modules),
        "legacy_aliases": {
            "extra": _jsonable(init["_EXTRA"]),
            "plain": _jsonable(init["_PLAIN_SYMS"]),
        },
        "auto_register": {
            "base_hero_modules": _jsonable(base_modules),
            "boss_types": boss_types,
            "boss_handler": "BossHeroSkills",
        },
        "handler_map": handler_map,
        "registry": recipes,
        "recipe_methods": recipe_methods,
        "visual_duration": visual_by_kind,
        "boss_hero_visual_duration": _jsonable(boss_visual),
        "default_visual_duration": _jsonable(default_visual),
        "state_keys": sorted(state_keys),
        "methods": _method_inventory(classes),
        "bridge_methods": bridge_methods,
        "base": base,
        "runtime": {
            "generated_kit": "res://scripts/entities/generated/HeroSkillKit.gd",
            "cooldown_units": "frames",
            "visual_units": "frames",
            "unknown_handler": "",
            "missing_recipe": "",
            "fallback_handler": "BossHeroSkills",
        },
    }
    if not math.isfinite(float(base["target_range_slack"])):
        raise AssertionError("Non-finite target range slack")
    return _jsonable(contract)


class _SilentSound:
    def play(self, *_args, **_kwargs) -> None:
        return None


@contextlib.contextmanager
def source_module():
    """Load hero_skills/_bundle.py with only its pure module dependencies stubbed."""
    sound = types.ModuleType("sound_manager")
    sound.SoundManager = _SilentSound
    settings = types.ModuleType("settings")
    settings.HERO_TYPES = {}
    settings.HERO_LEVELS = {}
    settings.get_all_hero_types = lambda: {}
    package = types.ModuleType("hero_skills")
    package.__path__ = [str(SOURCE_DIR)]
    names = ("sound_manager", "settings", "hero_skills", "hero_skills._bundle")
    old = {name: sys.modules.get(name) for name in names}
    sys.modules.update({"sound_manager": sound, "settings": settings, "hero_skills": package})
    try:
        spec = importlib.util.spec_from_file_location("hero_skills._bundle", SOURCE_DIR / "_bundle.py")
        if spec is None or spec.loader is None:
            raise AssertionError("Cannot load hero_skills/_bundle.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["hero_skills._bundle"] = module
        spec.loader.exec_module(module)
        yield module
    finally:
        for name, value in old.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value


class _Hero:
    def __init__(self, **kwargs):
        self.x = 0.0
        self.y = 0.0
        self.team = "blue"
        self.hero_type = "kaizen"
        self.target = None
        self.alive = True
        self.range = 0.0
        self.skill_range = 0.0
        self.skill_data = {}
        self.skill_damage = 0.0
        self.dmg_school = "physical"
        self.skill_timer = 0
        self.w_cooldown = 0
        self.e_cooldown = 0
        self.r_cooldown = 0
        self.skill_cooldown_max = 0
        self.w_cooldown_max = 0
        self.e_cooldown_max = 0
        self.r_cooldown_max = 0
        self.active_skill = None
        self.active_skill_timer = 0
        self.damage = 0.0
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _get_all_enemies(self, all_units, all_towers, all_bases):
        return list(all_units) + list(all_towers) + list(all_bases)


class _Unit:
    def __init__(self, x: float, y: float, unit_id: int):
        self.x = float(x)
        self.y = float(y)
        self.unit_id = unit_id
        self.alive = True
        self.team = "red"
        self.damage_events = []
        self.slows = []
        self.attack_timer = 0

    def take_damage(self, damage, team, source=None, school=None):
        self.damage_events.append(
            {"damage": int(damage), "team": team, "source": getattr(source, "unit_id", None),
             "school": school}
        )

    def apply_slow(self, amount, duration):
        self.slows.append([amount, duration])


def _handler_for(module, hero_type: str, hero: _Hero):
    if hero_type in kit_gen.STARTERS:
        namespace = getattr(module, f"_NS_{hero_type}_skills")
        return getattr(namespace, f"{hero_type.capitalize()}Skills")(hero)
    return module._NS_boss_hero_skills.BossHeroSkills(hero)


def build_oracle(contract: dict, module) -> dict:
    starters = contract["starters"]
    handler_map = contract["handler_map"]
    registry = contract["registry"]
    boss_types = contract["auto_register"]["boss_types"]
    base = contract["base"]

    hero_kind_cases = []
    for hero_type in sorted(set(handler_map) | {"__unknown__"}):
        handler = handler_map.get(hero_type, "")
        if not handler:
            kind = "unknown"
        elif hero_type in starters:
            kind = "starter"
        else:
            kind = "boss"
        hero_kind_cases.append({"hero_type": hero_type, "kind": kind, "handler": handler})

    visual_cases = []
    for hero_type in sorted(set(handler_map) | {"__unknown__"}):
        hero = _Hero(hero_type=hero_type)
        handler = _handler_for(module, hero_type, hero)
        for key in SKILL_KEYS:
            visual_cases.append(
                {
                    "hero_type": hero_type,
                    "key": key,
                    "frames": int(handler._get_visual_duration(key)),
                }
            )

    registry_cases = []
    for hero_type in sorted(set(boss_types) | {"__unknown__"}):
        recipe = registry.get(hero_type, {})
        for key in SKILL_KEYS:
            registry_cases.append(
                {"hero_type": hero_type, "key": key, "method": str(recipe.get(key, ""))}
            )

    cooldown_cases = []
    for key in SKILL_KEYS:
        field = base["cooldown_fields"][key]
        for timer in (-4, 0, 1, 17):
            hero = _Hero(**{field: timer})
            ready = bool(getattr(module.BaseSkill(hero), f"_check_{key}_cooldown")())
            cooldown_cases.append({"key": key, "timer": timer, "ready": ready})

    range_configs = [
        (150.0, 220.0, {}, 200.0),
        (150.0, 0.0, {"skill_range": 260}, 200.0),
        (150.0, None, {}, 200.0),
        (150.0, "invalid", {"skill_range": 300}, 200.0),
        (400.0, 220.0, {}, 200.0),
        (0.0, 0.0, {}, 350.0),
        (150.0, -20.0, {"skill_range": 260}, 200.0),
    ]
    skill_range_cases = []
    for attack_range, skill_range, skill_data, fallback in range_configs:
        hero = _Hero(range=attack_range, skill_range=skill_range, skill_data=skill_data)
        expected = float(module.BaseSkill(hero)._skill_range(fallback))
        skill_range_cases.append(
            {
                "attack_range": attack_range,
                "skill_range": skill_range,
                "skill_data": skill_data,
                "fallback": fallback,
                "expected": expected,
            }
        )

    geometry_specs = [
        ((0.0, 0.0), 100.0, [(0.0, 0.0), (30.0, 40.0), (60.0, 80.0), (90.0, 120.0), (-40.0, 0.0)]),
        ((10.0, 10.0), 50.0, [(10.0, 10.0), (40.0, 50.0), (60.0, 10.0), (10.0, -30.0)]),
        ((0.0, 0.0), 30.0, [(0.0, 0.0), (30.0, 40.0), (20.0, 0.0)]),
    ]
    geometry_cases = []
    for center, range_value, positions in geometry_specs:
        units = [_Unit(x, y, index) for index, (x, y) in enumerate(positions)]
        hero = _Hero(x=center[0], y=center[1])
        pairs = module.BaseSkill(hero)._get_enemies_in_range(
            units, [], [], range_value, center[0], center[1]
        )
        geometry_cases.append(
            {
                "center": [center[0], center[1]],
                "range": range_value,
                "units": [{"x": x, "y": y} for x, y in positions],
                "expected": [[int(unit.unit_id), float(dist)] for unit, dist in pairs],
                "hit_count": len(pairs),
            }
        )

    aoe_cases = []
    for skill_damage, multiplier in [(123.4, 1.0), (123.4, 0.5), (123.4, 2.0), (99.9, 0.0)]:
        units = [_Unit(0.0, 0.0, 0), _Unit(30.0, 40.0, 1), _Unit(200.0, 0.0, 2)]
        hero = _Hero(x=0.0, y=0.0, skill_damage=skill_damage, unit_id=-1)
        hit_count = module.BaseSkill(hero)._deal_aoe_damage(units, [], [], 100.0, multiplier)
        damage = int(skill_damage * multiplier)
        aoe_cases.append(
            {
                "skill_damage": skill_damage,
                "multiplier": multiplier,
                "expected_damage": damage,
                "hit_count": hit_count,
                "damage_events": [event["damage"] for event in units[0].damage_events]
                + [event["damage"] for event in units[1].damage_events],
            }
        )

    trigger_types = sorted(set(starters) | {"nyzrak", "vhalzun", "gornak"})
    trigger_cases = []
    cooldown_max = {"q": 301, "w": 241, "e": 421, "r": 901}
    for hero_type in trigger_types:
        for key in SKILL_KEYS:
            max_field = base["cooldown_max_fields"][key]
            hero = _Hero(
                hero_type=hero_type,
                **{
                    "skill_cooldown_max": cooldown_max["q"],
                    "w_cooldown_max": cooldown_max["w"],
                    "e_cooldown_max": cooldown_max["e"],
                    "r_cooldown_max": cooldown_max["r"],
                },
            )
            handler = _handler_for(module, hero_type, hero)
            getattr(handler, f"_trigger_{key}_cooldown")()
            trigger_cases.append(
                {
                    "hero_type": hero_type,
                    "key": key,
                    "cooldown_max": cooldown_max[key],
                    "expected": {
                        "cooldown_field": base["cooldown_fields"][key],
                        "cooldown": int(getattr(hero, base["cooldown_fields"][key])),
                        "active_skill": key,
                        "active_skill_timer": int(hero.active_skill_timer),
                        "shake": base["trigger_shake"][key],
                        "sound_volume": base["trigger_sound_volume"][key],
                        "max_field": max_field,
                    },
                }
            )
    trigger_cases.append(
        {
            "hero_type": "__unknown__",
            "key": "q",
            "cooldown_max": cooldown_max["q"],
            "expected": {},
        }
    )

    return _jsonable(
        {
            "schema": 1,
            "source_sha256": contract["source_sha256"],
            "generated_kit_sha256": contract["generated_kit"]["sha256"],
            "contract_cases": {
                "starters": starters,
                "recipes": contract["counts"]["recipes"],
                "hero_handlers": contract["counts"]["hero_handlers"],
                "boss_types": contract["counts"]["boss_types"],
                "state_keys": contract["counts"]["state_keys"],
                "kit_static_functions": contract["counts"]["kit_static_functions"],
                "require_target": base["require_target"],
                "target_range_slack": base["target_range_slack"],
                "skill_range_fallback": base["skill_range_fallback"],
                "default_visual_duration": base["default_visual_duration"],
            },
            "hero_kind_cases": hero_kind_cases,
            "visual_duration_cases": visual_cases,
            "registry_cases": registry_cases,
            "cooldown_cases": cooldown_cases,
            "skill_range_cases": skill_range_cases,
            "geometry_cases": geometry_cases,
            "aoe_cases": aoe_cases,
            "trigger_cases": trigger_cases,
        },
        float_digits=12,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        contract = build_contract()
        with source_module() as module:
            oracle = build_oracle(contract, module)
        outputs = {CONTRACT: _text(contract), FIXTURE: _text(oracle, float_digits=12)}
        if args.check:
            stale = [
                str(path.relative_to(ROOT))
                for path, text in outputs.items()
                if not path.is_file() or path.read_text(encoding="utf-8") != text
            ]
            if stale:
                parser.exit(
                    1,
                    "Stale hero skills data: %s; run tools/prepare_godot_hero_skills.py\n"
                    % ", ".join(stale),
                )
        else:
            for path, text in outputs.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix(path.suffix + ".tmp")
                temporary.write_text(text, encoding="utf-8")
                temporary.replace(path)
    except (AssertionError, ValueError, TypeError, KeyError, OSError, ImportError) as exc:
        parser.exit(1, f"Hero skills preparation failed: {exc}\n")
    digest = hashlib.sha256(outputs[CONTRACT].encode("utf-8")).hexdigest()[:12]
    print(
        f"{'Verified' if args.check else 'Prepared'} hero skills: "
        f"{contract['counts']['recipes']} recipes, "
        f"{contract['counts']['hero_handlers']} handlers, "
        f"{contract['counts']['state_keys']} kit state keys; sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
