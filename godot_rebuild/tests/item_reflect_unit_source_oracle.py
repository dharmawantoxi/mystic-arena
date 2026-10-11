"""Layer 9s oracle: the unconverted Razor Carapace reflect on MINION/HERO attackers.

The source reflect is `source.take_damage(dmg, self.hero.team, "magic")`
(`hero_items.py:2468`): three positional arguments, so the attacker runs with
`damage_type="magic"`, `source=None` and `school=None`. Layer 9i routed the BOSS
attacker that way; a minion/hero attacker still received the bus delivery
`_deliver_hit(-1, src_team, attacker, amount, "magic", position)` with the
`"normal"` type default, so an attacker with magic resist (undead 15%) ate a cut
the source never applies.

`--self-test` verifies the executed ladder against the committed fixture;
`--write` is the only fixture writer.
"""

import argparse
import json
import types
from pathlib import Path

from hero_veil_immunity_source_oracle import (  # noqa: E402
    _FakeHero,
    _case,
    _take_damage_callable,
)
from minion_damage_ladder_source_oracle import (  # noqa: E402
    _FakeMinion,
    _minion_take_damage_callable,
)
from boss_item_reflect_carapace_source_oracle import (  # noqa: E402
    INCOMING_DAMAGE,
    REFLECT_SENT,
    _build_source_runtime,
    _prepare_victim,
)

FIXTURE = Path(__file__).parent / "fixtures/item_reflect_unit_source.json"
RED = "red"
BLUE = "blue"
ATTACKER_ID = 11
UNDEAD_MAGIC_RESIST = 0.15
TROLL_ARMOR = 2
HERO_ARMOR = 6
ARMOR_ITEM = "steel_aegis"


def _minion_case(kind):
    return {
        "name": "reflect_unit",
        "damage": 0,
        "damage_type": "normal",
        "school": None,
        "source_school": None,
        "armor": TROLL_ARMOR if kind == "troll" else 0,
        "magic_resist": UNDEAD_MAGIC_RESIST if kind == "undead" else 0.0,
        "armor_shred": 0.0,
        "dmg_amp_timer": 0,
        "dmg_amp_amount": 0.0,
    }


def _minion_attacker(kind):
    take_damage, _resolve, credits = _minion_take_damage_callable()
    attacker = _FakeMinion(_minion_case(kind))
    attacker.id = ATTACKER_ID
    attacker.team = RED
    attacker.alive = True
    attacker.x = 20.0
    attacker.y = 0.0
    frame = take_damage.__globals__
    attacker.frame = frame
    attacker.real_take_damage = types.MethodType(take_damage, attacker)
    return attacker


def _hero_attacker(armor):
    take_damage, _credits = _take_damage_callable()
    attacker = _FakeHero(_case("reflect_unit", armor=armor, draws=[0.9]))
    attacker.id = ATTACKER_ID
    attacker.team = RED
    attacker.alive = True
    attacker.x = 20.0
    attacker.y = 0.0
    attacker.frame = take_damage.__globals__
    attacker.real_take_damage = types.MethodType(take_damage, attacker)
    return attacker


def _credited_total(rows):
    """`credit_hero_damage` skips the credit when `source is None`."""
    return sum(row[1] for row in rows if row[0])


def _run_case(inventory_class, scenario, native_old):
    kind = str(scenario["attacker_kind"])
    if kind == "hero":
        attacker = _hero_attacker(int(scenario.get("hero_armor", 0)))
    else:
        attacker = _minion_attacker(kind)
    victim, inventory = _prepare_victim(inventory_class, attacker, "reflect_unit")
    real_take_damage = attacker.real_take_damage
    observed = []

    def arm_take_damage(damage, from_team=None, damage_type="normal", source=None, school=None):
        # Observe the arguments the reflect arm actually sent. The native_old
        # column substitutes the pre-9s native delivery: `_deliver_hit` default
        # `"normal"` damage type with the declared magic school and no source.
        if native_old:
            observed.append([int(damage), "normal", "magic"])
            return real_take_damage(
                damage, from_team, "normal", source=None, school="magic"
            )
        observed.append([int(damage), str(damage_type), school if school else "neutral"])
        return real_take_damage(damage, from_team, damage_type, source=source, school=school)

    attacker.take_damage = arm_take_damage
    frame = attacker.frame
    credits_before = len(frame["_recorder"].rolls)
    hp_before = float(attacker.hp)
    inventory.notify_damage_taken(damage=INCOMING_DAMAGE, source=attacker)
    rows = [[row[0], row[1]] for row in frame["_recorder"].rolls[credits_before:]]
    return {
        "hp_loss": int(round(hp_before - float(attacker.hp))),
        "credited_total": _credited_total(rows),
        "reflect_args": observed,
    }


SCENARIOS = (
    {
        "name": "reflect_on_undead_attacker",
        "attacker_kind": "undead",
        "expect_divergence": True,
    },
    {
        "name": "reflect_on_troll_attacker",
        "attacker_kind": "troll",
        "expect_divergence": False,
    },
    {
        "name": "reflect_on_armoured_hero_attacker",
        "attacker_kind": "hero",
        "hero_armor": HERO_ARMOR,
        "expect_divergence": False,
    },
    {
        "name": "reflect_on_unarmoured_hero_attacker",
        "attacker_kind": "hero",
        "hero_armor": 0,
        "expect_divergence": False,
    },
)


def _shape(inventory_class) -> dict:
    """The source reflect passes the damage type as the third positional arg."""
    import ast

    root = Path(__file__).resolve().parents[2]
    text = (root / "hero_items.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "take_damage"
        and len(node.args) == 3
        and isinstance(node.args[2], ast.Constant)
        and node.args[2].value == "magic"
        and node.lineno < 2500
    ]
    return {
        "reflect_calls_with_magic_type": len(calls),
        "reflect_calls_with_source_kwarg": sum(
            1 for node in calls if any(keyword.arg == "source" for keyword in node.keywords)
        ),
        "reflect_call": "hero_items.py:2468 source.take_damage(dmg, self.hero.team, 'magic')",
    }


def source_fixture():
    catalog, inventory_class, _boss_class, _game_class, _lane = _build_source_runtime()
    cases = []
    for scenario in SCENARIOS:
        expected = _run_case(inventory_class, scenario, native_old=False)
        native_old = _run_case(inventory_class, scenario, native_old=True)
        cases.append(
            {
                "name": scenario["name"],
                "attacker_kind": scenario["attacker_kind"],
                "hero_armor": int(scenario.get("hero_armor", 0)),
                "expect_divergence": bool(scenario["expect_divergence"]),
                "expected": expected,
                "native_old": native_old,
            }
        )
    return {
        "source": (
            "hero_items.py::HeroItemInventory.notify_damage_taken reflect arm"
            " :2459-2472 via the real Minion.take_damage / Hero.take_damage"
        ),
        "native_old_model": (
            "pre-9s native bus: `world._deliver_hit(-1, src_team, attacker,"
            " amount, school, attacker.position)` with the declared magic school"
            " and the `normal` damage-type default"
        ),
        "reflect_sent": REFLECT_SENT,
        "incoming_damage": INCOMING_DAMAGE,
        "live_stats": {
            "undead_magic_resist": UNDEAD_MAGIC_RESIST,
            "troll_armor": TROLL_ARMOR,
            "hero_armor": HERO_ARMOR,
        },
        "armor_item": ARMOR_ITEM,
        "shape": _shape(inventory_class),
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not (args.self_test or args.write):
        parser.error("one of the arguments --self-test --write is required")
    fixture = source_fixture()
    if args.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
        print("wrote %s (%d cases)" % (FIXTURE.name, len(fixture["cases"])))
        return 0
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if committed != fixture:
        print("FAIL: fixture drift vs %s" % FIXTURE)
        return 1
    print("item reflect unit oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
