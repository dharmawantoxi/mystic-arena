"""AST oracle for Boss TowerDebuffMixin clocks and hp heal modifiers.

The fixture executes the real read-only `_core.py` methods. Only `take_damage`
is replaced by a recorder, so the oracle checks the exact burn tick payload and
status-clock mutation without importing Pygame or presentation/audio effects.
"""
import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
FIXTURE = Path(__file__).parent / "fixtures/boss_debuff_clock_source.json"
SOURCE = ROOT / "_core.py"

STATUS_FIELDS = (
    "hp",
    "slow_amount",
    "slow_timer",
    "atk_slow_amount",
    "atk_slow_timer",
    "skill_down_amount",
    "skill_down_timer",
    "anti_heal_amount",
    "anti_heal_timer",
    "stun_timer",
    "armor_shred_amount",
    "armor_shred_timer",
    "dmg_amp_amount",
    "dmg_amp_timer",
    "heal_amp_amount",
    "heal_amp_timer",
    "blind_amount",
    "blind_timer",
    "burn_dps",
    "burn_timer",
    "burn_accum",
    "burn_tick_cd",
    "burn_team",
)


def _top_level_constant(tree, name):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                return ast.literal_eval(node.value)
    raise AssertionError("Missing source constant %s" % name)


def source_class():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    mixin = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "TowerDebuffMixin"
    )
    wanted_methods = {"_init_tower_debuffs", "clear_tower_debuffs", "_tick_tower_debuffs"}
    methods = [
        node for node in mixin.body
        if isinstance(node, ast.FunctionDef)
        and (node.name in wanted_methods or node.name == "hp")
    ]
    names = [node.name for node in methods]
    assert wanted_methods <= set(names), "Re-audit TowerDebuffMixin clock methods"
    assert names.count("hp") == 2, "Re-audit TowerDebuffMixin.hp getter/setter"
    cls = ast.ClassDef(
        name="SourceBossDebuffClock",
        bases=[],
        keywords=[],
        body=methods,
        decorator_list=[],
    )
    env = {
        "TOWER_DEBUFF_BURN_TICK": _top_level_constant(tree, "TOWER_DEBUFF_BURN_TICK"),
        "TOWER_DEBUFF_FPS": _top_level_constant(tree, "TOWER_DEBUFF_FPS"),
    }
    exec(
        compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                "<source boss debuff clock>", "exec"),
        env,
    )
    result = env["SourceBossDebuffClock"]

    def take_damage(self, damage, from_team, damage_type="normal"):
        self.damage_calls.append(
            {"damage": int(damage), "from_team": from_team, "damage_type": damage_type}
        )

    result.take_damage = take_damage
    return result


def _boss(cls, state):
    boss = cls()
    boss._init_tower_debuffs()
    boss._hp_value = float(state.get("hp", 100000.0))
    boss.alive = bool(state.get("alive", True))
    boss.team = state.get("team", "red")
    boss.damage_calls = []
    for field, value in state.items():
        if field not in {"hp", "alive", "team"}:
            setattr(boss, field, value)
    return boss


def _state(boss):
    return {field: getattr(boss, field) for field in STATUS_FIELDS}


def run_tick_case(cls, label, state, ticks):
    boss = _boss(cls, state)
    for _ in range(ticks):
        boss._tick_tower_debuffs()
    return {
        "label": label,
        "input": state,
        "ticks": ticks,
        "result": {"state": _state(boss), "damage_calls": boss.damage_calls},
    }


def run_hp_write_case(cls, label, previous, requested, anti_heal, anti_heal_timer,
                      heal_amp, heal_amp_timer):
    boss = _boss(cls, {"hp": previous})
    boss.anti_heal_amount = anti_heal
    boss.anti_heal_timer = anti_heal_timer
    boss.heal_amp_amount = heal_amp
    boss.heal_amp_timer = heal_amp_timer
    boss.hp = requested
    return {
        "label": label,
        "previous": previous,
        "requested": requested,
        "anti_heal": anti_heal,
        "anti_heal_timer": anti_heal_timer,
        "heal_amp": heal_amp,
        "heal_amp_timer": heal_amp_timer,
        "result": boss.hp,
    }


def source_fixture():
    cls = source_class()
    cases = [
        run_tick_case(
            cls,
            "mixed_status_expiry",
            {
                "slow_amount": 0.3,
                "slow_timer": 1,
                "atk_slow_amount": 0.2,
                "atk_slow_timer": 2,
                "skill_down_amount": 0.4,
                "skill_down_timer": 1,
                "anti_heal_amount": 0.6,
                "anti_heal_timer": 2,
                "stun_timer": 1,
                "armor_shred_amount": 0.5,
                "armor_shred_timer": 1,
                "dmg_amp_amount": 0.25,
                "dmg_amp_timer": 2,
                "heal_amp_amount": 0.3,
                "heal_amp_timer": 1,
                "blind_amount": 0.2,
                "blind_timer": 3,
                "burn_dps": 30.0,
                "burn_timer": 2,
                "burn_accum": 0.25,
                "burn_tick_cd": 30,
                "burn_team": "blue",
            },
            1,
        ),
        run_tick_case(
            cls,
            "first_burn_tick",
            {
                "burn_dps": 120.0,
                "burn_timer": 35,
                "burn_accum": 0.0,
                "burn_tick_cd": 1,
                "burn_team": "blue",
            },
            1,
        ),
        run_tick_case(
            cls,
            "repeated_burn_ticks",
            {
                "burn_dps": 90.0,
                "burn_timer": 65,
                "burn_accum": 0.0,
                "burn_tick_cd": 2,
                "burn_team": None,
            },
            32,
        ),
        run_tick_case(
            cls,
            "burn_expiry_boundary",
            {
                "burn_dps": 120.0,
                "burn_timer": 1,
                "burn_accum": 29.5,
                "burn_tick_cd": 1,
                "burn_team": None,
            },
            1,
        ),
        run_tick_case(
            cls,
            "burn_accumulator_without_tick",
            {
                "burn_dps": 30.0,
                "burn_timer": 4,
                "burn_accum": 0.5,
                "burn_tick_cd": 7,
                "burn_team": "blue",
            },
            1,
        ),
    ]
    hp_writes = [
        run_hp_write_case(cls, "anti_heal_then_heal_amp", 400.0, 700.0, 0.4, 10, 0.25, 10),
        run_hp_write_case(cls, "anti_heal_only", 400.0, 800.0, 0.5, 10, 0.0, 0),
        run_hp_write_case(cls, "heal_amp_only", 400.0, 600.0, 0.0, 0, 0.5, 10),
        run_hp_write_case(cls, "downward_hp_write", 500.0, 300.0, 0.5, 10, 0.5, 10),
    ]
    return {"cases": cases, "hp_writes": hp_writes}


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %d Boss debuff clock cases and %d hp setter cases"
              % (len(actual["cases"]), len(actual["hp_writes"])))
    else:
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
        assert actual == expected, "Boss debuff clock source drift"
        print("PASS: Boss debuff clock — status expiry, burn ticks and anti-heal/heal-amp")


if __name__ == "__main__":
    main()
