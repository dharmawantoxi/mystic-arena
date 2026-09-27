"""Execute the real AIPlayer candidate ordering: kills descending, stable.

Covers `_try_upgrade_tower_new`, `_try_activate_regen_shield` and
`_try_upgrade_hero` with several candidates instead of one. Real Tower/Hero
methods run through AST, no game/pygame import; Python stays read-only.

Ordering evidence:
- tower: the source sorts `my_towers` in place, so the mutated list order is
  read back directly, together with which candidate actually paid.
- regen shield / hero upgrade: the sorted list is local to the source method,
  so the order is recovered by repeated calls where each success removes the
  winner from the candidate pool (shield flag set, hero reaching max level).

Note on attribution: `Tower.kills` is initialised in the source and never
incremented anywhere in the Python game, so real tower priority degenerates to
the original order. Kills are set explicitly here only to lock the rule.
"""
import ast
import json
import sys
from pathlib import Path

from ai_upgrade_source_oracle import compile_subset
from kaizen_source_oracle import build_hero_env, fresh_hero
from structure_source_oracle import ROOT, namespace

FIXTURE = Path(__file__).parent / "fixtures/ai_priority_source.json"

TOWER_CASES = [
    {"kills": [0, 0, 0], "levels": [2, 2, 2], "gold": 100000},
    {"kills": [1, 5, 3], "levels": [2, 2, 2], "gold": 100000},
    {"kills": [4, 4, 4, 4], "levels": [2, 3, 2, 4], "gold": 100000},
    {"kills": [2, 9, 9, 1], "levels": [3, 2, 2, 5], "gold": 100000},
    {"kills": [7, 7, 0], "levels": [1, 2, 2], "gold": 100000},
    # Not enough for the richest candidate: the source keeps scanning.
    {"kills": [9, 1], "levels": [5, 2], "gold": 200},
    {"kills": [9, 1], "levels": [5, 2], "gold": 400},
    {"kills": [3, 2, 1], "levels": [2, 2, 2], "gold": 0},
]

SHIELD_CASES = [
    {"kills": [0, 0, 0], "levels": [4, 5, 6]},
    {"kills": [1, 6, 6, 2], "levels": [4, 4, 5, 6]},
    {"kills": [5, 5, 5], "levels": [6, 4, 5]},
]

HERO_CASES = [
    {"kills": [0, 0, 0]},
    {"kills": [2, 8, 5]},
    {"kills": [4, 4, 9, 4]},
]


def source_fixture():
    env = build_hero_env()
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    ai_type = compile_subset(tree, "AIPlayer", (
        "__init__", "_ai_reserve", "_try_upgrade_tower_new",
        "_try_activate_regen_shield", "_try_upgrade_hero"), env)
    tower_env = namespace()
    tower_env["TOWER_UPGRADE_PATHS"] = {
        path: tower_env[path.upper() + "_LEVELS"]
        for path in ("archer", "cannon", "ice", "mage")}
    tower_type = compile_subset(tree, "Tower", (
        "__init__", "_apply_level_stats", "can_upgrade", "upgrade_cost", "upgrade",
        "can_activate_regen_shield", "regen_shield_cost", "activate_regen_shield"), tower_env)
    result = {"towers": [], "shields": [], "heroes": []}

    def ai(gold, reserve=0):
        player = ai_type()
        player.gold = gold
        player._hero_purchase_target = "kaizen" if reserve else None
        player._hero_purchase_target_cost = reserve
        return player

    def tower(level, kills, tag):
        obj = tower_type(500, 340, "red")
        for _ in range(1, level):
            assert obj.upgrade("archer")
        obj.kills = kills
        obj._tag = tag
        return obj

    for case in TOWER_CASES:
        for reserve in (0, 400):
            towers = [tower(level, kills, index) for index, (level, kills)
                      in enumerate(zip(case["levels"], case["kills"]))]
            player = ai(case["gold"], reserve)
            before = {t._tag: t.level for t in towers}
            success = player._try_upgrade_tower_new(towers)
            upgraded = [t._tag for t in towers if t.level != before[t._tag]]
            result["towers"].append({
                "kills": case["kills"], "levels": case["levels"],
                "gold": case["gold"], "reserved": reserve,
                "order": [t._tag for t in towers],
                "success": success, "upgraded": upgraded,
                "balance": player.gold, "count": player.total_upgraded,
                "paths": [t.tower_type for t in towers],
                "end_levels": [before[index] if index not in upgraded
                               else before[index] + 1 for index in range(len(towers))],
            })

    for case in SHIELD_CASES:
        towers = [tower(level, kills, index) for index, (level, kills)
                  in enumerate(zip(case["levels"], case["kills"]))]
        player = ai(100000)
        order = []
        while player._try_activate_regen_shield(towers):
            order.extend(t._tag for t in towers
                         if t.regen_shield_active and t._tag not in order)
        result["shields"].append({
            "kills": case["kills"], "levels": case["levels"],
            "order": order, "balance": player.gold,
            "spent": 100000 - player.gold,
        })

    max_level = env["MAX_HERO_LEVEL"]
    for case in HERO_CASES:
        heroes = []
        for index, kills in enumerate(case["kills"]):
            hero = fresh_hero(env)
            hero.team = "red"
            while hero.level < max_level - 1:
                assert hero.upgrade()
            hero.kills = kills
            hero._tag = index
            heroes.append(hero)
        player = ai(100000)
        player.heroes = heroes
        order = []
        while player._try_upgrade_hero():
            order.extend(h._tag for h in heroes
                         if h.level >= max_level and h._tag not in order)
        result["heroes"].append({
            "kills": case["kills"], "order": order,
            "count": player.total_hero_upgrades,
            "spent": 100000 - player.gold,
        })
    return result


if __name__ == "__main__":
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), "AI priority source drift"
    print("PASS: AI kills-descending stable candidate order — "
          + ", ".join(f"{len(rows)} {key}" for key, rows in actual.items()))
