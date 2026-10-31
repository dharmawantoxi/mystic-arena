#!/usr/bin/env python3
"""Execute the real read-only tactical command manager against source-shaped actors.

The fixture locks command selection, formation, hold/release timing, armed retries,
gather follow-up, and automatic castle protection without importing pygame.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import ast
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).with_name("fixtures") / "tactical_command_source.json"
INVENTORY = Path(__file__).with_name("fixtures") / "tactical_commands_inventory.json"
SOURCE = ROOT / "tactical_commands.py"
PROJECT = ROOT / "godot_rebuild"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tactical_commands import (  # noqa: E402
    GATHER_PUSH_DELAY_FRAMES,
    HOLD_RELEASE_TAIL,
    HOLD_TAP_MAX_FRAMES,
    TacticalCommand,
    TacticalCommandManager,
)


class Actor:
    def __init__(self, label, x, y, team="blue", hp=1000, max_hp=1000, alive=True):
        self.label = label
        self.name = label
        self.x = float(x)
        self.y = float(y)
        self.team = team
        self.hp = float(hp)
        self.max_hp = float(max_hp)
        self.alive = alive


class Hero(Actor):
    def __init__(self, label, x, y, team="blue", damage_dealt=0, attack_range=100):
        super().__init__(label, x, y, team)
        self.damage_dealt = damage_dealt
        self.range = attack_range
        self.destination = None
        self.destination_auto = False
        self.follow_target = None
        self.target = None
        self.is_retreating = True

    def move_to(self, x, y, auto=False):
        self.destination = (float(x), float(y))
        self.destination_auto = bool(auto)
        self.follow_target = None
        self.is_retreating = False


class Effects:
    """Records the presentation calls instead of swallowing them.

    The source wraps every effect call in `try/except`, so a spike that never
    fires is indistinguishable from one that fires — which is exactly how the
    GATHER / PROTECT CASTLE marker bursts went missing in the first port. The
    calls are part of the observable contract now.
    """

    def __init__(self):
        self.calls = []

    def add_damage_number(self, x, y, text, is_critical=False):
        self.calls.append({
            "kind": "damage_number",
            "x": round(float(x), 3),
            "y": round(float(y), 3),
            "text": text,
            "critical": bool(is_critical),
        })

    def add_death_explosion(self, x, y, team="red", size="medium"):
        self.calls.append({
            "kind": "death_explosion",
            "x": round(float(x), 3),
            "y": round(float(y), 3),
            "team": team,
            "size": size,
        })


class Game:
    def __init__(self, heroes=()):
        self.state = "playing"
        self.heroes = list(heroes)
        self.towers = []
        self.minions = []
        self.ai = SimpleNamespace(heroes=[])
        self.active_boss = None
        self.blue_base = Actor("blue_castle", 100, 620, "blue", 2000, 2000)
        self.red_base = Actor("red_castle", 1180, 100, "red", 2000, 2000)
        self.selected_hero = None
        self.selected_tower = None
        self.effects = Effects()
        self.wave_number = 1
        self.mouse_x = 640
        self.mouse_y = 360


class QuietManager(TacticalCommandManager):
    """Presentation callback remains source-equivalent but avoids optional imports."""

    def _set_feedback(self, text, color=(255, 220, 100)):
        # Banner state plus the third source side effect: a critical damage number
        # at (640, 100). `game.ui.add_notification` and `sidepanel.beri_tahu_global`
        # are no-ops in the source (`_core.add_notification` returns, the panel
        # helper returns False), so they are not modelled.
        self.feedback_text = text
        self.feedback_timer = 180
        self.feedback_color = color
        self.game.effects.add_damage_number(640, 100, text, is_critical=True)


def _point(value):
    if value is None:
        return None
    return [round(float(value[0]), 6), round(float(value[1]), 6)]


def _label(value):
    return None if value is None else value.label


def _snapshot(manager, game):
    return {
        "active": manager.active_command,
        "timer": manager.command_timer,
        "cooldown": manager.cooldown,
        "target": _label(manager.command_target),
        "point": _point(manager.gather_point),
        "point_timer": manager.gather_point_timer,
        "held": manager.held_command,
        "hold_elapsed": manager.hold_elapsed,
        "hold_fired": manager._hold_has_fired,
        "gather_push": manager._gather_push_fired,
        "feedback": manager.feedback_text,
        "effects": list(game.effects.calls),
        "heroes": [
            {
                "id": hero.label,
                "destination": _point(hero.destination),
                "follow": _label(hero.follow_target),
                "target": _label(hero.target),
                "retreating": hero.is_retreating,
            }
            for hero in game.heroes
        ],
    }


def _heroes(count, origin=(100, 200)):
    return [Hero(f"blue_{i}", origin[0] + i * 100, origin[1] + i * 20) for i in range(count)]


def source_fixture():
    cases = []

    heroes = _heroes(4)
    game = Game(heroes)
    manager = QuietManager(game)
    accepted = manager.command_gather(640, 360, silent=True)
    cases.append({"label": "gather_explicit", "accepted": accepted, "state": _snapshot(manager, game)})

    heroes = [
        Hero("blue_0", 250, 300),
        Hero("blue_1", 280, 300),
        Hero("blue_2", 500, 500),
        Hero("blue_3", 800, 600),
        Hero("blue_4", 1000, 100),
    ]
    game = Game(heroes)
    threatened = Actor("outer_tower", 300, 300, "blue", 500, 1000)
    safe = Actor("inner_tower", 800, 500, "blue", 1000, 1000)
    game.towers = [threatened, safe]
    game.minions = [Actor("red_minion_0", 320, 300, "red"), Actor("red_minion_1", 330, 310, "red")]
    game.active_boss = Actor("boss", 350, 300, "red")
    manager = QuietManager(game)
    accepted = manager.command_protect_tower(silent=True)
    cases.append({"label": "protect_most_threatened", "accepted": accepted, "state": _snapshot(manager, game)})

    heroes = _heroes(4)
    game = Game(heroes)
    manager = QuietManager(game)
    accepted = manager.command_protect_castle(silent=True)
    cases.append({"label": "protect_castle", "accepted": accepted, "state": _snapshot(manager, game)})

    heroes = _heroes(3)
    game = Game(heroes)
    game.active_boss = Actor("boss", 700, 300, "red")
    manager = QuietManager(game)
    accepted = manager.command_attack_boss(silent=True)
    cases.append({"label": "attack_boss", "accepted": accepted, "state": _snapshot(manager, game)})

    heroes = _heroes(3)
    game = Game(heroes)
    game.ai.heroes = [
        Hero("dealer_low", 750, 250, "red", damage_dealt=125),
        Hero("dealer_high", 800, 300, "red", damage_dealt=900),
        Hero("dealer_dead", 810, 320, "red", damage_dealt=5000),
    ]
    game.ai.heroes[-1].alive = False
    manager = QuietManager(game)
    accepted = manager.command_attack_damage_dealer(silent=True)
    cases.append({"label": "attack_damage_dealer", "accepted": accepted, "state": _snapshot(manager, game)})

    heroes = _heroes(2)
    game = Game(heroes)
    manager = QuietManager(game)
    manager.hold_start(TacticalCommand.GATHER, 600, 350)
    for _ in range(5):
        manager.update()
    manager.hold_end(TacticalCommand.GATHER)
    cases.append({"label": "quick_tap_keeps_duration", "accepted": True, "state": _snapshot(manager, game)})

    heroes = _heroes(2)
    game = Game(heroes)
    manager = QuietManager(game)
    manager.hold_start(TacticalCommand.PROTECT_CASTLE)
    for _ in range(35):
        manager.update()
    manager.hold_end(TacticalCommand.PROTECT_CASTLE)
    cases.append({"label": "long_hold_release_tail", "accepted": True, "state": _snapshot(manager, game)})

    heroes = _heroes(2)
    game = Game(heroes)
    manager = QuietManager(game)
    accepted = manager.hold_start(TacticalCommand.ATTACK_BOSS)
    for _ in range(10):
        manager.update()
    game.active_boss = Actor("late_boss", 700, 300, "red")
    for _ in range(5):
        manager.update()
    cases.append({"label": "armed_hold_waits_for_boss", "accepted": accepted, "state": _snapshot(manager, game)})

    heroes = [Hero("blue_0", 640, 360), Hero("blue_1", 650, 360), Hero("blue_2", 630, 360)]
    game = Game(heroes)
    game.active_boss = Actor("far_boss", 700, 360, "red")
    game.towers = [Actor("near_tower", 665, 360, "red")]
    game.ai.heroes = [Hero("enemy_hero", 680, 360, "red", damage_dealt=20)]
    manager = QuietManager(game)
    manager.hold_start(TacticalCommand.GATHER, 640, 360)
    for _ in range(GATHER_PUSH_DELAY_FRAMES):
        manager.update()
    cases.append({"label": "held_gather_push", "accepted": True, "state": _snapshot(manager, game)})

    heroes = _heroes(3)
    game = Game(heroes)
    game.blue_base.hp = 600
    game.blue_base.max_hp = 2000
    game.minions = [Actor("red_minion_0", 120, 600, "red"), Actor("red_minion_1", 140, 610, "red")]
    manager = QuietManager(game)
    manager._auto_check_timer = 89
    manager.update()
    cases.append({"label": "auto_protect_castle", "accepted": True, "state": _snapshot(manager, game)})

    return {
        "policy": {
            "duration": 600,
            "cooldown": 30,
            "hold_tap_max": HOLD_TAP_MAX_FRAMES,
            "hold_release_tail": HOLD_RELEASE_TAIL,
            "gather_push_delay": GATHER_PUSH_DELAY_FRAMES,
            "commands": [
                TacticalCommand.GATHER,
                TacticalCommand.PROTECT_TOWER,
                TacticalCommand.PROTECT_CASTLE,
                TacticalCommand.ATTACK_BOSS,
                TacticalCommand.ATTACK_DAMAGE_DEALER,
            ],
        },
        "cases": cases,
    }




# ════════════════════════════════════════════════════════════════════
# Layer 9co: the whole file, symbol by symbol
# ════════════════════════════════════════════════════════════════════

# name -> (kind, target relative to godot_rebuild/, live token, note)
CLASSIFICATION = {
    "settings": ("folded", "scripts/data/core_settings.gd", "DATA_PATH",
                 "module absent in this snapshot; the six base/screen constants live in "
                 "core settings + data/core/settings.json"),
    "math": ("folded", "scripts/match/tactical_commands.gd", "Vector2.from_angle(",
             "hypot/sin/cos/pi become Vector2 helpers and TAU"),
    "random": ("ported", "scripts/match/tactical_commands.gd", "boss_auto_roll_override",
               "seeded RandomNumberGenerator with a test override hook"),
    "HOLD_TAP_MAX_FRAMES": ("data", "scripts/match/tactical_commands.gd",
                            "const HOLD_TAP_MAX_TICKS := 20", ""),
    "HOLD_RELEASE_TAIL": ("data", "scripts/match/tactical_commands.gd",
                          "const HOLD_RELEASE_TAIL := 30", ""),
    "GATHER_PUSH_DELAY_FRAMES": ("data", "scripts/match/tactical_commands.gd",
                                 "const GATHER_PUSH_DELAY_TICKS := 240", ""),
    "TacticalCommand": ("ported", "scripts/match/tactical_commands.gd",
                        "const COMMANDS: Array[String] = [", ""),
    "TacticalCommand.GATHER": ("data", "scripts/match/tactical_commands.gd",
                               'const GATHER := "gather"', ""),
    "TacticalCommand.PROTECT_TOWER": ("data", "scripts/match/tactical_commands.gd",
                                      'const PROTECT_TOWER := "protect_tower"', ""),
    "TacticalCommand.PROTECT_CASTLE": ("data", "scripts/match/tactical_commands.gd",
                                       'const PROTECT_CASTLE := "protect_castle"', ""),
    "TacticalCommand.ATTACK_BOSS": ("data", "scripts/match/tactical_commands.gd",
                                    'const ATTACK_BOSS := "attack_boss"', ""),
    "TacticalCommand.ATTACK_DAMAGE_DEALER": ("data", "scripts/match/tactical_commands.gd",
                                             'const ATTACK_DAMAGE_DEALER := "attack_damage_dealer"',
                                             ""),
    "TacticalCommandManager": ("ported", "scripts/match/tactical_commands.gd",
                               'var active_command := ""', ""),
    "BLUE_BASE_X": ("dead", "", "", "fallback constant the source never reads"),
    "BLUE_BASE_Y": ("dead", "", "", "fallback constant the source never reads"),
    "RED_BASE_X": ("data", "scripts/match/tactical_commands.gd",
                   "const RED_BASE := Vector2(1180, 100)", ""),
    "RED_BASE_Y": ("data", "scripts/match/tactical_commands.gd",
                   "const RED_BASE := Vector2(1180, 100)", ""),
    "SCREEN_WIDTH": ("data", "scripts/match/tactical_commands.gd",
                     "const SCREEN_WIDTH := 1280", ""),
    "SCREEN_HEIGHT": ("data", "scripts/match/tactical_commands.gd",
                      "const SCREEN_HEIGHT := 720", ""),
    "TacticalCommandManager.__init__": ("ported", "scripts/match/tactical_commands.gd",
                                        "func _init() -> void:", ""),
    "TacticalCommandManager.can_issue": ("ported", "scripts/match/tactical_commands.gd",
                                         "func can_issue(world: Object) -> bool:", ""),
    "TacticalCommandManager._set_feedback": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _feedback(world: Object, text: String, color: Color) -> void:",
        "notification and side panel toast are source no-ops"),
    "TacticalCommandManager._get_alive_blue_heroes": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _alive_blue_heroes(world: Object) -> Array:", ""),
    "TacticalCommandManager._clear_hero_retreat": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _clear_retreat(heroes: Array) -> void:", ""),
    "TacticalCommandManager._issuers": ("folded", "scripts/match/tactical_commands.gd",
                                        "func issue(", "dict dispatch became a match"),
    "TacticalCommandManager.hold_start": ("ported", "scripts/match/tactical_commands.gd",
                                          "func hold_start(", ""),
    "TacticalCommandManager.hold_end": ("ported", "scripts/match/tactical_commands.gd",
                                        'func hold_end(name: String = "") -> void:', ""),
    "TacticalCommandManager.hold_active": ("ported", "scripts/match/tactical_commands.gd",
                                           "func hold_active() -> bool:", ""),
    "TacticalCommandManager._issue_held": ("ported", "scripts/match/tactical_commands.gd",
                                           "func _issue_held(world: Object, loud: bool) -> bool:",
                                           ""),
    "TacticalCommandManager._gather_hold_push": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _gather_hold_push(world: Object) -> bool:", ""),
    "TacticalCommandManager._try_gather_push": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _try_gather_push(world: Object) -> bool:", ""),
    "TacticalCommandManager.command_gather": ("ported", "scripts/match/tactical_commands.gd",
                                              "func _command_gather(", ""),
    "TacticalCommandManager.command_protect_tower": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _command_protect_tower(world: Object, target_id: int, silent: bool) -> bool:", ""),
    "TacticalCommandManager.command_protect_castle": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _command_protect_castle(world: Object, silent: bool) -> bool:", ""),
    "TacticalCommandManager.command_attack_boss": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _command_attack_boss(world: Object, silent: bool) -> bool:", ""),
    "TacticalCommandManager._find_enemy_damage_dealer": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _find_enemy_damage_dealer(world: Object) -> HeroState:", ""),
    "TacticalCommandManager.command_attack_damage_dealer": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _command_attack_damage_dealer(world: Object, silent: bool) -> bool:", ""),
    "TacticalCommandManager._find_most_threatened_tower": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _find_most_threatened_tower(world: Object) -> StructureState:", ""),
    "TacticalCommandManager._count_enemies_near": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _count_enemies_near(world: Object, point: Vector2, radius: float) -> int:", ""),
    "TacticalCommandManager._find_nearest_enemy_target": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _find_nearest_enemy_target(world: Object, point: Vector2) -> Object:", ""),
    "TacticalCommandManager.update": ("ported", "scripts/match/tactical_commands.gd",
                                      "func step_tick(world: Object) -> void:", ""),
    "TacticalCommandManager._auto_evaluate_protect": (
        "ported", "scripts/match/tactical_commands.gd",
        "func _auto_evaluate_protect(world: Object) -> void:", ""),
    "TacticalCommandManager._get_command_color": (
        "ported", "scripts/match/tactical_commands.gd", "func command_color() -> Color:", ""),
    "TacticalCommandManager.draw_world": (
        "ported", "scripts/ui/tactical_layout.gd", "static func world_ops(",
        "layer 9bi2 op list"),
    "TacticalCommandManager.draw_ui": (
        "ported", "scripts/ui/tactical_layout.gd", "static func feedback_ops(",
        "layer 9bi2 op list"),
    "TacticalCommandManager.draw": (
        "folded", "scenes/prototype/prototype_view.gd", "TacticalLayout.feedback_ops(",
        "legacy wrapper: the view paints world and UI ops separately"),
    "TacticalCommandManager.get_status_text": (
        "ported", "scripts/match/tactical_commands.gd",
        "func status_text(world: Object) -> String:", ""),
}


def _class_members(node):
    names = []
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(f"{node.name}.{child.name}")
        elif isinstance(child, ast.Assign):
            for target in child.targets:
                if isinstance(target, ast.Name):
                    names.append(f"{node.name}.{target.id}")
    return names


def symbol_inventory():
    text = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imports = []
    functions = []
    assigns = []
    classes = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Try):
            # `from settings import (...)` with an `except ImportError` fallback
            for inner in node.body:
                if isinstance(inner, ast.ImportFrom):
                    imports.append(inner.module or "")
            for handler in node.handlers:
                for inner in handler.body:
                    if isinstance(inner, ast.Assign):
                        for target in inner.targets:
                            if isinstance(target, ast.Name):
                                assigns.append(target.id)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
            classes.extend(_class_members(node))
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigns.append(target.id)
    names = imports + classes + functions + assigns
    return {
        "file": {
            "file": "tactical_commands.py",
            "lines": len(text.splitlines()),
            "classes": 2,
            "functions": 0,
            "assigns": len(assigns),
            "imports": len(imports),
        },
        "symbols": {"count": len(names), "names": names},
        "imports": imports,
        "classes": [name for name in classes if "." not in name],
        "methods": [name for name in classes if "." in name],
        "assigns": assigns,
    }


def _native_functions(target):
    text = (PROJECT / target).read_text(encoding="utf-8")
    return set(re.findall(r"^func ([A-Za-z_0-9]+)\(", text, re.M))


def folder_fixture():
    inventory = symbol_inventory()
    classification = {}
    for name in inventory["symbols"]["names"]:
        if name not in CLASSIFICATION:
            raise AssertionError(f"tactical_commands.py symbol without a classification: {name}")
        kind, target, token, note = CLASSIFICATION[name]
        classification[name] = {"kind": kind, "target": target, "token": token, "note": note}
    kinds = {}
    for row in classification.values():
        kinds[row["kind"]] = kinds.get(row["kind"], 0) + 1
    mapped = set()
    targets = set()
    for row in classification.values():
        if row["target"] and row["token"].startswith("func "):
            mapped.add(row["token"][5:].split("(")[0])
        if row["target"]:
            targets.add(row["target"])
    native_only = _native_functions("scripts/match/tactical_commands.gd") - mapped
    return {
        "source": "tactical_commands.py",
        "file": inventory["file"],
        "symbols": inventory["symbols"],
        "classification": classification,
        "kinds": dict(sorted(kinds.items())),
        "deviations": sorted(
            name for name, row in classification.items() if row["kind"] == "deviation"
        ),
        "dead": sorted(name for name, row in classification.items() if row["kind"] == "dead"),
        "native_only": sorted(native_only),
        "policy": {
            "duration": 600,
            "cooldown": 30,
            "point_ticks": 150,
            "feedback_ticks": 180,
            "hold_tap_max": HOLD_TAP_MAX_FRAMES,
            "hold_release_tail": HOLD_RELEASE_TAIL,
            "gather_push_delay": GATHER_PUSH_DELAY_FRAMES,
            "sound_click_volume": 0.8,
            "sound_skill_volume": 0.9,
        },
    }


def verify_folder():
    expected = json.loads(INVENTORY.read_text(encoding="utf-8"))
    actual = folder_fixture()
    if actual != expected:
        raise AssertionError("tactical_commands.py inventory drift; rerun with --write")
    for name, row in actual["classification"].items():
        if row["kind"] in ("dead", "deviation"):
            continue
        target = PROJECT / row["target"]
        if not target.is_file() or row["token"] not in target.read_text(encoding="utf-8"):
            raise AssertionError(f"tactical_commands.py symbol {name} lost its live target")
    return actual["symbols"]["count"] + len(actual["policy"]) + len(actual["native_only"])


def main():
    arguments = sys.argv[1:]
    with redirect_stdout(StringIO()):
        actual = source_fixture()
    expected = json.loads(FIXTURE.read_text(encoding="utf-8")) if FIXTURE.exists() else None
    folder = folder_fixture()
    folder_expected = (
        json.loads(INVENTORY.read_text(encoding="utf-8")) if INVENTORY.exists() else None
    )
    if "--write" in arguments or expected != actual or folder_expected != folder:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        INVENTORY.write_text(
            json.dumps(folder, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        if "--write" not in arguments and expected is not None:
            raise SystemExit("FAIL: tactical command fixture drift (fixtures refreshed)")
        print(f"WROTE: {FIXTURE.name} + {INVENTORY.name}")
        return
    print(
        f"PASS: {len(actual['cases'])} tactical command cases + "
        f"{verify_folder()} inventory facts"
    )


if __name__ == "__main__":
    main()
