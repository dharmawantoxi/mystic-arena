"""Check committed fixtures against the ORIGINAL Python source, without pygame.

Only a pure PathGenerator class is executed. No migration converter or game module
is imported. Runtime Godot never imports Python; this is a development/CI oracle.
"""
import ast
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
FIELDS = {
    "name", "hp", "damage", "speed", "range", "attack_cooldown",
    "gold_reward", "radius", "regen", "armor", "magic_resist",
}


def source_minions():
    module = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    table = next(
        node.value for node in module.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "MINION_TYPES" for target in node.targets)
    )
    result = {}
    for key, entry in zip(table.keys, table.values):
        result[ast.literal_eval(key)] = {
            ast.literal_eval(k): ast.literal_eval(v)
            for k, v in zip(entry.keys, entry.values)
            if ast.literal_eval(k) in FIELDS
        }
    # Lab's unscaled values are only valid for level-1 nexus.
    nexus = next(
        node.value for node in module.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "NEXUS_LEVELS" for target in node.targets)
    )
    tier_one = next(value for key, value in zip(nexus.keys, nexus.values) if ast.literal_eval(key) == 1)
    stats = ast.literal_eval(tier_one)
    assert stats["minion_scale"] == 1.0 and stats["minion_ai_level"] == 1, "Re-audit level-1 minions"
    return result


def source_lanes():
    module = ast.parse((ROOT / "map_components/_bundle.py").read_text(encoding="utf-8"))
    generator = next(node for node in ast.walk(module) if isinstance(node, ast.ClassDef) and node.name == "PathGenerator")
    namespace = {"_NS_generators": SimpleNamespace()}
    exec(compile(ast.Module(body=[generator], type_ignores=[]), "<Python source lane generator>", "exec"), namespace)
    namespace["_NS_generators"].PathGenerator = namespace["PathGenerator"]
    paths = namespace["PathGenerator"].generate_lanes(1280, 720)
    return {name: [list(point) for point in path] for name, path in zip(("top", "mid", "bot"), paths)}


def main():
    actual_stats = source_minions()
    actual_lanes = source_lanes()
    assert actual_stats == json.loads((FIXTURES / "minion_source.json").read_text()), "Minion fixture drift: re-audit source"
    assert actual_lanes == json.loads((FIXTURES / "lanes_source.json").read_text()), "Lane fixture drift: re-audit source"
    print("PASS: source contract — 5 minion definitions and all 277 lane points match Python.")


if __name__ == "__main__":
    main()
