#!/usr/bin/env python3
"""Execute original Zephyr Particle/ParticleSystem and impact burst methods.

Only Vector2 storage, draw surfaces and random input are replaced. The numeric
integrator, pool/budget logic, draw geometry and impact recipes are Python AST
from the actual source, not copied formulas. Not a pixel or RNG-algorithm oracle.
"""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import types
import prepare_godot_zephyr_bolt as bolt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "heroes/zephyr_fx.py"
OUTPUT = ROOT / "godot_rebuild/tests/fixtures/zephyr_particles.json"
TAPE = [0.1, 0.7, 0.25, 0.85, 0.45, 0.55, 0.05, 0.95]


class Surface(bolt.Surface):
    """Record helper requests, not rasterized/cache-backed spark bitmaps."""
    def set_alpha(self, alpha):
        for command in self.commands:
            command[1][3] = alpha

    def blit(self, source, pos, **kwargs):
        for command in source.commands:
            if command[0] == "spark":
                kind, color, origin, size = command
                self.commands.append([kind, color.copy(),
                                      [origin[0] + pos[0], origin[1] + pos[1]], size])
            else:
                child = bolt.Surface()
                child.commands = [command]
                super().blit(child, pos, **kwargs)


def spark(size, color):
    surface = Surface()
    surface.commands.append(["spark", [*color, 255], [0, 0], size])
    return surface


class Vector:
    def __init__(self):
        self.x = self.y = 0.0

    def update(self, x, y):
        self.x, self.y = float(x), float(y)

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)


class RandomTape:
    def __init__(self):
        self.index = 0

    def random(self):
        value = TAPE[self.index % len(TAPE)]
        self.index += 1
        return value

    def uniform(self, low, high):
        return low + (high - low) * self.random()


def environment():
    draw, _ = bolt.oracle()
    env = dict(draw.__globals__)
    env["pygame"].Vector2 = Vector
    env["spark_surface"] = spark
    tree = ast.parse(SOURCE.read_text())
    limit = next(n for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "MAX_PARTICLES" for t in n.targets))
    env["MAX_PARTICLES"] = ast.literal_eval(limit.value)
    env["random"] = RandomTape()
    budget = [1.0]
    env["particle_budget"] = lambda: budget[0]
    tree = ast.parse(SOURCE.read_text())
    nodes = [n for n in tree.body if
             (isinstance(n, ast.ClassDef) and n.name in ("Particle", "ParticleSystem"))
             or (isinstance(n, ast.FunctionDef) and n.name == "_mix")]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), env)
    return env, budget


def snapshot(particle):
    result = {name: getattr(particle, name) for name in particle.__slots__}
    for key in ("pos", "vel", "acc"):
        vector = result[key]
        result[key] = [vector.x, vector.y]
    return result


def geometry(particle):
    surface = Surface()
    if particle.active:
        particle.draw(surface)
    return surface.commands


def pool_cases():
    options = {"speed": [30, 70], "life": [0.1, 0.2], "size": [3, 5],
               "shape": "shard", "gravity": 80, "rotation_speed": [-2, 2]}
    cases = []
    for ratio in (0.0, 0.35, 0.65, 1.0):
        env, budget = environment()
        budget[0] = ratio
        pool = env["ParticleSystem"](5)
        actions = [
            ["burst", 10, 20, 8, options],
            ["spawn", 1, 2, 3, 4, 0.1, 3, [11, 22, 33], {}],
            ["update", 0.03], ["burst", 10, 20, 1, options],
            ["update", 0.5], ["budget", 1.0],
            ["spawn", 7, 8, 0, 0, 0.02, 4, [44, 55, 66], {"shape": "streak"}],
            ["clear"], ["burst", -2, -4, 3, options], ["clear"],
        ]
        rows = []
        for name, *args in actions:
            result = None
            if name == "budget":
                budget[0] = args[0]
            elif name in ("burst", "spawn"):
                *positional, kwargs = args
                result = getattr(pool, name)(*positional, **kwargs)
                if name == "spawn":
                    result = result is not None
            else:
                getattr(pool, name)(*args)
            rows.append({"result": result, "live": [snapshot(p) for p in pool._live],
                         "commands": [geometry(p) for p in pool._live],
                         "pooled": len(pool._pool), "random_index": env["random"].index})
        cases.append({"budget": ratio, "cap": 5, "actions": actions, "expected": rows})
    return cases


def particle_cases():
    cases = []
    for shape in ("pixel", "streak", "shard", "spark", "glow", "unknown"):
        for seconds, drag in ((0.5, 2.6), (-1.0, 90.0)):
            env, _ = environment()
            options = {"shape": shape, "gravity": 480, "ax": -3.5, "ay": 2.5,
                       "drag": drag, "rotation": 0.7, "rotation_speed": -4.0,
                       "alpha": 180, "color_end": [5, 11, 17], "fade_pow": 1.3}
            args = [-20.75, 13.25, 123.5, -85.25, seconds, 7.0, [180, 240, 90]]
            particle = env["Particle"]().spawn(*args, **options)
            rows = [{"state": snapshot(particle), "commands": geometry(particle)}]
            steps = [0.0, 1 / 60, 0.005, 0.05, 0.6]
            used = []
            for dt in steps:
                used.append(dt)
                alive = particle.update(dt)
                rows.append({"state": snapshot(particle), "commands": geometry(particle)})
                if not alive:
                    break
            cases.append({"args": args, "options": options, "steps": used, "expected": rows})
    return cases


def recipes():
    env, _ = environment()
    tree = ast.parse(SOURCE.read_text())
    director = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ZephyrFXDirector")
    method = next(n for n in director.body if isinstance(n, ast.FunctionDef) and n.name == "on_impact")
    env.update(ImpactFX=lambda *a: None, shake=lambda *a: None, hit_stop=lambda *a: None)
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(SOURCE), "exec"), env)
    cases = []
    for power in (-0.4, 0.7, 1.0, 2.3):
        for critical in (False, True):
            for angle in (0.0, 0.7):
                bursts = []
                def record(x, y, count, **options):
                    bursts.append({"count": count, "options": options})
                owner = types.SimpleNamespace(impacts=[], particles=types.SimpleNamespace(burst=record))
                env["on_impact"](owner, 0.0, 0.0, angle, power, critical)
                cases.append({"power": power, "critical": critical, "angle": angle, "expected": bursts})
    return cases


def hurt_cases():
    """Execute only the original director's HP/flash prefix, not its full update."""
    env, _ = environment()
    tree = ast.parse(SOURCE.read_text())
    director = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ZephyrFXDirector")
    methods = {n.name: n for n in director.body if isinstance(n, ast.FunctionDef)}
    update = methods["update"]
    boundary = next(i for i, n in enumerate(update.body) if isinstance(n, ast.Expr)
                    and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute)
                    and n.value.func.attr == "_update_state")
    update.body = update.body[:boundary]
    exec(compile(ast.Module(body=[methods["on_hurt"], methods["_draw_hit_flash"], update],
                            type_ignores=[]), str(SOURCE), "exec"), env)
    scenarios = [
        [[100, 30.75, 50.25, 0], [90, 30.75, 50.25, 0.016],
         [90, 40.5, 60.5, 0.05], [90, 40.5, 60.5, 0.2]],
        [[100, -20.75, -10.25, 0], [99.995, -20.75, -10.25, 0.01],
         [110, -20.75, -10.25, 0.01], [90, -20.75, -10.25, 0],
         [80, -20.75, -10.25, 0.08], [0, -20.75, -10.25, 0.2]],
    ]
    cases = []
    for steps in scenarios:
        bursts = []
        def record(x, y, count, **options):
            bursts.append({"position": [x, y], "count": count, "options": options})
        hero = types.SimpleNamespace(max_hp=100)
        owner = types.SimpleNamespace(hero=hero, hit_flash=0.0, _last_hp=None,
                                      time=0.0, frames=0,
                                      particles=types.SimpleNamespace(burst=record))
        owner.on_hurt = types.MethodType(env["on_hurt"], owner)
        rows = []
        for hp, x, y, dt in steps:
            hero.hp, hero.x, hero.y = hp, x, y
            bursts.clear()
            env["update"](owner, dt)
            surface = Surface()
            if owner.hit_flash > 0.0:
                env["_draw_hit_flash"](owner, surface)
            rows.append({"hit_flash": owner.hit_flash, "bursts": list(bursts),
                         "commands": surface.commands})
        cases.append({"steps": steps, "expected": rows})
    return cases


def build():
    # JSON round-trip normalizes palette tuples just like Godot's JSON loader.
    return json.loads(json.dumps({"schema": 1, "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "scope": "motion, pool, all shape commands/helper requests and impact recipes; not pixels, blending or RNG parity",
        "default_capacity": environment()[0]["ParticleSystem"]().cap,
        "hurt": hurt_cases(), "random_tape": TAPE, "particles": particle_cases(), "pools": pool_cases(), "recipes": recipes()}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(build(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            parser.exit(1, "Zephyr particle oracle drift; regenerate fixture\n")
    else:
        OUTPUT.write_text(text)
    print("Zephyr particle/pool/impact Python oracle OK")


if __name__ == "__main__":
    main()
