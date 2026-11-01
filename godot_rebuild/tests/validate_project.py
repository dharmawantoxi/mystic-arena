#!/usr/bin/env python3
"""Dependency-free guardrails for the native main.py migration."""
from __future__ import annotations

import ast
import json
import operator
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "godot_rebuild"
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


def constant(path: Path, name: str):
    """Read literals or the simple arithmetic used by the source constants."""
    def evaluate(node: ast.AST):
        if isinstance(node, ast.BinOp):
            operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
            return operations[type(node.op)](evaluate(node.left), evaluate(node.right))
        return ast.literal_eval(node)

    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
                return evaluate(node.value)
    raise AssertionError(f"Missing source constant: {path}:{name}")


def gd_constant(path: Path, name: str) -> float:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"^const {name} := ([0-9.]+)$", text, re.MULTILINE)
    check(match is not None, f"Missing GDScript constant: {path}:{name}")
    return float(match.group(1))


def main() -> int:
    project = (PROJECT / "project.godot").read_text(encoding="utf-8")
    presets = (PROJECT / "export_presets.cfg").read_text(encoding="utf-8")
    check('package/unique_name="io.github.dharmawantoxi.mysticarena"' in presets, "Android application ID parity")
    check('architectures/arm64-v8a=true' in presets, "Android ARM64 enabled")
    check('keystore/release_password' not in presets, "No exported signing secrets")
    for key, expected in {
        "config/name": "Mystic Arena",
        "run/main_scene": "res://scenes/Main.tscn",
        "window/size/viewport_width": "1280",
        "window/size/viewport_height": "720",
        'window/stretch/mode': "canvas_items",
        'window/stretch/aspect': "keep",
        "pointing/emulate_touch_from_mouse": "false",
        "pointing/emulate_mouse_from_touch": "false",
        "config/auto_accept_quit": "false",
        "config/quit_on_go_back": "false",
    }.items():
        quoted = not (expected in ("true", "false") or re.fullmatch(r"-?\d+(\.\d+)?", expected))
        pattern = f"{key}=" + (f'"{expected}"' if quoted else expected)
        check(pattern in project, f"Project setting: {key}")
    for scene in PROJECT.rglob("*.tscn"):
        for resource in re.findall(r'path="(res://[^"]+)"', scene.read_text(encoding="utf-8")):
            check((PROJECT / resource[6:]).is_file(), f"Missing scene resource: {resource}")
    main_source = ROOT / "main.py"
    clock = PROJECT / "scripts/core/FixedClock.gd"
    check(abs(1000.0 / gd_constant(clock, "HZ") - constant(main_source, "FIXED_DT_MS")) < 1e-12, "60 Hz source parity")
    check(gd_constant(clock, "MAX_CATCHUP") == constant(main_source, "MAX_CATCHUP"), "Catch-up source parity")
    check(gd_constant(clock, "MAX_FRAME_DELTA") == 0.250, "250 ms stall clamp")
    touch = ROOT / "mobile/touch.py"
    gestures = PROJECT / "scripts/core/GestureTracker.gd"
    for python_name, gd_name, scale in [
        ("TAP_SLOP", "TAP_SLOP", 1),
        ("LONG_PRESS_MS", "LONG_PRESS_SECONDS", 0.001),
        ("DOUBLE_TAP_MS", "DOUBLE_TAP_SECONDS", 0.001),
        ("SCROLL_STEP", "SCROLL_STEP", 1),
        ("FLING_FRICTION", "FLING_FRICTION", 1),
        ("FLING_MIN_SPEED", "FLING_MIN_SPEED", 1),
        ("TAP_SLOP", "TAP_SLOP", 1),
    ]:
        check(abs(gd_constant(gestures, gd_name) - constant(touch, python_name) * scale) < 1e-9,
              f"Gesture source parity: {python_name}")
    catalog = json.loads((PROJECT / "data/levels.json").read_text(encoding="utf-8"))
    check(len(catalog) == 54, "54 level metadata entries")
    check([row["level_number"] for row in catalog] == list(range(1, 55)), "Stable level order")
    check(catalog[0]["name"] == constant(ROOT / "levels/level_data.py", "LEVEL_1")["name"], "Level name parity")
    for path in PROJECT.rglob("*.gd"):
        source = path.read_text(encoding="utf-8")
        check("Engine.has_singleton(\"Python\"" not in source, "No embedded Python assumption")
        for resource in re.findall(r'"(res://[^"]+)"', source):
            if "%" not in resource:
                check((PROJECT / resource[6:]).exists(), f"Missing literal resource in {path.name}: {resource}")
    check((PROJECT / "scripts/Main.gd").is_file(), "Canonical Main.gd entry point exists")
    print(f"PASS: {checks} native project/source checks")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, ValueError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
