"""Layer 9v oracle: the Grimjaw R immediate hit is school-free.

`_NS_grimjaw_skills.cast_r` locks the current target with
`h.target.take_damage(int(h.skill_damage * 2.5), h.team)` - two positional
arguments, no `source=` and no `school=` - so `resolve_damage_school` returns
`None` (`_entity.py:106-130`): the minion armour never cuts the opening hit, a
tower victim keeps its armour out of it, and `credit_hero_damage(None, ...)`
records nothing. The native port already passed `-1` (no credit) but kept
`hero.dmg_school` (`grimjaw.tres` = `"physical"`), so troll armour 2 and the
archer tower armour 3 cut a hit the source never cuts.

The rest of the kit is already paritas and is pinned as a control: the Blade
Fury spin tick (`e.take_damage(h.skill_damage, h.team, source=h)`), the
Omnislash follow-up ticks, the E cone and the R fallback AOE all pass
`source=self.hero` with `school=getattr(hero, "dmg_school", None)`, which is
exactly the native delivery.

`--self-test` verifies the executed ladder against the committed fixture;
`--write` is the only fixture writer.
"""

import argparse
import json
import types
from pathlib import Path

from kaizen_source_oracle import build_hero_env  # noqa: E402
from hero_skill_sourceless_source_oracle import (  # noqa: E402
    _StubTower,
    _tower_take_damage,
)
from minion_damage_ladder_source_oracle import (  # noqa: E402
    _FakeMinion,
    _minion_take_damage_callable,
)
from hero_veil_immunity_source_oracle import (  # noqa: E402
    _FakeHero,
    _case,
    _take_damage_callable,
)

FIXTURE = Path(__file__).parent / "fixtures/grimjaw_skill_arm_source.json"
HERO_X = 500.0
HERO_Y = 340.0
TARGET_X = 560.0
TOWER_X = 540.0
TOWER_ARMOR = 3.0
TROLL_ARMOR = 2
HERO_ARMOR = 6
ARMOR_ITEM = "steel_aegis"
NATIVE_SCHOOL = "physical"


def _minion_case():
    return {
        "name": "grimjaw_arm",
        "damage": 0,
        "damage_type": "normal",
        "school": None,
        "source_school": None,
        "armor": TROLL_ARMOR,
        "magic_resist": 0.0,
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
    victim.apply_debuff = lambda *_a, **_k: None
    victim.apply_stun = lambda *_a, **_k: None
    victim.ladder = types.MethodType(take_damage, victim)
    victim.namespace = namespace
    return victim


def _hero_victim(x, armor):
    take_damage, _credits = _take_damage_callable()
    victim = _FakeHero(_case("grimjaw_arm", armor=int(armor), draws=[0.9]))
    victim.team = "blue"
    victim.x = float(x)
    victim.y = HERO_Y
    victim.frame = take_damage.__globals__
    victim.ladder = types.MethodType(take_damage, victim)
    return victim


def _victim(spec):
    kind = spec["victim_kind"]
    if kind == "tower":
        return _tower_victim(TOWER_X)
    if kind == "hero":
        return _hero_victim(TARGET_X, spec.get("hero_armor", 0))
    return _minion_victim(TARGET_X)


def _credit_rows(victim, credits_before):
    """Credit record of the victim, whatever ladder it runs."""
    if hasattr(victim, "credits"):
        return [[row[0], row[1]] for row in victim.credits.rolls[credits_before:]]
    if hasattr(victim, "namespace"):
        return list(victim.namespace["_credits"])
    return [[row[0], row[1]] for row in victim.frame["_recorder"].rolls]


def _credited_total(rows):
    """`credit_hero_damage` skips the credit when `source is None`."""
    return sum(row[1] for row in rows if row[0])


def _run_case(spec, native_old):
    env = build_hero_env()
    hero = env["SourceHero"]("grimjaw", "red", HERO_X, HERO_Y)
    hero.hp = 1000
    victim = _victim(spec)
    if spec["victim_kind"] == "hero":
        # Mirror the native armour item so both columns run the same ladder.
        victim.items.armor = int(spec.get("hero_armor", 0))
    observed = []
    real = victim.ladder

    def arm(damage, team, damage_type="normal", source=None, school=None):
        observed.append([int(damage), str(damage_type), school if school else "neutral"])
        if native_old:
            # Pre-9v native arguments: the declared `hero.dmg_school`, and the
            # dealing hero as source only for the arms that already passed one.
            return real(
                damage,
                team,
                "normal",
                source=hero if bool(spec.get("sourced", False)) else None,
                school=NATIVE_SCHOOL,
            )
        return real(damage, team, damage_type, source=source, school=school)

    victim.take_damage = arm
    hero.target = victim
    units = [victim] if spec["victim_kind"] != "tower" else []
    towers = [victim] if spec["victim_kind"] == "tower" else []
    credits_before = len(victim.credits.rolls) if hasattr(victim, "credits") else 0
    hp_before = float(victim.hp)
    assert getattr(hero.skills, "cast_" + spec["key"])(units, towers, []), spec["name"]
    for _tick in range(int(spec.get("ticks", 0))):
        hero.skills.update_timers(units, towers, [])
    rows = _credit_rows(victim, credits_before)
    return {
        "payloads": [row[0] for row in observed],
        "payload_count": len(observed),
        "hp_loss": int(round(hp_before - float(victim.hp))),
        "credited_total": _credited_total(rows),
        "reflect_args": observed,
    }


SCENARIOS = (
    {
        "name": "r_immediate_on_troll",
        "key": "r",
        "victim_kind": "minion",
        "sourced": False,
        "expect_divergence": True,
    },
    {
        "name": "r_immediate_on_tower",
        "key": "r",
        "victim_kind": "tower",
        "sourced": False,
        "expect_divergence": True,
    },
    {
        "name": "r_immediate_on_armoured_hero",
        "key": "r",
        "victim_kind": "hero",
        "hero_armor": HERO_ARMOR,
        "sourced": False,
        # Hero armour is damage-type driven (layer 9l), so the hero victim keeps
        # its cut in both columns: a control that the school fix changes nothing
        # there.
        "expect_divergence": False,
    },
    {
        "name": "blade_fury_tick_on_troll",
        "key": "q",
        "victim_kind": "minion",
        "ticks": 165,
        "sourced": True,
    },
    {"name": "e_cone_on_troll", "key": "e", "victim_kind": "minion", "sourced": True},
)


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
                "hero_armor": int(spec.get("hero_armor", 0)),
                "ticks": int(spec.get("ticks", 0)),
                "sourced": bool(spec.get("sourced", False)),
                "expect_divergence": bool(spec.get("expect_divergence", False)),
                "expected": expected,
                "native_old": native_old,
            }
        )
    return {
        "source": (
            "hero_skills/_bundle.py::_NS_grimjaw_skills cast_r locked-target hit"
            " / cast_q / cast_e / update_timers via the real Minion.take_damage /"
            " Tower.take_damage / Hero.take_damage"
        ),
        "native_old_model": (
            "pre-9v native port: `world._deliver_hit(-1, hero.team, victim,"
            " payload, hero.dmg_school, hero.position)` - already uncredited,"
            " but still physical"
        ),
        "live_stats": {
            "troll_armor": TROLL_ARMOR,
            "tower_armor": TOWER_ARMOR,
            "hero_armor": HERO_ARMOR,
            "native_school": NATIVE_SCHOOL,
        },
        "armor_item": ARMOR_ITEM,
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
    print("grimjaw skill arm oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
