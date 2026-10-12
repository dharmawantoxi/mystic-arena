"""9z: the burn tick is a fire hit through the victim's `take_damage` ladder.

`_core.py::TowerDebuffMixin._tick_tower_debuffs` accumulates
`burn_dps / TOWER_DEBUFF_FPS` every frame and, once per
`TOWER_DEBUFF_BURN_TICK` (30) frames, runs

    self.burn_accum -= dmg
    self.take_damage(dmg, self.burn_team or self.team, "fire")

- three positional arguments, no `source=` and no `school=`. The victim
therefore runs its WHOLE ladder at `damage_type='fire'`, `source=None`:

* a hero under Tempest Veil or Shadow Realm takes NOTHING (both return before
  the mitigation section),
* the Soul Rend amp applies (`_entity.py:4638-4642`),
* the damage block section is skipped, because it is nested inside the
  non-fire branch (`_entity.py:4644-4675`) - so a fire tick rolls neither the
  passive block nor the Bulwark Guard aura,
* Bristleback keeps 30% (fire is not the magic school),
* `notify_damage_taken(damage, source=None)` fires (Leviathan timer, Static
  Charge roll) but never reflects,
* `credit_hero_damage(None, ...)` credits nobody, and a lethal tick leaves
  `_killed_by = None`.

The native `_tick_burn` used to subtract hp directly and only emulated the
shadow realm by hand, so every other gate above was skipped. Every row records
the executed source ladder (`expected`) plus that pre-9z raw column
(`native_old`), so the suite can assert both the new value and the divergence.

`--self-test` verifies the executed rows and the shape flags; `--write` is the
only fixture writer.
"""

import argparse
import ast
import json
from pathlib import Path

from hero_veil_immunity_source_oracle import _case, _run_case, _take_damage_callable
from minion_damage_ladder_source_oracle import (
    _FakeMinion,
    _case as _minion_case,
    _minion_take_damage_callable,
)

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "_core.py"
ENTITY = ROOT / "_entity.py"
CATALOG = ROOT / "godot_rebuild" / "data" / "ai" / "item_catalog.json"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "burn_tick_delivery_source.json"
# One tick of a 60 dps burn: 60 / 60 fps * 30 frames.
DPS = 60.0
TICK_FRAMES = 30
PAYLOAD = int(DPS / 60.0 * TICK_FRAMES)
# The Bulwark Guard / passive block item (`scarlet_bulwark`), used to prove the
# fire branch skips the block section.
BLOCK_ITEM = "scarlet_bulwark"
BLOCK = json.loads(CATALOG.read_text(encoding="utf-8"))["items"][BLOCK_ITEM]["block"]
TROLL_ARMOR = 2.0
TROLL_MAGIC_RESIST = 0.05
TROLL_SHRED = 5.0


def _burn_shape() -> dict:
    text = CORE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    holder = next(
        node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "TowerDebuffMixin"
    )
    method = next(
        node for node in holder.body if isinstance(node, ast.FunctionDef) and node.name == "_tick_tower_debuffs"
    )
    calls = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "take_damage"
    ]
    call = calls[0]
    drained = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.AugAssign)
        and isinstance(node.op, ast.Sub)
        and ast.unparse(node.target) == "self.burn_accum"
    ]
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ("TOWER_DEBUFF_BURN_TICK", "TOWER_DEBUFF_FPS"):
                constants[node.targets[0].id] = ast.literal_eval(node.value)
    return {
        "take_damage_calls": len(calls),
        "three_positional_args": len(call.args) == 3,
        "damage_is_accum": ast.unparse(call.args[0]) == "dmg",
        "team_is_burn_team_or_team": ast.unparse(call.args[1]) == "self.burn_team or self.team",
        "third_arg_is_fire": ast.literal_eval(call.args[2]) == "fire",
        "no_source_keyword": all(kw.arg != "source" for kw in call.keywords),
        "no_school_keyword": all(kw.arg != "school" for kw in call.keywords),
        "accum_drained_before": bool(drained) and drained[0].lineno < call.lineno,
        "guarded_by_alive": "alive" in ast.unparse(method),
        "burn_tick_interval": int(constants["TOWER_DEBUFF_BURN_TICK"]),
        "burn_fps": float(constants["TOWER_DEBUFF_FPS"]),
    }


def _hero_fire_shape() -> dict:
    """The source nests the block section inside the non-fire branch."""
    text = ENTITY.read_text(encoding="utf-8")
    tree = ast.parse(text)
    holder = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Hero")
    method = next(
        node for node in holder.body if isinstance(node, ast.FunctionDef) and node.name == "take_damage"
    )
    guards = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.If) and "damage_type != 'fire'" in ast.unparse(node.test)
    ]
    inside = [
        node
        for node in ast.walk(guards[0])
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "get_block"
    ]
    bristle = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.If) and "_bristleback_active" in ast.unparse(node.test)
    ]
    return {
        "non_fire_guard_count": len(guards),
        "block_roll_inside_non_fire": bool(inside),
        "bristleback_keep_outside_non_fire": bool(bristle)
        and ast.unparse(bristle[0]).find("_bristleback_active") >= 0,
        "keep_is_not_magic_gated": "self._school != 'magic'" in ast.unparse(bristle[0]),
    }


def _minion_row(raw, *, damage_type, school, shred=TROLL_SHRED) -> dict:
    take_damage, _resolve, recorder = _minion_take_damage_callable()
    victim = _FakeMinion(
        _minion_case("burn", armor=TROLL_ARMOR, magic_resist=TROLL_MAGIC_RESIST, armor_shred=shred)
    )
    recorder.rolls.clear()
    take_damage(victim, raw, "blue", damage_type=damage_type, source=None, school=school)
    return {
        "hp_loss": int(1000 - victim.hp),
        "credited_total": sum(row[1] for row in recorder.rolls if row[0]),
    }


def _hero_row(take_damage, **overrides) -> dict:
    case = _case("burn_tick", **overrides)
    result = _run_case(take_damage, case)
    return {
        "hp_loss": result["hp_loss"],
        "credited_total": sum(row[1] for row in result["credits"] if row[0]),
        "notified": result["notified"],
        "random_draws": result["random_draws"],
        "reflects": result["reflects"],
    }


def _row(name, *, expected, native_old, case, note) -> dict:
    return {
        "name": name,
        "case": case,
        "note": note,
        "expected": expected,
        "native_old": native_old,
    }


def source_fixture() -> dict:
    take_damage, _credits = _take_damage_callable()
    fire = {"damage": PAYLOAD, "damage_type": "fire", "school": None, "source_school": None}
    amp = _hero_row(take_damage, **fire, dmg_amp_timer=120, dmg_amp_amount=0.5)
    keep = _hero_row(take_damage, **fire, bristleback=True)
    veiled = _hero_row(take_damage, **fire, veil=True)
    realm = _hero_row(take_damage, **fire, shadow_realm=True)
    blocked = _hero_row(take_damage, **fire, block=[float(BLOCK["chance"]), float(BLOCK["melee_block"])], draws=[0.1])
    troll_fire = _minion_row(PAYLOAD, damage_type="fire", school=None)
    troll_normal = _minion_row(PAYLOAD, damage_type="normal", school=None)
    raw_old = {
        "hp_loss": PAYLOAD,
        "credited_total": 0,
        "notified": 0,
        "random_draws": 0,
        "reflects": 0,
    }
    cases = [
        _row(
            "burn_tick_on_amped_hero",
            case=dict(fire, dmg_amp_timer=120, dmg_amp_amount=0.5),
            expected=amp,
            native_old=dict(raw_old),
            note="the Soul Rend amp runs before the fire branch, the raw column never applied it",
        ),
        _row(
            "burn_tick_on_bristleback_hero",
            case=dict(fire, bristleback=True),
            expected=keep,
            native_old=dict(raw_old),
            note="Bristleback keeps 30% because fire is not the magic school",
        ),
        _row(
            "burn_tick_on_veiled_hero",
            case=dict(fire, veil=True),
            expected=veiled,
            native_old=dict(raw_old),
            note="Tempest Veil returns before the mitigation section, so the tick lands nothing",
        ),
        _row(
            "burn_tick_on_shadow_realm_hero",
            case=dict(fire, shadow_realm=True),
            expected=realm,
            native_old=dict(raw_old, hp_loss=0),
            note="Shadow Realm already returned in the raw column: control row",
        ),
        _row(
            "burn_tick_with_block_item",
            case=dict(fire, block=[float(BLOCK["chance"]), float(BLOCK["melee_block"])], draws=[0.1]),
            expected=blocked,
            native_old=dict(raw_old),
            note="the block section is nested in the non-fire branch, so fire consumes no draw",
        ),
        _row(
            "burn_tick_on_troll",
            case=dict(damage=PAYLOAD, damage_type="fire", school=None, armor=TROLL_ARMOR),
            expected=troll_fire,
            native_old=dict(raw_old, credited_total=0),
            note="minion control: fire skips armour and magic_resist, and the Corroder bonus",
        ),
    ]
    return {
        "source": "`_core.py::TowerDebuffMixin._tick_tower_debuffs` burn branch run through the real `Hero.take_damage` and `Minion.take_damage`",
        "callsite": "godot_rebuild/scripts/combat/minion_battle.gd::_tick_burn",
        "native_old_model": "pre-9z native raw arm: `unit.hp = maxf(0, unit.hp - damage)` (+ a hand-rolled shadow-realm zero), recorded as the `native_old` column",
        "burn_shape": _burn_shape(),
        "hero_fire_shape": _hero_fire_shape(),
        "live_stats": {
            "dps": DPS,
            "tick_frames": TICK_FRAMES,
            "payload": PAYLOAD,
            "block_item": BLOCK_ITEM,
            "block_chance": float(BLOCK["chance"]),
            "block_amount": float(BLOCK["melee_block"]),
            "ranged_block_amount": float(BLOCK["ranged_block"]),
            "troll_armor": TROLL_ARMOR,
            "troll_magic_resist": TROLL_MAGIC_RESIST,
            "troll_shred": TROLL_SHRED,
            "troll_shred_payload": troll_normal["hp_loss"],
            "amped_payload": amp["hp_loss"],
            "bristleback_payload": keep["hp_loss"],
        },
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
    problems = []
    if fixture != committed:
        problems.append("fixture drift vs %s" % FIXTURE.name)
    shape = fixture["burn_shape"]
    if shape["take_damage_calls"] != 1 or not (
        shape["three_positional_args"]
        and shape["third_arg_is_fire"]
        and shape["team_is_burn_team_or_team"]
        and shape["damage_is_accum"]
        and shape["no_source_keyword"]
        and shape["no_school_keyword"]
        and shape["accum_drained_before"]
    ):
        problems.append("the source burn call shape drifted")
    if shape["burn_tick_interval"] != TICK_FRAMES or shape["burn_fps"] != 60.0:
        problems.append("the source burn interval constants drifted")
    fire_shape = fixture["hero_fire_shape"]
    if not fire_shape["block_roll_inside_non_fire"]:
        problems.append("the hero block section is no longer nested in the non-fire branch")
    for row in fixture["cases"]:
        label = row["name"]
        expected = row["expected"]
        old = row["native_old"]
        if label == "burn_tick_on_veiled_hero" and expected["hp_loss"] != 0:
            problems.append("%s must land nothing" % label)
        if label == "burn_tick_on_shadow_realm_hero" and expected["hp_loss"] != 0:
            problems.append("%s must land nothing" % label)
        if label == "burn_tick_on_amped_hero" and expected["hp_loss"] <= PAYLOAD:
            problems.append("%s must record the amp" % label)
        if label == "burn_tick_on_bristleback_hero" and expected["hp_loss"] >= PAYLOAD:
            problems.append("%s must record the keep" % label)
        if label == "burn_tick_with_block_item" and (
            expected["hp_loss"] != PAYLOAD or expected["random_draws"] != 0
        ):
            problems.append("%s must skip the block section" % label)
        if label == "burn_tick_on_troll":
            # The minion ladder exposes no notify/draw columns: the control row
            # only has to keep the pre-9z numbers.
            if expected["hp_loss"] != old["hp_loss"] or expected["credited_total"] != old["credited_total"]:
                problems.append("%s is the unchanged minion control" % label)
            continue
        for key in ("hp_loss", "credited_total", "notified", "random_draws", "reflects"):
            if key not in expected or key not in old:
                problems.append("%s is missing the %s column" % (label, key))
    if problems:
        for row in problems:
            print("FAIL: %s" % row)
        return 1
    print("burn tick delivery oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
