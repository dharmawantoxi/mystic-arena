"""9ag: the boss smart-AI slow arms deliver through the victim method.

Every slow in `Boss._smart_ai_*` is written as

    if hasattr(e, 'apply_slow'):
        e.apply_slow(amount, duration)

(`bosses/base_boss.py:1323-1324` and 18 more payload pairs, 39 calls in total),
so the victim runs `TowerDebuffMixin.apply_slow` (`_core.py:853-867`): alive
guard, item slow resist scaling (`inv.get_slow_resist()`, Abyss Breaker 0.30)
and the `amount > stored or timer < duration` refresh that rewrites both fields.
A tower never joins the mixin (`_entity.py:600` `class Tower` has no base), so
`hasattr` is false and the structure is skipped.

`boss_ai.gd::_slow` kept the payloads but wrote the fields raw, so a hero
holding Abyss Breaker took every boss slow at full strength and a
weaker-but-longer stored clock was kept at its long duration instead of the
source's rewrite. Rows come from the real source calls: the oracle walks
`base_boss.py` with AST, keeps every two-literal `apply_slow` call, and runs the
mixin method for the resist columns. `--write` rewrites the fixture.
"""

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from boss_core_source_oracle import namespace  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_ai_slow_source.json"
BOSS_SOURCE = ROOT / "bosses" / "base_boss.py"
NATIVE_AI = ROOT / "godot_rebuild" / "scripts" / "match" / "boss_ai.gd"
RESIST = 0.30
CAP_RESIST = 0.60

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
    def __init__(self, resist=None, amount=0.0, timer=0, alive=True):
        self.alive = alive
        self.slow_amount = amount
        self.slow_timer = timer
        if resist is not None:
            self.items = _Inventory(resist)


def _source_calls() -> list:
    tree = ast.parse(BOSS_SOURCE.read_text(encoding="utf-8"))
    calls = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr != "apply_slow" or len(node.args) != 2:
            continue
        try:
            amount = float(ast.literal_eval(node.args[0]))
            duration = int(ast.literal_eval(node.args[1]))
        except Exception:
            continue
        calls.append((amount, duration, node.lineno))
    return calls


def _column(resist, amount, duration, pre_amount=0.0, pre_timer=0):
    victim = _Victim(resist=resist, amount=pre_amount, timer=pre_timer)
    _mixin().apply_slow(victim, amount, duration)
    return {"amount": round(float(victim.slow_amount), 6), "timer": int(victim.slow_timer)}


def _native_old(amount, duration, pre_amount=0.0, pre_timer=0):
    if amount > pre_amount or pre_timer < duration:
        return {"amount": round(float(amount), 6), "timer": int(duration)}
    return {"amount": round(float(pre_amount), 6), "timer": int(pre_timer)}


def _shape() -> dict:
    calls = _source_calls()
    guarded = 0
    tree = ast.parse(BOSS_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        if "apply_slow" not in ast.unparse(node.test):
            continue
        if any(
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr == "apply_slow"
            for inner in ast.walk(node)
        ):
            guarded += 1
    native_text = NATIVE_AI.read_text(encoding="utf-8")
    # Count call sites only: the definition line starts with `static func` and
    # the doc comment mentions `apply_slow(`, so the line-start spelling is the
    # only reliable one.
    native_calls = sum(1 for line in native_text.splitlines() if line.strip().startswith("_slow("))
    owner_has_mixin = False
    entity = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    for node in entity.body:
        if isinstance(node, ast.ClassDef) and node.name == "Tower":
            owner_has_mixin = any(
                "TowerDebuffMixin" in ast.unparse(base) for base in node.bases
            )
    vortex = _vortex_shape()
    return {
        "source_calls": len(calls),
        **vortex,
        "hasattr_guarded": guarded,
        "unique_payloads": len({(amount, duration) for amount, duration, _ in calls}),
        "native_slow_calls": native_calls,
        "tower_has_mixin": owner_has_mixin,
    }


def _vortex_shape() -> dict:
    """Shape of the vortex duration block in `Boss.update`."""
    tree = ast.parse(BOSS_SOURCE.read_text(encoding="utf-8"))
    holder = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Boss"
    )
    smart = next(
        node
        for node in holder.body
        if isinstance(node, ast.FunctionDef) and node.name == "_smart_ai_ancient_apparition"
    )
    block = None
    for node in ast.walk(smart):
        text = ast.unparse(node)
        if "vortex_active_timer" in text and "take_damage" in text:
            if block is None or len(text) < len(ast.unparse(block)):
                block = node
    if block is None:
        return {"vortex_block_found": False}
    text = ast.unparse(block)
    return {
        "vortex_block_found": True,
        "vortex_every_20": "vortex_active_timer % 20 == 0" in text,
        "vortex_radius": "<= 80" in text,
        "vortex_damage_trisect": (
            "get('skill_q_damage', 180) // 3" in text
            or 'get("skill_q_damage", 180) // 3' in text
        ),
        "vortex_slow_hasattr": "hasattr(e, 'apply_slow')" in text,
        "vortex_slow_payload": "apply_slow(0.5, 60)" in text,
    }


def source_fixture():
    calls = _source_calls()
    rows = []
    for amount, duration in sorted({(a, d) for a, d, _ in calls}):
        rows.append(
            {
                "name": "boss_slow_%s_%d" % (str(amount).replace(".", "_"), duration),
                "note": "boss slow payload %s/%d delivered through the victim method%s"
                % (
                    amount,
                    duration,
                    " (the Ice Vortex DOT arm)" if (amount, duration) == (0.5, 60) else "",
                ),
                "input": {"amount": amount, "duration": duration},
                "expected_plain": _column(None, amount, duration),
                "expected_resisted": _column(RESIST, amount, duration),
                "native_old": _native_old(amount, duration),
            }
        )
    merge_rows = [
        {
            "name": "resisted_weakens_a_stronger_stored_clock",
            "note": "stored 0.4/10: the resisted 0.35 rewrites the magnitude, the raw 0.5 did not",
            "input": {"amount": 0.5, "duration": 180, "pre_amount": 0.4, "pre_timer": 10},
        },
        {
            "name": "resisted_keeps_a_stronger_stored_clock",
            "note": "stored 0.9/50: the shorter clock lets the resisted 0.35 rewrite both fields",
            "input": {"amount": 0.5, "duration": 180, "pre_amount": 0.9, "pre_timer": 50},
        },
        {
            "name": "resisted_payload_replaces_a_weaker_store",
            "note": "stored 0.2/400: the resisted 0.35 still beats it, so the clock shortens",
            "input": {"amount": 0.5, "duration": 180, "pre_amount": 0.2, "pre_timer": 400},
        },
        {
            "name": "plain_payload_refresh_rule_unchanged",
            "note": "no items: both columns rewrite the stored 0.4/300 to 0.5/180",
            "input": {"amount": 0.5, "duration": 180, "pre_amount": 0.4, "pre_timer": 300},
        },
    ]
    for row in merge_rows:
        payload = row["input"]
        plain = row.get("expected_plain") or _column(
            None,
            payload["amount"],
            payload["duration"],
            payload.get("pre_amount", 0.0),
            payload.get("pre_timer", 0),
        )
        resisted = row.get("expected_resisted") or _column(
            RESIST,
            payload["amount"],
            payload["duration"],
            payload.get("pre_amount", 0.0),
            payload.get("pre_timer", 0),
        )
        row["expected_plain"] = plain
        row["expected_resisted"] = resisted
        row["native_old"] = _native_old(
            payload["amount"],
            payload["duration"],
            payload.get("pre_amount", 0.0),
            payload.get("pre_timer", 0),
        )
    return {
        "source": "`bosses/base_boss.py` smart-AI `e.apply_slow(...)` + `_core.py::TowerDebuffMixin.apply_slow`",
        "callsite": "godot_rebuild/scripts/match/boss_ai.gd::_slow",
        "shape": _shape(),
        "live_stats": {
            "abyss_breaker_slow_resist": RESIST,
            "resist_cap": CAP_RESIST,
            "call_count": len(calls),
        },
        "rows": rows,
        "merge_rows": merge_rows,
    }


def _self_test(fixture):
    problems = []
    shape = fixture["shape"]
    if shape["source_calls"] != 39 or shape["hasattr_guarded"] != 39:
        problems.append("the source slow arms changed: %d calls, %d guarded"
                        % (shape["source_calls"], shape["hasattr_guarded"]))
    if shape["unique_payloads"] != 19:
        problems.append("the unique payload set changed: %d" % shape["unique_payloads"])
    if shape["native_slow_calls"] != shape["source_calls"]:
        problems.append("the native AI slow call count drifted from the source")
    if shape["tower_has_mixin"]:
        problems.append("the source Tower gained the mixin; the structure gate needs a review")
    if not shape.get("vortex_block_found", False):
        problems.append("the vortex duration block disappeared from Boss.update")
    elif not (
        shape["vortex_every_20"]
        and shape["vortex_radius"]
        and shape["vortex_damage_trisect"]
        and shape["vortex_slow_hasattr"]
        and shape["vortex_slow_payload"]
    ):
        problems.append("the vortex DOT shape drifted")
    for row in fixture["rows"]:
        amount = row["input"]["amount"]
        plain = row["expected_plain"]
        resisted = row["expected_resisted"]
        old = row["native_old"]
        if plain["amount"] != amount or plain["timer"] != row["input"]["duration"]:
            problems.append("%s: the plain column must land raw" % row["name"])
        want = round(amount * (1.0 - RESIST), 6)
        if abs(resisted["amount"] - want) > 1e-6:
            problems.append("%s: the resisted column must scale by 0.30" % row["name"])
        if old["amount"] != amount:
            problems.append("%s: the old column must show the untempered payload" % row["name"])
    by_name = {row["name"]: row for row in fixture["merge_rows"]}
    weak = by_name["resisted_weakens_a_stronger_stored_clock"]
    if (
        abs(weak["expected_resisted"]["amount"] - 0.35) > 1e-6
        or weak["expected_resisted"]["timer"] != 180
        or weak["native_old"]["amount"] != 0.5
    ):
        problems.append("the resisted payload must replace the stronger stored magnitude")
    kept = by_name["resisted_keeps_a_stronger_stored_clock"]
    if (
        abs(kept["expected_resisted"]["amount"] - 0.35) > 1e-6
        or kept["expected_resisted"]["timer"] != 180
    ):
        problems.append("a shorter stored clock lets the resisted payload rewrite both fields")
    weaker = by_name["resisted_payload_replaces_a_weaker_store"]
    if abs(weaker["expected_resisted"]["amount"] - 0.35) > 1e-6:
        problems.append("the resisted payload must still beat a weaker store")
    plain = by_name["plain_payload_refresh_rule_unchanged"]
    if (
        plain["expected_plain"]["amount"] != 0.5
        or plain["expected_plain"]["timer"] != 180
        or plain["native_old"]["amount"] != 0.5
    ):
        problems.append("the plain refresh rule must not move")
    if problems:
        for problem in problems:
            print("FAIL: %s" % problem)
        return 1
    print(
        "boss AI slow oracle self-test passed: %d payloads + %d merge rows"
        % (len(fixture["rows"]), len(fixture["merge_rows"]))
    )
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
        print("wrote %s (%d rows)" % (FIXTURE.name, len(fixture["rows"]) + len(fixture["merge_rows"])))
        return 0
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if fixture != committed:
        print("FAIL: fixture drift vs %s" % FIXTURE.name)
        return 1
    return _self_test(fixture)


if __name__ == "__main__":
    raise SystemExit(main())
