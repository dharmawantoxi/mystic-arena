"""Read-only AST oracle for the 54 source level definitions (no pygame import).

Run with --write only when intentionally refreshing native level data.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "levels/level_data.py"
DEST = ROOT / "godot_rebuild/data/levels"


def source_levels():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    levels = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.startswith("LEVEL_") and target.id[6:].isdigit():
                number = int(target.id[6:])
                value = ast.literal_eval(node.value)
                assert value["level_number"] == number, target.id
                assert number not in levels, target.id
                levels[number] = value
    assert sorted(levels) == list(range(1, 55)), "Expected 54 consecutive source levels"
    return levels


def check(write=False):
    levels = source_levels()
    bosses = json.loads((ROOT / "godot_rebuild/data/bosses/boss_stats.json").read_text(encoding="utf-8"))["bosses"]
    for number, source in levels.items():
        for boss_id in [source["true_boss"], *source["mini_bosses"].values()]:
            assert boss_id in bosses, f"Level {number} references missing native boss {boss_id}"
        path = DEST / f"level_{number}.json"
        if write:
            path.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        assert path.is_file(), f"Missing native catalog entry: {path}"
        native = json.loads(path.read_text(encoding="utf-8"))
        # JSON turns Python integer mini-boss wave keys into strings.
        assert native == json.loads(json.dumps(source)), f"Source level {number} drifted"
        assert native["unlock_after_level"] == (number - 1 if number > 1 else None), number
    assert {p.name for p in DEST.glob("level_*.json")} == {
        f"level_{number}.json" for number in levels
    }, "Unexpected native level entry"
    return len(levels)


if __name__ == "__main__":
    print(f"PASS: {check('--write' in sys.argv)} level catalog entries match source")
