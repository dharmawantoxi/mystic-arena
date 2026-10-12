"""9n: source oracle for the MINION damage ladder of `Minion.take_damage`.

`Minion.take_damage` (`_entity.py:5795-5825`) runs

    _sch = resolve_damage_school(damage_type, source, school, target_is_hero=False)
    if damage > 0:
        if self.dmg_amp_timer > 0:
            damage = int(round(damage * (1.0 + self.dmg_amp_amount)))
        shred = getattr(self, "armor_shred_amount", 0.0)
        if damage_type != 'fire' and shred > 0:
            damage = int(round(damage * (1.0 + min(1.0, shred * 0.06))))
        armor = self.armor - shred
        if _sch == 'physical' and armor != 0:  ...armour formula...
        elif _sch == 'magic' and self.magic_resist > 0:  ...MR cut...

so the Soul Rend amp and the Corroder shred bonus both scale the hit BEFORE the
school mitigation, the shred is subtracted from the armour a second time, and a
school-free hit still keeps the amp (only the mitigation branch needs a school).

The native build (layer 5b-3) instead resolved the school mitigation first,
applied the amp afterwards, returned the raw number for `neutral` and had no
shred bonus at all. Every row records the executed source ladder (`expected`,
plus the school the source resolver picked) next to that pre-9n native model
(`native_old`), so the suite can assert both the new value and the divergence.

`--self-test` verifies the executed ladder against the committed fixture;
`--write` is the only fixture writer.
"""
import argparse
import ast
import json
from pathlib import Path

from hero_veil_immunity_source_oracle import (
    _exec,
    _function_node,
    _method_node,
    _source_text,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "minion_damage_ladder_source.json"
# Live minion stats used by the base rows: troll armour and undead resistance.
TROLL_ARMOR = 2
UNDEAD_MAGIC_RESIST = 0.15


def _round_like_python(value: float) -> int:
    lower = int(value // 1)
    fraction = value - lower
    if fraction == 0.5:
        return lower if lower % 2 == 0 else lower + 1
    return lower + 1 if fraction > 0.5 else lower


def _armor_formula(raw: int, armor: float) -> int:
    if raw <= 0:
        return 0
    if armor > 0:
        reduction = armor * 0.06 / (1.0 + armor * 0.06)
        return max(1, _round_like_python(raw * (1.0 - reduction)))
    if armor < 0:
        return _round_like_python(raw * (1.0 + min(1.0, -armor * 0.06)))
    return raw


class _FakeMinion:
    """Stub victim for the real `Minion.take_damage` body."""

    def __init__(self, case):
        self.armor = float(case["armor"])
        self.magic_resist = float(case["magic_resist"])
        self.armor_shred_amount = float(case["armor_shred"])
        self.dmg_amp_timer = int(case["dmg_amp_timer"])
        self.dmg_amp_amount = float(case["dmg_amp_amount"])
        self.hp = 1000
        self.max_hp = 1000
        self.radius = 12
        self.x = 0.0
        self.y = 0.0
        self.team = "blue"
        self.alive = True

    def clear_tower_debuffs(self):
        return None


def _minion_take_damage_callable():
    """Compile the real `Minion.take_damage` body into a plain callable."""
    text = _source_text()
    tree = ast.parse(text)
    method = _method_node(tree, "Minion", "take_damage")
    helpers = [_function_node(tree, "resolve_damage_school")]

    class _Recorder:
        def __init__(self):
            self.rolls = []

        def __call__(self, source, damage):
            self.rolls.append([source is not None, int(damage)])

    credits = _Recorder()
    namespace = {
        "credit_hero_damage": lambda source, damage: credits(source, damage),
        "_ACTIVE_HERO": [None],
        "_recorder": credits,
        "SoundManager": lambda: type("S", (), {"play": lambda *a, **k: None})(),
    }
    for node in helpers:
        _exec(ast.get_source_segment(text, node), namespace)
    _exec(ast.get_source_segment(text, method), namespace)
    return namespace["take_damage"], namespace["resolve_damage_school"], credits


def _case(name, **overrides):
    case = {
        "name": name,
        "damage": 200,
        "damage_type": "normal",
        "school": None,
        "source_school": None,
        "armor": 0,
        "magic_resist": 0.0,
        "armor_shred": 0.0,
        "dmg_amp_timer": 0,
        "dmg_amp_amount": 0.0,
    }
    case.update(overrides)
    return case


def _run_case(take_damage, case):
    minion = _FakeMinion(case)
    hp_before = minion.hp
    attacker = None
    if case["source_school"] is not None:
        attacker = _FakeMinion(case)
        attacker.dmg_school = case["source_school"]
    frame = take_damage.__globals__
    credits_before = len(frame["_recorder"].rolls)
    take_damage(
        minion,
        int(case["damage"]),
        "red",
        damage_type=case["damage_type"],
        source=attacker,
        school=case["school"],
    )
    credits = frame["_recorder"].rolls[credits_before:]
    return {
        "hp_loss": int(hp_before - minion.hp),
        "hp_after": int(minion.hp),
        "credit": [row[1] for row in credits],
        "credited": [row[0] for row in credits],
    }


def _resolved_school(resolve_damage_school, case):
    attacker = None
    if case["source_school"] is not None:
        attacker = _FakeMinion(case)
        attacker.dmg_school = case["source_school"]
    return resolve_damage_school(
        damage_type=case["damage_type"],
        source=attacker,
        school=case["school"],
        target_is_hero=False,
    )


def _native_old_loss(case, school) -> int:
    """Pre-9n native model: school mitigation first, amp after, neutral raw."""
    raw = int(case["damage"])
    if raw <= 0:
        return 0
    if school is None:
        return raw
    armor = float(case["armor"]) - float(case["armor_shred"])
    if school == "physical":
        loss = _armor_formula(raw, armor)
    elif float(case["magic_resist"]) > 0:
        loss = max(1, _round_like_python(raw * (1.0 - float(case["magic_resist"]))))
    else:
        loss = raw
    if int(case["dmg_amp_timer"]) > 0 and loss > 0:
        loss = _round_like_python(loss * (1.0 + float(case["dmg_amp_amount"])))
    return max(0, loss)


CASES = [
    _case(
        "physical_live_armor_control",
        school="physical",
        source_school="physical",
        armor=TROLL_ARMOR,
    ),
    _case(
        "magic_live_resist_control",
        school="magic",
        source_school="magic",
        armor=0,
        magic_resist=UNDEAD_MAGIC_RESIST,
    ),
    _case("neutral_amp_only", dmg_amp_timer=240, dmg_amp_amount=0.5),
    _case(
        "physical_amp_then_armor",
        school="physical",
        source_school="physical",
        armor=TROLL_ARMOR,
        dmg_amp_timer=240,
        dmg_amp_amount=0.3,
    ),
    _case(
        "physical_shred_bonus_then_armor",
        school="physical",
        source_school="physical",
        armor=TROLL_ARMOR,
        armor_shred=5.0,
    ),
    _case(
        "magic_amp_shred_then_resist",
        school="magic",
        source_school="magic",
        magic_resist=UNDEAD_MAGIC_RESIST,
        armor_shred=5.0,
        dmg_amp_timer=240,
        dmg_amp_amount=0.3,
    ),
    _case(
        "fire_keeps_armor_skips_shred_bonus",
        damage_type="fire",
        school="physical",
        source_school="physical",
        armor=TROLL_ARMOR,
        armor_shred=5.0,
    ),
    _case(
        "neutral_amp_and_shred",
        armor=6,
        armor_shred=5.0,
        dmg_amp_timer=240,
        dmg_amp_amount=0.2,
    ),
    _case(
        "magic_ignores_armor",
        school="magic",
        source_school="magic",
        armor=6.0,
    ),
]


def source_fixture() -> dict:
    take_damage, resolve_damage_school, _credits = _minion_take_damage_callable()
    rows = []
    for case in CASES:
        expected = _run_case(take_damage, case)
        school = _resolved_school(resolve_damage_school, case)
        rows.append(
            {
                "name": case["name"],
                "damage": int(case["damage"]),
                "damage_type": case["damage_type"],
                "school": case["school"],
                "source_school": case["source_school"],
                "resolved_school": school,
                "armor": float(case["armor"]),
                "magic_resist": float(case["magic_resist"]),
                "armor_shred": float(case["armor_shred"]),
                "dmg_amp_timer": int(case["dmg_amp_timer"]),
                "dmg_amp_amount": float(case["dmg_amp_amount"]),
                "expected": expected,
                "native_old": {"hp_loss": _native_old_loss(case, school)},
            }
        )
    return {
        "source": "_entity.py::Minion.take_damage amp+shred+school section :5795-5825",
        "native_old_model": (
            "pre-9n native: school mitigation with the effective armour first,"
            " amp after it, neutral raw, no Corroder shred bonus"
        ),
        "live_stats": {"troll_armor": TROLL_ARMOR, "undead_magic_resist": UNDEAD_MAGIC_RESIST},
        "cases": rows,
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
    print("minion damage ladder oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
