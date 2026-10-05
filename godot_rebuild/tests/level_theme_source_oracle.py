"""Read-only AST parity of source MapRenderer terrain colors for 54 themes."""
import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from level_catalog_source_oracle import source_levels

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "map_components/_bundle.py"
OUTPUT = ROOT / "godot_rebuild/data/levels/theme_palette.json"
RIVER_OUTPUT = ROOT / "godot_rebuild/data/levels/river_path.json"
KEYS = ("radiant_grass_1", "radiant_grass_2", "dire_earth_1", "dire_earth_2",
        "transition_1", "path_stone_1", "path_stone_3", "river_deep", "river_mid",
        "river_light", "river_glow", "river_foam")


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


def source_river():
    module = ast.parse(SOURCE.read_text(encoding="utf-8"))
    generator = next(node for node in ast.walk(module)
                     if isinstance(node, ast.ClassDef) and node.name == "PathGenerator")
    env = {"_NS_generators": SimpleNamespace()}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[generator], type_ignores=[])),
                 "<source PathGenerator>", "exec"), env)
    env["_NS_generators"].PathGenerator = env["PathGenerator"]
    result = [list(point) for point in env["PathGenerator"].generate_river(1280, 720)]
    assert len(result) == 61 and result[0] == [0, 200] and result[-1] == [1280, 520]
    return result


def check(write=False):
    expected = source_palettes()
    river = source_river()
    if write:
        OUTPUT.write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
        RIVER_OUTPUT.write_text(json.dumps(river, indent=2) + "\n", encoding="utf-8")
    assert json.loads(OUTPUT.read_text(encoding="utf-8")) == expected, "Map theme palette drift"
    assert json.loads(RIVER_OUTPUT.read_text(encoding="utf-8")) == river, "River geometry drift"
    return len(expected)


if __name__ == "__main__":
    print(f"PASS: {check('--write' in sys.argv)} source terrain palettes")
