"""Execute original AIPlayer paid-shield methods + Tower/Castle state machines.

Real numeric methods via AST, no game/pygame imports. Presentation flashes are
out of scope. Cases use one tower candidate (kill-priority ordering is pending).
The dead-castle guard added by the native domain is tested separately, not claimed
as source behavior: Python's castle eligibility itself has no alive predicate.
"""
import ast
import json
import sys
from pathlib import Path

from ai_upgrade_source_oracle import compile_subset
from structure_source_oracle import ROOT, namespace

FIXTURE = Path(__file__).parent / "fixtures/ai_shield_source.json"


def source_fixture():
    env = namespace()
    env["TOWER_UPGRADE_PATHS"] = {p: env[p.upper() + "_LEVELS"] for p in ("archer", "cannon", "ice", "mage")}
    core = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    # This is a source alias, not a literal; execute it rather than guessing 850.
    alias = next(n for n in core.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "CASTLE_SHIELD_COST" for t in n.targets))
    exec(compile(ast.Module(body=[alias], type_ignores=[]), "<source castle shield price>", "exec"), env)
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    tower_type = compile_subset(tree, "Tower", (
        "__init__", "_apply_level_stats", "can_upgrade", "upgrade_cost", "upgrade", "sell_value",
        "can_activate_regen_shield", "regen_shield_cost", "activate_regen_shield", "_update_regen", "take_damage"), env)
    castle_type = compile_subset(tree, "Castle", (
        "__init__", "_apply_level_stats", "upgrade", "upgrade_cost", "set_wave", "take_damage",
        "can_activate_castle_shield", "castle_shield_cost", "activate_castle_shield", "_update_castle_shield"), env)
    ai_type = compile_subset(tree, "AIPlayer", (
        "__init__", "_ai_reserve", "_try_activate_regen_shield", "_try_activate_castle_shield"), env)
    result = {"constants": {key: env[key] for key in (
        "TOWER_REGEN_SHIELD_COST", "TOWER_REGEN_SHIELD_MIN_LEVEL", "CASTLE_SHIELD_COST")},
        "towers": [], "castles": [], "traces": [], "refunds": [], "castle_upgrades": []}

    def tower(path, level, team="red"):
        obj = tower_type(500, 340, team)
        for _ in range(1, level):
            assert obj.upgrade(path)
        return obj

    def castle(level):
        obj = castle_type(1180, 100, "red")
        for _ in range(1, level):
            assert obj.upgrade()
        return obj

    def ai(gold, reserve):
        player = ai_type()
        player.gold = gold
        player._hero_purchase_target = "kaizen" if reserve else None
        player._hero_purchase_target_cost = reserve
        return player

    def state(obj, kind):
        fields = {key: getattr(obj, key) for key in ("hp", "shield", "shield_max")}
        fields["no_damage_ticks"] = obj.no_damage_timer if kind == "tower" else obj.shield_no_damage_timer
        fields["level"] = obj.level
        if kind == "tower":
            fields["regen_shield_active"] = obj.regen_shield_active
        else:
            fields.update({key: getattr(obj, key) for key in
                           ("shield_active", "free_shield_active", "castle_shield_purchased")})
        return fields

    for path in ("archer", "cannon", "ice", "mage"):
        for level in range(1 if path == "archer" else 2, 7):
            for reserve in (0, 400):
                for delta in (-1, 0, 1):
                    gold = env["TOWER_REGEN_SHIELD_COST"] + reserve + delta
                    obj = tower(path, level)
                    obj.hp, obj.shield, obj.no_damage_timer = 1, 13, 27
                    player = ai(gold, reserve)
                    success = player._try_activate_regen_shield([obj])
                    repeat = player._try_activate_regen_shield([obj])
                    result["towers"].append(dict(path=path, level=level, gold=gold, reserve=reserve,
                        success=success, repeat=repeat, balance=player.gold, state=state(obj, "tower")))
    for level in range(1, 6):
        for wave in (10, 11, 20):
            for reserve in (0, 400):
                for delta in (-1, 0, 1):
                    gold = env["CASTLE_SHIELD_COST"] + reserve + delta
                    obj = castle(level)
                    obj.set_wave(wave)
                    obj.hp, obj.shield_no_damage_timer = 1, 27
                    player = ai(gold, reserve)
                    success = player._try_activate_castle_shield(obj)
                    repeat = player._try_activate_castle_shield(obj)
                    result["castles"].append(dict(level=level, wave=wave, gold=gold, reserve=reserve,
                        success=success, repeat=repeat, balance=player.gold, state=state(obj, "castle")))

    def trace(obj, kind, setup, delay):
        obj.hp = obj.max_hp - 2
        if kind == "tower" or obj.shield_active:
            obj.shield = obj.shield_max - 5
        clock = "no_damage_timer" if kind == "tower" else "shield_no_damage_timer"
        setattr(obj, clock, delay - 2)
        update = obj._update_regen if kind == "tower" else obj._update_castle_shield
        rows = []
        for tick in range(1, 5):
            update()
            rows.append(dict(operation="tick", ticks=1, state=state(obj, kind)))
        obj.take_damage(20, "blue", school="magic")
        rows.append(dict(operation="hit", damage=20, state=state(obj, kind)))
        # Record both sides of the delay boundary, then HP regen boundary/full cap.
        for ticks in (delay - 1, 1, 1, 300):
            for _ in range(ticks):
                update()
            rows.append(dict(operation="tick", ticks=ticks, state=state(obj, kind)))
        result["traces"].append(dict(kind=kind, setup=setup, delay=delay, rows=rows))

    for path in ("archer", "cannon", "ice", "mage"):
        for level in (4, 6):
            for paid in (False, True):
                obj = tower(path, level)
                if paid:
                    assert obj.activate_regen_shield()
                trace(obj, "tower", dict(path=path, level=level, paid=paid), env["TOWER_REGEN_SHIELD_DELAY"])
    for level in (1, 5):
        for mode in ("free", "off", "paid"):
            obj = castle(level)
            obj.set_wave(10 if mode == "free" else 11)
            if mode == "paid":
                assert obj.activate_castle_shield()
            trace(obj, "castle", dict(level=level, mode=mode), env["CASTLE_SHIELD_REGEN_DELAY"])
    for path in ("archer", "cannon", "ice", "mage"):
        obj = tower(path, 4, "blue")
        assert obj.activate_regen_shield()
        for level in range(4, 7):
            if level > 4:
                obj.hp, obj.shield, obj.no_damage_timer = 1, 0, 17
                assert obj.upgrade()
            result["refunds"].append(dict(path=path, level=level, refund=obj.sell_value(), state=state(obj, "tower")))
    for level in range(1, 5):
        obj = castle(level)
        obj.set_wave(11)
        assert obj.activate_castle_shield()
        obj.shield = int(obj.shield_max * 0.3)
        obj.hp, obj.shield_no_damage_timer = 1, 17
        assert obj.upgrade()
        obj.set_wave(20)
        result["castle_upgrades"].append(dict(level=level, state=state(obj, "castle")))
    return result


if __name__ == "__main__":
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), "AI shield source drift"
    print(f"PASS: paid shields — {len(actual['towers'])} tower, {len(actual['castles'])} castle transactions, "
          f"{len(actual['traces'])} regen/damage traces, refunds and paid upgrades")
