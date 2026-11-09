#!/usr/bin/env python3
"""Execute heroes/combat_feel.py itself to produce native bus parity fixtures.

Only the SDL clock is replaced. No package import, pygame rendering or copied
combat formulas are involved. --check never writes.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "heroes/combat_feel.py"
OUTPUT = ROOT / "godot_rebuild/tests/fixtures/hero_combat_feel.json"


def oracle():
    clock = [0]
    pygame = types.ModuleType("pygame")
    pygame.time = types.SimpleNamespace(get_ticks=lambda: clock[0])
    spec = importlib.util.spec_from_file_location("mystic_combat_feel_oracle", SOURCE)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"pygame": pygame}):
        spec.loader.exec_module(module)
    return module, clock


def scenarios():
    return [
        {"name": "duration bounds and no stacking", "actions": [
            ["hit_stop", 0.001], ["hit_stop", 0.08], ["hit_stop", 0.03],
            ["freeze"], ["freeze"], ["freeze"], ["freeze"], ["freeze"], ["freeze"]]},
        {"name": "python ties to even", "actions": [
            ["hit_stop", 2.5 / 60], ["freeze"], ["reset"], ["hit_stop", 4.5 / 60]]},
        {"name": "invalid and coercion", "actions": [
            ["hit_stop", "bad"], ["hit_stop", None], ["hit_stop", "0.05"],
            ["reset"], ["hit_stop", False], ["reset"], ["hit_stop", True]]},
        {"name": "master switch", "actions": [
            ["hit_stop", 0.08], ["hit_stop_enabled", False], ["freeze"],
            ["hit_stop", 0.08], ["hit_stop_enabled", True], ["freeze"]]},
        {"name": "clock caching and slow motion", "actions": [
            ["shake", 8.0, 0.22, False], ["frame_dt", 100], ["frame_dt", 101],
            ["frame_dt", 101], ["hit_stop", 0.08], ["fx_dt", 117],
            ["fx_dt", 117], ["frame_dt", 1000], ["reset"], ["frame_dt", 2000]]},
        {"name": "shake threshold scaling and reset", "actions": [
            ["shake", 3.9, 0.22, False], ["shake", 8.0, 0.22, False],
            ["shake", 4.0, 0.1, False], ["update_shake", 0.05],
            ["add_shake", 2.0, 0.5], ["update_shake", 0.2],
            ["update_shake", 0.5], ["reset"]]},
        {"name": "disabled shake", "actions": [
            ["shake_enabled", False], ["shake", 10.0, 0.5, False],
            ["add_shake", 20.0, 1.0], ["shake_enabled", True],
            ["add_shake", 4.0, 0.4], ["add_shake", -1.0, 1.0],
            ["add_shake", 5.0, 0.0], ["update_shake", 0.4]]},
    ]


def build():
    cases = scenarios()
    for case in cases:
        bus, clock = oracle()
        case["expected"] = []
        for name, *args in case["actions"]:
            result = None
            if name in ("frame_dt", "fx_dt"):
                clock[0] = args[0]
                result = getattr(bus, name)()
            elif name == "freeze":
                result = bus.should_freeze_frame()
            elif name == "hit_stop_enabled":
                bus.HIT_STOP_ENABLED = args[0]
            elif name == "shake_enabled":
                bus.SHAKE.enabled = args[0]
            elif name == "update_shake":
                bus.SHAKE.update(*args)
            elif name == "add_shake":
                bus.SHAKE.add(*args)
            else:
                getattr(bus, name)(*args)
            case["expected"].append({
                "result": result, "stats": bus.stats(), "progress": bus.HITSTOP.progress,
                "shake_strength": bus.SHAKE.shake_strength,
                "shake_duration": bus.SHAKE.shake_duration,
                "max_duration": bus.SHAKE._max_duration,
            })
    return {"schema": 1, "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(build(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            parser.exit(1, "combat feel oracle drift; regenerate fixture\n")
    else:
        OUTPUT.write_text(text)
    print("hero combat feel Python oracle OK")


if __name__ == "__main__":
    main()
