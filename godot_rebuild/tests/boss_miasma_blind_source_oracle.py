"""9c: source oracle for the Miasma tick damage type against the boss blind gate.

Checkpoint `ce381b4`. Python `_tick_miasma` (`hero_items.py:209-233`) damages the
poisoned target with `tgt.take_damage(m["damage"], team, "magic")`, so the third
positional argument of `Boss.take_damage` (`bosses/base_boss.py:5978-5979`) is
`damage_type="magic"` and `source` stays `None`. The blind block at the top of
that method only fires for `damage_type == 'normal'` **and** a non-`None`
source, so a blinded Miasma owner still poisons the boss in the source.

The pre-9c native path lost both facts: `hero_item_inventory.gd:817` calls
`BattleItemEffects.deal_damage_from`, and `battle_item_effects.gd` forwarded the
hit with `world._deliver_hit(source_id, source_team, tgt, amount, school,
origin)`, leaving `prototype_battle.gd:1366` to apply its `damage_type="normal"`
default while passing the live attacker as `source`. `BossState.blind_live`
(`boss_state.gd:662,689`) then rolls the attacker's blind and can swallow the
whole poison tick.

Every case executes the read-only source AST: the real `_apply_miasma` /
`_tick_miasma` helpers plus the real blind block lifted out of
`Boss.take_damage`. `expected` runs that gate with the source arguments
(`"magic"`, no source); `native_old` runs the very same gate with the pre-9c
native arguments (`"normal"`, live owner) and one pinned blind roll. Four
schedules per boss type, 216 boss types, 864 cases.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from boss_ability_source_oracle import (  # noqa: E402
    SOURCE_STATS,
    make_boss,
    source_class as boss_ability_class,
)
from boss_item_cleave_chain_source_oracle import (  # noqa: E402
    BLUE,
    _build_runtime,
    _func_node,
    _method_node,
)
from boss_miasma_source_oracle import _DummyOwner  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures/boss_miasma_blind_source.json"
OWNER_ID = 7
RED = 1
BASIC_DAMAGE = 50
BLIND_TIMER = 90
BLIND_ROLL = 0.0
FIRST_TICK_FRAME = 30

# `blind_frame` = number of lead frames that run *without* the blind; frame 0
# blinds the owner before the first tick, frame 30 blinds it right after the
# first tick lands (frame 30) and before the second one (frame 60).
SCENARIOS = (
    {
        "name": "blind_owner_tick_blocked",
        "blind_frame": 0,
        "blind_amount": 1.0,
        "true_strike": False,
        "observe_frames": 30,
    },
    {
        "name": "blind_owner_second_tick",
        "blind_frame": 30,
        "blind_amount": 1.0,
        "true_strike": False,
        "observe_frames": 60,
    },
    {
        "name": "blind_owner_true_strike_pierces",
        "blind_frame": 0,
        "blind_amount": 1.0,
        "true_strike": True,
        "observe_frames": 30,
    },
    {
        "name": "blind_owner_zero_amount",
        "blind_frame": 0,
        "blind_amount": 0.0,
        "true_strike": False,
        "observe_frames": 30,
    },
)

GAP_SCENARIOS = ("blind_owner_tick_blocked", "blind_owner_second_tick")


class _PinnedRandom:
    """`random.random()` pinned to the roll the native replay pins as well."""

    def __init__(self, value):
        self.value = value

    def random(self):
        return self.value


def _shape_flags():
    tick_text = ast.unparse(_func_node("_tick_miasma", "hero_items.py"))
    gate_text = ast.unparse(_method_node("Boss", "take_damage", "bosses/base_boss.py").body[0])
    return {
        "tick_passes_magic": "tgt.take_damage(m['damage'], team, 'magic')" in tick_text,
        "tick_passes_no_source": "source=" not in tick_text,
        "gate_needs_normal": (
            "if damage_type == 'normal' and damage > 0 and (source is not None)" in gate_text
        ),
        "gate_reads_blind": "getattr(source, 'blind_timer', 0) > 0" in gate_text,
        "gate_reads_true_strike": "src_inv.has_true_strike()" in gate_text,
    }


def _blind_gate():
    """Compile the real blind block of `Boss.take_damage` as a predicate.

    The block ends in a bare `return`, so `None` means "source returned before
    touching hp" (blind miss) while `False` means the gate did not fire.
    """
    gate = _method_node("Boss", "take_damage", "bosses/base_boss.py").body[0]
    wrapper = ast.parse("def _boss_blind_gate(self, damage, damage_type, source):\n    return False\n").body[0]
    wrapper.body = [gate, wrapper.body[0]]
    module = ast.Module(body=[wrapper], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"random": _PinnedRandom(BLIND_ROLL), "getattr": getattr}
    exec(compile(module, "<source-boss-blind-gate>", "exec"), namespace)
    return namespace["_boss_blind_gate"]


def _prepare_case_boss(boss_cls, boss_type, owner, gate, native_old):
    boss = make_boss(boss_cls, boss_type)
    boss.id = 500
    boss.team = RED
    boss.alive = True
    boss.hits = []

    def _take_damage(damage, from_team=None, damage_type="normal", source=None, school=None):
        if not getattr(boss, "alive", False):
            return 0
        # Pre-9c native: `deal_damage_from` -> `_deliver_hit` never overrode the
        # `damage_type` default ("normal") and handed the live attacker over as
        # `source`, which is exactly what `BossState.take_damage` received.
        gate_damage_type = "normal" if native_old else damage_type
        gate_source = owner if native_old else source
        if gate(boss, damage, gate_damage_type, gate_source) is None:
            return 0
        boss.hits.append(int(damage))
        return int(damage)

    boss.take_damage = _take_damage
    return boss


def _run_case(catalog, inv_cls, boss_cls, boss_type, scenario, gate, native_old):
    env = inv_cls._on_hit_common.__globals__
    env["_MIASMA"] = {}
    owner = _DummyOwner(None)
    owner.id = OWNER_ID
    owner.team = BLUE
    owner.blind_timer = 0
    owner.blind_amount = 0.0
    inv = inv_cls(owner)
    owner.items = inv
    assert inv.add("basilisk_breath"), "cannot equip basilisk_breath"
    boss = _prepare_case_boss(boss_cls, boss_type, owner, gate, native_old)
    owner.target = boss
    # The source's real on-hit hook: `_on_hit_common` -> `_apply_miasma`.
    inv.on_basic_attack_hit(boss, BASIC_DAMAGE, [boss])
    if bool(scenario["true_strike"]):
        # Equipped after the hit so the Cudgel bash arm cannot pollute the tick.
        assert inv.add("sundering_cudgel"), "cannot equip sundering_cudgel"
    tracker = env["_MIASMA"].get(id(boss))
    assert tracker is not None, "Miasma tracker missing"
    events = []
    blind_frame = int(scenario["blind_frame"])
    for frame in range(1, int(scenario["observe_frames"]) + 1):
        if frame > blind_frame:
            owner.blind_timer = BLIND_TIMER
            owner.blind_amount = float(scenario["blind_amount"])
        before = len(boss.hits)
        env["_tick_miasma"](1)
        if len(boss.hits) > before:
            events.append([frame, int(boss.hits[-1])])
    return {
        "miasma_damage": int(tracker["damage"]),
        "events": events,
    }


def source_fixture():
    catalog, inv_cls, boss_cls = _build_runtime()
    env = inv_cls._on_hit_common.__globals__
    env["_MIASMA"] = {}
    source_module = ast.Module(
        body=[
            _func_node("_apply_miasma", "hero_items.py"),
            _func_node("_tick_miasma", "hero_items.py"),
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(source_module)
    exec(compile(source_module, "<source-miasma-blind>", "exec"), env)
    gate = _blind_gate()
    item_data = catalog["basilisk_breath"]["on_attack"]
    cases = []
    for boss_type in sorted(SOURCE_STATS):
        for scenario in SCENARIOS:
            expected = _run_case(
                catalog, inv_cls, boss_cls, boss_type, scenario, gate, False
            )
            native_old = _run_case(
                catalog, inv_cls, boss_cls, boss_type, scenario, gate, True
            )
            cases.append(
                {
                    "boss_type": boss_type,
                    "scenario": scenario["name"],
                    "boss_max_hp": int(SOURCE_STATS[boss_type]["hp"]),
                    "blind_frame": int(scenario["blind_frame"]),
                    "blind_amount": float(scenario["blind_amount"]),
                    "true_strike": bool(scenario["true_strike"]),
                    "observe_frames": int(scenario["observe_frames"]),
                    "miasma_damage": int(expected["miasma_damage"]),
                    "expected": {
                        "events": expected["events"],
                        "damage_total": sum(int(row[1]) for row in expected["events"]),
                    },
                    "native_old": {
                        "events": native_old["events"],
                        "damage_total": sum(int(row[1]) for row in native_old["events"]),
                    },
                }
            )
    return {
        "source": {
            "ast_shape": _shape_flags(),
            "on_attack": {
                "max_hp_pct_per_tick": float(item_data["max_hp_pct_per_tick"]),
                "cap_damage": int(item_data["cap_damage"]),
                "duration": int(item_data["duration"]),
                "tick": int(item_data["tick"]),
            },
            "blind": {
                "timer": BLIND_TIMER,
                "roll": BLIND_ROLL,
                "first_tick_frame": FIRST_TICK_FRAME,
            },
            "python_source": "hero_items.py:209-233; bosses/base_boss.py:5978-5993",
            "native_old_source": (
                "hero_item_inventory.gd:817; battle_item_effects.gd:20-37; "
                "prototype_battle.gd:1366,1388; boss_state.gd:662,689"
            ),
            "boss_types": len(SOURCE_STATS),
            "gap_scenarios": list(GAP_SCENARIOS),
        },
        "cases": cases,
    }


if __name__ == "__main__":
    fixture = source_fixture()
    assert len(fixture["cases"]) == 864
    assert fixture["source"]["boss_types"] == 216
    assert all(fixture["source"]["ast_shape"].values())
    for row in fixture["cases"]:
        expected_events = row["expected"]["events"]
        native_old_events = row["native_old"]["events"]
        assert expected_events, "source always poisons: blind never gates 'magic'"
        if row["scenario"] in GAP_SCENARIOS:
            assert expected_events != native_old_events
            assert row["native_old"]["damage_total"] < row["expected"]["damage_total"]
        else:
            assert expected_events == native_old_events
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n")
    print(
        "PASS: 864 Miasma blind-gate cases; source 'magic' tick vs pre-9c "
        "'normal' damage_type counterfactual"
    )
