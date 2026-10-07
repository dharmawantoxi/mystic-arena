"""Read-only oracle for the player's in-match Hero Shop transaction.

Executes Game.try_buy_hero from _core.py through AST with tiny stand-ins for
render/audio/entity dependencies. The source method itself owns every gate,
debit and spawn-offset calculation exercised below.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_core.py"
FIXTURE = Path(__file__).parent / "fixtures/player_recruit_source.json"

CATALOG = {
    "kaizen": {"cost": 400},
    "thorne": {"cost": 500},
    "grimjaw": {"cost": 450},
    "sylara": {"cost": 380},
    "vex": {"cost": 420},
    "zephyr": {"cost": 420},
}


class Hero:
    def __init__(self, hero_type, team, x, y):
        self.hero_type = hero_type
        self.team = team
        self.x = x
        self.y = y
        self.alive = True


class _Sound:
    def play(self, *_args, **_kwargs):
        return None


class SoundManager:
    def __new__(cls):
        return _Sound()


def _source_game_type():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    game = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Game")
    method = next(
        node for node in game.body if isinstance(node, ast.FunctionDef) and node.name == "try_buy_hero"
    )
    stub = ast.ClassDef(
        name="SourceGame",
        bases=[],
        keywords=[],
        body=[method],
        decorator_list=[],
    )
    module = ast.fix_missing_locations(ast.Module(body=[stub], type_ignores=[]))
    env = {
        "MAX_HEROES_OWNED": 5,
        "SoundManager": SoundManager,
        "Hero": Hero,
        "get_all_hero_types": lambda: CATALOG,
    }
    exec(compile(module, "<Game.try_buy_hero>", "exec"), env)
    return env["SourceGame"]


def _hero(hero_type, alive=True):
    value = Hero(hero_type, "blue", 0, 0)
    value.alive = alive
    return value


def _run_case(case):
    game_type = _source_game_type()
    game = game_type()
    game.gold = case["gold"]
    game.purchased_heroes = list(case["unlocked"])
    game.heroes = [_hero(row["id"], row.get("alive", True)) for row in case.get("owned", [])]
    game.map_renderer = SimpleNamespace(radiant_shop_pos=(340, 540))
    before = len(game.heroes)
    error = ""
    try:
        game.try_buy_hero(case["buy"])
    except Exception as exc:  # Captured to lock source failure shape, not hidden.
        error = type(exc).__name__
    receipts = [
        {
            "id": hero.hero_type,
            "team": hero.team,
            "position": [hero.x, hero.y],
            "alive": hero.alive,
        }
        for hero in game.heroes[before:]
    ]
    return {
        "label": case["label"],
        "input": case,
        "gold": game.gold,
        "owned": [hero.hero_type for hero in game.heroes],
        "receipts": receipts,
        "error": error,
    }


def source_fixture():
    cases = [
        {"label": "locked", "gold": 1000, "unlocked": [], "owned": [], "buy": "kaizen"},
        {
            "label": "exact_first",
            "gold": 400,
            "unlocked": ["kaizen"],
            "owned": [],
            "buy": "kaizen",
        },
        {
            "label": "one_short",
            "gold": 399,
            "unlocked": ["kaizen"],
            "owned": [],
            "buy": "kaizen",
        },
        {
            "label": "duplicate_alive",
            "gold": 1000,
            "unlocked": ["kaizen"],
            "owned": [{"id": "kaizen"}],
            "buy": "kaizen",
        },
        {
            "label": "duplicate_dead",
            "gold": 1000,
            "unlocked": ["kaizen"],
            "owned": [{"id": "kaizen", "alive": False}],
            "buy": "kaizen",
        },
        {
            "label": "cap_five",
            "gold": 10000,
            "unlocked": list(CATALOG),
            "owned": [
                {"id": "kaizen"},
                {"id": "thorne"},
                {"id": "grimjaw"},
                {"id": "sylara"},
                {"id": "vex"},
            ],
            "buy": "zephyr",
        },
        {
            "label": "second_slot",
            "gold": 900,
            "unlocked": ["kaizen", "thorne"],
            "owned": [{"id": "kaizen"}],
            "buy": "thorne",
        },
        {
            "label": "fifth_slot",
            "gold": 2000,
            "unlocked": list(CATALOG),
            "owned": [
                {"id": "kaizen"},
                {"id": "thorne"},
                {"id": "grimjaw"},
                {"id": "sylara"},
            ],
            "buy": "vex",
        },
    ]
    return [_run_case(case) for case in cases]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    current = source_fixture()
    if args.write:
        FIXTURE.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE {FIXTURE}")
        return
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert current == expected, "Player Hero Shop source fixture drift"
    print(f"PASS: {len(current)} player recruit source cases")


if __name__ == "__main__":
    main()
