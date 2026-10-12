"""9l: source oracle for the hero ARMOUR model of `Hero.take_damage`.

`Hero.take_damage` mitigation (`_entity.py:4638-4672`) runs

    if damage > 0 and self.dmg_amp_timer > 0:
        damage = int(round(damage * (1.0 + self.dmg_amp_amount)))
    if damage_type != 'fire' and damage > 0:
        armor = (inv.get_armor() if inv is not None else 0)
        armor -= getattr(self, "armor_shred_amount", 0.0)
        if armor > 0:
            reduction = armor * 0.06 / (1.0 + armor * 0.06)
            damage = max(1, int(round(damage * (1.0 - reduction))))
        elif armor < 0:
            bonus = min(1.0, -armor * 0.06)
            damage = int(round(damage * (1.0 + bonus)))

so the amp runs FIRST and the armour formula then applies to every non-fire hit
**regardless of school**: `magic_resist` is never read for heroes, and all 222
hero definitions carry `armor = 0`, so the only armour a hero has is the item
armour (`get_armor()`) minus `armor_shred_amount`.

The native build (layer 5b-3) instead resolved mitigation from the SCHOOL -
physical -> armour, magic -> `definition.magic_resist` (0 for every hero, so
magic hits landed raw) - and ran the amp after it. Every row records the
executed source ladder (`expected`) plus that pre-9l native model
(`native_old`), so the suite can assert both the new value and the divergence.

`--self-test` verifies the executed ladder against the committed fixture;
`--write` is the only fixture writer.
"""
import argparse
import json
from pathlib import Path

from hero_veil_immunity_source_oracle import _case, _run_case, _take_damage_callable

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "godot_rebuild" / "data" / "ai" / "item_catalog.json"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hero_armor_model_source.json"
# `steel_aegis` is the catalog armour item WITHOUT a `block` entry, so a row can
# carry armour without arming the 9k passive block roll.
ARMOR_ITEM = "steel_aegis"
_ITEMS = json.loads(CATALOG.read_text(encoding="utf-8"))["items"]
ARMOR = int(_ITEMS[ARMOR_ITEM]["stats"]["armor"])


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


def _native_old_loss(case) -> int:
    """Pre-9l native model: school decides, amp after, neutral untouched."""
    raw = int(case["damage"])
    amp = bool(case.get("dmg_amp_timer", 0) > 0)
    amount = float(case.get("dmg_amp_amount", 0.0)) if amp else 0.0
    armor = float(case.get("armor", 0)) - float(case.get("armor_shred", 0.0))
    school = case.get("school")
    if school is None:
        return raw
    if school == "physical":
        loss = _armor_formula(raw, armor)
    else:
        # heroes carry magic_resist 0, so the school resolver returned the raw
        # amount; `item_aware_amount` then applied the amp.
        loss = raw
    if amp and loss > 0:
        loss = _round_like_python(loss * (1.0 + amount))
    return max(0, loss)


CASES = [
    _case(
        "magic_hit_item_armor",
        school="magic",
        source_school="magic",
        armor=ARMOR,
        draws=[0.90],
    ),
    _case(
        "physical_hit_item_armor",
        school="physical",
        armor=ARMOR,
        draws=[0.90],
    ),
    _case("magic_hit_no_armor", school="magic", source_school="magic", draws=[0.90]),
    _case(
        "neutral_hit_item_armor",
        school=None,
        source_school=None,
        armor=ARMOR,
        draws=[0.90],
    ),
    _case(
        "fire_hit_skips_armor",
        damage_type="fire",
        school=None,
        source_school=None,
        armor=ARMOR,
        draws=[0.90],
    ),
    _case(
        "amp_then_armor",
        school="physical",
        armor=ARMOR,
        dmg_amp_timer=120,
        dmg_amp_amount=0.5,
        draws=[0.90],
    ),
    _case(
        "magic_hit_negative_armor",
        school="magic",
        source_school="magic",
        armor=0,
        armor_shred=5.0,
        draws=[0.90],
    ),
    _case(
        "physical_hit_negative_armor",
        school="physical",
        armor=0,
        armor_shred=5.0,
        draws=[0.90],
    ),
    _case("no_armor_no_amp_control", school="physical", draws=[0.90]),
]


def source_fixture() -> dict:
    take_damage, _credits = _take_damage_callable()
    rows = []
    for case in CASES:
        expected = _run_case(take_damage, case)
        rows.append(
            {
                "name": case["name"],
                "damage": int(case["damage"]),
                "damage_type": case["damage_type"],
                "school": case["school"],
                "source_school": case["source_school"],
                "armor": int(case["armor"]),
                "armor_shred": float(case.get("armor_shred", 0.0)),
                "dmg_amp_timer": int(case.get("dmg_amp_timer", 0)),
                "dmg_amp_amount": float(case.get("dmg_amp_amount", 0.0)),
                "draws": list(case["draws"]),
                "expected": expected,
                "native_old": {"hp_loss": _native_old_loss(case)},
            }
        )
    return {
        "source": "_entity.py::Hero.take_damage amp+armour section :4638-4672",
        "native_old_model": (
            "pre-9l native: school decides (physical -> item armour, magic ->"
            " definition magic_resist = 0), amp after mitigation, neutral raw"
        ),
        "item": {"id": ARMOR_ITEM, "armor": ARMOR, "block": None},
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
    print("hero armour model oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
