"""Layer 9q oracle: the un-sourced cleave splash against minion/hero victims.

`HeroItemInventory.on_basic_attack_hit` runs the Cleave Axe splash as
`u.take_damage(splash, h.team)` (`hero_items.py:2504-2518`) - two positional
arguments and never a `source=`, so every splash victim runs school-free and
`credit_hero_damage(None, ...)` records nothing. The native bus still delivered
the splash as `_deliver_hit(dealer_id, src_team, u, splash, "physical", ...)`,
which let the minion armour cut the splash and credited the dealing hero.

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

FIXTURE = Path(__file__).parent / "fixtures/item_cleave_splash_source.json"
BLUE = "blue"
RED = "red"
BASIC_DAMAGE = 100
CLEAVE_ITEM = "cleave_axe"
SPLASH_DISTANCE = 50.0
TROLL_ARMOR = 2
UNDEAD_MAGIC_RESIST = 0.15
HERO_ARMOR = 6


def _minion_case(spec, damage):
    kind, _, value = spec.partition(":")
    return {
        "name": "cleave_splash",
        "damage": damage,
        "damage_type": "normal",
        "school": None,
        "source_school": None,
        "armor": TROLL_ARMOR if kind == "troll" else 0,
        "magic_resist": UNDEAD_MAGIC_RESIST if kind == "undead" else 0.0,
        "armor_shred": 0.0,
        "dmg_amp_timer": 0,
        "dmg_amp_amount": 0.0,
    }


def _victim(spec, x, y):
    """Unit stub wired to the real ladder; returns (victim, recorder)."""
    kind, _, value = spec.partition(":")
    if kind in ("troll", "undead"):
        take_damage, _resolve, recorder = _minion_take_damage_callable()
        minion = _FakeMinion(_minion_case(spec, 0))
        minion.team = RED
        minion.alive = True
        minion.x = float(x)
        minion.y = float(y)
        minion.take_damage = types.MethodType(take_damage, minion)
        return minion, recorder
    take_damage, recorder = _take_damage_callable()
    hero = _FakeHero(_case("cleave_splash", armor=int(value or 0), draws=[0.9]))
    hero.team = RED
    hero.alive = True
    hero.x = float(x)
    hero.y = float(y)
    hero.take_damage = types.MethodType(take_damage, hero)
    return hero, recorder


def _prepare_owner(inventory_class):
    owner = _DummyOwner(None)
    owner.id = 7
    owner.team = BLUE
    owner.kills = 0
    owner.name = "Kaizen"
    owner.hero_type = "kaizen"
    owner.skills = ["q", "w", "e", "r"]
    inventory = inventory_class(owner)
    owner.items = inventory
    return owner, inventory


def _credited_total(rows):
    """`credit_hero_damage` skips the credit when `source is None`."""
    return sum(row[1] for row in rows if row[0])


def _run_case(catalog, inventory_class, scenario, native_old):
    primary, _primary_recorder = _victim("troll", 0.0, 0.0)
    victims = []
    for index, spec in enumerate(scenario["victims"]):
        victims.append(_victim(spec, SPLASH_DISTANCE, 10.0 * index))
    owner, inventory = _prepare_owner(inventory_class)
    assert inventory.add(CLEAVE_ITEM), "cannot equip " + CLEAVE_ITEM
    owner.dmg_school = "physical"
    if native_old:
        for victim, recorder in victims:
            real_take_damage = victim.take_damage

            def native_splash(
                damage, from_team=None, damage_type="normal", source=None, school=None, _real=real_take_damage
            ):
                # Pre-9q native bus: the splash carried the dealing hero as
                # source and the declared physical school.
                return _real(
                    damage, from_team, damage_type, source=owner, school="physical"
                )

            victim.take_damage = native_splash
    all_units = [primary] + [victim for victim, _ in victims] + [owner]
    for _victim_stub, recorder in victims:
        recorder.rolls.clear()
    inventory.on_basic_attack_hit(primary, BASIC_DAMAGE, all_units)
    hp_loss = []
    credited = []
    for victim, recorder in victims:
        rows = [[bool(row[0]), int(row[1])] for row in recorder.rolls]
        hp_loss.append(int(round(1000.0 - float(victim.hp))))
        credited.append(_credited_total(rows))
    passive = catalog[CLEAVE_ITEM]["passive"]
    return {
        "splash_damage": int(BASIC_DAMAGE * float(passive["cleave_pct"])),
        "hp_loss": hp_loss,
        "credited_total": credited,
        "total_hp_loss": sum(hp_loss),
        "total_credited": sum(credited),
    }


def _shape() -> dict:
    """The source splash call passes no school and no `source=`."""
    text = (ROOT / "hero_items.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "take_damage"
        and node.lineno >= 2500
        and len(node.args) == 2
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "splash"
    ]
    return {
        "splash_calls": len(calls),
        "splash_calls_with_source_kwarg": sum(
            1 for node in calls if any(keyword.arg == "source" for keyword in node.keywords)
        ),
        "splash_call": "hero_items.py:2516 u.take_damage(splash, h.team)",
    }


SCENARIOS = (
    {"name": "cleave_splash_on_minion", "victims": ["troll"]},
    {"name": "cleave_splash_on_hero_armor", "victims": ["hero:%d" % HERO_ARMOR]},
    {"name": "cleave_splash_on_hero_unarmoured", "victims": ["hero:0"]},
    {"name": "cleave_splash_on_two_minions", "victims": ["troll", "undead"]},
)


def source_fixture():
    catalog, inventory_class, _unused_boss = _build_runtime()
    cases = []
    for scenario in SCENARIOS:
        expected = _run_case(catalog, inventory_class, scenario, native_old=False)
        native_old = _run_case(catalog, inventory_class, scenario, native_old=True)
        cases.append(
            {
                "name": scenario["name"],
                "victims": list(scenario["victims"]),
                "splash_distance": SPLASH_DISTANCE,
                "expected": expected,
                "native_old": native_old,
            }
        )
    return {
        "source": (
            "hero_items.py::HeroItemInventory.on_basic_attack_hit cleave loop"
            " :2504-2518 via the real Minion.take_damage / Hero.take_damage"
        ),
        "native_old_model": (
            "pre-9q native bus: `world._deliver_hit(dealer_id, src_team, u,"
            " splash, \"physical\", src_pos)` gave the splash a source and the"
            " physical school"
        ),
        "cleave_item": CLEAVE_ITEM,
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
    print("item cleave splash oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
