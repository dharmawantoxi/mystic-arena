"""Layer 9r oracle: the magic arms against MINION/HERO victims.

The on-hit magic arms pass the damage type as the source third positional
argument: `u.take_damage(chain["damage"], h.team, "magic")`
(`hero_items.py:2552-2570`) and `target.take_damage(b["damage"], h.team,
"magic")` (`:2589`). Layer 9g routed the BOSS victim that way; layers 9p/9q
made the unit victims sourceless but still delivered the `"normal"` default, so
the victim ran a hit the source never sends: a hero with Windrun active rolled
the 75% miss gate and an evasive hero rolled Monarch Wings evasion for an arm
the source marks as magic (both gates are `_is_physical_hit` driven:
`_entity.py:92-103`).

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
    _RecordingRandom,
    _case,
    _take_damage_callable,
)
from minion_damage_ladder_source_oracle import (  # noqa: E402
    _FakeMinion,
    _minion_take_damage_callable,
)

FIXTURE = Path(__file__).parent / "fixtures/item_magic_arm_unit_source.json"
BLUE = "blue"
RED = "red"
BASIC_DAMAGE = 50
EVASION_ITEM = "monarch_wings"
ARMOR_ITEM = "steel_aegis"
PIERCE_ITEM = "sundering_cudgel"
CHAIN_ITEM = "fenrir_chain"
TROLL_ARMOR = 2
HERO_ARMOR = 6
EVASION = 0.28
SPLASH_DISTANCE = 30.0


def _minion_case(kind, damage=0):
    return {
        "name": "magic_arm",
        "damage": damage,
        "damage_type": "normal",
        "school": None,
        "source_school": None,
        "armor": TROLL_ARMOR if kind == "troll" else 0,
        "magic_resist": 0.0,
        "armor_shred": 0.0,
        "dmg_amp_timer": 0,
        "dmg_amp_amount": 0.0,
    }


def _hero_victim(scenario, draws):
    take_damage, _credits = _take_damage_callable()
    hero = _FakeHero(
        _case(
            "magic_arm",
            armor=int(scenario.get("hero_armor", 0)),
            evasion=float(scenario.get("hero_evasion", 0.0)),
            windrun=bool(scenario.get("hero_windrun", False)),
        )
    )
    hero.team = RED
    hero.x = SPLASH_DISTANCE
    hero.y = 0.0
    hero.frame = take_damage.__globals__
    hero.real_take_damage = types.MethodType(take_damage, hero)
    return hero


def _minion_victim(scenario):
    take_damage, _resolve, credits = _minion_take_damage_callable()
    minion = _FakeMinion(_minion_case(str(scenario.get("minion_kind", "troll"))))
    minion.team = RED
    minion.x = SPLASH_DISTANCE
    minion.y = 0.0
    minion.frame = take_damage.__globals__
    minion.real_take_damage = types.MethodType(take_damage, minion)
    minion.credits = credits
    return minion


def _victim(scenario, draws):
    if str(scenario["victim_kind"]) == "hero":
        return _hero_victim(scenario, draws)
    return _minion_victim(scenario)


def _prepare_owner(inventory_class, target):
    owner = _DummyOwner(target)
    owner.id = 7
    owner.team = BLUE
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
    draws = [float(value) for value in scenario["draws"]]
    victim = _victim(scenario, draws)
    owner, inventory = _prepare_owner(inventory_class, victim)
    assert inventory.add(str(scenario["item"])), "cannot equip " + str(scenario["item"])
    owner.dmg_school = "physical"

    if native_old:
        real = victim.real_take_damage

        def native_arm(damage, from_team=None, damage_type="normal", source=None, school=None):
            # Pre-9r native bus: the unit arms fell back to `deal_damage`, which
            # delivered school-free damage with the `"normal"` type default.
            return real(damage, from_team, "normal", source=None, school=None)

        victim.take_damage = native_arm
    else:
        victim.take_damage = victim.real_take_damage

    target = victim
    all_units = [victim, owner]
    if scenario.get("primary") is not None:
        # Chain rows need a live enemy primary target at the impact point for
        # the arm to iterate over `all_units`.
        primary = _minion_victim({"minion_kind": "troll"})
        primary.x = 0.0
        primary.y = 0.0
        target = primary
        all_units = [primary, victim, owner]

    victim.frame["random"] = _RecordingRandom(list(draws))
    victim.frame["_ACTIVE_HERO"] = [None]
    credits_before = len(victim.credits.rolls) if hasattr(victim, "credits") else None
    hp_before = float(victim.hp)
    inventory.on_basic_attack_hit(target, BASIC_DAMAGE, all_units)
    hp_loss = int(round(hp_before - float(victim.hp)))
    if credits_before is None:
        rows = [[row[0], row[1]] for row in victim.frame["_recorder"].rolls]
    else:
        rows = [[row[0], row[1]] for row in victim.credits.rolls[credits_before:]]
    return {
        "hp_loss": hp_loss,
        "credited_total": _credited_total(rows),
        "draws": victim.frame["random"].draws,
    }


def _shape() -> dict:
    """The magic unit arms pass the damage type as the third positional arg."""
    text = (ROOT / "hero_items.py").read_text(encoding="utf-8")
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
    ]
    return {
        "unit_arm_calls_with_magic_type": len(calls),
        "calls_with_source_kwarg": sum(
            1 for node in calls if any(keyword.arg == "source" for keyword in node.keywords)
        ),
        "chain_call": "hero_items.py:2568 u.take_damage(chain['damage'], h.team, 'magic')",
        "pierce_call": "hero_items.py:2589 target.take_damage(b['damage'], h.team, 'magic')",
    }


SCENARIOS = (
    {
        "name": "chain_on_windrun_hero",
        "item": CHAIN_ITEM,
        "arm": "chain",
        "victim_kind": "hero",
        "primary": "troll",
        "hero_windrun": True,
        "draws": [0.1],
        "expect_divergence": True,
    },
    {
        "name": "chain_on_evasive_hero",
        "item": CHAIN_ITEM,
        "arm": "chain",
        "victim_kind": "hero",
        "primary": "troll",
        "hero_evasion": EVASION,
        "draws": [0.1],
        "expect_divergence": True,
    },
    {
        "name": "pierce_bash_on_armoured_hero",
        "item": PIERCE_ITEM,
        "arm": "pierce_bash",
        "victim_kind": "hero",
        "hero_armor": HERO_ARMOR,
        "draws": [0.1],
        "expect_divergence": False,
    },
    {
        "name": "pierce_bash_on_minion",
        "item": PIERCE_ITEM,
        "arm": "pierce_bash",
        "victim_kind": "minion",
        "minion_kind": "troll",
        "draws": [0.1],
        "expect_divergence": False,
    },
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
                "item": scenario["item"],
                "arm": scenario["arm"],
                "victim_kind": scenario["victim_kind"],
                "minion_kind": scenario.get("minion_kind", ""),
                "hero_armor": int(scenario.get("hero_armor", 0)),
                "hero_evasion": float(scenario.get("hero_evasion", 0.0)),
                "hero_windrun": bool(scenario.get("hero_windrun", False)),
                "draws": [float(value) for value in scenario["draws"]],
                "expect_divergence": bool(scenario["expect_divergence"]),
                "expected": expected,
                "native_old": native_old,
            }
        )
    return {
        "source": (
            "hero_items.py::HeroItemInventory._on_hit_common magic arms"
            " :2552-2570 (chain) / :2589 (piercing bash) via the real"
            " Hero.take_damage / Minion.take_damage"
        ),
        "native_old_model": (
            "pre-9r native bus: `deal_damage_magic_sourceless` handed unit"
            " victims to `deal_damage`, which delivered `-1`/`neutral` with the"
            " `normal` damage type - the source third positional argument"
            " `\"magic\"` only reached the boss arm (layer 9g)"
        ),
        "evasion_item": EVASION_ITEM,
        "armor_item": ARMOR_ITEM,
        "live_stats": {
            "troll_armor": TROLL_ARMOR,
            "hero_armor": HERO_ARMOR,
            "evasion": EVASION,
        },
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
    print("item magic arm unit oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
