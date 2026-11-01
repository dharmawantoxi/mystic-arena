#!/usr/bin/env python3
"""Export hero_archetypes.py to the active Godot project (pure Python, no pygame).

The committed analyzer output is authoritative: this tool never reclassifies a
hero or recalibrates a boss. It validates catalog coverage, writes the runtime
contract, and writes an independent Python-oracle fixture for the GDScript
suite. --check compares exact bytes and writes nothing.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
SOURCE = ROOT / "hero_archetypes.py"
CONTRACT = PROJECT / "data/hero_archetypes.json"
FIXTURE = PROJECT / "tests/fixtures/hero_archetypes_parity.json"


def source_module():
    spec = importlib.util.spec_from_file_location("mystic_archetype_export", SOURCE)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate(contract: dict, core: dict) -> None:
    heroes = core.get("heroes", {})
    bosses = {key: kind for kind in ("mini", "true") for key in core.get("bosses", {}).get(kind, {})}
    if not heroes or not bosses:
        raise AssertionError("Empty core catalog; run tools/prepare_godot_core.py first")
    missing_heroes = sorted(set(heroes) - set(contract["archetypes"]))
    extra_heroes = sorted(set(contract["archetypes"]) - set(heroes))
    missing_bosses = sorted(set(bosses) - set(contract["boss_resistances"]))
    extra_bosses = sorted(set(contract["boss_resistances"]) - set(bosses))
    if missing_heroes or extra_heroes or missing_bosses or extra_bosses:
        raise AssertionError(
            f"Archetype coverage mismatch: missing heroes={missing_heroes}, "
            f"extra heroes={extra_heroes}, missing bosses={missing_bosses}, "
            f"extra bosses={extra_bosses}"
        )
    for key, row in contract["archetypes"].items():
        if set(row) != {"dmg_type", "playstyle", "tier", "power"}:
            raise AssertionError(f"Unexpected archetype fields for {key}: {sorted(row)}")
        if row["dmg_type"] not in ("PHYSICAL", "MAGIC") or row["playstyle"] not in ("FIGHTER", "TANK", "CARRY"):
            raise AssertionError(f"Invalid school/playstyle for {key}")
        if not isinstance(row["tier"], str) or not isinstance(row["power"], int) or row["power"] < 0:
            raise AssertionError(f"Invalid tier/power for {key}")
    for key, row in contract["boss_resistances"].items():
        if set(row) != {"armor", "magic_resist", "profile", "boss_class"}:
            raise AssertionError(f"Unexpected resistance fields for {key}: {sorted(row)}")
        if row["boss_class"] != bosses[key] or row["profile"] not in contract["boss_resist_profile_mods"]:
            raise AssertionError(f"Invalid boss class/profile for {key}")
        if not isinstance(row["armor"], int) or not 0 <= row["armor"] <= contract["armor_max"]:
            raise AssertionError(f"Invalid armor for {key}")
        if not _number(row["magic_resist"]) or not 0 <= row["magic_resist"] <= contract["mr_max"]:
            raise AssertionError(f"Invalid magic resistance for {key}")


def build_contract(module=None, core: dict | None = None) -> dict:
    module = module or source_module()
    if core is None:
        core = json.loads((PROJECT / "data/core_data.json").read_text(encoding="utf-8"))
    contract = {
        "schema": 1,
        "source": "hero_archetypes.py",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "default_dmg_type": module.DEFAULT_DMG_TYPE,
        "armor_factor": module.ARMOR_FACTOR,
        "armor_max": module.ARMOR_MAX,
        "mr_max": module.MR_MAX,
        "boss_resist_base": module.BOSS_RESIST_BASE,
        "boss_resist_profile_mods": module.BOSS_RESIST_PROFILE_MODS,
        "boss_resist_scale": module.BOSS_RESIST_SCALE,
        "boss_resist_target_ratio": module.BOSS_RESIST_TARGET_RATIO,
        "archetypes": copy.deepcopy(module.ARCHETYPES),
        "boss_resistances": copy.deepcopy(module.BOSS_RESISTANCES),
    }
    # JSON has arrays, not Python tuples; normalize before validation/serialization.
    contract = json.loads(json.dumps(contract, ensure_ascii=False, allow_nan=False))
    validate(contract, core)
    return contract


def _profile_cases(module) -> list[dict]:
    cases = []
    for boss_class in ("mini", "true"):
        scale = module.BOSS_RESIST_SCALE[boss_class]
        for profile in module.BOSS_RESIST_PROFILE_MODS:
            cases.append({"profile": profile, "boss_class": boss_class,
                          "armor_scale": scale["armor"], "mr_scale": scale["mr"]})
    cases.extend([
        {"profile": "unknown", "boss_class": "true"},
        {"profile": "armored", "boss_class": "unknown"},
        {"profile": "armored", "boss_class": "mini", "armor_off": 100},
        {"profile": "magic", "boss_class": "true", "mr_scale": 100},
        {"profile": "soft", "boss_class": "mini", "armor_scale": 100},
        {"profile": "armored", "boss_class": "mini", "armor_off": -100},
        {"profile": "magic", "boss_class": "true", "mr_scale": -100},
        # Python round() is half-to-even, unlike Godot roundf(). Include ties.
        {"profile": "balanced", "boss_class": "mini", "armor_off": 0.5},
        {"profile": "balanced", "boss_class": "mini", "armor_off": 1.5},
        {"profile": "balanced", "boss_class": "mini", "armor_off": -11.5},
        {"profile": "balanced", "boss_class": "mini", "base": {}, "mods": {}},
        {"profile": "custom", "boss_class": "custom",
         "base": {"custom": [10, 0.1]}, "mods": {"custom": [2, 0.05]},
         "armor_scale": 1.5, "mr_scale": 2.0, "armor_off": 0.5},
    ])
    for case in cases:
        case["expected"] = list(module._resist_from_profile(
            case["profile"], case["boss_class"], base=case.get("base"),
            mods=case.get("mods"), armor_scale=case.get("armor_scale", 1.0),
            mr_scale=case.get("mr_scale", 1.0), armor_off=case.get("armor_off", 0),
        ))
    return cases


def _boss_setup(module, boss_type: str, boss_class: str, stats: dict) -> dict:
    armor, mr = module.get_boss_resistances(boss_type, boss_class)
    armor = max(0, min(module.ARMOR_MAX, int(stats.get("armor", armor))))
    mr = max(0.0, min(module.MR_MAX, float(stats.get("magic_resist", mr))))
    profile = stats.get("resist_profile") or module.BOSS_RESISTANCES.get(boss_type, {}).get("profile", "balanced")
    return {"boss_type": boss_type, "boss_class": boss_class, "stats": stats,
            "expected": {"armor": armor, "magic_resist": mr, "profile": profile}}


def build_oracle(module=None) -> dict:
    module = module or source_module()
    overrides = []
    for hero in ("kaizen", "vex", "unlisted_hero"):
        for forced in ("MAGIC", "magic", "PHYSICAL", "physical", "invalid", "", None, 0, 123):
            stats = {"dmg_type": forced, "playstyle": "CARRY"}
            overrides.append({"hero_type": hero, "stats": stats,
                              "expected": module.get_archetype(hero, stats),
                              "school": module.school_of(hero, stats)})
    fallbacks = []
    for boss_type, boss_class in (("unlisted_boss", "mini"), ("unlisted_boss", "true"),
                                  ("unlisted_boss", "unknown"), ("abaddon", "mini"),
                                  ("aelyrion", "true")):
        fallbacks.append({"boss_type": boss_type, "boss_class": boss_class,
                          "expected": list(module.get_boss_resistances(boss_type, boss_class))})
    setups = [
        _boss_setup(module, "abaddon", "true", {}),
        _boss_setup(module, "gornak", "mini", {}),
        _boss_setup(module, "abaddon", "true", {"armor": 999, "magic_resist": 0.99}),
        _boss_setup(module, "abaddon", "true", {"armor": -5, "magic_resist": -0.2}),
        _boss_setup(module, "gornak", "mini", {"armor": 7.9, "magic_resist": 0.125, "resist_profile": "custom"}),
        _boss_setup(module, "unlisted_boss", "true", {}),
        _boss_setup(module, "unlisted_boss", "unknown", {"armor": 0, "magic_resist": 0}),
    ]
    return {
        "schema": 1,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "heroes": {key: {"expected": module.get_archetype(key), "school": module.school_of(key)}
                   for key in module.ARCHETYPES},
        "hero_overrides": overrides,
        "bosses": {key: list(module.get_boss_resistances(key)) for key in module.BOSS_RESISTANCES},
        "boss_fallbacks": fallbacks,
        "profiles": _profile_cases(module),
        "boss_setups": setups,
        "mitigation": [[value, module.physical_mitigation(value)]
                       for value in (-100, -1, 0, 1, 8, 12, 18, 26, 32, 40, 100, 1000)],
    }


def _text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify tracked files; write nothing")
    args = parser.parse_args()
    try:
        module = source_module()
        contract = build_contract(module)
        oracle = build_oracle(module)
        outputs = {CONTRACT: _text(contract), FIXTURE: _text(oracle)}
        if args.check:
            stale = [str(path.relative_to(ROOT)) for path, text in outputs.items()
                     if not path.is_file() or path.read_text(encoding="utf-8") != text]
            if stale:
                parser.exit(1, "Stale archetype data: %s; run tools/prepare_godot_archetypes.py\n" % ", ".join(stale))
        else:
            for path, text in outputs.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix(path.suffix + ".tmp")
                temporary.write_text(text, encoding="utf-8")
                temporary.replace(path)
    except (AssertionError, ValueError, TypeError, KeyError, OSError, ImportError) as exc:
        parser.exit(1, f"Archetype preparation failed: {exc}\n")
    digest = hashlib.sha256(outputs[CONTRACT].encode()).hexdigest()[:12]
    print(f"{'Verified' if args.check else 'Prepared'} archetypes: {len(contract['archetypes'])} heroes, "
          f"{len(contract['boss_resistances'])} bosses; sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
