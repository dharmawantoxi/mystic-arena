"""Layer 9u oracle: the Sylara skill arms run school-free.

Every Sylara damage call in `hero_skills/_bundle.py` passes the team only
(`e.take_damage(int(h.skill_damage * ...), h.team)`): the Q line
(`_NS_sylara_skills.cast_q`), the E initial hit and its 15-frame chain tick
(`cast_e` / `update_timers`), and the R powershot release
(`_release_powershot`). Two positional arguments, so `resolve_damage_school`
returns `None`: minion armour/magic resist never cut the skill and a tower
victim keeps its armour out of the hit. The native port sent
`hero.dmg_school` (`sylara.tres` = `"physical"`), which let the troll armour and
the tower armour cut the skill and handed the victim a school the source never
sends.

`--self-test` verifies the executed ladder against the committed fixture;
`--write` is the only fixture writer.
"""

import argparse
import ast
import json
import types
from pathlib import Path

from sylara_source_oracle import ROOT, setup  # noqa: E402
from hero_skill_sourceless_source_oracle import (  # noqa: E402
    _StubTower,
    _tower_take_damage,
)
from minion_damage_ladder_source_oracle import (  # noqa: E402
    _FakeMinion,
    _minion_take_damage_callable,
)

FIXTURE = Path(__file__).parent / "fixtures/sylara_skill_arm_source.json"
HERO_X = 500.0
HERO_Y = 340.0
TROLL_X = 560.0
SHACKLE_X = 600.0
TOWER_ARMOR = 3.0
TROLL_ARMOR = 2
TROLL_MAGIC_RESIST = 0.05
NATIVE_SCHOOL = "physical"


def _minion_case():
    return {
        "name": "sylara_arm",
        "damage": 0,
        "damage_type": "normal",
        "school": None,
        "source_school": None,
        "armor": TROLL_ARMOR,
        "magic_resist": TROLL_MAGIC_RESIST,
        "armor_shred": 0.0,
        "dmg_amp_timer": 0,
        "dmg_amp_amount": 0.0,
    }


def _minion_victim(x):
    take_damage, _resolve, credits = _minion_take_damage_callable()
    victim = _FakeMinion(_minion_case())
    victim.team = "blue"
    victim.x = float(x)
    victim.y = HERO_Y
    victim.attack_timer = 0
    victim.frame = take_damage.__globals__
    victim.ladder = types.MethodType(take_damage, victim)
    victim.credits = credits
    return victim


def _tower_victim(x):
    take_damage, namespace = _tower_take_damage()
    victim = _StubTower(TOWER_ARMOR)
    victim.team = "blue"
    victim.x = float(x)
    victim.y = HERO_Y
    victim.attack_timer = 0
    victim.apply_debuff = lambda *_a, **_k: None
    victim.apply_stun = lambda *_a, **_k: None
    victim.ladder = types.MethodType(take_damage, victim)
    victim.namespace = namespace
    return victim


def _victim(spec):
    if spec["victim_kind"] == "tower":
        return _tower_victim(SHACKLE_X)
    return _minion_victim(TROLL_X if spec["key"] == "q" else SHACKLE_X)


def _credited_total(rows):
    """`credit_hero_damage` skips the credit when `source is None`."""
    return sum(row[1] for row in rows if row[0])


def _run_case(spec, native_old):
    env = setup()
    hero = env["SourceHero"]("sylara", "red", HERO_X, HERO_Y)
    hero.hp = 1000
    victim = _victim(spec)
    observed = []
    real = victim.ladder

    def arm(damage, team, damage_type="normal", source=None, school=None):
        observed.append([int(damage), str(damage_type), school if school else "neutral"])
        if native_old:
            # Pre-9u native argument: the declared `hero.dmg_school`.
            return real(damage, team, "normal", source=None, school=NATIVE_SCHOOL)
        return real(damage, team, damage_type, source=source, school=school)

    victim.take_damage = arm
    hero.target = victim
    units = [] if spec["victim_kind"] == "tower" else [victim]
    towers = [victim] if spec["victim_kind"] == "tower" else []
    credits_before = len(victim.credits.rolls) if hasattr(victim, "credits") else 0
    hp_before = float(victim.hp)
    assert getattr(hero.skills, "cast_" + spec["key"])(units, towers, []), spec["name"]
    for _tick in range(int(spec.get("ticks", 0))):
        hero.skills.update_timers(units, towers, [])
    if hasattr(victim, "credits"):
        rows = [[row[0], row[1]] for row in victim.credits.rolls[credits_before:]]
    else:
        rows = list(victim.namespace["_credits"])
    return {
        "payloads": [row[0] for row in observed],
        "payload_count": len(observed),
        "hp_loss": int(round(hp_before - float(victim.hp))),
        "credited_total": _credited_total(rows),
        "reflect_args": observed,
    }


SCENARIOS = (
    {"name": "q_line_on_troll", "key": "q", "victim_kind": "minion"},
    {"name": "e_shackle_on_troll", "key": "e", "victim_kind": "minion"},
    {"name": "e_shackle_tick_on_troll", "key": "e", "victim_kind": "minion", "ticks": 15},
    {"name": "e_shackle_on_tower", "key": "e", "victim_kind": "tower"},
)


def _shape() -> dict:
    """Every Sylara damage call passes exactly two positional arguments."""
    text = (ROOT / "hero_skills" / "_bundle.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    holder = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "_NS_sylara_skills"
    )
    calls = [
        node
        for node in ast.walk(holder)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "take_damage"
    ]
    return {
        "sylara_take_damage_calls": len(calls),
        "sylara_calls_with_two_positional_args": sum(
            1 for node in calls if len(node.args) == 2
        ),
        "sylara_calls_with_school_kwarg": sum(
            1 for node in calls if any(keyword.arg == "school" for keyword in node.keywords)
        ),
        "sylara_calls_with_source_kwarg": sum(
            1 for node in calls if any(keyword.arg == "source" for keyword in node.keywords)
        ),
        "arms": {
            "q_line": "_NS_sylara_skills.cast_q piercing line",
            "e_shackle": "cast_e initial hit + update_timers chain tick",
            "powershot": "_release_powershot cone",
        },
    }


def source_fixture():
    cases = []
    for spec in SCENARIOS:
        expected = _run_case(spec, native_old=False)
        native_old = _run_case(spec, native_old=True)
        cases.append(
            {
                "name": spec["name"],
                "key": spec["key"],
                "victim_kind": spec["victim_kind"],
                "ticks": int(spec.get("ticks", 0)),
                "expected": expected,
                "native_old": native_old,
            }
        )
    return {
        "source": (
            "hero_skills/_bundle.py::_NS_sylara_skills cast_q / cast_e /"
            " update_timers / _release_powershot via the real Minion.take_damage"
            " / Tower.take_damage"
        ),
        "native_old_model": (
            "pre-9u native port: `world._deliver_hit(-1, hero.team, victim,"
            " payload, hero.dmg_school, hero.position)` with `sylara.tres`"
            " `dmg_school = \"physical\"`"
        ),
        "live_stats": {
            "troll_armor": TROLL_ARMOR,
            "troll_magic_resist": TROLL_MAGIC_RESIST,
            "tower_armor": TOWER_ARMOR,
            "native_school": NATIVE_SCHOOL,
        },
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
        print("FAIL: fixture drift vs %s" % FIXTURE)
        return 1
    print("sylara skill arm oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
