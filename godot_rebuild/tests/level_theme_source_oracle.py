"""Read-only AST parity of source MapRenderer terrain colors for 54 themes."""
import ast
import json
import sys
from pathlib import Path

from level_catalog_source_oracle import source_levels

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "map_components/_bundle.py"
OUTPUT = ROOT / "godot_rebuild/data/levels/theme_palette.json"
KEYS = ("radiant_grass_1", "radiant_grass_2", "dire_earth_1", "dire_earth_2",
        "transition_1", "path_stone_1", "path_stone_3", "river_mid", "river_light")


def source_palettes():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    assignments = {
        target.id: node.value
        for node in tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }
    registry = assignments["THEMES"]
    rows = {}
    for key, value in zip(registry.keys, registry.values):
        theme_name = ast.literal_eval(key)
        theme = ast.literal_eval(assignments[value.id])
        rows[theme_name] = {field: list(theme[field]) for field in KEYS}
        for color in rows[theme_name].values():
            assert len(color) == 3 and all(isinstance(channel, int) and 0 <= channel <= 255 for channel in color)
    assert len(rows) == 54
    assert {config["map_theme"] for config in source_levels().values()} == set(rows)
    return rows


def check(write=False):
    expected = source_palettes()
    if write:
        OUTPUT.write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    assert json.loads(OUTPUT.read_text(encoding="utf-8")) == expected, "Map theme palette drift"
    return len(expected)


if __name__ == "__main__":
    print(f"PASS: {check('--write' in sys.argv)} source terrain palettes")
