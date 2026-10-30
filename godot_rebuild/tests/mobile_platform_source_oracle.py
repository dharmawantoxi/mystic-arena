#!/usr/bin/env python3
"""Read-only source oracle for ``mobile/platform_utils.py`` (layer 9bv20).

The source module is compiled from its AST with a pygame shim (only ``Rect``
and ``pygame.display.get_window_size`` are needed) plus a fake writable
directory, so the REAL functions run:

* ``_refresh_display_metrics`` - scale / letterbox offset from the real window
* ``window_to_logical`` / ``finger_to_logical`` / ``pointer_to_logical``
* ``get_safe_area`` - notch / gesture-bar insets in 1280x720 logical space
* ``panel_popup_pos`` / ``panel_pos_bawah`` - right-panel popup routing
* ``load_display_mode`` / ``save_display_mode`` - persisted display mode

No pygame runtime, jnius or legacy module is imported, and the Pygame source
tree is never modified.

Run:
    python godot_rebuild/tests/mobile_platform_source_oracle.py            # verify
    python godot_rebuild/tests/mobile_platform_source_oracle.py --write    # refresh
"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mobile" / "platform_utils.py"
FIXTURE = Path(__file__).with_name("fixtures") / "mobile_platform_source.json"

WINDOWS = [(1280, 720), (1624, 720), (2436, 1080), (1920, 1080), (1024, 768), (800, 480)]
PANEL = (1280, 0, 344, 720)
POPUPS = [(316, 165, 12), (336, 165, 12), (344, 165, 12), (260, 200, 12), (316, 600, 12)]


class Rect:
    def __init__(self, *args):
        if len(args) == 1:
            args = tuple(args[0])
        self.x, self.y, self.width, self.height = [int(value) for value in args]

    right = property(lambda self: self.x + self.width)
    bottom = property(lambda self: self.y + self.height)
    center = property(lambda self: (self.x + self.width // 2, self.y + self.height // 2))

    def tuple(self):
        return (self.x, self.y, self.width, self.height)


class _Display:
    def __init__(self):
        self.window_size = (1280, 720)

    def get_window_size(self):
        return self.window_size


class _Surface:
    def __init__(self, size):
        self._size = tuple(size)

    def get_size(self):
        return self._size


def _source_namespace(workdir: Path):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    constants = {
        "LOGICAL_WIDTH",
        "LOGICAL_HEIGHT",
        "DISPLAY_MODES",
        "ZONA_POPUP_Y",
        "ZONA_BAWAH_H",
        "_SAFE_MARGIN_LOGICAL",
        "_display_state",
    }
    functions = {
        "_mode_file",
        "get_writable_dir",
        "load_display_mode",
        "save_display_mode",
        "_refresh_display_metrics",
        "window_to_logical",
        "finger_to_logical",
        "pointer_to_logical",
        "get_safe_area",
        "panel_popup_pos",
        "panel_pos_bawah",
    }
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in constants for target in node.targets
        ):
            nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in functions:
            nodes.append(node)
    assert len(nodes) == len(constants) + len(functions), (len(nodes), constants, functions)

    pygame = type(sys)("pygame")
    pygame.Rect = Rect
    pygame.display = _Display()
    pygame.version = type(sys)("pygame.version")
    pygame.version.ver = "2.6.1-oracle"
    pygame.get_sdl_version = lambda: (2, 30, 0)
    pygame.Surface = _Surface
    pygame.error = type("error", (Exception,), {})

    env = {
        "pygame": pygame,
        "os": os,
        "sys": sys,
        "__file__": str(workdir / "main.py"),
        "IS_ANDROID": False,
        "IS_DESKTOP": True,
        "TOUCH_MODE": True,
        "FORCE_TOUCH": True,
    }
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, "<source platform_utils>", "exec"), env)
    return env


def _round(value):
    return round(float(value), 6)


def _point(values):
    return [_round(values[0]), _round(values[1])]


def _maybe_point(values):
    return None if values is None else _point(values)


def source_fixture():
    with tempfile.TemporaryDirectory() as raw_dir:
        workdir = Path(raw_dir)
        env = _source_namespace(workdir)
        display = env["pygame"].display
        state = env["_display_state"]

        refresh = []
        for window in WINDOWS:
            display.window_size = window
            state["window_size"] = window
            env["_refresh_display_metrics"](_Surface(window))
            refresh.append(
                {
                    "window": list(window),
                    "scale": _round(state["scale"]),
                    "offset": _point(state["offset"]),
                }
            )

        conversions = []
        for row in refresh:
            window = row["window"]
            display.window_size = tuple(window)
            state["window_size"] = tuple(window)
            state["scale"] = row["scale"]
            state["offset"] = tuple(row["offset"])
            points = [
                (0.0, 0.0),
                (1.0, 1.0),
                (float(window[0]) / 2.0, float(window[1]) / 2.0),
                (float(window[0]), float(window[1])),
                (float(window[0]) * 1.5, float(window[1]) * 0.25),
            ]
            conversions.append(
                {
                    "window": window,
                    "window_points": [
                        {
                            "window": _point(point),
                            "logical": _point(env["window_to_logical"](*point)),
                        }
                        for point in points
                    ],
                    "finger_points": [
                        {
                            "finger": [_round(fx), _round(fy)],
                            "logical": _point(env["finger_to_logical"](fx, fy)),
                        }
                        for fx, fy in ((0.5, 0.5), (0.25, 0.75), (1.0, 1.0))
                    ],
                }
            )

        pointer = []
        for mode in ("native", "scaled_vsync", "scaled"):
            state["mode"] = mode
            display.window_size = (2436, 1080)
            state["window_size"] = (2436, 1080)
            state["scale"] = 1.5
            state["offset"] = (258.0, 0.0)
            pointer.append(
                {
                    "mode": mode,
                    "points": [
                        {
                            "input": _point(point),
                            "logical": _point(env["pointer_to_logical"](point)),
                        }
                        for point in ((0.0, 0.0), (640.0, 360.0), (1300.0, 700.0))
                    ],
                }
            )

        safe_areas = []
        for touch in (True, False):
            env["TOUCH_MODE"] = touch
            safe_areas.append({"touch_mode": touch, "rect": list(env["get_safe_area"]().tuple())})

        panel = Rect(PANEL)
        state["panel"] = panel
        popups = []
        for width, height, top in POPUPS:
            popups.append(
                {
                    "width": width,
                    "height": height,
                    "top": top,
                    "popup_pos": _maybe_point(_as_tuple(env["panel_popup_pos"](width, height, top))),
                    "bottom_pos": _maybe_point(_as_tuple(env["panel_pos_bawah"](width, height))),
                }
            )
        state["panel"] = None
        popups.append(
            {
                "width": 316,
                "height": 165,
                "top": 12,
                "popup_pos": None,
                "bottom_pos": None,
            }
        )

        mode_file = env["_mode_file"]()
        modes = []
        for env_mode, file_text in (
            ("native", None),
            ("scaled", "native"),
            (None, "scaled"),
            (None, "bogus"),
            ("bogus", None),
            (None, None),
        ):
            if file_text is None:
                if Path(mode_file).exists():
                    Path(mode_file).unlink()
            else:
                Path(mode_file).write_text(file_text, encoding="utf-8")
            if env_mode is None:
                os.environ.pop("MYSTIC_DISPLAY_MODE", None)
            else:
                os.environ["MYSTIC_DISPLAY_MODE"] = env_mode
            modes.append(
                {
                    "env": env_mode,
                    "file": file_text,
                    "resolved": env["load_display_mode"](),
                }
            )
        os.environ.pop("MYSTIC_DISPLAY_MODE", None)

        save_rows = []
        for mode in ("scaled", "native", "nonsense"):
            saved = bool(env["save_display_mode"](mode))
            reloaded = env["load_display_mode"]()
            save_rows.append({"save": mode, "ok": saved, "reloaded": reloaded})
        saved_file = Path(mode_file).read_text(encoding="utf-8") if Path(mode_file).exists() else None
        if Path(mode_file).exists():
            Path(mode_file).unlink()

        return {
            "source": "mobile/platform_utils.py",
            "logical_size": [env["LOGICAL_WIDTH"], env["LOGICAL_HEIGHT"]],
            "display_modes": list(env["DISPLAY_MODES"]),
            "default_mode": env["load_display_mode"](),
            "safe_margin": env["_SAFE_MARGIN_LOGICAL"],
            "zona_popup_y": env["ZONA_POPUP_Y"],
            "zona_bawah_h": env["ZONA_BAWAH_H"],
            "refresh": refresh,
            "conversions": conversions,
            "pointer": pointer,
            "safe_area": safe_areas,
            "panel": list(panel.tuple()),
            "popups": popups,
            "display_mode": modes,
            "save_mode": save_rows,
            "saved_file": saved_file,
        }


def _as_tuple(value):
    if value is None:
        return None
    if hasattr(value, "tuple"):
        return value.tuple()
    return tuple(value)


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {FIXTURE}")
        return
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if actual != expected:
        raise SystemExit("FAIL: mobile platform source fixture drift")
    print(
        "PASS: mobile platform — %d windows, %d popup cases, %d display modes"
        % (len(actual["refresh"]), len(actual["popups"]), len(actual["display_mode"]))
    )


if __name__ == "__main__":
    main()
