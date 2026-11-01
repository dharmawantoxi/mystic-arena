#!/usr/bin/env python3
"""Prepare native _render.py migration artifacts.

Default/--check validates the tracked 54-theme map bakes, themes_raw.json and a
render_data.json contract extracted from _render.py (budgets, timings, easings,
fonts, shop anchors). --bake re-runs the pygame map exporter first; the exporter
swallows exceptions, so this script fails closed if the bake is incomplete.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
RENDER = ROOT / "_render.py"
EXPECTED_THEMES = 54


def _tree() -> ast.Module:
    return ast.parse(RENDER.read_text(encoding="utf-8"))


def _class(tree: ast.Module, name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise AssertionError(f"Missing class {name}")


def _method(node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for item in node.body:
        if isinstance(item, ast.FunctionDef) and item.name == name:
            return item
    raise AssertionError(f"Missing method {node.name}.{name}")


def _self_literals(node: ast.AST, attr: str) -> list:
    values = []
    for item in ast.walk(node):
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) \
                        and target.value.id == "self" and target.attr == attr:
                    try:
                        values.append(ast.literal_eval(item.value))
                    except (ValueError, TypeError):
                        pass
    return values


def _class_constants(node: ast.ClassDef) -> dict:
    result = {}
    for item in node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    result[target.id] = ast.literal_eval(item.value)
    return result


def easing_samples() -> dict:
    tree = _tree()
    samples = {}
    for name in ("_ease_out_back", "_ease_in_back", "_ease_out_cubic", "_ease_out_elastic"):
        func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        namespace = {"math": math}
        module = ast.Module(body=[func], type_ignores=[])
        exec(compile(ast.fix_missing_locations(module), str(RENDER), "exec"), namespace)  # noqa: S102
        samples[name] = [round(namespace[name](t), 9) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
    return samples


def render_contract() -> dict:
    tree = _tree()
    effects = _class_constants(_class(tree, "EffectManager"))
    map_renderer = _method(_class(tree, "MapRenderer"), "__init__")
    font_map = next(
        ast.literal_eval(n.value) for n in tree.body
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_STYLE_FONT_MAP" for t in n.targets)
    )
    bakes = json.loads((PROJECT / "data/map_bakes.json").read_text(encoding="utf-8"))
    themes = json.loads((PROJECT / "data/themes_raw.json").read_text(encoding="utf-8"))["themes"]
    png_sha = {}
    for name, entry in sorted(bakes["maps"].items()):
        path = PROJECT / entry["file"][6:]
        data = path.read_bytes()
        width, height = struct.unpack(">II", data[16:24])
        if (width, height) != (entry["w"], entry["h"]) or (width, height) != (1280, 720):
            raise AssertionError(f"Bad map dimensions: {name} {width}x{height}")
        png_sha[name] = hashlib.sha256(data).hexdigest()
    contract = {
        "_generated_by": "tools/prepare_godot_render.py",
        "_source": "_render.py + map_components/_bundle.py (AST contract, no pygame import)",
        "effect_caps": {k: effects[k] for k in ("MAX_FLOATING", "MAX_PARTICLES", "MAX_EXPLOSIONS")},
        "timings": {
            "combo": _self_literals(_method(_class(tree, "ComboCounter"), "__init__"), "max_timer")[0],
            "wave": _self_literals(_method(_class(tree, "WaveAnnouncer"), "__init__"), "duration")[0],
            "path_preview": _self_literals(_method(_class(tree, "PathPreview"), "__init__"), "duration")[0],
            "achievement": _self_literals(_method(_class(tree, "AchievementPopup"), "__init__"), "duration")[0],
            "boss_intro": _self_literals(_method(_class(tree, "BossIntroCinematic"), "__init__"), "duration")[0],
            "boss_death": sorted(_self_literals(_method(_class(tree, "BossDeathAnimation"), "__init__"), "duration")),
            "celebration": _self_literals(_method(_class(tree, "BossDeathAnimation"), "__init__"), "celebration_duration")[0],
            "level_fade_in": _self_literals(_method(_class(tree, "LevelIntroScreen"), "__init__"), "fade_in_duration")[0],
        },
        "shops": {
            "radiant": _self_literals(map_renderer, "radiant_shop_pos")[0],
            "dire": _self_literals(map_renderer, "dire_shop_pos")[0],
            "size": _self_literals(map_renderer, "shop_size")[0],
        },
        "fonts": font_map,
        "easings": easing_samples(),
        "quality_presets": {
            "low": {"max_damage_numbers": 8, "particle_ratio": 0.35},
            "medium": {"max_damage_numbers": 16, "particle_ratio": 0.65},
            "high": {"max_damage_numbers": 32, "particle_ratio": 1.0},
        },
        "map_bake_seed": bakes["seed"],
        "map_themes": sorted(themes),
        "map_png_sha256": png_sha,
    }
    return json.loads(json.dumps(contract))


def verify_assets() -> None:
    themes = json.loads((PROJECT / "data/themes_raw.json").read_text(encoding="utf-8"))["themes"]
    bakes = json.loads((PROJECT / "data/map_bakes.json").read_text(encoding="utf-8"))["maps"]
    if len(themes) != EXPECTED_THEMES or len(bakes) != EXPECTED_THEMES:
        raise AssertionError(f"Expected {EXPECTED_THEMES} themes/bakes, got {len(themes)}/{len(bakes)}")
    if set(themes) != set(bakes):
        raise AssertionError("themes_raw.json and map_bakes.json disagree")
    levels = json.loads((PROJECT / "data/core_data.json").read_text(encoding="utf-8"))["levels"]
    for level in levels:
        theme = level.get("map_theme", "forest")
        if theme not in bakes:
            raise AssertionError(f"Level {level.get('level_number')} uses unbaked theme {theme}")
    for name, entry in bakes.items():
        path = PROJECT / entry["file"][6:]
        if not path.is_file():
            raise AssertionError(f"Missing map bake: {path}")
        for key in ("river_points", "torch_stones", "radiant_shop", "dire_shop"):
            if key not in entry:
                raise AssertionError(f"Map bake {name} missing dynamic anchor {key}; re-run --bake")


def bake() -> None:
    env = dict(os.environ)
    env["MYSTIC_GODOT_ROOT"] = str(PROJECT)
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    env.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    for flag in ("--map-raw", "--maps-png"):
        subprocess.run([sys.executable, str(ROOT / "tools/convert_to_godot.py"), flag], check=True, env=env)
    verify_assets()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify tracked artifacts; write nothing")
    parser.add_argument("--bake", action="store_true", help="re-bake 54 map PNGs via pygame before verifying")
    args = parser.parse_args()
    if args.bake:
        bake()
    verify_assets()
    contract = render_contract()
    target = PROJECT / "data/render_data.json"
    text = json.dumps(contract, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            parser.exit(1, "Stale render contract; run tools/prepare_godot_render.py\n")
    else:
        target.write_text(text, encoding="utf-8")
    digest = hashlib.sha256(text.encode()).hexdigest()[:12]
    print(f"{'Verified' if args.check else 'Prepared'} render contract: {len(contract['map_themes'])} themes; sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
