"""Source oracle and deterministic data generator for `DynamicRenderer` (layer 9d0).

The real class and its true-boss overrides are harvested from
`map_components/_bundle.py` with AST and executed under the shared recording
pygame shim. Off-screen fog/glow/smoke/torch surfaces are flattened by the
recorder, so fixtures contain final screen-space primitives in source order.

Two deterministic artifacts are written:
* `data/art/map_dynamic.json`: source theme data, the seed-42 decoration layout,
  and initial particle/fog state for all 54 themes at LOW/MEDIUM/HIGH.
* `tests/fixtures/dynamic_renderer_source.json`: initial state, random replay,
  post-update state and draw ops for every particle family, boss environment,
  quality preset, and every torch palette branch.

No pygame installation is required and the Python source is never modified.

Run: python godot_rebuild/tests/dynamic_renderer_source_oracle.py
"""
from __future__ import annotations

import ast
import copy
import json
import math
import random
import types
from pathlib import Path
from types import SimpleNamespace

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "map_components" / "_bundle.py"
MANIFEST = ROOT / "godot_rebuild" / "data" / "art" / "map_dynamic.json"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "dynamic_renderer_source.json"
SIZE = (1280, 720)
SHOPS = ((340, 540), (940, 180))
QUALITY = {
    "low": {
        "level": "low",
        "particle_ratio": 0.20,
        "particles": False,
        "fog": False,
        "floating_decor": False,
    },
    "medium": {
        "level": "medium",
        "particle_ratio": 0.40,
        "particles": True,
        "fog": True,
        "floating_decor": True,
    },
    "high": {
        "level": "high",
        "particle_ratio": 0.70,
        "particles": True,
        "fog": True,
        "floating_decor": True,
    },
}
CASES = [
    {"name": "ash_abaddon", "theme": "forest", "quality": "high", "wrap": "ash"},
    {"name": "acid_alchemist", "theme": "desert", "quality": "high", "wrap": "acid"},
    {"name": "ember_ignis", "theme": "volcanic", "quality": "high", "wrap": "ember"},
    {"name": "spirit_krobellus", "theme": "haunted", "quality": "high", "wrap": "spirit"},
    {"name": "snow_ice", "theme": "ice", "quality": "high", "wrap": "snow"},
    {"name": "mist_ocean", "theme": "ocean", "quality": "high"},
    {"name": "firefly", "theme": "primordial", "quality": "high", "force_velocity": True},
    {
        "name": "sand",
        "theme": "desert",
        "quality": "high",
        "particle_type": "sand",
        "boss_identity": "",
        "wrap": "sand",
    },
    {"name": "low", "theme": "forest", "quality": "low", "full_count": True},
    {"name": "medium", "theme": "forest", "quality": "medium", "full_count": True},
]
TORCH_THEMES = [
    "forest",
    "ice",
    "desert",
    "soulforged",
    "radiant",
    "abyssal",
    "eldritch",
    "sanctum",
    "eternalflame",
    "primordial",
    "celestialpeaks",
    "cosmic",
    "royal",
    "violet",
    "crimson",
]
PYGAME = rec.make_pygame({"ticks": 0})


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _source_literals():
    tree = ast.parse(BUNDLE.read_text(encoding="utf-8"))
    constants, themes, registry = {}, {}, {}
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            continue
        name = node.targets[0].id
        if name == "THEMES":
            registry = {
                ast.literal_eval(key): value.id
                for key, value in zip(node.value.keys, node.value.values)
            }
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            continue
        constants[name] = value
        if name.endswith("_THEME") and isinstance(value, dict):
            themes[name] = value
    assert len(themes) == len(registry) == 54
    return constants, themes, registry


def _namespace(constants):
    namespace = {**constants, "math": math, "random": random, "pygame": PYGAME}
    for segment in rec.harvest(BUNDLE, ["_NS_generators", "DynamicRenderer"]):
        exec(compile(segment, "map_components/_bundle.py", "exec"), namespace)
    renderer = namespace["DynamicRenderer"]
    namespace["_original_dynamic_init_particles"] = renderer._init_particles
    namespace["_original_dynamic_update"] = renderer.update
    namespace["_original_dynamic_draw_particles"] = renderer._draw_particles
    namespace["_original_dynamic_draw"] = renderer.draw
    functions = [
        "_boss_init_particles",
        "_boss_update",
        "_boss_draw_particles",
        "_draw_boss_environment",
        "_boss_dynamic_draw",
    ]
    for segment in rec.harvest(BUNDLE, functions, kind=(ast.FunctionDef,)):
        exec(compile(segment, "map_components/_bundle.py", "exec"), namespace)
    renderer._init_particles = namespace["_boss_init_particles"]
    renderer.update = namespace["_boss_update"]
    renderer._draw_particles = namespace["_boss_draw_particles"]
    renderer.draw = namespace["_boss_dynamic_draw"]
    return namespace, renderer, namespace["_NS_generators"]


def _set_quality(perf, level):
    for key, value in QUALITY[level].items():
        setattr(perf.Quality, key, value)


def _layout(generators):
    lanes = generators.PathGenerator.generate_lanes(*SIZE)
    river = generators.PathGenerator.generate_river(*SIZE)
    generator = generators.DecorationGenerator(
        SIZE[0], SIZE[1], lanes[0] + lanes[2] + lanes[1], river, SHOPS
    )
    decorations = generator.generate_all()
    assert len(river) == 61
    return {
        "river_points": _jsonable(river),
        "torch_stones": _jsonable(decorations["torch_stones"]),
        "bones": _jsonable(decorations["bones"]),
        "rocks_mossy": _jsonable(decorations["rocks_mossy"]),
        "gravestones": _jsonable(decorations["gravestones"]),
    }


def _map_renderer(theme, layout, compact=False):
    return SimpleNamespace(
        map_width=SIZE[0],
        map_height=SIZE[1],
        theme=theme,
        radiant_shop_pos=SHOPS[0],
        dire_shop_pos=SHOPS[1],
        river_points=[tuple(point) for point in layout["river_points"]],
        torch_stones=[
            tuple(point)
            for point in layout["torch_stones"][:(2 if compact else len(layout["torch_stones"]))]
        ],
        bones=[tuple(entry) for entry in layout["bones"]],
        rocks_mossy=[tuple(entry) for entry in layout["rocks_mossy"]],
        gravestones=[tuple(entry) for entry in layout["gravestones"]],
    )


def _initial(renderer):
    return {
        "particles": _jsonable(renderer.particles),
        "fog_particles": _jsonable(renderer.fog_particles),
    }


def _configuration(mr, level):
    return {
        "map_width": mr.map_width,
        "map_height": mr.map_height,
        "theme": _jsonable(mr.theme),
        "radiant_shop_pos": _jsonable(mr.radiant_shop_pos),
        "dire_shop_pos": _jsonable(mr.dire_shop_pos),
        "river_points": _jsonable(mr.river_points),
        "torch_stones": _jsonable(mr.torch_stones),
        "bones": _jsonable(mr.bones),
        "rocks_mossy": _jsonable(mr.rocks_mossy),
        "gravestones": _jsonable(mr.gravestones),
        "quality": copy.deepcopy(QUALITY[level]),
    }


class RandomRecorder:
    """Deterministic random source which records values consumed by one draw."""

    def __init__(self, seed, prefix=()):
        self.random_source = random.Random(seed)
        self.prefix = iter(prefix)
        self.log = []

    def _record(self, fallback):
        try:
            value = next(self.prefix)
        except StopIteration:
            value = fallback()
        self.log.append(value)
        return value

    def random(self):
        return self._record(self.random_source.random)

    def uniform(self, low, high):
        return self._record(lambda: self.random_source.uniform(low, high))


def _build_manifest(cls, themes, registry, layout, perf):
    entries = {}
    for theme_name in sorted(registry):
        theme = copy.deepcopy(themes[registry[theme_name]])
        mr = _map_renderer(theme, layout)
        states = {}
        for level in ("low", "medium", "high"):
            _set_quality(perf, level)
            random.seed(f"{theme_name}:dynamic")
            renderer = cls(mr)
            states[level] = _initial(renderer)
        entries[theme_name] = {"theme": _jsonable(theme), "states": states}
    return {
        "source": "map_components/_bundle.py::DynamicRenderer",
        "generator": "godot_rebuild/tests/dynamic_renderer_source_oracle.py",
        "layout_seed": 42,
        "dynamic_seed": "{theme}:dynamic",
        "screen": list(SIZE),
        "shop_positions": {"radiant": list(SHOPS[0]), "dire": list(SHOPS[1])},
        "quality": copy.deepcopy(QUALITY),
        "layout": layout,
        "themes": entries,
    }


def _mutate_initial(renderer, case):
    if not case.get("wrap") or not renderer.particles:
        return
    particle = renderer.particles[0]
    kind = case["wrap"]
    if kind == "snow":
        particle["y"], particle["vy"] = 731.0, 1.0
    elif kind == "sand":
        particle["x"], particle["vx"] = 1300.0, 1.0
    elif kind == "ember":
        particle["y"], particle["vy"] = -10.0, -1.0
    elif kind == "acid":
        particle["y"], particle["vy"] = 29.0, -1.0
    elif kind == "ash":
        particle["y"], particle["vy"] = 700.0, 1.0
    elif kind == "spirit":
        particle["y"], particle["vy"] = 28.0, -1.0


def _build_cases(namespace, cls, themes, registry, layout, perf):
    cases = []
    for case in CASES:
        level = case["quality"]
        _set_quality(perf, level)
        theme = copy.deepcopy(themes[registry[case["theme"]]])
        if not case.get("full_count", False):
            theme["particle_count"] = 6
            theme["fog_count"] = 4
        if "particle_type" in case:
            theme["particle_type"] = case["particle_type"]
        if "boss_identity" in case:
            theme["boss_identity"] = case["boss_identity"]
        mr = _map_renderer(theme, layout, compact=True)
        random.seed(f"case:{case['name']}:init")
        namespace["random"] = random
        renderer = cls(mr)
        _mutate_initial(renderer, case)
        initial = _configuration(mr, level)
        initial.update(_initial(renderer))
        frames = []
        for tick in (0, 1, 6):
            prefix = [0.0, 0.4, 0.4] * len(renderer.particles) if case.get("force_velocity") else ()
            recorder = RandomRecorder(f"case:{case['name']}:{tick}", prefix)
            namespace["random"] = recorder
            target = rec.Surface(SIZE)
            renderer.draw(target, tick)
            frames.append(
                {
                    "t": tick,
                    "random": recorder.log,
                    "particles": _jsonable(renderer.particles),
                    "fog_particles": _jsonable(renderer.fog_particles),
                    "ops": target.ops,
                }
            )
        namespace["random"] = random
        cases.append({"name": case["name"], "initial": initial, "frames": frames})
    return cases


def _build_torch_cases(cls, themes, registry, layout):
    cases = []
    for theme_key in TORCH_THEMES:
        theme = copy.deepcopy(themes[registry[theme_key]])
        mr = _map_renderer(theme, layout, compact=True)
        mr.torch_stones = mr.torch_stones[:1]
        renderer = cls.__new__(cls)
        renderer.mr = mr
        renderer.theme = theme
        renderer._surf_cache = {}
        target = rec.Surface(SIZE)
        renderer._draw_torches(target, 6)
        cases.append(
            {
                "theme_key": theme_key,
                "theme": _jsonable(theme),
                "torch_stones": _jsonable(mr.torch_stones),
                "t": 6,
                "ops": target.ops,
            }
        )
    return cases


def source_artifacts():
    constants, themes, registry = _source_literals()
    namespace, cls, generators = _namespace(constants)
    perf = rec.make_perf(True)
    mobile = types.ModuleType("mobile")
    mobile.perf = perf
    with rec.installed({"pygame": PYGAME, "mobile": mobile, "mobile.perf": perf}):
        layout = _layout(generators)
        manifest = _build_manifest(cls, themes, registry, layout, perf)
        cases = _build_cases(namespace, cls, themes, registry, layout, perf)
        torch_cases = _build_torch_cases(cls, themes, registry, layout)
    fixture = {
        "source": "map_components/_bundle.py::DynamicRenderer + true-boss overrides",
        "screen": list(SIZE),
        "cases": cases,
        "torch_cases": torch_cases,
    }
    return manifest, fixture


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main():
    manifest, fixture = source_artifacts()
    _write(MANIFEST, manifest)
    _write(FIXTURE, fixture)
    frames = sum(len(case["frames"]) for case in fixture["cases"])
    ops = sum(len(frame["ops"]) for case in fixture["cases"] for frame in case["frames"])
    torch_ops = sum(len(case["ops"]) for case in fixture["torch_cases"])
    print(
        f"wrote {MANIFEST.relative_to(ROOT)} ({len(manifest['themes'])} themes, "
        f"{len(manifest['layout']['torch_stones'])} torches)"
    )
    print(
        f"wrote {FIXTURE.relative_to(ROOT)} ({len(fixture['cases'])} cases, "
        f"{frames} frames, {ops} ops; {len(fixture['torch_cases'])} torch palettes, "
        f"{torch_ops} ops)"
    )


if __name__ == "__main__":
    main()
