"""Record the source tower-hover indicators for the read-only Godot painter (slice 9bv11).

The oracle executes `HoverIndicators.draw` and its two tower helpers from
`ui_components/_bundle.py` under the shared pygame recorder. It covers the pulsing range
surface (fill, border, rotating dash dots), tooltip shadow/panel/text/arrow, and the no-hover
branch. It does not port the source's pointer detection or change input routing.

Run: python godot_rebuild/tests/tower_hover_source_oracle.py
"""
import ast
import json
import math
import textwrap
import types
from pathlib import Path
from types import SimpleNamespace

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "ui_components" / "_bundle.py"
CORE = ROOT / "_core.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "tower_hover_source.json"
METHODS = ("draw", "_draw_tower_range_hover", "_draw_tower_tooltip")


def _constant(name):
    for node in ast.parse(CORE.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(target, "id", "") == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("%s not found in %s" % (name, CORE.name))


TOWER_COLORS = _constant("TOWER_TYPE_COLORS")
FRAMES = [
    {
        "name": "archer_tower_hover",
        "state": {
            "x": 360,
            "y": 330,
            "range": 140,
            "animation_time": 42,
            "name": "Archer",
            "level": 2,
            "damage": 75,
            "kills": 4,
            "color": list(TOWER_COLORS["archer"]["main"]),
        },
    },
    {
        "name": "cannon_tower_hover",
        "state": {
            "x": 895,
            "y": 505,
            "range": 205,
            "animation_time": 117,
            "name": "Cannon",
            "level": 5,
            "damage": 198,
            "kills": 12,
            "color": list(TOWER_COLORS["cannon"]["main"]),
        },
    },
    {"name": "no_tower_hover", "state": None},
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
    clock = {"ticks": 0}
    pygame = rec.make_pygame(clock)
    original_get_rect = rec.Surface.get_rect

    def get_rect(surface, **anchors):
        if "centerx" in anchors or "top" in anchors:
            x = int(anchors.get("centerx", 0)) - surface.w // 2
            y = int(anchors.get("top", 0))
            return rec.Rect(x, y, surface.w, surface.h)
        return original_get_rect(surface, **anchors)

    rec.Surface.get_rect = get_rect
    perf = types.ModuleType("mobile.perf")

    class Pool:
        @staticmethod
        def get(width, height):
            return rec.Surface((width, height))

        @staticmethod
        def release(_surface):
            return None

    perf.POOL = Pool()
    mobile = types.ModuleType("mobile")
    mobile.__path__ = []
    try:
        with rec.installed({"pygame": pygame, "mobile": mobile, "mobile.perf": perf}):
            namespace = {"math": math, "pygame": pygame}
            hover_class = _harvest_class(namespace)
            painter = hover_class()
            tower = None
            if state is not None:
                tower = SimpleNamespace(**state)
            painter.game = SimpleNamespace(
                animation_time=float(state["animation_time"]) if state else 0.0,
                hovered_tower=tower,
                hovered_slot=None,
            )
            painter.ui = SimpleNamespace(font_small=rec.Font(24, "body_medium"))
            surface = rec.Surface((1280, 720))
            painter.draw(surface)
            return surface.ops
    finally:
        rec.Surface.get_rect = original_get_rect


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
