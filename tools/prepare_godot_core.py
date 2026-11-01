#!/usr/bin/env python3
"""Export _core.py data for the native Godot core without importing pygame.

Pure data modules are read with AST/importlib; no game runtime is started and
no Python save file is written. Regenerate after changing source balance data.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import operator
from pathlib import Path
import types
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "godot_rebuild" / "data"


def _eval(node: ast.AST, names: dict):
    if isinstance(node, ast.Name):
        return names[node.id]
    if isinstance(node, ast.Dict):
        return {_eval(k, names): _eval(v, names) for k, v in zip(node.keys, node.values)}
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = [_eval(v, names) for v in node.elts]
        return tuple(values) if isinstance(node, ast.Tuple) else values
    if isinstance(node, ast.BinOp):
        ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
               ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}
        return ops[type(node.op)](_eval(node.left, names), _eval(node.right, names))
    if isinstance(node, ast.UnaryOp):
        return {ast.UAdd: operator.pos, ast.USub: operator.neg, ast.Not: operator.not_}[type(node.op)](_eval(node.operand, names))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("dict", "tuple", "list"):
        value = [_eval(a, names) for a in node.args]
        return {"dict": dict, "tuple": tuple, "list": list}[node.func.id](value[0] if value else [])
    return ast.literal_eval(node)


def assignments(path: Path, *, upper_only: bool = False, include_private: bool = False) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {"math": math}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if not targets or (upper_only and not all(t.isupper() or t.startswith("DEV_") for t in targets)):
            continue
        try:
            value = _eval(node.value, names)
        except (ValueError, KeyError, TypeError, SyntaxError):
            continue
        for target in targets:
            names[target] = value
    return {k: v for k, v in names.items() if k != "math" and (include_private or not k.startswith("_"))}


def _module(name: str, path: Path):
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw_hero_catalog(core: dict) -> dict:
    """Assemble the playable catalog before hero_balance.apply_to_catalog().

    Kept separate so the native balance migration can oracle the exact same
    pre-balance input that prepare_godot_core.py balances for core_data.json.
    """
    bosses = _module("mystic_boss_data", ROOT / "bosses/boss_data.py")
    catalog = {key: dict(value) for key, value in core["HERO_TYPES"].items()}
    for value in catalog.values():
        value.update(is_boss_hero=False, unlock_require_boss=None, unlock_cost=0)
    for kind, table in (("mini", bosses.MINI_BOSS_TYPES), ("true", bosses.TRUE_BOSS_TYPES)):
        for key, boss in table.items():
            unlock = boss.get("hero_unlock")
            if not unlock:
                continue
            catalog[key] = dict(unlock, is_boss_hero=True, boss_class=kind,
                                unlock_require_boss=key, unlock_cost=4500,
                                source_boss_name=boss.get("name", key.title()))
    return catalog


def hero_catalog(core: dict) -> dict:
    catalog = raw_hero_catalog(core)
    # The balance module is pure Python and is the authoritative final pass.
    balance = _module("mystic_hero_balance", ROOT / "hero_balance.py")
    balance.apply_to_catalog(catalog)
    return catalog


def boss_catalog() -> dict:
    bosses = _module("mystic_boss_data", ROOT / "bosses/boss_data.py")
    return {"mini": bosses.MINI_BOSS_TYPES, "true": bosses.TRUE_BOSS_TYPES,
            "level_true_boss": bosses.LEVEL_TRUE_BOSS}


def item_catalog() -> dict:
    names = assignments(ROOT / "hero_items.py")
    return names["ITEM_CATALOG"]


def lane_paths() -> dict:
    tree = ast.parse((ROOT / "map_components/_bundle.py").read_text(encoding="utf-8"))
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "PathGenerator")
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "<PathGenerator>", "exec"), namespace)
    namespace["_NS_generators"] = types.SimpleNamespace(PathGenerator=namespace["PathGenerator"])
    gen = namespace["PathGenerator"]
    top, mid, bot = gen.generate_lanes(1280, 720)
    return {"top": top, "mid": mid, "bot": bot, "river": gen.generate_river(1280, 720)}


def build() -> dict:
    core = assignments(ROOT / "_core.py", upper_only=True)
    levels = assignments(ROOT / "levels/level_data.py", upper_only=True)
    level_rows = [levels[f"LEVEL_{i}"] for i in range(1, 55)]
    localization = assignments(ROOT / "localization.py", include_private=True)
    currency = assignments(ROOT / "topup_currency.py", upper_only=True)
    return {
        "schema": 1,
        "source": "_core.py",
        "rules": core,
        "levels": level_rows,
        "heroes": hero_catalog(core),
        "bosses": boss_catalog(),
        "items": item_catalog(),
        "lanes": lane_paths(),
        "localization": localization["_TEXT"],
        "currency": currency,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = build()
    text = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    target = OUT / "core_data.json"
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            parser.exit(1, "Stale core_data.json; run tools/prepare_godot_core.py\n")
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    print(f"{'Verified' if args.check else 'Prepared'} core data: {len(data['levels'])} levels, "
          f"{len(data['heroes'])} heroes, {len(data['bosses']['mini']) + len(data['bosses']['true'])} bosses, "
          f"{len(data['items'])} items; sha256={hashlib.sha256(text.encode()).hexdigest()[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
