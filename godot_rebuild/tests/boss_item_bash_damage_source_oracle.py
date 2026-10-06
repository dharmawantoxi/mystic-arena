"""9f: source oracle for the Abyss Breaker Bash damage arguments on a boss.

`HeroItemInventory._on_hit_common` lands the bash bonus with

    target.take_damage(bash["damage"], h.team)         # hero_items.py:2542

two positional arguments, exactly like the cleave splash closed in layer 9e.
When the victim is `game.active_boss` that reaches `Boss.take_damage`
(`bosses/base_boss.py:5978`) as `damage_type='normal'`, `source=None`,
`school=None`, so

* the Solar Brand blind block is skipped (it needs `source is not None`): a
  blinded bruiser still bashes the boss for full damage;
* `resolve_damage_school('normal', None, None)` returns `None`
  (`_entity.py:106-130`), so boss armor never cuts the 55 bonus damage;
* a lethal bash stores `self._killed_by = None`, so `Game._process_boss_kill`
  (`_core.py:2516-2545`) awards neither `kills` nor the mini/true boss counter.

The native bus delivered this arm as
`effects.deal_damage(target_id, hero_team, damage, "physical")`
(`scripts/match/hero_item_inventory.gd`), i.e. physical with the attacking hero
as `source`. Each row therefore carries `expected` (source arguments) and
`native_old` (the pre-9f native arguments).

Four deterministic scenarios per boss type (864 cases): armor mitigation, a
fully blinded owner, a lethal bash, and the internal bash cooldown as the
control that must stay identical. `--self-test` skips the fixture; `--write` is
the only fixture writer.
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

FIXTURE = Path(__file__).parent / "fixtures/boss_item_bash_damage_source.json"

# Source teams are the strings "blue"/"red"; `Game._process_boss_kill` compares
# `killer.team != "blue"` literally, so the oracle keeps the source types.
BLUE = "blue"
RED = "red"
MAIN_TARGET_ID = 10
OWNER_ID = 7
BASIC_DAMAGE = 50
BASH_ITEM = "abyss_breaker"
BOSS_X = 40.0
BLIND_TICKS = 90
COOLDOWN_LEFT = 5

SCENARIOS = (
    {
        "name": "bash_school_vs_boss_armor",
        "blind": False,
        "lethal": False,
        "bash_cd": 0,
    },
    {
        "name": "bash_blind_owner_still_lands",
        "blind": True,
        "lethal": False,
        "bash_cd": 0,
    },
    {
        "name": "bash_lethal_without_kill_credit",
        "blind": False,
        "lethal": True,
        "bash_cd": 0,
    },
    {
        "name": "bash_internal_cooldown_control",
        "blind": False,
        "lethal": False,
        "bash_cd": COOLDOWN_LEFT,
    },
)
CONTROL_SCENARIO = "bash_internal_cooldown_control"


def _boss_method(name):
    tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    boss = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss"
    )
    return next(
        node for node in boss.body if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _bash_call_shape():
    """Positional/keyword shape of the bash `take_damage` call in source."""
    common = ast.parse(_method_text("HeroItemInventory", "_on_hit_common", "hero_items.py"))
    for node in ast.walk(common):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "take_damage"
            and node.args
            and ast.unparse(node.args[0]) == "bash['damage']"
        ):
            return len(node.args), sorted(keyword.arg for keyword in node.keywords)
    return -1, []


def _source_shape():
    arity, keywords = _bash_call_shape()
    common = _method_text("HeroItemInventory", "_on_hit_common", "hero_items.py")
    take_damage = ast.unparse(_boss_method("take_damage"))
    return {
        "bash_take_damage_positional_args": arity,
        "bash_take_damage_keywords": keywords,
        "bash_requires_internal_cooldown": _compact("if bash and self.bash_cd <= 0")
        in _compact(common),
        "bash_sets_internal_cooldown": _compact("self.bash_cd = bash['cooldown']")
        in _compact(common),
        "boss_blind_block_requires_source": _compact(
            "if damage_type == 'normal' and damage > 0 and (source is not None):"
        )
        in _compact(take_damage),
        "boss_school_comes_from_resolver": "resolve_damage_school(damage_type, source, school)"
        in take_damage,
        "boss_lethal_branch_stores_source": "self._killed_by = source" in take_damage,
    }


def _build_source_runtime():
    catalog, inventory_class, _unused_boss = _build_runtime()
    boss_class = core_boss_class(core_namespace())
    lane = source_lanes()["mid"]
    return catalog, inventory_class, boss_class, game_class(), lane


def _prepare_boss(boss_class, boss_type, lane, scenario):
    boss = boss_class(boss_type, lane)
    boss.id = 500
    boss.team = RED
    boss.alive = True
    boss.defeated = False
    boss.x = BOSS_X
    boss.y = 0.0
    boss._killed_by = None
    boss.hp = 1 if scenario["lethal"] else boss.max_hp
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
    assert inventory.add(BASH_ITEM), "cannot equip Abyss Breaker"
    inventory.bash_cd = int(scenario["bash_cd"])
    return owner, inventory


def _run_case(catalog, inventory_class, boss_class, source_game_class, lane,
              boss_type, scenario, native_old):
    boss = _prepare_boss(boss_class, boss_type, lane, scenario)
    # The bash arm hits the hero's main target, so the boss is the victim here.
    owner, inventory = _prepare_owner(inventory_class, boss, scenario)
    bystander = _DummyUnit(MAIN_TARGET_ID, RED, 500.0)

    if native_old:
        source_take_damage = boss.take_damage

        def native_bash(damage, from_team=None, damage_type="normal", source=None, school=None):
            # Pre-9f native bus: `deal_damage(..., "physical")` forwarded the
            # dealing hero as `_deliver_hit` source.
            return source_take_damage(
                damage, from_team, damage_type, source=owner, school="physical"
            )

        boss.take_damage = native_bash

    hp_before = float(boss.hp)
    inventory.on_basic_attack_hit(boss, BASIC_DAMAGE, [boss, bystander, owner])
    hp_loss = int(round(hp_before - float(boss.hp)))

    game = credit_game(source_game_class)
    game._process_boss_kill(boss)
    return {
        "bash_damage": int(catalog[BASH_ITEM]["bash"]["damage"]),
        "boss_hp_before": int(hp_before),
        "boss_hp_loss": hp_loss,
        "boss_alive": bool(boss.alive),
        "bash_cd_after": int(inventory.bash_cd),
        "killed_by_owner": getattr(boss, "_killed_by", None) is owner,
        "owner_kills": int(owner.kills),
        "miniboss_kill_count": int(game.miniboss_kill_count),
        "trueboss_kill_count": int(game.trueboss_kill_count),
        "bystander_hits": list(bystander.hits),
    }


def source_fixture():
    catalog, inventory_class, boss_class, source_game_class, lane = _build_source_runtime()
    bash = catalog[BASH_ITEM]["bash"]
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
                    "owner_blind": bool(scenario["blind"]),
                    "bash_cd_before": int(scenario["bash_cd"]),
                    "boss_hp_before": expected["boss_hp_before"],
                    "expected": expected,
                    "native_old": native_old,
                }
            )
    fixture = {
        "source": {
            "ast_shape": _source_shape(),
            "bash_chance": float(bash["chance"]),
            "bash_damage": int(bash["damage"]),
            "bash_stun": int(bash["stun"]),
            "bash_cooldown": int(bash["cooldown"]),
            "basic_damage": BASIC_DAMAGE,
            "blind_ticks": BLIND_TICKS,
            "cooldown_left": COOLDOWN_LEFT,
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
    assert shape["bash_take_damage_positional_args"] == 2, "bash call shape drifted"
    assert shape["bash_take_damage_keywords"] == [], "bash call gained keywords"
    assert shape["bash_requires_internal_cooldown"], "bash cooldown gate drifted"
    assert shape["bash_sets_internal_cooldown"], "bash cooldown write drifted"
    assert shape["boss_blind_block_requires_source"], "boss blind gate drifted"
    assert shape["boss_school_comes_from_resolver"], "boss school resolution drifted"
    assert shape["boss_lethal_branch_stores_source"], "boss kill attribution drifted"
    cases = fixture["cases"]
    boss_types = {row["boss_type"] for row in cases}
    assert fixture["boss_type_count"] == 216 and len(boss_types) == 216
    assert fixture["case_count"] == len(cases) == 864
    assert all(sum(row["boss_type"] == boss for row in cases) == 4 for boss in boss_types)
    cooldown = fixture["source"]["bash_cooldown"]
    blind_gap = 0
    armor_gap = 0
    for row in cases:
        expected = row["expected"]
        native_old = row["native_old"]
        # No other on-hit arm is equipped, so nobody else is ever touched.
        assert expected["bystander_hits"] == native_old["bystander_hits"] == []
        if row["scenario"] == CONTROL_SCENARIO:
            assert expected == native_old, "control row must not diverge"
            assert expected["boss_hp_loss"] == 0 and expected["bash_cd_after"] == COOLDOWN_LEFT
            continue
        assert expected["bash_cd_after"] == native_old["bash_cd_after"] == cooldown
        if row["scenario"] == "bash_blind_owner_still_lands":
            assert expected["boss_hp_loss"] > 0, "source blind gate needs a source"
            assert native_old["boss_hp_loss"] == 0, "pre-9f native dropped the bash"
            blind_gap += 1
        if row["scenario"] == "bash_school_vs_boss_armor":
            assert expected["boss_hp_loss"] >= native_old["boss_hp_loss"]
            if expected["boss_hp_loss"] != native_old["boss_hp_loss"]:
                armor_gap += 1
        if row["scenario"] == "bash_lethal_without_kill_credit":
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
        print(f"wrote {len(fixture['cases'])} bash damage cases to {FIXTURE}")
    else:
        print(
            "bash damage oracle self-test passed: "
            f"{len(fixture['cases'])} cases across {fixture['boss_type_count']} bosses"
        )


if __name__ == "__main__":
    main()
