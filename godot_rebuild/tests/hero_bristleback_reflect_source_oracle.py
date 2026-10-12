"""Layer 9t oracle: the Bristleback reflect against minion/hero attackers.

`Hero.take_damage` (`_entity.py:4697-4711`) reflects `max(1, int(damage * 0.25))`
of the damage that landed with `_src.take_damage(payload, self.team,
source=None)`: two positional arguments plus a `source=None` keyword, so the
attacker runs with `damage_type="normal"` and `school=None`. The native
`_deliver_hit` sent the reflect with school `"physical"`, so an armoured
attacker (troll, armor 2) ate an armour cut the source never applies and the
delivered hit carried a school the source never sends.

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

FIXTURE = Path(__file__).parent / "fixtures/hero_bristleback_reflect_source.json"
BLUE = "blue"
RED = "red"
ATTACKER_ID = 11
INCOMING_DAMAGE = 200
UNDEAD_MAGIC_RESIST = 0.15
TROLL_ARMOR = 2
TROLL_MAGIC_RESIST = 0.05
HERO_ARMOR = 6
ARMOR_ITEM = "steel_aegis"
KEEP_PHYSICAL = 0.70
KEEP_MAGIC = 0.85
REFLECT_PCT = 0.25


def _minion_case(kind):
    return {
        "name": "bristleback_reflect",
        "damage": 0,
        "damage_type": "normal",
        "school": None,
        "source_school": None,
        "armor": TROLL_ARMOR if kind == "troll" else 0,
        "magic_resist": (
            TROLL_MAGIC_RESIST
            if kind == "troll"
            else UNDEAD_MAGIC_RESIST
            if kind == "undead"
            else 0.0
        ),
        "armor_shred": 0.0,
        "dmg_amp_timer": 0,
        "dmg_amp_amount": 0.0,
    }


def _attacker(scenario):
    """Attacker stub wired to the real unit ladder; returns (attacker, credits)."""
    kind = str(scenario["attacker_kind"])
    if kind == "hero":
        take_damage, credits = _take_damage_callable()
        attacker = _FakeHero(_case("bristleback_reflect", armor=int(scenario.get("hero_armor", 0))))
    else:
        take_damage, _resolve, credits = _minion_take_damage_callable()
        attacker = _FakeMinion(_minion_case(kind))
    attacker.id = ATTACKER_ID
    attacker.team = RED
    attacker.alive = True
    attacker.x = 20.0
    attacker.y = 0.0
    attacker.frame = take_damage.__globals__
    attacker.ladder = types.MethodType(take_damage, attacker)
    return attacker, credits


def _credited_total(rows):
    """`credit_hero_damage` skips the credit when `source is None`."""
    return sum(row[1] for row in rows if row[0])


def _run_case(scenario, native_old):
    take_damage, _credits = _take_damage_callable()
    defender = _FakeHero(_case("bristleback_reflect", bristleback=True, draws=[0.9]))
    defender.team = BLUE
    defender.hp = 1000.0
    defender.take_damage = types.MethodType(take_damage, defender)
    attacker, credits = _attacker(scenario)
    # A magic incoming hit spreads on the attacker's `dmg_school` (the hero
    # ladder resolves the school from the source), which is what flips the
    # Bristleback keep from 0.70 to 0.85.
    if str(scenario.get("incoming_school", "physical")) == "magic":
        attacker.dmg_school = "magic"
    observed = []

    def reflect_take_damage(damage, from_team=None, damage_type="normal", source=None, school=None):
        # Observe the arguments the reflect arm actually sent. The native_old
        # column substitutes the pre-9t delivery: `_deliver_hit` handed the
        # attacker the declared physical school with no source.
        observed.append([int(damage), str(damage_type), school if school else "neutral"])
        if native_old:
            return attacker.ladder(
                damage, from_team, "normal", source=None, school="physical"
            )
        return attacker.ladder(damage, from_team, damage_type, source=source, school=school)

    attacker.take_damage = reflect_take_damage
    credits_before = len(credits.rolls)
    hp_before = float(attacker.hp)
    defender_hp_before = float(defender.hp)
    defender.take_damage(INCOMING_DAMAGE, RED, source=attacker)
    rows = [[row[0], row[1]] for row in credits.rolls[credits_before:]]
    return {
        "attacker_hp_loss": int(round(hp_before - float(attacker.hp))),
        "defender_hp_loss": int(round(defender_hp_before - float(defender.hp))),
        "credited_total": _credited_total(rows),
        "reflect_args": observed,
    }


SCENARIOS = (
    {
        "name": "bristleback_on_troll_attacker",
        "attacker_kind": "troll",
        "expect_divergence": True,
    },
    {
        "name": "bristleback_on_troll_attacker_magic_hit",
        "attacker_kind": "troll",
        "incoming_school": "magic",
        "expect_divergence": True,
    },
    {
        "name": "bristleback_on_undead_attacker",
        "attacker_kind": "undead",
        "expect_divergence": False,
    },
    {
        "name": "bristleback_on_armoured_hero_attacker",
        "attacker_kind": "hero",
        "hero_armor": HERO_ARMOR,
        "expect_divergence": False,
    },
    {
        "name": "bristleback_on_unarmoured_hero_attacker",
        "attacker_kind": "hero",
        "hero_armor": 0,
        "expect_divergence": False,
    },
)


def _shape() -> dict:
    """The source reflect passes no school and a `source=None` keyword."""
    import ast

    root = Path(__file__).resolve().parents[2]
    text = (root / "_entity.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    holder = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Hero"
    )
    method = next(
        node for node in holder.body if isinstance(node, ast.FunctionDef) and node.name == "take_damage"
    )
    calls = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "take_damage"
        and len(node.args) == 2
        and isinstance(node.args[0], ast.Call)
        and isinstance(node.args[0].func, ast.Name)
        and node.args[0].func.id == "max"
    ]
    return {
        "reflect_calls": len(calls),
        "reflect_calls_with_source_kwarg_is_none": sum(
            1
            for node in calls
            if any(
                keyword.arg == "source"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is None
                for keyword in node.keywords
            )
        ),
        "reflect_calls_with_school_kwarg": sum(
            1 for node in calls if any(keyword.arg == "school" for keyword in node.keywords)
        ),
        "reflect_call": (
            "_entity.py:4708 _src.take_damage(max(1, int(damage * 0.25)), self.team,"
            " source=None)"
        ),
    }


def source_fixture():
    cases = []
    for scenario in SCENARIOS:
        expected = _run_case(scenario, native_old=False)
        native_old = _run_case(scenario, native_old=True)
        cases.append(
            {
                "name": scenario["name"],
                "attacker_kind": scenario["attacker_kind"],
                "hero_armor": int(scenario.get("hero_armor", 0)),
                "incoming_school": str(scenario.get("incoming_school", "physical")),
                "expect_divergence": bool(scenario["expect_divergence"]),
                "expected": expected,
                "native_old": native_old,
            }
        )
    return {
        "source": (
            "_entity.py::Hero.take_damage Bristleback reflect :4697-4711 via the"
            " real Minion.take_damage / Hero.take_damage of the attacker"
        ),
        "native_old_model": (
            "pre-9t native `_deliver_hit` reflect:"
            " `world._deliver_hit(-1, target.team, atk, payload, \"physical\","
            " target.position)` with the `normal` damage type default"
        ),
        "incoming_damage": INCOMING_DAMAGE,
        "reflect_pct": REFLECT_PCT,
        "keep_physical": KEEP_PHYSICAL,
        "keep_magic": KEEP_MAGIC,
        "live_stats": {
            "troll_armor": TROLL_ARMOR,
            "troll_magic_resist": TROLL_MAGIC_RESIST,
            "undead_magic_resist": UNDEAD_MAGIC_RESIST,
            "hero_armor": HERO_ARMOR,
        },
        "armor_item": ARMOR_ITEM,
        "shape": _shape(),
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
    print("hero bristleback reflect oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
