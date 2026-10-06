"""9i: source oracle for the Razor Carapace Thornmail reflect on the boss.

`HeroItemInventory.notify_damage_taken` (`hero_items.py:2439-2472`) ends with
the Thornmail reflect (`:2459-2472`):

    refl = self.get_reflect_pct()
    if (refl > 0 and damage > 0 and source is not None
            and getattr(source, "alive", False)
            and getattr(source, "team", self.hero.team)
            != self.hero.team):
        dmg = int(damage * refl)
        if dmg > 0:
            try:
                source.take_damage(dmg, self.hero.team, "magic")
            except TypeError:
                source.take_damage(dmg, self.hero.team)

`get_reflect_pct` returns the catalog fraction (`reflect_pct = 0.85`) only
while `thorn_timer > 0` and the victim owns `razor_carapace`, else `0.0`.
When the attacker is `game.active_boss` the try branch reaches
`Boss.take_damage` (`bosses/base_boss.py:5978`) as `damage_type='magic'`,
`source=None`, `school=None`, so

* the Solar Brand blind block is skipped (it needs `damage_type == 'normal'`
  **and** `source is not None`);
* `resolve_damage_school('magic', None, None)` returns `None`
  (`_entity.py:106-130`), so no school mitigation applies - neither boss magic
  resist nor armor;
* a lethal reflect stores `self._killed_by = None`, so
  `Game._process_boss_kill` (`_core.py:2516-2545`) awards neither `kills` nor
  the mini/true boss counter.

The native reflect already travels on its own bus (`ReflectItemEffects`,
`reflect_item_effects.gd`), which sends `source_id=-1`: the blind gate and
the kill credit already match the source, and only the school gap remains.
Pre-9i the bus delivered school `"magic"` with the `"normal"` damage-type
default, so boss magic resist cut the reflected payload.

One arm, four scenarios per boss type (216 bosses x 4 = 864 cases): the
school/resist gap against the boss attacker, a minion-attacker control that
must stay identical in both columns, a thorn-inactive control where nothing
fires, and a lethal reflect where the call shape diverges but both columns
credit nobody. `--self-test` skips the fixture; `--write` is the only
fixture writer.
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

FIXTURE = Path(__file__).parent / "fixtures/boss_item_reflect_carapace_source.json"

# Source teams are the strings "blue"/"red"; `Game._process_boss_kill` compares
# `killer.team != "blue"` literally, so the oracle keeps the source types.
BLUE = "blue"
RED = "red"
EXTRA_ONE_ID = 11
EXTRA_TWO_ID = 12
BOSS_ID = 500
VICTIM_ID = 7
VICTIM_X = -40.0
# Incoming post-mitigation damage on the victim; the reflected payload is
# `int(200 * 0.85) == 170`.
INCOMING_DAMAGE = 200
REFLECT_SENT = 170
# Catalog Thornmail duration (`razor_carapace.active.duration`); the oracle
# pins only the notify reflect arm, not the HP<55% auto-trigger in `update`.
THORN_ACTIVE_TICKS = 270

# `Boss.take_damage(damage, from_team, damage_type='normal', source=None,
# school=None)` is the only signature the reflect arm reaches, so the source
# column is "three positional arguments and nothing else".
SOURCE_ARG_COUNT = 3

ARM = "reflect"
ITEM_ID = "razor_carapace"
RESIST_SCENARIO = "reflect_vs_boss_resist"
MINION_SCENARIO = "reflect_to_minion_unchanged"
INACTIVE_SCENARIO = "reflect_thorn_inactive"
LETHAL_SCENARIO = "reflect_lethal_no_credit"
SCENARIO_NAMES = (
    RESIST_SCENARIO,
    MINION_SCENARIO,
    INACTIVE_SCENARIO,
    LETHAL_SCENARIO,
)
CONTROL_SCENARIOS = (MINION_SCENARIO, INACTIVE_SCENARIO)

# World layout, replayed verbatim by the native suite. Reflect has no radius
# gate; the positions only keep the shared arena shape.
LAYOUT = {
    "boss_x": 0.0,
    "extra_one_x": 20.0,
    "extra_two_x": 50.0,
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


def _notify_call_shape():
    """Shape of the `take_damage` call inside `notify_damage_taken`."""
    notify_node = _method_node("HeroItemInventory", "notify_damage_taken", "hero_items.py")
    best = {}
    fallback = {}
    for node in ast.walk(notify_node):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "take_damage"
            and node.args
        ):
            continue
        if len(node.args) == 3 and not best:
            best = {
                "positional_args": len(node.args),
                "keywords": sorted(keyword.arg for keyword in node.keywords),
                "third_arg": ast.unparse(node.args[2]),
            }
        elif len(node.args) == 2 and not fallback:
            fallback = {
                "positional_args": len(node.args),
                "keywords": sorted(keyword.arg for keyword in node.keywords),
            }
    best["fallback_positional_args"] = fallback.get("positional_args", -1)
    best["fallback_keywords"] = fallback.get("keywords", ["?"])
    return best


def _source_shape():
    take_damage = ast.unparse(_boss_method("take_damage"))
    resolver = _resolver_text()
    notify_src = _method_text("HeroItemInventory", "notify_damage_taken", "hero_items.py")
    reflect_src = _method_text("HeroItemInventory", "get_reflect_pct", "hero_items.py")
    hero_take_damage_src = _method_text("Hero", "take_damage", "_entity.py")
    call = _notify_call_shape()
    shape = {
        "reflect_take_damage_positional_args": call.get("positional_args", -1),
        "reflect_take_damage_keywords": call.get("keywords", []),
        "reflect_take_damage_third_arg": call.get("third_arg", ""),
        "reflect_take_damage_fallback_positional_args": call.get(
            "fallback_positional_args", -1
        ),
        "reflect_take_damage_fallback_keywords": call.get("fallback_keywords", ["?"]),
    }
    compact_reflect = _compact(reflect_src)
    shape["reflect_pct_needs_thorn_timer"] = "self.thorn_timer>0" in compact_reflect
    shape["reflect_pct_needs_razor"] = "self.has('razor_carapace')" in compact_reflect
    compact_notify = _compact(notify_src)
    shape["reflect_guard_requires_alive_attacker"] = (
        "getattr(source,'alive',False)" in compact_notify
    )
    shape["reflect_guard_requires_enemy_team"] = "!=self.hero.team" in compact_notify
    shape["notify_is_reached_from_hero_take_damage"] = (
        "notify_damage_taken(" in hero_take_damage_src
    )
    shape["notify_wraps_reflect_in_try_except"] = "exceptTypeError:" in compact_notify
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
    return shape


def _build_runtime():
    item_env = item_source_namespace(with_inventory=True, with_functions=True)
    _install_effect_stubs(item_env)
    item_env["math"] = math
    item_env["random"] = _AlwaysRandom()
    catalog = item_env["ITEM_CATALOG"]
    # `inventory_type` execs the real `HeroItemInventory.notify_damage_taken`
    # (plus add/slot bookkeeping); the effect stubs above give it a working
    # `_fx_notify`, and `_apply_*` helpers identical to the source.
    inv_cls = inventory_type(item_env)
    boss_cls = core_boss_class(core_namespace())
    return catalog, inv_cls, boss_cls


def _build_source_runtime():
    catalog, inventory_class, boss_class = _build_runtime()
    lane = source_lanes()["mid"]
    return catalog, inventory_class, boss_class, game_class(), lane


def _prepare_boss(boss_class, boss_type, lane, scenario):
    boss = boss_class(boss_type, lane)
    boss.id = BOSS_ID
    boss.team = RED
    boss.alive = True
    boss.defeated = False
    boss.x = float(LAYOUT["boss_x"])
    boss.y = 0.0
    boss._killed_by = None
    boss.lane = lane
    boss.hp = 1 if scenario == LETHAL_SCENARIO else boss.max_hp
    return boss


def _prepare_victim(inventory_class, target, scenario):
    victim = _DummyOwner(target)
    victim.id = VICTIM_ID
    victim.name = "Kaizen"
    # The shared dummy carries the native int teams; the boss-kill pass compares
    # `killer.team != "blue"` literally, so the source column needs the strings.
    victim.team = BLUE
    # `Game._killer_is_hero` requires the source `hero_type` + `skills` pair.
    victim.hero_type = "kaizen"
    victim.skills = ["q", "w", "e", "r"]
    victim.x = VICTIM_X
    victim.y = 0.0
    victim.role = "Bruiser"
    victim.range = 70
    victim.is_melee_hero = True
    victim.level = 1
    victim.base_hp = 1000
    victim.blind_timer = 0
    victim.blind_amount = 0.0
    inventory = inventory_class(victim)
    victim.items = inventory
    assert inventory.add(ITEM_ID), "cannot equip {}".format(ITEM_ID)
    # `add()` runs the real `_on_item_changed`, which recomputes the owner max
    # HP from hero stats this dummy does not model; restore the live values.
    victim.hp = 1000
    victim.max_hp = 1000
    inventory.thorn_timer = 0 if scenario == INACTIVE_SCENARIO else THORN_ACTIVE_TICKS
    return victim, inventory


def _run_case(catalog, inventory_class, boss_class, source_game_class, lane,
              boss_type, scenario, native_old):
    boss = _prepare_boss(boss_class, boss_type, lane, scenario)
    extra_one = _DummyUnit(EXTRA_ONE_ID, RED, float(LAYOUT["extra_one_x"]))
    extra_two = _DummyUnit(EXTRA_TWO_ID, RED, float(LAYOUT["extra_two_x"]))
    attacker = extra_one if scenario == MINION_SCENARIO else boss
    victim, inventory = _prepare_victim(inventory_class, attacker, scenario)

    source_take_damage = boss.take_damage
    calls = []
    landed = []

    def recording_take_damage(damage, from_team=None, damage_type="normal",
                              source=None, school=None):
        # Observe the arguments the reflect arm actually sent. The source
        # column keeps the source call untouched; the native_old column
        # substitutes the pre-9i native arguments (`ReflectItemEffects` ->
        # `_deliver_hit` default "normal" damage_type with no source and the
        # declared magic school). The source leaves `school=None`;
        # `resolve_damage_school` returns `None` there, which the native plan
        # spells as "neutral".
        hp_before_call = float(boss.hp)
        if native_old:
            result = source_take_damage(damage, from_team, "normal", source=None,
                                        school="magic")
            observed = (int(damage), "normal", "magic")
        else:
            result = source_take_damage(damage, from_team, damage_type,
                                        source=source, school=school)
            observed = (int(damage), damage_type, school if school else "neutral")
        calls.append(observed)
        if float(boss.hp) < hp_before_call:
            landed.append(observed)
        return result

    boss.take_damage = recording_take_damage

    hp_before = float(boss.hp)
    inventory.notify_damage_taken(damage=INCOMING_DAMAGE, source=attacker)
    hp_loss = int(round(hp_before - float(boss.hp)))

    game = credit_game(source_game_class)
    game._process_boss_kill(boss)
    if calls:
        reflect_sent = calls[0][0]
    elif scenario == MINION_SCENARIO and extra_one.hits:
        reflect_sent = int(extra_one.hits[0])
    else:
        reflect_sent = 0
    return {
        "boss_hp_loss": hp_loss,
        "boss_alive": bool(boss.alive),
        "owner_kills": int(victim.kills),
        "boss_counter": int(game.miniboss_kill_count) + int(game.trueboss_kill_count),
        "regular_hits": [int(hit) for hit in extra_one.hits + extra_two.hits],
        "reflect_sent": reflect_sent,
        "boss_schools": [entry[2] for entry in landed],
        "boss_damage_types": [entry[1] for entry in landed],
    }


def _reflect_payload(catalog):
    active = catalog[ITEM_ID]["active"]
    return {
        "reflect_pct": float(active["reflect_pct"]),
        "duration": int(active["duration"]),
        "cooldown": int(active["cooldown"]),
        "hp_threshold": float(active["hp_threshold"]),
    }


def source_fixture():
    catalog, inventory_class, boss_class, source_game_class, lane = _build_source_runtime()
    payload = _reflect_payload(catalog)
    cases = []
    for boss_type in sorted(SOURCE_STATS):
        for scenario in SCENARIO_NAMES:
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
                    "arm": ARM,
                    "scenario": scenario,
                    "attacker": "minion" if scenario == MINION_SCENARIO else "boss",
                    "thorn_active": scenario != INACTIVE_SCENARIO,
                    "boss_hp_before": 1
                    if scenario == LETHAL_SCENARIO
                    else int(boss_class(boss_type, lane).max_hp),
                    "expected": expected,
                    "native_old": native_old,
                }
            )
    fixture = {
        "source": {
            "ast_shape": _source_shape(),
            "arm": {
                "name": ARM,
                "item": ITEM_ID,
                "role": "Bruiser",
                "control_scenarios": list(CONTROL_SCENARIOS),
                "payload": payload,
            },
            "scenario_names": list(SCENARIO_NAMES),
            "incoming_damage": INCOMING_DAMAGE,
            "reflect_sent": REFLECT_SENT,
            "thorn_active_ticks": THORN_ACTIVE_TICKS,
            "owner_team": BLUE,
            "boss_team": RED,
            "owner_id": VICTIM_ID,
            "owner_x": VICTIM_X,
            "extra_one_id": EXTRA_ONE_ID,
            "extra_two_id": EXTRA_TWO_ID,
            "boss_id": BOSS_ID,
            "layout": dict(LAYOUT),
        },
        "boss_type_count": len(SOURCE_STATS),
        "case_count": len(cases),
        "cases": cases,
    }
    _assert_fixture_logic(fixture)
    return fixture


def _assert_fixture_logic(fixture):
    shape = fixture["source"]["ast_shape"]
    assert shape["reflect_take_damage_positional_args"] == SOURCE_ARG_COUNT, (
        "reflect call shape drifted"
    )
    assert shape["reflect_take_damage_keywords"] == [], "reflect call gained keywords"
    assert shape["reflect_take_damage_third_arg"] == "'magic'", (
        "reflect third argument drifted"
    )
    assert shape["reflect_take_damage_fallback_positional_args"] == 2, (
        "reflect TypeError fallback drifted"
    )
    assert shape["reflect_take_damage_fallback_keywords"] == [], (
        "reflect fallback gained keywords"
    )
    assert shape["reflect_pct_needs_thorn_timer"], "thorn gate drifted"
    assert shape["reflect_pct_needs_razor"], "razor gate drifted"
    assert shape["reflect_guard_requires_alive_attacker"], "attacker-alive gate drifted"
    assert shape["reflect_guard_requires_enemy_team"], "enemy-team gate drifted"
    assert shape["notify_is_reached_from_hero_take_damage"], "notify entry point drifted"
    assert shape["notify_wraps_reflect_in_try_except"], "try/except wrapper drifted"
    assert shape["boss_blind_block_requires_source"], "boss blind gate drifted"
    assert shape["boss_school_comes_from_resolver"], "boss school resolution drifted"
    assert shape["resolver_returns_none_without_school_or_source"], "resolver drifted"
    assert shape["boss_lethal_branch_stores_source"], "boss kill attribution drifted"

    payload = fixture["source"]["arm"]["payload"]
    assert payload["reflect_pct"] == 0.85, "catalog reflect fraction drifted"
    assert payload["duration"] == THORN_ACTIVE_TICKS, "catalog thorn duration drifted"
    assert fixture["source"]["incoming_damage"] == INCOMING_DAMAGE
    assert INCOMING_DAMAGE * payload["reflect_pct"] == REFLECT_SENT

    cases = fixture["cases"]
    boss_types = {row["boss_type"] for row in cases}
    assert fixture["boss_type_count"] == 216 and len(boss_types) == 216
    assert fixture["case_count"] == len(cases) == 864
    assert all(sum(row["boss_type"] == boss for row in cases) == 4 for boss in boss_types)
    resist_gap = 0
    for row in cases:
        expected = row["expected"]
        native_old = row["native_old"]
        scenario = row["scenario"]
        assert expected["regular_hits"] == native_old["regular_hits"], (
            "the regular-unit arm must not change for {}".format(scenario)
        )
        assert expected["reflect_sent"] == native_old["reflect_sent"], (
            "the reflected payload math must not change for {}".format(scenario)
        )
        # Neither column may ever credit the reflect victim: both send no
        # source, so `_killed_by` stays None on both sides.
        assert expected["owner_kills"] == 0 and native_old["owner_kills"] == 0
        assert expected["boss_counter"] == 0 and native_old["boss_counter"] == 0
        if scenario in CONTROL_SCENARIOS:
            assert expected == native_old, "control row must not diverge"
            assert expected["boss_hp_loss"] == 0 and expected["boss_alive"]
            assert expected["boss_schools"] == [] and expected["boss_damage_types"] == []
            if scenario == MINION_SCENARIO:
                # The minion attacker eats the full reflected payload.
                assert expected["regular_hits"] == [REFLECT_SENT]
                assert expected["reflect_sent"] == REFLECT_SENT
            else:
                assert expected["regular_hits"] == []
                assert expected["reflect_sent"] == 0
            continue
        # Every proccing row records the call shape the arm sent to the boss:
        # the source omits `source`/`school` and keeps `damage_type="magic"`,
        # while the pre-9i native bus sent "normal" with no source and the
        # declared magic school.
        assert expected["reflect_sent"] == REFLECT_SENT
        assert expected["boss_schools"] == ["neutral"], "source school is resolved to None"
        assert expected["boss_damage_types"] == ["magic"]
        assert native_old["boss_schools"] == ["magic"]
        assert native_old["boss_damage_types"] == ["normal"]
        assert expected != native_old, "proccing rows must diverge"
        if scenario == RESIST_SCENARIO:
            assert expected["boss_hp_loss"] > 0, "the source reflect must land"
            assert expected["boss_hp_loss"] >= native_old["boss_hp_loss"]
            assert expected["boss_alive"] and native_old["boss_alive"]
            if expected["boss_hp_loss"] != native_old["boss_hp_loss"]:
                resist_gap += 1
        else:
            assert scenario == LETHAL_SCENARIO
            assert not expected["boss_alive"] and not native_old["boss_alive"]
    # Small magic resist can round away on some boss types, so the gap is only
    # required to exist across the roster.
    assert resist_gap > 0, "the magic-resist gap must be recorded"
    for scenario in SCENARIO_NAMES:
        rows = [row for row in cases if row["scenario"] == scenario]
        assert len(rows) == 216, "{} rows drifted".format(scenario)


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
        print("wrote {} reflect carapace cases to {}".format(len(fixture["cases"]), FIXTURE))
    else:
        print(
            "reflect carapace oracle self-test passed: "
            "{} cases across {} bosses".format(
                len(fixture["cases"]), fixture["boss_type_count"]
            )
        )


if __name__ == "__main__":
    main()
