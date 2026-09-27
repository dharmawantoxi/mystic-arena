"""Execute AIPlayer upgrade attempts plus real Tower/Castle/Hero methods.

Single-candidate parity only: kill-priority selection is not implemented yet.
Hero uses the existing Kaizen oracle's empty-inventory/audio stubs; no kit claims
beyond Kaizen. Python files remain read-only. No scene/game/pygame is imported.
"""
import ast
import json
import sys
from pathlib import Path

from kaizen_source_oracle import build_hero_env, fresh_hero
from structure_source_oracle import ROOT

FIXTURE = Path(__file__).parent / "fixtures/ai_upgrade_source.json"


def compile_subset(tree, name, methods, env):
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
    selected = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in methods]
    assert {n.name for n in selected} == set(methods)
    node = ast.ClassDef(name=name, bases=[], keywords=[], decorator_list=[], body=selected)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 f"<source {name} upgrade>", "exec"), env)
    return env[name]


def source_fixture():
    env = build_hero_env()
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    ai_type = compile_subset(tree, "AIPlayer", (
        "__init__", "_ai_reserve", "_try_upgrade_tower_new", "_try_upgrade_nexus", "_try_upgrade_hero"), env)
    castle_type = compile_subset(tree, "Castle", (
        "__init__", "_apply_level_stats", "upgrade", "upgrade_cost"), env)
    tower_type = env["SourceTower"]
    result = {"towers": [], "nexuses": [], "heroes": []}

    def ai(gold, reserve):
        player = ai_type()
        player.gold = gold
        player._hero_purchase_target = "kaizen" if reserve else None
        player._hero_purchase_target_cost = reserve
        return player

    def snapshot(obj, player, success, counter, fields):
        return {"success": success, "gold": player.gold, "count": getattr(player, counter),
                "reserve": player._ai_reserve(), "state": {key: getattr(obj, key) for key in fields}}

    for path in ("archer", "cannon", "ice", "mage"):
        for level in range(1 if path == "archer" else 2, 7):
            if level == 1:
                costs = sorted({env["TOWER_UPGRADE_PATHS"][p][2]["cost"]
                                for p in ("cannon", "ice", "archer", "mage")})
            else:
                costs = [env["TOWER_UPGRADE_PATHS"][path].get(level + 1, {}).get("cost", 0)]
            for reserve in (0, 400):
                for gold in sorted({max(0, cost + reserve + delta) for cost in costs for delta in (-1, 0, 1)}):
                    obj = tower_type(500, 340, "red")
                    for _ in range(1, level):
                        assert obj.upgrade(path)
                    obj.hp, obj.shield, obj.timer, obj.no_damage_timer = 1, 0, 17, 9
                    player = ai(gold, reserve)
                    success = player._try_upgrade_tower_new([obj])
                    result["towers"].append(dict(path=path, level=level, gold=gold, reserved=reserve,
                        expected=snapshot(obj, player, success, "total_upgraded",
                            ("level", "tower_type", "hp", "max_hp", "shield", "shield_max", "damage", "timer", "no_damage_timer"))))
    for level in range(1, 6):
        cost = env["NEXUS_LEVELS"][level]["upgrade_cost"]
        for reserve in (0, 400):
            for gold in sorted({max(0, cost + reserve + delta) for delta in (-1, 0, 1)}):
                for paid in (False, True):
                    obj = castle_type(1180, 100, "red")
                    for _ in range(1, level):
                        assert obj.upgrade()
                    obj.hp, obj.timer, obj.shield_no_damage_timer = 1, 17, 9
                    obj.castle_shield_purchased = paid
                    if paid:
                        obj.shield_max = int(obj.max_hp * env["CASTLE_SHIELD_HP_RATIO"])
                    obj.shield = int(obj.shield_max * 0.3)
                    player = ai(gold, reserve)
                    success = player._try_upgrade_nexus(obj)
                    result["nexuses"].append(dict(level=level, gold=gold, reserved=reserve, paid=paid,
                        expected=snapshot(obj, player, success, "total_nexus_upgrades",
                            ("level", "hp", "max_hp", "shield", "shield_max", "damage", "timer", "shield_no_damage_timer"))))
    for level in (1, 2, 7, 14, 15):
        cost = env["HERO_LEVELS"][level]["upgrade_cost"]
        for reserve in (0, 400):
            for gold in sorted({max(0, cost + reserve + delta) for delta in (-1, 0, 1)}):
                for alive in (False, True):
                    obj = fresh_hero(env)
                    obj.team = "red"
                    for _ in range(1, level):
                        assert obj.upgrade()
                    obj.hp, obj.alive, obj.skill_timer = int(alive), alive, 29
                    player = ai(gold, reserve)
                    player.heroes = [obj]
                    success = player._try_upgrade_hero()
                    result["heroes"].append(dict(level=level, gold=gold, reserved=reserve, alive=alive,
                        expected=snapshot(obj, player, success, "total_hero_upgrades",
                            ("level", "hp", "max_hp", "damage", "alive", "skill_timer"))))
    return result


if __name__ == "__main__":
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), "AI upgrade source drift"
    print("PASS: AI single-candidate upgrades with real Tower/Castle/Kaizen methods — "
          + ", ".join(f"{len(rows)} {key}" for key, rows in actual.items()))
