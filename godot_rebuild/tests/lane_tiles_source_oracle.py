"""Capture source three-lane cobblestone/border commands without Pygame."""
import ast
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

from check_source_contract import source_lanes
from level_theme_source_oracle import source_palettes

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "map_components/_bundle.py"
FIXTURE = ROOT / "godot_rebuild/data/levels/lane_tiles.json"
COLORS = ("path_stone_1", "path_stone_2", "path_stone_3", "path_stone_4",
          "path_moss", "path_crack", "radiant_moss")
STONES = ((12, 8, 12), (55, 55, 65), (95, 95, 105), (135, 135, 145), (175, 175, 185))


def source_commands():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    renderer = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "StaticRenderer")
    renderer.body = [n for n in renderer.body if isinstance(n, ast.FunctionDef) and n.name in
                     ("draw_lane", "_draw_cobblestone_tile", "_draw_lane_border_stone")]
    assignments = {
        target.id: ast.literal_eval(node.value)
        for node in tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name) and target.id in ("TILE_SIZE", "OUTLINE")
    }
    assert assignments == {"TILE_SIZE": 16, "OUTLINE": STONES[0]}
    theme = source_palettes()["forest"]
    colors = [tuple(theme[key]) for key in COLORS] + list(STONES)
    assert len(set(colors)) == len(colors)
    commands = []

    def rect(_surface, color, bounds, width=0):
        commands.append([colors.index(tuple(color)), *bounds, width])

    def line(_surface, color, start, end, width=1):
        assert width == 1
        commands.append([colors.index(tuple(color)), *start, *end, -1])

    env = {"math": math, "TILE_SIZE": assignments["TILE_SIZE"],
           "OUTLINE": assignments["OUTLINE"], "_NS_static_renderer": SimpleNamespace(),
           "pygame": SimpleNamespace(draw=SimpleNamespace(rect=rect, line=line))}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[renderer], type_ignores=[])),
                 "<source lane renderer>", "exec"), env)
    env["_NS_static_renderer"].StaticRenderer = env["StaticRenderer"]
    for path in source_lanes().values():
        env["StaticRenderer"].draw_lane(None, path, 1280, 720, theme)
    assert len(commands) == 6654 and sum(row[5] == -1 for row in commands) == 127
    return commands


def check(write=False):
    commands = source_commands()
    if write:
        FIXTURE.write_text(json.dumps(commands, separators=(",", ":")) + "\n", encoding="utf-8")
    assert json.loads(FIXTURE.read_text(encoding="utf-8")) == commands, "Source lane tiles drift"
    return len(commands)


if __name__ == "__main__":
    print(f"PASS: {check('--write' in sys.argv)} source lane draw commands")
