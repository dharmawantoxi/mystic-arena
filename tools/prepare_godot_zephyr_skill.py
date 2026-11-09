#!/usr/bin/env python3
"""Execute original SkillFX constructor/update; record emissions/front geometry, not pixels."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import types
import prepare_godot_zephyr_particles as particles

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "heroes/zephyr_fx.py"
OUTPUT = ROOT / "godot_rebuild/tests/fixtures/zephyr_skill.json"
CONFIG = ROOT / "godot_rebuild/data/zephyr_skill.json"
FIELDS = ("kind", "x", "y", "radius", "age", "t_charge", "t_release", "t_area",
          "t_impact", "total", "active", "phase", "_released", "_impacted", "_emit", "seed")


def environment():
    env, _ = particles.environment()
    tree = ast.parse(SOURCE.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SkillFX")
    env["random"].randint = lambda _low, _high: 1234
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), env)
    return env


class Surface(particles.bolt.Surface):
    def __init__(self, size=(0, 0), *_args):
        super().__init__()
        self.size = size

    def get_width(self):
        return self.size[0]

    def get_height(self):
        return self.size[1]

    def set_alpha(self, alpha):
        for command in self.commands:
            command[1][3] = alpha

    def blit(self, source, pos, **kwargs):
        for command in source.commands:
            if command[0] in ("circle", "oval"):
                kind, color, center, *args = command
                self.commands.append([kind, color.copy(), [center[0] + pos[0], center[1] + pos[1], *center[2:]], *args])
            else:
                child = particles.bolt.Surface()
                child.commands = [command]
                super().blit(child, pos, **kwargs)


class Rect:
    def __init__(self, x, y, width, height):
        self.values = [int(x), int(y), int(width), int(height)]

    def inflate(self, width, height):
        x, y, w, h = self.values
        return Rect(x - int(width / 2), y - int(height / 2), w + width, h + height)


def front_environment(detail):
    env = environment()
    env["skill_detail"] = lambda: detail
    env["_scratch"] = lambda *_args: Surface()
    env["_SURF_CACHE"] = {}
    env["_cache_put"] = lambda _key, surface: surface
    env["pygame"].Surface = Surface
    env["pygame"].SRCALPHA = 0
    def circle(surface, color, center, radius, thickness):
        surface.commands.append(["circle", list(color), list(center), radius, thickness])
    env["pygame"].draw.circle = circle
    tree = ast.parse(SOURCE.read_text())
    helpers = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("ring_surface", "_clamp_color")]
    exec(compile(ast.Module(body=helpers, type_ignores=[]), str(SOURCE), "exec"), env)
    return env


def front_cases(ground=False):
    cases = []
    for detail in (.35, .55, 1.0):
        env = front_environment(detail)
        if ground:
            env["pygame"].Rect = Rect
            def ellipse(surface, color, rect, width=0):
                box = rect.values if isinstance(rect, Rect) else list(rect)
                surface.commands.append(["oval", list(color), box, width])
            env["pygame"].draw.ellipse = ellipse
            tree = ast.parse(SOURCE.read_text())
            helpers = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                       and n.name in ("ground_glow_surface", "_hash01")]
            exec(compile(ast.Module(body=helpers, type_ignores=[]), str(SOURCE), "exec"), env)
        for kind in "qwer":
            for x, y in ((100.75, 200.25), (-20.75, -10.25)):
                skill = env["SkillFX"](kind, x, y)
                samples = [("cast", 0, True), ("charge", skill.t_charge * .5, True)]
                for phase, start, end in (("release", skill.t_charge, skill.t_release),
                                          ("area", skill.t_release, skill.t_area),
                                          ("impact", skill.t_area, skill.t_impact)):
                    samples.extend((phase, start + (end - start) * t, True) for t in (0, .5, .99))
                samples.extend([("fade", skill.t_impact, True), ("fade", skill.total, False)])
                for phase, age, active in samples:
                    if ground and phase == "cast":
                        continue  # constructor-only cast has invalid legacy ground alpha before update
                    skill.phase, skill.age, skill.active = phase, age, active
                    surface = Surface()
                    if ground:
                        skill.draw_ground(surface)
                    else:
                        skill.draw_front(surface)
                    cases.append({"kind": kind, "x": x, "y": y, "detail": detail,
                                  "phase": phase, "age": age, "active": active,
                                  "commands": surface.commands})
    return cases


def build():
    cases = []
    for kind, radius, connected, steps in [
        *[(key, None, True, [0, .02, .02, .18, .05, .08, .12, .3, .06, .06, .3, .5, .4, 1])
          for key in "qwer"],
        ("unknown", 0, True, [.44, .9, .18, 1]),
        ("q", 35, False, [.1, .2, .14, .9, .18, .55]),
        ("r", -10, True, [2.1, .01, 1]),
    ]:
        env = environment()
        events = []
        def spawn(*args, **options):
            events.append({"type": "spawn", "args": args, "options": options})
        def burst(*args, **options):
            events.append({"type": "burst", "args": args, "options": options})
        pool = types.SimpleNamespace(spawn=spawn, burst=burst) if connected else None
        skill = env["SkillFX"](kind, -20.75, 13.25, pool, radius)
        def snapshot():
            return {key: getattr(skill, key) for key in FIELDS}
        initial = snapshot()
        rows = []
        for dt in steps:
            events.clear()
            alive = skill.update(dt)
            rows.append({"alive": alive, "state": snapshot(), "events": list(events),
                         "random_index": env["random"].index})
            if not alive:
                break
        cases.append({"kind": kind, "radius": radius, "connected": connected,
                      "steps": steps[:len(rows)], "initial": initial, "expected": rows})
    cls = environment()["SkillFX"]
    tree = ast.parse(SOURCE.read_text())
    director = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ZephyrFXDirector")
    cast = next(n for n in director.body if isinstance(n, ast.FunctionDef) and n.name == "on_cast")
    guard = next(n for n in cast.body if isinstance(n, ast.If))
    limit = ast.literal_eval(guard.test.comparators[0])
    config = {"timeline": cls.TIMELINE, "tint": cls.TINT, "radius": cls.RADIUS,
              "director_limit": limit}
    fixture = {"schema": 1, "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
               "scope": "SkillFX lifecycle/emission requests and front primitive/helper commands; fixed seed, no pixel/blending or RNG parity",
               "random_tape": particles.TAPE, "cases": cases, "front": front_cases(), "ground": front_cases(ground=True)}
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
                parser.exit(1, f"SkillFX oracle/config drift: {path}\n")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print("Zephyr SkillFX lifecycle/emission oracle OK")


if __name__ == "__main__":
    main()
