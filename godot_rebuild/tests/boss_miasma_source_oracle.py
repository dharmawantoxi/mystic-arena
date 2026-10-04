"""9b: source-execute Basilisk Breath reapplication to a boss by two heroes.

At checkpoint 4935af8, hero_items.py:189-206 keys _MIASMA by id(target),
replaces the stored source, keeps max damage/timer and min tick_cd; its
:209-234 tick uses that stored source. The source hit hook calls it at
hero_items.py:2608-2611. Native instead had one tracker in each
HeroItemInventory (hero_item_inventory.gd:123,768-818), applied through its
on-hit hook (:909-932; prototype_battle.gd:2193-2195) and ticked from
prototype_battle.gd:1956,1986-1993. Two inventories therefore retained two
poisons instead of one merged poison.

Each of the 216 boss types has four replay schedules. `expected` executes the
read-only Python on-hit/helper AST; `native_old` models the pre-9b per-inventory
tracker and records its counterfactual damage/source events.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from boss_item_cleave_chain_source_oracle import (  # noqa: E402
    SOURCE_STATS,
    _DummyOwner,
    _build_runtime,
    _func_node,
    _prepare_boss,
)

FIXTURE = Path(__file__).parent / "fixtures/boss_miasma_source.json"
OWNER_A_ID = 7
OWNER_B_ID = 8
BLUE = 0
BASIC_DAMAGE = 50

SCENARIOS = (
    {
        "name": "same_frame_reapply",
        "pre_frames": 0,
        "observe_frames": 15,
        "reapplying_hero_dies": False,
    },
    {
        "name": "reapply_near_tick",
        "pre_frames": 14,
        "observe_frames": 1,
        "reapplying_hero_dies": False,
    },
    {
        "name": "reapply_after_first_tick",
        "pre_frames": 15,
        "observe_frames": 15,
        "reapplying_hero_dies": False,
    },
    {
        "name": "reapplying_hero_dies",
        "pre_frames": 0,
        "observe_frames": 30,
        "reapplying_hero_dies": True,
    },
)


def _shape_flags():
    apply_node = _func_node("_apply_miasma", "hero_items.py")
    tick_node = _func_node("_tick_miasma", "hero_items.py")
    apply_text = ast.unparse(apply_node)
    tick_text = ast.unparse(tick_node)
    return {
        "global_target_key": "key = id(target)" in apply_text and "_MIASMA.get(key)" in apply_text,
        "source_replaced": "prev['source'] = source" in apply_text,
        "damage_max": "prev['damage'] = max(prev['damage'], dmg)" in apply_text,
        "timer_max": "prev['timer'] = max(prev['timer'], data['duration'])" in apply_text,
        "tick_cd_min": "prev['tick_cd'] = min(prev['tick_cd'], data['tick'])" in apply_text,
        "tick_uses_stored_source": "src = m['source']" in tick_text
        and "team = getattr(src, 'team', None)" in tick_text,
        "tick_reset_30": "m['tick_cd'] = 30" in tick_text,
    }


def _owner_label(owner):
    owner_id = int(owner.id)
    if owner_id == OWNER_A_ID:
        return "hero_a"
    if owner_id == OWNER_B_ID:
        return "hero_b"
    return "unknown"


def _source_application(inv):
    # This is the source inventory's real on_basic_attack_hit -> _on_hit_common
    # path. The boss is the attack target, as in the native hero_basic_attack.
    inv.on_basic_attack_hit(inv.hero.target, BASIC_DAMAGE, [inv.hero.target])


def _source_tick(env, boss, frame, events):
    tracker = env["_MIASMA"].get(id(boss))
    source = tracker["source"] if tracker is not None else None
    previous_hits = len(boss.hits)
    env["_tick_miasma"](1)
    if len(boss.hits) > previous_hits:
        events.append([frame, _owner_label(source), int(boss.hits[-1])])


def _legacy_apply(trackers, owner, target, data):
    damage = int(float(target.max_hp) * float(data["max_hp_pct_per_tick"]))
    damage = max(6, min(int(data.get("cap_damage", 9999)), damage))
    previous = trackers.get(owner)
    if previous is None:
        trackers[owner] = {
            "damage": damage,
            "timer": int(data["duration"]),
            "tick_cd": int(data["tick"]),
        }
    else:
        previous["damage"] = max(previous["damage"], damage)
        previous["timer"] = max(previous["timer"], int(data["duration"]))
        previous["tick_cd"] = min(previous["tick_cd"], int(data["tick"]))


def _legacy_tick(trackers, owner, frame, events):
    tracker = trackers.get(owner)
    if tracker is None:
        return
    tracker["timer"] -= 1
    tracker["tick_cd"] -= 1
    if tracker["tick_cd"] <= 0:
        tracker["tick_cd"] = 30
        events.append([frame, owner, int(tracker["damage"])])
    if tracker["timer"] <= 0:
        trackers.pop(owner, None)


def _advance_source(env, boss, live_owners, frame, events):
    # hero_items.py calls _tick_miasma from each inventory update. Each living
    # hero therefore makes one global-registry tick in the source behavior.
    for _owner in live_owners:
        _source_tick(env, boss, frame, events)


def _advance_legacy(trackers, live_owners, frame, events):
    # The old native path ticked only the current hero inventory; a tracker
    # applied by a different hero stayed in that hero's local dictionary.
    for owner in live_owners:
        _legacy_tick(trackers, owner, frame, events)


def _run_case(catalog, inv_cls, boss_cls, boss_type, scenario):
    env = inv_cls._on_hit_common.__globals__
    env["_MIASMA"] = {}
    boss = _prepare_boss(boss_cls, boss_type, 0.0)
    owner_a = _DummyOwner(boss)
    owner_a.id = OWNER_A_ID
    owner_a.team = BLUE
    owner_b = _DummyOwner(boss)
    owner_b.id = OWNER_B_ID
    owner_b.team = BLUE
    inv_a = inv_cls(owner_a)
    inv_b = inv_cls(owner_b)
    assert inv_a.add("basilisk_breath") and inv_b.add("basilisk_breath")
    data = catalog["basilisk_breath"]["on_attack"]

    _source_application(inv_a)
    legacy_trackers = {}
    _legacy_apply(legacy_trackers, "hero_a", boss, data)

    ignored_source_events = []
    ignored_native_events = []
    for frame in range(1, int(scenario["pre_frames"]) + 1):
        _advance_source(env, boss, ["hero_a", "hero_b"], frame, ignored_source_events)
        _advance_legacy(legacy_trackers, ["hero_a", "hero_b"], frame, ignored_native_events)

    _source_application(inv_b)
    _legacy_apply(legacy_trackers, "hero_b", boss, data)
    if bool(scenario["reapplying_hero_dies"]):
        owner_b.alive = False

    native_old_trackers = [
        {"owner": owner, **dict(legacy_trackers[owner])}
        for owner in ("hero_a", "hero_b")
        if owner in legacy_trackers
    ]
    tracker = env["_MIASMA"].get(id(boss))
    expected_tracker = {
        "count": len(env["_MIASMA"]),
        "owner": _owner_label(tracker["source"]),
        "damage": int(tracker["damage"]),
        "timer": int(tracker["timer"]),
        "tick_cd": int(tracker["tick_cd"]),
    }
    boss.hits.clear()

    expected_events = []
    native_old_events = []
    live_owners = (
        ["hero_a"]
        if bool(scenario["reapplying_hero_dies"])
        else ["hero_a", "hero_b"]
    )
    for frame in range(1, int(scenario["observe_frames"]) + 1):
        _advance_source(env, boss, live_owners, frame, expected_events)
        _advance_legacy(legacy_trackers, live_owners, frame, native_old_events)

    return {
        "boss_type": boss_type,
        "scenario": scenario["name"],
        "boss_max_hp": float(boss.max_hp),
        "pre_frames": int(scenario["pre_frames"]),
        "observe_frames": int(scenario["observe_frames"]),
        "reapplying_hero_dies": bool(scenario["reapplying_hero_dies"]),
        "expected": {"tracker": expected_tracker, "events": expected_events},
        "native_old": {
            "tracker_count": len(native_old_trackers),
            "trackers": native_old_trackers,
            "events": native_old_events,
        },
    }


def source_fixture():
    catalog, inv_cls, boss_cls = _build_runtime()
    env = inv_cls._on_hit_common.__globals__
    env["_MIASMA"] = {}
    source_module = ast.Module(
        body=[
            _func_node("_apply_miasma", "hero_items.py"),
            _func_node("_tick_miasma", "hero_items.py"),
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(source_module)
    exec(compile(source_module, "<source-miasma>", "exec"), env)
    item_data = catalog["basilisk_breath"]["on_attack"]
    cases = [
        _run_case(catalog, inv_cls, boss_cls, boss_type, scenario)
        for boss_type in sorted(SOURCE_STATS)
        for scenario in SCENARIOS
    ]
    return {
        "source": {
            "ast_shape": _shape_flags(),
            "on_attack": {
                "max_hp_pct_per_tick": float(item_data["max_hp_pct_per_tick"]),
                "cap_damage": int(item_data["cap_damage"]),
                "duration": int(item_data["duration"]),
                "tick": int(item_data["tick"]),
            },
            "python_source": "hero_items.py:189-234,2608-2611",
            "native_old_source": (
                "hero_item_inventory.gd:123,768-818,909-932; "
                "prototype_battle.gd:1956,1986-1993,2193-2195"
            ),
            "boss_types": len(SOURCE_STATS),
        },
        "cases": cases,
    }


if __name__ == "__main__":
    fixture = source_fixture()
    assert len(fixture["cases"]) == 864
    assert fixture["source"]["boss_types"] == 216
    assert all(fixture["source"]["ast_shape"].values())
    for row in fixture["cases"]:
        assert row["expected"]["tracker"]["count"] == 1
        assert row["expected"]["tracker"]["owner"] == "hero_b"
        assert row["native_old"]["tracker_count"] == 2
        assert row["expected"]["events"] != row["native_old"]["events"]
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n")
    print("PASS: 864 Miasma source cases; global source transfer vs per-inventory counterfactual")
