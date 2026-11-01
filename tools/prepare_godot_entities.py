#!/usr/bin/env python3
"""Prepare native _entity.py migration artifacts.

Generated GDScript kits are transpiled from the Python skill/boss sources by the
existing generators, then adapted to the RefCounted BattleUnit API. Sprite bake
is optional (--bake) because it needs pygame-ce/numpy; tracked PNG manifests are
validated by default so normal CI does not need a display stack.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
OUT = PROJECT / "scripts" / "entities" / "generated"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _adapt(text: str) -> str:
    # BattleUnit keeps pygame-style frame units. The legacy node generators used
    # seconds for attack_cooldown and px/s for move_speed; expose compatibility
    # properties on BattleUnit and rewrite only the cooldown field name.
    text = text.replace(".global_position", ".pos")
    text = text.replace(".attack_cooldown", ".attack_cooldown_seconds")
    return text.rstrip() + "\n"


def kits() -> dict[str, str]:
    hero = _load("mystic_gen_hero_skill", ROOT / "tools/gen_hero_skill_kit.py")
    boss = _load("mystic_gen_boss_ai", ROOT / "tools/gen_boss_smart_ai.py")
    hero_text, _keys, _registry = hero.emit_all()
    boss_text, _smart, _helpers = boss.generate()
    return {
        "HeroSkillKit.gd": _adapt(hero_text),
        "BossKit.gd": _adapt(boss_text),
    }


def manifest_summary() -> dict:
    units = json.loads((PROJECT / "data/baked_units.json").read_text(encoding="utf-8"))
    props = json.loads((PROJECT / "data/baked_props.json").read_text(encoding="utf-8"))
    return {
        "units": len(units.get("units", {})),
        "minions": len(props.get("minions", {})),
        "towers": len(props.get("towers", {})),
        "nexus": len(props.get("nexus", {})),
    }


def bake() -> None:
    import os
    import subprocess

    env = dict(os.environ)
    env["MYSTIC_GODOT_ROOT"] = str(PROJECT)
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    env.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    for flag in ("--units-png", "--props-png"):
        subprocess.run([sys.executable, str(ROOT / "tools/convert_to_godot.py"), flag],
                       check=True, env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--bake", action="store_true", help="re-bake sprites from Python renderers")
    args = parser.parse_args()
    if args.bake:
        bake()
    generated = kits()
    stale = []
    for name, text in generated.items():
        target = OUT / name
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != text:
                stale.append(str(target.relative_to(ROOT)))
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
    summary = manifest_summary()
    if summary["units"] < 222 or summary["minions"] < 10 or summary["towers"] < 8 or summary["nexus"] < 2:
        parser.exit(1, f"Incomplete entity sprite manifests: {summary}; run --bake\n")
    if args.check and stale:
        parser.exit(1, "Stale entity kits: " + ", ".join(stale) + "; run tools/prepare_godot_entities.py\n")
    digest = hashlib.sha256("".join(generated.values()).encode()).hexdigest()[:12]
    print(f"{'Verified' if args.check else 'Prepared'} entity kits: {len(generated)} files; "
          f"sprites={summary}; sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
