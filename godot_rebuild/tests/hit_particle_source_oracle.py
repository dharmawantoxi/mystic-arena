"""Source oracle for the HitParticle port.

`import _render` fails today with a pre-existing circular import, and the
Python sources are read-only, so this oracle extracts the real
`class HitParticle` block from `_render.py` and executes it verbatim with
`pygame`, `math` and `random` in scope. The class pre-renders a sprite in
`__init__` via pygame, which works headless, so the whole source body runs
untouched.

Every number in the fixture therefore comes from the actual source
algorithm. Cases with an explicit velocity are fully deterministic; the
random-velocity case is seeded and its vx/vy are recorded so the native
suite can pin them.

Run: python godot_rebuild/tests/hit_particle_source_oracle.py
"""
import json
import math
import random
import sys
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hit_particle_source.json"

CASES = [
    {
        "name": "spark_default",
        "x": 100.0, "y": 200.0, "color": [255, 200, 100],
        "velocity": [1.5, -2.0], "lifetime": 15, "size": 2,
    },
    {
        "name": "magic_short",
        "x": 10.0, "y": 20.0, "color": [80, 180, 255],
        "velocity": [-0.5, 1.25], "lifetime": 8, "size": 3,
    },
    {
        "name": "random_velocity",
        "x": 300.0, "y": 400.0, "color": [255, 80, 80],
        "velocity": None, "lifetime": 20, "size": 1,
    },
]

EXTRA_STEPS = 3


def _load_class():
    """Execute only the real `class HitParticle` block from _render.py."""
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("class HitParticle:"))
    end = next(i for i, line in enumerate(lines) if i > start and line.startswith("class "))
    block = "\n".join(lines[start:end])
    namespace = {"random": random, "math": math, "pygame": pygame}
    exec(compile(block, "_render.py:HitParticle", "exec"), namespace)
    return namespace["HitParticle"]


def _trace(cls, case):
    random.seed(11235813)
    if case["velocity"] is None:
        item = cls(
            case["x"], case["y"], tuple(case["color"]),
            None, case["lifetime"], case["size"],
        )
    else:
        item = cls(
            case["x"], case["y"], tuple(case["color"]),
            tuple(case["velocity"]), case["lifetime"], case["size"],
        )
    # Record the velocity the source starts from: the random-velocity case
    # needs it so the native suite can replay the same trajectory.
    start_vx = round(item.vx, 6)
    start_vy = round(item.vy, 6)
    steps = []
    for _ in range(case["lifetime"] + EXTRA_STEPS):
        item.update()
        ratio = item.lifetime / item.max_lifetime
        steps.append([
            round(item.x, 6), round(item.y, 6),
            round(item.vx, 6), round(item.vy, 6),
            item.lifetime, 1 if item.alive else 0,
            int(255 * ratio), max(1, int(item.size * ratio)),
        ])
    return {
        "vx": start_vx, "vy": start_vy,
        "gravity": item.gravity, "steps": steps,
    }


def source_fixture():
    cls = _load_class()
    cases = []
    for case in CASES:
        traced = _trace(cls, case)
        cases.append({
            "name": case["name"],
            "config": {k: case[k] for k in
                       ("x", "y", "color", "velocity", "lifetime", "size")},
            "vx": traced["vx"], "vy": traced["vy"],
            "gravity": traced["gravity"],
            "steps": traced["steps"],
        })
    return {"source": "_render.py::HitParticle", "cases": cases}


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%d cases)" % (FIXTURE, len(fixture["cases"])))


if __name__ == "__main__":
    sys.exit(main())
