"""Read-only AST oracle for once-per-tick AI hero control dispatch.

The source AIPlayer.update calls _control_heroes exactly once, before its
think-timer early return. The old native match path also called the controller,
whose policy called the same control callback, after a direct _step_ai_heroes
call in PrototypeBattle.step_tick. The fixture preserves that native_old=2
counterfactual while expected is executed from the source update AST.
"""
import ast
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTITY = ROOT / "_entity.py"
CORE = ROOT / "_core.py"
FIXTURE = Path(__file__).parent / "fixtures/ai_control_tick_source.json"
PRE_FIX_EXTRA_CONTROL_CALLS = 1
SCENARIOS = (("think_wait_tick", 90), ("think_expiry_tick", 1))


def _class_method(path: Path, class_name: str, method_name: str) -> ast.FunctionDef:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return child
    raise AssertionError(f"Missing {class_name}.{method_name} in {path}")


def _self_call_count(function: ast.FunctionDef, method_name: str) -> int:
    return sum(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == method_name
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
        for node in ast.walk(function)
    )


def _game_ai_update_count(function: ast.FunctionDef) -> int:
    return sum(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "update"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "ai"
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "self"
        for node in ast.walk(function)
    )


def _execute_update(update_node: ast.FunctionDef, think_timer: int) -> dict:
    module = ast.Module(body=[copy.deepcopy(update_node)], type_ignores=[])
    env = {"AI_THINK_INTERVAL": 90}
    exec(
        compile(ast.fix_missing_locations(module), "<source AIPlayer.update>", "exec"),
        env,
    )
    source_update = env["update"]

    class Probe:
        def __init__(self) -> None:
            self.think_timer = think_timer
            self.level_number = 1
            self.control_calls = 0
            self.step_calls = 0

        def _control_heroes(self, *_args) -> None:
            self.control_calls += 1

        def _ai_brain(self) -> float:
            return 0.0

        def _ai_elite(self) -> float:
            return 0.0

        def _ai_step(self, *_args) -> bool:
            self.step_calls += 1
            return False

    probe = Probe()
    source_update(probe, [], [], [], None, [])
    return {
        "control_calls": probe.control_calls,
        "step_calls": probe.step_calls,
        "think_timer_after": probe.think_timer,
    }


def source_fixture() -> dict:
    update_node = _class_method(ENTITY, "AIPlayer", "update")
    game_update = _class_method(CORE, "Game", "update")
    source_control_calls = _self_call_count(update_node, "_control_heroes")
    source_game_ai_calls = _game_ai_update_count(game_update)
    assert source_control_calls == 1, "AIPlayer.update must control heroes once per tick"
    assert source_game_ai_calls == 1, "Game.update must dispatch the AI update once"

    cases = []
    for scenario, think_timer in SCENARIOS:
        expected = _execute_update(update_node, think_timer)
        native_old = dict(expected)
        native_old["control_calls"] += PRE_FIX_EXTRA_CONTROL_CALLS
        cases.append(
            {
                "scenario": scenario,
                "think_timer_before": think_timer,
                "expected": expected,
                "native_old": native_old,
            }
        )
    return {
        "source": {
            "ai_player_update_control_calls": source_control_calls,
            "game_update_ai_calls": source_game_ai_calls,
            "native_old_extra_control_calls": PRE_FIX_EXTRA_CONTROL_CALLS,
        },
        "cases": cases,
    }


if __name__ == "__main__":
    import sys

    fixture = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    else:
        assert fixture == json.loads(FIXTURE.read_text(encoding="utf-8")), (
            "AI control tick source fixture drift"
        )
    print("PASS: AIPlayer source controls heroes exactly once per update")
