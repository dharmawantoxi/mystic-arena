#!/usr/bin/env python3
"""Read-only oracle for importing a Pygame slot file into the Godot save layer.

Two halves are locked here:

* what the real ``_system.py::SaveManager`` makes of a slot file — the backfilled
  defaults from ``load()``, the slot card from ``get_slot_info()``, and the fact
  that a corrupt file silently falls back to an empty profile;
* what the Godot import must produce from those values, because the Godot save
  envelope is stricter than the Python dictionary (known hero IDs, boss flag on
  unlocked bosses, levels 1-54, exact ``LevelStats`` entries).

The fixture is the contract ``scripts/match/pygame_save_import.gd`` is checked
against in ``tests/pygame_save_import_checks.gd``. Nothing here writes to a real
save directory, and the Pygame sources are only read.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import save_slot_source_oracle as harness  # noqa: E402  (sibling oracle harness)

ROOT = harness.ROOT
FIXTURE = Path(__file__).with_name("fixtures") / "pygame_save_import_source.json"
HERO_DIR = ROOT / "godot_rebuild" / "data" / "heroes"
ARENA_JSON = ROOT / "hero_archetypes.json"
MAX_LEVEL = 54
DIFFICULTIES = ("normal", "hard")
STATS_FIELDS = (
    "best_score",
    "best_time_seconds",
    "total_attempts",
    "wins",
    "total_kills",
    "max_combo",
    "total_playtime_seconds",
)


def roster():
    """Godot hero roster: known IDs plus the native boss flag from the data."""
    heroes, bosses = set(), set()
    for path in sorted(HERO_DIR.glob("*.tres")):
        text = path.read_text(encoding="utf-8")
        hero_id = path.stem
        heroes.add(hero_id)
        if "is_boss_hero = true" in text:
            bosses.add(hero_id)
    return heroes, bosses


def as_int(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer() and abs(value) <= 2**53:
        return int(value)
    return None


def levels(value, report):
    if not isinstance(value, list):
        return []
    result, seen = [], set()
    for raw in value:
        number = as_int(raw)
        if number is None or not 1 <= number <= MAX_LEVEL:
            report["dropped_levels"].append(raw)
            continue
        if number in seen:
            report["dropped_duplicates"].append(f"level:{number}")
            continue
        seen.add(number)
        result.append(number)
    return result


def heroes(value, boss_only, known, bosses, report):
    if not isinstance(value, list):
        return []
    result, seen = [], set()
    bucket = report["dropped_bosses"] if boss_only else report["dropped_heroes"]
    for raw in value:
        if not isinstance(raw, str) or raw not in known or (boss_only and raw not in bosses):
            bucket.append(raw)
            continue
        if raw in seen:
            report["dropped_duplicates"].append(f"hero:{raw}")
            continue
        seen.add(raw)
        result.append(raw)
    return result


def stats_entry(entry):
    if not isinstance(entry, dict):
        return None
    converted = {}
    for field in STATS_FIELDS:
        number = as_int(entry.get(field, 0))
        if number is None or number < 0:
            return None
        converted[field] = number
    if converted["wins"] > converted["total_attempts"]:
        return None
    return converted


def level_stats(value, report):
    if not isinstance(value, dict):
        return {}
    result = {}
    for raw_key, entry in value.items():
        key = str(raw_key)
        if not key.isdigit() or str(int(key)) != key:
            report["dropped_level_stats"].append(key)
            continue
        if not 1 <= int(key) <= MAX_LEVEL:
            report["dropped_level_stats"].append(key)
            continue
        converted = stats_entry(entry)
        if converted is None:
            report["dropped_level_stats"].append(key)
            continue
        result[key] = converted
    return result


def last_level(value, report):
    number = as_int(value)
    if number is None:
        report["clamped_last_level"] = 1
        return 1
    if number < 1:
        report["clamped_last_level"] = number
        return 1
    if number > MAX_LEVEL:
        report["clamped_last_level"] = number
        return MAX_LEVEL
    return number


def timestamp(value, now):
    if isinstance(value, bool):
        return now
    if isinstance(value, (int, float)) and value >= 0:
        return float(value)
    return now


def difficulty(value, report):
    if value is None:
        return None
    if isinstance(value, str) and value in DIFFICULTIES:
        return value
    report["rejected_difficulty"] = str(value)
    return None


def expected(loaded, now, known, bosses):
    report = {
        "dropped_heroes": [],
        "dropped_bosses": [],
        "dropped_levels": [],
        "dropped_level_stats": [],
        "dropped_duplicates": [],
        "rejected_difficulty": "",
        "clamped_last_level": 0,
    }
    gold = as_int(loaded.get("meta_gold"))
    if gold is None or gold < 0:
        return {"ok": False, "reason": "corrupt_meta_gold", "state": None, "report": None}
    state = {
        "meta_gold": gold,
        "completed_levels": levels(loaded.get("completed_levels"), report),
        "purchased_heroes": heroes(
            loaded.get("purchased_heroes"), False, known, bosses, report
        ),
        "unlocked_bosses": heroes(
            loaded.get("unlocked_bosses"), True, known, bosses, report
        ),
        "level_stats": level_stats(loaded.get("level_stats"), report),
        "last_played_level": last_level(loaded.get("last_played_level"), report),
        "slot_created": timestamp(loaded.get("slot_created"), now),
        "slot_last_played": timestamp(loaded.get("slot_last_played"), now),
        "slot_playtime_seconds": int(loaded.get("slot_playtime_seconds") or 0),
        "run_difficulty": difficulty(loaded.get("run_difficulty"), report),
        "replay_reward_counts": {},
        "import_source": "pygame",
    }
    return {"ok": True, "reason": "", "state": state, "report": report}


FULL_STATS = {
    "3": {
        "best_score": 1820,
        "best_time_seconds": 143,
        "total_attempts": 4,
        "wins": 2,
        "total_kills": 61,
        "max_combo": 19,
        "total_playtime_seconds": 905,
    }
}

CASES = [
    {
        "name": "full",
        "note": "Pygame save written by SaveManager.save (all documented keys)",
        "text": {
            "meta_gold": 7250,
            "completed_levels": [1, 2, 4],
            "last_played_level": 4,
            "purchased_heroes": ["kaizen", "thorne"],
            "unlocked_bosses": ["gornak"],
            "level_stats": FULL_STATS,
            "slot_created": 1_699_000_000.0,
            "slot_last_played": 1_699_500_000.0,
            "slot_playtime_seconds": 3665,
            "run_difficulty": "hard",
        },
    },
    {
        "name": "legacy_minimal",
        "note": "old save before slot metadata existed: load() backfills the rest",
        "text": {"meta_gold": 410, "completed_levels": [1], "last_played_level": 1},
    },
    {
        "name": "float_numbers",
        "note": "integers stored as floats by a JSON round-trip",
        "text": {
            "meta_gold": 900.0,
            "completed_levels": [1.0, 2.0],
            "last_played_level": 2.0,
            "purchased_heroes": ["kaizen"],
            "unlocked_bosses": [],
            "slot_playtime_seconds": 61.0,
        },
    },
    {
        "name": "unknown_heroes",
        "note": "unknown ID, duplicated ID and a non-string in the hero lists",
        "text": {
            "meta_gold": 100,
            "completed_levels": [],
            "last_played_level": 1,
            "purchased_heroes": ["kaizen", "ghost_hero", "kaizen", 42],
            "unlocked_bosses": ["gornak", "kaizen", "gornak"],
        },
    },
    {
        "name": "level_bounds",
        "note": "levels outside 1-54, duplicates, and an out-of-range cursor",
        "text": {
            "meta_gold": 10,
            "completed_levels": [0, 1, 55, 54, 3, 3],
            "last_played_level": 99,
        },
    },
    {
        "name": "broken_stats",
        "note": "level_stats with wrong keys, a bad level number and wins > attempts",
        "text": {
            "meta_gold": 20,
            "completed_levels": [3, 4],
            "last_played_level": 4,
            "level_stats": {
                "3": FULL_STATS["3"],
                "4": {"best_score": 5},
                "abc": FULL_STATS["3"],
                "55": FULL_STATS["3"],
                "5": {
                    "best_score": 1,
                    "best_time_seconds": 1,
                    "total_attempts": 1,
                    "wins": 2,
                    "total_kills": 1,
                    "max_combo": 1,
                    "total_playtime_seconds": 1,
                },
            },
        },
        "probe_stats_level": 4,
    },
    {
        "name": "bad_difficulty",
        "note": "run_difficulty outside the native difficulty list",
        "text": {
            "meta_gold": 30,
            "completed_levels": [1],
            "last_played_level": 1,
            "run_difficulty": "nightmare",
        },
    },
    {
        "name": "negative_gold",
        "note": "negative currency: the native envelope refuses the whole file",
        "text": {"meta_gold": -5, "completed_levels": [1], "last_played_level": 1},
    },
    {
        "name": "string_gold",
        "note": "non-numeric currency",
        "text": {"meta_gold": "7250", "completed_levels": [1], "last_played_level": 1},
    },
    {
        "name": "corrupt_json",
        "note": "truncated file: source load() silently returns an empty profile",
        "text": '{"meta_gold": 12, "completed_levels": [1,',
    },
    {
        "name": "list_json",
        "note": "valid JSON but not an object: source load() falls back to empty",
        "text": "[1, 2, 3]",
    },
]


def probe():
    known, bosses = roster()
    arena_ids = set(
        json.loads(ARENA_JSON.read_text(encoding="utf-8"))["heroes"]
    )
    assert known == arena_ids, "Godot hero roster drifted from hero_archetypes.json"
    clock = harness.Clock()
    cloud = harness.CloudProbe()
    cases = []
    with (
        tempfile.TemporaryDirectory(prefix="mystic-pygame-import-oracle-") as directory,
        harness._isolated_cloud_module(cloud),
    ):
        save_dir = Path(directory)
        manager = harness._source_manager(save_dir, clock, cloud)
        target = save_dir / "slot_1.json"
        for case in CASES:
            raw = case["text"]
            text = raw if isinstance(raw, str) else json.dumps(raw)
            target.write_text(text, encoding="utf-8")
            parsed = None
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                pass
            loaded = manager.load(1)
            info = manager.get_slot_info(1)
            record = {
                "name": case["name"],
                "note": case["note"],
                "raw_text": text,
                "parsed": parsed,
                "source_loaded": loaded,
                "source_slot_info": info,
                "expected": (
                    expected(parsed, clock.now, known, bosses)
                    if isinstance(parsed, dict)
                    else {"ok": False, "reason": "not_a_save", "state": None, "report": None}
                ),
            }
            if "probe_stats_level" in case:
                record["source_level_stats"] = manager.get_level_stats(
                    loaded, case["probe_stats_level"]
                )
            cases.append(record)
        target.unlink()
        legacy = {
            "meta_gold": 99,
            "completed_levels": [1],
            "last_played_level": 1,
            "purchased_heroes": ["kaizen"],
            "unlocked_bosses": [],
        }
        (save_dir / "progress.json").write_text(json.dumps(legacy), encoding="utf-8")
        migrated = manager.migrate_legacy_save()
        migration_state = manager.load(1)
    return harness._json_value(
        {
            "policy": {
                "clock": clock.now,
                "slot_count": 3,
                "max_level": MAX_LEVEL,
                "difficulties": list(DIFFICULTIES),
                "stats_fields": list(STATS_FIELDS),
                "roster_size": len(known),
                "boss_flag_count": len(bosses),
                "replay_reward_counts_in_source": False,
                "backfill_keys": sorted(
                    {"unlocked_bosses", "purchased_heroes", "meta_gold", "completed_levels",
                     "last_played_level", "slot_created", "slot_last_played",
                     "slot_playtime_seconds", "level_stats", "run_difficulty"}
                ),
            },
            "cases": cases,
            "migration": {
                "migrated": migrated,
                "state": migration_state,
                "can_import_after_migration": True,
            },
        }
    )


def main():
    actual = probe()
    if "--write" in sys.argv:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    else:
        expected_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        if actual != expected_fixture:
            raise SystemExit("FAIL: Pygame save-import source fixture drift")
    print(
        "PASS: Pygame save import — "
        f"{len(actual['cases'])} slot files, backfill, slot card, sanitising"
    )


if __name__ == "__main__":
    main()
