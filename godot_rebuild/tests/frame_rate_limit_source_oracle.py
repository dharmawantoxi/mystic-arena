"""Read-only AST oracle for the active Python user FPS-limit setting.

The oracle parses source only and never imports Pygame or touches Python save paths.
"""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures" / "frame_rate_limit_source.json"


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
    return []


def _literal_attribute(function, name):
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Attribute) and target.attr == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Missing source setting {name}")


def _assigned_name_values(tree, name):
    values = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            values.append(ast.literal_eval(node.value))
    return values


def _calls(node, path):
    return [
        call for call in ast.walk(node)
        if isinstance(call, ast.Call) and _attribute_path(call.func) == path
    ]


def _source_fixture():
    core_path = ROOT / "_core.py"
    main_path = ROOT / "main.py"
    perf_path = ROOT / "mobile/perf.py"
    core = ast.parse(core_path.read_text(encoding="utf-8"), filename=str(core_path))
    main_tree = ast.parse(main_path.read_text(encoding="utf-8"), filename=str(main_path))
    perf = ast.parse(perf_path.read_text(encoding="utf-8"), filename=str(perf_path))

    settings = _class(core, "GameSettings")
    defaults = _method(settings, "_init_defaults")
    setter = _method(settings, "set_fps_limit")
    label = _method(settings, "get_fps_label")
    main = _function(main_tree, "main")
    quality = _class(perf, "_Quality")
    quality_apply = _method(quality, "apply")
    auto_quality = _function(perf, "auto_detect_quality")
    target_fps = next(
        node.value for node in ast.walk(quality_apply)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Attribute) and target.attr == "target_fps" for target in node.targets)
    )
    target_values = [
        ast.literal_eval(target_fps.body), ast.literal_eval(target_fps.orelse)
    ]
    option_lists = _assigned_name_values(core, "fps_options")
    save_calls = _calls(setter, ["self", "save"])
    fps_label_suffix = next(
        value.value
        for node in ast.walk(label)
        if isinstance(node, ast.Return) and isinstance(node.value, ast.JoinedStr)
        for value in node.value.values
        if isinstance(value, ast.Constant) and isinstance(value.value, str)
    ).strip()
    has_android_low = any(
        isinstance(node, ast.Call)
        and _attribute_path(node.func) == ["Quality", "apply"]
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "LOW"
        for node in ast.walk(auto_quality)
    )
    desktop_uses_high = any(
        isinstance(node, ast.Call)
        and _attribute_path(node.func) == ["Quality", "apply"]
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "HIGH"
        for node in ast.walk(auto_quality)
    )
    loop_uses_frame_limit = any(
        isinstance(node, ast.Call)
        and _attribute_path(node.func) == ["clock", "tick"]
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "limit"
        for node in ast.walk(main)
    )
    fallback_assignment = any(
        isinstance(node, ast.If)
        and any(
            isinstance(statement, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "limit" for target in statement.targets)
            and _attribute_path(statement.value) == ["perf", "Quality", "target_fps"]
            for statement in node.body
        )
        for node in ast.walk(main)
    )
    touch_cap = any(
        isinstance(node, ast.Call)
        and _attribute_path(node.func) == ["min"]
        and len(node.args) == 2
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "limit"
        and _attribute_path(node.args[1]) == ["perf", "Quality", "target_fps"]
        for node in ast.walk(main)
    )
    return {
        "source": "_core.py:GameSettings + main.py:main + mobile/perf.py:Quality",
        "default": _literal_attribute(defaults, "fps_limit"),
        "presets": option_lists[0] if option_lists else [],
        "preset_controls": len(option_lists),
        "saved_by_setter": bool(save_calls),
        "setter_validates_presets": any(
            isinstance(node, ast.Compare)
            and isinstance(node.left, ast.Name)
            and node.left.id == "fps"
            and len(node.ops) == 1
            and isinstance(node.ops[0], ast.In)
            and ast.literal_eval(node.comparators[0]) == [30, 60, 120, 0]
            for node in ast.walk(setter)
        ),
        "labels": {
            "unlimited": next(
                ast.literal_eval(node.value)
                for node in ast.walk(label)
                if isinstance(node, ast.Return)
                and isinstance(node.value, ast.Constant)
                and node.value.value == "Unlimited"
            ),
            "unit": fps_label_suffix,
        },
        "quality_targets": {
            "android_low": target_values[0],
            "desktop_high": target_values[1],
            "android_starts_low": has_android_low,
            "desktop_starts_high": desktop_uses_high,
        },
        "runtime_cap": {
            "clock_tick_uses_limit": loop_uses_frame_limit,
            "zero_falls_back_to_quality_target": fallback_assignment,
            "touch_mode_caps_explicit_selection": touch_cap,
        },
    }


def source_fixture():
    return _source_fixture()


def verify():
    actual = source_fixture()
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if actual != expected:
        raise AssertionError("FPS-limit fixture drift; re-audit the active Python path")
    if actual["default"] != 60 or actual["presets"] != [30, 60, 120, 0]:
        raise AssertionError("Python FPS setting default/presets changed")
    if actual["preset_controls"] < 2 or not actual["saved_by_setter"]:
        raise AssertionError("Python FPS controls or persistence changed")
    if not actual["setter_validates_presets"]:
        raise AssertionError("Python FPS setter no longer validates the four options")
    if actual["labels"] != {"unlimited": "Unlimited", "unit": "FPS"}:
        raise AssertionError("Python FPS label contract changed")
    if actual["quality_targets"] != {
        "android_low": 30,
        "desktop_high": 60,
        "android_starts_low": True,
        "desktop_starts_high": True,
    }:
        raise AssertionError("Python source quality target policy changed")
    if not all(actual["runtime_cap"].values()):
        raise AssertionError("Python main loop no longer applies the FPS cap contract")
    return 10


if __name__ == "__main__":
    print(f"PASS: {verify()} read-only frame-rate-source checks")
