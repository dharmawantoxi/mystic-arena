"""9e: source oracle for the damage arguments of hero item cleave on a boss.

Layer 8z proved the active boss is a legal secondary target of the cleave
splash, but it recorded the hit through a stubbed `take_damage`, so the call
*shape* was never compared. The source splash is

    u.take_damage(splash, h.team)                     # hero_items.py:2516

inside `HeroItemInventory.on_basic_attack_hit`: no `damage_type`, no `source=`
and no `school=`. For the active boss that reaches `Boss.take_damage`
(`bosses/base_boss.py:5978`) as `damage_type='normal'`, `source=None`,
`school=None`, which means

* the Solar Brand blind block at the head of the method is skipped (it needs
  `source is not None`), so a blinded cleaver still splashes the boss;
* `resolve_damage_school('normal', None, None)` returns `None`
  (`_entity.py:106-130`), so boss armor and magic resist never apply;
* a lethal splash stores `self._killed_by = None`, so `Game._process_boss_kill`
  (`_core.py:2516-2545`) credits nobody.

The native bus delivered the same arm as
`world._deliver_hit(dealer_id, src_team, boss, splash, "physical", src_pos)`
(`scripts/match/battle_item_effects.gd::cleave_splash`), i.e. with the attacking
hero as `source` and an explicit physical school. Every row therefore carries
`expected` (source arguments) and `native_old` (the pre-9e native arguments).

Four deterministic scenarios are recorded for each of the 216 boss types (864
cases): armor mitigation, a fully blinded owner, a lethal splash, and a boss
outside the cleave radius as the control. `--self-test` runs the oracle without
touching the fixture; `--write` is the only fixture writer.
"""
import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from boss_item_cleave_chain_source_oracle import (  # noqa: E402
    _DummyOwner,
    _DummyUnit,
    _build_runtime,
    _compact,
    _method_text,
)
from boss_kill_credit_source_oracle import (  # noqa: E402
    core_boss_class,
    core_namespace,
    credit_game,
    game_class,
)
from bosses.boss_data import get_all_boss_types  # noqa: E402
from check_source_contract import source_lanes  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures/boss_item_cleave_damage_source.json"

# Source teams are the strings "blue"/"red"; `Game._process_boss_kill` compares
# `killer.team != "blue"` literally, so the oracle keeps the source types.
BLUE = "blue"
RED = "red"
MAIN_TARGET_ID = 10
NEAR_MINION_ID = 11
OWNER_ID = 7
BASIC_DAMAGE = 50
CLEAVE_ITEM = "cleave_axe"
INSIDE_X = 60.0
OUTSIDE_X = 140.0
NEAR_MINION_X = 30.0
BLIND_TICKS = 90

# Each scenario: boss offset from the main target, owner blind state and the
# boss hp the splash lands on. `lethal` puts the boss at 1 hp so the splash
# kills it; the other rows keep the boss at full hp.
SCENARIOS = (
    {
        "name": "cleave_school_vs_boss_armor",
        "boss_offset": INSIDE_X,
        "blind": False,
        "lethal": False,
    },
    {
        "name": "cleave_blind_owner_still_lands",
        "boss_offset": INSIDE_X,
        "blind": True,
        "lethal": False,
    },
    {
        "name": "cleave_lethal_without_kill_credit",
        "boss_offset": INSIDE_X,
        "blind": False,
        "lethal": True,
    },
    {
        "name": "cleave_outside_radius_control",
        "boss_offset": OUTSIDE_X,
        "blind": False,
        "lethal": False,
    },
)
CONTROL_SCENARIO = "cleave_outside_radius_control"


def _boss_method(name):
    tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    boss = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss"
    )
    return next(
        node for node in boss.body if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _cleave_call_arity():
    """Number of positional args of the cleave `take_damage` call in source."""
    onhit = ast.parse(_method_text("HeroItemInventory", "on_basic_attack_hit", "hero_items.py"))
    for node in ast.walk(onhit):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "take_damage"
            and ast.unparse(node.func.value) == "u"
            and any(ast.unparse(arg) == "splash" for arg in node.args)
        ):
            return len(node.args), sorted(keyword.arg for keyword in node.keywords)
    return -1, []


def _source_shape():
    arity, keywords = _cleave_call_arity()
    blind_block = ast.unparse(_boss_method("take_damage"))
    resolve = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    resolver = next(
        node
        for node in resolve.body
        if isinstance(node, ast.FunctionDef) and node.name == "resolve_damage_school"
    )
    resolver_text = _compact(ast.unparse(resolver))
    return {
        "cleave_take_damage_positional_args": arity,
        "cleave_take_damage_keywords": keywords,
        "boss_blind_block_requires_source": _compact(
            "if damage_type == 'normal' and damage > 0 and (source is not None):"
        )
        in _compact(blind_block),
        "boss_school_comes_from_resolver": "resolve_damage_school(damage_type, source, school)"
        in blind_block,
        "resolver_returns_none_without_school_or_source": (
            _compact("if source is None:") in resolver_text and _compact("return None") in resolver_text
        ),
        "boss_lethal_branch_stores_source": "self._killed_by = source" in blind_block,
    }


def _build_source_runtime():
    catalog, inventory_class, _unused_boss = _build_runtime()
    env = core_namespace()
    boss_class = core_boss_class(env)
    lane = source_lanes()["mid"]
    return catalog, inventory_class, boss_class, game_class(), lane


def _prepare_boss(boss_class, boss_type, lane, scenario):
    boss = boss_class(boss_type, lane)
    boss.id = 500
    boss.team = RED
    boss.alive = True
    boss.defeated = False
    boss.x = float(scenario["boss_offset"])
    boss.y = 0.0
    boss._killed_by = None
    if scenario["lethal"]:
        boss.hp = 1
    else:
        boss.hp = boss.max_hp
    return boss


def _prepare_owner(inventory_class, target, scenario):
    owner = _DummyOwner(target)
    owner.id = OWNER_ID
    owner.team = BLUE
    owner.kills = 0
    owner.name = "Kaizen"
    owner.hero_type = "kaizen"
    owner.skills = ["q", "w", "e", "r"]
    owner.blind_timer = BLIND_TICKS if scenario["blind"] else 0
    owner.blind_amount = 1.0 if scenario["blind"] else 0.0
    inventory = inventory_class(owner)
    owner.items = inventory
    assert inventory.add(CLEAVE_ITEM), "cannot equip Cleave Axe"
    return owner, inventory


def _run_case(catalog, inventory_class, boss_class, source_game_class, lane,
              boss_type, scenario, native_old):
    boss = _prepare_boss(boss_class, boss_type, lane, scenario)
    target = _DummyUnit(MAIN_TARGET_ID, RED, 0.0)
    near = _DummyUnit(NEAR_MINION_ID, RED, NEAR_MINION_X)
    owner, inventory = _prepare_owner(inventory_class, target, scenario)
    # Source melee on-hit list: minions, then heroes, then the living boss.
    all_units = [target, near, owner, boss]

    if native_old:
        source_take_damage = boss.take_damage

        def native_cleave(damage, from_team=None, damage_type="normal", source=None, school=None):
            # Pre-9e native bus: the dealing hero is passed as `source` and the
            # splash is declared physical.
            return source_take_damage(
                damage, from_team, damage_type, source=owner, school="physical"
            )

        boss.take_damage = native_cleave

    hp_before = float(boss.hp)
    inventory.on_basic_attack_hit(target, BASIC_DAMAGE, all_units)
    hp_loss = int(round(hp_before - float(boss.hp)))

    game = credit_game(source_game_class)
    game._process_boss_kill(boss)
    splash = int(BASIC_DAMAGE * float(catalog[CLEAVE_ITEM]["passive"]["cleave_pct"]))
    return {
        "splash_damage": splash,
        "boss_hp_before": int(hp_before),
        "boss_hp_loss": hp_loss,
        "boss_alive": bool(boss.alive),
        "killed_by_owner": getattr(boss, "_killed_by", None) is owner,
        "owner_kills": int(owner.kills),
        "miniboss_kill_count": int(game.miniboss_kill_count),
        "trueboss_kill_count": int(game.trueboss_kill_count),
        "minion_hits": list(near.hits),
        "target_hits": list(target.hits),
    }


def source_fixture():
    catalog, inventory_class, boss_class, source_game_class, lane = _build_source_runtime()
    cleave = catalog[CLEAVE_ITEM]["passive"]
    cases = []
    for boss_type in sorted(get_all_boss_types()):
        for scenario in SCENARIOS:
            expected = _run_case(
                catalog, inventory_class, boss_class, source_game_class, lane,
                boss_type, scenario, native_old=False,
            )
            native_old = _run_case(
                catalog, inventory_class, boss_class, source_game_class, lane,
                boss_type, scenario, native_old=True,
            )
            cases.append(
                {
                    "boss_type": boss_type,
                    "scenario": scenario["name"],
                    "boss_offset": float(scenario["boss_offset"]),
                    "owner_blind": bool(scenario["blind"]),
                    "boss_hp_before": expected["boss_hp_before"],
                    "expected": expected,
                    "native_old": native_old,
                }
            )
    fixture = {
        "source": {
            "ast_shape": _source_shape(),
            "cleave_pct": float(cleave["cleave_pct"]),
            "cleave_radius": float(cleave["cleave_radius"]),
            "basic_damage": BASIC_DAMAGE,
            "splash_damage": int(BASIC_DAMAGE * float(cleave["cleave_pct"])),
            "main_target_x": 0.0,
            "near_minion_x": NEAR_MINION_X,
            "blind_ticks": BLIND_TICKS,
            "owner_team": "blue",
            "boss_team": "red",
            "scenario_names": [scenario["name"] for scenario in SCENARIOS],
        },
        "boss_type_count": len(get_all_boss_types()),
        "case_count": len(cases),
        "cases": cases,
    }
    _assert_fixture_logic(fixture)
    return fixture


def _assert_fixture_logic(fixture):
    shape = fixture["source"]["ast_shape"]
    assert shape["cleave_take_damage_positional_args"] == 2, "cleave call shape drifted"
    assert shape["cleave_take_damage_keywords"] == [], "cleave call gained keywords"
    assert shape["boss_blind_block_requires_source"], "boss blind gate drifted"
    assert shape["boss_school_comes_from_resolver"], "boss school resolution drifted"
    assert shape["resolver_returns_none_without_school_or_source"], "damage school resolver drifted"
    assert shape["boss_lethal_branch_stores_source"], "boss kill attribution drifted"
    cases = fixture["cases"]
    boss_types = {row["boss_type"] for row in cases}
    assert fixture["boss_type_count"] == 216 and len(boss_types) == 216
    assert fixture["case_count"] == len(cases) == 864
    assert all(sum(row["boss_type"] == boss for row in cases) == 4 for boss in boss_types)
    splash = fixture["source"]["splash_damage"]
    blind_gap = 0
    armor_gap = 0
    for row in cases:
        expected = row["expected"]
        native_old = row["native_old"]
        # The regular-unit arm is untouched by this slice in every scenario.
        assert expected["minion_hits"] == native_old["minion_hits"] == [splash]
        assert expected["target_hits"] == native_old["target_hits"] == []
        if row["scenario"] == CONTROL_SCENARIO:
            assert expected == native_old, "control row must not diverge"
            assert expected["boss_hp_loss"] == 0 and expected["boss_alive"]
            continue
        if row["scenario"] == "cleave_blind_owner_still_lands":
            assert expected["boss_hp_loss"] > 0, "source blind gate needs a source"
            assert native_old["boss_hp_loss"] == 0, "pre-9e native dropped the splash"
            blind_gap += 1
        if row["scenario"] == "cleave_school_vs_boss_armor":
            assert expected["boss_hp_loss"] >= native_old["boss_hp_loss"]
            if expected["boss_hp_loss"] != native_old["boss_hp_loss"]:
                armor_gap += 1
        if row["scenario"] == "cleave_lethal_without_kill_credit":
            assert not expected["boss_alive"] and not native_old["boss_alive"]
            assert expected["owner_kills"] == 0 and not expected["killed_by_owner"]
            assert native_old["owner_kills"] == 1 and native_old["killed_by_owner"]
            assert expected["miniboss_kill_count"] + expected["trueboss_kill_count"] == 0
            assert native_old["miniboss_kill_count"] + native_old["trueboss_kill_count"] == 1
    assert blind_gap == 216, "every boss type records the blind gap"
    assert armor_gap > 0, "at least one boss has armor that the native school cut"


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    fixture = source_fixture()
    if args.write:
        FIXTURE.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {len(fixture['cases'])} cleave damage cases to {FIXTURE}")
    else:
        print(
            "cleave damage oracle self-test passed: "
            f"{len(fixture['cases'])} cases across {fixture['boss_type_count']} bosses"
        )


if __name__ == "__main__":
    main()
