#!/usr/bin/env python3
"""Execute original Grimjaw SkillFX lifecycle/emissions with fixed palette/tape.

Front primitive geometry included; no ground, live palette-sync, full director or RNG parity.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import types
import prepare_godot_grimjaw_hurt as hurt
import prepare_godot_zephyr_skill as zephyr

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "heroes/grimjaw_fx.py"
OUTPUT = ROOT / "godot_rebuild/tests/fixtures/grimjaw_skill.json"
CONFIG = ROOT / "godot_rebuild/data/grimjaw_skill.json"


def environment():
    env = hurt.environment()
    env["_sync_palette"] = lambda: None  # Export the repository palette, not runtime skins.
    def randint(low, high):
        if high == 9999:
            return 1234
        return low + min(high - low, int(env["random"].random() * (high - low + 1)))
    env["random"].randint = randint
    tree = ast.parse(SOURCE.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SkillFX")
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), env)
    return env


class Surface(zephyr.Surface):
    def set_alpha(self, alpha):
        for command in self.commands:
            command[1][3] = command[1][3] * alpha / 255.0

    def blit(self, source, pos, **kwargs):
        for command in source.commands:
            if command[0] in ("polyline", "polygon_outline"):
                self.commands.append([command[0], command[1].copy(),
                    [[p[0] + pos[0], p[1] + pos[1]] for p in command[2]], *command[3:]])
            else:
                child = zephyr.particles.bolt.Surface()
                child.commands = [command]
                super().blit(child, pos, **kwargs)


def front_environment(detail, glow):
    env = environment()
    env["skill_detail"] = lambda: detail
    env["glow_allowed"] = lambda: glow
    env["pygame"].Surface = Surface
    env["_scratch"] = lambda *_args: Surface()
    def lines(surface, color, closed, points, width):
        points = [list(p) for p in points]
        surface.commands.append(["polyline", list(color), points + points[:1] if closed else points, width])
    def polygon(surface, color, points, width=0):
        surface.commands.append(["polygon_outline" if width else "polygon", list(color),
                                [list(p) for p in points], *([width] if width else [])])
    env["pygame"].draw.lines = lines
    env["pygame"].draw.polygon = polygon
    tree = ast.parse(SOURCE.read_text())
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "ring_surface")
    exec(compile(ast.Module(body=[helper], type_ignores=[]), str(SOURCE), "exec"), env)
    return env


def front_cases():
    cases = []
    for detail in (.35, .55, 1.0):
        for glow in (False, True):
            env = front_environment(detail, glow)
            for key in "qwer":
                for facing in ((-1, 1) if key == "e" else (1,)):
                    for x, y in ((100.75, 200.25), (-20.75, -10.25)):
                        skill = env["SkillFX"](key, x, y)
                        skill._facing = facing
                        samples = [("cast", 0, True), ("charge", skill.t_charge * .5, True)]
                        for phase, start, end in (("release", skill.t_charge, skill.t_release),
                                                  ("area", skill.t_release, skill.t_area),
                                                  ("impact", skill.t_area, skill.t_impact)):
                            samples.extend((phase, start + (end - start) * t, True) for t in (0, .5, .99))
                        samples.extend([("fade", skill.t_impact, True), ("fade", skill.total, False)])
                        for phase, age, active in samples:
                            skill.phase, skill.age, skill.active = phase, age, active
                            canvas = Surface()
                            skill.draw_front(canvas)
                            cases.append({"key": key, "x": x, "y": y, "detail": detail,
                                          "glow": glow, "facing": facing, "phase": phase,
                                          "age": age, "active": active, "commands": canvas.commands})
    return cases


def build():
    cases = []
    for key, radius, connected, steps in [
        *[(key, None, True, [0, .02, .02, .12, .10, .10, .08, .10, .10, .20, .08, .08, .08, .40, .08, .08, .16, .16, 1]) for key in "qwer"],
        ("unknown", 0, True, [.50, .95, .1, 1]),
        ("w", 35, False, [.1, .2, .14, 1, 1]),
        ("r", -10, True, [1.9, .01, 2]),
    ]:
        env = environment()
        events = []
        pool = types.SimpleNamespace(
            spawn=lambda *a, **kw: events.append({"type": "spawn", "args": a, "options": kw}),
            burst=lambda *a, **kw: events.append({"type": "burst", "args": a, "options": kw})) if connected else None
        skill = env["SkillFX"](key, -20.75, 13.25, pool, radius)
        def snapshot():
            return {name: getattr(skill, name) for name in (*zephyr.FIELDS, "col_a", "col_b")}
        initial = snapshot()
        rows = []
        for dt in steps:
            events.clear()
            alive = skill.update(dt)
            rows.append({"alive": alive, "state": snapshot(), "events": list(events),
                         "random_index": env["random"].index})
            if not alive:
                break
        cases.append({"key": key, "radius": radius, "connected": connected,
                      "steps": steps[:len(rows)], "initial": initial, "expected": rows})
    env = environment()
    cls = env["SkillFX"]
    colors = {}
    for key in "qwer":
        skill = cls(key, 0, 0)
        colors[key] = [skill.col_a, skill.col_b]
    tree = ast.parse(SOURCE.read_text())
    director = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GrimjawFXDirector")
    cast = next(n for n in director.body if isinstance(n, ast.FunctionDef) and n.name == "on_cast")
    limit = ast.literal_eval(next(n for n in cast.body if isinstance(n, ast.If)).test.comparators[0])
    config = {"timeline": cls.TIMELINE, "radius": cls.RADIUS, "colors": colors,
              "palette": env["P"], "director_limit": limit}
    fixture = {"schema": 1, "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
               "scope": "Grimjaw SkillFX lifecycle/emissions/front primitives; fixed palette/seed/tape, not pixels",
               "random_tape": hurt.particles.TAPE, "cases": cases, "front": front_cases()}
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
                parser.exit(1, f"Grimjaw SkillFX oracle/config drift: {path}\n")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print("Grimjaw SkillFX lifecycle/emission oracle OK")


if __name__ == "__main__":
    main()
