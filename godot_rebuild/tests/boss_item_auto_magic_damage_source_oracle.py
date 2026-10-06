"""9h: source oracle for the auto/active magic arms on the active boss.

`HeroItemInventory.update` lands six auto-trigger arms with a
three-positional `take_damage` call that carries the magic `damage_type` but
never passes `source=`:

    e.take_damage(act["damage"], h.team, "magic")      # hero_items.py:2209 Fenrir
    e.take_damage(act["damage"], h.team, "magic")      # hero_items.py:2257 Thunder
    e.take_damage(act["damage"], h.team, "magic")      # hero_items.py:2286 Everfrost
    e.take_damage(act["damage"], h.team, "magic")      # hero_items.py:2329 Searbrand
    e.take_damage(act["damage"], h.team, "magic")      # hero_items.py:2358 Astral
    tgt.take_damage(act["damage"], h.team, "magic")    # hero_items.py:2377 Fulgur

Each call is wrapped in `try: ... except TypeError:` with a two-argument
fallback for entities that do not accept the third argument. All live combat
targets (Minion/Tower/Castle/Hero/Boss) accept `damage_type`, so the fallback
never fires for the boss; it is asserted in the AST shape but not executed.

When the victim is `game.active_boss` the try branch reaches
`Boss.take_damage` (`bosses/base_boss.py:5978`) as `damage_type='magic'`,
`source=None`, `school=None`, so

* the Solar Brand blind block is skipped (it needs `damage_type == 'normal'`
  **and** `source is not None`): a blinded owner still lands the proc;
* `resolve_damage_school('magic', None, None)` returns `None`
  (`_entity.py:106-130`), so no school mitigation applies - neither boss magic
  resist nor armor;
* a lethal proc stores `self._killed_by = None`, so `Game._process_boss_kill`
  (`_core.py:2516-2545`) awards neither `kills` nor the mini/true boss counter.

Layer 9g closed the four on-hit magic arms with the typed bus entry
`deal_damage_magic_sourceless`. The native bus still delivered these six arms
as `effects.deal_damage(id, hero_team, amount, "magic")`, i.e. `damage_type`
"normal" with the dealing hero as `source`, so the blind gate swallowed the hit
and `school="magic"` cut it by boss magic resist. Each row therefore carries
`expected` (source arguments) and `native_old` (the pre-9h native arguments).

The Razor Carapace reflect (`hero_items.py:2468`, via `notify_damage_taken`)
uses the same three-positional shape but a different bus
(`ReflectItemEffects`, which already sends `source_id=-1`); it keeps only the
school gap and is left for layer 9i so this oracle stays uniform.

Four scenarios per arm per boss type (216 bosses x 6 arms x 4 scenarios = 5184
cases): the school/resist gap, a fully blinded owner, a lethal proc, and one
arm-specific control that must stay identical in both columns (radius arms move
the boss outside the trigger radius while two minions keep the 2+ gate firing;
Fulgur retargets the owner's target onto a minion). `--self-test` skips the
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

FIXTURE = Path(__file__).parent / "fixtures/boss_item_auto_magic_damage_source.json"

# Source teams are the strings "blue"/"red"; `Game._process_boss_kill` compares
# `killer.team != "blue"` literally, so the oracle keeps the source types.
BLUE = "blue"
RED = "red"
EXTRA_ONE_ID = 11
EXTRA_TWO_ID = 12
BOSS_ID = 500
OWNER_ID = 7
OWNER_X = -40.0
BLIND_TICKS = 90

# `Boss.take_damage(damage, from_team, damage_type='normal', source=None,
# school=None)` is the only signature the arms above reach, so the source column
# is "three positional arguments and nothing else".
SOURCE_ARG_COUNT = 3

# arm -> catalog payload + the call shape the AST must still prove.
ARMS = (
    {
        "name": "fenrir",
        "item": "fenrir_chain",
        "role": "Bruiser",
        "gate_field": "chains_cd",
        "control": "fenrir_boss_outside_radius_control",
    },
    {
        "name": "thunder",
        "item": "thunder_coil",
        "role": "Bruiser",
        "gate_field": "static_tick",
        "control": "thunder_boss_outside_radius_control",
    },
    {
        "name": "everfrost",
        "item": "everfrost_guard",
        "role": "Bruiser",
        "gate_field": "arctic_cd",
        "control": "everfrost_boss_outside_radius_control",
    },
    {
        "name": "searbrand",
        "item": "searbrand",
        "role": "Bruiser",
        "gate_field": "searbrand_cd",
        "control": "searbrand_boss_outside_radius_control",
    },
    {
        "name": "astral",
        "item": "astral_codex",
        "role": "Mage",
        "gate_field": "arcane_cd",
        "control": "astral_boss_outside_radius_control",
    },
    {
        "name": "fulgur",
        "item": "fulgur_scepter",
        "role": "Mage",
        "gate_field": "fulgur_cd",
        "control": "fulgur_target_is_minion_control",
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

# World layout per arm, replayed verbatim by the native suite. Radius arms need
# two minions inside the trigger radius so the 2+ gate fires with or without
# the boss; the control row moves only the boss outside. Fulgur hits the
# owner's target only, so its control retargets onto a minion.
LAYOUT = {
    "fenrir": {
        "boss_x": 0.0,
        "extra_one_x": 20.0,
        "extra_two_x": 50.0,
        "control_boss_x": 400.0,
    },
    "thunder": {
        "boss_x": 0.0,
        "extra_one_x": 20.0,
        "extra_two_x": 50.0,
        "control_boss_x": 500.0,
    },
    "everfrost": {
        "boss_x": 0.0,
        "extra_one_x": 20.0,
        "extra_two_x": 50.0,
        "control_boss_x": 500.0,
    },
    "searbrand": {
        "boss_x": 0.0,
        "extra_one_x": 20.0,
        "extra_two_x": 50.0,
        "control_boss_x": 500.0,
    },
    "astral": {
        "boss_x": 0.0,
        "extra_one_x": 20.0,
        "extra_two_x": 50.0,
        "control_boss_x": 500.0,
    },
    "fulgur": {
        "boss_x": 0.0,
        "extra_one_x": 20.0,
        "extra_two_x": 50.0,
        "control_target": "minion",
    },
}
GATE_FIELDS = {arm["name"]: arm["gate_field"] for arm in ARMS}


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


def _arm_call_shape(item_id):
    """Shape of the `take_damage` call inside the `self.has(item_id)` block."""
    update_node = _method_node("HeroItemInventory", "update", "hero_items.py")
    for node in ast.walk(update_node):
        if not isinstance(node, ast.If):
            continue
        try:
            test_src = ast.unparse(node.test)
        except Exception:
            continue
        if 'self.has("{}")'.format(item_id) not in test_src and "self.has('{}')".format(
            item_id
        ) not in test_src:
            continue
        best = {}
        fallback = {}
        for inner in ast.walk(node):
            if not (
                isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Attribute)
                and inner.func.attr == "take_damage"
                and inner.args
            ):
                continue
            if len(inner.args) == 3 and not best:
                best = {
                    "positional_args": len(inner.args),
                    "keywords": sorted(keyword.arg for keyword in inner.keywords),
                    "third_arg": ast.unparse(inner.args[2]),
                }
            elif len(inner.args) == 2 and not fallback:
                fallback = {
                    "positional_args": len(inner.args),
                    "keywords": sorted(keyword.arg for keyword in inner.keywords),
                }
        if best:
            best["fallback_positional_args"] = fallback.get("positional_args", -1)
            best["fallback_keywords"] = fallback.get("keywords", ["?"])
            return best
    return {}


def _source_shape():
    take_damage = ast.unparse(_boss_method("take_damage"))
    resolver = _resolver_text()
    update_src = _method_text("HeroItemInventory", "update", "hero_items.py")
    hero_update_src = _method_text("Hero", "update", "_entity.py")
    shape = {}
    for arm in ARMS:
        call = _arm_call_shape(arm["item"])
        prefix = "{}_take_damage".format(arm["name"])
        shape[prefix + "_positional_args"] = call.get("positional_args", -1)
        shape[prefix + "_keywords"] = call.get("keywords", [])
        shape[prefix + "_third_arg"] = call.get("third_arg", "")
        shape[prefix + "_fallback_positional_args"] = call.get(
            "fallback_positional_args", -1
        )
        shape[prefix + "_fallback_keywords"] = call.get("fallback_keywords", ["?"])
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
    shape["arms_are_reached_from_hero_update"] = "inv.update(1, enemies" in hero_update_src
    shape["update_wraps_magic_arms_in_try_except"] = update_src.count("except TypeError:") >= 6
    return shape


def _build_runtime():
    item_env = item_source_namespace(with_inventory=True, with_functions=True)
    _install_effect_stubs(item_env)
    item_env["math"] = math
    item_env["random"] = _AlwaysRandom()
    catalog = item_env["ITEM_CATALOG"]
    # `inventory_type` execs the real `HeroItemInventory.update` (plus add/slot
    # bookkeeping); the effect stubs above give it working `_fx_*` notifiers, a
    # no-op `_tick_miasma`, and `_apply_*` helpers identical to the source.
    inv_cls = inventory_type(item_env)
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


def _prepare_owner(inventory_class, arm, target):
    owner = _DummyOwner(target)
    owner.id = OWNER_ID
    owner.name = "Kaizen"
    # The shared dummy carries the native int teams; the boss-kill pass compares
    # `killer.team != "blue"` literally, so the source column needs the strings.
    owner.team = BLUE
    # `Game._killer_is_hero` requires the source `hero_type` + `skills` pair.
    owner.hero_type = "kaizen"
    owner.skills = ["q", "w", "e", "r"]
    owner.x = OWNER_X
    owner.y = 0.0
    owner.role = ARM_BY_NAME[arm]["role"]
    owner.range = 130 if owner.role == "Mage" else 70
    owner.is_melee_hero = owner.role != "Mage"
    owner.level = 1
    owner.base_hp = 1000
    owner.blind_timer = 0
    owner.blind_amount = 0.0
    inventory = inventory_class(owner)
    owner.items = inventory
    assert inventory.add(ARM_BY_NAME[arm]["item"]), "cannot equip {}".format(arm)
    # `add()` runs the real `_on_item_changed`, which recomputes the owner max
    # HP from hero stats this dummy does not model; restore the live values so
    # the source `h.alive and h.max_hp > 0` gate in `update` opens.
    owner.hp = 1000
    owner.max_hp = 1000
    if arm == "thunder":
        catalog_duration = 480
        inventory.static_timer = catalog_duration
        inventory.static_tick = 1
        inventory.static_cd = 0
    return owner, inventory


def _is_control(arm, scenario):
    return scenario == CONTROL_BY_ARM[arm]


def _run_case(catalog, inventory_class, boss_class, source_game_class, lane,
              boss_type, arm, scenario, native_old):
    layout = _layout_for(arm, scenario)
    boss = _prepare_boss(boss_class, boss_type, lane, layout, scenario)
    extra_one = _DummyUnit(EXTRA_ONE_ID, RED, float(layout["extra_one_x"]))
    extra_two = _DummyUnit(EXTRA_TWO_ID, RED, float(layout["extra_two_x"]))
    if arm == "fulgur" and _is_control(arm, scenario):
        target = extra_one
    else:
        target = boss
    owner, inventory = _prepare_owner(inventory_class, arm, target)
    if scenario.endswith(BLIND_SCENARIO_SUFFIX):
        owner.blind_timer = BLIND_TICKS
        owner.blind_amount = 1.0
    # Source `_get_all_enemies` filters `all_units` (minions + heroes + boss
    # last) by team/alive, so the update list is red units with the boss last.
    enemies = [extra_one, extra_two, boss]

    source_take_damage = boss.take_damage
    landed = []

    def recording_take_damage(damage, from_team=None, damage_type="normal",
                              source=None, school=None):
        # Observe the arguments the arm actually sent. The source column keeps
        # the source call untouched; the native_old column substitutes the pre-9h
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
    inventory.update(1, enemies)
    hp_loss = int(round(hp_before - float(boss.hp)))

    game = credit_game(source_game_class)
    game._process_boss_kill(boss)
    gate = GATE_FIELDS[arm]
    return {
        "boss_hp_loss": hp_loss,
        "boss_alive": bool(boss.alive),
        "owner_kills": int(owner.kills),
        "boss_counter": int(game.miniboss_kill_count) + int(game.trueboss_kill_count),
        "regular_hits": [int(hit) for hit in extra_one.hits + extra_two.hits],
        "gate_after": int(getattr(inventory, gate)),
        "boss_schools": [entry[1] for entry in landed],
        "boss_damage_types": [entry[0] for entry in landed],
    }


def _arm_payload(catalog, arm):
    active = catalog[ARM_BY_NAME[arm]["item"]]["active"]
    payload = {
        "damage": int(active["damage"]),
        "cooldown": int(active["cooldown"]),
    }
    for key in (
        "trigger_enemies",
        "trigger_radius",
        "root_radius",
        "root_duration",
        "radius",
        "targets",
        "tick",
        "duration",
        "slow",
        "slow_duration",
        "burn_dps",
        "burn_duration",
        "silence_duration",
    ):
        if key in active:
            value = active[key]
            payload[key] = float(value) if isinstance(value, float) else int(value)
    return payload


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
            "basic_blind_ticks": BLIND_TICKS,
            "owner_team": BLUE,
            "boss_team": RED,
            "owner_id": OWNER_ID,
            "owner_x": OWNER_X,
            "extra_one_id": EXTRA_ONE_ID,
            "extra_two_id": EXTRA_TWO_ID,
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
        assert shape["{}_take_damage_fallback_positional_args".format(arm)] == 2, (
            "{} TypeError fallback drifted".format(arm)
        )
        assert shape["{}_take_damage_fallback_keywords".format(arm)] == [], (
            "{} fallback gained keywords".format(arm)
        )
    assert shape["boss_blind_block_requires_source"], "boss blind gate drifted"
    assert shape["boss_school_comes_from_resolver"], "boss school resolution drifted"
    assert shape["resolver_returns_none_without_school_or_source"], "resolver drifted"
    assert shape["boss_lethal_branch_stores_source"], "boss kill attribution drifted"
    assert shape["arms_are_reached_from_hero_update"], "update entry point drifted"
    assert shape["update_wraps_magic_arms_in_try_except"], "try/except wrapper drifted"

    cases = fixture["cases"]
    boss_types = {row["boss_type"] for row in cases}
    assert fixture["boss_type_count"] == 216 and len(boss_types) == 216
    assert fixture["case_count"] == len(cases) == 5184
    assert all(sum(row["boss_type"] == boss for row in cases) == 24 for boss in boss_types)
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
            # The control still fires the arm at the minions, so the gate must
            # have advanced and the regular payload must be non-empty.
            assert expected["regular_hits"], "the control arm must still hit minions"
            continue
        # Every proccing row records the call shape the arm sent to the boss:
        # the source omits `source`/`school` and keeps `damage_type="magic"`,
        # while the pre-9h native bus sent "normal" with the owner as source and
        # the declared magic school.
        assert expected["boss_hp_loss"] > 0, "the source arm must land on the boss"
        assert expected["boss_schools"] == ["neutral"], "source school is resolved to None"
        assert expected["boss_damage_types"] == ["magic"]
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
            assert native_old["boss_hp_loss"] == 0, "pre-9h native dropped it"
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
    assert blind_gap == 216 * 6, "every arm records the blind gap"
    assert lethal_gap == 216 * 6, "every boss type records the kill-credit gap"
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
        print("wrote {} auto magic damage cases to {}".format(len(fixture["cases"]), FIXTURE))
    else:
        print(
            "auto magic damage oracle self-test passed: "
            "{} cases across {} bosses".format(
                len(fixture["cases"]), fixture["boss_type_count"]
            )
        )


if __name__ == "__main__":
    main()
