"""9d: source oracle for whether a Miasma tick can credit the boss killer.

The read-only source path executes HeroItemInventory.on_basic_attack_hit plus
_apply_miasma/_tick_miasma and the real Boss.take_damage and Game kill-credit
methods. `_tick_miasma` calls `take_damage(..., team, "magic")` without `source=`,
so a lethal tick must leave Boss._killed_by unset. `native_old` models the
post-9c native bus, which forwarded the live Miasma owner as BossState's source.

Four deterministic schedules are generated for each of the 216 boss types:
blue-owner lethal poison, red-owner lethal poison, nonlethal poison followed by
a lethal hero strike, and a nonlethal poison control. `--self-test` exercises
the source oracle without writing a fixture; `--write` is the only fixture
writer.
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
    _build_runtime,
    _func_node,
)
from boss_kill_credit_source_oracle import (  # noqa: E402
    core_boss_class,
    core_namespace,
    credit_game,
    game_class,
)
from bosses.boss_data import get_all_boss_types  # noqa: E402
from check_source_contract import source_lanes  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures/boss_miasma_kill_credit_source.json"
BASIC_DAMAGE = 50
TICK_FRAMES = 30

SCENARIOS = (
    {
        "name": "miasma_lethal_blue_owner",
        "owner_team": "blue",
        "boss_team": "red",
        "mode": "miasma_lethal",
    },
    {
        "name": "miasma_lethal_red_owner",
        "owner_team": "red",
        "boss_team": "blue",
        "mode": "miasma_lethal",
    },
    {
        "name": "miasma_nonlethal_then_hero_lethal",
        "owner_team": "blue",
        "boss_team": "red",
        "mode": "hero_followup",
    },
    {
        "name": "miasma_nonlethal_only",
        "owner_team": "blue",
        "boss_team": "red",
        "mode": "nonlethal",
    },
)
GAP_SCENARIOS = {"miasma_lethal_blue_owner", "miasma_lethal_red_owner"}


def _boss_method(name):
    tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    boss = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss")
    return next(node for node in boss.body if isinstance(node, ast.FunctionDef) and node.name == name)


def _game_method(name):
    tree = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    game = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Game")
    return next(node for node in game.body if isinstance(node, ast.FunctionDef) and node.name == name)


def _assigns_killed_by_source(node):
    for child in ast.walk(node):
        if not isinstance(child, ast.Assign) or not isinstance(child.value, ast.Name):
            continue
        if child.value.id != "source":
            continue
        if any(
            isinstance(target, ast.Attribute)
            and ast.unparse(target) == "self._killed_by"
            for target in child.targets
        ):
            return True
    return False


def _source_shape():
    tick = _func_node("_tick_miasma", "hero_items.py")
    tick_calls_magic_without_source = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "take_damage"
        and len(node.args) == 3
        and isinstance(node.args[2], ast.Constant)
        and node.args[2].value == "magic"
        and not any(keyword.arg == "source" for keyword in node.keywords)
        for node in ast.walk(tick)
    )
    boss_take_damage = _boss_method("take_damage")
    lethal_source_assignment = any(
        isinstance(node, ast.If)
        and ast.unparse(node.test) == "self.hp <= 0"
        and _assigns_killed_by_source(ast.Module(body=node.body, type_ignores=[]))
        for node in ast.walk(boss_take_damage)
    )
    game_kill_text = ast.unparse(_game_method("_process_boss_kill"))
    return {
        "miasma_tick_calls_magic_without_source": tick_calls_magic_without_source,
        "boss_stores_source_only_in_lethal_branch": lethal_source_assignment,
        "boss_kill_pass_reads_killed_by": "_killed_by" in game_kill_text and "getattr(boss" in game_kill_text,
        "boss_kill_pass_requires_hero": "_killer_is_hero" in game_kill_text,
    }


def _build_source_runtime():
    catalog, inventory_class, _unused_boss_class = _build_runtime()
    item_env = inventory_class._on_hit_common.__globals__
    helpers = ast.Module(
        body=[_func_node("_apply_miasma", "hero_items.py"), _func_node("_tick_miasma", "hero_items.py")],
        type_ignores=[],
    )
    ast.fix_missing_locations(helpers)
    exec(compile(helpers, "<source-miasma-kill-credit>", "exec"), item_env)  # noqa: S102
    boss_class = core_boss_class(core_namespace())
    lane = source_lanes()["mid"]
    return catalog, inventory_class, item_env, boss_class, game_class(), lane


def _run_case(catalog, inventory_class, item_env, boss_class, source_game_class, lane,
              boss_type, scenario, native_old):
    item_env["_MIASMA"] = {}
    boss = boss_class(boss_type, lane)
    boss.team = scenario["boss_team"]
    boss.alive = True
    boss.defeated = False

    owner = _DummyOwner(boss)
    owner.id = 7
    owner.team = scenario["owner_team"]
    owner.kills = 0
    owner.name = "Kaizen"
    owner.hero_type = "kaizen"
    owner.skills = ["q", "w", "e", "r"]
    owner.blind_timer = 0
    owner.blind_amount = 0.0
    inventory = inventory_class(owner)
    owner.items = inventory
    assert inventory.add("basilisk_breath"), "cannot equip Basilisk Breath"
    inventory.on_basic_attack_hit(boss, BASIC_DAMAGE, [boss])

    tracker = item_env["_MIASMA"].get(id(boss))
    assert tracker is not None, "real source on-hit hook did not apply Miasma"
    miasma_damage = int(tracker["damage"])
    boss_hp_before_tick = 1 if scenario["mode"] == "miasma_lethal" else miasma_damage + 1
    boss.hp = float(boss_hp_before_tick)

    if native_old:
        source_take_damage = boss.take_damage

        def attributed_tick(damage, from_team=None, damage_type="normal", source=None, school=None):
            return source_take_damage(
                damage, from_team, damage_type, source=owner, school=school
            )

        boss.take_damage = attributed_tick

    hp_before = float(boss.hp)
    tick_damage = 0
    for _frame in range(TICK_FRAMES):
        previous_hp = float(boss.hp)
        item_env["_tick_miasma"](1)
        if float(boss.hp) != previous_hp:
            tick_damage = miasma_damage
    hp_loss = int(round(hp_before - float(boss.hp)))
    boss_alive_after_tick = bool(boss.alive)

    if scenario["mode"] == "hero_followup":
        boss.hp = 1.0
        boss.take_damage(BASIC_DAMAGE, owner.team, "normal", source=owner, school="physical")

    game = credit_game(source_game_class)
    game._process_boss_kill(boss)
    return {
        "miasma_damage": miasma_damage,
        "tick_damage": tick_damage,
        "boss_hp_loss_from_tick": hp_loss,
        "boss_alive_after_tick": boss_alive_after_tick,
        "boss_alive_after_schedule": bool(boss.alive),
        "killed_by_owner": getattr(boss, "_killed_by", None) is owner,
        "owner_kills": int(owner.kills),
        "miniboss_kill_count": int(game.miniboss_kill_count),
        "trueboss_kill_count": int(game.trueboss_kill_count),
    }


def source_fixture():
    catalog, inventory_class, item_env, boss_class, source_game_class, lane = _build_source_runtime()
    cases = []
    for boss_type in sorted(get_all_boss_types()):
        for scenario in SCENARIOS:
            expected = _run_case(
                catalog, inventory_class, item_env, boss_class, source_game_class, lane,
                boss_type, scenario, native_old=False,
            )
            native_old = _run_case(
                catalog, inventory_class, item_env, boss_class, source_game_class, lane,
                boss_type, scenario, native_old=True,
            )
            cases.append(
                {
                    "boss_type": boss_type,
                    "scenario": scenario["name"],
                    "owner_team": scenario["owner_team"],
                    "boss_team": scenario["boss_team"],
                    "mode": scenario["mode"],
                    "boss_hp_before_tick": expected["miasma_damage"] + 1
                    if scenario["mode"] != "miasma_lethal"
                    else 1,
                    "expected": expected,
                    "native_old": native_old,
                }
            )
    fixture = {
        "source": {
            "ast_shape": _source_shape(),
            "miasma_damage_type": "magic",
            "miasma_source_argument": None,
            "first_tick_frames": TICK_FRAMES,
            "basic_attack_damage": BASIC_DAMAGE,
            "scenario_names": [scenario["name"] for scenario in SCENARIOS],
        },
        "boss_type_count": len(get_all_boss_types()),
        "case_count": len(cases),
        "cases": cases,
    }
    _assert_fixture_logic(fixture)
    return fixture


def _assert_fixture_logic(fixture):
    expected_shape = {
        "miasma_tick_calls_magic_without_source": True,
        "boss_stores_source_only_in_lethal_branch": True,
        "boss_kill_pass_reads_killed_by": True,
        "boss_kill_pass_requires_hero": True,
    }
    cases = fixture["cases"]
    boss_types = {row["boss_type"] for row in cases}
    assert fixture["source"]["ast_shape"] == expected_shape, "Miasma/boss kill source AST drifted"
    assert fixture["boss_type_count"] == 216 and len(boss_types) == 216
    assert fixture["case_count"] == len(cases) == 864
    assert all(sum(row["boss_type"] == boss_type for row in cases) == 4 for boss_type in boss_types)
    for row in cases:
        expected = row["expected"]
        native_old = row["native_old"]
        assert "expected" in row and "native_old" in row
        assert expected["miasma_damage"] > 0
        assert expected["tick_damage"] == expected["miasma_damage"]
        assert native_old["tick_damage"] == expected["tick_damage"]
        if row["scenario"] in GAP_SCENARIOS:
            assert not expected["boss_alive_after_schedule"]
            assert expected["owner_kills"] == 0 and not expected["killed_by_owner"]
            assert native_old["owner_kills"] == 1 and native_old["killed_by_owner"]
            expected_boss_kills = expected["miniboss_kill_count"] + expected["trueboss_kill_count"]
            native_boss_kills = native_old["miniboss_kill_count"] + native_old["trueboss_kill_count"]
            assert expected_boss_kills == 0
            assert native_boss_kills == (1 if row["owner_team"] == "blue" else 0)
        else:
            assert expected == native_old, f"counterfactual should match control: {row['scenario']}"
        if row["scenario"] == "miasma_nonlethal_only":
            assert expected["boss_alive_after_schedule"] and expected["owner_kills"] == 0
        if row["scenario"] == "miasma_nonlethal_then_hero_lethal":
            assert expected["boss_alive_after_tick"] and not expected["boss_alive_after_schedule"]
            assert expected["owner_kills"] == 1 and expected["killed_by_owner"]


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    fixture = source_fixture()
    if args.write:
        FIXTURE.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {len(fixture['cases'])} Miasma boss kill-credit cases to {FIXTURE}")
    else:
        print(
            "Miasma kill-credit oracle self-test passed: "
            f"{len(fixture['cases'])} cases across {fixture['boss_type_count']} bosses"
        )


if __name__ == "__main__":
    main()
