"""Execute original AIPlayer policy via AST; no game imports or source edits.

Action methods are probes, not implementations of the pending transactions.
The fixture proves scheduling/priority only, never full AIPlayer parity.
"""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures/ai_policy_source.json"


def source_fixture():
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    source = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "AIPlayer")
    names = {"__init__", "_ai_brain", "_ai_elite", "update", "_ai_step"}
    cls = ast.ClassDef(name="AIPlayer", bases=[], keywords=[], decorator_list=[],
                      body=[n for n in source.body if isinstance(n, ast.FunctionDef) and n.name in names])
    env = {}
    core = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    for node in core.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and (target.id.startswith("AI_") or target.id == "STARTING_GOLD"):
                    env[target.id] = ast.literal_eval(node.value)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                 "<source AIPlayer policy>", "exec"), env)
    result = {"schedules": [], "priorities": []}
    levels = SimpleNamespace(get_level_count=lambda: 54)
    with patch.dict(sys.modules, {"levels": levels}):
        for count in (54, 24):
            levels.get_level_count = lambda: count
            for level in (-2, 1, 2, 10, 20, 21, 28, 29, 37, 45, 46, 54, 80):
                for succeeds in (False, True):
                    ai = env["AIPlayer"](level_number=level)
                    controls, steps, ticks = [], [], []
                    ai._control_heroes = lambda *args: controls.append(1)
                    def step(*args):
                        steps.append(1)
                        return succeeds
                    ai._ai_step = step
                    for tick in range(1, 201):
                        before = len(steps)
                        ai.update([], [], [], None, [])
                        if len(steps) != before:
                            ticks.append([tick, len(steps) - before, ai.think_timer])
                    result["schedules"].append(dict(level=level, level_count=count,
                        succeeds=succeeds, brain=ai._ai_brain(), elite=ai._ai_elite(),
                        controls=len(controls), ticks=ticks))
        levels.get_level_count = lambda: 54
        actions = {"_try_build_tower": "build", "_try_buy_hero": "buy_hero",
            "_try_upgrade_hero": "upgrade_hero", "_try_buy_item": "buy_item",
            "_try_upgrade_tower_new": "upgrade_tower",
            "_try_activate_regen_shield": "regen_shield",
            "_try_activate_castle_shield": "castle_shield", "_try_upgrade_nexus": "upgrade_nexus"}
        for level in (1, 20, 54):
            for gold, heroes, towers, slots in ((149, 0, 0, 0), (150, 1, 1, 1), (1000, 5, 2, 1)):
                for draw in (0.0, 0.245, 0.4, 0.85, 0.98, 0.999):
                    for success in ("none", *actions.values()):
                        ai = env["AIPlayer"](level_number=level)
                        ai.gold, ai.heroes = gold, [None] * heroes
                        visited, draws = [], []
                        def random_draw():
                            draws.append(draw)
                            return draw
                        env["random"] = SimpleNamespace(random=random_draw)
                        for method, name in actions.items():
                            def attempt(*args, name=name):
                                visited.append(name)
                                return name == success
                            setattr(ai, method, attempt)
                        structures = [SimpleNamespace(team="red", alive=True,
                            can_upgrade=lambda: True)] * towers
                        outcome = ai._ai_step(structures, [{"taken": False}] * slots,
                                              None, ai._ai_brain(), ai._ai_elite())
                        result["priorities"].append(dict(level=level, gold=gold, hero_count=heroes,
                            upgradeable_towers=towers, living_towers=towers, empty_slots=slots,
                            draw=draw, success=success, visited=visited, draws=len(draws), outcome=outcome))
    return result


if __name__ == "__main__":
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), "AI policy source fixture drift"
    print("PASS: AIPlayer policy source oracle (transactions/scene not covered)")
