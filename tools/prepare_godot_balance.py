#!/usr/bin/env python3
"""Export hero_balance.py to the active Godot project (pure Python, no pygame).

Python remains the calibration oracle. This tool never invents new balance
numbers: it replays the real module over the same pre-balance catalog used by
prepare_godot_core.py, verifies the tracked core catalog, writes the native
constants/pristine contract, and writes a runtime parity fixture. --check is a
fail-closed exact-byte gate.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics as st
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
SOURCE = ROOT / "hero_balance.py"
CONTRACT = PROJECT / "data/hero_balance.json"
FIXTURE = PROJECT / "tests/fixtures/hero_balance_parity.json"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
import prepare_godot_core as core_prep  # noqa: E402

BALANCE_FIELDS = (
    "hp", "damage", "skill_damage", "skill_q_damage", "skill_w_damage",
    "skill_e_damage", "skill_r_damage", "attack_cooldown", "skill_cooldown",
    "armor", "magic_resist", "cost", "unlock_cost", "is_boss_hero", "boss_class",
    "unlock_require_boss", "dmg_type",
)
FINAL_FIELDS = ("hp", "damage", "skill_damage", "skill_q_damage", "skill_w_damage",
                "skill_e_damage", "skill_r_damage")
CATCHUP_UNLOCKS = (0, 1, 5, 11, 12, 13, 24, 216)
CATCHUP_LEVELS = (0, 1, 2, 3, 5, 8, 9, 20)


def source_module():
    spec = importlib.util.spec_from_file_location("mystic_balance_export", SOURCE)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(stats: dict) -> dict:
    return {key: copy.deepcopy(stats[key]) for key in BALANCE_FIELDS if key in stats}


def _jsonable(value):
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, float) and not math.isfinite(value):
        raise AssertionError(f"Non-finite balance value: {value!r}")
    return value


def _text(value: dict) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, indent=2, allow_nan=False, sort_keys=True) + "\n"


def raw_catalog() -> dict:
    core = core_prep.assignments(ROOT / "_core.py", upper_only=True)
    return core_prep.raw_hero_catalog(core)


@contextlib.contextmanager
def _game(purchased=None):
    main_mod = sys.modules["__main__"]
    had = hasattr(main_mod, "game_instance")
    old = getattr(main_mod, "game_instance", None)
    main_mod.game_instance = None if purchased is None else types.SimpleNamespace(
        purchased_heroes=list(purchased), save_data={"purchased_heroes": list(purchased)})
    try:
        yield
    finally:
        if had:
            main_mod.game_instance = old
        elif hasattr(main_mod, "game_instance"):
            del main_mod.game_instance


def _reset_last(module) -> None:
    module.LAST.clear()
    module.LAST.update({"table": {}, "pool": {}, "parity": {}})


def validate_final(final: dict, core: dict) -> None:
    heroes = core.get("heroes", {})
    if set(final) != set(heroes):
        raise AssertionError("Balance catalog coverage differs from core_data heroes")
    for key, stats in final.items():
        tracked = heroes[key]
        for field in FINAL_FIELDS:
            if stats.get(field) != tracked.get(field):
                raise AssertionError(
                    f"Stale core balance for {key}.{field}: "
                    f"oracle={stats.get(field)!r} tracked={tracked.get(field)!r}; "
                    "run tools/prepare_godot_core.py"
                )
        if bool(stats.get("is_boss_hero")) != ("__bal" in tracked):
            raise AssertionError(f"Balance metadata presence differs for {key}")
        if stats.get("is_boss_hero") and stats.get("__bal") != tracked.get("__bal"):
            raise AssertionError(f"Stale __bal metadata for {key}; run tools/prepare_godot_core.py")


def build_contract(module=None, core: dict | None = None, raw: dict | None = None) -> dict:
    module = module or source_module()
    raw = raw if raw is not None else raw_catalog()
    if core is None:
        core = json.loads((PROJECT / "data/core_data.json").read_text(encoding="utf-8"))
    final = copy.deepcopy(raw)
    with _game():
        _reset_last(module)
        module.apply_to_catalog(final)
    validate_final(final, core)
    pristine = module.pristine_boss_stats()
    if len(raw) != 222 or len(pristine) != 216:
        raise AssertionError(f"Unexpected balance coverage: raw={len(raw)} pristine={len(pristine)}")
    contract = {
        "schema": 1,
        "source": "hero_balance.py",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "switches": {
            "enable_rebudget": module.ENABLE_REBUDGET,
            "enable_school_mod": module.ENABLE_SCHOOL_MOD,
            "enable_starter_catchup": module.ENABLE_STARTER_CATCHUP,
            "school_parity": module.SCHOOL_PARITY,
            "cell_parity": module.CELL_PARITY,
            "pool_mean_anchor": module.POOL_MEAN_ANCHOR,
            "final_fixpoint": module.FINAL_FIXPOINT,
        },
        "constants": {
            "w_dps": module.W_DPS, "w_ehp": module.W_EHP, "ehp_per_hp": module.EHP_PER_HP,
            "target_ratio": module.TARGET_RATIO, "school_ratio_bonus": module.SCHOOL_RATIO_BONUS,
            "ratio_blend": module.RATIO_BLEND, "budget_compress": module.BUDGET_COMPRESS,
            "style_power": module.STYLE_POWER, "hp_mult_range": module.HP_MULT_RANGE,
            "dmg_mult_range": module.DMG_MULT_RANGE, "school_parity_cap": module.SCHOOL_PARITY_CAP,
            "cell_parity_cap": module.CELL_PARITY_CAP, "pool_mean_tol_max": module.POOL_MEAN_TOL_MAX,
            "final_corr_cap": module.FINAL_CORR_CAP, "cost_bucket": module.COST_BUCKET,
            "cost_eff_band": module.COST_EFF_BAND, "cost_eff_damp": module.COST_EFF_DAMP,
            "cost_eff_min_group": module.COST_EFF_MIN_GROUP, "meta_eff_band": module.META_EFF_BAND,
            "meta_eff_damp": module.META_EFF_DAMP, "tower_armor_at_l3": module.TOWER_ARMOR_AT_L3,
            "armor_factor": module.ARMOR_FACTOR, "tower_phys_factor": module.TOWER_PHYS_FACTOR,
            "school_mod_cap": module.SCHOOL_MOD_CAP, "starter_catchup_max": module.STARTER_CATCHUP_MAX,
            "starter_catchup_ref": module.STARTER_CATCHUP_REF, "starter_catchup_lv0": module.STARTER_CATCHUP_LV0,
            "starter_catchup_lv1": module.STARTER_CATCHUP_LV1, "starter_catchup_decay": module.STARTER_CATCHUP_DECAY,
        },
        "starter_heroes": list(module.STARTER_HEROES),
        "pristine_boss_stats": {key: _row(value) for key, value in pristine.items()},
    }
    return _jsonable(contract)


def _helpers(module, raw: dict, pristine: dict, table: dict) -> dict:
    import hero_archetypes as ha
    boss_keys = list(pristine)
    round_cases = [0.5, 1.5, 2.5, 7.5, 8.5, 12.5, 1733.5, 2026.5, -0.5, -1.5, -2.5,
                   -12.5, 0.0, 3.0, 123456.789, -123456.789, 0.499999999999, 0.500000000001]
    round_n_cases = []
    for n, vals in ((1, [12.2, 17.74074074074074, 0.05, 0.15, 2.25, -0.05, 587.55]),
                    (3, [1.421, 1.2370430282389036, 0.187, 0.0005, 1.0005, -1.0005, 16.1065]),
                    (4, [1.4, 1.272, 1.0, 1.00005, 0.00005, -0.00005, 2.00005, 1.46475,
                         1.0937411506268484, 0.999890763, 1.000109263])):
        for value in vals:
            round_n_cases.append({"n": n, "in": value, "out": round(value, n)})
    budgets = sorted(module.metrics(pristine[key])["budget"] for key in boss_keys)
    ratios = sorted(module.metrics(pristine[key])["ehp"] / module.metrics(pristine[key])["dps"]
                    for key in boss_keys)
    med_dps = st.median([module.metrics(pristine[key])["dps"] for key in boss_keys])
    med_ehp = st.median([module.metrics(pristine[key])["ehp"] for key in boss_keys])
    power_cases, eff_cases = [], []
    for key in boss_keys[:2] + boss_keys[162:164] + boss_keys[100:101] + boss_keys[200:201]:
        m = module.metrics(pristine[key])
        t = table[key]
        power_cases.append({"hero": key, "m": m, "y": t["hp"], "x_dmg": t["dmg"],
                            "x_sk": t["skill"], "med_dps": med_dps, "med_ehp": med_ehp,
                            "out": module._final_power(m, t["hp"], t["dmg"], t["skill"], med_dps, med_ehp)})
        dps = (m["dmg"] * t["dmg"]) * 60.0 / m["cd"] + (m["skill"] * t["skill"]) * 60.0 / m["skcd"]
        eff_cases.append({"hero": key, "stats": _row(pristine[key]), "m": m, "dps": dps,
                          "out": module._eff_dps(ha, ha.BOSS_RESISTANCES, key, dict(pristine[key]), m, dps)})
    return {
        "py_round": [[value, round(value)] for value in round_cases],
        "py_round_n": round_n_cases,
        "median": [{"in": [], "out": 0.0}, {"in": [5.0], "out": 5.0},
                   {"in": [3.0, 1.0, 2.0], "out": 2.0}, {"in": [1.0, 2.0], "out": 1.5},
                   {"in": budgets, "out": st.median(budgets)}, {"in": ratios, "out": st.median(ratios)}],
        "fmean": [{"in": [], "out": 0.0}, {"in": [1.0, 2.0, 3.0], "out": 2.0},
                  {"in": budgets, "out": st.fmean(budgets)}, {"in": budgets[:10], "out": st.fmean(budgets[:10])}],
        "school_mod": [[school, module.school_mod(school)]
                       for school in ("physical", "PHYSICAL", "magic", "MAGIC", "")],
        "tower_phys_factor": module.TOWER_PHYS_FACTOR,
        "level_factor": [[level, module.starter_level_factor(level)] for level in list(range(0, 11)) + [20]],
        "final_power": power_cases,
        "eff_dps": eff_cases,
    }


def build_oracle(module=None, raw: dict | None = None) -> dict:
    module = module or source_module()
    import hero_archetypes as ha
    raw = raw if raw is not None else raw_catalog()
    pristine = module.pristine_boss_stats()
    starters = list(module.STARTER_HEROES)
    boss_keys = list(pristine)
    with _game():
        _reset_last(module)
        resolve_table = copy.deepcopy(module.resolve_catalog(copy.deepcopy(raw)))
        _reset_last(module)
        catalog = copy.deepcopy(raw)
        module.apply_to_catalog(catalog)
        table = copy.deepcopy(module.LAST["table"])
        last = {key: copy.deepcopy(value) for key, value in module.LAST.items() if key != "table"}
    final_stats = {key: {field: value.get(field) for field in FINAL_FIELDS}
                   for key, value in catalog.items() if value.get("is_boss_hero")}
    for key, value in catalog.items():
        if not value.get("is_boss_hero") and value != raw[key]:
            raise AssertionError(f"Starter catalog was modified by apply_to_catalog: {key}")
    mult_grid = []
    grid_heroes = starters + ["gornak", boss_keys[162]]
    for hero in grid_heroes:
        for unlocks in CATCHUP_UNLOCKS:
            for level in CATCHUP_LEVELS:
                hp, dmg = module.starter_catchup(hero, unlocks, level)
                mult_grid.append({"hero": hero, "unlocks": unlocks, "level": level, "hp": hp, "dmg": dmg})
    stat_cases = []
    for hero in starters:
        for unlocks, level in ((0, 1), (5, 3), (11, 1), (12, 8), (24, 5), (216, 1)):
            hp, dmg = module.starter_catchup_stats(hero, raw[hero], unlocks, level)
            stat_cases.append({"hero": hero, "unlocks": unlocks, "level": level,
                               "base_hp": raw[hero]["hp"], "base_damage": raw[hero]["damage"],
                               "hp": hp, "damage": dmg})
    unlock_lists = [None, [], starters, starters + starters[:3], ["gornak"],
                    ["kaizen", "gornak", "vex", boss_keys[162]], ["gornak", "gornak", boss_keys[162]], boss_keys]
    unlock_counts = [{"purchased": purchased, "unlocks": module.boss_unlocks_for_purchases(purchased)}
                     for purchased in unlock_lists]
    rows = []
    for key in boss_keys:
        entry = ha.BOSS_RESISTANCES[key]
        rows.append({"boss_type": key, "boss_class": entry["boss_class"], "profile": entry["profile"],
                     "dps": module.metrics(pristine[key])["dps"], "dmg_type": ha.get_archetype(key)["dmg_type"]})
    calibrated, calibration_report = module.calibrate_boss_resistances(rows)
    band_catalog = copy.deepcopy(catalog)
    band_info = module._final_fixpoint(band_catalog, cell_band=[1.0 / 1.1, 1.1])
    band_damage = {key: {"damage": value["damage"], "skill_damage": value["skill_damage"]}
                   for key, value in band_catalog.items() if value.get("is_boss_hero")}
    variants = []
    variant_src = copy.deepcopy(raw)
    for key, value in pristine.items():
        variant_src[key] = copy.deepcopy(value)
    saved_last = copy.deepcopy(module.LAST)
    try:
        for unlocks in (5, 216):
            purchased = starters[:2] + boss_keys[:unlocks]
            with _game(purchased):
                _reset_last(module)
                resolved = module.resolve_catalog(variant_src)
            variants.append({"unlocks": unlocks, "level": 1,
                             "starters": {hero: resolved[hero] for hero in starters}})
    finally:
        module.LAST.clear()
        module.LAST.update(saved_last)
    return {
        "schema": 1,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "raw_catalog": {key: _row(value) for key, value in raw.items()},
        "pristine": {key: _row(value) for key, value in pristine.items()},
        "resolve_table": resolve_table,
        "table": table,
        "final_stats": final_stats,
        "metrics": {key: module.metrics(value) for key, value in raw.items()},
        "last": last,
        "catchup": {"mult_grid": mult_grid, "stat_cases": stat_cases,
                    "starter_heroes": starters, "unlock_counts": unlock_counts},
        "calibrate": {"rows": rows, "res": calibrated, "report": calibration_report},
        "helpers": _helpers(module, raw, pristine, table),
        "fix_band": {"cell_band": [1.0 / 1.1, 1.1], "info": band_info, "damage": band_damage},
        "resolve_variants": variants,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify tracked files; write nothing")
    args = parser.parse_args()
    try:
        module = source_module()
        raw = raw_catalog()
        contract = build_contract(module, raw=raw)
        oracle = build_oracle(module, raw)
        outputs = {CONTRACT: _text(contract), FIXTURE: _text(oracle)}
        if args.check:
            stale = [str(path.relative_to(ROOT)) for path, text in outputs.items()
                     if not path.is_file() or path.read_text(encoding="utf-8") != text]
            if stale:
                parser.exit(1, "Stale balance data: %s; run tools/prepare_godot_balance.py\n" % ", ".join(stale))
        else:
            for path, text in outputs.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix(path.suffix + ".tmp")
                temporary.write_text(text, encoding="utf-8")
                temporary.replace(path)
    except (AssertionError, ValueError, TypeError, KeyError, OSError, ImportError) as exc:
        parser.exit(1, f"Balance preparation failed: {exc}\n")
    digest = hashlib.sha256(outputs[CONTRACT].encode()).hexdigest()[:12]
    print(f"{'Verified' if args.check else 'Prepared'} hero balance: {len(contract['pristine_boss_stats'])} pristine bosses, "
          f"{len(contract['starter_heroes'])} starters; sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
