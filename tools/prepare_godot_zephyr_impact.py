#!/usr/bin/env python3
"""Execute actual Zephyr ImpactFX lifecycle/draw with semantic helper recording.

Low-level lines/arcs are recorded directly. ellipse_ring_surface and
spark_surface are replaced by descriptor surfaces (ellipse center and spark
origin), NOT rasterized Pygame helpers. No pixel/additive/rotation-cache parity
is implied. This also regression-tests both corrected radial loop variables.
"""
import argparse
import ast
import hashlib
import json
import struct
from pathlib import Path
import prepare_godot_zephyr_bolt as bolt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "heroes/zephyr_fx.py"
OUTPUT = ROOT / "godot_rebuild/tests/fixtures/zephyr_impact.json"


class Surface(bolt.Surface):
    def get_width(self):
        return 0  # semantic ellipse CENTER, not rotated bitmap bounds

    def get_height(self):
        return 0

    def set_alpha(self, alpha):
        for command in self.commands:
            command[1][3] = alpha

    def blit(self, source, pos, **kwargs):
        for command in source.commands:
            if command[0] in ("ellipse", "spark", "arc"):
                kind, color, geometry, *tail = command
                geometry = [geometry[0] + pos[0], geometry[1] + pos[1], *geometry[2:]]
                self.commands.append([kind, color.copy(), geometry, *tail])
            else:
                child = bolt.Surface()
                child.commands = [command]
                super().blit(child, pos, **kwargs)


def environment():
    draw, _ = bolt.oracle()
    env = dict(draw.__globals__)
    env["_scratch"] = lambda *_args: Surface()
    def ellipse(rx, ry, width, color, angle):
        surface = Surface()
        surface.commands.append(["ellipse", [*color, 255], [0, 0], rx, ry, width, angle])
        return surface
    def spark(size, color):
        surface = Surface()
        surface.commands.append(["spark", [*color, 255], [0, 0], size])
        return surface
    def arc(surface, color, rect, start, end, width):
        surface.commands.append(["arc", list(color), list(rect), start, end, width])
    env.update(ellipse_ring_surface=ellipse, spark_surface=spark)
    env["pygame"].Rect = lambda *args: tuple(args)
    env["pygame"].error = RuntimeError
    env["pygame"].draw.arc = arc
    tree = ast.parse(SOURCE.read_text())
    nodes = [n for n in tree.body if
             (isinstance(n, ast.ClassDef) and n.name == "ImpactFX")
             or (isinstance(n, ast.FunctionDef) and n.name in ("_mix", "_clamp_color"))]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), env)
    return env


def snapshot(impact):
    return {name: getattr(impact, name) for name in impact.__slots__}


def helpers():
    env = environment()
    tree = ast.parse(SOURCE.read_text())
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "spark_surface")
    env["_SURF_CACHE"] = {}
    env["_cache_put"] = lambda _key, surface: surface
    env["pygame"].Surface = lambda *_args: Surface()
    env["pygame"].SRCALPHA = 0
    def circle(surface, color, center, radius):
        surface.commands.append(["circle", list(color), list(center), radius])
    env["pygame"].draw.circle = circle
    exec(compile(ast.Module(body=[helper], type_ignores=[]), str(SOURCE), "exec"), env)
    sparks = []
    for size in (3, 6, 12):
        for color in (env["P"]["fx_hot"], env["P"]["gold"]):
            surface = env["spark_surface"](size, color)
            sparks.append({"size": size, "color": color, "commands": surface.commands})
    ellipse = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "ellipse_ring_surface")
    step = next(n.value for n in ellipse.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "step" for t in n.targets))
    rotations = [{"degrees": angle, "expected": eval(compile(ast.Expression(step), str(SOURCE), "eval"),
                  {"angle_deg": angle})} for angle in (-139.9, -9.9, -0.1, 0.0, 9.9, 15.4, 137.5)]
    return sparks, rotations


def build():
    env = environment()
    cases = []
    fractions = [0.0, 0.1, 0.22, 0.42, 0.55, 0.6, 0.95, 1.0]
    for position in ((100.75, 200.25), (-20.75, -10.25)):
        for angle in (0.0, 0.7, -2.4):
            for power in (0.1, 1.0, 2.8):
                for critical in (False, True):
                    args = [*position, angle, power, critical]
                    impact = env["ImpactFX"](*args)
                    initial = snapshot(impact)
                    rows = []
                    for fraction in fractions:
                        # Absolute ages avoid accumulated dt obscuring branch boundaries.
                        impact.age = impact.duration * fraction
                        impact.active = fraction < 1.0
                        surface = Surface()
                        impact.draw(surface)
                        rows.append({"age_f64": struct.pack("<d", impact.age).hex(), "fraction": fraction, "state": snapshot(impact), "commands": surface.commands})
                    impact = env["ImpactFX"](*args)
                    lifecycle = []
                    for dt in (0.0, 0.016, 0.1, 0.6):
                        result = impact.update(dt)
                        lifecycle.append({"dt": dt, "result": result, "state": snapshot(impact)})
                    cases.append({"args": args, "initial": initial, "frames": rows, "lifecycle": lifecycle})
    sparks, rotations = helpers()
    tree = ast.parse(SOURCE.read_text())
    director = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ZephyrFXDirector")
    method = next(n for n in director.body if isinstance(n, ast.FunctionDef) and n.name == "on_impact")
    guard = next(n for n in method.body if isinstance(n, ast.If))
    limit = ast.literal_eval(guard.test.comparators[0])
    return json.loads(json.dumps({"schema": 1,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "scope": "ImpactFX lifecycle, primitive commands and helper descriptors; NOT pixel/helper raster parity",
        "source_fix": "two radial loops now bind k rather than unbound i/k mismatch",
        "director_limit": limit, "cases": cases, "spark_helpers": sparks, "ellipse_rotations": rotations}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(build(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            parser.exit(1, "Zephyr impact oracle drift; regenerate fixture\n")
    else:
        OUTPUT.write_text(text)
    print("Zephyr ImpactFX lifecycle and command/descriptor Python oracle OK")


if __name__ == "__main__":
    main()
