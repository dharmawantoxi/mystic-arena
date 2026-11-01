#!/usr/bin/env python3
"""Prepare native _system.py migration contract (AST-only, no pygame import).

Extracts performance constants (SpatialGrid/FrustumCuller/FPSCounter/
AdaptiveQuality), SoundManager volumes/throttle/load manifest, and SaveManager
slot/level-stat defaults into godot_rebuild/data/system_data.json. --check is a
fail-closed staleness gate for CI.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
SYSTEM = ROOT / "_system.py"


def _tree() -> ast.Module:
    return ast.parse(SYSTEM.read_text(encoding="utf-8"))


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


def _self_assign(node: ast.AST, attr: str):
    for item in ast.walk(node):
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) \
                        and target.value.id == "self" and target.attr == attr:
                    return ast.literal_eval(item.value)
    raise AssertionError(f"Missing self.{attr}")


def _module_assign(tree: ast.Module, name: str):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"Missing module constant {name}")


def sound_manifest(tree: ast.Module) -> list[dict]:
    load_all = _method(_class(tree, "SoundManager"), "load_all")
    entries = []
    for node in ast.walk(load_all):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "load" and isinstance(node.func.value, ast.Name) \
                and node.func.value.id == "self":
            name = ast.literal_eval(node.args[0])
            filename = ast.literal_eval(node.args[1])
            category = ast.literal_eval(node.args[2]) if len(node.args) > 2 else "sfx"
            entries.append({"name": name, "file": filename, "category": category})
    if not entries:
        raise AssertionError("SoundManager.load_all manifest empty")
    return entries


def system_contract() -> dict:
    tree = _tree()
    text = SYSTEM.read_text(encoding="utf-8")
    frustum = _class(tree, "FrustumCuller")
    margin = next(ast.literal_eval(n.value) for n in frustum.body
                  if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MARGIN" for t in n.targets))
    grid_call = next(n for n in tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "_grid" for t in n.targets))
    cell_size = next(ast.literal_eval(kw.value) for kw in grid_call.value.keywords if kw.arg == "cell_size")
    fps_init = _method(_class(tree, "FPSCounter"), "__init__")
    adaptive_init = _method(_class(tree, "AdaptiveQuality"), "_init")
    sound_init = _method(_class(tree, "SoundManager"), "__init__")
    window = re.search(r"self\.fps_history\[-(\d+):\]", text)
    refresh = re.search(r"self\.frame_count >= (\d+)", text)
    if not window or not refresh:
        raise AssertionError("FPSCounter display window/refresh not found")
    empty_save = _method(_class(tree, "SaveManager"), "get_empty_save")
    empty_dict = next(n.value for n in ast.walk(empty_save) if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict))
    empty_keys = [ast.literal_eval(k) for k in empty_dict.keys]
    level_stats = _method(_class(tree, "SaveManager"), "get_level_stats")
    stats_dict = next(n.value for n in ast.walk(level_stats) if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict))
    stats_defaults = {ast.literal_eval(k): ast.literal_eval(v) for k, v in zip(stats_dict.keys, stats_dict.values)}
    contract = {
        "_generated_by": "tools/prepare_godot_system.py",
        "_source": "_system.py (AST contract, no pygame import)",
        "performance": {
            "frustum_margin": margin,
            "screen": [1280, 720],
            "spatial_cell_size": cell_size,
            "fps_history_size": _self_assign(fps_init, "history_size"),
            "fps_display_window": int(window.group(1)),
            "fps_refresh_frames": int(refresh.group(1)),
            "adaptive_history_size": _self_assign(adaptive_init, "history_size"),
            "adaptive_high_threshold": _self_assign(adaptive_init, "HIGH_THRESHOLD"),
            "adaptive_medium_threshold": _self_assign(adaptive_init, "MEDIUM_THRESHOLD"),
        },
        "audio": {
            "channels": 32,
            "volumes": {
                "master": _self_assign(sound_init, "master_volume"),
                "sfx": _self_assign(sound_init, "sfx_volume"),
                "voice": _self_assign(sound_init, "voice_volume"),
                "bgm": _self_assign(sound_init, "bgm_volume"),
                "ambient": _self_assign(sound_init, "ambient_volume"),
            },
            "throttle_ms": _self_assign(sound_init, "throttle_ms"),
            "default_throttle_ms": 50,
            "positional_max_distance": 800,
            "positional_min_volume": 0.15,
            "manifest": sound_manifest(tree),
        },
        "save": {
            "num_slots": _module_assign(tree, "NUM_SLOTS"),
            "empty_save_keys": empty_keys,
            "level_stats_defaults": stats_defaults,
        },
    }
    return json.loads(json.dumps(contract))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify tracked contract; write nothing")
    args = parser.parse_args()
    contract = system_contract()
    target = PROJECT / "data/system_data.json"
    text = json.dumps(contract, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            parser.exit(1, "Stale system contract; run tools/prepare_godot_system.py\n")
    else:
        target.write_text(text, encoding="utf-8")
    digest = hashlib.sha256(text.encode()).hexdigest()[:12]
    print(f"{'Verified' if args.check else 'Prepared'} system contract: "
          f"{len(contract['audio']['manifest'])} sounds, {contract['save']['num_slots']} slots; sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
