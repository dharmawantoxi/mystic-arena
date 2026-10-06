"""Static source terrain draw commands using isolated, reproducible visual RNG.

Game source seeds detail circles (100), but terrain speckles use global random.
A visual-only seed here fixes the latter without affecting Godot gameplay RNG.
"""
import ast
import json
import random
import sys
from pathlib import Path
from types import SimpleNamespace

from level_theme_source_oracle import source_palettes

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "map_components/_bundle.py"
FIXTURE = ROOT / "godot_rebuild/data/levels/terrain_tiles.json"
SEED = 20260929
KEYS = ("radiant_grass_1", "radiant_grass_2", "radiant_grass_3", "radiant_grass_4",
        "radiant_grass_high", "radiant_moss", "dire_earth_1", "dire_earth_2",
        "dire_earth_3", "dire_earth_4", "dire_ash", "dire_burnt",
        "transition_1", "transition_2")
ASH_SPECK = (60, 60, 70)


def source_commands():
    module = ast.parse(SOURCE.read_text(encoding="utf-8"))
    cls = next(n for n in ast.walk(module) if isinstance(n, ast.ClassDef) and n.name == "StaticRenderer")
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in
               ("draw_terrain", "draw_terrain_details")]
    for method in methods:
        method.decorator_list = []
    tile_size = next(ast.literal_eval(n.value) for n in module.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "TILE_SIZE" for t in n.targets))
    assert tile_size == 16
    theme = source_palettes()["forest"]
    colors = [tuple(theme[key]) for key in KEYS] + [ASH_SPECK]
    assert len(colors) == len(set(colors))
    commands = []

    def rect(_surface, color, bounds, width=0):
        assert width == 0
        commands.append([0, colors.index(tuple(color)), *bounds])

    def line(_surface, color, start, end, width=1):
        assert width == 1
        commands.append([1, colors.index(tuple(color)), *start, *end])

    def circle(_surface, color, center, radius):
        commands.append([2, colors.index(tuple(color)), *center, radius])

    env = {"TILE_SIZE": tile_size, "random": random.Random(SEED),
           "pygame": SimpleNamespace(draw=SimpleNamespace(rect=rect, line=line, circle=circle))}
    exec(compile(ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[])),
                 "<source terrain renderer>", "exec"), env)
    env["draw_terrain"](None, 1280, 720, theme)
    env["draw_terrain_details"](None, 1280, 720, theme)
    assert len(commands) > 5000 and sum(row[0] == 2 for row in commands) > 10
    return commands


def check(write=False):
    rows = source_commands()
    if write:
        FIXTURE.write_text(json.dumps(rows, separators=(",", ":")) + "\n", encoding="utf-8")
    assert json.loads(FIXTURE.read_text(encoding="utf-8")) == rows, "Source terrain drift"
    return len(rows)


if __name__ == "__main__":
    print(f"PASS: {check('--write' in sys.argv)} source terrain commands")
