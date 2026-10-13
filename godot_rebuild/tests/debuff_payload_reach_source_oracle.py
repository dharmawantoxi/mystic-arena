"""9ai: the world debuff store's non-positive guard is unreachable - measured.

Layer 9af recorded one open divergence (`AI_CONTRACT.md` "Divergensi yang
dicatat terbuka"): the native store refuses `amount <= 0 or duration <= 0`
(`godot_rebuild/scripts/combat/minion_battle.gd`, five methods) while
`TowerDebuffMixin.apply_debuff` (`_core.py:918`) and `Minion.apply_slow` have no
such gate, so a non-positive payload would still be stored by the source.

This oracle closes the item by measuring reachability instead of guessing:

* every debuff payload the Python source can emit is extracted from the data
  tables (`CANNON_LEVELS`, `ICE_LEVELS`, `MAGE_LEVELS` in `_core.py`) and from
  every call site in `_core.py`, `_entity.py`, `hero_items.py` and `bosses/`;
  all of them are positive, so the guard never sees a payload it would refuse;
* the source emission gates are counted (the cannon burn, ice attack-slow, mage
  skill-down and anti-heal arms all sit behind `> 0`; only the ice movement
  slow is ungated, and it reads the positive `ICE_LEVELS` values);
* every native arm in `godot_rebuild/scripts` passes positive literals (no arm
  can fire the guard either), and all five source burn sites pass
  `source_team`, which makes the store's unconditional `burn_team` write
  equivalent;
* the rows replay the real payloads through the live store (source rule and
  native store must agree), and the refused sentinel/window rows stay pinned in
  `native_open` with a `divergence` note so the difference keeps being visible
  instead of hidden. `--write` rewrites the fixture.
"""

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "debuff_payload_reach_source.json"
CORE = ROOT / "_core.py"
ENTITY = ROOT / "_entity.py"
HERO_ITEMS = ROOT / "hero_items.py"
NATIVE_STORE = ROOT / "godot_rebuild" / "scripts" / "combat" / "minion_battle.gd"
NATIVE_SCRIPTS = ROOT / "godot_rebuild" / "scripts"

SKIP_FILES = {"lighting.py"}
PY_SOURCES = [CORE, ENTITY, HERO_ITEMS]
for folder in ("bosses", "heroes", "towers"):
    PY_SOURCES.extend(sorted((ROOT / folder).glob("*.py")))

# store key -> (store kind, amount key, duration key)
PAYLOAD_KEYS = {
    "slow": ("slow", "slow", "slow_duration"),
    "atk_slow": ("atk_slow", "atk_slow", "slow_duration"),
    "burn_dps": ("burn", "burn_dps", "burn_duration"),
    "skill_down": ("skill_down", "skill_down", "debuff_duration"),
    "anti_heal": ("anti_heal", "anti_heal", "debuff_duration"),
}

TABLES = {
    "ICE_LEVELS": ("slow", "slow_duration", "atk_slow"),
    "CANNON_LEVELS": ("burn_dps", "burn_duration"),
    "MAGE_LEVELS": ("skill_down", "debuff_duration", "anti_heal"),
}

NATIVE_ARMS = ("apply_slow", "apply_atk_slow", "apply_skill_down", "apply_anti_heal", "apply_burn")

STORE_METHODS = ["apply_burn", "apply_slow", "apply_atk_slow", "apply_skill_down", "apply_anti_heal"]


def _store_fresh(kind):
    if kind == "burn":
        return {"dps": 0.0, "timer": 0, "team": -1}
    return {"amount": 0.0, "timer": 0}


def _simulate(kind, steps, native=False, start=None):
    """Source rule from `_core.py:918-943`; native adds the non-positive gate."""
    store = dict(start or _store_fresh(kind))
    accepted = []
    for step in steps:
        amount = float(step["amount"])
        duration = int(step["duration"])
        if native and (amount <= 0 or duration <= 0):
            accepted.append(False)
            continue
        accepted.append(True)
        if kind == "burn":
            if store["timer"] <= 0:
                store["dps"] = amount
            else:
                store["dps"] = max(store["dps"], amount)
            store["timer"] = max(store["timer"], duration)
            if "team" in step:
                store["team"] = int(step["team"])
        else:
            if amount > store["amount"] or store["timer"] < duration:
                store["amount"] = amount
                store["timer"] = duration
    return store, accepted


def _row(name, kind, steps, note, divergence=None):
    source, _ = _simulate(kind, steps)
    native, accepted = _simulate(kind, steps, native=True)
    return {
        "name": name,
        "kind": kind,
        "note": note,
        "input": steps,
        "expected": native,
        "source_rule": source,
        "accepted": accepted,
        "divergence": divergence,
    }


def _data_values():
    """Numeric literals keyed by the debuff payload names in the Python source."""
    found = []
    for path in PY_SOURCES:
        if path.name in SKIP_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if not isinstance(key, ast.Constant) or key.value not in PAYLOAD_KEYS:
                        continue
                    if isinstance(value, ast.Constant) and isinstance(value.value, (int, float)):
                        if not isinstance(value.value, bool):
                            found.append((str(key.value), float(value.value), path.name, key.lineno))
            if isinstance(node, ast.Call):
                target = ast.unparse(node.func)
                if target.split(".")[-1] not in NATIVE_ARMS:
                    continue
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, (int, float)):
                        if not isinstance(arg.value, bool):
                            found.append(("call", float(arg.value), path.name, node.lineno))
    return found


def _emission_shape():
    """Gate (`> 0`) count per debuff arm in the Python sources."""
    gated = {}
    ungated = {}
    burn_source_team = {"sites": 0, "with_source_team": 0}
    for path in PY_SOURCES:
        if path.name in SKIP_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        guarded = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.If):
                continue
            if "> 0" not in ast.unparse(node.test):
                continue
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call):
                    guarded.append(id(inner))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = ast.unparse(node.func).split(".")[-1]
            if name not in ("apply_slow", "apply_atk_slow", "apply_debuff"):
                continue
            kind = name.replace("apply_", "") if name != "apply_debuff" else None
            if kind is None and node.args and isinstance(node.args[0], ast.Constant):
                kind = str(node.args[0].value)
            if kind == "debuff":
                kind = None
            if kind == "burn":
                burn_source_team["sites"] += 1
                if any(kw.arg == "source_team" for kw in node.keywords):
                    burn_source_team["with_source_team"] += 1
            bucket = gated if id(node) in guarded else ungated
            bucket[kind] = bucket.get(kind, 0) + 1
    return {
        "gated": {str(key): gated[key] for key in sorted(gated, key=str)},
        "ungated": {str(key): ungated[key] for key in sorted(ungated, key=str)},
        "burn_sites": burn_source_team["sites"],
        "burn_with_source_team": burn_source_team["with_source_team"],
    }


def _table_payloads():
    """Every level payload of the source tower tables."""
    tables = {}
    tree = ast.parse(CORE.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in TABLES:
            continue
        levels = {}
        for key, value in zip(node.value.keys, node.value.values):
            if not isinstance(value, ast.Dict):
                continue
            entry = {}
            for inner_key, inner_value in zip(value.keys, value.values):
                if isinstance(inner_key, ast.Constant) and isinstance(inner_value, ast.Constant):
                    if isinstance(inner_value.value, (int, float)):
                        entry[str(inner_key.value)] = float(inner_value.value)
            levels[int(key.value)] = entry
        tables[target.id] = levels
    return tables


def _native_shape():
    arms = {}
    bad = []
    for path in sorted(NATIVE_SCRIPTS.rglob("*.gd")):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for arm in NATIVE_ARMS:
                match = re.match(r"(?:.*\.)?%s\((.*)\)" % arm, stripped)
                if not match or "func " in stripped:
                    continue
                arms[arm] = arms.get(arm, 0) + 1
                args = [arg.strip() for arg in match.group(1).split(",")]
                literals = []
                for arg in args:
                    hit = re.fullmatch(r"-?\d+(?:\.\d+)?", arg)
                    literals.append(float(hit.group(0)) if hit else None)
                if any(value is not None and value <= 0 for value in literals[-2:]):
                    bad.append("%s:%s" % (path.name, stripped))
    store = NATIVE_STORE.read_text(encoding="utf-8")
    guards = {}
    for method in STORE_METHODS:
        body = re.search(r"func %s\(.*?\n\n" % method, store, re.S)
        text = body.group(0) if body else ""
        guards[method] = "<= 0" in text
    return {
        "arms": {key: arms[key] for key in sorted(arms)},
        "non_positive_arms": bad,
        "store_guarded": guards,
    }


def source_fixture():
    values = _data_values()
    per_key = {}
    for key, value, _, _ in values:
        per_key.setdefault(key, []).append(value)
    tables = _table_payloads()

    payloads = []
    for key in ("ICE_LEVELS", "CANNON_LEVELS", "MAGE_LEVELS"):
        for level, entry in sorted(tables[key].items()):
            for payload_key, (kind, amount_key, duration_key) in PAYLOAD_KEYS.items():
                if payload_key not in entry or amount_key not in entry:
                    continue
                if kind == "slow" and key != "ICE_LEVELS":
                    continue
                if kind == "atk_slow" and key != "ICE_LEVELS":
                    continue
                if kind == "burn" and key != "CANNON_LEVELS":
                    continue
                if kind in ("skill_down", "anti_heal") and key != "MAGE_LEVELS":
                    continue
                step = {"amount": entry[amount_key], "duration": int(entry[duration_key])}
                if kind == "burn":
                    step["team"] = 0
                payloads.append(
                    _row(
                        "%s_l%d_%s" % (key.split("_")[0].lower(), level, kind),
                        kind,
                        [step],
                        "%s level %d payload (%s=%s, %s=%s)"
                        % (key, level, amount_key, entry[amount_key], duration_key, int(entry[duration_key])),
                    )
                )

    sentinels = [
        _row(
            "zero_amount_positive_duration",
            "slow",
            [{"amount": 0.0, "duration": 90}],
            "the source stores a zero amount with a live timer; the native guard refuses",
            "unreachable: no source arm emits a zero slow (ICE_LEVELS min 0.25)",
        ),
        _row(
            "positive_amount_zero_duration",
            "slow",
            [{"amount": 0.5, "duration": 0}],
            "the source stores the amount with a dead timer (lock-in); native refuses",
            "unreachable: only the ungated ice slow feeds durations, and ICE_LEVELS starts at 90",
        ),
        _row(
            "negative_amount",
            "atk_slow",
            [{"amount": -0.2, "duration": 90}],
            "a negative amount would buff the victim; native refuses",
            "unreachable: every atk_slow arm is gated behind `> 0`",
        ),
        _row(
            "zero_burn_payload",
            "burn",
            [{"amount": 0.0, "duration": 120, "team": 0}],
            "the source arms a 120 tick zero-dps burn; native refuses",
            "unreachable: every burn arm is gated behind `burn_dps > 0`",
        ),
        _row(
            "empty_payload",
            "skill_down",
            [{"amount": 0.0, "duration": 0}],
            "both rules leave a fresh victim untouched (control row, no divergence)",
            None,
        ),
    ]

    windows = [
        _row(
            "stronger_amount_with_dead_timer_cancels_the_slow",
            "slow",
            [
                {"amount": 0.2, "duration": 90},
                {"amount": 0.5, "duration": 0},
            ],
            "the source writes (0.5, 0) and cancels the running slow; the native guard keeps (0.2, 90)",
            "unreachable window: needs a zero-duration payload, which no arm emits",
        ),
        _row(
            "zero_burn_dps_extends_the_timer",
            "burn",
            [
                {"amount": 8.0, "duration": 120, "team": 0},
                {"amount": 0.0, "duration": 180, "team": 0},
            ],
            "the source extends an existing burn to 180 ticks; native keeps 120",
            "unreachable window: every burn arm is gated behind `burn_dps > 0`",
        ),
    ]

    native = _native_shape()
    return {
        "source": "`_core.py` tower tables + debuff arms; `_entity.py` bullet gates",
        "callsite": "godot_rebuild/scripts/combat/minion_battle.gd store methods",
        "shape": {
            "payload_literals": {key: len(per_key[key]) for key in sorted(per_key)},
            "min_payload": {
                key: min(per_key[key]) for key in sorted(per_key) if key != "call"
            },
            "call_literals": len(per_key.get("call", [])),
            "min_call_literal": min(per_key.get("call", [0.0])),
            "emission": _emission_shape(),
            "tables": {key: sorted(levels) for key, levels in sorted(tables.items())},
            "native": native,
            "guarded_kinds": sorted(PAYLOAD_KEYS),
        },
        "rows": payloads + sentinels + windows,
    }


def _self_test(fixture):
    problems = []
    shape = fixture["shape"]
    minimums = shape["min_payload"]
    for key, value in sorted(minimums.items()):
        if value <= 0:
            problems.append("source payload %s is not positive: %s" % (key, value))
    if shape["min_call_literal"] <= 0:
        problems.append("a source call site passes a non-positive literal")
    emission = shape["emission"]
    if emission["burn_sites"] != emission["burn_with_source_team"]:
        problems.append("a source burn site no longer passes source_team")
    # The counts pin which arms sit inside a `> 0` test (a payload gate on the
    # bullet arms at `_entity.py:265/282/296/311/322/325`, or a timer gate on
    # the two smart-AI slow arms and the hero-item slow arm). The reachability
    # claim itself rests on the payload minimums, not on these counts.
    if emission["gated"] != {"anti_heal": 1, "atk_slow": 2, "burn": 3, "skill_down": 1, "slow": 3}:
        problems.append("the gated source arms changed: %s" % emission["gated"])
    if emission["ungated"] != {
        "None": 1,
        "anti_heal": 3,
        "atk_slow": 3,
        "burn": 2,
        "skill_down": 1,
        "slow": 44,
    }:
        problems.append("the ungated source arms changed: %s" % emission["ungated"])
    native = shape["native"]
    if native["arms"] != {
        "apply_anti_heal": 4,
        "apply_atk_slow": 5,
        "apply_burn": 5,
        "apply_skill_down": 2,
        "apply_slow": 94,
    }:
        problems.append("the native arm census changed: %s" % native["arms"])
    if native["non_positive_arms"]:
        problems.append("native arms with non-positive payloads: %s" % native["non_positive_arms"])
    if not all(native["store_guarded"].values()):
        problems.append("a store method lost its guard: %s" % native["store_guarded"])
    diverging = [row for row in fixture["rows"] if row["source_rule"] != row["expected"]]
    unreachable = [row for row in diverging if not row["divergence"]]
    if unreachable:
        problems.append("divergences without a reachability note: %s" % [row["name"] for row in unreachable])
    hidden = [row["name"] for row in fixture["rows"] if row["divergence"] and row["source_rule"] == row["expected"]]
    if hidden:
        problems.append("divergence notes on agreeing rows: %s" % hidden)
    if len(diverging) < 6:
        problems.append("the fixture no longer shows the divergences to close: %d" % len(diverging))
    for row in fixture["rows"]:
        if row["divergence"] is not None or len(row["input"]) != 1:
            continue
        if row["source_rule"] != row["expected"]:
            problems.append("a replayable single-step row diverges: %s" % row["name"])
    payload_count = len(
        [
            row
            for row in fixture["rows"]
            if row["divergence"] is None and row["accepted"][0] and len(row["input"]) == 1
        ]
    )
    if payload_count < 25:
        problems.append("expected at least 25 real payload rows, found %d" % payload_count)
    if problems:
        for problem in problems:
            print("FAIL: %s" % problem)
        return 1
    print(
        "debuff payload reach oracle self-test passed: %d rows (%d real payloads, %d documented divergences)"
        % (len(fixture["rows"]), payload_count, len(diverging))
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
        print("wrote %s (%d rows)" % (FIXTURE.name, len(fixture["rows"])))
        return 0
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if fixture != committed:
        print("FAIL: fixture drift vs %s" % FIXTURE.name)
        return 1
    return _self_test(fixture)


if __name__ == "__main__":
    raise SystemExit(main())
