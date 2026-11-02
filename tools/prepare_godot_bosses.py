#!/usr/bin/env python3
"""Prepare the native bosses/ migration contract and closed-world pygame oracle.

    python tools/prepare_godot_bosses.py           # write contract + fixture
    python tools/prepare_godot_bosses.py --check   # fail closed on any drift
    python tools/prepare_godot_bosses.py --bake    # re-bake sprites, then write

The contract covers every tracked file in bosses/, the generated renderer index,
all 216 baked boss sprite strips, the pristine->final normalization pipeline, and
the runtime constants. The fixture is produced by the real pygame Boss class and
the existing smart-AI harness; no gameplay formula is reimplemented here.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import hashlib
import importlib
import io
import json
import math
import os
from pathlib import Path
import sys
import types
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
SOURCE_DIR = ROOT / "bosses"
CONTRACT = PROJECT / "data/bosses.json"
FIXTURE = PROJECT / "tests/fixtures/bosses_parity.json"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

PRISTINE_BOSS_FIELDS = (
    "hp", "damage", "ability_damage",
    "skill_q_damage", "skill_w_damage", "skill_e_damage", "skill_r_damage",
)
PRISTINE_UNLOCK_FIELDS = (
    "cost", "hp", "damage", "attack_cooldown", "skill_damage", "range", "skill_range", "role",
)
EXPECTED_HELPERS = {"__init__.py", "_boss_index.py", "base_boss.py", "boss_data.py"}
EXPECTED_RENDERERS = {f"level{i}.py" for i in range(1, 55)}
EXPECTED_V4 = {"razak_v4.py", "nyzrak_v4.py", "thalgryn_v4.py"}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _jsonable(value):
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise AssertionError(f"Non-ffinite boss value: {value!r}")
        return round(value, 9)
    return value


def _text(value) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, indent=2,
                      allow_nan=False, sort_keys=True) + "\n"


def _literals(path: Path, names: set[str]) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    out[target.id] = ast.literal_eval(node.value)
    missing = sorted(names - set(out))
    if missing:
        raise AssertionError(f"Missing literal(s) in {path.name}: {missing}")
    return out


def _slim(table: dict) -> dict:
    out = {}
    for key, row in table.items():
        slim = {"boss_class": row.get("boss_class", "mini")}
        for field in PRISTINE_BOSS_FIELDS:
            if field in row:
                slim[field] = row[field]
        unlock = row.get("hero_unlock")
        if isinstance(unlock, dict):
            slim["hero_unlock"] = {f: unlock[f] for f in PRISTINE_UNLOCK_FIELDS if f in unlock}
        elif unlock is not None:
            slim["hero_unlock"] = None
        out[key] = slim
    return out


def _inventory() -> dict:
    files = sorted(p for p in SOURCE_DIR.iterdir() if p.is_file() and p.suffix == ".py")
    names = {p.name for p in files}
    expected = EXPECTED_HELPERS | EXPECTED_RENDERERS | EXPECTED_V4
    if names != expected:
        raise AssertionError(
            f"bosses/ closed world changed: missing={sorted(expected - names)} "
            f"extra={sorted(names - expected)}"
        )
    rows = {}
    for path in files:
        data = path.read_bytes()
        role = ("renderer" if path.name in EXPECTED_RENDERERS else
                "renderer_v4" if path.name in EXPECTED_V4 else
                "data" if path.name == "boss_data.py" else
                "runtime" if path.name == "base_boss.py" else
                "index" if path.name == "_boss_index.py" else "package")
        rows[path.name] = {"sha256": _sha(data), "lines": data.count(b"\n"), "role": role}
    return rows


def _renderer_closure(module: str, inventory: dict) -> list[str]:
    """Hash the renderer module plus its bosses/*.py dependencies (v4 rigs)."""
    seen: set[str] = set()
    todo = [module]
    while todo:
        name = todo.pop()
        filename = name + ".py"
        if name in seen or filename not in inventory:
            continue
        seen.add(name)
        tree = ast.parse((SOURCE_DIR / filename).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("bosses."):
                todo.append(node.module.split(".", 1)[1])
    return sorted(seen)


def _smart_and_kite() -> tuple[list[str], list[str]]:
    tree = ast.parse((SOURCE_DIR / "base_boss.py").read_text(encoding="utf-8"))
    update = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "update")
    smart: list[str] = []
    kite: list[str] = []
    for node in ast.walk(update):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            cmp = node.test
            if (len(cmp.ops) == 1 and isinstance(cmp.ops[0], ast.Eq)
                    and isinstance(cmp.left, ast.Attribute) and cmp.left.attr == "boss_type"
                    and isinstance(cmp.comparators[0], ast.Constant)):
                smart.append(cmp.comparators[0].value)
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.In):
            if (isinstance(node.left, ast.Attribute) and node.left.attr == "boss_type"
                    and isinstance(node.comparators[0], (ast.Tuple, ast.List))):
                kite.extend(ast.literal_eval(node.comparators[0]))
    if len(smart) != 79 or len(kite) != 12:
        raise AssertionError(f"Unexpected dispatch coverage: smart={len(smart)} kite={len(kite)}")
    return smart, kite


def _art_row(entry: dict) -> dict:
    row = {}
    for key in ("png", "skills_png", "rage_png"):
        if key not in entry:
            continue
        rel = str(entry[key])
        if not rel.startswith("res://"):
            raise AssertionError(f"Unexpected sprite path: {rel}")
        path = PROJECT / rel[6:]
        if not path.is_file():
            raise AssertionError(f"Missing baked sprite: {rel}")
        row[key] = {"path": rel, "sha256": _sha(path.read_bytes())}
    if "png" not in row:
        raise AssertionError("Boss sprite entry has no base strip")
    return row


def build_contract(baked: dict | None = None) -> dict:
    inventory = _inventory()
    lit = _literals(SOURCE_DIR / "boss_data.py", {
        "MINI_BOSS_WAVES", "MINI_BOSS_TYPES", "LEVEL_TRUE_BOSS", "TRUE_BOSS_TYPES",
        "TRUE_BOSS_HP_CURVE", "TRUE_BOSS_DMG_CURVE", "TRUE_BOSS_ABILITY_CURVE", "MELEE_ROLE_HINTS",
    })
    base_lit = _literals(SOURCE_DIR / "base_boss.py", {"BOSS_LABEL_TOP"})
    index = _literals(SOURCE_DIR / "_boss_index.py", {"BOSS_INDEX"})["BOSS_INDEX"]
    mini, true = lit["MINI_BOSS_TYPES"], lit["TRUE_BOSS_TYPES"]
    all_keys = {**mini, **true}
    if len(mini) != 162 or len(true) != 54 or len(index) != 216 or set(index) != set(all_keys):
        raise AssertionError("Boss catalog/index coverage mismatch")
    if set(base_lit["BOSS_LABEL_TOP"]) != set(all_keys):
        raise AssertionError("BOSS_LABEL_TOP must cover every boss exactly")
    if baked is None:
        baked = json.loads((PROJECT / "data/baked_units.json").read_text(encoding="utf-8"))
    units = baked.get("units", {})
    smart, kite = _smart_and_kite()
    bosses = {}
    tracked = {}
    if CONTRACT.is_file():
        with contextlib.suppress(json.JSONDecodeError, OSError):
            tracked = json.loads(CONTRACT.read_text(encoding="utf-8")).get("bosses", {})
    for key in sorted(all_keys):
        module, draw_fn = index[key]
        entry = units.get(key)
        if not isinstance(entry, dict) or entry.get("renderer") != "boss":
            raise AssertionError(f"Missing baked boss strip for {key}")
        closure = _renderer_closure(module, inventory)
        source_digest = _sha("".join(inventory[m + ".py"]["sha256"] for m in closure).encode())
        art = _art_row(entry)
        old = tracked.get(key, {})
        if old and old.get("source_sha256") != source_digest:
            old_art = old.get("art", {}).get("png", {}).get("sha256")
            if old_art == art["png"]["sha256"]:
                raise AssertionError(
                    f"Renderer source for {key} changed but baked PNG did not; "
                    "run tools/prepare_godot_bosses.py --bake"
                )
        bosses[key] = {
            "boss_class": all_keys[key].get("boss_class", "mini"),
            "module": module, "draw_fn": draw_fn,
            "label_top": base_lit["BOSS_LABEL_TOP"][key],
            "source_modules": closure, "source_sha256": source_digest,
            "art": art,
        }
    return {
        "schema": 1,
        "source": "bosses/",
        "files": inventory,
        "mini_boss_waves": {str(k): v for k, v in lit["MINI_BOSS_WAVES"].items()},
        "level_true_boss": {str(k): v for k, v in lit["LEVEL_TRUE_BOSS"].items()},
        "pristine": {"mini": _slim(mini), "true": _slim(true)},
        "pristine_order": {"mini": list(mini), "true": list(true)},
        "curves": {"hp": lit["TRUE_BOSS_HP_CURVE"], "damage": lit["TRUE_BOSS_DMG_CURVE"],
                   "ability": lit["TRUE_BOSS_ABILITY_CURVE"]},
        "melee_role_hints": list(lit["MELEE_ROLE_HINTS"]),
        "smart_ai": smart, "kite_types": kite,
        "bosses": bosses,
        "counts": {"files": len(inventory), "renderers": len(EXPECTED_RENDERERS),
                   "mini": len(mini), "true": len(true), "smart_ai": len(smart)},
    }


def validate_core(contract: dict, core: dict) -> None:
    mini = core.get("bosses", {}).get("mini", {})
    true = core.get("bosses", {}).get("true", {})
    if set(mini) != set(contract["pristine"]["mini"]) or set(true) != set(contract["pristine"]["true"]):
        raise AssertionError("core_data boss coverage differs from bosses contract")
    levels = core.get("levels", [])
    for level in levels:
        number = str(level.get("level_number"))
        if contract["level_true_boss"].get(number) != level.get("true_boss"):
            raise AssertionError(f"level_true_boss mismatch at level {number}")
        cfg_waves = {str(k): v for k, v in (level.get("mini_bosses") or {}).items()}
        # boss_data.MINI_BOSS_WAVES is the legacy 5/10/15 template; levels/
        # level_data.py owns the live 10/15/25 schedule. The boss order must
        # still match, but the wave numbers are intentionally not rewritten.
        if number == "1" and list(cfg_waves.values()) != list(contract["mini_boss_waves"].values()):
            raise AssertionError("mini_boss_waves order mismatch at level 1")


def _pygame():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        core = importlib.import_module("_core")
    bb = importlib.import_module("bosses.base_boss")
    bd = importlib.import_module("bosses.boss_data")
    return core, bb, bd


class _Probe:
    def __init__(self, idx, x, y, events, frame):
        self.idx = idx
        self.x = float(x)
        self.y = float(y)
        self.team = "blue"
        self.alive = True
        self.hp = 1e9
        self.max_hp = 1e9
        self.attack_timer = 0
        self.slow_amount = 0.0
        self.slow_timer = 0
        self.speed = 2.0
        self._events = events
        self._frame = frame

    def take_damage(self, amount, from_team, **_kw):
        self.hp -= float(amount)
        self._events.append(["dmg", self._frame[0], self.idx, round(float(amount), 3)])
        if self.hp <= 0:
            self.alive = False

    def apply_slow(self, amount, duration):
        self._events.append(["slow", self._frame[0], self.idx, float(amount), float(duration)])
        if amount > self.slow_amount or self.slow_timer < duration:
            self.slow_amount = amount
            self.slow_timer = duration


def _snapshot(boss, probes):
    return {
        "hp": round(float(boss.hp), 3), "x": round(boss.x, 2), "y": round(boss.y, 2),
        "damage": int(boss.damage), "speed": round(float(boss.speed), 6),
        "facing": int(boss.direction), "enraged": bool(boss.is_enraged),
        "attack_timer": int(boss.timer), "ability_timer": int(boss.ability_timer),
        "ability2_timer": int(boss.ability2_timer), "entrance_timer": int(boss.entrance_timer),
        "stun_timer": int(boss.stun_timer), "moving": bool(boss.is_moving),
        "target": boss.target.idx if isinstance(boss.target, _Probe) else None,
        "probes": [{"hp": round(p.hp, 3), "x": round(p.x, 2), "y": round(p.y, 2),
                    "attack_timer": round(p.attack_timer, 3),
                    "slow_amount": p.slow_amount, "slow_timer": p.slow_timer} for p in probes],
    }


def _controller_case(bb, boss_type, scenario):
    boss = bb.Boss(boss_type)
    boss.x, boss.y = 600.0, 400.0
    boss._prev_x, boss._prev_y = boss.x, boss.y
    events = []
    frame = [0]
    probes = [_Probe(0, 630.0, 400.0, events, frame), _Probe(1, 660.0, 420.0, events, frame)]
    frames = 90
    if scenario == "entrance":
        probes = []
    elif scenario == "stun":
        boss.entrance_timer = 0
        boss.apply_stun(40)
    elif scenario == "kite":
        boss.entrance_timer = 0
        probes = [_Probe(0, 600.0 + 230.0, 400.0, events, frame)]
    elif scenario == "lane":
        boss.entrance_timer = 0
        boss.lane_path = [(100.0, 620.0), (400.0, 400.0), (600.0, 400.0)]
        boss.waypoint_index = 2
        probes = []
        frames = 120
    elif scenario == "heal":
        boss.entrance_timer = 0
        boss.hp = int(boss.max_hp * 0.2)
        probes = []
    else:
        boss.entrance_timer = 0
    steps = []
    for frame[0] in range(frames):
        boss.update(probes, [], [])
        steps.append(_snapshot(boss, probes))
    return {"boss_type": boss_type, "scenario": scenario, "frames": frames,
            "events": events, "steps": steps}


def _combat_cases(bb):
    cases = []
    specs = [
        ("physical", 1000, "normal", "physical", 0, 0.0, False, 0.5),
        ("magic", 1000, "normal", "magic", 0, 0.0, False, 0.5),
        ("fire", 1000, "fire", "", 0, 0.0, False, 0.5),
        ("amp_shred", 1000, "normal", "physical", 5, 0.25, False, 0.5),
        ("defense", 1000, "normal", "physical", 0, 0.0, True, 0.5),
        ("cap", 10 ** 9, "normal", "physical", 0, 0.0, False, 0.5),
        ("blind_miss", 1000, "normal", "physical", 0, 0.0, False, 0.1),
        ("blind_hit", 1000, "normal", "physical", 0, 0.0, False, 0.9),
        ("true_strike", 1000, "normal", "physical", 0, 0.0, False, 0.1, True),
        ("lethal", 10 ** 9, "normal", "physical", 0, 0.0, False, 0.5),
    ]
    for spec in specs:
        name, amount, dtype, school, shred, amp, defense, roll = spec[:8]
        true_strike = spec[8] if len(spec) > 8 else False
        boss = bb.Boss("gornak")
        boss.entrance_timer = 0
        if name == "lethal":
            boss.max_damage_per_hit = 10 ** 9
        boss.armor_shred_amount = shred
        boss.armor_shred_timer = 100 if shred else 0
        boss.dmg_amp_amount = amp
        boss.dmg_amp_timer = 100 if amp else 0
        boss.defense_boost = defense
        source = types.SimpleNamespace(
            damage_dealt=0, blind_timer=100, blind_amount=0.5,
            items=types.SimpleNamespace(has_true_strike=lambda: true_strike))
        with mock.patch.object(bb.random, "random", return_value=roll):
            before = boss.hp
            boss.take_damage(amount, "blue", dtype, source=source, school=school or None)
        cases.append({
            "name": name, "boss_type": "gornak", "amount": amount, "damage_type": dtype,
            "school": school, "shred": shred, "amp": amp, "defense": defense,
            "roll": roll, "true_strike": true_strike,
            "cap_override": boss.max_damage_per_hit,
            "expected": {"hp": round(float(boss.hp), 3), "dealt": round(before - boss.hp, 3),
                         "alive": bool(boss.alive), "defeated": bool(boss.defeated),
                         "source_dealt": source.damage_dealt, "hurt_flash": boss.hurt_flash_timer},
        })
    return cases


def build_oracle() -> dict:
    core, bb, bd = _pygame()
    legacy = importlib.import_module("test_godot_match_parity")
    with contextlib.redirect_stdout(io.StringIO()):
        runtime = legacy.make_boss_fixture()
        smart = legacy.make_boss_smart_ai_fixture()
    controller = []
    for boss_type, scenario in [
        ("gornak", "basic"), ("abaddon", "basic"), ("krobellus", "basic"),
        ("morgath", "kite"), ("ancient_apparition", "kite"),
        ("gornak", "entrance"), ("gornak", "stun"), ("gornak", "lane"),
        ("abaddon", "heal"), ("kunkka", "heal"),
    ]:
        controller.append(_controller_case(bb, boss_type, scenario))
    final_slim = {"mini": _slim(bd.MINI_BOSS_TYPES), "true": _slim(bd.TRUE_BOSS_TYPES)}
    trend_cases = []
    for values in ([], [(100, 10.0)], [(100, 1.0), (100, 3.0)],
                   [(100, 10.0), (200, 20.0), (300, 35.0)]):
        a, b = bd._hero_unlock_trend(values)
        trend_cases.append({"values": values, "a": a, "b": b})
    return {
        "schema": 1,
        "source_sha256": _sha((SOURCE_DIR / "base_boss.py").read_bytes()),
        "normalization": {"final": final_slim, "trend": trend_cases,
                          "slots": [[w, bd._slot_of_mini_wave(w)] for w in (10, 12, 13, 21, 22, 30)]},
        "runtime": runtime,
        "smart_ai": smart,
        "controller": controller,
        "combat": _combat_cases(bb),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--bake", action="store_true")
    args = parser.parse_args()
    try:
        if args.bake:
            import prepare_godot_entities as entities
            entities.bake()
        contract = build_contract()
        core = json.loads((PROJECT / "data/core_data.json").read_text(encoding="utf-8"))
        validate_core(contract, core)
        oracle = build_oracle()
        contract_text, oracle_text = _text(contract), _text(oracle)
        if args.check:
            if not CONTRACT.is_file() or not FIXTURE.is_file():
                raise AssertionError("Missing bosses contract/fixture; run prepare first")
            if CONTRACT.read_text(encoding="utf-8") != contract_text:
                raise AssertionError("Stale bosses contract; run tools/prepare_godot_bosses.py")
            if FIXTURE.read_text(encoding="utf-8") != oracle_text:
                raise AssertionError("Stale bosses oracle; run tools/prepare_godot_bosses.py")
        else:
            CONTRACT.parent.mkdir(parents=True, exist_ok=True)
            FIXTURE.parent.mkdir(parents=True, exist_ok=True)
            CONTRACT.write_text(contract_text, encoding="utf-8")
            FIXTURE.write_text(oracle_text, encoding="utf-8")
    except (AssertionError, ValueError, TypeError, KeyError, OSError, ImportError) as exc:
        print(f"bosses preparation failed: {exc}", file=sys.stderr)
        return 1
    counts = contract["counts"]
    print(f"{'Verified' if args.check else 'Prepared'} bosses: {counts['files']} files, "
          f"{counts['mini']} mini + {counts['true']} true, {counts['smart_ai']} smart-AI, "
          f"{len(oracle['controller'])} controller cases, {len(oracle['combat'])} combat cases; "
          f"sha256={oracle['source_sha256'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
