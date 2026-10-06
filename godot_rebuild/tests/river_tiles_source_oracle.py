"""Capture source StaticRenderer.draw_river rectangles without importing pygame."""
import ast
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

from level_theme_source_oracle import source_palettes, source_river

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "map_components/_bundle.py"
FIXTURE = ROOT / "godot_rebuild/data/levels/river_tiles.json"
COLORS = ("river_deep", "river_mid", "river_glow", "river_foam")
BANKS = ((55, 55, 65), (95, 95, 105), (135, 135, 145), (12, 8, 12))


def source_commands():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    renderer = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "StaticRenderer")
    method = next(n for n in renderer.body if isinstance(n, ast.FunctionDef) and n.name == "draw_river")
    method.decorator_list = []
    assignments = {
        target.id: ast.literal_eval(node.value)
        for node in tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name) and target.id in ("TILE_SIZE", "OUTLINE")
    }
    assert assignments == {"TILE_SIZE": 16, "OUTLINE": BANKS[-1]}
    theme = source_palettes()["forest"]
    colors = [tuple(theme[key]) for key in COLORS] + list(BANKS)
    commands = []

    def capture(_surface, color, rect, border=0):
        commands.append([colors.index(tuple(color)), *rect, border])

    env = {"math": math, "TILE_SIZE": assignments["TILE_SIZE"],
           "OUTLINE": assignments["OUTLINE"],
           "pygame": SimpleNamespace(draw=SimpleNamespace(rect=capture))}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
                 "<source river renderer>", "exec"), env)
    env["draw_river"](None, source_river(), 1280, 720, theme)
    assert len(commands) == 1878 and len(colors) == 8
    return commands


def check(write=False):
    commands = source_commands()
    if write:
        FIXTURE.write_text(json.dumps(commands, separators=(",", ":")) + "\n", encoding="utf-8")
    assert json.loads(FIXTURE.read_text(encoding="utf-8")) == commands, "Source river tiles drift"
    return len(commands)


if __name__ == "__main__":
    print(f"PASS: {check('--write' in sys.argv)} source river draw commands")
