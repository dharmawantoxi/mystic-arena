"""9k: source oracle for the hero damage BLOCK ladder (`Hero.take_damage`).

`hero_items.HeroItemInventory.get_block` (`hero_items.py:2051-2069`) returns
`(chance, amount)` from the best `block` entry the owner holds - for the real
catalog that is `scarlet_bulwark` (`chance=0.55`, `melee_block=25`,
`ranged_block=14`) - and `Hero.take_damage` consumes it inside the non-fire
armour section (`_entity.py:4657-4672`):

    block_amt = 0
    if inv is not None:
        blk = inv.get_block()
        if blk and random.random() < blk[0]:
            block_amt = blk[1]
        if getattr(inv, "aura_guard_block", 0) > block_amt:
            block_amt = inv.aura_guard_block
    if block_amt > 0:
        damage = max(0, damage - block_amt)

That section sits AFTER school mitigation + the Soul Rend amp and BEFORE the
Bristleback keep (0.70 physical / 0.85 magic), so the block lowers the damage
that the keep then multiplies. `scarlet_bulwark` also grants `armor = 6`, so
every row that holds the item carries that item armour into the armour step,
exactly like the native `DamageRules.effective_armor` does for a hero.

The native build consumed `aura_guard_block` only, and subtracted it after the
Bristleback keep; the passive `get_block()` roll had no consumer at all. The
`native_old` column of each row is the pre-9k model: the executed source amount
without any block, then the aura subtraction on top of the keep.

`--self-test` verifies the executed ladder against the committed fixture;
`--write` is the only fixture writer.
"""
import argparse
import json
from pathlib import Path

from hero_veil_immunity_source_oracle import (
    _case,
    _run_case,
    _take_damage_callable,
)

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "godot_rebuild" / "data" / "ai" / "item_catalog.json"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hero_block_source.json"
# The catalog block item the replay adds to the defender via `items.add()`.
BLOCK_ITEM = "scarlet_bulwark"
_BLOCK = json.loads(CATALOG.read_text(encoding="utf-8"))["items"][BLOCK_ITEM]
BLOCK_CHANCE = float(_BLOCK["block"]["chance"])
BLOCK_MELEE = int(_BLOCK["block"]["melee_block"])
BLOCK_ARMOR = int(_BLOCK["stats"]["armor"])
BLOCK_TUPLE = (BLOCK_CHANCE, BLOCK_MELEE)
# Source `_entity.py:6571`-style Python rounding (ties to even).
OMIT = ("block", "guard_block")


def _without_block(case):
    row = {key: value for key, value in case.items()}
    for key in OMIT:
        row[key] = None if key == "block" else 0
    return row


def _native_old_loss(take_damage, case) -> int:
    # Pre-9k native: item armour + amp, then the Bristleback keep, then the
    # aura subtraction. No passive block roll existed.
    base = _run_case(take_damage, _without_block(case))["hp_loss"]
    return max(0, int(base) - int(case.get("guard_block", 0)))


CASES = [
    _case(
        "block_roll_hits",
        armor=BLOCK_ARMOR,
        block=BLOCK_TUPLE,
        draws=[0.10],
    ),
    _case(
        "block_roll_misses",
        armor=BLOCK_ARMOR,
        block=BLOCK_TUPLE,
        draws=[0.80],
    ),
    _case(
        "block_aura_overrides_chance",
        armor=BLOCK_ARMOR,
        block=BLOCK_TUPLE,
        guard_block=120,
        draws=[0.10],
    ),
    _case("aura_only_without_item", guard_block=60),
    _case(
        "block_then_bristleback_keep",
        armor=BLOCK_ARMOR,
        block=BLOCK_TUPLE,
        bristleback=True,
        draws=[0.10],
    ),
    _case(
        "block_projectile_hits",
        armor=BLOCK_ARMOR,
        block=BLOCK_TUPLE,
        damage_type="projectile",
        draws=[0.10],
    ),
    _case("block_inactive_control", draws=[0.50]),
    _case(
        "block_zero_damage_control",
        damage=0,
        armor=BLOCK_ARMOR,
        block=BLOCK_TUPLE,
        draws=[0.10],
    ),
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
                "block": list(BLOCK_TUPLE) if case.get("block") else None,
                "guard_block": int(case.get("guard_block", 0)),
                "bristleback": bool(case["bristleback"]),
                "draws": list(case["draws"]),
                "expected": expected,
                "native_old": {"hp_loss": _native_old_loss(take_damage, case)},
            }
        )
    return {
        "source": "_entity.py::Hero.take_damage armour/block section :4652-4672",
        "native_old_model": (
            "pre-9k native: DamageRules.item_aware_amount -> aura_guard_block"
            " (no passive block, aura subtracted after the Bristleback keep)"
        ),
        "item": {
            "id": BLOCK_ITEM,
            "chance": BLOCK_CHANCE,
            "melee_block": BLOCK_MELEE,
            "armor": BLOCK_ARMOR,
        },
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
    print("hero block oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
