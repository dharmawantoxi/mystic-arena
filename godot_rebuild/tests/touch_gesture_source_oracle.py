#!/usr/bin/env python3
"""Read-only behavioral oracle for ``mobile/touch.py::TouchManager``.

The source classes are compiled from their AST with a deterministic monotonic
clock. Scenarios exercise release-gated taps, long press, slop, scroll notches,
velocity smoothing, fling inertia, double-tap suppression, multi-touch and the
real tap/hold/scroll dispatch bridge. No pygame runtime or legacy module is imported.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mobile/touch.py"
FIXTURE = Path(__file__).with_name("fixtures") / "touch_gesture_source.json"
BASE_MS = 10_000.0


class Clock:
    def __init__(self):
        self.milliseconds = BASE_MS

    def perf_counter(self):
        return self.milliseconds / 1000.0


SCENARIOS = [
    {
        "label": "tap_release_gate",
        "ops": [
            {"at": 0, "op": "down", "id": 0, "pos": [320, 240]},
            {"at": 120, "op": "up", "id": 0, "pos": [320, 240]},
        ],
    },
    {
        "label": "long_press_once",
        "ops": [
            {"at": 0, "op": "down", "id": 3, "pos": [700, 330]},
            {"at": 449, "op": "update"},
            {"at": 451, "op": "update"},
            {"at": 900, "op": "update"},
            {"at": 920, "op": "up", "id": 3, "pos": [700, 330]},
        ],
    },
    {
        "label": "slop_boundary_and_drag",
        "ops": [
            {"at": 0, "op": "down", "id": 0, "pos": [100, 100]},
            {"at": 40, "op": "motion", "id": 0, "pos": [114, 100]},
            {"at": 80, "op": "up", "id": 0, "pos": [114, 100]},
            {"at": 1000, "op": "down", "id": 1, "pos": [200, 200]},
            {"at": 1040, "op": "motion", "id": 1, "pos": [215, 200]},
            {"at": 1080, "op": "up", "id": 1, "pos": [215, 200]},
        ],
    },
    {
        "label": "scroll_and_fling_down",
        "ops": [
            {"at": 0, "op": "down", "id": 0, "pos": [500, 200]},
            {"at": 16, "op": "motion", "id": 0, "pos": [500, 243]},
            {"at": 32, "op": "motion", "id": 0, "pos": [500, 290]},
            {"at": 40, "op": "up", "id": 0, "pos": [500, 290]},
            {"at": 56, "op": "update"},
            {"at": 72, "op": "update"},
            {"at": 88, "op": "update"},
        ],
    },
    {
        "label": "scroll_and_fling_up",
        "ops": [
            {"at": 0, "op": "down", "id": 9, "pos": [620, 500]},
            {"at": 16, "op": "motion", "id": 9, "pos": [620, 410]},
            {"at": 32, "op": "up", "id": 9, "pos": [620, 410]},
            {"at": 48, "op": "update"},
            {"at": 64, "op": "update"},
        ],
    },
    {
        "label": "double_tap_and_distance_gate",
        "ops": [
            {"at": 0, "op": "down", "id": 0, "pos": [400, 300]},
            {"at": 50, "op": "up", "id": 0, "pos": [400, 300]},
            {"at": 180, "op": "down", "id": 0, "pos": [439, 339]},
            {"at": 220, "op": "up", "id": 0, "pos": [439, 339]},
            {"at": 300, "op": "down", "id": 0, "pos": [479, 339]},
            {"at": 340, "op": "up", "id": 0, "pos": [479, 339]},
        ],
    },
    {
        "label": "multi_touch_independent",
        "ops": [
            {"at": 0, "op": "down", "id": 10, "pos": [200, 300]},
            {"at": 10, "op": "down", "id": 11, "pos": [900, 300]},
            {"at": 30, "op": "motion", "id": 10, "pos": [200, 350]},
            {"at": 60, "op": "up", "id": 11, "pos": [900, 300]},
            {"at": 80, "op": "up", "id": 10, "pos": [200, 350]},
        ],
    },
    {
        "label": "new_down_stops_fling_and_cancel",
        "ops": [
            {"at": 0, "op": "down", "id": 0, "pos": [100, 100]},
            {"at": 20, "op": "motion", "id": 0, "pos": [100, 180]},
            {"at": 30, "op": "up", "id": 0, "pos": [100, 180]},
            {"at": 40, "op": "down", "id": 1, "pos": [300, 300]},
            {"at": 50, "op": "cancel"},
            {"at": 500, "op": "update"},
        ],
    },
]


def _source_namespace(clock):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    constants = {
        "TAP_SLOP",
        "LONG_PRESS_MS",
        "DOUBLE_TAP_MS",
        "SCROLL_STEP",
        "FLING_FRICTION",
        "FLING_MIN_SPEED",
    }
    classes = {"TouchPoint", "TouchAction", "TouchManager"}
    functions = {"dispatch_to_game", "dispatch_to_menu"}
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in constants for target in node.targets
        ):
            nodes.append(node)
        elif isinstance(node, ast.ClassDef) and node.name in classes:
            nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in functions:
            nodes.append(node)
    assert len(nodes) == len(constants) + len(classes) + len(functions)
    env = {"time": clock}
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, "<source TouchManager>", "exec"), env)
    return env


def _action(action):
    return {
        "kind": action.kind,
        "pos": [round(float(action.pos[0]), 6), round(float(action.pos[1]), 6)],
        "delta": [round(float(action.delta[0]), 6), round(float(action.delta[1]), 6)],
        "value": round(float(action.value), 6),
        "touch_id": int(action.touch_id),
    }


def _state(manager):
    return {
        "points": sorted(int(value) for value in manager.points),
        "active_pos": None if manager.active_pos is None else list(manager.active_pos),
        "fling_velocity": round(float(manager.fling_velocity), 6),
        "fling_pos": list(manager.fling_pos),
        "tap_count": int(manager.counts["tap"]),
    }


def _run_case(env, clock, spec):
    manager = env["TouchManager"](use_finger_events=False)
    steps = []
    for operation in spec["ops"]:
        clock.milliseconds = BASE_MS + float(operation["at"])
        name = operation["op"]
        touch_id = int(operation.get("id", 0))
        position = tuple(operation.get("pos", (0, 0)))
        if name == "down":
            manager._down(touch_id, position)
        elif name == "motion":
            manager._motion(touch_id, position)
        elif name == "up":
            manager._up(touch_id, position)
        elif name == "update":
            manager.update()
        elif name == "cancel":
            manager.cancel()
        else:
            raise AssertionError(name)
        steps.append(
            {
                "at": operation["at"],
                "op": name,
                "actions": [_action(value) for value in manager.collect()],
                "state": _state(manager),
            }
        )
    return {"label": spec["label"], "ops": spec["ops"], "steps": steps}


def _dispatch_fixture(env):
    class Target:
        def __init__(self):
            self.calls = []

        def handle_click(self, position, button):
            self.calls.append({"pos": list(position), "button": int(button)})

    rows = []
    for kind, value in (
        ("tap", 0),
        ("long_press", 0),
        ("scroll", -1),
        ("scroll", 1),
        ("double_tap", 0),
        ("drag", 0),
    ):
        target = Target()
        action = env["TouchAction"](kind, (120, 240), value=value, touch_id=7)
        consumed = env["dispatch_to_game"](action, target)
        rows.append(
            {
                "kind": kind,
                "value": value,
                "consumed": bool(consumed),
                "calls": target.calls,
            }
        )
    return rows


def source_fixture():
    clock = Clock()
    env = _source_namespace(clock)
    sample = env["TouchManager"](use_finger_events=False)
    return {
        "policy": {
            "tap_slop": env["TAP_SLOP"],
            "long_press_ms": env["LONG_PRESS_MS"],
            "double_tap_ms": env["DOUBLE_TAP_MS"],
            "scroll_step": env["SCROLL_STEP"],
            "fling_friction": env["FLING_FRICTION"],
            "fling_min_speed": env["FLING_MIN_SPEED"],
            "initial_active_pos": sample.active_pos,
        },
        "dispatch_to_game": _dispatch_fixture(env),
        "cases": [_run_case(env, clock, spec) for spec in SCENARIOS],
    }


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    else:
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
        if actual != expected:
            raise SystemExit("FAIL: touch gesture source fixture drift")
    actions = sum(
        len(step["actions"]) for case in actual["cases"] for step in case["steps"]
    )
    print(f"PASS: touch gesture runtime — {len(actual['cases'])} cases, {actions} actions")


if __name__ == "__main__":
    main()
