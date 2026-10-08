"""Read-only AST oracle for the active Python audio-volume controls.

This parses source only: it does not import the game, instantiate Pygame, or
read/write Python save and settings paths.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures" / "audio_settings_source.json"


def _class(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name)


def _method(class_node, name):
    return next(
        node
        for node in class_node.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    )


def _function(tree, name):
    return next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    )


def _literal_assignment(function, attribute):
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Attribute) and target.attr == attribute for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Missing source assignment for {attribute}")


def _attribute_path(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.insert(0, node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.insert(0, node.id)
        return parts
    return []


def _number(node):
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_number(node.operand)
    return float(ast.literal_eval(node))


def _audio_controls(menu_tree):
    draw_settings = _function(menu_tree, "_draw_settings")
    for node in ast.walk(draw_settings):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "audio_settings" for target in node.targets):
            continue
        return [
            {"label": ast.literal_eval(item.elts[0]), "id": ast.literal_eval(item.elts[2])}
            for item in node.value.elts
            if isinstance(item, ast.Tuple) and len(item.elts) == 3
        ]
    raise AssertionError("Could not find active Python settings audio rows")


def _adjustment_steps(menu_tree):
    values = []
    for node in ast.walk(menu_tree):
        if not isinstance(node, ast.Call) or _attribute_path(node.func) not in (
            ["self", "_adjust_volume"], ["_adjust_volume"]
        ):
            continue
        if len(node.args) == 2:
            values.append(_number(node.args[1]))
    return sorted(set(values))


def _clamp_bounds(adjust):
    for node in ast.walk(adjust):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "max":
            continue
        if len(node.args) != 2 or _number(node.args[0]) != 0.0:
            continue
        inner = node.args[1]
        if (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Name)
            and inner.func.id == "min"
            and len(inner.args) == 2
            and _number(inner.args[0]) == 1.0
        ):
            return [_number(node.args[0]), _number(inner.args[0])]
    raise AssertionError("Could not find Python volume clamp bounds")


def _load_categories(sound_manager):
    load_all = _method(sound_manager, "load_all")
    entries = []
    for node in ast.walk(load_all):
        if not isinstance(node, ast.Call) or _attribute_path(node.func) != ["self", "load"]:
            continue
        if len(node.args) < 3:
            continue
        entries.append(
            {
                "name": ast.literal_eval(node.args[0]),
                "file": ast.literal_eval(node.args[1]),
                "category": ast.literal_eval(node.args[2]),
            }
        )
    return sorted(entries, key=lambda item: item["name"])


def _has_product(function, names):
    wanted = set(names)
    return any(
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Mult)
        and {
            part.id if isinstance(part, ast.Name) else part.attr
            for part in ast.walk(node)
            if isinstance(part, (ast.Name, ast.Attribute))
        }
        >= wanted
        for node in ast.walk(function)
    )


def source_fixture():
    system_path = ROOT / "_system.py"
    menu_path = ROOT / "_core.py"
    system_tree = ast.parse(system_path.read_text(encoding="utf-8"), filename=str(system_path))
    menu_tree = ast.parse(menu_path.read_text(encoding="utf-8"), filename=str(menu_path))
    sound_manager = _class(system_tree, "SoundManager")
    init = _method(sound_manager, "__init__")
    play = _method(sound_manager, "play")
    play_bgm = _method(sound_manager, "play_bgm")
    play_ambient = _method(sound_manager, "play_ambient")
    update_bgm = _method(sound_manager, "update_bgm_volume")
    adjust = _function(menu_tree, "_adjust_volume")
    categories = _load_categories(sound_manager)
    voice_keys = [entry["name"] for entry in categories if entry["category"] == "voice"]

    return {
        "source": "_system.py:SoundManager + _core.py:settings audio controls",
        "defaults": {
            "master": _literal_assignment(init, "master_volume"),
            "sfx": _literal_assignment(init, "sfx_volume"),
            "bgm": _literal_assignment(init, "bgm_volume"),
            "voice": _literal_assignment(init, "voice_volume"),
            "ambient": _literal_assignment(init, "ambient_volume"),
        },
        "settings_controls": _audio_controls(menu_tree),
        "adjustment_steps": _adjustment_steps(menu_tree),
        "clamp": _clamp_bounds(adjust),
        "runtime_mix": {
            "sfx_multiplies_master": _has_product(play, ["master_volume", "volume_mult"]),
            "bgm_multiplies_master_and_category": _has_product(
                play_bgm, ["master_volume", "bgm_volume"]
            ),
            "ambient_multiplies_master_and_category": _has_product(
                play_ambient, ["master_volume", "ambient_volume"]
            ),
            "master_refreshes_bgm": any(
                isinstance(node, ast.Call)
                and _attribute_path(node.func) in (["self", "update_bgm_volume"], ["update_bgm_volume"])
                for node in ast.walk(_method(sound_manager, "set_master_volume"))
            ),
            "bgm_refresh_multiplies_master_and_category": _has_product(
                update_bgm, ["master_volume", "bgm_volume"]
            ),
            "voice_sound_keys": voice_keys,
        },
        "audio_adjustment_saves_settings": any(
            isinstance(node, ast.Call) and _attribute_path(node.func)[-1:] == ["save"]
            for node in ast.walk(adjust)
        ),
    }


def verify():
    actual = source_fixture()
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if actual != expected:
        raise AssertionError("Audio settings fixture drift; re-audit Python source before updating it")
    if [row["id"] for row in actual["settings_controls"]] != ["master", "sfx", "bgm", "voice"]:
        raise AssertionError("Python settings channel ordering changed")
    if actual["adjustment_steps"] != [-0.1, 0.1] or actual["clamp"] != [0.0, 1.0]:
        raise AssertionError("Python volume step/clamp contract changed")
    if not all(value is True for key, value in actual["runtime_mix"].items() if key != "voice_sound_keys"):
        raise AssertionError("Python audio mixer no longer applies the source mix")
    if actual["audio_adjustment_saves_settings"]:
        raise AssertionError("Python volume controls now save settings; re-audit persistence behavior")
    return len(actual["settings_controls"]) + len(actual["runtime_mix"]) + 3


if __name__ == "__main__":
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(source_fixture(), indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {verify()} read-only audio-source checks")
