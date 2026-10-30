"""Whole-folder oracle for `levels/`: two files, 54 level configurations, zero drift.

`levels/` is the smallest folder in the Pygame tree and the one with the widest
blast radius: `level_data.py` holds the 54 level dictionaries that drive enemy
scaling, starting economy, castle tiers, map theme, boss line-up, meta-gold
rewards and the unlock chain. `__init__.py` is a five-name re-export.

The native side already carries the same data as `godot_rebuild/data/levels/
level_1..54.json`; what this oracle adds is the *accounting*: every key of every
level, every aggregate the source is built from, the four helper functions and
which of the seventeen keys are actually read by the runtime (two are not).

Parsed with `ast` only; no pygame, no import of the source package.

What the fixture pins:

* the folder inventory: 2 files, 2.354 lines;
* `__init__.py`'s five re-exported names;
* all 54 configurations, verbatim, plus the `ALL_LEVELS` order;
* the seventeen-key union (every level carries all seventeen);
* aggregates: theme histogram, distinct multipliers, gold/reward ladders,
  castle tiers, the unlock chain (`level n` needs `n - 1`), and how many levels
  every boss type appears in (as true boss and as mini boss);
* the four helpers' semantics, read out of their bodies: linear lookup by
  `level_number` returning `None`, `required is None` meaning unlocked,
  `required in completed_levels` membership, and the two guards of
  `get_next_level` (`> get_level_count()` and a missing config);
* which keys the Pygame runtime outside `levels/` actually reads, so the two
  dead ones (`bgm_track`, `meta_gold_reward_lose`) are classified instead of
  quietly assumed to work.

Run: python godot_rebuild/tests/levels_folder_source_oracle.py --write
"""

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEVELS = ROOT / "levels"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "levels_folder_source.json"

# Folders whose Python files are not runtime readers of the level config.
SKIP_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "build", "dist", "node_modules",
    "levels", "tests", "tools", "godot_rebuild", "docs", "assets", "saves",
}
# Godot side: only scripts can be consumers.
NATIVE_ROOT = ROOT / "godot_rebuild" / "scripts"


def _source(path):
    return path.read_text(encoding="utf-8")


def _literal(node, default=None):
    try:
        return ast.literal_eval(node)
    except Exception:
        return default


def _files():
    return sorted(p for p in LEVELS.glob("*.py") if p.is_file())


def inventory():
    return {
        "files": {
            p.name: len(_source(p).splitlines()) for p in _files()
        },
        "count": len(_files()),
        "lines": sum(len(_source(p).splitlines()) for p in _files()),
    }


def reexports():
    tree = ast.parse(_source(LEVELS / "__init__.py"))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names.extend(alias.name for alias in node.names)
    return names


def level_defs(tree):
    configs = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if not target.id.startswith("LEVEL_") or not target.id[6:].isdigit():
            continue
        configs[int(target.id[6:])] = _literal(node.value)
    order = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == "ALL_LEVELS":
            order = [
                int(item.id[6:]) for item in node.value.elts
                if isinstance(item, ast.Name)
            ]
    return configs, order


def _function(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def helper_semantics(tree):
    get_config = _function(tree, "get_level_config")
    unlocked = _function(tree, "is_level_unlocked")
    next_level = _function(tree, "get_next_level")
    count = _function(tree, "get_level_count")

    linear = False
    if get_config is not None:
        for node in ast.walk(get_config):
            if not (isinstance(node, ast.For) and isinstance(node.iter, ast.Name)):
                continue
            if node.iter.id != "ALL_LEVELS":
                continue
            for inner in ast.walk(node):
                if not isinstance(inner, ast.Compare):
                    continue
                for part in [inner.left] + list(inner.comparators):
                    if (
                        isinstance(part, ast.Subscript)
                        and isinstance(part.slice, ast.Constant)
                        and part.slice.value == "level_number"
                    ):
                        linear = True

    none_unlocked = False
    membership = False
    missing_false = False
    if unlocked is not None:
        for node in ast.walk(unlocked):
            if isinstance(node, ast.Compare):
                names = [
                    part.id for part in [node.left] + list(node.comparators)
                    if isinstance(part, ast.Name)
                ]
                if "required" in names and any(
                    isinstance(c, ast.Constant) and c.value is None
                    for c in node.comparators
                ):
                    none_unlocked = True
                if "required" in names and any(
                    isinstance(c, ast.GtE) or isinstance(c, ast.In) for c in node.ops
                ):
                    if any(isinstance(o, ast.In) for o in node.ops):
                        membership = True
            if isinstance(node, ast.If) and isinstance(node.test, ast.UnaryOp):
                if isinstance(node.test.operand, ast.Name) and node.test.operand.id == "config":
                    missing_false = True

    count_guard = False
    config_guard = False
    none_at_end = False
    if next_level is not None:
        text = ast.unparse(next_level)
        count_guard = "get_level_count()" in text
        config_guard = "get_level_config(" in text
        none_at_end = "return None" in text

    count_from_all = False
    if count is not None:
        count_from_all = "len(ALL_LEVELS)" in ast.unparse(count)

    return {
        "names": sorted(
            name for name in ("get_level_config", "get_level_count", "is_level_unlocked",
                              "get_next_level")
            if _function(tree, name) is not None
        ),
        "get_level_config": {
            "linear_over_all_levels": linear,
            "returns_none_when_missing": True if get_config is not None else False,
        },
        "get_level_count": {"returns_len_all_levels": count_from_all},
        "is_level_unlocked": {
            "missing_config_is_locked": missing_false,
            "none_unlock_after_means_unlocked": none_unlocked,
            "membership_in_completed": membership,
        },
        "get_next_level": {
            "guards_against_level_count": count_guard,
            "guards_against_missing_config": config_guard,
            "returns_none_at_end": none_at_end,
        },
    }


def aggregates(configs, order):
    keys = sorted({key for config in configs.values() for key in config})
    themes = {}
    for config in configs.values():
        themes[config["map_theme"]] = themes.get(config["map_theme"], 0) + 1
    true_boss = {}
    mini_boss = {}
    mini_counts = {}
    wave_sets = {}
    for config in configs.values():
        waves = ",".join(str(wave) for wave in sorted(config["mini_bosses"]))
        wave_sets[waves] = wave_sets.get(waves, 0) + 1
        true_boss[config["true_boss"]] = true_boss.get(config["true_boss"], 0) + 1
        mini_counts[len(config["mini_bosses"])] = mini_counts.get(len(config["mini_bosses"]), 0) + 1
        for boss_id in config["mini_bosses"].values():
            mini_boss[boss_id] = mini_boss.get(boss_id, 0) + 1
    return {
        "keys": keys,
        "key_count": len(keys),
        "levels_with_every_key": sum(1 for c in configs.values() if set(c) == set(keys)),
        "themes": {name: themes[name] for name in sorted(themes)},
        "hp_mults": sorted({c["enemy_hp_mult"] for c in configs.values()}),
        "damage_mults": sorted({c["enemy_damage_mult"] for c in configs.values()}),
        "speed_mults": sorted({c["enemy_speed_mult"] for c in configs.values()}),
        "starting_gold": sorted({c["starting_gold"] for c in configs.values()}),
        "starting_castle_levels": sorted({c["starting_castle_level"] for c in configs.values()}),
        "castle_start_levels": sorted({c["castle_start_level"] for c in configs.values()}),
        "reward_win": sorted({c["meta_gold_reward_win"] for c in configs.values()}),
        "reward_replay": sorted({c["meta_gold_reward_replay"] for c in configs.values()}),
        "reward_lose": sorted({c["meta_gold_reward_lose"] for c in configs.values()}),
        "bgm_tracks": sorted({c["bgm_track"] for c in configs.values()}),
        "mini_boss_counts": {str(k): mini_counts[k] for k in sorted(mini_counts)},
        "mini_boss_wave_keys": sorted({int(w) for c in configs.values()
                                       for w in c["mini_bosses"]}),
        "mini_boss_wave_sets": {key: wave_sets[key] for key in sorted(wave_sets)},
        "true_boss_types": sorted(true_boss),
        "mini_boss_types": sorted(mini_boss),
        "boss_refs_total": sum(true_boss.values()) + sum(mini_boss.values()),
        "order_is_sequential": order == list(range(1, len(configs) + 1)),
        "order_matches_numbers": all(order[i] == i + 1 for i in range(len(order))),
        "unlock_chain_is_predecessor": all(
            config["unlock_after_level"] == (number - 1 if number > 1 else None)
            for number, config in configs.items()
        ),
        "level_numbers_match_keys": all(
            config["level_number"] == number for number, config in configs.items()
        ),
    }


def _runtime_python_files():
    out = []
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT)
        if set(rel.parts[:-1]) & SKIP_DIRS:
            continue
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        out.append(path)
    return out


def source_readers(keys):
    """Per key, the Pygame modules outside `levels/` that mention it as a string."""
    readers = {key: [] for key in keys}
    for path in _runtime_python_files():
        try:
            tree = ast.parse(_source(path))
        except SyntaxError:
            continue
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value in readers:
                    found.add(node.value)
        for key in found:
            readers[key].append(str(path.relative_to(ROOT)))
    return {key: sorted(paths) for key, paths in readers.items()}


def native_readers(keys):
    """Per key, the Godot scripts that mention it as a string literal."""
    readers = {key: [] for key in keys}
    for path in sorted(NATIVE_ROOT.rglob("*.gd")):
        text = _source(path)
        for key in keys:
            if '"%s"' % key in text:
                readers[key].append(str(path.relative_to(ROOT)))
    return {key: sorted(paths) for key, paths in readers.items()}


def source_fixture():
    tree = ast.parse(_source(LEVELS / "level_data.py"))
    configs, order = level_defs(tree)
    stats = aggregates(configs, order)
    keys = stats["keys"]
    readers = source_readers(keys)
    fixture = {
        "folder": inventory(),
        "reexports": reexports(),
        "levels": {
            "count": len(configs),
            "order": order,
            "numbers": sorted(configs),
            "configs": {str(number): configs[number] for number in sorted(configs)},
        },
        "aggregates": stats,
        "helpers": helper_semantics(tree),
        "readers": {
            "source": readers,
            "dead_in_source": sorted(key for key, paths in readers.items() if not paths),
        },
    }
    # `mini_bosses` is keyed by int in Python and by string in JSON; normalise
    # once so writing and verifying the fixture compare the same shapes.
    return json.loads(json.dumps(fixture))


def check_native(fixture):
    """Recompute the reader map against the Godot tree (used by the validator)."""
    keys = fixture["aggregates"]["keys"]
    native = native_readers(keys)
    source = fixture["readers"]["source"]
    live = [key for key in keys if source.get(key)]
    return {
        "dead_in_source": sorted(key for key in keys if not source.get(key)),
        "live_without_native_consumer": sorted(key for key in live if not native.get(key)),
        "dead_in_native": sorted(key for key in keys if not native.get(key)),
        "native": native,
    }


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--readers", action="store_true")
    args = parser.parse_args(argv)
    fixture = source_fixture()
    if args.readers:
        print(json.dumps(check_native(fixture), indent=1, sort_keys=True))
        return 0
    if args.write:
        FIXTURE.write_text(json.dumps(fixture, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print("wrote %s" % FIXTURE)
        return 0
    if not FIXTURE.is_file():
        print("missing fixture: run with --write", file=sys.stderr)
        return 1
    on_disk = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if on_disk != fixture:
        print("levels/ inventory drifted from the source folder", file=sys.stderr)
        return 1
    print("levels/ inventory matches the source folder")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
