"""9g: source oracle for the on-hit magic arms on the active boss.

`HeroItemInventory._on_hit_common` lands four on-hit arms with a
three-positional `take_damage` call that carries the magic `damage_type` but
never passes `source=`:

    u.take_damage(chain["damage"], h.team, "magic")        # hero_items.py:2568
    target.take_damage(b["damage"], h.team, "magic")       # hero_items.py:2589
    u.take_damage(dmg, h.team, "magic")                    # hero_items.py:2633
    target.take_damage(bonus, h.team, "magic")             # hero_items.py:2648

When the victim is `game.active_boss` that reaches `Boss.take_damage`
(`bosses/base_boss.py:5978`) as `damage_type='magic'`, `source=None`,
`school=None`, so

* the Solar Brand blind block is skipped (it needs `damage_type == 'normal'`
  **and** `source is not None`): a blinded owner still lands the proc;
* `resolve_damage_school('magic', None, None)` returns `None`
  (`_entity.py:106-130`), so no school mitigation applies - neither boss magic
  resist nor armor;
* a lethal proc stores `self._killed_by = None`, so `Game._process_boss_kill`
  (`_core.py:2516-2545`) awards neither `kills` nor the mini/true boss counter.

Layer 9e/9f closed the two-argument arms (cleave splash, Abyss Breaker Bash).
The native bus still delivered these four arms as
`effects.deal_damage(id, hero_team, amount, "magic")`, i.e. `damage_type`
"normal" with the dealing hero as `source`, so the blind gate swallowed the hit
and `school="magic"` cut it by boss magic resist. Each row therefore carries
`expected` (source arguments) and `native_old` (the pre-9g native arguments).

Four scenarios per arm per boss type (216 bosses x 4 arms x 4 scenarios = 3456
cases): the school/resist gap, a fully blinded owner, a lethal proc, and one
arm-specific control that must stay identical in both columns (chain and
Polycephaly move the boss outside the radius, Piercing Bash holds its internal
cooldown, Empower Strike holds a pending charge). `--self-test` skips the
fixture; `--write` is the only fixture writer.
"""
import argparse
import ast
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_item_source_oracle import (  # noqa: E402
    _install_effect_stubs,
    inventory_type,
    source_namespace as item_source_namespace,
)
from boss_ability_source_oracle import SOURCE_STATS  # noqa: E402
from boss_item_cleave_chain_source_oracle import (  # noqa: E402
    _AlwaysRandom,
    _compact,
    _DummyOwner,
    _DummyUnit,
    _method_node,
    _method_text,
)
from boss_kill_credit_source_oracle import (  # noqa: E402
    core_boss_class,
    core_namespace,
    credit_game,
    game_class,
)
from check_source_contract import source_lanes  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures/boss_item_magic_damage_source.json"

# Source teams are the strings "blue"/"red"; `Game._process_boss_kill` compares
# `killer.team != "blue"` literally, so the oracle keeps the source types.
BLUE = "blue"
RED = "red"
MAIN_TARGET_ID = 10
REGULAR_UNIT_ID = 11
BOSS_ID = 500
OWNER_ID = 7
BASIC_DAMAGE = 50
BLIND_TICKS = 90

# `Boss.take_damage(damage, from_team, damage_type='normal', source=None,
# school=None)` is the only signature the arms above reach, so the source column
# is "three positional arguments and nothing else".
SOURCE_ARG_COUNT = 3

# arm -> catalog payload + the call shape the AST must still prove.
ARMS = (
    {
        "name": "chain",
        "item": "fenrir_chain",
        "take_damage_first_arg": "chain['damage']",
        "third_arg": "'magic'",
        "role": "secondary",
        "control": "chain_boss_outside_radius_control",
    },
    {
        "name": "pierce_bash",
        "item": "sundering_cudgel",
        "take_damage_first_arg": "b['damage']",
        "third_arg": "'magic'",
        "role": "main",
        "control": "pierce_bash_internal_cooldown_control",
    },
    {
        "name": "polycephaly",
        "item": "basilisk_breath",
        "take_damage_first_arg": "dmg",
        "third_arg": "'magic'",
        "role": "secondary",
        "control": "polycephaly_boss_outside_radius_control",
    },
    {
        "name": "empower",
        "item": "runic_gavel",
        "take_damage_first_arg": "bonus",
        "third_arg": "'magic'",
        "role": "main",
        "control": "empower_strike_charge_pending_control",
    },
)
ARM_BY_NAME = {arm["name"]: arm for arm in ARMS}
SCENARIO_SUFFIXES = (
    "magic_arm_vs_boss_resist",
    "blind_owner_still_lands",
    "lethal_without_kill_credit",
)
CONTROL_BY_ARM = {arm["name"]: arm["control"] for arm in ARMS}
BLIND_SCENARIO_SUFFIX = "blind_owner_still_lands"
LETHAL_SCENARIO_SUFFIX = "lethal_without_kill_credit"
RESIST_SCENARIO_SUFFIX = "magic_arm_vs_boss_resist"

# World layout per arm, replayed verbatim by the native suite. `main` decides
# whether the boss is the main target of the arm or a secondary victim on the
# on-hit candidate list that the source appends last (`_all_units.append(
# gi.active_boss)`).
LAYOUT = {
    "chain": {
        "main": "minion",
        "boss_x": 200.0,
        "regular_x": 100.0,
        "control_boss_x": 400.0,
    },
    "pierce_bash": {
        "main": "boss",
        "boss_x": 0.0,
        "regular_x": 500.0,
        "control_gate": 5,
    },
    "polycephaly": {
        "main": "minion",
        "boss_x": 120.0,
        "regular_x": 1500.0,
        "control_boss_x": 900.0,
    },
    "empower": {
        "main": "boss",
        "boss_x": 0.0,
        "regular_x": 500.0,
        "control_gate": 540,
    },
}
# Internal gate each arm exposes; "none" means the arm has no internal timer
# (Polycephaly is chance-gated only, arc chain has no on-hit cooldown).
GATE_FIELDS = {
    "chain": "chains_cd",
    "pierce_bash": "pierce_bash_cd",
    "polycephaly": "none",
    "empower": "empower_charge",
}


def _boss_method(name):
    tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    boss = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss"
    )
    return next(
        node for node in boss.body if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _resolver_text():
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    node = next(
        item
        for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name == "resolve_damage_school"
    )
    return ast.unparse(node)


def _arm_call_shape(first_arg):
    """Shape of the `take_damage` call whose first argument is `first_arg`."""
    common = ast.parse(_method_text("HeroItemInventory", "_on_hit_common", "hero_items.py"))
    for node in ast.walk(common):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "take_damage"
            and node.args
            and ast.unparse(node.args[0]) == first_arg
        ):
            return {
                "positional_args": len(node.args),
                "keywords": sorted(keyword.arg for keyword in node.keywords),
                "third_arg": ast.unparse(node.args[2]) if len(node.args) > 2 else "",
            }
    return {}


def _source_shape():
    common = _method_text("HeroItemInventory", "_on_hit_common", "hero_items.py")
    take_damage = ast.unparse(_boss_method("take_damage"))
    resolver = _resolver_text()
    shape = {}
    for arm in ARMS:
        call = _arm_call_shape(arm["take_damage_first_arg"])
        prefix = "{}_take_damage".format(arm["name"])
        shape[prefix + "_positional_args"] = call.get("positional_args", -1)
        shape[prefix + "_keywords"] = call.get("keywords", [])
        shape[prefix + "_third_arg"] = call.get("third_arg", "")
    shape["boss_blind_block_requires_source"] = _compact(
        "if damage_type == 'normal' and damage > 0 and (source is not None):"
    ) in _compact(take_damage)
    shape["boss_school_comes_from_resolver"] = (
        "resolve_damage_school(damage_type, source, school)" in take_damage
    )
    compact_resolver = _compact(resolver)
    shape["resolver_returns_none_without_school_or_source"] = (
        _compact("if source is None:") in compact_resolver
        and _compact("target_hero = target_is_hero if target_is_hero is not None else False")
        in compact_resolver
        and _compact("return None") in compact_resolver
    )
    shape["boss_lethal_branch_stores_source"] = "self._killed_by = source" in take_damage
    onhit = _compact(
        _method_text("HeroItemInventory", "on_basic_attack_hit", "hero_items.py")
    )
    shape["arms_are_reached_from_basic_attack"] = (
        _compact("self._on_hit_common(target, damage, all_units)") in onhit
    )
    shape["chain_uses_the_chain_getter"] = (
        _compact("chain = self.get_on_attack_chain() or {}") in _compact(common)
    )
    shape["pierce_uses_the_cudgel_bash_block"] = (
        _compact("pb = self.get_bash()") in _compact(common)
        or _compact("ITEM_CATALOG['sundering_cudgel']['bash']") in _compact(common)
    )
    return shape


def _build_runtime():
    item_env = item_source_namespace(with_inventory=True, with_functions=True)
    _install_effect_stubs(item_env)
    item_env["math"] = math
    item_env["random"] = _AlwaysRandom()
    catalog = item_env["ITEM_CATALOG"]
    inv_cls = inventory_type(item_env)
    item_module = ast.Module(
        body=[
            _method_node("HeroItemInventory", "on_basic_attack_hit", "hero_items.py"),
            _method_node("HeroItemInventory", "_on_hit_common", "hero_items.py"),
            _method_node("HeroItemInventory", "get_on_attack_chain", "hero_items.py"),
            _method_node("HeroItemInventory", "get_bash", "hero_items.py"),
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(item_module)
    exec(compile(item_module, "_hero_item_magic_damage_source", "exec"), item_env)
    inv_cls.on_basic_attack_hit = item_env["on_basic_attack_hit"]
    inv_cls._on_hit_common = item_env["_on_hit_common"]
    inv_cls.get_on_attack_chain = item_env["get_on_attack_chain"]
    inv_cls.get_bash = item_env["get_bash"]

    boss_cls = core_boss_class(core_namespace())
    return catalog, inv_cls, boss_cls


def _build_source_runtime():
    catalog, inventory_class, boss_class = _build_runtime()
    lane = source_lanes()["mid"]
    return catalog, inventory_class, boss_class, game_class(), lane


def _scenario_names(arm):
    return tuple(
        "{}_{}".format(arm, suffix) for suffix in SCENARIO_SUFFIXES
    ) + (CONTROL_BY_ARM[arm],)


def _layout_for(arm, scenario):
    layout = dict(LAYOUT[arm])
    if scenario == CONTROL_BY_ARM[arm]:
        if "control_boss_x" in layout:
            layout["boss_x"] = layout["control_boss_x"]
        layout["control"] = True
    else:
        layout["control"] = False
    return layout


def _prepare_boss(boss_class, boss_type, lane, layout, scenario):
    boss = boss_class(boss_type, lane)
    boss.id = BOSS_ID
    boss.team = RED
    boss.alive = True
    boss.defeated = False
    boss.x = float(layout["boss_x"])
    boss.y = 0.0
    boss._killed_by = None
    boss.lane = lane
    boss.hp = 1 if scenario.endswith(LETHAL_SCENARIO_SUFFIX) else boss.max_hp
    return boss


def _prepare_owner(inventory_class, target, arm, scenario):
    owner = _DummyOwner(target)
    owner.name = "Kaizen"
    # The shared dummy carries the native int teams; the boss-kill pass compares
    # `killer.team != "blue"` literally, so the source column needs the strings.
    owner.team = BLUE
    # `Game._killer_is_hero` requires the source `hero_type` + `skills` pair.
    owner.hero_type = "kaizen"
    owner.skills = ["q", "w", "e", "r"]
    owner.is_melee_hero = arm != "polycephaly"
    owner.range = 70 if owner.is_melee_hero else 130
    owner.blind_timer = (
        BLIND_TICKS if scenario.endswith(BLIND_SCENARIO_SUFFIX) else 0
    )
    owner.blind_amount = 1.0 if owner.blind_timer else 0.0
    inventory = inventory_class(owner)
    owner.items = inventory
    assert inventory.add(ARM_BY_NAME[arm]["item"]), "cannot equip {}".format(arm)
    if GATE_FIELDS[arm] != "none":
        # Normal rows start from a ready gate: Piercing Bash off cooldown,
        # Empower Strike fully charged. The control row holds the gate busy.
        setattr(
            inventory,
            GATE_FIELDS[arm],
            int(LAYOUT[arm].get("control_gate", 0)) if _is_control(arm, scenario) else 0,
        )
    return owner, inventory


def _is_control(arm, scenario):
    return scenario == CONTROL_BY_ARM[arm]


def _run_case(catalog, inventory_class, boss_class, source_game_class, lane,
              boss_type, arm, scenario, native_old):
    layout = _layout_for(arm, scenario)
    main_is_boss = layout["main"] == "boss"
    boss = _prepare_boss(boss_class, boss_type, lane, layout, scenario)
    target = boss if main_is_boss else _DummyUnit(MAIN_TARGET_ID, RED, 0.0)
    owner, inventory = _prepare_owner(inventory_class, target, arm, scenario)
    if main_is_boss:
        # The arm hits the hero's main target; the regular unit is a bystander
        # that must stay untouched in both columns.
        regular = _DummyUnit(REGULAR_UNIT_ID, RED, float(layout["regular_x"]))
    else:
        regular = _DummyUnit(REGULAR_UNIT_ID, RED, float(layout["regular_x"]))
    # Source on-hit candidate order: minions, heroes, then the living boss.
    all_units = [regular, owner, boss]

    source_take_damage = boss.take_damage
    landed = []

    def recording_take_damage(damage, from_team=None, damage_type="normal",
                              source=None, school=None):
        # Observe the arguments the arm actually sent. The source column keeps
        # the source call untouched; the native_old column substitutes the pre-9g
        # native arguments (`deal_damage` -> `_deliver_hit` default "normal"
        # damage_type with the dealing hero as source and the declared magic
        # school). The source leaves `school=None`; `resolve_damage_school`
        # returns `None` there, which the native plan spells as "neutral".
        hp_before_call = float(boss.hp)
        if native_old:
            result = source_take_damage(damage, from_team, "normal", source=owner,
                                        school="magic")
            observed = ("normal", "magic")
        else:
            result = source_take_damage(damage, from_team, damage_type,
                                        source=source, school=school)
            observed = (damage_type, school if school else "neutral")
        if float(boss.hp) < hp_before_call:
            landed.append(observed)
        return result

    boss.take_damage = recording_take_damage

    hp_before = float(boss.hp)
    inventory.on_basic_attack_hit(target, BASIC_DAMAGE, all_units)
    hp_loss = int(round(hp_before - float(boss.hp)))

    game = credit_game(source_game_class)
    game._process_boss_kill(boss)
    gate = GATE_FIELDS[arm]
    return {
        "boss_hp_loss": hp_loss,
        "boss_alive": bool(boss.alive),
        "owner_kills": int(owner.kills),
        "boss_counter": int(game.miniboss_kill_count) + int(game.trueboss_kill_count),
        "regular_hits": [int(hit) for hit in regular.hits],
        "gate_after": 0 if gate == "none" else int(getattr(inventory, gate)),
        "boss_schools": [entry[1] for entry in landed],
        "boss_damage_types": [entry[0] for entry in landed],
    }


def _arm_true_strike(catalog, inventory_class, arm):
    """Does the arm's own item grant true strike (`HeroItemInventory` gate)?"""
    owner = _DummyOwner(None)
    owner.team = BLUE
    inventory = inventory_class(owner)
    owner.items = inventory
    assert inventory.add(ARM_BY_NAME[arm]["item"]), "cannot equip {}".format(arm)
    return bool(inventory.has_true_strike())


def _arm_payload(catalog, arm):
    if arm == "chain":
        chain = catalog["fenrir_chain"]["on_attack"]
        return {
            "chance": float(chain["chance"]),
            "damage": int(chain["damage"]),
            "targets": int(chain["targets"]),
            "radius": float(chain["radius"]),
        }
    if arm == "pierce_bash":
        bash = catalog["sundering_cudgel"]["bash"]
        return {
            "chance": float(bash["chance"]),
            "damage": int(bash["damage"]),
            "stun": int(bash["stun"]),
            "cooldown": int(bash["cooldown"]),
        }
    if arm == "polycephaly":
        multi = catalog["basilisk_breath"]["multishot"]
        return {
            "chance": float(multi["chance"]),
            "targets": int(multi["targets"]),
            "radius": float(multi["radius"]),
            "damage_pct": float(multi["damage_pct"]),
            "damage": int(BASIC_DAMAGE * float(multi["damage_pct"])),
        }
    passive = catalog["runic_gavel"]["passive"]
    return {
        "charge_time": int(passive["charge_time"]),
        "damage": int(passive["damage"]),
    }


def source_fixture():
    catalog, inventory_class, boss_class, source_game_class, lane = _build_source_runtime()
    cases = []
    for boss_type in sorted(SOURCE_STATS):
        for arm in ARM_BY_NAME:
            for scenario in _scenario_names(arm):
                expected = _run_case(
                    catalog, inventory_class, boss_class, source_game_class, lane,
                    boss_type, arm, scenario, native_old=False,
                )
                native_old = _run_case(
                    catalog, inventory_class, boss_class, source_game_class, lane,
                    boss_type, arm, scenario, native_old=True,
                )
                cases.append(
                    {
                        "boss_type": boss_type,
                        "arm": arm,
                        "scenario": scenario,
                        "owner_blind": scenario.endswith(BLIND_SCENARIO_SUFFIX),
                        "boss_hp_before": 1
                        if scenario.endswith(LETHAL_SCENARIO_SUFFIX)
                        else int(boss_class(boss_type, lane).max_hp),
                        "expected": expected,
                        "native_old": native_old,
                    }
                )
    fixture = {
        "source": {
            "ast_shape": _source_shape(),
            "arms": {
                arm: {
                    "item": ARM_BY_NAME[arm]["item"],
                    "role": ARM_BY_NAME[arm]["role"],
                    "gate_field": GATE_FIELDS[arm],
                    "control_scenario": CONTROL_BY_ARM[arm],
                    "payload": _arm_payload(catalog, arm),
                }
                for arm in ARM_BY_NAME
            },
            "scenario_names": {
                arm: list(_scenario_names(arm)) for arm in ARM_BY_NAME
            },
            # Sundering Cudgel carries `true_strike` in `ITEM_CATALOG`, so a
            # blinded owner still pierces the Solar Brand gate in BOTH columns
            # (`Boss.take_damage` reads `source.items.has_true_strike()`).
            "owner_true_strike": {
                arm: _arm_true_strike(catalog, inventory_class, arm)
                for arm in ARM_BY_NAME
            },
            "basic_damage": BASIC_DAMAGE,
            "blind_ticks": BLIND_TICKS,
            "owner_team": BLUE,
            "boss_team": RED,
            "main_target_id": MAIN_TARGET_ID,
            "regular_unit_id": REGULAR_UNIT_ID,
            "boss_id": BOSS_ID,
            "layout": {
                arm: {
                    key: float(value) if isinstance(value, float) else value
                    for key, value in LAYOUT[arm].items()
                }
                for arm in LAYOUT
            },
        },
        "boss_type_count": len(SOURCE_STATS),
        "case_count": len(cases),
        "cases": cases,
    }
    _assert_fixture_logic(fixture)
    return fixture


def _assert_fixture_logic(fixture):
    shape = fixture["source"]["ast_shape"]
    for arm in ARM_BY_NAME:
        assert shape["{}_take_damage_positional_args".format(arm)] == SOURCE_ARG_COUNT, (
            "{} call shape drifted".format(arm)
        )
        assert shape["{}_take_damage_keywords".format(arm)] == [], (
            "{} call gained keywords".format(arm)
        )
        assert shape["{}_take_damage_third_arg".format(arm)] == "'magic'", (
            "{} third argument drifted".format(arm)
        )
    assert shape["boss_blind_block_requires_source"], "boss blind gate drifted"
    assert shape["boss_school_comes_from_resolver"], "boss school resolution drifted"
    assert shape["resolver_returns_none_without_school_or_source"], "resolver drifted"
    assert shape["boss_lethal_branch_stores_source"], "boss kill attribution drifted"
    assert shape["arms_are_reached_from_basic_attack"], "on-hit entry point drifted"
    assert shape["chain_uses_the_chain_getter"], "arc chain getter drifted"
    assert shape["pierce_uses_the_cudgel_bash_block"], "cudgel bash block drifted"

    cases = fixture["cases"]
    boss_types = {row["boss_type"] for row in cases}
    assert fixture["boss_type_count"] == 216 and len(boss_types) == 216
    assert fixture["case_count"] == len(cases) == 3456
    assert all(sum(row["boss_type"] == boss for row in cases) == 16 for boss in boss_types)
    resist_gap = 0
    resist_gap_by_arm = {arm: 0 for arm in ARM_BY_NAME}
    blind_gap = 0
    lethal_gap = 0
    for row in cases:
        expected = row["expected"]
        native_old = row["native_old"]
        arm = row["arm"]
        scenario = row["scenario"]
        assert expected["regular_hits"] == native_old["regular_hits"], (
            "the regular-unit arm must not change for {}".format(scenario)
        )
        if scenario == CONTROL_BY_ARM[arm]:
            assert expected == native_old, "control row must not diverge"
            assert expected["boss_hp_loss"] == 0 and expected["boss_alive"]
            assert expected["boss_schools"] == [] and expected["boss_damage_types"] == []
            continue
        # Every proccing row records the call shape the arm sent to the boss:
        # the source omits `source`/`school` and keeps `damage_type="magic"`,
        # while the pre-9g native bus sent "normal" with the owner as source and
        # the declared magic school. That pair makes the divergence measurable
        # even when the magic resist rounds away on the smallest payload.
        assert expected["boss_hp_loss"] > 0, "the source arm must land on the boss"
        assert expected["boss_schools"] == ["neutral"], "source school is resolved to None"
        assert expected["boss_damage_types"] == ["magic"]
        # The pre-9g native arm carried "normal" with the declared magic school,
        # unless the Solar Brand gate dropped the hit entirely (empty record).
        native_dropped = native_old["boss_schools"] == []
        assert native_old["boss_damage_types"] == ([] if native_dropped else ["normal"])
        assert native_old["boss_schools"] == ([] if native_dropped else ["magic"])
        assert expected != native_old, "proccing rows must diverge"
        assert expected["gate_after"] == native_old["gate_after"]
        if scenario.endswith(RESIST_SCENARIO_SUFFIX):
            assert expected["boss_hp_loss"] >= native_old["boss_hp_loss"]
            if expected["boss_hp_loss"] != native_old["boss_hp_loss"]:
                resist_gap += 1
                resist_gap_by_arm[arm] += 1
        if scenario.endswith(BLIND_SCENARIO_SUFFIX):
            assert expected["boss_hp_loss"] > 0, "source magic type ignores blind"
            if fixture["source"]["owner_true_strike"][arm]:
                # Sundering Cudgel's true strike pierces the Solar Brand gate in
                # both columns, so only the school gap separates them.
                assert native_old["boss_hp_loss"] > 0, "true strike must pierce blind"
            else:
                assert native_old["boss_hp_loss"] == 0, "pre-9g native dropped it"
                blind_gap += 1
        if scenario.endswith(LETHAL_SCENARIO_SUFFIX):
            assert not expected["boss_alive"] and not native_old["boss_alive"]
            assert expected["owner_kills"] == 0 and expected["boss_counter"] == 0
            assert native_old["owner_kills"] == 1 and native_old["boss_counter"] == 1
            lethal_gap += 1
    # Small magic resist can round away on the smallest payload, so the gap is
    # recorded per arm instead of once per boss type.
    assert resist_gap > 0, "the magic-resist gap must be recorded"
    assert all(count > 0 for count in resist_gap_by_arm.values()), (
        "every arm records at least one magic-resist gap"
    )
    assert blind_gap == 216 * 3, "every non-true-strike arm records the blind gap"
    assert lethal_gap == 216 * 4, "every boss type records the kill-credit gap"
    for arm in ARM_BY_NAME:
        rows = [row for row in cases if row["arm"] == arm]
        assert len(rows) == 216 * 4, "{} rows drifted".format(arm)
        assert {row["scenario"] for row in rows} == set(_scenario_names(arm))


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    fixture = source_fixture()
    if args.write:
        FIXTURE.write_text(
            json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("wrote {} magic damage cases to {}".format(len(fixture["cases"]), FIXTURE))
    else:
        print(
            "magic damage oracle self-test passed: "
            "{} cases across {} bosses".format(
                len(fixture["cases"]), fixture["boss_type_count"]
            )
        )


if __name__ == "__main__":
    main()
