#!/usr/bin/env python3
"""Prepare native SwingTrail oracle and sampled staff attachments.

Executes original SwingTrail, ZephyrFXDirector._staff_points and the minimal
staff-rig AST dependencies. No heroes package import or pygame is required.
Attachments follow the existing baked attack samples; they are not a full rig
port. Commands test geometry/order, not rasterized pixel/compositing parity.
"""
import argparse
import ast
import builtins
import copy
import hashlib
import json
import math
from pathlib import Path
import types
import prepare_godot_zephyr_bolt as bolt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "heroes/zephyr_fx.py"
BUNDLE = ROOT / "heroes/_bundle.py"
BAKER = ROOT / "tools/convert_to_godot.py"
MANIFEST = ROOT / "godot_rebuild/data/baked_units.json"
CONFIG = ROOT / "godot_rebuild/data/zephyr_trail.json"
FIXTURE = ROOT / "godot_rebuild/tests/fixtures/zephyr_trail.json"


class Vector:
    def __init__(self, x=0.0, y=None):
        if y is not None:
            self.x, self.y = float(x), float(y)
        elif isinstance(x, Vector):
            self.x, self.y = x.x, x.y
        else:
            self.x, self.y = map(float, x)

    def lerp(self, other, fraction):
        return Vector(self.x + (other.x - self.x) * fraction,
                      self.y + (other.y - self.y) * fraction)


def literal(tree, name):
    node = next(n for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
    return ast.literal_eval(node.value)


def rig():
    tree = ast.parse(BUNDLE.read_text())
    namespace = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "_NS_zephyr")
    helpers = {"_ease_in", "_ease_out", "_ease_in_out", "_staff_arc_pose", "_staff_tip_local"}
    constants = {"STAFF_PIVOT", "STAFF_R_REST", "STAFF_R_WINDUP", "STAFF_R_STRIKE", "STAFF_R_FOLLOW",
                 "ATTACK_ANTICIPATION_END", "ATTACK_WINDUP_END", "ATTACK_SWING_END", "ATTACK_IMPACT_END",
                 "ATTACK_FOLLOW_END", "ATTACK_ARC_START", "ATTACK_ARC_SWEEP", "ATTACK_ARC_END"}
    selected = []
    found = set()
    for node in namespace.body:
        if isinstance(node, ast.FunctionDef) and node.name in helpers:
            selected.append(copy.deepcopy(node))
            found.add(node.name)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in node.targets):
            ast.literal_eval(node.value)  # constants must remain closed-world literals
            selected.append(copy.deepcopy(node))
            found.update(t.id for t in node.targets if isinstance(t, ast.Name))
    if not (helpers | constants) <= found:
        raise ValueError("Missing staff rig dependency")
    reduced = copy.deepcopy(namespace)
    reduced.body = selected
    env = {"math": math}
    exec(compile(ast.Module(body=[reduced], type_ignores=[]), str(BUNDLE), "exec"), env)
    return env["_NS_zephyr"]


def environment():
    draw, colors = bolt.oracle()
    env = dict(draw.__globals__)
    env["pygame"].Vector2 = Vector
    tree = ast.parse(SOURCE.read_text())
    env["TRAIL_SAMPLES"] = literal(tree, "TRAIL_SAMPLES")
    env["ATTACK_PHASES"] = literal(tree, "ATTACK_PHASES")
    nodes = [n for n in tree.body if
             (isinstance(n, ast.ClassDef) and n.name == "SwingTrail")
             or (isinstance(n, ast.FunctionDef) and n.name == "attack_phase")]
    director = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ZephyrFXDirector")
    nodes.append(next(n for n in director.body if isinstance(n, ast.FunctionDef) and n.name == "_staff_points"))
    module = types.SimpleNamespace(_NS_zephyr=rig())
    real_import = builtins.__import__
    def source_import(name, *args, **kwargs):
        if name == "heroes._bundle":
            return module
        if name.startswith("heroes"):
            raise AssertionError("Unexpected package import in staff attachment oracle: " + name)
        return real_import(name, *args, **kwargs)
    env["__builtins__"] = dict(vars(builtins), __import__=source_import)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), env)
    return env, colors


def bake_samples():
    tree = ast.parse(BAKER.read_text())
    count = literal(tree, "UNIT_ATTACK_FRAMES")
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_bake_unit_frames")
    pulse = [n.value.value for n in function.body if isinstance(n, ast.Assign)
             and isinstance(n.value, ast.Constant)
             and any(isinstance(t, ast.Attribute) and t.attr == "pulse" for t in n.targets)]
    if len(pulse) != 1:
        raise ValueError("Attack bake phase changed; inspect attachment sampling")
    loop = next(n for n in function.body if isinstance(n, ast.For)
                and isinstance(n.iter, ast.Call) and ast.unparse(n.iter) == "range(UNIT_ATTACK_FRAMES)")
    progress = next(n.value for n in loop.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "p" for t in n.targets))
    # Execute the baker's exact expression rather than duplicating its formula.
    values = [eval(compile(ast.Expression(progress), str(BAKER), "eval"),
                   {"k": k, "UNIT_ATTACK_FRAMES": count}) for k in range(count)]
    return pulse[0], values


def state(trail):
    return {"samples": trail.samples, "life": trail.life, "width_boost": trail.width_boost,
            "color_edge": trail.color_edge, "color_core": trail.color_core, "active": trail.active,
            "points": [[[g.x, g.y], [t.x, t.y], age] for g, t, age in trail.points]}


def record(trail):
    surface = bolt.Surface()
    trail.draw(surface)
    return {"state": state(trail), "commands": surface.commands}


def build():
    env, _ = environment()
    initial = env["SwingTrail"]()
    pulse, progresses = bake_samples()
    unit = json.loads(MANIFEST.read_text())["units"]["zephyr"]
    if unit["anims"]["attack"][1] != len(progresses):
        raise ValueError("Zephyr baked pose count is stale")
    attachments = []
    for progress in progresses:
        hero = types.SimpleNamespace(x=0.0, y=0.0, facing=1, pulse=pulse,
                                     _render_scale=1.0, _zp_attack_progress=progress)
        inner, outer = env["_staff_points"](types.SimpleNamespace(hero=hero))
        phase = env["attack_phase"](progress)
        attachments.append({"inner": [inner.x, inner.y], "outer": [outer.x, outer.y],
                            "progress": progress, "phase": phase, "swinging": phase in ("SWING", "IMPACT")})
    cases = [
        {"samples": 3, "actions": [
            ["push", [0.2, 5.8], [18.9, -6.2]], ["update", 0.016],
            ["push", [3.7, 6.1], [25.3, -8.8]], ["update", 0.016],
            ["push", [-4.2, 2.5], [24.9, -2.1]], ["push", [-6.5, 0.5], [20.1, 8.2]],
            ["width_boost", 1.7], ["update", 0.23], ["update", 0.03], ["reset"]]},
        {"samples": 7, "actions": [
            ["push", [-20.2, -10.8], [-10.3, 2.7]], ["push", [-20.2, -10.8], [-10.3, 2.7]],
            ["update", 0.25], ["update", 0.01], ["reset"]]},
        {"samples": 7, "actions": [
            ["push", [0, 0], [2, 2]], ["push", [1386, 0], [1388, 2]],
            ["push", [1600, 0], [1602, 2]], ["reset"],
            ["push", [0, 0], [2, 2]], ["push", [3, 1], [5, 3]], ["update", 0.26]]},
        {"samples": 0, "actions": [["push", [1, 2], [3, 4]], ["update", 0.0], ["reset"]]},
    ]
    for case in cases:
        trail = env["SwingTrail"](case["samples"])
        case["expected"] = []
        for action, *args in case["actions"]:
            if action == "width_boost":
                trail.width_boost = args[0]
            else:
                getattr(trail, action)(*args)
            case["expected"].append(record(trail))
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (SOURCE, BUNDLE, BAKER, MANIFEST)}
    config = {"schema": 1, "sources": hashes, "hero_scale": unit["hero_scale"], "bake_pulse": pulse,
              "defaults": state(initial), "attachments": attachments}
    world = []
    for facing in (-1, 1):
        for scale in (1.0, unit["hero_scale"]):
            for index, progress in enumerate(progresses):
                hero = types.SimpleNamespace(x=100.25, y=-20.5, facing=facing, pulse=pulse,
                                             _render_scale=scale, _zp_attack_progress=progress)
                inner, outer = env["_staff_points"](types.SimpleNamespace(hero=hero))
                world.append({"index": index, "position": [hero.x, hero.y], "facing": facing, "scale": scale,
                              "inner": [inner.x, inner.y], "outer": [outer.x, outer.y]})
    fixture = {"schema": 1, "sources": hashes, "cases": cases, "world_attachments": world,
               "scope": "sampled attachments and trail geometry/lifecycle, not full rig or pixel parity"}
    return json.loads(json.dumps(config)), json.loads(json.dumps(fixture))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    config, fixture = build()
    for path, value in ((CONFIG, config), (FIXTURE, fixture)):
        text = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text() != text:
                parser.exit(1, f"Zephyr trail artifact drift: {path}\n")
        else:
            path.write_text(text)
    print("Zephyr trail geometry and staff attachments Python oracle OK")


if __name__ == "__main__":
    main()
