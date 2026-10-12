"""Layer 9w oracle: structure bullets land school-free on every victim.

`_entity.py::Bullet._on_hit` (`:242-247`) delivers the impact as

    self.target.take_damage(self.damage, self.team,
                            damage_type='projectile')

- two positional arguments plus the type, no `source=` and no `school=`, so
`resolve_damage_school('projectile', None, None, target_is_hero=False)`
returns `None` (`_entity.py:106-130`; the `'fire'/'ice'/'heal'/'crit'` early-out
does not fire and the `_ACTIVE_HERO` context branch only exists for
`target_is_hero=True`). Consequences for the tower/nexus shot:

* a **minion** victim runs `Minion.take_damage` with `_sch = None`: the armour
  branch (`_sch == 'physical'`) and the `magic_resist` branch
  (`_sch == 'magic'`) are both skipped, so the bullet lands raw
  (`_entity.py:5816-5825`);
* a **hero** victim keeps its armour (the hero armour formula is
  `damage_type != 'fire'` driven, not school driven) but the Wind Wall gate
  reads `self._school`: `_school = None` is **not** `'magic'`, so a mage tower
  bolt is walled too (`_entity.py:4570-4580`);
* the cannon splash arm calls `u.take_damage(int(self.damage * 0.6), self.team)`
  (`:277`) - same sourceless shape, so splash damage is raw as well;
* `credit_hero_damage(None, damage)` records nothing (the ATTACK DAMAGE DEALER
  picker) - the native path already sent no source.

The pre-9w native delivery handed the shooter's declared school
(`"magic" if shot.kind == "mage" else "physical"`) to the target, so troll
armour 2 cut archer bolts, troll `magic_resist` 0.05 cut mage bolts, and the
Wind Wall pre-check (`_hero_blocks_projectile`) let a mage bolt through a live
wall. `--self-test` verifies the executed ladder against the committed fixture;
`--write` is the only fixture writer.
"""

import argparse
import ast
import json
import sys
import textwrap
from pathlib import Path

from hero_veil_immunity_source_oracle import (  # noqa: E402
    _case as _hero_case,
    _run_case as _hero_run_case,
    _take_damage_callable,
)
from minion_damage_ladder_source_oracle import (  # noqa: E402
    _case as _minion_case,
    _run_case as _minion_run_case,
    _minion_take_damage_callable,
)

FIXTURE = Path(__file__).parent / "fixtures/tower_bullet_school_source.json"
ROOT = Path(__file__).resolve().parents[2]
ENTITY = ROOT / "_entity.py"
ARCHER = ROOT / "godot_rebuild/data/structures/archer_level_1.tres"
MAGE = ROOT / "godot_rebuild/data/structures/mage_level_2.tres"
CANNON = ROOT / "godot_rebuild/data/structures/cannon_level_2.tres"
TROLL = ROOT / "godot_rebuild/data/minions/troll.tres"
CATALOG = ROOT / "godot_rebuild/data/ai/item_catalog.json"
ARMOR_ITEM = "steel_aegis"
SPLASH_FRACTION = 0.6


def _tres_number(path, key):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(key + " ="):
            return float(line.split("=", 1)[1].strip())
    raise AssertionError("missing %s in %s" % (key, path))


def _live_stats():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    return {
        "archer_damage": int(_tres_number(ARCHER, "damage")),
        "mage_damage": int(_tres_number(MAGE, "damage")),
        "cannon_damage": int(_tres_number(CANNON, "damage")),
        "troll_armor": int(_tres_number(TROLL, "armor")),
        "troll_magic_resist": _tres_number(TROLL, "magic_resist"),
        "hero_armor": int(catalog["items"][ARMOR_ITEM]["stats"]["armor"]),
    }


def _minion_ladder(payload, *, school, damage_type):
    take_damage, _resolve, _credits = _minion_take_damage_callable()
    case = _minion_case(
        "tower_bullet",
        damage=payload,
        damage_type=damage_type,
        school=school,
        source_school=None,
        armor=int(_live_stats()["troll_armor"]),
        magic_resist=_live_stats()["troll_magic_resist"],
    )
    result = _minion_run_case(take_damage, case)
    return {
        "hp_loss": int(result["hp_loss"]),
        "credited_total": sum(amount for amount, credited in zip(result["credit"], result["credited"]) if credited),
    }


def _hero_ladder(payload, *, school, damage_type, wind_wall, armor):
    take_damage, _credits = _take_damage_callable()
    case = _hero_case(
        "tower_bullet",
        damage=payload,
        damage_type=damage_type,
        school=school,
        source_school=None,
        armor=int(armor),
        wind_wall=bool(wind_wall),
        draws=[0.90],
    )
    result = _hero_run_case(take_damage, case)
    return {
        "hp_loss": int(result["hp_loss"]),
        "credited_total": sum(amount for amount, credited in zip(result["credit"], result["credited"]) if credited)
        if "credit" in result
        else sum(
            amount for credited, amount in ((bool(row[0]), int(row[1])) for row in result["credits"]) if credited
        ),
    }


def _run_row(spec, native_old):
    payload = int(spec["payload"])
    if spec["victim_kind"] == "hero":
        if native_old:
            # Pre-9w native arm: the Wind Wall pre-check ran on the DECLARED
            # school and the ladder then received `school=declared` with
            # `damage_type='projectile'`.
            if bool(spec["wind_wall"]) and spec["declared"] != "magic":
                return {"hp_loss": 0, "credited_total": 0}
            return _hero_ladder(
                payload,
                school=spec["declared"],
                damage_type="projectile",
                wind_wall=spec["wind_wall"],
                armor=spec["hero_armor"],
            )
        # Source arm: `Bullet._on_hit` passes neither source nor school.
        return _hero_ladder(
            payload,
            school=None,
            damage_type="projectile",
            wind_wall=spec["wind_wall"],
            armor=spec["hero_armor"],
        )
    if native_old:
        # Pre-9w native arm: the declared school with the `"normal"` type
        # default of `_deliver_hit`.
        return _minion_ladder(payload, school=spec["declared"], damage_type="normal")
    return _minion_ladder(payload, school=None, damage_type="projectile")


def _take_damage_calls():
    text = ENTITY.read_text(encoding="utf-8")
    tree = ast.parse(text)
    holder = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Bullet")
    calls = []
    for node in ast.walk(holder):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "take_damage":
            continue
        calls.append(
            {
                "args": len(node.args),
                "kwargs": {
                    kw.arg: (kw.value.value if isinstance(kw.value, ast.Constant) else None)
                    for kw in node.keywords
                },
            }
        )
    return calls


def _shape():
    text = ENTITY.read_text(encoding="utf-8")
    tree = ast.parse(text)
    school = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "resolve_damage_school"
    )
    segment = ast.get_source_segment(text, school) or ""
    calls = _take_damage_calls()
    return {
        "bullet_take_damage_calls": len(calls),
        "bullet_two_positional": sum(1 for call in calls if call["args"] == 2),
        "bullet_kwarg_calls": calls,
        "kind_only_projectile_type": any(
            call["kwargs"].get("damage_type") == "projectile" for call in calls
        ),
        "bullet_no_source_kwarg": all("source" not in call["kwargs"] for call in calls),
        "bullet_no_school_kwarg": all("school" not in call["kwargs"] for call in calls),
        "early_out_types": "if damage_type in ('fire', 'ice', 'heal', 'crit'):" in segment,
        "hero_context_requires_target": "if hero is not None and target_hero:" in segment,
    }


def source_fixture():
    stats = _live_stats()
    specs = (
        {
            "name": "archer_bullet_on_troll",
            "victim_kind": "minion",
            "shot": "archer",
            "declared": "physical",
            "payload": stats["archer_damage"],
            "expect_divergence": True,
        },
        {
            "name": "mage_bullet_on_troll",
            "shot": "mage",
            "victim_kind": "minion",
            "declared": "magic",
            "payload": stats["mage_damage"],
            "expect_divergence": True,
        },
        {
            "name": "cannon_splash_on_troll",
            "shot": "cannon",
            "victim_kind": "minion",
            "declared": "physical",
            "payload": int(stats["cannon_damage"] * SPLASH_FRACTION),
            "expect_divergence": True,
        },
        {
            "name": "archer_bullet_on_armoured_hero",
            "shot": "archer",
            "victim_kind": "hero",
            "declared": "physical",
            "payload": stats["archer_damage"],
            "hero_armor": stats["hero_armor"],
            "wind_wall": False,
            "expect_divergence": False,
        },
        {
            "name": "mage_bullet_on_wind_wall_hero",
            "shot": "mage",
            "victim_kind": "hero",
            "declared": "magic",
            "payload": stats["mage_damage"],
            "hero_armor": 0,
            "wind_wall": True,
            "expect_divergence": True,
        },
        {
            "name": "archer_bullet_on_wind_wall_hero",
            "shot": "archer",
            "victim_kind": "hero",
            "declared": "physical",
            "payload": stats["archer_damage"],
            "hero_armor": 0,
            "wind_wall": True,
            "expect_divergence": False,
        },
    )
    cases = []
    for spec in specs:
        row = dict(spec)
        row["hero_armor"] = int(spec.get("hero_armor", 0))
        row["wind_wall"] = bool(spec.get("wind_wall", False))
        row["expected"] = _run_row(spec, native_old=False)
        row["native_old"] = _run_row(spec, native_old=True)
        cases.append(row)
    return {
        "source": (
            "`_entity.py::Bullet._on_hit` main impact and cannon splash, run through the real"
            " `Minion.take_damage` and the real `Hero.take_damage`"
        ),
        "native_old_model": (
            "pre-9w native arm: `_deliver_hit(shot.source_id, shot.team, target, shot.damage,"
            " declared_school, shot.position)` (damage_type `normal`) plus, for heroes, the"
            " `_hero_blocks_projectile(target, declared_school)` pre-check"
        ),
        "callsite": "godot_rebuild/scripts/combat/siege_battle.gd::_update_projectiles",
        "armor_item": ARMOR_ITEM,
        "splash_fraction": SPLASH_FRACTION,
        "live_stats": stats,
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
        if committed.get("live_stats") != fixture.get("live_stats"):
            print("FAIL: live stats drift: %s vs %s" % (committed.get("live_stats"), fixture.get("live_stats")))
        else:
            print("FAIL: fixture drift vs %s" % FIXTURE)
        return 1
    print("tower bullet school oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
