"""9aa: the Miasma tick is a sourceless `take_damage(damage, team, "magic")`.

`hero_items.py::_tick_miasma` (`:209-234`) lands the poison with

    team = getattr(src, "team", None)
    tgt.take_damage(m["damage"], team, "magic")

- three positional arguments, so `"magic"` is the DAMAGE TYPE and the school
stays unresolved: `resolve_damage_school('magic', None, None, target_is_hero)`
falls through the `school`/fire-ice-heal-crit/`source.dmg_school` branches and
returns `None` (`_entity.py:106-130`). Every victim therefore takes the tick
with NO school mitigation at all (tower armour and magic resist, minion
`magic_resist`, boss magic resist), while the non-fire branches still run:

* hero: the armour formula applies (it keys on `damage_type != 'fire'`), the
  damage block section runs and consumes its roll, the Soul Rend amp applies,
  the veil/shadow-realm gates still swallow the tick, and - because there is no
  `source=` - nothing is credited, `notify_damage_taken(source=None)` never
  reflects through Razor Carapace, and a lethal tick leaves `_killed_by` unset;
* minion: the Soul Rend amp and the Corroder shred bonus apply (the source gates
  the shred on `damage_type != 'fire'`), the armour/`magic_resist` cuts do not;
* tower: no mitigation at all, no credit, `_killed_by = None`.

The native bus delivered the same tick with the live owner as source and with
`school="magic"`, which credited the owner, cut unit/structure/boss magic
resist, reflected through the victim's thornmail and attributed kills. Every row
records the executed source ladder (`expected`) plus that pre-9aa model
(`native_old`).

`--self-test` verifies the executed rows and the shape flags; `--write` is the
only fixture writer.
"""

import argparse
import ast
import json
from pathlib import Path

from hero_skill_sourceless_source_oracle import _StubTower, _tower_take_damage
from hero_veil_immunity_source_oracle import _case, _run_case, _take_damage_callable
from minion_damage_ladder_source_oracle import (
    _FakeMinion,
    _case as _minion_case,
    _minion_take_damage_callable,
)

ROOT = Path(__file__).resolve().parents[2]
ITEMS = ROOT / "hero_items.py"
ENTITY = ROOT / "_entity.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "miasma_tick_delivery_source.json"
# One tick of the level-3 Basilisk Breath: 2.2% of 1000 max hp, capped at 60.
PAYLOAD = 30
ARMOR_ITEM = "steel_aegis"
BLOCK_ITEM = "scarlet_bulwark"
CATALOG = ROOT / "godot_rebuild" / "data" / "ai" / "item_catalog.json"
_ITEMS = json.loads(CATALOG.read_text(encoding="utf-8"))["items"]
ARMOR = int(_ITEMS[ARMOR_ITEM]["stats"]["armor"])
BLOCK = _ITEMS[BLOCK_ITEM]["block"]
TROLL_ARMOR = 2.0
TROLL_MAGIC_RESIST = 0.05
TROLL_SHRED = 5.0
TOWER_ARMOR = 3.0


def _norm(text) -> str:
    return str(text).replace("'", '"')


def _tick_shape() -> dict:
    text = ITEMS.read_text(encoding="utf-8")
    tree = ast.parse(text)
    method = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_tick_miasma"
    )
    calls = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "take_damage"
    ]
    primary = next(node for node in calls if len(node.args) == 3)
    fallback = next(node for node in calls if len(node.args) == 2)
    resets = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Assign)
        and _norm(ast.unparse(node.targets[0])) == 'm["tick_cd"]'
        and ast.literal_eval(node.value) == 30
    ]
    drains = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.AugAssign)
        and isinstance(node.op, ast.Sub)
        and _norm(ast.unparse(node.target)) == 'm["timer"]'
    ] + [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.AugAssign)
        and isinstance(node.op, ast.Sub)
        and _norm(ast.unparse(node.target)) == 'm["tick_cd"]'
    ]
    expiries = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.If) and "expired" in ast.unparse(node)
    ]
    return {
        "take_damage_calls": len(calls),
        "primary_three_positional_args": len(primary.args) == 3,
        "damage_is_tracker": _norm(ast.unparse(primary.args[0])) == 'm["damage"]',
        "team_is_source_team": ast.unparse(primary.args[1]) == "team",
        "third_arg_is_magic": ast.literal_eval(primary.args[2]) == "magic",
        "no_source_keyword": all(kw.arg != "source" for kw in primary.keywords),
        "no_school_keyword": all(kw.arg != "school" for kw in primary.keywords),
        "fallback_two_positional": len(fallback.args) == 2
        and _norm(ast.unparse(fallback.args[0])) == 'm["damage"]'
        and ast.unparse(fallback.args[1]) == "team",
        "team_from_stored_source": 'team = getattr(src, "team", None)' in text,
        "tick_reset_is_30": bool(resets),
        "drains_timer_and_tick_cd": len(drains) == 2,
        "expires_dead_or_spent": len(expiries) >= 2,
        "keep_alive_guard": 'if tgt is None or not getattr(tgt, "alive", False)' in text,
    }


def _resolver(school, damage_type, source_none, target_is_hero) -> object:
    """Execute the real `resolve_damage_school` for one call shape."""
    text = ENTITY.read_text(encoding="utf-8")
    tree = ast.parse(text)
    helper = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "resolve_damage_school"
    )
    namespace = {"_ACTIVE_HERO": [None]}
    exec(
        compile(ast.get_source_segment(text, helper), "<entity>", "exec"),
        namespace,
    )
    source = None if source_none else _StubSource(damage_type)
    return namespace["resolve_damage_school"](
        damage_type, source, school, target_is_hero=target_is_hero
    )


class _StubSource:
    def __init__(self, school="magic", team="blue"):
        self.dmg_school = school
        self.team = team
        self.alive = True


def _hero_row(take_damage, *, armor=0, block=None, veil=False, shadow_realm=False, draws=None) -> dict:
    case = _case(
        "miasma_tick",
        damage=PAYLOAD,
        damage_type="magic",
        school=None,
        source_school=None,
        armor=armor,
        block=block,
        veil=veil,
        shadow_realm=shadow_realm,
        draws=draws if draws else [0.9],
    )
    result = _run_case(take_damage, case)
    return {
        "hp_loss": result["hp_loss"],
        "credited_total": sum(row[1] for row in result["credits"] if row[0]),
        "notified": result["notified"],
        "random_draws": result["random_draws"],
        "reflects": result["reflects"],
    }


def _minion_row(raw, *, damage_type="magic", school=None, shred=0.0) -> dict:
    take_damage, _resolve, recorder = _minion_take_damage_callable()
    victim = _FakeMinion(
        _minion_case("miasma", armor=TROLL_ARMOR, magic_resist=TROLL_MAGIC_RESIST, armor_shred=shred)
    )
    recorder.rolls.clear()
    take_damage(victim, raw, "blue", damage_type=damage_type, source=None, school=school)
    return {
        "hp_loss": int(1000 - victim.hp),
        "credited_total": sum(row[1] for row in recorder.rolls if row[0]),
    }


def _minion_schooled_row(raw, *, school) -> dict:
    """Pre-9aa native column: the owner as source and the resolved school."""
    take_damage, _resolve, recorder = _minion_take_damage_callable()
    victim = _FakeMinion(_minion_case("miasma", armor=TROLL_ARMOR, magic_resist=TROLL_MAGIC_RESIST))
    recorder.rolls.clear()
    take_damage(victim, raw, "blue", damage_type="magic", source=_StubSource("magic"), school=school)
    return {
        "hp_loss": int(1000 - victim.hp),
        "credited_total": sum(row[1] for row in recorder.rolls if row[0]),
    }


def _tower_row(raw, *, school, sourced=False) -> dict:
    take_damage, namespace = _tower_take_damage()
    tower = _StubTower(TOWER_ARMOR)
    namespace["_credits"].clear()
    take_damage(
        tower,
        raw,
        "blue",
        damage_type="magic",
        source=_StubSource("magic") if sourced else None,
        school=school,
    )
    return {
        "hp_loss": int(1000.0 - tower.hp),
        "credited_total": sum(row[1] for row in namespace["_credits"] if row[0]),
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
    plain = _hero_row(take_damage)
    armored = _hero_row(take_damage, armor=ARMOR)
    blocked = _hero_row(
        take_damage,
        armor=ARMOR,
        block=[float(BLOCK["chance"]), float(BLOCK["ranged_block"])],
        draws=[0.5],
    )
    veiled = _hero_row(take_damage, veil=True)
    troll = _minion_row(PAYLOAD)
    troll_shred = _minion_row(PAYLOAD, shred=TROLL_SHRED)
    troll_magic = _minion_schooled_row(PAYLOAD, school="magic")
    tower = _tower_row(PAYLOAD, school=None)
    tower_magic = _tower_row(PAYLOAD, school="magic", sourced=True)
    cases = [
        _row(
            "miasma_tick_on_plain_hero",
            case={"damage": PAYLOAD, "damage_type": "magic", "school": None, "source_school": None},
            expected=plain,
            native_old=dict(plain, credited_total=plain["hp_loss"]),
            note="the native bus credited the owner the landed amount",
        ),
        _row(
            "miasma_tick_on_armoured_hero",
            case={
                "damage": PAYLOAD,
                "damage_type": "magic",
                "school": None,
                "source_school": None,
                "armor": ARMOR,
            },
            expected=armored,
            native_old=dict(armored, credited_total=armored["hp_loss"]),
            note="the hero armour formula keys on damage_type, so it still applies",
        ),
        _row(
            "miasma_tick_with_block_item",
            case={
                "damage": PAYLOAD,
                "damage_type": "magic",
                "school": None,
                "source_school": None,
                "armor": ARMOR,
                "armor_from_block_item": True,
                "block": [float(BLOCK["chance"]), float(BLOCK["ranged_block"])],
                "draws": [0.5],
            },
            expected=blocked,
            native_old=dict(blocked, credited_total=blocked["hp_loss"]),
            note="a non-fire tick still rolls the passive ranged block after the item armour",
        ),
        _row(
            "miasma_tick_on_veiled_hero",
            case={"damage": PAYLOAD, "damage_type": "magic", "school": None, "source_school": None, "veil": True},
            expected=veiled,
            native_old=dict(veiled, credited_total=veiled["hp_loss"]),
            note="the veil gate returns before mitigation, so the tick lands nothing",
        ),
        _row(
            "miasma_tick_on_troll",
            case={"damage": PAYLOAD, "damage_type": "magic", "school": None, "armor": TROLL_ARMOR},
            expected=troll,
            native_old=dict(troll_magic, credited_total=troll_magic["credited_total"]),
            note="no school means the troll magic_resist never cuts the tick",
        ),
        _row(
            "miasma_tick_on_shredded_troll",
            case={
                "damage": PAYLOAD,
                "damage_type": "magic",
                "school": None,
                "armor": TROLL_ARMOR,
                "shred": TROLL_SHRED,
            },
            expected=troll_shred,
            native_old=dict(troll_shred),
            note="the Corroder shred bonus is not gated on the school",
        ),
        _row(
            "miasma_tick_on_tower",
            case={"damage": PAYLOAD, "damage_type": "magic", "school": None, "armor": TOWER_ARMOR},
            expected=tower,
            native_old=dict(tower_magic),
            note="the tower magic branch needed a resolved school, which the source never provides",
        ),
    ]
    return {
        "source": "`hero_items.py::_tick_miasma` run through the real `Hero.take_damage`, `Minion.take_damage` and `Tower.take_damage`",
        "callsite": "godot_rebuild/scripts/match/battle_item_effects.gd::deal_damage_from",
        "caller": "godot_rebuild/scripts/match/hero_item_inventory.gd::tick_miasma",
        "native_model": "the tick reaches the bus as `deal_damage_from(..., \"neutral\", \"magic\")`: the owner id stays only for the boss replay handle (9b/9d) while every other victim is delivered sourceless",
        "tick_shape": _tick_shape(),
        "hero_shape": {
            "non_fire_guard_count": 0,
            "armor_keys_on_damage_type": True,
            "block_inside_non_fire": True,
        },
        "live_stats": {
            "payload": PAYLOAD,
            "armor_item": ARMOR_ITEM,
            "armor": ARMOR,
            "block_item": BLOCK_ITEM,
            "block_chance": float(BLOCK["chance"]),
            "block_amount": float(BLOCK["melee_block"]),
            "troll_armor": TROLL_ARMOR,
            "troll_magic_resist": TROLL_MAGIC_RESIST,
            "troll_shred": TROLL_SHRED,
            "troll_shred_payload": troll_shred["hp_loss"],
            "tower_armor": TOWER_ARMOR,
            "school_resolution": {
                "tick_school_for_hero": _resolver(None, "magic", True, True),
                "tick_school_for_minion": _resolver(None, "magic", True, False),
                "tick_school_with_active_hero": _resolver(None, "magic", True, True),
            },
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
    shape = fixture["tick_shape"]
    if shape["take_damage_calls"] != 2 or not (
        shape["primary_three_positional_args"]
        and shape["third_arg_is_magic"]
        and shape["damage_is_tracker"]
        and shape["team_is_source_team"]
        and shape["no_source_keyword"]
        and shape["no_school_keyword"]
        and shape["fallback_two_positional"]
        and shape["team_from_stored_source"]
        and shape["tick_reset_is_30"]
        and shape["drains_timer_and_tick_cd"]
        and shape["expires_dead_or_spent"]
        and shape["keep_alive_guard"]
    ):
        problems.append("the source miasma tick call shape drifted")
    resolution = fixture["live_stats"]["school_resolution"]
    for key, value in resolution.items():
        if value is not None:
            problems.append("the sourceless tick resolved the school %s = %r" % (key, value))
    rows = {row["name"]: row for row in fixture["cases"]}
    for name in (
        "miasma_tick_on_plain_hero",
        "miasma_tick_on_armoured_hero",
        "miasma_tick_with_block_item",
        "miasma_tick_on_veiled_hero",
        "miasma_tick_on_troll",
        "miasma_tick_on_shredded_troll",
        "miasma_tick_on_tower",
    ):
        if name not in rows:
            problems.append("%s is missing" % name)
    for row in fixture["cases"]:
        label = row["name"]
        expected = row["expected"]
        if expected.get("credited_total") != 0:
            problems.append("%s must not credit the owner" % label)
        if label != "miasma_tick_on_troll" and "notified" in expected and expected["notified"] != 1:
            if label != "miasma_tick_on_veiled_hero":
                problems.append("%s must notify the item hook once" % label)
    if rows["miasma_tick_on_veiled_hero"]["expected"]["hp_loss"] != 0:
        problems.append("the veil row must land nothing")
    if rows["miasma_tick_on_troll"]["expected"]["hp_loss"] != PAYLOAD:
        problems.append("the trol row must stay unmitigated")
    if rows["miasma_tick_on_troll"]["native_old"]["hp_loss"] >= PAYLOAD:
        problems.append("the pre-9aa trol column must show the magic-resist cut")
    if rows["miasma_tick_with_block_item"]["expected"]["random_draws"] != 1:
        problems.append("the block row must consume exactly one roll")
    if problems:
        for row in problems:
            print("FAIL: %s" % row)
        return 1
    print("miasma tick delivery oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
