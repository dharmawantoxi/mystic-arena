"""Whole-file oracle for `_core.py` (10.281 lines, eight merged modules).

`_core.py` is the pygame app shell merged from eight files:

    settings.py (28-1296)   game.py (1297-3042)      menu.py (3043-7694)
    game_input.py (7695-8505)                        game_ui.py (8506-8690)
    game_dev.py (8691-9083) game_settings.py (9084-9298)
    controller_manager.py (9299-10281) + the `sys.modules` alias shim

The runtime behaviour of those modules already lives in the Godot rebuild (the match
simulation, the menu scene, the controller adapter, the side panel, the settings
stores), so this oracle does two things:

* it inventories the file (sections, 10 classes, 235 methods, 11 module-level
  functions, 139 settings constants, the alias shim) and classifies **every symbol**
  with a target file and a token that target must contain, and
* it ships the `settings.py` half as data: the constants are executed for real
  (`exec` of lines 28-1240 with a stub pygame) and written to
  `data/core/settings.json`, together with a `parity` table that maps the constants
  whose value a live Godot module already pins to the `const NAME := value` line
  that carries it. That turns the settings migration into a drift guard instead of a
  copy.

Run: python godot_rebuild/tests/core_source_oracle.py --write
"""

import argparse
import ast
import json
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "_core.py"
GODOT = ROOT / "godot_rebuild"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "core_source.json"
SETTINGS_DATA = GODOT / "data" / "core" / "settings.json"

SECTIONS = [
    ("settings", 28, 1296),
    ("game", 1297, 3042),
    ("menu", 3043, 7694),
    ("game_input", 7695, 8505),
    ("game_ui", 8506, 8690),
    ("game_dev", 8691, 9083),
    ("game_settings", 9084, 9298),
    ("controller_manager", 9299, 10281),
]
SETTINGS_BLOCK = (28, 1291)
META_CONSTANTS = {
    "_globals_before_settings", "_settings_public", "_settings_alias",
    "_settings_meta", "_original_get_all_hero_types_shop_prices",
}

CLASS_TARGETS = {
    "TowerDebuffMixin": ("ported", "godot_rebuild/scripts/combat/unit_state.gd",
                         "func apply_armor_shred(",
                         "matematika debuff/status ada di unit state bersama"),
    "Game": ("ported", "godot_rebuild/scripts/match/prototype_battle.gd",
             "func _roll_mini_boss_schedule(",
             "simulasi match menggantikan loop Game pygame"),
    "MenuState": ("ported", "godot_rebuild/scenes/menu/main_menu.gd",
                  "func _open_how_to_play(",
                  "layar menu berupa scene, bukan string state"),
    "Menu": ("ported", "godot_rebuild/scenes/menu/main_menu.gd",
             "func _toggle_input_mode(",
             "scene menu + layout `scripts/ui/menu_*` yang menggambar"),
    "InputHandler": ("ported", "godot_rebuild/scenes/prototype/prototype_screen.gd",
                     "func _primary_action(",
                     "routing tap/drag ada di lapisan input prototype screen"),
    "UIRenderer": ("ported", "godot_rebuild/scripts/ui/side_panel.gd",
                   "func update_snapshot(",
                   "dock panel memegang permukaan koordinator"),
    "DevMode": ("deviation", "", "",
                "cheat F1-F12 adalah perkakas developer, bukan perilaku pemain"),
    "GameSettings": ("ported", "godot_rebuild/scripts/settings/presentation_settings_store.gd",
                     "static func defaults()",
                     "setelan dipersist lewat settings store"),
    "InputMode": ("ported", "godot_rebuild/scripts/input/controller_runtime.gd",
                  "signal action_requested(",
                  "adapter controller memodelkan mode, bukan enum string"),
    "ControllerManager": ("ported", "godot_rebuild/scripts/input/controller_runtime.gd",
                          "func rumble(",
                          "Godot menormalisasi pad, jadi adapter memindahkan perilakunya"),
}

# Source methods whose responsibility lives under a different conventional name in the
# replacement module (Godot calls it _process/_draw, the pygame shell called it
# update/draw). Only pairs that really do the same job are listed.
METHOD_ALIASES = {
    "Game": {"update": "step_tick", "reset": "_init", "handle_click": "clicked_shop_at"},
    "Menu": {"update": "_process", "draw": "_layout_source_menu",
             "handle_click": "_click_and_emit", "reset": "_refresh_localized_labels"},
    "InputHandler": {"update": "_process", "handle_click": "_primary_action"},
    "UIRenderer": {"draw": "_draw", "update": "update_snapshot", "handle_click": "_gui_input"},
    "ControllerManager": {"update": "advance_frame"},
}

MODULE_TARGETS = {
    "settings": ("data", "godot_rebuild/data/core/settings.json", '"SCREEN_WIDTH":',
                 "seluruh blok settings.py dikirim sebagai data"),
    "game": CLASS_TARGETS["Game"],
    "menu": CLASS_TARGETS["Menu"],
    "game_input": CLASS_TARGETS["InputHandler"],
    "game_ui": CLASS_TARGETS["UIRenderer"],
    "game_dev": CLASS_TARGETS["DevMode"],
    "game_settings": CLASS_TARGETS["GameSettings"],
    "controller_manager": CLASS_TARGETS["ControllerManager"],
}

TOP_TARGETS = {
    "_PANEL_AKTIF": ("ported", "godot_rebuild/scripts/ui/side_panel.gd", "func is_active()",
                     "dock panel menjawab apakah panel kanan ada"),
    "compute_starting_gold": ("ported", "godot_rebuild/scripts/match/prototype_battle.gd",
                              "compute_starting_gold", ""),
    "compute_gold_per_second": ("ported", "godot_rebuild/scripts/match/prototype_battle.gd",
                                "compute_gold_per_second", ""),
    "format_gold_rate": ("ported", "godot_rebuild/scripts/match/match_economy.gd",
                         "format_gold_rate", ""),
    "_default_hero_unlock_cost": ("ported", "godot_rebuild/scripts/match/hero_unlock_store.gd",
                                  "static func entry(", "biaya unlock per hero berasal dari data"),
    "get_all_hero_types": ("ported", "godot_rebuild/scripts/match/hero_unlock_store.gd",
                           "static func entry(", "katalog hero dikirim sebagai data"),
    "get_hero_shop_order": ("ported", "godot_rebuild/scripts/match/hero_unlock_store.gd",
                            "static func ids_for_tab(", ""),
    "fmt_idr": ("ported", "godot_rebuild/scripts/match/topup_currency.gd", "fmt_idr", ""),
    "_install_root_aliases": ("meta", "", "", "Godot punya modul nyata, tanpa shim alias"),
    "install_aliases": ("meta", "", "", "pemasang alias idempoten, tidak perlu di Godot"),
}

HISTOGRAM_KEYS = ("data", "dead", "deviation", "folded", "meta", "native", "ported")
FUNC_RE = re.compile(r"^(?:static )?func ([a-zA-Z0-9_]+)\(", re.M)


def _source():
    return CORE.read_text(encoding="utf-8")


def _tree():
    return ast.parse(_source())


def section_of(line):
    for name, start, end in SECTIONS:
        if start <= line <= end:
            return name
    return "prelude"


def inventory():
    text = _source()
    tree = _tree()
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    top_functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    methods = sum(len([m for m in node.body if isinstance(m, ast.FunctionDef)])
                  for node in classes)
    constants = [node for node in tree.body
                 if isinstance(node, ast.Assign) and section_of(node.lineno) == "settings"]
    return {
        "file": "_core.py",
        "lines": len(text.splitlines()),
        "sections": len(SECTIONS),
        "classes": len(classes),
        "methods": methods,
        "top_functions": len(top_functions),
        "settings_constants": len(constants),
    }


def section_ranges():
    rows = []
    for index, (name, start, end) in enumerate(SECTIONS):
        rows.append({"name": name, "start": start, "end": end, "lines": end - start + 1})
        if index + 1 < len(SECTIONS) and SECTIONS[index + 1][1] != end + 1:
            raise AssertionError("sections are not contiguous at %s" % name)
    return rows


def settings_payload():
    """Execute the settings half for real; the alias shim at the end is skipped."""
    lines = _source().splitlines()
    block = "\n".join(lines[SETTINGS_BLOCK[0] - 1:SETTINGS_BLOCK[1]])
    if "pygame" not in sys.modules:
        sys.modules["pygame"] = types.ModuleType("pygame")
    namespace = {"__name__": "_core_settings", "sys": sys, "types": types,
                 "_types": types, "_globals_before_settings": set()}
    exec(compile(block, str(CORE), "exec"), namespace)  # noqa: S102 - source oracle
    values = {}
    for node in _tree().body:
        if not isinstance(node, ast.Assign):
            continue
        if section_of(node.lineno) != "settings":
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            if name in META_CONSTANTS or name.startswith("__"):
                continue
            if name not in namespace:
                raise AssertionError("%s did not evaluate" % name)
            value = namespace[name]
            if callable(value):
                continue
            values[name] = {"line": node.lineno, "value": _plain(value)}
    return values


def _plain(value):
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    return value


def settings_document():
    return {
        "source": "_core.py settings.py (lines 28-1291), executed by "
                  "tests/core_source_oracle.py",
        "constants": {name: row["value"] for name, row in sorted(settings_payload().items())},
    }


# ── parity: which live Godot constant already pins a settings value ──────
def _godot_constants():
    found = {}
    for path in sorted(GODOT.rglob("*.gd")):
        relative = str(path.relative_to(ROOT))
        if "/tests/" in relative:
            continue
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"^const ([A-Z0-9_]+)\s*:?=\s*([^#\n]+)", text, re.M):
            found.setdefault(match.group(1), []).append(
                (relative, match.group(2).strip(), text.count("\n", 0, match.start()) + 1)
            )
    return found


def _suffixes(name):
    parts = name.split("_")
    return ["_".join(parts[index:]) for index in range(len(parts))]


def parity_rows():
    constants = settings_payload()
    godot = _godot_constants()
    rows = []
    for name, row in sorted(constants.items()):
        value = row["value"]
        if isinstance(value, (str, bool, list, dict)):
            continue
        wanted = "%g" % value
        for suffix in _suffixes(name):
            if suffix not in godot:
                continue
            for path, literal, line in godot[suffix]:
                if literal.replace(".0", "") != wanted.replace(".0", ""):
                    continue
                rows.append({"constant": name, "value": value, "godot_const": suffix,
                             "target": path, "literal": literal, "line": line})
                break
            break
    return rows


# ── classification ───────────────────────────────────────────────────────
def _called_names():
    found = set()
    for path in sorted(ROOT.rglob("*.py")):
        relative = str(path.relative_to(ROOT))
        if relative.startswith("godot_rebuild") or "__pycache__" in relative:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                if name:
                    found.add(name)
            elif isinstance(node, ast.Attribute):
                found.add(node.attr)
    return found


def _godot_functions(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    return {}, set(FUNC_RE.findall(text))


def _target_functions(target):
    text = (ROOT / target).read_text(encoding="utf-8")
    return set(FUNC_RE.findall(text))


def symbol_rows():
    tree = _tree()
    called = _called_names()
    rows = []

    for name, _, _ in SECTIONS:
        kind, target, token, note = MODULE_TARGETS[name]
        rows.append({"symbol": "module:%s" % name, "kind": kind, "target": target,
                     "token": token, "note": note})

    for node in tree.body:
        if isinstance(node, ast.Assign) and section_of(node.lineno) == "settings":
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                name = target.id
                if name in META_CONSTANTS:
                    rows.append({"symbol": "settings:%s" % name, "kind": "meta",
                                 "target": "", "token": "",
                                 "note": "bookkeeping modul, bukan nilai permainan"})
                    continue
                rows.append({"symbol": "settings:%s" % name, "kind": "data",
                             "target": "godot_rebuild/data/core/settings.json",
                             "token": '"%s":' % name,
                             "note": "baris settings.py %d" % node.lineno})

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        kind, target, token, note = CLASS_TARGETS[node.name]
        rows.append({"symbol": "class:%s" % node.name, "kind": kind, "target": target,
                     "token": token, "note": note})
        for method in node.body:
            if not isinstance(method, ast.FunctionDef):
                continue
            symbol = "class:%s.%s" % (node.name, method.name)
            if kind == "deviation":
                rows.append({"symbol": symbol, "kind": "deviation", "target": "", "token": "",
                             "note": "cheat F1-F12 adalah perkakas developer"})
                continue
            functions = _target_functions(target)
            if method.name in functions:
                rows.append({"symbol": symbol, "kind": "ported", "target": target,
                             "token": "func %s(" % method.name, "note": ""})
                continue
            alias = METHOD_ALIASES.get(node.name, {}).get(method.name)
            if alias and alias in functions:
                rows.append({"symbol": symbol, "kind": "ported", "target": target,
                             "token": "func %s(" % alias,
                             "note": "hook %s pygame menjadi %s di %s"
                                     % (method.name, alias, target.split("/")[-1])})
                continue
            if method.name not in called:
                rows.append({"symbol": symbol, "kind": "dead", "target": "", "token": "",
                             "note": "tidak ada call-site di pohon pygame"})
                continue
            rows.append({"symbol": symbol, "kind": "folded", "target": target, "token": token,
                         "note": "berjalan di alur %s, tanpa fungsi 1:1"
                                 % target.split("/")[-1]})

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        symbol = "top:%s@%d" % (node.name, node.lineno)
        kind, target, token, note = TOP_TARGETS[node.name]
        if node.name == "get_all_hero_types" and node.lineno > 1200:
            kind, target, token = "meta", "", ""
            note = "definisi kedua menimpa yang pertama; override kebijakan shop yang menang"
        rows.append({"symbol": symbol, "kind": kind, "target": target, "token": token,
                     "note": note})

    rows.append({"symbol": "shim:_install_root_aliases", "kind": "meta", "target": "",
                 "token": "", "note": "peta alias sys.modules untuk 25 nama modul lama"})
    rows.append({"symbol": "shim:install_aliases", "kind": "meta", "target": "", "token": "",
                 "note": "pembungkus idempoten _install_root_aliases"})
    rows.append({"symbol": "shim:_CORE_MOD", "kind": "meta", "target": "", "token": "",
                 "note": "referensi diri modul untuk peta alias"})
    return _dedupe(rows)


def _dedupe(rows):
    """`FPS` and the `hp` property pair are defined twice; keep one row per symbol."""
    unique = {}
    order = []
    for row in rows:
        name = row["symbol"]
        if name in unique:
            merged = [text for text in (unique[name]["note"], row["note"]) if text]
            unique[name]["note"] = ", ".join(dict.fromkeys(merged))
            continue
        unique[name] = row
        order.append(name)
    return [unique[name] for name in order]


## Names assigned more than once inside the settings block (`FPS = 60` appears twice).
def reassignments():
    found = {}
    for node in _tree().body:
        if not isinstance(node, ast.Assign) or section_of(node.lineno) != "settings":
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                found.setdefault(target.id, []).append(node.lineno)
    return {name: lines for name, lines in found.items() if len(lines) > 1}


def dead_helpers(rows):
    return sorted(row["symbol"] for row in rows if row["kind"] == "dead")


def duplicates():
    tree = _tree()
    found = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            found.setdefault(node.name, []).append(node.lineno)
        elif isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, ast.FunctionDef):
                    key = "class:%s.%s" % (node.name, member.name)
                    found.setdefault(key, []).append(member.lineno)
    return {name: {"lines": lines, "copies": len(lines)}
            for name, lines in found.items() if len(lines) > 1}


def source_fixture():
    rows = symbol_rows()
    histogram = {}
    for row in rows:
        histogram[row["kind"]] = histogram.get(row["kind"], 0) + 1
    return {
        "file": inventory(),
        "sections": section_ranges(),
        "symbols": {"count": len(rows), "kinds": histogram},
        "classification": {row["symbol"]: {"kind": row["kind"], "target": row["target"],
                                           "token": row["token"], "note": row["note"]}
                           for row in rows},
        "dead_helpers": dead_helpers(rows),
        "duplicates": duplicates(),
        "reassignments": reassignments(),
        "settings": {"count": len(settings_payload()),
                     "keys": sorted(settings_payload())},
        "parity": parity_rows(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="rewrite the JSON fixtures")
    parser.add_argument("--check", action="store_true", help="compare against the fixtures")
    args = parser.parse_args(argv)
    data = source_fixture()
    document = settings_document()
    if args.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_DATA.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
        SETTINGS_DATA.write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")
        print("wrote %s (%d symbols) and %s (%d constants)" %
              (FIXTURE, data["symbols"]["count"], SETTINGS_DATA, data["settings"]["count"]))
        return 0
    existing = json.loads(FIXTURE.read_text(encoding="utf-8")) if FIXTURE.exists() else None
    existing_data = (json.loads(SETTINGS_DATA.read_text(encoding="utf-8"))
                     if SETTINGS_DATA.exists() else None)
    if args.check and (existing != data or existing_data != document):
        print("FAIL: fixtures are stale; rerun with --write")
        return 1
    print(json.dumps({"file": data["file"], "kinds": data["symbols"]["kinds"],
                      "parity": len(data["parity"]), "dead": len(data["dead_helpers"])},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
