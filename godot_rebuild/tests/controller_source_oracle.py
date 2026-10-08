#!/usr/bin/env python3
"""Read-only behavioral oracle for the Pygame controller gameplay runtime.

The real ``ControllerManager`` class is compiled from ``_core.py`` without
importing pygame. A source-shaped joystick then drives cursor acceleration,
button edges, D-pad repeat, trigger edges, right-stick scrolling, snapping,
and context hints. The gameplay action vocabulary is read from the real
``main_desktop_legacy.py`` controller branch.
"""
from __future__ import annotations

import ast
from contextlib import redirect_stdout
from io import StringIO
import json
import math
from pathlib import Path
import re
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).with_name("fixtures") / "controller_source.json"


class FakeJoystick:
    def __init__(self, buttons: int = 16, axes: int = 6):
        self.buttons = [0] * buttons
        self.axes = [0.0] * axes
        self.hat = (0, 0)
        self.rumbles = []
        self.stops = 0

    def get_numbuttons(self):
        return len(self.buttons)

    def get_button(self, index):
        return self.buttons[index]

    def get_numaxes(self):
        return len(self.axes)

    def get_axis(self, index):
        return self.axes[index]

    def get_numhats(self):
        return 1

    def get_hat(self, _index):
        return self.hat

    def rumble(self, low, high, duration):
        self.rumbles.append([low, high, duration])

    def stop_rumble(self):
        self.stops += 1


class Rect:
    def __init__(self, centerx, centery):
        self.centerx = centerx
        self.centery = centery


def _source_namespace():
    tree = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    wanted = {"InputMode", "XBOX_MAP", "PS_MAP", "GENERIC_MAP", "ControllerManager"}
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name in wanted:
            nodes.append(node)
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in wanted for target in node.targets
        ):
            nodes.append(node)
    assert len(nodes) == 5
    env = {
        "math": math,
        "SCREEN_WIDTH": 1280,
        "SCREEN_HEIGHT": 720,
        # Only unused initialization/rescan methods touch pygame.
        "pygame": SimpleNamespace(),
    }
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, "<source ControllerManager>", "exec"), env)
    return env


def _manager(env, mapping="XBOX_MAP"):
    manager = env["ControllerManager"]()
    manager.active_mode = env["InputMode"].CONTROLLER
    manager.connected = True
    manager.cursor_visible = True
    manager.controller_type = {
        "XBOX_MAP": "xbox",
        "PS_MAP": "ps",
        "GENERIC_MAP": "generic",
    }[mapping]
    manager.button_map = env[mapping].copy()
    manager.joystick = FakeJoystick()
    manager._prev_buttons = {
        index: False for index in range(manager.joystick.get_numbuttons())
    }
    return manager


def _rounded_point(manager):
    return [round(manager.cursor_x, 6), round(manager.cursor_y, 6)]


def _cursor_cases(env):
    specs = (
        ("inside_deadzone", 0.24, -0.24, 1),
        ("deadzone_boundary", 0.25, 0.0, 1),
        ("half_horizontal", 0.5, 0.0, 1),
        ("half_diagonal", 0.5, -0.5, 1),
        ("full_horizontal", 1.0, 0.0, 1),
        ("clamp_bottom_right", 1.0, 1.0, 40),
    )
    rows = []
    for label, axis_x, axis_y, frames in specs:
        manager = _manager(env)
        manager.joystick.axes[0] = axis_x
        manager.joystick.axes[1] = axis_y
        for _ in range(frames):
            manager.update()
        rows.append(
            {
                "label": label,
                "axes": [axis_x, axis_y],
                "frames": frames,
                "position": _rounded_point(manager),
                "integer_position": list(manager.get_cursor_pos()),
            }
        )
    return rows


def _button_cases(env):
    rows = []
    names = (
        "confirm",
        "cancel",
        "skill_q",
        "skill_w",
        "skill_e",
        "skill_r",
        "start",
        "back",
        "stick_left",
        "stick_right",
    )
    for mapping in ("XBOX_MAP", "PS_MAP", "GENERIC_MAP"):
        for action in names:
            manager = _manager(env, mapping)
            button = manager.button_map[action]
            manager.joystick.buttons[button] = 1
            pressed = manager.get_pressed_actions()
            held = manager.get_pressed_actions()
            manager.joystick.buttons[button] = 0
            released = manager.get_pressed_actions()
            manager.joystick.buttons[button] = 1
            repressed = manager.get_pressed_actions()
            rows.append(
                {
                    "mapping": mapping.removesuffix("_MAP").lower(),
                    "action": action,
                    "button": button,
                    "sequence": [pressed, held, released, repressed],
                }
            )
    return rows


def _dpad_cases(env):
    rows = []
    for label, hat in (
        ("up", (0, 1)),
        ("down", (0, -1)),
        ("left", (-1, 0)),
        ("right", (1, 0)),
        ("up_right", (1, 1)),
    ):
        manager = _manager(env)
        manager.joystick.hat = hat
        events = []
        for frame in range(31):
            actions = manager.get_pressed_actions()
            if actions:
                events.append({"frame": frame, "actions": actions})
        manager.joystick.hat = (0, 0)
        manager.get_pressed_actions()
        manager.joystick.hat = hat
        events.append({"frame": "repress", "actions": manager.get_pressed_actions()})
        rows.append({"label": label, "hat": list(hat), "events": events})
    return rows


def _trigger_case(env):
    manager = _manager(env)
    left = manager.button_map["left_trigger"]
    right = manager.button_map["right_trigger"]
    samples = (
        (0.5, 0.5),
        (0.51, 0.5),
        (0.8, 0.75),
        (0.0, 0.75),
        (0.51, 0.0),
        (0.51, 0.51),
    )
    rows = []
    for lt_value, rt_value in samples:
        manager.joystick.axes[left] = lt_value
        manager.joystick.axes[right] = rt_value
        rows.append(
            {
                "axes": [lt_value, rt_value],
                "actions": manager.get_pressed_actions(),
            }
        )
    return rows


def _scroll_cases(env):
    rows = []
    for label, mapped, alternate, frames in (
        ("deadzone", 0.18, 0.0, 5),
        ("positive_half", 0.5, 0.0, 12),
        ("negative_full", -0.9, 0.0, 8),
        ("alternate_axis", -1.0, 0.6, 8),
    ):
        manager = _manager(env)
        manager.joystick.axes[3] = mapped
        manager.joystick.axes[2] = alternate
        events = []
        for frame in range(frames):
            actions = manager.get_pressed_actions()
            if actions:
                events.append({"frame": frame, "actions": actions})
        rows.append(
            {
                "label": label,
                "mapped": mapped,
                "alternate": alternate,
                "events": events,
                "resolved_axis": manager._scroll_axis,
                "accumulator": round(manager._scroll_accum, 6),
            }
        )
    return rows


def _snap_cases(env):
    rows = []
    for start in ((0, 0), (600, 300), (1280, 720)):
        manager = _manager(env)
        manager.cursor_x, manager.cursor_y = start
        controls = {
            "left": Rect(100, 100),
            "middle": Rect(640, 360),
            "right": Rect(1180, 620),
        }
        manager.snap_to_nearest_button(controls)
        rows.append({"start": list(start), "position": _rounded_point(manager)})
    return rows


def _gameplay_actions():
    source = (ROOT / "main_desktop_legacy.py").read_text(encoding="utf-8")
    start = source.index("                elif current_state == STATE_GAME:")
    end = source.index("                # ─── PAUSE ───", start)
    block = source[start:end]
    names = set(re.findall(r"action == ['\"]([^'\"]+)['\"]", block))
    for tuple_body in re.findall(r"action in \(([^\n]+)\)", block):
        names.update(re.findall(r"['\"]([^'\"]+)['\"]", tuple_body))
    return sorted(names)


def source_fixture():
    env = _source_namespace()
    sample = _manager(env)
    maps = {
        key.removesuffix("_MAP").lower(): env[key]
        for key in ("XBOX_MAP", "PS_MAP", "GENERIC_MAP")
    }
    # The real source announces auto-detected fallback axes. Keep oracle output
    # stable while still executing those exact branches.
    with redirect_stdout(StringIO()):
        trigger_rows = _trigger_case(env)
        scroll_rows = _scroll_cases(env)
    return {
        "policy": {
            "screen": [1280, 720],
            "cursor_speed": sample.cursor_speed,
            "cursor_max_speed": sample.cursor_max_speed,
            "cursor_acceleration": sample.cursor_acceleration,
            "deadzone": sample.deadzone,
            "hat_repeat_delay": sample.hat_repeat_delay,
            "hat_repeat_rate": sample.hat_repeat_rate,
            "scroll_step": sample.scroll_step,
            "scroll_speed": sample.scroll_speed,
            "scroll_deadzone": sample.scroll_deadzone,
            "trigger_threshold": 0.5,
            "gameplay_actions": _gameplay_actions(),
            "maps": maps,
        },
        "cursor": _cursor_cases(env),
        "buttons": _button_cases(env),
        "dpad": _dpad_cases(env),
        "triggers": trigger_rows,
        "scroll": scroll_rows,
        "snap": _snap_cases(env),
        "hints": {
            context: [list(row) for row in sample.get_hints(context)]
            for context in ("game", "shop", "pause", "victory", "defeat")
        },
    }


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    else:
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
        if actual != expected:
            raise SystemExit("FAIL: controller source fixture drift")
    print(
        "PASS: controller runtime — "
        f"{len(actual['cursor'])} cursor, {len(actual['buttons'])} button, "
        f"{len(actual['dpad'])} D-pad and {len(actual['scroll'])} scroll cases"
    )


if __name__ == "__main__":
    main()
