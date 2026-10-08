"""Read-only oracle for the main-menu Hero Shop unlock transaction.

Executes Menu._unlock_hero_in_meta_shop from _core.py through AST with small
save/audio stand-ins. Python/Pygame remains the source of truth and is never
modified by this oracle.
"""
from __future__ import annotations

import argparse
import ast
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_core.py"
FIXTURE = Path(__file__).parent / "fixtures/meta_hero_unlock_source.json"

CATALOG = {
    "kaizen": {
        "unlock_cost": 0,
        "unlock_require_boss": None,
        "is_boss_hero": False,
        "boss_class": "",
    },
    "thorne": {
        "unlock_cost": 0,
        "unlock_require_boss": None,
        "is_boss_hero": False,
        "boss_class": "",
    },
    "gornak": {
        "unlock_cost": 4500,
        "unlock_require_boss": "gornak",
        "is_boss_hero": True,
        "boss_class": "mini",
    },
    "abaddon": {
        "unlock_cost": 4500,
        "unlock_require_boss": "abaddon",
        "is_boss_hero": True,
        "boss_class": "true",
    },
}


class _Sound:
    events: list[str] = []

    def play(self, key, **_kwargs):
        self.events.append(str(key))


class SoundManager:
    def __new__(cls):
        return _Sound()


class SaveManager:
    writes: list[dict] = []

    @classmethod
    def save(cls, state):
        cls.writes.append(copy.deepcopy(state))
        return True


def _last_int_constant(tree: ast.Module, name: str) -> int:
    values = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            values.append(ast.literal_eval(node.value))
    assert values and isinstance(values[-1], int), name
    return values[-1]


def _starter_auto_grant(tree: ast.Module) -> str:
    game = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Game")
    reset = next(node for node in game.body if isinstance(node, ast.FunctionDef) and node.name == "reset")
    for node in ast.walk(reset):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        owner = node.func.value
        if (
            node.func.attr == "append"
            and isinstance(owner, ast.Attribute)
            and owner.attr == "purchased_heroes"
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            return node.args[0].value
    raise AssertionError("Game starter auto-grant not found")


def _source_menu_type(tree: ast.Module):
    menu = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Menu")
    method = next(
        node
        for node in menu.body
        if isinstance(node, ast.FunctionDef) and node.name == "_unlock_hero_in_meta_shop"
    )
    stub = ast.ClassDef(
        name="SourceMenu",
        bases=[],
        keywords=[],
        body=[method],
        decorator_list=[],
    )
    module = ast.fix_missing_locations(ast.Module(body=[stub], type_ignores=[]))
    env = {
        "DEV_UNLIMITED_HERO_GOLD": False,
        "SaveManager": SaveManager,
        "SoundManager": SoundManager,
        "get_all_hero_types": lambda: copy.deepcopy(CATALOG),
    }
    exec(compile(module, "<Menu._unlock_hero_in_meta_shop>", "exec"), env)
    return env["SourceMenu"]


def _run_case(menu_type, case):
    SaveManager.writes = []
    _Sound.events = []
    menu = menu_type()
    menu.meta_gold = case["gold"]
    menu.save_data = {
        "meta_gold": case["gold"],
        "purchased_heroes": list(case["purchased"]),
        "unlocked_bosses": list(case["defeated"]),
    }
    menu._unlock_hero_in_meta_shop(case["hero"])
    return {
        "label": case["label"],
        "input": case,
        "gold": menu.meta_gold,
        "purchased": menu.save_data["purchased_heroes"],
        "defeated": menu.save_data["unlocked_bosses"],
        "save_count": len(SaveManager.writes),
        "sounds": list(_Sound.events),
    }


def source_fixture():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    policy = {
        "starter_cost": _last_int_constant(tree, "STARTER_HERO_UNLOCK_COST"),
        "mini_boss_cost": _last_int_constant(tree, "MINI_BOSS_HERO_UNLOCK_COST"),
        "true_boss_cost": _last_int_constant(tree, "TRUE_BOSS_HERO_UNLOCK_COST"),
        "starter_auto_grant": _starter_auto_grant(tree),
    }
    assert policy == {
        "starter_cost": 0,
        "mini_boss_cost": 4500,
        "true_boss_cost": 4500,
        "starter_auto_grant": "kaizen",
    }
    menu_type = _source_menu_type(tree)
    cases = [
        {
            "label": "unknown",
            "gold": 9000,
            "purchased": ["kaizen"],
            "defeated": [],
            "hero": "missing",
        },
        {
            "label": "duplicate_starter",
            "gold": 0,
            "purchased": ["kaizen"],
            "defeated": [],
            "hero": "kaizen",
        },
        {
            "label": "free_starter",
            "gold": 0,
            "purchased": ["kaizen"],
            "defeated": [],
            "hero": "thorne",
        },
        {
            "label": "locked_mini_boss",
            "gold": 4500,
            "purchased": ["kaizen"],
            "defeated": [],
            "hero": "gornak",
        },
        {
            "label": "mini_boss_one_short",
            "gold": 4499,
            "purchased": ["kaizen"],
            "defeated": ["gornak"],
            "hero": "gornak",
        },
        {
            "label": "mini_boss_exact",
            "gold": 4500,
            "purchased": ["kaizen"],
            "defeated": ["gornak"],
            "hero": "gornak",
        },
        {
            "label": "true_boss_exact",
            "gold": 4500,
            "purchased": ["kaizen", "thorne"],
            "defeated": ["abaddon"],
            "hero": "abaddon",
        },
    ]
    return {"policy": policy, "cases": [_run_case(menu_type, case) for case in cases]}


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
    assert current == expected, "Main-menu Hero Shop source fixture drift"
    print(f"PASS: {len(current['cases'])} meta Hero Shop source cases")


if __name__ == "__main__":
    main()
