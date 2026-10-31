"""Read-only AST oracle for `main.py` — the pygame entry point (layer 9cn).

`main.py` is the app shell: mixer pre-init, display, the splash/menu/game/pause
state machine, the fixed-step catch-up loop, lifecycle handling and the startup
banner. It is never imported (it calls `pygame.init()` at import time), so this
oracle walks its AST instead: the file inventory, the 35 symbol classification,
the loop constants (`MAX_CATCHUP`, `FIXED_DT_MS`, the 2 s error cooldown, the
debug env switch), the keyboard mapping and the exact startup banner template.

Writes/checks `godot_rebuild/tests/fixtures/main_source.json`.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "godot_rebuild"
FIXTURE = PROJECT / "tests/fixtures/main_source.json"
SOURCE = ROOT / "main.py"
PROJECT_FILE = PROJECT / "project.godot"


def _literal(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Dict):
        return {_literal(key): _literal(value) for key, value in zip(node.keys, node.values)}
    if isinstance(node, ast.Tuple):
        return tuple(_literal(value) for value in node.elts)
    if isinstance(node, ast.List):
        return [_literal(value) for value in node.elts]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_literal(node.operand)
    if isinstance(node, ast.BinOp):
        left = _literal(node.left)
        right = _literal(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Div):
            return left / right
    raise AssertionError(f"Unsupported main.py data expression at line {node.lineno}")


def _import_name(node):
    if isinstance(node, ast.Import):
        return ", ".join(alias.name for alias in node.names)
    module = node.module or ""
    target = node.names[0].name
    if node.level:
        module = "." * node.level + module
    return f"{module}.{target}"


def _assign_name(node):
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    labels = []
    for target in targets:
        if isinstance(target, ast.Name):
            labels.append(target.id)
        elif isinstance(target, ast.Tuple):
            names = [element.id for element in target.elts if isinstance(element, ast.Name)]
            labels.append("..".join([names[0], names[-1]]) if names else ast.unparse(target))
        else:
            labels.append(ast.unparse(target))
    return ", ".join(labels)


def _main_function(tree):
    return next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"
    )


def _local_assignment(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return _literal(node.value)
    raise AssertionError(f"Missing main.py assignment {name}")


def _startup_banner(tree):
    """The eight print lines between the two `"=" * 60` rules."""
    printed = []
    for statement in _main_function(tree).body:
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            continue
        call = statement.value
        if not isinstance(call.func, ast.Name) or call.func.id != "print" or not call.args:
            continue
        argument = call.args[0]
        if isinstance(argument, ast.BinOp) and isinstance(argument.op, ast.Mod):
            argument = argument.left
        try:
            printed.append(_literal(argument))
        except AssertionError:
            continue
    rules = [index for index, line in enumerate(printed) if isinstance(line, str) and set(line) == {"="}]
    if len(rules) < 2:
        raise AssertionError("main.py startup banner rules changed")
    return printed[rules[0]:rules[1] + 1]


def _key_actions(tree):
    """`pygame.K_*` -> the first action of that branch inside the event loop."""
    actions = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not node.body:
            continue
        test = node.test
        if not (
            isinstance(test, ast.Compare)
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Eq)
            and isinstance(test.left, ast.Attribute)
            and test.left.attr == "key"
            and isinstance(test.comparators[0], ast.Attribute)
            and test.comparators[0].value.__class__ is ast.Name
        ):
            continue
        key_name = test.comparators[0].attr
        if not key_name.startswith("K_"):
            continue
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Call):
            call = first.value
            actions[key_name] = ast.unparse(call.func)
        elif isinstance(first, ast.Assign) and isinstance(first.targets[0], ast.Subscript):
            actions[key_name] = ast.unparse(first.targets[0].slice)
        elif isinstance(first, ast.If):
            actions[key_name] = "state-transition"
    return actions


def _debug_env(tree):
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            return node.args[0].value
    raise AssertionError("main.py debug environment switch changed")


def _mixer_pre_init(tree):
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "pre_init"
        ):
            return {keyword.arg: _literal(keyword.value) for keyword in node.keywords}
    raise AssertionError("main.py mixer pre_init contract changed")


# Symbol -> (kind, target, token, note). `target` is relative to godot_rebuild/.
CLASSIFICATION = {
    "os": ("folded", "scripts/app/frame_error_log.gd", "FileAccess.open(", ""),
    "sys": ("folded", "app/app.gd", "get_tree().quit()", ""),
    "pygame": ("baked", "", "", "engine + scene tree replace pygame primitives"),
    "mobile.platform_utils": (
        "ported", "scripts/platform/mobile_platform.gd", "static func is_touch_mode()",
        ""),
    "mobile.perf": (
        "baked", "", "",
        "font/blit hot patches have no GDScript analogue; quality presets live in adaptive_quality"),
    "mobile.touch": (
        "ported", "scripts/input/touch_gesture_runtime.gd", "func touch_down(", ""),
    "mobile.hud": (
        "ported", "scripts/ui/touch_hud_layout.gd", "static func action_intent(", ""),
    "mobile.debug": (
        "deviation", "", "", "dev overlay is opt-in via MYSTIC_DEBUG and not ported (D5)"),
    "mobile.diagnostics": (
        "deviation", "", "", "PYGAME_SDL self-test screen replaced by the native suite (D6)"),
    "mobile.bootcheck": (
        "deviation", "", "", "MYSTIC_BOOTCHECK diagnostic screen is Android-dev only (D6)"),
    "mobile.combat_audio": (
        "ported", "scripts/audio/combat_audio.gd", "func new_frame()", ""),
    "mobile.sidepanel": (
        "ported", "scripts/ui/side_panel.gd", "func is_active()", ""),
    "mobile.kaizen_review": ("deviation", "", "", "opt-in F9 review sheet (D5)"),
    "mobile.vex_review": ("deviation", "", "", "opt-in F10 review sheet (D5)"),
    "mobile.grimjaw_review": ("deviation", "", "", "opt-in F11 review sheet (D5)"),
    "mobile.sylara_review": ("deviation", "", "", "opt-in F7 review sheet (D5)"),
    "_core": ("ported", "scripts/data/core_settings.gd", "DATA_PATH", ""),
    "storage_paths.SAVE_DIR": (
        "folded", "scripts/match/save_slot_store.gd", "const PATH_TEMPLATE", ""),
    "settings.TITLE": (
        "folded", "scripts/data/core_settings.gd", "DATA_PATH",
        "module absent in this snapshot; TITLE lives in core settings"),
    "game.Game": (
        "folded", "scenes/prototype/PrototypeMatch.tscn", "[node name=\"PrototypeMatch\"",
        "module absent in this snapshot; the session scene is the port"),
    "menu.Menu": (
        "folded", "scenes/menu/MainMenu.tscn", "[node name=\"MainMenu\"",
        "module absent in this snapshot; the menu scene is the port"),
    "splash_screen.SplashScreen": (
        "ported", "scenes/splash/SplashScreen.tscn", "[node name=\"SplashScreen\"", ""),
    "_render.get_font": ("ported", "scripts/ui/rebuild_theme.gd", "static func create_theme(", ""),
    "_log_frame_error": ("ported", "scripts/app/frame_error_log.gd", "func record(", ""),
    "_cinematic_active": (
        "ported", "scenes/prototype/prototype_screen.gd", "celebration_active", ""),
    "_handle_background": (
        "folded", "app/app.gd", "NOTIFICATION_APPLICATION_PAUSED",
        "the engine owns background suspension"),
    "main": ("folded", "app/app.gd", "func _install_screen(", "loop lives in the scene tree"),
    "adaptive": (
        "ported", "scripts/settings/adaptive_quality_runtime.gd", "func update_fps(", ""),
    "screen": ("baked", "", "", "the viewport replaces the pygame render surface"),
    "STATE_SPLASH..STATE_PAUSE": (
        "ported", "app/app.gd", "_install_screen(SPLASH)", ""),
    "APP_BG": ("folded", "app/app.gd", "NOTIFICATION_APPLICATION_FOCUS_OUT", ""),
    "APP_FG": ("folded", "app/app.gd", "NOTIFICATION_APPLICATION_PAUSED", ""),
    "_FRAME_ERR_LAST": ("ported", "scripts/app/frame_error_log.gd", "var last_written", ""),
    "_FRAME_ERR_COOLDOWN": (
        "data", "scripts/app/frame_error_log.gd", "const COOLDOWN_SECONDS := 2.0", ""),
    "__main__": ("folded", "project.godot", "run/main_scene=", ""),
}


def _inventory():
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    assigns = [node for node in tree.body if isinstance(node, ast.Assign)]
    entrypoints = [
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and getattr(node.test.left, "id", "") == "__name__"
    ]
    return {
        "file": {
            "file": "main.py",
            "lines": len(source.splitlines()),
            "classes": len(classes),
            "functions": len(functions),
            "assigns": len(assigns),
            "entrypoints": len(entrypoints),
            "imports": len(imports),
        },
        "symbols": {
            "count": len(imports) + len(classes) + len(functions) + len(assigns) + len(entrypoints),
            "names": (
                [_import_name(node) for node in imports]
                + [node.name for node in classes]
                + [node.name for node in functions]
                + [_assign_name(node) for node in assigns]
                + ["__main__" for _ in entrypoints]
            ),
        },
        "imports": [_import_name(node) for node in imports],
        "functions": [node.name for node in functions],
        "assigns": [_assign_name(node) for node in assigns],
        "entrypoints": ["__main__" for _ in entrypoints],
    }


def _constants():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    states = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Tuple):
            names = [element.id for element in node.targets[0].elts if isinstance(element, ast.Name)]
            if names and all(name.startswith("STATE_") for name in names):
                states = _literal(node.value)
    if states is None:
        raise AssertionError("main.py state tuple changed")
    return {
        "states": list(states),
        "frame_error_kinds": sorted(_literal(
            next(
                node.value
                for node in tree.body
                if isinstance(node, ast.Assign)
                and getattr(node.targets[0], "id", "") == "_FRAME_ERR_LAST"
            )
        )),
        "frame_error_cooldown": _literal(
            next(
                node.value
                for node in tree.body
                if isinstance(node, ast.Assign)
                and getattr(node.targets[0], "id", "") == "_FRAME_ERR_COOLDOWN"
            )
        ),
        "max_catchup": _local_assignment(tree, "MAX_CATCHUP"),
        "fixed_dt_ms": _local_assignment(tree, "FIXED_DT_MS"),
        "debug_env": _debug_env(tree),
        "mixer_pre_init": _mixer_pre_init(tree),
        "keys": _key_actions(tree),
        "banner": _startup_banner(tree),
    }


def source_fixture():
    inventory = _inventory()
    classification = {}
    for name in inventory["symbols"]["names"]:
        if name not in CLASSIFICATION:
            raise AssertionError(f"main.py symbol without a classification: {name}")
        kind, target, token, note = CLASSIFICATION[name]
        classification[name] = {"kind": kind, "target": target, "token": token, "note": note}
    kinds = {}
    for row in classification.values():
        kinds[row["kind"]] = kinds.get(row["kind"], 0) + 1
    return {
        "source": "main.py",
        "file": inventory["file"],
        "symbols": inventory["symbols"],
        "classification": classification,
        "kinds": dict(sorted(kinds.items())),
        "deviations": sorted(
            name for name, row in classification.items() if row["kind"] == "deviation"
        ),
        "constants": _constants(),
    }


def verify():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    actual = source_fixture()
    if actual != fixture:
        raise AssertionError("main.py oracle drift; rerun with --write after auditing main.py")
    for name, row in actual["classification"].items():
        if row["kind"] in ("baked", "deviation"):
            continue
        target = PROJECT / row["target"]
        if not target.is_file() or row["token"] not in target.read_text(encoding="utf-8"):
            raise AssertionError(f"main.py symbol {name} lost its live target {row['target']}")
    project = PROJECT_FILE.read_text(encoding="utf-8")
    if project.count("common/max_physics_steps_per_frame=%d" % actual["constants"]["max_catchup"]) != 1:
        raise AssertionError("project.godot no longer mirrors main.py MAX_CATCHUP")
    return (
        actual["symbols"]["count"]
        + len(actual["constants"]["states"])
        + len(actual["constants"]["keys"])
        + len(actual["constants"]["banner"])
    )


def main(argv):
    if "--write" in argv:
        FIXTURE.write_text(
            json.dumps(source_fixture(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"wrote {FIXTURE.relative_to(ROOT)}")
        return 0
    print(f"PASS: {verify()} read-only main.py source checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
