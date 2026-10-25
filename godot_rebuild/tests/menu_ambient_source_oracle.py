"""Deterministic source replay for `_core.py` menu ambient fog and particles (9bs).

The real Menu methods are harvested with AST and run against the shared recording pygame
shim. The fixture records all 64 seeded source particles, per-tick wrap RNG calls and snapshots
through 800 source updates, plus the first three particles' exact source draw circles.

Run: `python godot_rebuild/tests/menu_ambient_source_oracle.py`
"""
from __future__ import annotations

import ast
import copy
import json
import math
import random
import types
from pathlib import Path

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_core.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "menu_ambient_source.json"
SIZE = (1280, 720)
TICKS = (1, 60, 300, 800)


class MenuProbe:
    def __init__(self, namespace):
        self._namespace = namespace
        self.screen = rec.Surface(SIZE)
        self._bg_cache = rec.Surface(SIZE)
        self._fog_layers = self._build_menu_fog()
        self.animation_time = 0
        self.particles = []

    def _build_menu_fog(self):
        return self._namespace["_build_menu_fog"](self)

    def _init_particles(self):
        return self._namespace["_init_particles"](self)

    def _update_particles(self):
        return self._namespace["_update_particles"](self)

    def _draw_main_background(self):
        return self._namespace["_draw_main_background"](self)


def _methods() -> dict[str, str]:
    text = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    menu = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Menu")
    wanted = {"_build_menu_fog", "_init_particles", "_update_particles", "_draw_main_background"}
    found = {
        node.name: ast.get_source_segment(text, node)
        for node in menu.body
        if isinstance(node, ast.FunctionDef) and node.name in wanted
    }
    if set(found) != wanted:
        raise AssertionError("missing source ambient methods: %s" % sorted(wanted - set(found)))
    return found


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def source_fixture() -> dict:
    clock = {"ticks": 0}
    pygame = rec.make_pygame(clock)
    perf = rec.make_perf(cheap_alpha=True)
    mobile = types.ModuleType("mobile")
    mobile.perf = perf
    namespace = {
        "pygame": pygame,
        "math": math,
        "random": random,
        "SCREEN_WIDTH": SIZE[0],
        "SCREEN_HEIGHT": SIZE[1],
    }
    for name, segment in _methods().items():
        exec(compile(segment, str(SOURCE), "exec"), namespace)
    menu = MenuProbe(namespace)

    random.seed(2026)
    menu.particles = menu._init_particles()
    initial = copy.deepcopy(menu.particles)
    original_uniform = random.uniform
    wraps_by_tick = []
    for tick in range(1, max(TICKS) + 1):
        wraps = []

        def record_uniform(low, high):
            value = original_uniform(low, high)
            wraps.append(value)
            return value

        random.uniform = record_uniform
        try:
            menu._update_particles()
        finally:
            random.uniform = original_uniform
        wraps_by_tick.append(wraps)
        if tick in TICKS:
            snapshot = copy.deepcopy(menu.particles)
            if "snapshots" not in locals():
                snapshots = []
            snapshots.append({"tick": tick, "particles": _jsonable(snapshot)})

    menu.particles = copy.deepcopy(initial)
    menu.animation_time = 0
    menu.screen = rec.Surface(SIZE)
    with rec.installed({"mobile": mobile, "mobile.perf": perf}):
        menu._draw_main_background()
    particle_ops = menu.screen.ops[-(64 * 2) :]

    return {
        "source": "_core.py::Menu._init_particles/_update_particles/_draw_main_background",
        "seed": 2026,
        "screen_size": list(SIZE),
        "particle_count": len(initial),
        "initial_particles": _jsonable(initial),
        "update_wrap_x": _jsonable(wraps_by_tick),
        "snapshots": snapshots,
        "draw": {
            "tick": 0,
            "fog_layers": len(menu._fog_layers),
            "fog_circle_ops": sum(len(fog.ops) for fog, _speed, _alpha in menu._fog_layers),
            "particle_circle_ops": len(particle_ops),
            "first_three_particles": _jsonable(particle_ops[:6]),
        },
    }


def main() -> None:
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%d particles, %d ticks)" % (FIXTURE.relative_to(ROOT), fixture["particle_count"], len(fixture["update_wrap_x"])))


if __name__ == "__main__":
    main()
