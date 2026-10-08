"""Read-only AST oracle for player build choices and paid shield commands.

The original Game/InputHandler/Tower/Castle methods execute against small
source-shaped objects. No pygame module or legacy game runtime is imported.
"""
import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from ai_upgrade_source_oracle import compile_subset
from structure_source_oracle import ROOT, namespace

FIXTURE = Path(__file__).parent / "fixtures/player_structure_command_source.json"
PATHS = ("archer", "cannon", "ice", "mage")


def source_fixture():
    env = namespace()
    env["TOWER_UPGRADE_PATHS"] = {
        path: env[path.upper() + "_LEVELS"] for path in PATHS
    }
    core = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    castle_cost = next(
        node
        for node in core.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "CASTLE_SHIELD_COST"
            for target in node.targets
        )
    )
    exec(
        compile(ast.Module(body=[castle_cost], type_ignores=[]), "<source shield alias>", "exec"),
        env,
    )
    entities = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    tower_type = compile_subset(
        entities,
        "Tower",
        (
            "__init__",
            "_apply_level_stats",
            "upgrade",
            "can_upgrade",
            "upgrade_cost",
            "sell_value",
            "can_activate_regen_shield",
            "regen_shield_cost",
            "activate_regen_shield",
        ),
        env,
    )
    castle_type = compile_subset(
        entities,
        "Castle",
        (
            "__init__",
            "_apply_level_stats",
            "set_wave",
            "can_activate_castle_shield",
            "castle_shield_cost",
            "activate_castle_shield",
        ),
        env,
    )
    env["Tower"] = tower_type
    game_type = compile_subset(
        core, "Game", ("try_build_tower", "try_activate_castle_shield"), env
    )
    input_type = compile_subset(
        core,
        "InputHandler",
        ("handle_build_popup_click", "handle_popup_click", "_try_activate_regen_shield"),
        env,
    )
    result = {
        "constants": {
            "build_cost": 100,
            "regen_cost": env["TOWER_REGEN_SHIELD_COST"],
            "regen_min_level": env["TOWER_REGEN_SHIELD_MIN_LEVEL"],
            "castle_cost": env["CASTLE_SHIELD_COST"],
            "castle_free_waves": env["CASTLE_SHIELD_FREE_WAVES"],
        },
        "routes": command_routes(input_type),
        "builds": build_cases(game_type),
        "regen": regen_cases(tower_type, input_type, env),
        "castle": castle_cases(castle_type, game_type, env),
    }
    return result


def command_routes(input_type):
    rows = []
    for path in PATHS:
        calls = []
        game = SimpleNamespace(
            ui_buttons={"build_" + path: True},
            try_build_tower=lambda value, out=calls: out.append(["build", value]),
            close_build_popup=lambda: calls.append(["close"]),
        )
        handler = input_type()
        handler.game = game
        handler._kena = lambda rect, _x, _y: bool(rect)
        handled = handler.handle_build_popup_click(10, 10, 1)
        rows.append({"button": "build_" + path, "handled": handled, "calls": calls})
    for action in ("regen_shield", "castle_shield"):
        calls = []
        game = SimpleNamespace(
            ui_buttons={"popup_" + action: True},
            try_activate_castle_shield=lambda out=calls: out.append(["castle_shield"]),
        )
        handler = input_type()
        handler.game = game
        handler._kena = lambda rect, _x, _y: bool(rect)
        handler._try_activate_regen_shield = lambda out=calls: out.append(["regen_shield"])
        handled = handler.handle_popup_click(10, 10, 1)
        rows.append({"button": "popup_" + action, "handled": handled, "calls": calls})
    return rows


def build_cases(game_type):
    rows = []
    for path in PATHS:
        for gold in (99, 100):
            slot = {"x": 250, "y": 170, "lane": "top", "taken": False}
            game = SimpleNamespace(
                build_popup_slot=slot,
                gold=gold,
                towers=[],
                close_build_popup=lambda: setattr(game, "build_popup_slot", None),
            )
            game_type.try_build_tower(game, path)
            tower = game.towers[0] if game.towers else None
            receipt = None
            if tower is not None:
                receipt = {
                    "path": tower.tower_type,
                    "name": tower.name,
                    "level": tower.level,
                    "team": tower.team,
                    "lane": tower.lane,
                    "position": [tower.x, tower.y],
                    "max_hp": tower.max_hp,
                    "hp": tower.hp,
                    "shield_max": tower.shield_max,
                    "shield": tower.shield,
                    "damage": tower.damage,
                    "range": tower.range,
                    "cooldown": tower.attack_cooldown,
                    "armor": tower.armor,
                    "splash": tower.splash,
                    "slow": tower.slow,
                    "chain": tower.chain,
                }
            rows.append(
                {
                    "label": f"build_{path}_{gold}",
                    "input": {"path": path, "gold": gold},
                    "gold": game.gold,
                    "taken": slot["taken"],
                    "popup_open": game.build_popup_slot is not None,
                    "receipt": receipt,
                }
            )
    return rows


def _tower_at_level(tower_type, level, team="blue"):
    tower = tower_type(500, 340, team)
    while tower.level < level:
        assert tower.upgrade("archer" if tower.level == 1 else None)
    return tower


def regen_cases(tower_type, input_type, env):
    specs = (
        ("below_level", 3, 850, "blue", True),
        ("poor", 4, 849, "blue", True),
        ("exact", 4, 850, "blue", True),
        ("repeat", 4, 1700, "blue", True),
        ("enemy", 4, 1700, "red", True),
        ("dead", 4, 1700, "blue", False),
    )
    rows = []
    for label, level, gold, team, alive in specs:
        tower = _tower_at_level(tower_type, level, team)
        tower.alive = alive
        tower.shield = 1
        game = SimpleNamespace(
            selected_tower=tower,
            gold=gold,
            effects=SimpleNamespace(add_damage_number=lambda *args, **kwargs: None),
        )
        handler = input_type()
        handler.game = game
        states = []
        for _ in range(2):
            handler._try_activate_regen_shield()
            states.append(
                {
                    "gold": game.gold,
                    "active": tower.regen_shield_active,
                    "shield": tower.shield,
                    "shield_max": tower.shield_max,
                    "refund": tower.sell_value(),
                }
            )
        rows.append(
            {
                "label": label,
                "input": {
                    "level": level,
                    "gold": gold,
                    "team": team,
                    "alive": alive,
                },
                "states": states,
            }
        )
    assert env["TOWER_REGEN_SHIELD_COST"] == 850
    return rows


def castle_cases(castle_type, game_type, env):
    specs = (
        ("free", 10, 850),
        ("poor", 11, 849),
        ("exact", 11, 850),
        ("repeat", 11, 1700),
    )
    rows = []
    for label, wave, gold in specs:
        castle = castle_type(1180, 100, "blue")
        castle.set_wave(wave)
        castle.shield = 1
        game = SimpleNamespace(
            blue_base=castle,
            gold=gold,
            effects=SimpleNamespace(add_damage_number=lambda *args, **kwargs: None),
        )
        states = []
        for _ in range(2):
            game_type.try_activate_castle_shield(game)
            states.append(
                {
                    "gold": game.gold,
                    "purchased": castle.castle_shield_purchased,
                    "free": castle.free_shield_active,
                    "active": castle.shield_active,
                    "shield": castle.shield,
                    "shield_max": castle.shield_max,
                }
            )
        rows.append(
            {
                "label": label,
                "input": {"wave": wave, "gold": gold},
                "states": states,
            }
        )
    assert env["CASTLE_SHIELD_COST"] == 850
    return rows


if __name__ == "__main__":
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), (
            "Player structure command source drift"
        )
    print(
        "PASS: player structure commands — "
        f"{len(actual['routes'])} routes, {len(actual['builds'])} builds, "
        f"{len(actual['regen'])} regen and {len(actual['castle'])} castle cases"
    )
