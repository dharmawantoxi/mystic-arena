"""9ae: slow resist and the source store rule on the item slow arm.

`TowerDebuffMixin.apply_slow` (`_core.py:853-867`) is the polymorphic method
every item slow arm calls - Frostbound Frostbite `target.apply_slow(oa['slow'],
oa['duration'])` (`hero_items.py:2594-2595`), Vine Rod Entangle
`target.apply_slow(1.0, vr['root_duration'])` (`:2662`), Everfrost Arctic Blast
`e.apply_slow(act['slow'], act['slow_duration'])` (`:2290-2291`), each behind
`hasattr(target, 'apply_slow')`. The method:

* ignores a dead victim (`alive` guard),
* scales the payload by the victim's item slow resist when it carries an
  inventory (`inv.get_slow_resist()`, Abyss Breaker 0.30, capped 0.60),
* stores with `amount > slow_amount or slow_timer < duration`, which rewrites
  BOTH fields - a weaker longer slow lowers the magnitude, a stronger shorter
  slow shortens the clock.

The native bus (`battle_item_effects.gd::apply_slow`) delegated only when the
victim already had an `apply_slow` method, which was true for the boss alone, so
hero/minion/structure victims fell through to the raw `maxf`/`maxi` write: no
slow resist for a hero holding Abyss Breaker, max-wins instead of the refresh
rule, and no dead-victim guard.

Rows execute the real `TowerDebuffMixin.apply_slow` (expected column) against the
pre-9ae native rule (native_old column) with payloads read from the live item
catalog. `--write` rewrites the fixture.
"""

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from boss_core_source_oracle import namespace  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "item_slow_resist_source.json"
CATALOG = ROOT / "godot_rebuild" / "data" / "ai" / "item_catalog.json"
CORE_SOURCE = ROOT / "_core.py"
HERO_ITEMS = ROOT / "hero_items.py"

_ENV = None
MIXIN = None


def _mixin():
    global _ENV, MIXIN
    if _ENV is None:
        _ENV = namespace()
        MIXIN = _ENV["TowerDebuffMixin"]
    return MIXIN


class _Inventory:
    def __init__(self, resist):
        self._resist = resist

    def get_slow_resist(self):
        return self._resist


class _Victim:
    """Minimal victim carrying the mixin fields the source method reads."""

    def __init__(self, resist=None, alive=True, amount=0.0, timer=0):
        self.alive = alive
        self.slow_amount = amount
        self.slow_timer = timer
        if resist is not None:
            self.items = _Inventory(resist)


def _shape() -> dict:
    tree = ast.parse(CORE_SOURCE.read_text(encoding="utf-8"))
    holder = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "TowerDebuffMixin"
    )
    method = next(
        node
        for node in holder.body
        if isinstance(node, ast.FunctionDef) and node.name == "apply_slow"
    )
    text = ast.unparse(method)
    items = ast.parse(HERO_ITEMS.read_text(encoding="utf-8"))
    resist_text = ast.unparse(
        next(
            node
            for node in ast.walk(items)
            if isinstance(node, ast.FunctionDef) and node.name == "get_slow_resist"
        )
    )
    return {
        "alive_guard": "getattr(self, 'alive', True)" in text,
        "reads_items": "getattr(self, 'items', None)" in text,
        "scales_by_resist": "amount *= 1.0 - inv.get_slow_resist()" in text,
        "resist_guarded": "try:" in text and "except Exception:" in text,
        "refresh_rule": "amount > getattr(self, 'slow_amount', 0.0)" in text
        and "getattr(self, 'slow_timer', 0) < duration" in text,
        "catalog_resist_cap": "min(0.6, self._sum_stat('slow_resist'))" in resist_text,
    }


def _source_column(resist, amount, duration, alive=True, pre_amount=0.0, pre_timer=0):
    victim = _Victim(resist=resist, alive=alive, amount=pre_amount, timer=pre_timer)
    _mixin().apply_slow(victim, amount, duration)
    return {"amount": round(float(victim.slow_amount), 6), "timer": int(victim.slow_timer)}


def _native_old_column(resist, amount, duration, alive=True, pre_amount=0.0, pre_timer=0):
    """Pre-9ae bus write: raw `maxf`/`maxi`, no resist, no alive guard."""
    if not alive:
        return {"amount": round(float(amount), 6), "timer": int(duration)}
    return {
        "amount": round(max(float(pre_amount), float(amount)), 6),
        "timer": max(int(pre_timer), int(duration)),
    }


def _row(name, note, resist, amount, duration, alive=True, pre_amount=0.0, pre_timer=0,
         source_name="`_core.py::TowerDebuffMixin.apply_slow`"):
    return {
        "name": name,
        "note": note,
        "source_name": source_name,
        "input": {
            "resist": resist,
            "amount": round(float(amount), 6),
            "duration": int(duration),
            "alive": bool(alive),
            "pre_amount": round(float(pre_amount), 6),
            "pre_timer": int(pre_timer),
        },
        "expected": _source_column(resist, amount, duration, alive, pre_amount, pre_timer),
        "native_old": _native_old_column(resist, amount, duration, alive, pre_amount, pre_timer),
    }


def source_fixture():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))["items"]
    abyss = catalog["abyss_breaker"]["stats"]
    frost = catalog["frostbound_eye"]["on_attack"]
    vine = catalog["vine_rod"]
    arctic = catalog["everfrost_guard"]["active"]
    resist = float(abyss["slow_resist"])
    rows = [
        _row(
            "hero_without_items_frostbound",
            "no inventory: the payload lands raw and both columns agree",
            None,
            float(frost["slow"]),
            int(frost["duration"]),
            source_name="`hero_items.py::Frostbite`",
        ),
        _row(
            "hero_with_abyss_breaker_frostbound",
            "slow resist 0.30 scales the item slow before the store",
            resist,
            float(frost["slow"]),
            int(frost["duration"]),
            source_name="`hero_items.py::Frostbite` + `get_slow_resist`",
        ),
        _row(
            "hero_with_abyss_breaker_arctic_blast",
            "Everfrost Arctic Blast slow is resisted the same way",
            resist,
            float(arctic["slow"]),
            int(arctic["slow_duration"]),
            source_name="`hero_items.py::Arctic Blast`",
        ),
        _row(
            "hero_with_abyss_breaker_entangle_root",
            "a full root (1.0) becomes 0.70 for a hero holding Abyss Breaker",
            resist,
            1.0,
            int(vine.get("root_duration", 120)),
            source_name="`hero_items.py::Entangle`",
        ),
        _row(
            "hero_at_the_resist_cap",
            "the cap 0.60 leaves 0.40 of a full root",
            0.6,
            1.0,
            120,
            source_name="`hero_items.py::get_slow_resist` cap",
        ),
        _row(
            "merge_weak_long_after_strong_short",
            "source refresh rewrites both fields: 0.20/120 replaces 0.50/20",
            None,
            0.20,
            120,
            pre_amount=0.50,
            pre_timer=20,
        ),
        _row(
            "merge_strong_short_after_weak_long",
            "a stronger shorter slow shortens the clock: 0.50/30 wins over 0.20/120",
            None,
            0.50,
            30,
            pre_amount=0.20,
            pre_timer=120,
        ),
        _row(
            "merge_tie_keeps_clock",
            "equal strength and duration keeps the old clock (no write)",
            None,
            0.30,
            60,
            pre_amount=0.30,
            pre_timer=60,
        ),
        _row(
            "dead_victim_ignored",
            "a dead victim takes no slow (pre-9ae wrote it anyway)",
            None,
            0.50,
            120,
            alive=False,
        ),
        _row(
            "minion_victim_no_items",
            "a minion carries no inventory, so only the store rule matters",
            None,
            0.20,
            120,
            pre_amount=0.50,
            pre_timer=20,
            source_name="`_core.py::TowerDebuffMixin.apply_slow` (minion)",
        ),
    ]
    return {
        "source": "`_core.py::TowerDebuffMixin.apply_slow` + `hero_items.py::HeroItemInventory.get_slow_resist`",
        "callsite": "godot_rebuild/scripts/match/battle_item_effects.gd::apply_slow",
        "shape": _shape(),
        "live_stats": {
            "abyss_breaker_slow_resist": resist,
            "resist_cap": 0.6,
            "frostbound": {
                "slow": float(frost["slow"]),
                "duration": int(frost["duration"]),
            },
            "arctic_blast": {
                "slow": float(arctic["slow"]),
                "duration": int(arctic["slow_duration"]),
            },
            "vine_root_duration": int(vine.get("root_duration", 120)),
        },
        "rows": rows,
    }


def _self_test(fixture):
    problems = []
    shape = fixture["shape"]
    for key, label in (
        ("alive_guard", "alive guard"),
        ("reads_items", "inventory read"),
        ("scales_by_resist", "slow resist scaling"),
        ("resist_guarded", "resist try/except"),
        ("refresh_rule", "amount-or-timer refresh rule"),
        ("catalog_resist_cap", "catalog resist cap"),
    ):
        if not shape[key]:
            problems.append("the source %s drifted" % label)
    resist = fixture["live_stats"]["abyss_breaker_slow_resist"]
    for row in fixture["rows"]:
        payload = row["input"]
        expected = row["expected"]
        old = row["native_old"]
        name = row["name"]
        if not payload["alive"]:
            if expected["amount"] != payload["pre_amount"] or expected["timer"] != payload["pre_timer"]:
                problems.append("%s: a dead victim must not be written" % name)
        elif payload["resist"] is None:
            if expected["amount"] != payload["amount"] or expected["timer"] != payload["duration"]:
                problems.append("%s: an unresisted payload must land raw" % name)
        else:
            want = round(payload["amount"] * (1.0 - payload["resist"]), 6)
            if abs(expected["amount"] - want) > 1e-6 or expected["timer"] != payload["duration"]:
                problems.append("%s: resist scaling drifted" % name)
        if name == "merge_weak_long_after_strong_short" and expected["amount"] != 0.2:
            problems.append("the weaker longer slow must rewrite the magnitude to 0.20")
        if name == "hero_with_abyss_breaker_frostbound" and (
            expected["amount"] != round(0.28 * (1.0 - resist), 6) or old["amount"] != 0.28
        ):
            problems.append("Frostbite on an Abyss Breaker hero must be 0.196 vs the old 0.28")
        if name == "hero_at_the_resist_cap" and expected["amount"] != 0.4:
            problems.append("the resist cap must leave 0.40")
    if abs(resist - 0.3) > 1e-9:
        problems.append("the catalog slow resist changed")
    if problems:
        for problem in problems:
            print("FAIL: %s" % problem)
        return 1
    print("item slow resist oracle self-test passed: %d rows" % len(fixture["rows"]))
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
