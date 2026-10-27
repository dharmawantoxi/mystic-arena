"""Source oracle for the reachability of the castle magic aura (layer 9bv15).

The migration map used to list the "castle level-6 magic aura" as an unfinished
visual item, on the assumption that the Godot nexus stopping at level 5 was a
rebuild limitation. It is not. `_core.py` pins `MAX_NEXUS_LEVEL = 5`,
`NEXUS_LEVELS` has only keys 1..5, and `Castle.upgrade()` in `_entity.py`
refuses any level >= 5. Both `if lvl >= 6:` arms in
`_render_dynamic_effects` / `_render_dynamic_effects_direct` (the only callers
of `_draw_castle_magic_aura`) and the `else: _render_castle_lvl6(...)` branch
of `_render_castle_full` are therefore dead code in the Python source.

Godot's `NexusUpgrades.LEVELS` (1..5) and the 9bl structure bake
(`CASTLE_LEVELS = (1, 2, 3, 4, 5)`) are already at parity. Raising the native
cap to 6 would DIVERGE from the source and change the simulation, which is
out of scope. The item is therefore closed as "not a migration gap".

This oracle harvests those facts with `ast` and executes the real
`Castle.upgrade` body on a stub to prove an upgrade walk stops at 5.

Run: python godot_rebuild/tests/castle_aura_reach_source_oracle.py
"""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "_core.py"
ENTITY = ROOT / "_entity.py"
BAKE = ROOT / "godot_rebuild" / "bake" / "bake_structure_atlas.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "castle_aura_reach_source.json"


def _assignments(tree):
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out[target.id] = node.value
    return out


def _called_names(node):
    return {
        call.func.id
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    }


def _eq_levels(function):
    """Every `lvl == <int>` constant compared inside a function."""
    found = []
    for node in ast.walk(function):
        if (isinstance(node, ast.Compare)
                and isinstance(node.left, ast.Name) and node.left.id == "lvl"
                and len(node.comparators) == 1
                and isinstance(node.comparators[0], ast.Constant)
                and isinstance(node.comparators[0].value, int)
                and any(isinstance(op, ast.Eq) for op in node.ops)):
            found.append(node.comparators[0].value)
    return sorted(found)


def source_fixture():
    core = ast.parse(CORE.read_text(encoding="utf-8"))
    entity = ast.parse(ENTITY.read_text(encoding="utf-8"))
    bake = ast.parse(BAKE.read_text(encoding="utf-8"))

    core_a = _assignments(core)
    max_level = ast.literal_eval(core_a["MAX_NEXUS_LEVEL"])
    nexus_keys = sorted(ast.literal_eval(core_a["NEXUS_LEVELS"]).keys())
    max_castle_ref = ast.unparse(core_a["MAX_CASTLE_LEVEL"])
    castle_levels_ref = ast.unparse(core_a["CASTLE_LEVELS"])
    bake_levels = list(ast.literal_eval(_assignments(bake)["CASTLE_LEVELS"]))

    castle = next(node for node in entity.body
                  if isinstance(node, ast.ClassDef) and node.name == "Castle")
    upgrade = next(node for node in castle.body
                   if isinstance(node, ast.FunctionDef) and node.name == "upgrade")
    guard = upgrade.body[0]
    upgrade_guard = ast.unparse(guard.test)
    gate_returns_false = (
        isinstance(guard, ast.If)
        and len(guard.body) == 1
        and isinstance(guard.body[0], ast.Return)
        and ast.literal_eval(guard.body[0].value) is False
    )

    functions = {node.name: node for node in entity.body
                 if isinstance(node, ast.FunctionDef)}
    full = functions["_render_castle_full"]
    dispatch_levels = _eq_levels(full)
    else_renderer = ("_render_castle_lvl6"
                     if "_render_castle_lvl6" in _called_names(full) else None)

    aura_call_sites = []
    aura_guards = set()
    for name in ("_render_dynamic_effects", "_render_dynamic_effects_direct"):
        function = functions[name]
        for node in ast.walk(function):
            if (isinstance(node, ast.If)
                    and ast.unparse(node.test) == "lvl >= 6"
                    and "_draw_castle_magic_aura" in _called_names(node)):
                aura_call_sites.append(name)
                aura_guards.add(ast.unparse(node.test))

    # Execute the real Castle.upgrade body on a minimal stub to prove the walk.
    module = ast.Module(body=[upgrade], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"MAX_NEXUS_LEVEL": max_level}
    exec(compile(module, str(ENTITY), "exec"), namespace)  # noqa: S102 - pinned source method

    class Stub:
        def __init__(self):
            self.level = 1
            self.applies = 0

        def _apply_level_stats(self):
            self.applies += 1

    stub = Stub()
    results, levels = [], []
    for _ in range(8):
        results.append(bool(namespace["upgrade"](stub)))
        levels.append(stub.level)

    return {
        "layer": "9bv15",
        "source": "_core.py + _entity.py::Castle + bake/bake_structure_atlas.py",
        "max_nexus_level": max_level,
        "max_castle_level_ref": max_castle_ref,
        "castle_levels_ref": castle_levels_ref,
        "nexus_level_keys": nexus_keys,
        "castle_dispatch_levels": dispatch_levels,
        "castle_else_renderer": else_renderer,
        "magic_aura_function": ("_draw_castle_magic_aura"
                                if "_draw_castle_magic_aura" in functions else None),
        "citadel_function": ("_render_castle_lvl6"
                             if "_render_castle_lvl6" in functions else None),
        "aura_guard": sorted(aura_guards)[0] if aura_guards else None,
        "aura_call_sites": sorted(set(aura_call_sites)),
        "upgrade_guard": upgrade_guard,
        "gate_returns_false": gate_returns_false,
        "upgrade_walk": {
            "results": results,
            "levels": levels,
            "final_level": stub.level,
            "apply_level_stats_calls": stub.applies,
        },
        "bake_castle_levels": bake_levels,
        "aura_reachable_in_source": bool(max_level >= 6 and 6 in nexus_keys),
    }


if __name__ == "__main__":
    FIXTURE.write_text(json.dumps(source_fixture(), indent=1) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)
