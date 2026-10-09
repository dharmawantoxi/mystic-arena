"""Read-only AST oracle for the active Pygame simulation-speed behavior.

This parses _core.py without importing or executing the game, touching Python
settings, or opening any Python save directory.
"""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_core.py"
FIXTURE = Path(__file__).parent / "fixtures" / "game_speed_source.json"


class Oracle:
    def __init__(self):
        self.checks = 0

    def check(self, condition, message):
        self.checks += 1
        if not condition:
            raise AssertionError(message)


def _class(tree, name):
    return next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name
    )


def _method(class_node, name):
    return next(
        node
        for node in class_node.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    )


def _assigned_value(function, name):
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Attribute) and target.attr == name for target in node.targets
        ):
            return node.value
    return None


def _speed_preset_lists(tree):
    values = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "speeds" for target in node.targets):
            continue
        if isinstance(node.value, ast.List):
            values.append([ast.literal_eval(item) for item in node.value.elts])
    return values


def _has_compare(function, name, operator, value):
    for node in ast.walk(function):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        if not isinstance(node.left, ast.Name) or node.left.id != name:
            continue
        if type(node.ops[0]) is not operator:
            continue
        if len(node.comparators) == 1 and ast.literal_eval(node.comparators[0]) == value:
            return True
    return False


def verify():
    oracle = Oracle()
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    game_update = _method(_class(tree, "Game"), "update")
    settings = _class(tree, "GameSettings")
    defaults = _method(settings, "_init_defaults")
    setter = _method(settings, "set_game_speed")
    oracle.check(
        ast.literal_eval(_assigned_value(defaults, "game_speed")) == 1.0,
        "source default is 1.0x",
    )
    clamp = _assigned_value(setter, "game_speed")
    oracle.check(
        isinstance(clamp, ast.Call)
        and isinstance(clamp.func, ast.Name)
        and clamp.func.id == "max"
        and ast.dump(clamp, include_attributes=False)
        == "Call(func=Name(id='max', ctx=Load()), args=[Constant(value=0.5), Call(func=Name(id='min', ctx=Load()), args=[Constant(value=2.0), Name(id='speed', ctx=Load())], keywords=[])], keywords=[])",
        "source setter clamps speed to [0.5, 2.0]",
    )
    extra_updates = next(
        node.value
        for node in ast.walk(game_update)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "extra_updates" for target in node.targets)
    )
    oracle.check(
        ast.dump(extra_updates, include_attributes=False)
        == "BinOp(left=Call(func=Name(id='int', ctx=Load()), args=[Name(id='speed_mult', ctx=Load())], keywords=[]), op=Sub(), right=Constant(value=1))",
        "source truncates the multiplier before calculating extra updates",
    )
    oracle.check(_has_compare(game_update, "speed_mult", ast.Gt, 1.0), "source has the fast-speed branch")
    oracle.check(_has_compare(game_update, "speed_mult", ast.Lt, 1.0), "source has the slow-speed branch")
    oracle.check(
        any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "range"
            and len(node.args) == 1 and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "extra_updates" for node in ast.walk(game_update)),
        "source executes one additional gameplay update per integer extra update",
    )
    oracle.check(
        any(
            isinstance(node, ast.Compare)
            and isinstance(node.left, ast.BinOp)
            and isinstance(node.left.left, ast.Attribute)
            and node.left.left.attr == "_speed_skip_counter"
            and isinstance(node.left.op, ast.Mod)
            and ast.literal_eval(node.left.right) == 2
            and len(node.ops) == 1
            and isinstance(node.ops[0], ast.Eq)
            and ast.literal_eval(node.comparators[0]) == 0
            for node in ast.walk(game_update)
        ),
        "source skips every even half-speed frame",
    )
    preset_lists = _speed_preset_lists(tree)
    oracle.check(
        preset_lists.count([0.5, 1.0, 1.5, 2.0]) >= 2,
        "source previous/next controls use the four exact speed presets",
    )
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    oracle.check(fixture["default"] == 1.0, "fixture records the source default")
    oracle.check(fixture["presets"] == [0.5, 1.0, 1.5, 2.0], "fixture records source presets")
    expected = {
        "0.5": [1, 0, 1, 0],
        "1.0": [1, 1, 1, 1],
        "1.5": [1, 1, 1, 1],
        "2.0": [2, 2, 2, 2],
    }
    oracle.check(fixture["ticks_per_physics_call"] == expected, "fixture locks source tick counts")
    oracle.check(
        "int(1.5)-1 is 0" in fixture["skip_oddity"],
        "fixture explicitly preserves the active 1.5x truncation behavior",
    )
    guard_names = {
        node.attr
        for node in ast.walk(game_update)
        if isinstance(node, ast.Attribute) and node.attr in {"boss_intro", "level_intro"}
    }
    oracle.check(guard_names == {"boss_intro", "level_intro"}, "source excludes intro cinematics from speed scaling")
    return oracle.checks


if __name__ == "__main__":
    print(f"PASS: {verify()} read-only Pygame speed-source checks")
