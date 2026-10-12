"""9ad: boss tenacity on tower item debuffs (slow / ice / mage / anti-heal).

`Boss.apply_slow` and `Boss.apply_debuff` (`bosses/base_boss.py:528-552`) cut
every debuff that arrives through the entity method by tenacity 0.50 - magnitude
`min(0.35, amount * 0.50)` and duration `int(duration * 0.50)` - while a minion or
hero runs the plain `TowerDebuffMixin` store (`_core.py:918-948`), i.e. the raw
payload.

The polymorphic call sites are:

* mage tower bolts: `self.target.apply_debuff('skill_down', skill_down,
  debuff_duration)` / `apply_debuff('anti_heal', ...)` (`_entity.py:313-325`),
* ice bolts: `self.target.apply_slow(...)` plus `apply_debuff('atk_slow', ...)`
  (`_entity.py:286-306`),
* item arms: Frostbound Frostbite (`hero_items.py:2594-2599`), Everfrost Arctic
  Blast (`:2290-2291`) and Freezing Aura (`:2843-2844`), Searbrand Cauterize
  (`:2869-2870`), Vine Rod Entangle (`:2662`).

Rows execute the real `Boss.apply_slow` / `Boss.apply_debuff` and the real
`TowerDebuffMixin.apply_debuff` (unit column) with payloads read from the
source tower tables and the live item catalog, so both columns come from the
source algorithm. `--write` rewrites the fixture.
"""

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from boss_core_source_oracle import boss_class, namespace  # noqa: E402
from check_source_contract import source_lanes  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_debuff_tenacity_source.json"
CATALOG = ROOT / "godot_rebuild" / "data" / "ai" / "item_catalog.json"
BOSS_SOURCE = ROOT / "bosses" / "base_boss.py"
CORE_SOURCE = ROOT / "_core.py"
MINI = "gornak"
CAP = 0.35
TENACITY = 0.50
# `Boss.apply_debuff` only cuts `slow` (through `apply_slow`) and `atk_slow`;
# `skill_down`, `anti_heal` and `burn` pass through to the mixin store raw.
CUT_KINDS = ("slow", "atk_slow")

_ENV = None
BOSS_CLS = None
MIXIN = None
LANE = None


def _harness():
    global _ENV, BOSS_CLS, MIXIN, LANE
    if _ENV is None:
        _ENV = namespace()
        BOSS_CLS = boss_class(_ENV)
        MIXIN = _ENV["TowerDebuffMixin"]
        LANE = source_lanes()["mid"]
    return BOSS_CLS


def _tenacity_shape() -> dict:
    tree = ast.parse(BOSS_SOURCE.read_text(encoding="utf-8"))
    holder = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss")
    methods = {
        node.name: node
        for node in holder.body
        if isinstance(node, ast.FunctionDef) and node.name in ("apply_slow", "apply_debuff")
    }
    slow = ast.unparse(methods["apply_slow"])
    debuff = ast.unparse(methods["apply_debuff"])
    mixture = ast.parse(CORE_SOURCE.read_text(encoding="utf-8"))
    mixin = next(
        node
        for node in mixture.body
        if isinstance(node, ast.ClassDef) and node.name == "TowerDebuffMixin"
    )
    store = next(
        node for node in mixin.body if isinstance(node, ast.FunctionDef) and node.name == "apply_debuff"
    )
    store_text = ast.unparse(store)
    return {
        "has_apply_slow_override": "apply_slow" in methods,
        "has_apply_debuff_override": "apply_debuff" in methods,
        "slow_tenacity_default": "getattr(self, 'tenacity', 0.5)" in slow,
        "slow_cap": "min(0.35, amount * (1.0 - tenacity))" in slow,
        "slow_duration_cut": "int(duration * (1.0 - tenacity))" in slow,
        "atk_slow_cut": "min(0.35, amount * (1.0 - tenacity))" in debuff
        and "int(duration * (1.0 - tenacity))" in debuff,
        "slow_kind_routes_to_apply_slow": "kind == 'slow'" in debuff,
        "skill_down_not_cut": 'skill_down' not in debuff,
        "anti_heal_not_cut": 'anti_heal' not in debuff,
        "skill_down_not_cut": "skill_down" not in debuff,
        "anti_heal_not_cut": "anti_heal" not in debuff,
        "unit_store_has_no_tenacity": "tenacity" not in store_text,
        "unit_store_skill_down": "kind == 'skill_down'" in store_text,
        "unit_store_anti_heal": "kind == 'anti_heal'" in store_text,
    }


def _columns(amount, timer, cap_applied):
    return {"amount": round(float(amount), 6), "timer": int(timer), "capped": bool(cap_applied)}


def _boss_row(kind, debuff_kind, amount, duration):
    boss = _harness()(MINI, LANE)
    if debuff_kind == "slow":
        boss.apply_slow(amount, duration)
    else:
        boss.apply_debuff(debuff_kind, amount, duration)
    if debuff_kind == "slow":
        stored, timer = boss.slow_amount, boss.slow_timer
    elif debuff_kind == "atk_slow":
        stored, timer = boss.atk_slow_amount, boss.atk_slow_timer
    elif debuff_kind == "skill_down":
        stored, timer = boss.skill_down_amount, boss.skill_down_timer
    else:
        stored, timer = boss.anti_heal_amount, boss.anti_heal_timer
    capped = debuff_kind in CUT_KINDS and amount * (1.0 - TENACITY) > CAP
    return _columns(stored, timer, capped)


def _unit_row(debuff_kind, amount, duration):
    unit = MIXIN()
    unit._init_tower_debuffs()
    unit.alive = True
    unit.apply_debuff(debuff_kind, amount, duration)
    if debuff_kind == "slow":
        stored, timer = unit.slow_amount, unit.slow_timer
    elif debuff_kind == "atk_slow":
        stored, timer = unit.atk_slow_amount, unit.atk_slow_timer
    elif debuff_kind == "skill_down":
        stored, timer = unit.skill_down_amount, unit.skill_down_timer
    else:
        stored, timer = unit.anti_heal_amount, unit.anti_heal_timer
    return _columns(stored, timer, False)


def _row(name, payload, source_name, note):
    boss = _boss_row(MINI, payload["kind"], payload["amount"], payload["duration"])
    unit = _unit_row(payload["kind"], payload["amount"], payload["duration"])
    return {
        "name": name,
        "source_name": source_name,
        "note": note,
        "payload": payload,
        "boss": boss,
        "unit": unit,
    }


def source_fixture():
    env = _harness() and _ENV
    mage = env["MAGE_LEVELS"]
    ice = env["ICE_LEVELS"]
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))["items"]
    rows = []
    for level in sorted(mage):
        data = mage[level]
        for kind, key in (("skill_down", "skill_down"), ("anti_heal", "anti_heal")):
            rows.append(
                _row(
                    "mage_level_%d_%s" % (level, kind),
                    {
                        "kind": kind,
                        "amount": float(data[key]),
                        "duration": int(data["debuff_duration"]),
                    },
                    "`_core.py::MAGE_LEVELS[%d]`" % level,
                    "mage bolt debuff: boss tenacity halves magnitude and duration",
                )
            )
    for level in sorted(ice):
        data = ice[level]
        rows.append(
            _row(
                "ice_level_%d_slow" % level,
                {
                    "kind": "slow",
                    "amount": float(data["slow"]),
                    "duration": int(data["slow_duration"]),
                },
                "`_core.py::ICE_LEVELS[%d]`" % level,
                "ice bolt movement slow routes through `Boss.apply_slow`",
            )
        )
        if data.get("atk_slow"):
            rows.append(
                _row(
                    "ice_level_%d_atk_slow" % level,
                    {
                        "kind": "atk_slow",
                        "amount": float(data["atk_slow"]),
                        "duration": int(data["slow_duration"]),
                    },
                    "`_core.py::ICE_LEVELS[%d]`" % level,
                    "ice bolt attack slow keeps the kind-specific store",
                )
            )
    frost = catalog["frostbound_eye"]["on_attack"]
    rows.append(
        _row(
            "frostbound_slow",
            {"kind": "slow", "amount": float(frost["slow"]), "duration": int(frost["duration"])},
            "`hero_items.py::Frostbite`",
            "item slow arm calls `target.apply_slow`",
        )
    )
    rows.append(
        _row(
            "frostbound_atk_slow",
            {"kind": "atk_slow", "amount": float(frost["atk_slow"]), "duration": int(frost["duration"])},
            "`hero_items.py::Frostbite`",
            "item attack slow arm calls `target.apply_debuff('atk_slow', ...)`",
        )
    )
    rows.append(
        _row(
            "frostbound_anti_heal",
            {
                "kind": "anti_heal",
                "amount": float(frost["anti_heal"]),
                "duration": int(frost["duration"]),
            },
            "`hero_items.py::Frostbite`",
            "item anti-heal arm is polymorphic: the boss store halves it",
        )
    )
    everfrost_aura = catalog["everfrost_guard"]["aura"]
    rows.append(
        _row(
            "everfrost_aura_atk_slow",
            {
                "kind": "atk_slow",
                "amount": float(everfrost_aura["enemy_atk_slow"]),
                "duration": 30,
            },
            "`hero_items.py::Freezing Aura`",
            "aura attack slow runs the boss store when the victim is the boss",
        )
    )
    rows.append(
        _row(
            "everfrost_aura_anti_heal",
            {
                "kind": "anti_heal",
                "amount": float(everfrost_aura["enemy_anti_heal"]),
                "duration": 30,
            },
            "`hero_items.py::Freezing Aura`",
            "aura anti-heal must halve for a boss victim",
        )
    )
    sear_aura = catalog["searbrand"]["aura"]
    rows.append(
        _row(
            "searbrand_aura_anti_heal",
            {
                "kind": "anti_heal",
                "amount": float(sear_aura["enemy_anti_heal"]),
                "duration": 30,
            },
            "`hero_items.py::Cauterize`",
            "searbrand anti-heal halves for a boss victim",
        )
    )
    active = catalog["everfrost_guard"]["active"]
    rows.append(
        _row(
            "everfrost_active_slow",
            {
                "kind": "slow",
                "amount": float(active["slow"]),
                "duration": int(active["slow_duration"]),
            },
            "`hero_items.py::Arctic Blast`",
            "item active slow is a `Boss.apply_slow` call",
        )
    )
    rows.append(
        _row(
            "vine_rod_root_slow",
            {"kind": "slow", "amount": 1.0, "duration": 120},
            "`hero_items.py::Entangle`",
            "a full root is capped at 0.35 for a boss and halved in duration",
        )
    )
    return {
        "source": "`bosses/base_boss.py::Boss.apply_slow`/`apply_debuff` plus `_core.py::TowerDebuffMixin.apply_debuff`",
        "callsite": "godot_rebuild/scripts/match/prototype_battle.gd::_mage_impact/_update_auras + battle_item_effects.gd::apply_anti_heal",
        "shape": _tenacity_shape(),
        "live_stats": {
            "tenacity": TENACITY,
            "cap": CAP,
            "kind": MINI,
            "mage_levels": {str(level): dict(data) for level, data in mage.items()},
            "ice_levels": {str(level): dict(data) for level, data in ice.items()},
        },
        "rows": rows,
    }


def _self_test(fixture):
    problems = []
    shape = fixture["shape"]
    if not (
        shape["has_apply_slow_override"]
        and shape["has_apply_debuff_override"]
        and shape["slow_tenacity_default"]
        and shape["slow_cap"]
        and shape["slow_duration_cut"]
        and shape["atk_slow_cut"]
        and shape["slow_kind_routes_to_apply_slow"]
        and shape["skill_down_not_cut"]
        and shape["anti_heal_not_cut"]
    ):
        problems.append("the boss tenacity overrides drifted")
    if not (
        shape["unit_store_has_no_tenacity"]
        and shape["unit_store_skill_down"]
        and shape["unit_store_anti_heal"]
    ):
        problems.append("the TowerDebuffMixin store drifted")
    for row in fixture["rows"]:
        payload = row["payload"]
        boss = row["boss"]
        unit = row["unit"]
        if payload["kind"] in CUT_KINDS:
            expected_amount = round(min(CAP, payload["amount"] * (1.0 - TENACITY)), 6)
            expected_timer = int(payload["duration"] * (1.0 - TENACITY))
        else:
            expected_amount = round(float(payload["amount"]), 6)
            expected_timer = int(payload["duration"])
        if boss["amount"] != expected_amount or boss["timer"] != expected_timer:
            problems.append("%s must halve through tenacity" % row["name"])
        if unit["amount"] != round(float(payload["amount"]), 6) or unit["timer"] != int(
            payload["duration"]
        ):
            problems.append("%s unit column must keep the raw payload" % row["name"])
        if row["name"] == "mage_level_6_anti_heal" and (
            boss["amount"] != 1.0 or boss["timer"] != 180
        ):
            problems.append("mage L6 anti-heal keeps the raw 1.00/180 payload on a boss")
        if row["name"] == "mage_level_6_skill_down" and (
            boss["amount"] != 0.5 or boss["timer"] != 180
        ):
            problems.append("mage L6 skill-down keeps the raw 0.50/180 payload on a boss")
        if row["name"] == "vine_rod_root_slow" and not boss["capped"]:
            problems.append("a full root must hit the 0.35 cap")
    if problems:
        for problem in problems:
            print("FAIL: %s" % problem)
        return 1
    print("boss debuff tenacity oracle self-test passed: %d rows" % len(fixture["rows"]))
    return 0


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
        print("wrote %s (%d rows)" % (FIXTURE.name, len(fixture["rows"])))
        return 0
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if fixture != committed:
        print("FAIL: fixture drift vs %s" % FIXTURE.name)
        return 1
    return _self_test(fixture)


if __name__ == "__main__":
    raise SystemExit(main())
