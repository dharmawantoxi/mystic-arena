#!/usr/bin/env python3
"""Execute Grimjaw hurt/death slices, particle primitives and bounded pool AST.

Not a full Grimjaw director or pixel/blending oracle.
"""
import copy
import argparse
import ast
import hashlib
import json
from pathlib import Path
import types
import prepare_godot_zephyr_particles as particles

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "heroes/grimjaw_fx.py"
OUTPUT = ROOT / "godot_rebuild/tests/fixtures/grimjaw_hurt.json"
CONFIG = ROOT / "godot_rebuild/data/grimjaw_hurt.json"


class Surface(particles.bolt.Surface):
    def set_alpha(self, alpha):
        # Effective primitive alpha only; no scratch overwrite/raster oracle.
        for command in self.commands:
            command[1][3] = command[1][3] * alpha / 255.0

    def blit(self, source, pos, **kwargs):
        for command in source.commands:
            if command[0] == "circle":
                self.commands.append(["circle", command[1].copy(),
                    [command[2][0] + pos[0], command[2][1] + pos[1]], command[3]])
            else:
                child = particles.bolt.Surface()
                child.commands = [command]
                super().blit(child, pos, **kwargs)


def environment():
    draw, _ = particles.bolt.oracle()
    env = dict(draw.__globals__)
    env["pygame"].Vector2 = particles.Vector
    env["pygame"].Surface = lambda *_args: Surface()
    env["pygame"].SRCALPHA = 0
    env["pygame"].draw.circle = lambda surface, color, center, radius: surface.commands.append(
        ["circle", list(color), list(center), radius])
    env["_SURF_CACHE"] = {}
    env["_cache_put"] = lambda _key, surface: surface
    tree = ast.parse(SOURCE.read_text())
    palette = next(n for n in tree.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "GRIMJAW_PALETTE" for t in n.targets))
    env["P"] = ast.literal_eval(palette.value)
    env["particle_budget"] = lambda: 1.0
    env["glow_allowed"] = lambda: True
    env["random"] = particles.RandomTape()
    limit = next(n for n in tree.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "MAX_PARTICLES" for t in n.targets))
    env["MAX_PARTICLES"] = ast.literal_eval(limit.value)
    nodes = [n for n in tree.body if
             (isinstance(n, ast.ClassDef) and n.name in ("Particle", "ParticleSystem"))
             or (isinstance(n, ast.FunctionDef) and n.name in ("_mix", "_budgeted", "_clamp_color", "_hash01", "glow_surface", "spark_surface"))]
    director = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GrimjawFXDirector")
    methods = {n.name: n for n in director.body if isinstance(n, ast.FunctionDef)}
    death_update = copy.deepcopy(methods["update"])
    death_update.name = "death_update"
    alive_index = next(i for i, n in enumerate(death_update.body) if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "alive" for t in n.targets))
    death_update.body = death_update.body[alive_index:alive_index + 3]
    death_update.body.insert(0, ast.parse("h = self.hero").body[0])
    ast.fix_missing_locations(death_update)
    nodes.extend([methods["on_death"], death_update])
    env["shake"] = lambda *_args: None
    update = methods["update"]
    hp = next(i for i, n in enumerate(update.body) if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == "hp" for t in n.targets))
    flash = next(n for n in update.body if isinstance(n, ast.If) and
                 isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Attribute)
                 and n.test.left.attr == "hit_flash")
    hero = next(n for n in update.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "h" for t in n.targets))
    update.body = [hero, update.body[hp], update.body[hp + 1], flash]
    nodes.extend([methods["on_hurt"], methods["_draw_hit_flash"], update])
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), env)
    return env


def death_cases():
    env = environment()
    bursts, feedback = [], []
    env["shake"] = lambda *args: feedback.append(list(args))
    owner = types.SimpleNamespace(hero=types.SimpleNamespace(x=30.75, y=-20.25), _was_alive=True,
        particles=types.SimpleNamespace(burst=lambda x, y, count, **kw:
            bursts.append({"position": [x, y], "count": count, "options": kw})))
    owner.on_death = types.MethodType(env["on_death"], owner)
    rows = []
    for alive in (True, False, False, True, False):
        bursts.clear()
        feedback.clear()
        owner.hero.alive = alive
        env["death_update"](owner, .016)
        rows.append({"alive": alive, "bursts": list(bursts), "feedback": list(feedback)})
    return rows


def particle_cases():
    cases = []
    for shape in ("ember", "smoke", "streak", "shard", "pixel", "glow", "spark", "glow_low"):
        for size in (3, 6):
            env = environment()
            args = [-20.75, 13.25, 123.5, -85.25, .5, size, env["P"]["ember"]]
            env["glow_allowed"] = lambda: shape != "glow_low"
            options = {"shape": "glow" if shape == "glow_low" else shape, "back": shape == "smoke", "rotation": .7,
                       "rotation_speed": -4, "gravity": 240, "drag": 1.4,
                       "color_end": env["P"]["fx_dark"], "fade_pow": 1.3}
            particle = env["Particle"]().spawn(*args, **options)
            rows = []
            for dt in (0, .016, .05, .1, .6):
                particle.update(dt)
                canvas = Surface()
                if particle.active:
                    particle.draw(canvas)
                rows.append({"state": particles.snapshot(particle), "commands": canvas.commands})
            cases.append({"glow_allowed": shape != "glow_low", "args": args, "options": options, "steps": [0, .016, .05, .1, .6], "expected": rows})
    return cases


def pool_cases():
    cases = []
    for ratio in (0, .1, .35, .5, 1):
        env = environment()
        env["particle_budget"] = lambda: ratio
        pool = env["ParticleSystem"](5)
        actions = [["burst", 0, 0, 8, {"shape": "smoke", "back": True}],
                   ["burst", 0, 0, 3, {"shape": "ember"}], ["stream", 0, 0, 50, -10, 6, {}], ["update", .1],
                   ["update", 1], ["stream", -10, 20, -10, 20, 6, {}], ["clear"], ["burst", 1, 2, 3, {"shape": "streak"}], ["clear"]]
        rows = []
        for name, *args in actions:
            result = None
            if name in ("burst", "stream"):
                *positional, options = args
                result = getattr(pool, name)(*positional, **options)
            else:
                getattr(pool, name)(*args)
            rows.append({"result": result, "live": [particles.snapshot(p) for p in pool._live],
                         "pooled": len(pool._pool), "random_index": env["random"].index})
        cases.append({"budget": ratio, "actions": actions, "expected": rows})
    return cases


def build():
    env = environment()
    cases = []
    for steps in (
        [[100, 30.75, 50.25, 0], [90, 30.75, 50.25, .016],
         [90, 40.5, 60.5, .05], [90, 40.5, 60.5, .2]],
        [[100, -20.75, -10.25, 0], [99.995, -20.75, -10.25, .01],
         [110, -20.75, -10.25, .01], [90, -20.75, -10.25, 0],
         [80, -20.75, -10.25, .08], [0, -20.75, -10.25, .2]],
    ):
        bursts = []
        hero = types.SimpleNamespace(max_hp=100)
        owner = types.SimpleNamespace(hero=hero, _last_hp=None, hit_flash=0.0,
            particles=types.SimpleNamespace(burst=lambda x, y, count, **options:
                bursts.append({"position": [x, y], "count": count, "options": options})))
        owner.on_hurt = types.MethodType(env["on_hurt"], owner)
        rows = []
        for hp, x, y, dt in steps:
            hero.hp, hero.x, hero.y = hp, x, y
            bursts.clear()
            env["update"](owner, dt)
            canvas = Surface()
            if owner.hit_flash > 0:
                env["_draw_hit_flash"](owner, canvas)
            rows.append({"hit_flash": owner.hit_flash, "bursts": list(bursts), "commands": canvas.commands})
        cases.append({"steps": steps, "expected": rows})
    recipe = next(row["bursts"][0] for case in cases for row in case["expected"] if row["bursts"])
    budget_rows = []
    for budget in (0, .1, .35, .5, .75, 1):
        env["particle_budget"] = lambda: budget
        budget_rows.append({"budget": budget, "count": env["_budgeted"](recipe["count"])})
    trajectories = []
    for life in (.5, .01):
        options = {"shape": "streak", "drag": 3.0, "gravity": 80, "fade_pow": 1.3,
                   "color_end": env["P"]["fx_dark"], "ax": -3.5, "rotation_speed": 2.0}
        args = [-20.75, 13.25, 123.5, -85.25, life, 4.0, env["P"]["ember"]]
        particle = env["Particle"]().spawn(*args, **options)
        rows = []
        steps = [0, .016, .05, .1, .6]
        used = []
        for dt in steps:
            used.append(dt)
            particle.update(dt)
            state = particles.snapshot(particle)
            # Shared backend supports only the foreground streak used by on_hurt.
            assert state.pop("back") is False
            rows.append({"state": state, "commands": particles.geometry(particle)})
            if not particle.active:
                break
        trajectories.append({"args": args, "options": options, "steps": used, "expected": rows})
    tree = ast.parse(SOURCE.read_text())
    limit = next(n for n in tree.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "MAX_PARTICLES" for t in n.targets))
    recipe = next(row["bursts"][0] for case in cases for row in case["expected"] if row["bursts"])
    death = death_cases()
    death_recipes = [{"offset": [row["position"][0] - 30.75, row["position"][1] + 20.25],
                      "count": row["count"], "options": row["options"]} for row in death[1]["bursts"]]
    config = {"death_recipes": death_recipes, "death_feedback": death[1]["feedback"], "capacity": ast.literal_eval(limit.value), "palette": env["P"],
              "recipe": {"count": recipe["count"], "options": recipe["options"]}}
    fixture = {"schema": 1, "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
               "scope": "Grimjaw HP/hurt/death, flash/particle primitives, burst and stream pool; not pixels/blending",
               "cases": cases, "budgets": budget_rows, "trajectories": trajectories,
               "death": death, "particles": particle_cases(), "pools": pool_cases(), "random_tape": particles.TAPE}
    return json.loads(json.dumps(fixture)), json.loads(json.dumps(config))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    fixture, config = build()
    for path, data in ((OUTPUT, fixture), (CONFIG, config)):
        text = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text() != text:
                parser.exit(1, f"Grimjaw hurt oracle/config drift: {path}\n")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print("Grimjaw hurt/streak oracle OK")


if __name__ == "__main__":
    main()
