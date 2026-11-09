#!/usr/bin/env python3
"""Execute original visual projectile AST with double Vector2 and draw recorder.

No gameplay damage, raster/blending or cross-subsystem RNG parity is claimed.
"""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import types
import prepare_godot_zephyr_particles as particles

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "heroes/zephyr_fx.py"
OUTPUT = ROOT / "godot_rebuild/tests/fixtures/zephyr_projectile.json"
CONFIG = ROOT / "godot_rebuild/data/zephyr_projectile.json"


class Vector:
    def __init__(self, x=0, y=None):
        if hasattr(x, "x"):
            x, y = x.x, x.y
        self.x, self.y = float(x), float(y or 0)

    def update(self, x, y=None):
        value = Vector(x, y)
        self.x, self.y = value.x, value.y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scale):
        return Vector(self.x * scale, self.y * scale)

    def length_squared(self):
        return self.x * self.x + self.y * self.y

    def normalize(self):
        length = math.sqrt(self.length_squared())
        return Vector(self.x / length, self.y / length)

    def scale_to_length(self, length):
        value = self.normalize() * length
        self.x, self.y = value.x, value.y

    def distance_squared_to(self, other):
        return (self - other).length_squared()


def environment():
    draw, _ = particles.bolt.oracle()
    env = dict(draw.__globals__)
    env["pygame"].Vector2 = Vector
    env["random"] = particles.RandomTape()
    def lines(surface, color, closed, points, width):
        # Preserve one polyline command: overlapping joins are not separate lines.
        surface.commands.append(["polyline", list(color), [list(p) for p in points], width])
    env["pygame"].draw.lines = lines
    env["_scratch"] = lambda *_args: Surface()
    nodes = [n for n in ast.parse(SOURCE.read_text()).body
             if isinstance(n, ast.ClassDef) and n.name in ("ZephyrProjectile", "ProjectileSystem")]
    limit = next(n for n in ast.parse(SOURCE.read_text()).body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "MAX_PROJECTILES" for t in n.targets))
    env["MAX_PROJECTILES"] = ast.literal_eval(limit.value)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), env)
    return env


class Surface(particles.bolt.Surface):
    def blit(self, source, pos, **kwargs):
        for command in source.commands:
            if command[0] == "polyline":
                self.commands.append([command[0], command[1].copy(),
                    [[p[0] + pos[0], p[1] + pos[1]] for p in command[2]], command[3]])
            else:
                child = particles.bolt.Surface()
                child.commands = [command]
                super().blit(child, pos, **kwargs)


def snapshot(projectile):
    result = {key: getattr(projectile, key) for key in (
        "speed", "damage", "lifetime", "max_lifetime", "radius", "rotation", "trail_life",
        "active", "state", "kind", "homing", "_impact_age", "_emit_acc")}
    for key in ("position", "spawn_pos", "velocity", "hit_pos"):
        value = getattr(projectile, key)
        result[key] = [value.x, value.y]
    result["trail"] = [[[v.x, v.y], age] for v, age in projectile.trail]
    return result


def manager_case():
    env = environment()
    manager = env["ProjectileSystem"](cap=2)
    actions = [["spawn", 0, 0, 100, 0], ["spawn", 0, 0, 0, 100],
               ["spawn", 0, 0, 100, 100], ["update", .01], ["update", 2.7],
               ["update", .281], ["spawn", 0, 0, 100, 0], ["clear"]]
    rows = []
    for name, *args in actions:
        result = getattr(manager, name)(*args)
        rows.append({"result": result is not None if name == "spawn" else None,
                     "states": [snapshot(p) for p in manager.projectiles]})
    return {"cap": 2, "actions": actions, "expected": rows}


def build():
    cases = []
    for name, args, connected, actions in (
        ("straight", [-20.75, 13.25, 200, 40], True,
         [{"dt": dt} for dt in (0, .016, .016, .1, .2, 2.3, .28, .001)]),
        ("zero_aim", [0, 0, 0, 0], False,
         [{"dt": dt} for dt in (.01, .01, .2, 2.4, .28, .001)]),
        ("moving_target", [0, 0, 100, 0], True,
         [{"dt": .016, "target": {"alive": True, "x": 100, "y": y, "radius": 12}} for y in (0, 30, 60, 20)]
         + [{"dt": .2, "target": {"alive": False, "x": 100, "y": 20, "radius": 12}}, {"kill": [9, -7]}, {"kill": [0, 0]}, {"dt": .28}, {"dt": .001}]),
        ("collision", [0, 0, 10, 0], True,
         [{"dt": 0, "target": {"alive": True, "x": 10, "y": 0, "radius": 12}}, {"dt": .28}, {"dt": .001}]),
        ("trail_cap", [0, 0, 100, 0], False,
         [{"dt": .001} for _ in range(20)] + [{"kill": None}, {"dt": .2}, {"dt": .081}]),
        ("custom", [-30.5, -20.5, 300, 50], True,
         [{"dt": .04}, {"dt": .1}, {"kill": None}, {"dt": .3}]),
        ("expiry_strict", [0, 0, 100, 0], False,
         [{"dt": 2.6}, {"dt": .000001}, {"dt": .28}, {"dt": .001}, {"dt": 0}]),
    ):
        env = environment()
        events, hits = [], []
        pool = types.SimpleNamespace(spawn=lambda *a, **kw: events.append({"args": a, "options": kw})) if connected else None
        options = {"speed": 180.0, "damage": 37, "radius": 3.0, "homing": 2.0, "kind": "custom"} if name == "custom" else {}
        projectile = env["ZephyrProjectile"](*args, **options, particles=pool, on_impact=lambda p: hits.append([p.hit_pos.x, p.hit_pos.y]))
        rows = []
        initial = snapshot(projectile)
        for action in actions:
            events.clear()
            hits.clear()
            if "target" in action:
                projectile.target = types.SimpleNamespace(**action["target"])
            alive = None
            if "kill" in action:
                coords = action["kill"]
                projectile.kill(*coords) if coords is not None else projectile.kill()
            else:
                alive = projectile.update(action["dt"])
            canvas = Surface()
            if projectile.active:
                projectile.draw(canvas)
            rows.append({"alive": alive, "state": snapshot(projectile), "events": list(events),
                         "hits": list(hits), "commands": canvas.commands, "random_index": env["random"].index})
        cases.append({"name": name, "args": args, "connected": connected, "actions": actions,
                      "options": options, "initial": initial, "expected": rows})
    fixture = {"schema": 1, "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
               "scope": "visual projectile lifecycle/homing/trail/emission/commands; no damage or pixels",
               "default_capacity": environment()["MAX_PROJECTILES"], "random_tape": particles.TAPE, "cases": cases, "manager": manager_case()}
    return json.loads(json.dumps(fixture)), {"capacity": environment()["MAX_PROJECTILES"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    fixture, config = build()
    for path, value in ((OUTPUT, fixture), (CONFIG, config)):
        text = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text() != text:
                parser.exit(1, f"Zephyr projectile oracle/config drift: {path}\n")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print("Zephyr visual projectile oracle OK")


if __name__ == "__main__":
    main()
