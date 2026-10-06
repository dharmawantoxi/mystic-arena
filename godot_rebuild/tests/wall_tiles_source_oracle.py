"""Capture source StaticRenderer.draw_border_wall commands without pygame."""
import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "map_components/_bundle.py"
FIXTURE = ROOT / "godot_rebuild/data/levels/wall_tiles.json"
COLORS = ((12, 8, 12), (55, 55, 65), (95, 95, 105), (135, 135, 145), (175, 175, 185))


def source_commands():
    module = ast.parse(SOURCE.read_text(encoding="utf-8"))
    renderer = next(n for n in ast.walk(module) if isinstance(n, ast.ClassDef) and n.name == "StaticRenderer")
    renderer.body = [n for n in renderer.body if isinstance(n, ast.FunctionDef) and n.name in
                     ("draw_border_wall", "_draw_dark_stone_block", "_draw_wall_spike")]
    assignments = {
        target.id: ast.literal_eval(node.value)
        for node in module.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name) and target.id in ("TILE_SIZE", "OUTLINE")
    }
    assert assignments == {"TILE_SIZE": 16, "OUTLINE": COLORS[0]}
    result = []

    def rect(_surface, color, bounds):
        result.append([0, COLORS.index(tuple(color)), *bounds])

    def polygon(_surface, color, points):
        assert len(points) == 3
        result.append([1, COLORS.index(tuple(color)), *points[0], *points[1], *points[2]])

    def line(_surface, color, start, end, width=1):
        assert width == 1 and start[0] == end[0]
        result.append([2, COLORS.index(tuple(color)), *start, *end, width])

    env = {"TILE_SIZE": assignments["TILE_SIZE"], "OUTLINE": assignments["OUTLINE"],
           "_NS_static_renderer": SimpleNamespace(),
           "pygame": SimpleNamespace(draw=SimpleNamespace(rect=rect, polygon=polygon, line=line))}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[renderer], type_ignores=[])),
                 "<source wall renderer>", "exec"), env)
    env["_NS_static_renderer"].StaticRenderer = env["StaticRenderer"]
    env["StaticRenderer"].draw_border_wall(None, 1280, 720, {})
    assert len(result) == 1323 and sum(row[0] == 1 for row in result) == 62
    return result


def check(write=False):
    expected = source_commands()
    if write:
        FIXTURE.write_text(json.dumps(expected, separators=(",", ":")) + "\n", encoding="utf-8")
    assert json.loads(FIXTURE.read_text(encoding="utf-8")) == expected, "Source wall tile drift"
    return len(expected)


if __name__ == "__main__":
    print(f"PASS: {check('--write' in sys.argv)} source wall commands")
