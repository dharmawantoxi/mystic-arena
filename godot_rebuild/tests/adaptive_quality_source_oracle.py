"""Read-only AST oracle for the active Python adaptive-quality governor."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures" / "adaptive_quality_source.json"


def _class(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name)


def _method(class_node, name):
    return next(
        node for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _function(tree, name):
    return next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _attribute_path(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.insert(0, node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.insert(0, node.id)
    return parts


def _self_assignment(function, attribute):
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign):
            continue
        if any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == attribute
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Missing Python runtime field self.{attribute}")


def _constructor_defaults(function):
    args = function.args.args
    defaults = function.args.defaults
    return {
        args[len(args) - len(defaults) + index].arg: ast.literal_eval(value)
        for index, value in enumerate(defaults)
    }


def _level_constants(tree):
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Tuple):
            continue
        names = node.targets[0].elts if isinstance(node.targets[0], ast.Tuple) else []
        if [name.id for name in names if isinstance(name, ast.Name)] == ["LOW", "MEDIUM", "HIGH"]:
            values = ast.literal_eval(node.value)
            return dict(zip(["low", "medium", "high"], values))
    raise AssertionError("Missing LOW/MEDIUM/HIGH source constants")


def _source_fixture():
    perf_path = ROOT / "mobile/perf.py"
    main_path = ROOT / "main.py"
    perf = ast.parse(perf_path.read_text(encoding="utf-8"), filename=str(perf_path))
    main = ast.parse(main_path.read_text(encoding="utf-8"), filename=str(main_path))
    quality = _class(perf, "_Quality")
    quality_apply = _method(quality, "apply")
    adaptive = _class(perf, "AdaptiveQuality")
    adaptive_init = _method(adaptive, "__init__")
    adaptive_update = _method(adaptive, "update")
    auto_quality = _function(perf, "auto_detect_quality")
    install = _function(perf, "install_all")
    game_loop = _function(main, "main")

    target_expression = next(
        node.value for node in ast.walk(quality_apply)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Attribute) and target.attr == "target_fps"
            for target in node.targets
        )
    )
    lower_calls = [
        node for node in ast.walk(adaptive_update)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == "_cooldown"
            for target in node.targets
        )
    ]
    cooldown_values = sorted(ast.literal_eval(node.value) for node in lower_calls)
    apply_calls = [
        node for node in ast.walk(adaptive_update)
        if isinstance(node, ast.Call) and _attribute_path(node.func) == ["Quality", "apply"]
    ]
    step_expressions = [ast.unparse(node.args[0]) for node in apply_calls]
    initial_calls = {
        node.args[0].id
        for node in ast.walk(auto_quality)
        if isinstance(node, ast.Call)
        and _attribute_path(node.func) == ["Quality", "apply"]
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
    }
    adaptive_loop_call = any(
        isinstance(node, ast.Call)
        and _attribute_path(node.func) == ["adaptive", "update"]
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Call)
        and _attribute_path(node.args[0].func) == ["clock", "get_fps"]
        for node in ast.walk(game_loop)
    )
    adaptive_default = _constructor_defaults(install).get("adaptive")
    quality_args = _constructor_defaults(adaptive_init)
    cooldown_gate = any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Attribute)
        and node.test.left.attr == "_cooldown"
        and any(isinstance(operator, ast.Gt) for operator in node.test.ops)
        and any(isinstance(stmt, ast.Return) for stmt in node.body)
        for node in ast.walk(adaptive_update)
    )
    samples_reset_at_window = any(
        isinstance(node, ast.Call)
        and _attribute_path(node.func) == ["self", "_samples", "clear"]
        for node in ast.walk(adaptive_update)
    )
    return {
        "source": "mobile/perf.py:Quality + AdaptiveQuality; main.py:main",
        "levels": _level_constants(perf),
        "initial_quality": {
            "desktop": "high" if "HIGH" in initial_calls else "missing",
            "touch": "low" if "LOW" in initial_calls else "missing",
        },
        "adaptive": {
            "enabled_by_default": adaptive_default,
            "low_fps": quality_args.get("low_fps"),
            "high_fps": quality_args.get("high_fps"),
            "sample_window": quality_args.get("window"),
            "cooldown_steps": cooldown_values,
            "transition_steps": step_expressions,
            "cooldown_returns_before_sampling": cooldown_gate,
            "clears_each_full_window": samples_reset_at_window,
            "fps_source_applied_each_frame": adaptive_loop_call,
        },
        "target_fps": {
            "low": ast.literal_eval(target_expression.body),
            "medium_and_high": ast.literal_eval(target_expression.orelse),
        },
    }


def source_fixture():
    return _source_fixture()


def verify():
    actual = source_fixture()
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if actual != expected:
        raise AssertionError("Adaptive-quality fixture drift; re-audit active Python runtime")
    if actual["levels"] != {"low": "low", "medium": "medium", "high": "high"}:
        raise AssertionError("Python quality level IDs changed")
    if actual["initial_quality"] != {"desktop": "high", "touch": "low"}:
        raise AssertionError("Python initial quality selection changed")
    if actual["adaptive"] != {
        "enabled_by_default": True,
        "low_fps": 26,
        "high_fps": 52,
        "sample_window": 90,
        "cooldown_steps": [180, 300],
        "transition_steps": [
            "LOW if Quality.level == MEDIUM else MEDIUM",
            "HIGH if Quality.level == MEDIUM else MEDIUM",
        ],
        "cooldown_returns_before_sampling": True,
        "clears_each_full_window": True,
        "fps_source_applied_each_frame": True,
    }:
        raise AssertionError("Python adaptive-quality thresholds or transition timing changed")
    if actual["target_fps"] != {"low": 30, "medium_and_high": 60}:
        raise AssertionError("Python quality target FPS mapping changed")
    return 11


if __name__ == "__main__":
    print(f"PASS: {verify()} read-only adaptive-quality source checks")
