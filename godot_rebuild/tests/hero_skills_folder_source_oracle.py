"""Whole-folder oracle for `hero_skills/`: two files, every symbol accounted for.

`hero_skills/` is small on disk and large in reach: `_bundle.py` (5.220 lines)
is the merge of eight Pygame skill modules, so it holds the `BaseSkill` helper
API that every hero kit inherits, the `BossHeroSkills` registry (66 recipes over
264 cast methods) with its generic dispatcher and `_fallback_cast`, and the six
starter kits (kaizen, grimjaw, sylara, thorne, vex, zephyr). `__init__.py` is the
handler registry plus the `sys.modules` aliasing that keeps the deleted
submodule names importable.

Everything here is parsed with `ast`; nothing executes, so no pygame, no display
and no `settings`/`sound_manager` imports are needed. The native side is asked to
account for the result in `tests/hero_skills_folder_checks.gd`.

What the fixture pins:

* `BaseSkill`: 30 methods, `REQUIRE_TARGET`, `TARGET_RANGE_SLACK` (1.15), the
  `_DEFAULT_VISUAL_DURATION` and empty class-level `SKILL_VISUAL_DURATION`, and
  the shake/volume feedback each `_trigger_*_cooldown` performs;
* `BossHeroSkills`: the 66-entry registry, the per-hero visual overrides
  (`nyzrak`, `vhalzun`), the per-slot shake amounts the `cast_*` wrappers pass,
  the `max(skill_range, 140)` cast gate, and `_fallback_cast`'s multipliers,
  timer and AOE radii;
* the six starter kits: their `SKILL_VISUAL_DURATION` and the shake amount of
  every `_trigger_*_cooldown` call;
* `__init__.py`: handler registry API, the seven aliased submodules, the six
  auto-registered starters and the "register every boss type" loop.

Run: python godot_rebuild/tests/hero_skills_folder_source_oracle.py --write
"""

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "hero_skills"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hero_skills_folder_source.json"

SLOTS = ("q", "w", "e", "r")
BASE_HEROES = ("kaizen", "grimjaw", "sylara", "thorne", "vex", "zephyr")


def _source(path):
    return path.read_text(encoding="utf-8")


def _literal(node, default=None):
    try:
        return ast.literal_eval(node)
    except Exception:
        return default


def _class(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _methods(node):
    return [item.name for item in node.body if isinstance(item, ast.FunctionDef)]


def _assign(node, name):
    for item in node.body:
        if isinstance(item, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in item.targets
        ):
            return _literal(item.value)
    return None


def _call_keywords(node):
    return {kw.arg: _literal(kw.value) for kw in node.keywords if kw.arg}


def base_skill(tree):
    """`BaseSkill`: the helper API, its constants, and the cast feedback."""
    node = _class(tree, "BaseSkill")
    triggers = {}
    for item in node.body:
        if not isinstance(item, ast.FunctionDef) or not item.name.startswith("_trigger_"):
            continue
        slot = item.name.split("_")[2]
        defaults = {}
        for arg, value in zip(item.args.args[-len(item.args.defaults):], item.args.defaults):
            defaults[arg.arg] = _literal(value)
        volume = None
        for call in ast.walk(item):
            if isinstance(call, ast.Call) and getattr(call.func, "attr", "") == "_play_skill_sound":
                volume = _call_keywords(call).get("volume")
        triggers[slot] = {"shake": defaults.get("shake_amount"), "volume": volume}
    play = _class(tree, "BaseSkill")
    play_default = None
    for item in play.body:
        if isinstance(item, ast.FunctionDef) and item.name == "_play_skill_sound":
            play_default = _literal(item.args.defaults[0]) if item.args.defaults else None
    return {
        "methods": _methods(node),
        "require_target": _assign(node, "REQUIRE_TARGET"),
        "target_range_slack": _assign(node, "TARGET_RANGE_SLACK"),
        "default_visual_duration": _assign(node, "_DEFAULT_VISUAL_DURATION"),
        "class_visual_duration": _assign(node, "SKILL_VISUAL_DURATION"),
        "default_skill_range": 200,
        "play_sound_default_volume": play_default,
        "triggers": triggers,
    }


def starter_kit(tree, namespace):
    """One starter kit class: methods, visual durations, per-slot shake."""
    node = None
    for item in ast.walk(tree):
        if isinstance(item, ast.ClassDef) and item.name == namespace:
            node = item
            break
    if node is None:
        return None
    shakes = {}
    for item in node.body:
        if not isinstance(item, ast.FunctionDef):
            continue
        for call in ast.walk(item):
            if not isinstance(call, ast.Call):
                continue
            name = getattr(call.func, "attr", "")
            if not name.startswith("_trigger_") or not name.endswith("_cooldown"):
                continue
            slot = name.split("_")[2]
            shake = _call_keywords(call).get("shake_amount")
            if shake is not None:
                shakes.setdefault(slot, shake)
    return {
        "methods": _methods(node),
        "visual_duration": _assign(node, "SKILL_VISUAL_DURATION"),
        "require_target": _assign(node, "REQUIRE_TARGET"),
        "shake": {slot: shakes[slot] for slot in SLOTS if slot in shakes},
    }


def boss_hero_skills(tree):
    """`BossHeroSkills`: registry, dispatcher, per-hero visuals, fallback."""
    node = None
    for item in ast.walk(tree):
        if isinstance(item, ast.ClassDef) and item.name == "BossHeroSkills":
            node = item
            break
    registry = _assign(node, "_SKILL_REGISTRY") or {}
    casts = {}
    for item in node.body:
        if isinstance(item, ast.FunctionDef) and item.name in ("cast_%s" % s for s in SLOTS):
            slot = item.name.split("_")[1]
            for call in ast.walk(item):
                if isinstance(call, ast.Call) and getattr(call.func, "attr", "") == "_generic_cast":
                    casts[slot] = _call_keywords(call).get("shake_amount")
    generic = None
    fallback = None
    for item in node.body:
        if not isinstance(item, ast.FunctionDef):
            continue
        if item.name == "_generic_cast":
            generic = item
        elif item.name == "_fallback_cast":
            fallback = item
    cast_range_floor = None
    if generic is not None:
        for call in ast.walk(generic):
            if isinstance(call, ast.Call) and getattr(call.func, "id", "") == "max":
                literals = [_literal(arg) for arg in call.args]
                if literals and literals[-1] is not None:
                    cast_range_floor = literals[-1]
    fallback_data = {}
    if fallback is not None:
        for assign in ast.walk(fallback):
            if not isinstance(assign, ast.Assign):
                continue
            target = getattr(assign.targets[0], "id", "")
            if target == "mult":
                # `{"q": 1.0, ...}.get(skill_key, 1.0)` - keep the dict only.
                for node_ in ast.walk(assign.value):
                    if isinstance(node_, ast.Dict):
                        fallback_data["multipliers"] = _literal(node_)
                        break
            elif target == "aoe_range":
                # `150 if skill_key == "e" else 200` - keep both radii in order.
                numbers = [
                    _literal(node_) for node_ in ast.walk(assign.value)
                    if isinstance(node_, ast.Constant) and isinstance(node_.value, int)
                ]
                fallback_data["aoe_range"] = numbers
        for number in ast.walk(fallback):
            if (
                isinstance(number, ast.Assign)
                and getattr(number.targets[0], "attr", "") == "active_skill_timer"
                and isinstance(number.value, ast.Constant)
            ):
                fallback_data["visual_duration"] = number.value.value
    return {
        "methods": _methods(node),
        "registry": {boss: dict(recipes) for boss, recipes in registry.items()},
        "visual_overrides": _assign(node, "BOSS_HERO_VISUAL_DURATION"),
        "cast_shake": {slot: casts[slot] for slot in SLOTS if slot in casts},
        "cast_range_floor": cast_range_floor,
        "fallback": fallback_data,
    }


def handler_registry(tree):
    """`__init__.py`: the handler API, aliases and the auto-register loop."""
    aliases = _assign(tree, "_EXTRA") or {}
    plain = _assign(tree, "_PLAIN_SYMS") or {}
    base_modules = _assign(tree, "_BASE_HERO_MODULES") or []
    text = _source(SKILLS / "__init__.py")
    return {
        "functions": [
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        ],
        "aliased_submodules": sorted(aliases),
        "aliased_symbols": {name: sorted(symbols) for name, symbols in aliases.items()},
        "plain_submodules": sorted(plain),
        "registered_starters": [entry[0] for entry in base_modules],
        "registered_classes": [entry[2] for entry in base_modules],
        "auto_registers_every_boss_type": "from bosses.boss_data import" in text
        and "register_handler(boss_type, BossHeroSkills)" in text,
        "keeps_legacy_import_paths": "_install_aliases()" in text,
    }


def source_fixture():
    bundle = ast.parse(_source(SKILLS / "_bundle.py"))
    init = ast.parse(_source(SKILLS / "__init__.py"))
    base = base_skill(bundle)
    boss = boss_hero_skills(bundle)
    starters = {}
    for hero in BASE_HEROES:
        namespace = "_NS_%s_skills" % hero
        class_name = "%sSkills" % hero.capitalize()
        kit = starter_kit(bundle, class_name)
        assert kit is not None, "missing %s in _bundle.py" % class_name
        kit["namespace"] = namespace
        starters[hero] = kit

    registry = boss["registry"]
    cast_methods = sorted({name for recipes in registry.values() for name in recipes.values()})
    for recipes in registry.values():
        assert sorted(recipes) == sorted(SLOTS), "registry entry without all four slots"
    for name in cast_methods:
        assert name in boss["methods"], "registry names a missing method: %s" % name

    files = {
        path.name: len(_source(path).splitlines())
        for path in sorted(SKILLS.glob("*.py"))
    }
    return {
        "source": "hero_skills/ (Pygame, read-only oracle)",
        "files": files,
        "counts": {
            "files": len(files),
            "base_skill_methods": len(base["methods"]),
            "bundle_classes": len(
                [n for n in ast.walk(bundle) if isinstance(n, ast.ClassDef)]
            ),
            "boss_hero_methods": len(boss["methods"]),
            "registry_bosses": len(registry),
            "registry_casts": len(cast_methods),
            "starter_kits": len(starters),
            "starter_methods": sum(len(kit["methods"]) for kit in starters.values()),
        },
        "base_skill": base,
        "boss_hero_skills": boss,
        "starter_kits": starters,
        "handler_registry": handler_registry(init),
    }


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="rewrite the fixture")
    args = parser.parse_args(argv)
    fixture = source_fixture()
    if args.write:
        FIXTURE.write_text(json.dumps(fixture, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print("wrote %s" % FIXTURE)
    counts = fixture["counts"]
    print(
        "files %(files)d base_skill %(base_skill_methods)d methods boss_hero %(boss_hero_methods)d "
        "registry %(registry_bosses)d bosses / %(registry_casts)d casts starters %(starter_kits)d "
        "(%(starter_methods)d methods)" % counts
    )
    if FIXTURE.is_file():
        on_disk = json.loads(FIXTURE.read_text(encoding="utf-8"))
        if on_disk != fixture:
            print("fixture drift: rerun with --write", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
