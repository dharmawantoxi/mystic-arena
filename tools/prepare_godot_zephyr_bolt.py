#!/usr/bin/env python3
"""Record original Zephyr draw_bolt geometry without importing pygame.

Executes the actual function AST, replacing only pygame draw/surface calls by a
command recorder. This is a geometry/order oracle, NOT a pixel/blending oracle.
"""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "heroes/zephyr_fx.py"
OUTPUT = ROOT / "godot_rebuild/tests/fixtures/zephyr_bolt.json"
PALETTE = ROOT / "godot_rebuild/data/zephyr_palette.json"


class Surface:
    def __init__(self):
        self.commands = []

    def blit(self, source, pos, **_kwargs):
        for command in source.commands:
            kind, color, *args = command
            if kind == "polygon":
                args[0] = [[x + pos[0], y + pos[1]] for x, y in args[0]]
            elif kind == "line":
                args[:2] = [[p[0] + pos[0], p[1] + pos[1]] for p in args[:2]]
            elif kind in ("rect", "glow"):
                args[0] = [args[0][0] + pos[0], args[0][1] + pos[1], *args[0][2:]]
            else:
                raise ValueError(kind)
            self.commands.append([kind, color, *args])


def palette(tree):
    node = next(n for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "ZEPHYR_PALETTE" for t in n.targets))
    return ast.literal_eval(node.value)


def oracle():
    tree = ast.parse(SOURCE.read_text())
    colors = palette(tree)
    def rgba(color):
        return list(color) if len(color) == 4 else [*color, 255]
    def polygon(surface, color, points):
        surface.commands.append(["polygon", rgba(color), [list(p) for p in points]])
    def line(surface, color, start, end, width):
        surface.commands.append(["line", rgba(color), list(start), list(end), width])
    def rect(surface, color, box):
        surface.commands.append(["rect", rgba(color), list(box)])
    def glow(radius, color, power):
        surface = Surface()
        surface.commands.append(["glow", rgba(color), [0, 0], radius, power])
        return surface
    env = {"math": math, "P": colors,
           "pygame": types.SimpleNamespace(draw=types.SimpleNamespace(polygon=polygon, line=line, rect=rect), BLEND_RGB_ADD=1),
           "_scratch": lambda *_args: Surface(), "glow_surface": glow}
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "draw_bolt")
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), "exec"), env)
    return env["draw_bolt"], colors


def build():
    draw, colors = oracle()
    cases = []
    for x, y in ((100.75, 200.25), (-20.8, -10.2)):
        for angle in (0.0, 0.37, math.pi / 4, math.pi / 2, 2.2,
                      math.pi, -math.pi / 2, -0.37, -2.4, 5.8):
            for crit in (False, True):
                for age, radius in ((0, 6.0), (19, 4.5)):
                    surface = Surface()
                    params = dict(px=x, py=y, angle=angle, age=age, crit=crit, radius=radius)
                    draw(surface, **params)
                    cases.append({"params": params, "commands": surface.commands})
    return {"schema": 1, "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "scope": "draw command geometry and order; not pixel/additive blending parity",
            "cases": cases}, colors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    fixture, colors = build()
    for path, value in ((OUTPUT, fixture), (PALETTE, colors)):
        text = json.dumps(value, indent=2, sort_keys=True) + "\n"
        if args.check:
            if not path.exists() or path.read_text() != text:
                parser.exit(1, f"Zephyr bolt artifact drift: {path}\n")
        else:
            path.write_text(text)
    print("Zephyr bolt geometry oracle and palette OK")


if __name__ == "__main__":
    main()
