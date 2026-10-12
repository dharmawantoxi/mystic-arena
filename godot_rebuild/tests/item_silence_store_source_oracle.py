"""9af: the unit arm of item silence runs the source mixin store.

`hero_items._apply_silence_to(target, duration)` (`hero_items.py:2693-2697`)
calls `target.apply_debuff("atk_slow", 1.0, duration)` then
`target.apply_debuff("skill_down", 1.0, duration)` inside a `try` that swallows
the `AttributeError` a target without the mixin raises. `TowerDebuffMixin`
belongs to `Hero`, `Minion` and `Boss` only (`_entity.py:3235`, `:5400`), so:

* a hero/minion runs the mixin store - alive guard, and the
  `amount > stored or timer < duration` rule that rewrites BOTH fields;
* a tower raises and is left untouched.

The native bus delegated to the victim method only for the boss, and the unit
arm wrote the fields raw: `1.0` forced into the amount even when a stronger
clock was already stored, `maxi` for the timer (so a weaker-but-longer store
kept its long clock while the source shortens it), no alive guard, and towers -
which have no mixin - were silenced. Rows execute the mixin method (expected
column) against the pre-9af raw write (native_old column). `--write` rewrites
the fixture.
"""

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from boss_core_source_oracle import namespace  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "item_silence_store_source.json"
CORE_SOURCE = ROOT / "_core.py"
HERO_ITEMS = ROOT / "hero_items.py"
ENTITY = ROOT / "_entity.py"
SILENCE = 1.0

_ENV = None
MIXIN = None


def _mixin():
    global _ENV, MIXIN
    if _ENV is None:
        _ENV = namespace()
        MIXIN = _ENV["TowerDebuffMixin"]
    return MIXIN


class _Victim:
    """Minimal hero/minion stub: the mixin fields the store reads."""

    def __init__(self, alive=True, atk_amount=0.0, atk_timer=0, skill_amount=0.0, skill_timer=0):
        self.alive = alive
        self.atk_slow_amount = atk_amount
        self.atk_slow_timer = atk_timer
        self.skill_down_amount = skill_amount
        self.skill_down_timer = skill_timer


def _shape() -> dict:
    core = ast.parse(CORE_SOURCE.read_text(encoding="utf-8"))
    holder = next(
        node
        for node in core.body
        if isinstance(node, ast.ClassDef) and node.name == "TowerDebuffMixin"
    )
    store = next(
        node
        for node in holder.body
        if isinstance(node, ast.FunctionDef) and node.name == "apply_debuff"
    )
    text = ast.unparse(store)
    items = ast.parse(HERO_ITEMS.read_text(encoding="utf-8"))
    silence = next(
        node
        for node in ast.walk(items)
        if isinstance(node, ast.FunctionDef) and node.name == "_apply_silence_to"
    )
    silence_text = ast.unparse(silence)
    entity = ast.parse(ENTITY.read_text(encoding="utf-8"))
    mixin_owners = sorted(
        node.name
        for node in entity.body
        if isinstance(node, ast.ClassDef) and any(
            base_id == "TowerDebuffMixin" for base_id in (ast.unparse(b) for b in node.bases)
        )
    )
    return {
        "silence_calls_atk_slow": "apply_debuff('atk_slow', 1.0, duration)" in silence_text,
        "silence_calls_skill_down": "apply_debuff('skill_down', 1.0, duration)" in silence_text,
        "silence_swallows_lookup": "except Exception:" in silence_text,
        "store_alive_guard": "getattr(self, 'alive', True)" in text,
        "store_atk_slow_merge": "atk_slow_amount" in text and "atk_slow_timer" in text,
        "store_skill_down_merge": "skill_down_amount" in text and "skill_down_timer" in text,
        "mixin_owners": mixin_owners,
    }


def _expected(alive, atk_amount, atk_timer, skill_amount, skill_timer, duration):
    victim = _Victim(alive, atk_amount, atk_timer, skill_amount, skill_timer)
    _mixin().apply_debuff(victim, "atk_slow", SILENCE, duration)
    _mixin().apply_debuff(victim, "skill_down", SILENCE, duration)
    return {
        "atk_amount": round(float(victim.atk_slow_amount), 6),
        "atk_timer": int(victim.atk_slow_timer),
        "skill_amount": round(float(victim.skill_down_amount), 6),
        "skill_timer": int(victim.skill_down_timer),
    }


def _native_old(alive, atk_amount, atk_timer, skill_amount, skill_timer, duration):
    """Pre-9af unit arm: `1.0` forced in, `maxi` clock, no alive guard, no tower gate."""
    del alive
    return {
        "atk_amount": SILENCE,
        "atk_timer": max(int(atk_timer), int(duration)),
        "skill_amount": SILENCE,
        "skill_timer": max(int(skill_timer), int(duration)),
    }


def _row(
    name,
    note,
    duration,
    alive=True,
    atk_amount=0.0,
    atk_timer=0,
    skill_amount=0.0,
    skill_timer=0,
    native_open=None,
):
    return {
        "name": name,
        "note": note,
        "input": {
            "duration": int(duration),
            "alive": bool(alive),
            "atk_amount": round(float(atk_amount), 6),
            "atk_timer": int(atk_timer),
            "skill_amount": round(float(skill_amount), 6),
            "skill_timer": int(skill_timer),
        },
        "expected": _expected(alive, atk_amount, atk_timer, skill_amount, skill_timer, duration),
        "native_old": _native_old(alive, atk_amount, atk_timer, skill_amount, skill_timer, duration),
        # `native_open` marks a source behaviour the native world store still
        # refuses, so the suite pins the current native state beside the source
        # column instead of claiming parity.
        "native_open": native_open,
    }


def source_fixture():
    rows = [
        _row("fresh_victim", "an empty store takes the full silence on both clocks", 60),
        _row(
            "weaker_longer_atk_clock",
            "a 0.9/200 attack clock is rewritten to 1.0/60, not kept at 1.0/200",
            60,
            atk_amount=0.9,
            atk_timer=200,
        ),
        _row(
            "equal_amount_longer_clock",
            "1.0/200 already beats the silence: the source writes nothing",
            60,
            atk_amount=1.0,
            atk_timer=200,
            skill_amount=1.0,
            skill_timer=200,
        ),
        _row(
            "shorter_clock_refreshes",
            "a 1.0/10 clock is refreshed to the 60 tick silence",
            60,
            atk_amount=1.0,
            atk_timer=10,
        ),
        _row(
            "dead_victim_ignored",
            "a dead victim takes no silence at all (pre-9af wrote 1.0/60)",
            60,
            alive=False,
            atk_amount=0.5,
            atk_timer=5,
            skill_amount=0.5,
            skill_timer=5,
        ),
        _row(
            "skill_down_only_stored",
            "the two clocks are independent: a stored skill-down keeps its own row",
            90,
            skill_amount=0.5,
            skill_timer=30,
        ),
        _row(
            "zero_duration_keeps_store",
            "the mixin has no duration guard: amount 1.0 is stored with a 0 clock; the "
            "native world store still refuses non-positive durations (recorded open item)",
            0,
            atk_amount=1.0,
            atk_timer=0,
            native_open={"skill_amount": 0.0, "skill_timer": 0},
        ),
    ]
    return {
        "source": "`hero_items.py::_apply_silence_to` + `_core.py::TowerDebuffMixin.apply_debuff`",
        "callsite": "godot_rebuild/scripts/match/battle_item_effects.gd::apply_silence",
        "shape": _shape(),
        "live_stats": {"silence_amount": SILENCE},
        "rows": rows,
    }


def _self_test(fixture):
    problems = []
    shape = fixture["shape"]
    for key in (
        "silence_calls_atk_slow",
        "silence_calls_skill_down",
        "silence_swallows_lookup",
        "store_alive_guard",
        "store_atk_slow_merge",
        "store_skill_down_merge",
    ):
        if not shape[key]:
            problems.append("the source silence/store shape drifted (%s)" % key)
    if shape["mixin_owners"] != ["Hero", "Minion"]:
        problems.append("the mixin owners changed: %s" % shape["mixin_owners"])
    for row in fixture["rows"]:
        payload = row["input"]
        expected = row["expected"]
        old = row["native_old"]
        name = row["name"]
        if not payload["alive"]:
            if (
                expected["atk_amount"] != payload["atk_amount"]
                or expected["atk_timer"] != payload["atk_timer"]
                or expected["skill_amount"] != payload["skill_amount"]
                or expected["skill_timer"] != payload["skill_timer"]
            ):
                problems.append("%s: a dead victim must keep its store" % name)
        elif name == "weaker_longer_atk_clock":
            if expected["atk_amount"] != 1.0 or expected["atk_timer"] != 60:
                problems.append("the weaker longer clock must be rewritten to 1.0/60")
            if old["atk_timer"] != 200:
                problems.append("the old column must show the kept 200 tick clock")
        elif name == "equal_amount_longer_clock":
            if expected["atk_timer"] != 200 or expected["skill_timer"] != 200:
                problems.append("an already stronger store must not be rewritten")
        elif name == "shorter_clock_refreshes":
            if expected["atk_timer"] != 60:
                problems.append("a shorter clock must refresh to 60")
        elif name == "zero_duration_keeps_store":
            if expected["atk_amount"] != 1.0 or expected["atk_timer"] != 0:
                problems.append("the zero duration row must not open a clock")
    if problems:
        for problem in problems:
            print("FAIL: %s" % problem)
        return 1
    print("item silence store oracle self-test passed: %d rows" % len(fixture["rows"]))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
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
