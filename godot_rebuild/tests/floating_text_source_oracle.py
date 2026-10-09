"""Source oracle for the FloatingText (damage number) port.

`import _render` fails today with a pre-existing circular import
("cannot import name 'MapRenderer' from partially initialized module
'_render'"), and the Python sources are read-only, so this oracle does not
import the module. It extracts the real `class FloatingText` source block
from `_render.py` verbatim and executes it with `get_font` stubbed out (the
class already degrades to `None` surfaces when pre-rendering fails).

Every number in the fixture therefore comes from the actual source
algorithm, not from a re-implementation.

Run: python godot_rebuild/tests/floating_text_source_oracle.py
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "floating_text_source.json"

CASES = [
    {
        "name": "normal_medium",
        "x": 100.0, "y": 200.0, "text": "123",
        "color": [255, 220, 50], "size": "medium",
        "velocity": [0.0, -2.0], "lifetime": 45, "critical": False,
    },
    {
        "name": "critical_large",
        "x": 50.0, "y": 60.0, "text": "999!",
        "color": [255, 220, 50], "size": "large",
        "velocity": [0.0, -2.5], "lifetime": 30, "critical": True,
    },
    {
        "name": "heal_small",
        "x": 10.0, "y": 20.0, "text": "+40",
        "color": [100, 255, 100], "size": "small",
        "velocity": [1.0, -1.0], "lifetime": 20, "critical": False,
    },
]

STEPS = 60


def _load_class():
    """Execute only the real `class FloatingText` block from _render.py."""
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("class FloatingText:"))
    end = next(i for i, line in enumerate(lines) if i > start and line.startswith("class "))
    block = "\n".join(lines[start:end])

    def _get_font(*_args, **_kwargs):
        raise RuntimeError("oracle stub: no font backend")

    namespace = {"random": random, "get_font": _get_font}
    exec(compile(block, "_render.py:FloatingText", "exec"), namespace)
    return namespace["FloatingText"]


def _trace(cls, case):
    random.seed(20240917)
    item = cls(
        case["x"], case["y"], case["text"],
        tuple(case["color"]), case["size"],
        tuple(case["velocity"]), case["lifetime"], case["critical"],
    )
    drift = item.x_drift
    steps = []
    for _ in range(STEPS):
        item.update()
        ratio = min(1.0, item.lifetime / (item.max_lifetime * 0.5))
        steps.append([
            round(item.x, 6), round(item.y, 6),
            round(item.velocity_y, 6), round(item.scale, 6),
            item.lifetime, 1 if item.alive else 0,
            int(255 * ratio),
        ])
    return drift, steps


def source_fixture():
    cls = _load_class()
    cases = []
    for case in CASES:
        drift, steps = _trace(cls, case)
        cases.append({
            "name": case["name"],
            "config": {k: case[k] for k in
                       ("x", "y", "text", "color", "size", "velocity", "lifetime", "critical")},
            "x_drift": round(drift, 6),
            "font_size": _trace_font_size(cls, case),
            "steps": steps,
        })
    return {"source": "_render.py::FloatingText", "cases": cases}


def _trace_font_size(cls, case):
    random.seed(20240917)
    item = cls(
        case["x"], case["y"], case["text"], tuple(case["color"]), case["size"],
        tuple(case["velocity"]), case["lifetime"], case["critical"],
    )
    return item.font_size


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%d cases)" % (FIXTURE, len(fixture["cases"])))


if __name__ == "__main__":
    sys.exit(main())
