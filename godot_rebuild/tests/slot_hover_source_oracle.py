"""Record the source build-slot hover indicators for the view-only Godot painter (slice 9bv12).

The oracle executes `HoverIndicators.draw` and `_draw_slot_hover` from
`ui_components/_bundle.py` under the shared pygame recorder. It covers the pulsing glow
surface, the rounded hint box, the hint text, integer anchoring of fractional slot
positions, and the no-hover branch. It does not port pointer detection or change input.

Run: python godot_rebuild/tests/slot_hover_source_oracle.py
"""
import ast
import json
import math
import textwrap
from pathlib import Path
from types import SimpleNamespace

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "ui_components" / "_bundle.py"
CORE = ROOT / "_core.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "slot_hover_source.json"
METHODS = ("draw", "_draw_slot_hover")
FRAMES = [
    {
        "name": "slot_hover_top_lane",
        "state": {"x": 245, "y": 210, "animation_time": 42},
    },
    {
        "name": "slot_hover_low_pulse",
        "state": {"x": 895, "y": 505, "animation_time": 117},
    },
    {
        "name": "slot_hover_fractional_position",
        "state": {"x": 512.75, "y": 318.25, "animation_time": 301},
    },
    {"name": "no_slot_hover", "state": None},
]


def _harvest_class(namespace):
    source = BUNDLE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    owner = next(
        (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "HoverIndicators"),
        None,
    )
    if owner is None:
        raise AssertionError("HoverIndicators not found in %s" % BUNDLE.name)
    found = {
        node.name: node
        for node in owner.body
        if isinstance(node, ast.FunctionDef) and node.name in METHODS
    }
    missing = set(METHODS) - set(found)
    if missing:
        raise AssertionError("%s not found in HoverIndicators" % sorted(missing))
    body = "".join(
        textwrap.indent(textwrap.dedent(ast.get_source_segment(source, found[name], padded=True)), "    ") + "\n"
        for name in METHODS
    )
    exec(compile("class HoverIndicators:\n%s" % body, BUNDLE.name, "exec"), namespace)
    return namespace["HoverIndicators"]


def _record(state):
    pygame = rec.make_pygame({"ticks": 0})
    original_center = rec.Rect.__dict__.get("center")
    rec.Rect.center = property(lambda rect: (rect.x + rect.w // 2, rect.y + rect.h // 2))
    try:
        with rec.installed({"pygame": pygame}):
            namespace = {"math": math, "pygame": pygame}
            hover_class = _harvest_class(namespace)
            painter = hover_class()
            slot = dict(state) if state is not None else None
            painter.game = SimpleNamespace(
                animation_time=float(state["animation_time"]) if state else 0.0,
                hovered_tower=None,
                hovered_slot=slot,
            )
            painter.ui = SimpleNamespace(font_tiny=rec.Font(20, "body"))
            surface = rec.Surface((1280, 720))
            painter.draw(surface)
            return surface.ops
    finally:
        if original_center is None:
            del rec.Rect.center
        else:
            rec.Rect.center = original_center


def source_fixture():
    return {
        "source": "ui_components/_bundle.py::HoverIndicators",
        "frames": [
            {"name": frame["name"], "state": frame["state"], "ops": _record(frame["state"])}
            for frame in FRAMES
        ],
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    op_count = sum(len(frame["ops"]) for frame in fixture["frames"])
    print("Wrote %s: %d frames / %d ops" % (FIXTURE.name, len(fixture["frames"]), op_count))


if __name__ == "__main__":
    main()
