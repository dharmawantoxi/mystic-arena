"""Source AST oracle: 54 levels x 3 difficulties opening gold and passive rate."""
import ast
import json
import sys
from pathlib import Path

from level_catalog_source_oracle import source_levels

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "godot_rebuild/tests/fixtures/level_economy_source.json"


def rows():
    tree = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    names = {"GOLD_PER_LEVEL_BONUS", "GOLD_PER_SECOND", "GOLD_PER_SECOND_LEVEL_BONUS", "DIFFICULTY_GOLD_MULT"}
    env = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    env[target.id] = ast.literal_eval(node.value)
        if isinstance(node, ast.FunctionDef) and node.name in ("compute_starting_gold", "compute_gold_per_second"):
            exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), "<source economy>", "exec"), env)
    assert names.issubset(env) and "compute_starting_gold" in env and "compute_gold_per_second" in env
    return [
        {"level": n, "difficulty": difficulty,
         "gold": env["compute_starting_gold"](config, n, difficulty),
         "passive": env["compute_gold_per_second"](n, difficulty)}
        for n, config in source_levels().items()
        for difficulty in ("easy", "normal", "hard")
    ]


def check(write=False):
    expected = rows()
    if write:
        FIXTURE.write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    assert json.loads(FIXTURE.read_text(encoding="utf-8")) == expected, "Level economy source drift"
    return len(expected)


if __name__ == "__main__":
    print(f"PASS: {check('--write' in sys.argv)} source economy rows")
