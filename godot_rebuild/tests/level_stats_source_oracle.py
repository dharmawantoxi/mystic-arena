#!/usr/bin/env python3
"""Read-only oracle for source match rewards and per-level statistics.

The oracle executes SaveManager's real level-stat methods plus the exact reward
loops from Game.update and the real ComboCounter. Pygame and the game bootstrap
are never imported.
"""
from __future__ import annotations

import argparse
import ast
import copy
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SYSTEM_SOURCE = ROOT / "_system.py"
CORE_SOURCE = ROOT / "_core.py"
RENDER_SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).with_name("fixtures") / "level_stats_source.json"


def _class_node(path: Path, name: str) -> ast.ClassDef:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name)


def _method(node: ast.ClassDef, name: str) -> ast.FunctionDef:
    return next(item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == name)


def _source_save_manager():
    source = _class_node(SYSTEM_SOURCE, "SaveManager")
    methods = [
        copy.deepcopy(_method(source, name))
        for name in ("get_level_stats", "update_level_stats", "format_time")
    ]
    stub = ast.ClassDef(
        name="SaveManager",
        bases=[],
        keywords=[],
        decorator_list=[],
        body=methods,
    )
    module = ast.fix_missing_locations(ast.Module(body=[stub], type_ignores=[]))
    env: dict[str, object] = {}
    exec(compile(module, "<source SaveManager level stats>", "exec"), env)
    return env["SaveManager"]


def _source_combo_counter():
    node = copy.deepcopy(_class_node(RENDER_SOURCE, "ComboCounter"))
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    env: dict[str, object] = {}
    exec(compile(module, "<source ComboCounter>", "exec"), env)
    return env["ComboCounter"]


def _source_reward_method():
    game = _class_node(CORE_SOURCE, "Game")
    update = _method(game, "update")

    def source_text(node: ast.AST) -> str:
        return ast.unparse(node)

    minion_loop = next(
        node
        for node in update.body
        if isinstance(node, ast.For)
        and "self.total_kills += 1" in source_text(node)
        and "combo_counter.add_kill()" in source_text(node)
    )
    tower_loop = next(
        node
        for node in update.body
        if isinstance(node, ast.For) and "self.red_towers_destroyed += 1" in source_text(node)
    )
    hero_loop = next(
        node
        for node in update.body
        if isinstance(node, ast.For) and "hero_reward = 150" in source_text(node)
    )
    effects_update = next(
        node
        for node in update.body
        if isinstance(node, ast.Expr) and source_text(node) == "self.effects.update()"
    )
    minion_text = source_text(minion_loop)
    assert minion_text.index("current_combo =") < minion_text.index("self.max_combo =")
    assert minion_text.index("self.max_combo =") < minion_text.index("combo_counter.add_kill()")

    method = ast.FunctionDef(
        name="apply_rewards",
        args=ast.arguments(
            posonlyargs=[],
            args=[ast.arg(arg="self"), ast.arg(arg="all_heroes")],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
        ),
        body=[
            copy.deepcopy(minion_loop),
            copy.deepcopy(tower_loop),
            copy.deepcopy(hero_loop),
            copy.deepcopy(effects_update),
        ],
        decorator_list=[],
    )
    stub = ast.ClassDef(
        name="SourceRewards",
        bases=[],
        keywords=[],
        decorator_list=[],
        body=[method],
    )
    module = ast.fix_missing_locations(ast.Module(body=[stub], type_ignores=[]))
    env: dict[str, object] = {}
    exec(compile(module, "<source Game reward loops>", "exec"), env)
    return env["SourceRewards"].apply_rewards


class EffectsProbe:
    def __init__(self, combo):
        self.combo_counter = combo
        self.popups: list[int] = []

    def add_gold_popup(self, _x, _y, reward):
        self.popups.append(reward)

    def update(self):
        self.combo_counter.update()


def _unit(team: str, reward: int):
    return SimpleNamespace(alive=False, team=team, gold_reward=reward, x=0, y=0)


def _reward_fixture():
    ComboCounter = _source_combo_counter()
    apply_rewards = _source_reward_method()
    game = SimpleNamespace(
        minions=[],
        towers=[],
        gold=0,
        score=0,
        total_kills=0,
        max_combo=0,
        red_towers_destroyed=0,
        ai=SimpleNamespace(gold=0),
        effects=EffectsProbe(ComboCounter()),
    )

    def frame(heroes=()):
        apply_rewards(game, list(heroes))
        combo = game.effects.combo_counter
        return {
            "gold": game.gold,
            "ai_gold": game.ai.gold,
            "score": game.score,
            "total_kills": game.total_kills,
            "max_combo": game.max_combo,
            "combo_count": combo.count,
            "combo_timer": combo.timer,
            "last_combo": combo.last_combo,
            "red_towers_destroyed": game.red_towers_destroyed,
        }

    trace = []
    for reward in (8, 8, 8):
        game.minions.append(_unit("red", reward))
        trace.append(frame())

    game.minions.append(_unit("blue", 8))
    game.towers.extend((_unit("red", 100), _unit("blue", 100)))
    trace.append(frame((_unit("red", 0), _unit("blue", 0))))

    for _ in range(118):
        frame()
    expired = frame()

    game.minions.append(_unit("red", 8))
    after_expiry = frame()
    return {"trace": trace, "expired": expired, "after_expiry": after_expiry}


def _json_value(value):
    return json.loads(json.dumps(value, sort_keys=True))


def source_fixture():
    SaveManager = _source_save_manager()
    data: dict[str, object] = {}
    empty = _json_value(SaveManager.get_level_stats(data, 1))

    scenarios = [
        {
            "name": "loss",
            "level": 1,
            "match": {
                "won": False,
                "score": 999,
                "time_seconds": 90,
                "kills": 4,
                "combo": 3,
                "playtime_seconds": 90,
            },
        },
        {
            "name": "first_win",
            "level": 1,
            "match": {
                "won": True,
                "score": 1000,
                "time_seconds": 120,
                "kills": 5,
                "combo": 4,
                "playtime_seconds": 120,
            },
        },
        {
            "name": "higher_slower",
            "level": 1,
            "match": {
                "won": True,
                "score": 1500,
                "time_seconds": 180,
                "kills": 2,
                "combo": 2,
                "playtime_seconds": 180,
            },
        },
        {
            "name": "lower_faster",
            "level": 1,
            "match": {
                "won": True,
                "score": 1200,
                "time_seconds": 90,
                "kills": 1,
                "combo": 1,
                "playtime_seconds": 90,
            },
        },
        {
            "name": "loss_cannot_replace_best",
            "level": 1,
            "match": {
                "won": False,
                "score": 9999,
                "time_seconds": 1,
                "kills": 3,
                "combo": 8,
                "playtime_seconds": 1,
            },
        },
        {
            "name": "independent_level",
            "level": 2,
            "match": {
                "won": True,
                "score": 77,
                "time_seconds": 65,
                "kills": 2,
                "combo": 1,
                "playtime_seconds": 65,
            },
        },
    ]
    results = []
    for scenario in scenarios:
        result = SaveManager.update_level_stats(data, scenario["level"], scenario["match"])
        results.append(
            {
                "name": scenario["name"],
                "level": scenario["level"],
                "match": scenario["match"],
                "is_new_best_score": result["is_new_best_score"],
                "is_new_best_time": result["is_new_best_time"],
                "new_stats": _json_value(result["new_stats"]),
            }
        )

    return {
        "empty": empty,
        "updates": results,
        "final_level_stats": _json_value(data["level_stats"]),
        "format": {
            "zero": SaveManager.format_time(0),
            "sixty_five": SaveManager.format_time(65),
            "hour": SaveManager.format_time(3605),
        },
        "rewards": _reward_fixture(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    fixture = source_fixture()
    if args.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if fixture != expected:
        raise SystemExit("FAIL: level-stat source fixture drift (run with --write only after source audit)")
    print("PASS: source level stats, score rewards and combo lifecycle")


if __name__ == "__main__":
    main()
