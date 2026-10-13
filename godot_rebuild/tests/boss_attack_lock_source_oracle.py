"""9ah: the boss attack lock is hero-only, like the source `hasattr` gate.

Every attack lock in `Boss._smart_ai_*` / `Boss._cast_*` is written as

    if hasattr(e, 'attack_timer'):
        e.attack_timer = max(getattr(e, 'attack_timer', 0), N)

(`bosses/base_boss.py:1080-1082`, `:1542-1544`, `:1700-1701`, `:1729-1730` and
12 more payloads - 46 writes across 14 durations). `attack_timer` is created by
`Hero.__init__` alone (`_entity.py:3392`), so minions and towers never answer
`hasattr` and the source lock leaves them alone.

`boss_ai.gd::_attack_lock` kept the payloads but added an `else` branch that
pushed the duration into `cooldown_ticks`, stalling a minion's attacks - a lock
the source never applies. The oracle checks the guard shape, the hero-only
owner and the payload multiset against the native call sites, and runs the real
`Hero` clock rule for the columns. `--write` rewrites the fixture.
"""

import argparse
import ast
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_attack_lock_source.json"
BOSS_SOURCE = ROOT / "bosses" / "base_boss.py"
ENTITY = ROOT / "_entity.py"
NATIVE_AI = ROOT / "godot_rebuild" / "scripts" / "match" / "boss_ai.gd"


def _source_writes():
    """Every `...attack_timer = max(..., N)` / `= N` write with its guard flag."""
    tree = ast.parse(BOSS_SOURCE.read_text(encoding="utf-8"))
    writes = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Attribute) and target.attr == "attack_timer"
            for target in node.targets
        ):
            continue
        value = node.value
        duration = None
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "max":
            try:
                duration = int(ast.literal_eval(value.args[-1]))
            except Exception:
                duration = None
        elif isinstance(value, ast.Constant):
            duration = int(value.value)
        writes.append((duration, node.lineno))
    return writes


def _guard_flags():
    """How many attack_timer writes sit inside a `hasattr` guard."""
    tree = ast.parse(BOSS_SOURCE.read_text(encoding="utf-8"))
    guarded = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        if "attack_timer" not in ast.unparse(node.test):
            continue
        if any(
            isinstance(inner, ast.Assign)
            and any(
                isinstance(target, ast.Attribute) and target.attr == "attack_timer"
                for target in inner.targets
            )
            for inner in ast.walk(node)
        ):
            guarded += 1
    return guarded


def _owner_classes():
    """Classes that create the attribute in the source."""
    tree = ast.parse(ENTITY.read_text(encoding="utf-8"))
    owners = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Assign) and any(
                isinstance(target, ast.Attribute) and target.attr == "attack_timer"
                for target in inner.targets
            ):
                owners.append(node.name)
                break
    return owners


def _native_writes():
    """Payloads of every `_attack_lock(x, N)` call in the native AI."""
    payloads = Counter()
    unparsed = []
    for line in NATIVE_AI.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("_attack_lock("):
            continue
        match = re.match(r"_attack_lock\((.*),\s*([0-9]+)\)", stripped)
        if match:
            payloads[int(match.group(2))] += 1
        else:
            unparsed.append(stripped)
    return payloads, unparsed


def _shape():
    writes = _source_writes()
    payloads = Counter(duration for duration, _ in writes if duration is not None)
    native, unparsed = _native_writes()
    return {
        "source_writes": len(writes),
        "resolved_payloads": sum(payloads.values()),
        "hasattr_guarded": _guard_flags(),
        "owner_classes": _owner_classes(),
        "payload_multiset": {str(key): payloads[key] for key in sorted(payloads)},
        "native_writes": sum(native.values()),
        "native_payload_multiset": {str(key): native[key] for key in sorted(native)},
        "native_unparsed": unparsed,
    }


def _row(name, note, kind, duration, pre_clock=0, alive=True):
    return {
        "name": name,
        "note": note,
        "input": {
            "kind": kind,
            "duration": int(duration),
            "pre_clock": int(pre_clock),
            "alive": bool(alive),
        },
        # Source rule: `attack_timer = max(existing, N)` when the victim answers
        # `hasattr`; every other kind keeps its own clock untouched. The source
        # builds its enemy list from living units, so a dead probe is unchanged
        # in both columns.
        "expected": {"clock": max(int(pre_clock), int(duration)) if kind == "hero" and alive else int(pre_clock)},
        # Pre-9ah: the same hero rule, but a non-hero victim got the duration
        # pushed into `cooldown_ticks`.
        # The pre-9ah `else` branch wrote `cooldown_ticks = maxi(clock, N)`, i.e.
        # the same max rule but applied to every non-hero victim.
        "native_old": {
            "clock": max(int(pre_clock), int(duration))
            if alive and kind != "structure"
            else int(pre_clock)
        },
    }


def source_fixture():
    rows = [
        _row("hero_empty_clock", "an idle hero takes the full 90 tick lock", "hero", 90),
        _row(
            "hero_longer_clock_kept",
            "a hero already locked for 200 keeps its longer clock",
            "hero",
            90,
            pre_clock=200,
        ),
        _row(
            "hero_shorter_clock_raised",
            "a hero locked for 10 is raised to the 150 tick payload",
            "hero",
            150,
            pre_clock=10,
        ),
        _row(
            "hero_takes_the_smallest_payload",
            "the smallest source payload (30) still raises an empty clock",
            "hero",
            30,
        ),
        _row(
            "minion_clock_untouched",
            "a minion has no attack_timer, so the source locks nothing",
            "minion",
            90,
            pre_clock=5,
        ),
        _row(
            "minion_longer_clock_kept",
            "a minion already at 200 is quiet in both columns (the old max rule kept it too)",
            "minion",
            90,
            pre_clock=200,
        ),
        _row(
            "structure_clock_untouched",
            "a tower has no attack_timer either",
            "structure",
            120,
            pre_clock=7,
        ),
        _row(
            "dead_hero_untouched",
            "the source enemy list holds living units only",
            "hero",
            90,
            pre_clock=0,
            alive=False,
        ),
        _row(
            "dead_minion_untouched",
            "a dead minion is not in the source enemy list",
            "minion",
            60,
            pre_clock=3,
            alive=False,
        ),
    ]
    return {
        "source": "`bosses/base_boss.py` attack locks + `_entity.py::Hero.attack_timer`",
        "callsite": "godot_rebuild/scripts/match/boss_ai.gd::_attack_lock",
        "shape": _shape(),
        "live_stats": {
            "hero_clock_owner": _owner_classes(),
            "distinct_durations": len(_shape()["payload_multiset"]),
        },
        "rows": rows,
    }


def _self_test(fixture):
    problems = []
    shape = fixture["shape"]
    if shape["source_writes"] != 46 or shape["resolved_payloads"] != 46:
        problems.append(
            "the source attack locks changed: %d writes, %d resolved"
            % (shape["source_writes"], shape["resolved_payloads"])
        )
    if shape["hasattr_guarded"] != 46:
        problems.append("guarded writes changed: %d" % shape["hasattr_guarded"])
    if shape["owner_classes"] != ["Hero"]:
        problems.append("attack_timer is no longer hero-only: %s" % shape["owner_classes"])
    if shape["payload_multiset"] != shape["native_payload_multiset"]:
        problems.append("the native payload multiset drifted from the source")
    if shape["native_unparsed"]:
        problems.append("unparsed native locks: %s" % shape["native_unparsed"])
    by_name = {row["name"]: row for row in fixture["rows"]}
    if by_name["hero_empty_clock"]["expected"]["clock"] != 90:
        problems.append("an idle hero must take 90")
    if by_name["hero_longer_clock_kept"]["expected"]["clock"] != 200:
        problems.append("a longer hero clock must be kept")
    if by_name["hero_shorter_clock_raised"]["expected"]["clock"] != 150:
        problems.append("a shorter hero clock must be raised to 150")
    minion = by_name["minion_clock_untouched"]
    if minion["expected"]["clock"] != 5 or minion["native_old"]["clock"] != 90:
        problems.append("the minion lock must be the 9ah gap (source 5, old 90)")
    tower = by_name["structure_clock_untouched"]
    if tower["expected"]["clock"] != 7 or tower["native_old"]["clock"] != 7:
        problems.append("the structure control must be quiet in both columns")
    if by_name["dead_hero_untouched"]["expected"]["clock"] != 0:
        problems.append("a dead probe must stay untouched")
    if problems:
        for problem in problems:
            print("FAIL: %s" % problem)
        return 1
    print("boss attack lock oracle self-test passed: %d rows" % len(fixture["rows"]))
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
