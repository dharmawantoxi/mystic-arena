"""Layer 9p oracle: the un-sourced item arms against minion and hero victims.

The source `HeroItemInventory.on_basic_attack_hit` arms land their bonus with
`target.take_damage(bash["damage"], h.team)` (`hero_items.py:2542`) and
`take_damage(damage, h.team, "magic")` (`:2568/:2589/:2633/:2648`): three (or
two) positional arguments and never a `source=`, so `Minion.take_damage` /
`Hero.take_damage` run school-free and `credit_hero_damage(None, ...)` records
nothing. Layer 9o already routed structure victims that way; this oracle pins
the same route for the two unit victims.

`--self-test` verifies the executed ladder against the committed fixture;
`--write` is the only fixture writer.
"""

import argparse
import ast
import json
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from boss_item_cleave_chain_source_oracle import _DummyOwner, _build_runtime  # noqa: E402
from hero_veil_immunity_source_oracle import (  # noqa: E402
    _FakeHero,
    _case,
    _take_damage_callable,
)
from minion_damage_ladder_source_oracle import (  # noqa: E402
    _FakeMinion,
    _minion_take_damage_callable,
)

FIXTURE = Path(__file__).parent / "fixtures/item_unit_arm_source.json"
BLUE = "blue"
RED = "red"
BASIC_DAMAGE = 50
BASH_ITEM = "abyss_breaker"
PIERCE_ITEM = "sundering_cudgel"
TROLL_ARMOR = 2
UNDEAD_MAGIC_RESIST = 0.15
HERO_ARMOR = 6


def _minion_case(scenario, damage):
    return {
        "name": "unit_arm",
        "damage": damage,
        "damage_type": "normal",
        "school": None,
        "source_school": None,
        "armor": int(scenario.get("minion_armor", 0)),
        "magic_resist": float(scenario.get("minion_magic_resist", 0.0)),
        "armor_shred": 0.0,
        "dmg_amp_timer": 0,
        "dmg_amp_amount": 0.0,
    }


def _victim(kind, scenario):
    """Unit stub wired to the real ladder; returns (victim, recorder)."""
    if kind == "minion":
        take_damage, _resolve, recorder = _minion_take_damage_callable()
        minion = _FakeMinion(_minion_case(scenario, 0))
        minion.team = RED
        minion.id = 500
        minion.take_damage = types.MethodType(take_damage, minion)
        return minion, recorder
    take_damage, recorder = _take_damage_callable()
    hero = _FakeHero(_case("unit_arm", armor=int(scenario.get("hero_armor", 0)), draws=[0.9]))
    hero.team = RED
    hero.id = 500
    hero.take_damage = types.MethodType(take_damage, hero)
    return hero, recorder


SCENARIOS = (
    {
        "name": "bash_on_minion_armor",
        "kind": "minion",
        "item": BASH_ITEM,
        "arm": "bash",
        "native_damage_type": "normal",
        "native_school": "physical",
        "minion_kind": "troll",
        "minion_armor": TROLL_ARMOR,
    },
    {
        "name": "pierce_bash_on_minion_magic_resist",
        "kind": "minion",
        "item": PIERCE_ITEM,
        "arm": "bash",
        "native_damage_type": "magic",
        "native_school": "magic",
        "minion_kind": "undead",
        "minion_magic_resist": UNDEAD_MAGIC_RESIST,
    },
    {
        "name": "bash_on_hero_armor",
        "kind": "hero",
        "item": BASH_ITEM,
        "arm": "bash",
        "native_damage_type": "normal",
        "native_school": "physical",
        "hero_armor": HERO_ARMOR,
    },
    {
        "name": "pierce_bash_on_hero_unarmoured",
        "kind": "hero",
        "item": PIERCE_ITEM,
        "arm": "bash",
        "native_damage_type": "magic",
        "native_school": "magic",
        "hero_armor": 0,
    },
)


def _prepare_owner(inventory_class, target):
    owner = _DummyOwner(target)
    owner.id = 7
    owner.team = BLUE
    owner.kills = 0
    owner.name = "Kaizen"
    owner.hero_type = "kaizen"
    owner.skills = ["q", "w", "e", "r"]
    inventory = inventory_class(owner)
    owner.items = inventory
    return owner, inventory


def _credit_rows(recorder):
    return [[bool(row[0]), int(row[1])] for row in recorder.rolls]


def _credited_total(rows):
    """`credit_hero_damage` skips the credit when `source is None`."""
    return sum(row[1] for row in rows if row[0])


def _run_case(catalog, inventory_class, scenario, native_old):
    victim, recorder = _victim(str(scenario["kind"]), scenario)
    owner, inventory = _prepare_owner(inventory_class, victim)
    assert inventory.add(str(scenario["item"])), "cannot equip " + str(scenario["item"])
    arm_damage = int(catalog[str(scenario["item"])][str(scenario["arm"])]["damage"])
    owner.dmg_school = str(scenario["native_school"])

    if native_old:
        real_take_damage = victim.take_damage

        def native_arm(damage, from_team=None, damage_type="normal", source=None, school=None):
            # Pre-9p native bus: the arm carried the dealing hero as source and
            # the declared school.
            return real_take_damage(
                damage,
                from_team,
                damage_type,
                source=owner,
                school=str(scenario["native_school"]),
            )

        victim.take_damage = native_arm
    recorder.rolls.clear()

    hp_before = float(victim.hp)
    inventory.on_basic_attack_hit(victim, BASIC_DAMAGE, [victim, owner])
    rows = _credit_rows(recorder)
    return {
        "arm_damage": arm_damage,
        "hp_loss": int(round(hp_before - float(victim.hp))),
        "credits": rows,
        "credited_total": _credited_total(rows),
    }


def _shape() -> dict:
    """The arm call sites pass no `source=`, so the victim ladder stays sourceless."""
    text = (ROOT / "hero_items.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "take_damage" and node.lineno >= 2500:
                calls.append(node)
    sourceless = [
        node
        for node in calls
        if not any(keyword.arg == "source" for keyword in node.keywords)
    ]
    return {
        "arm_take_damage_calls": len(calls),
        "arm_calls_without_source_kwarg": len(sourceless),
        "bash_call": "hero_items.py:2542 target.take_damage(bash['damage'], h.team)",
        "magic_arms": (
            "hero_items.py:2568/:2589/:2633/:2648"
            " u.take_damage(damage, h.team, 'magic')"
        ),
    }


def source_fixture():
    catalog, inventory_class, _unused_boss = _build_runtime()
    cases = []
    for scenario in SCENARIOS:
        expected = _run_case(catalog, inventory_class, scenario, native_old=False)
        native_old = _run_case(catalog, inventory_class, scenario, native_old=True)
        cases.append(
            {
                "name": scenario["name"],
                "victim_kind": scenario["kind"],
                "minion_kind": scenario.get("minion_kind", ""),
                "native_school": scenario["native_school"],
                "item": scenario["item"],
                "minion_armor": int(scenario.get("minion_armor", 0)),
                "minion_magic_resist": float(scenario.get("minion_magic_resist", 0.0)),
                "hero_armor": int(scenario.get("hero_armor", 0)),
                "expected": expected,
                "native_old": native_old,
            }
        )
    return {
        "source": (
            "_entity.py::Minion.take_damage :5795 / Hero.take_damage via the"
            " un-sourced item arms of hero_items.py"
        ),
        "native_old_model": (
            "pre-9p native bus: `deal_damage(target_id, hero_team, amount, school)`"
            " kept the dealing hero as source and the declared school"
        ),
        "arm_sources": {
            "bash": "hero_items.py:2542 abyss_breaker",
            "pierce_bash": "hero_items.py:2589 sundering_cudgel",
        },
        "shape": _shape(),
        "live_stats": {
            "troll_armor": TROLL_ARMOR,
            "undead_magic_resist": UNDEAD_MAGIC_RESIST,
            "hero_armor": HERO_ARMOR,
        },
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
    print("item unit arm oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
