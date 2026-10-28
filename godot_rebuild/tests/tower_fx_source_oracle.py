"""Record the remaining `Tower.draw` view-only FX for the Godot painter (slice 9bv14).

The oracle harvests the three source blocks that 9bl left behind - selected range, upgrade
flash, and the archer muzzle glow - from `_entity.py::Tower.draw` and executes them under the
shared pygame recorder. `get_archer_bow_position` and its level table come from the real
`towers/_bundle.py`, so the fixture pins the source anchor as well as the draw ops.

Run: python godot_rebuild/tests/tower_fx_source_oracle.py
"""
import ast
import json
import textwrap
import types
from pathlib import Path
from types import SimpleNamespace

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
ENTITY = ROOT / "_entity.py"
TOWERS = ROOT / "towers" / "_bundle.py"
CORE = ROOT / "_core.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "tower_fx_source.json"
BLOCK_TESTS = (
    "self.selected",
    "self.upgrade_flash > 0",
    "self.shoot_flash_timer > 0 and self.tower_type == 'archer'",
)


def _constant(name):
    for node in ast.parse(CORE.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(target, "id", "") == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("%s not found in %s" % (name, CORE.name))


TOWER_COLORS = _constant("TOWER_TYPE_COLORS")


def _archer_bow():
    source = TOWERS.read_text(encoding="utf-8")
    tree = ast.parse(source)
    owner = next(
        (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "_NS_archer_tower"),
        None,
    )
    if owner is None:
        raise AssertionError("_NS_archer_tower not found in %s" % TOWERS.name)
    config = next(
        (
            node
            for node in owner.body
            if isinstance(node, ast.Assign)
            and any(getattr(target, "id", "") == "LEVEL_CONFIGS" for target in node.targets)
        ),
        None,
    )
    function = next(
        (node for node in owner.body if isinstance(node, ast.FunctionDef)
         and node.name == "get_archer_bow_position"),
        None,
    )
    if config is None or function is None:
        raise AssertionError("Archer level table or bow helper not found")
    namespace = {}
    for node in (config, function):
        module = ast.Module(body=[node], type_ignores=[])
        ast.fix_missing_locations(module)
        exec(compile(module, str(TOWERS), "exec"), namespace)
    namespace["_NS_archer_tower"] = SimpleNamespace(LEVEL_CONFIGS=namespace["LEVEL_CONFIGS"])
    # The function resolves `_NS_archer_tower` at call time, so one more exec binds the helper.
    module = ast.Module(body=[function], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(TOWERS), "exec"), namespace)
    return namespace["get_archer_bow_position"], namespace["LEVEL_CONFIGS"]


BOW_POSITION, LEVEL_CONFIGS = _archer_bow()
BOW_HEIGHTS = {str(level): LEVEL_CONFIGS[level]["tower_h"] for level in sorted(LEVEL_CONFIGS)}
FRAMES = [
    {
        "name": "selected_archer",
        "state": {
            "x": 360, "y": 330, "range": 180,
            "color": list(TOWER_COLORS["archer"]["main"]),
            "level": 1, "bow_platform_height": BOW_HEIGHTS["1"],
            "selected": True, "upgrade_flash": 0, "shoot_flash_timer": 0,
            "tower_type": "archer", "target_x": None,
        },
    },
    {
        "name": "selected_cannon_upgrade",
        "state": {
            "x": 895, "y": 505, "range": 205,
            "color": list(TOWER_COLORS["cannon"]["main"]),
            "level": 4, "bow_platform_height": BOW_HEIGHTS["4"],
            "selected": True, "upgrade_flash": 15, "shoot_flash_timer": 0,
            "tower_type": "cannon", "target_x": None,
        },
    },
    {
        "name": "archer_muzzle_right",
        "state": {
            "x": 420, "y": 310, "range": 200,
            "color": list(TOWER_COLORS["archer"]["main"]),
            "level": 3, "bow_platform_height": BOW_HEIGHTS["3"],
            "selected": False, "upgrade_flash": 0, "shoot_flash_timer": 8,
            "tower_type": "archer", "target_x": 700,
        },
    },
    {
        "name": "archer_muzzle_left_low",
        "state": {
            "x": 895, "y": 505, "range": 230,
            "color": list(TOWER_COLORS["archer"]["main"]),
            "level": 6, "bow_platform_height": BOW_HEIGHTS["6"],
            "selected": False, "upgrade_flash": 0, "shoot_flash_timer": 4,
            "tower_type": "archer", "target_x": 300,
        },
    },
    {
        "name": "archer_muzzle_zero",
        "state": {
            "x": 420, "y": 310, "range": 200,
            "color": list(TOWER_COLORS["archer"]["main"]),
            "level": 3, "bow_platform_height": BOW_HEIGHTS["3"],
            "selected": False, "upgrade_flash": 0, "shoot_flash_timer": 1,
            "tower_type": "archer", "target_x": 700,
        },
    },
    {
        "name": "archer_all_fx",
        "state": {
            "x": 640, "y": 360, "range": 190,
            "color": list(TOWER_COLORS["archer"]["main"]),
            "level": 2, "bow_platform_height": BOW_HEIGHTS["2"],
            "selected": True, "upgrade_flash": 30, "shoot_flash_timer": 8,
            "tower_type": "archer", "target_x": 100,
        },
    },
    {
        "name": "no_tower_fx",
        "state": {
            "x": 640, "y": 360, "range": 180,
            "color": list(TOWER_COLORS["archer"]["main"]),
            "level": 1, "bow_platform_height": BOW_HEIGHTS["1"],
            "selected": False, "upgrade_flash": 0, "shoot_flash_timer": 0,
            "tower_type": "archer", "target_x": None,
        },
    },
]


def _draw_fx_source(namespace):
    source = ENTITY.read_text(encoding="utf-8")
    tree = ast.parse(source)
    owner = next(
        (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "Tower"),
        None,
    )
    if owner is None:
        raise AssertionError("Tower not found in %s" % ENTITY.name)
    draw = next(
        (node for node in owner.body if isinstance(node, ast.FunctionDef) and node.name == "draw"),
        None,
    )
    if draw is None:
        raise AssertionError("Tower.draw not found")
    found = {}
    for node in ast.walk(draw):
        if isinstance(node, ast.If):
            test = ast.unparse(node.test)
            if test in BLOCK_TESTS and test not in found:
                found[test] = node
    missing = set(BLOCK_TESTS) - set(found)
    if missing:
        raise AssertionError("Tower.draw blocks not found: %s" % sorted(missing))
    blocks = "\n".join(
        textwrap.dedent(ast.get_source_segment(source, found[test], padded=True))
        for test in BLOCK_TESTS
    )
    method = "def draw_fx(self, surface):\n    x, y = self.x, self.y\n%s\n" % textwrap.indent(blocks, "    ")
    exec(compile(method, str(ENTITY), "exec"), namespace)
    return namespace["draw_fx"]


def _record(state):
    pygame = rec.make_pygame({"ticks": 0})
    towers = types.ModuleType("towers")
    towers.__path__ = []
    archer = types.ModuleType("towers.archer_tower")
    archer.get_archer_bow_position = BOW_POSITION
    namespace = {"pygame": pygame, "_TOWER_SPRITE_CACHE": {}}
    with rec.installed({"pygame": pygame, "towers": towers, "towers.archer_tower": archer}):
        draw_fx = _draw_fx_source(namespace)
        fields = dict(state)
        target_x = fields.pop("target_x", None)
        target = SimpleNamespace(x=target_x, alive=True) if target_x is not None else None
        tower = SimpleNamespace(target=target, **fields)
        surface = rec.Surface((1280, 720))
        draw_fx(tower, surface)
        return surface.ops


def source_fixture():
    return {
        "source": "_entity.py::Tower.draw",
        "bow_heights": BOW_HEIGHTS,
        "frames": [
            {"name": frame["name"], "state": frame["state"], "ops": _record(frame["state"])}
            for frame in FRAMES
        ],
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    op_count = sum(len(frame["ops"]) for frame in fixture["frames"])
    print("Wrote %s: %d frames / %d ops" % (FIXTURE.name, len(fixture["frames"]), op_count))


if __name__ == "__main__":
    main()
