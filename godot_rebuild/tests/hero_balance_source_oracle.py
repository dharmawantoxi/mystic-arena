"""Source oracle for layer 9cj: `hero_balance.py` (935 lines).

The module is the ONLY place hero balance is calibrated. It reads the catalog that
`_core.get_all_hero_types()` assembles, computes one multiplier triple per hero
(hp / damage / skill) and writes the rounded stats back in place, so the shop, the
skill preview and the battle read the same numbers.

This oracle:

* inventories the file (sections, 20 functions, 37 named constants + the
  `W_DPS, W_EHP, EHP_PER_HP` tuple) and classifies EVERY symbol with a target file
  and a token that target must contain;
* builds the REAL catalog (the source `get_all_hero_types`, both definitions, with
  the real `bosses.boss_data` and the real `hero_balance`), snapshots the pristine
  pre-balance rows, and executes the whole pipeline — `resolve_catalog`,
  `apply_to_catalog`, the pool anchor and the audit-formula fixpoint;
* proves the baked native data: the source's post-balance `hp`/`damage`/
  `skill_damage` for all 216 boss heroes must equal `godot_rebuild/data/heroes/*.tres`
  (`max_hp`/`damage`/`base_skill`), and `hero_archetypes.BOSS_RESISTANCES` must equal
  the paired `armor`/`magic_resist` in `data/bosses/boss_stats.json`;
* executes the pure helpers the rebuild now owns natively (`metrics`, `hero_target`,
  `stat_multipliers`, `starter_catchup`, `boss_unlocks_for_purchases`) plus the
  offline calibration (`calibrate_boss_resistances` on the real rows, reduced grid).

Run: python godot_rebuild/tests/hero_balance_source_oracle.py --write
     python godot_rebuild/tests/hero_balance_source_oracle.py --check
"""
import argparse
import ast
import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kaizen_source_oracle import _exec_catalog, _install_stubs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "hero_balance.py"
GODOT = ROOT / "godot_rebuild"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hero_balance_source.json"

sys.path.insert(0, str(ROOT))
import hero_archetypes as ha  # noqa: E402
import hero_balance as hb  # noqa: E402

BALANCE_GD = "godot_rebuild/scripts/data/hero_balance.gd"
ARCH_GD = "godot_rebuild/scripts/data/hero_archetypes.gd"
HEROES_GD = "godot_rebuild/scripts/data/hero_definition.gd"

SECTIONS = [
    ("header", 1, 46),
    ("switches", 47, 55),
    ("rebudget", 56, 79),
    ("guards", 80, 87),
    ("school_mod_constants", 88, 95),
    ("starter_constants", 96, 104),
    ("metrics", 105, 139),
    ("targets", 140, 262),
    ("parity", 263, 354),
    ("resolve", 355, 562),
    ("calibrate", 563, 690),
    ("anchors", 691, 839),
    ("apply", 840, 935),
]

SWITCHES = ("ENABLE_REBUDGET", "ENABLE_SCHOOL_MOD", "ENABLE_STARTER_CATCHUP",
            "SCHOOL_PARITY", "CELL_PARITY", "POOL_MEAN_ANCHOR", "FINAL_FIXPOINT")

# symbol -> (kind, target, token, note)
CLASSIFICATION = {
    "import:statistics": ("folded", BALANCE_GD, "static func _mean(",
                          "fmean/median diganti _mean/_median native"),
    "import:hero_archetypes": ("ported", BALANCE_GD,
                               'const Archetypes = preload("res://scripts/data/hero_archetypes.gd")',
                               "tabel + aritmetika resist diport di layer yang sama"),
    "assign:ENABLE_REBUDGET": ("data", BALANCE_GD, "const ENABLE_REBUDGET := true",
                               "saklar A aktif"),
    "assign:ENABLE_SCHOOL_MOD": ("data", BALANCE_GD, "const ENABLE_SCHOOL_MOD := false",
                                 "hanya dipakai kalau paritas mati"),
    "assign:ENABLE_STARTER_CATCHUP": ("data", BALANCE_GD,
                                      "const ENABLE_STARTER_CATCHUP := true",
                                      "saklar C aktif"),
    "assign:SCHOOL_PARITY": ("data", BALANCE_GD, "const SCHOOL_PARITY := true",
                             "paritas sekolah per kelas boss"),
    "assign:CELL_PARITY": ("data", BALANCE_GD, "const CELL_PARITY := true",
                           "paritas sel arketipe"),
    "assign:POOL_MEAN_ANCHOR": ("data", BALANCE_GD, "const POOL_MEAN_ANCHOR := true",
                                "rata-rata pool dikunci"),
    "assign:FINAL_FIXPOINT": ("data", BALANCE_GD, "const FINAL_FIXPOINT := true",
                              "koreksi akhir rumus audit"),
    "assign:W_DPS,W_EHP,EHP_PER_HP": ("data", BALANCE_GD, "const W_DPS := 0.72",
                                      "bobot skor power 0.72 / 0.28"),
    "assign:TARGET_RATIO": ("data", BALANCE_GD, "const TARGET_RATIO: Dictionary = {",
                            "rasio EHP/DPS per gaya main"),
    "assign:SCHOOL_RATIO_BONUS": ("data", BALANCE_GD,
                                  "const SCHOOL_RATIO_BONUS: Dictionary = {",
                                  "geseran rasio per sekolah"),
    "assign:RATIO_BLEND": ("data", BALANCE_GD, "const RATIO_BLEND := 0.55",
                           "campuran data lama vs target"),
    "assign:BUDGET_COMPRESS": ("data", BALANCE_GD, "const BUDGET_COMPRESS := 0.45",
                              "kompresi budget ke median pool"),
    "assign:STYLE_POWER": ("data", BALANCE_GD, "const STYLE_POWER: Dictionary = {",
                           "bobot power per gaya main"),
    "assign:HP_MULT_RANGE": ("data", BALANCE_GD, "const HP_MULT_RANGE := [0.66, 1.50]",
                             "batas multiplier HP"),
    "assign:DMG_MULT_RANGE": ("data", BALANCE_GD,
                              "const DMG_MULT_RANGE := [0.68, 1.45]",
                              "batas multiplier damage/skill"),
    "assign:SCHOOL_PARITY_CAP": ("data", BALANCE_GD,
                                 "const SCHOOL_PARITY_CAP := 1.45",
                                 "pengapung paritas sekolah"),
    "assign:CELL_PARITY_CAP": ("data", BALANCE_GD, "const CELL_PARITY_CAP := 1.30",
                               "pengapung paritas sel"),
    "assign:POOL_MEAN_TOL_MAX": ("data", BALANCE_GD,
                                 "const POOL_MEAN_TOL_MAX := 0.18",
                                 "batas jangkar pool"),
    "assign:FINAL_CORR_CAP": ("data", BALANCE_GD, "const FINAL_CORR_CAP := 1.35",
                              "batas koreksi akhir"),
    "assign:COST_BUCKET": ("data", BALANCE_GD, "const COST_BUCKET := 1000",
                           "lebar band harga"),
    "assign:COST_EFF_BAND": ("data", BALANCE_GD,
                             "const COST_EFF_BAND := [0.78, 1.28]",
                             "band efisiensi harga"),
    "assign:COST_EFF_DAMP": ("data", BALANCE_GD, "const COST_EFF_DAMP := 0.60",
                             "redaman koreksi harga"),
    "assign:COST_EFF_MIN_GROUP": ("data", BALANCE_GD,
                                  "const COST_EFF_MIN_GROUP := 8",
                                  "ukuran grup minimum"),
    "assign:META_EFF_BAND": ("data", BALANCE_GD,
                             "const META_EFF_BAND := [0.80, 1.25]",
                             "band efisiensi toko meta"),
    "assign:META_EFF_DAMP": ("data", BALANCE_GD, "const META_EFF_DAMP := 0.75",
                             "redaman toko meta"),
    "assign:TOWER_ARMOR_AT_L3": ("data", BALANCE_GD,
                                 "const TOWER_ARMOR_AT_L3 := 5.0",
                                 "armor menara level 3"),
    "assign:ARMOR_FACTOR": ("data", BALANCE_GD, "const ARMOR_FACTOR := 0.06",
                            "kurva armor (sama dengan hero_archetypes)"),
    "assign:TOWER_PHYS_FACTOR": ("data", BALANCE_GD,
                                 "const TOWER_PHYS_FACTOR := 1.0 / (1.0 + TOWER_ARMOR_AT_L3 * ARMOR_FACTOR)",
                                 "mitigasi fisik menara"),
    "assign:SCHOOL_MOD_CAP": ("data", BALANCE_GD, "const SCHOOL_MOD_CAP := 1.06",
                              "pengapung modifier sekolah"),
    "assign:STARTER_CATCHUP_MAX": ("data", BALANCE_GD,
                                   "const STARTER_CATCHUP_MAX := 1.32",
                                   "bonus catch-up maksimum"),
    "assign:STARTER_CATCHUP_REF": ("data", BALANCE_GD,
                                   "const STARTER_CATCHUP_REF := 12",
                                   "roster penuh = 12 unlock"),
    "assign:STARTER_CATCHUP_LV0": ("data", BALANCE_GD,
                                   "const STARTER_CATCHUP_LV0 := 1",
                                   "level bonus penuh"),
    "assign:STARTER_CATCHUP_LV1": ("data", BALANCE_GD,
                                   "const STARTER_CATCHUP_LV1 := 8",
                                   "level bonus habis"),
    "assign:STARTER_CATCHUP_DECAY": ("data", BALANCE_GD,
                                     "const STARTER_CATCHUP_DECAY := 0.20",
                                     "sisa bonus di level tinggi"),
    "assign:STARTER_HEROES": ("data", BALANCE_GD, "const STARTER_HEROES: Array[String] = [",
                              "enam starter"),
    "assign:_DBG": ("deviation", "", "",
                    "D5: log MYSTIC_DEBUG_BALANCE ke stderr tidak diport"),
    "assign:LAST": ("deviation", BALANCE_GD, "static var last_result: Dictionary = {",
                    "D4: global LAST -> last_result, direset tiap apply"),
    "func:metrics": ("ported", BALANCE_GD, "static func metrics(", ""),
    "func:_clamp": ("ported", BALANCE_GD, "static func _clamp(", ""),
    "func:_median": ("ported", BALANCE_GD, "static func _median(", ""),
    "func:_mean": ("ported", BALANCE_GD, "static func _mean(", ""),
    "func:hero_target": ("ported", BALANCE_GD, "static func hero_target(", ""),
    "func:stat_multipliers": ("ported", BALANCE_GD, "static func stat_multipliers(", ""),
    "func:school_mod": ("ported", BALANCE_GD, "static func school_mod(", ""),
    "func:starter_level_factor": ("ported", BALANCE_GD,
                                  "static func starter_level_factor(", ""),
    "func:starter_catchup": ("ported", BALANCE_GD, "static func starter_catchup(", ""),
    "func:starter_catchup_stats": ("ported", BALANCE_GD,
                                   "static func starter_catchup_stats(", ""),
    "func:boss_unlocks_for_purchases": ("ported", BALANCE_GD,
                                        "static func boss_unlocks_for_purchases(", ""),
    "func:_eff_dps": ("ported", BALANCE_GD, "static func eff_dps(", ""),
    "func:_final_power": ("ported", BALANCE_GD, "static func final_power(", ""),
    "func:cell_parity_factors": ("ported", BALANCE_GD,
                                 "static func cell_parity_factors(", ""),
    "func:pristine_boss_stats": ("deviation", BALANCE_GD,
                                 "static func pristine_boss_stats(",
                                 "D1: impor bosses.boss_data -> parameter pristine"),
    "func:resolve_catalog": ("ported", BALANCE_GD,
                             "static func resolve_catalog(catalog: Dictionary, unlocks: int = 0)",
                             "D2: unlock starter jadi argumen"),
    "func:calibrate_boss_resistances": ("ported", BALANCE_GD,
                                        "static func calibrate_boss_resistances(", ""),
    "func:_pool_mean_rescale": ("ported", BALANCE_GD, "static func pool_mean_rescale(", ""),
    "func:_final_fixpoint": ("ported", BALANCE_GD, "static func final_fixpoint(", ""),
    "func:apply_to_catalog": ("ported", BALANCE_GD,
                              "static func apply_to_catalog(catalog: Dictionary, pristine: Dictionary = {})",
                              "D3: tanpa try/except, gagal keras"),
}

CATALOG_KEYS = ("hp", "damage", "skill_damage", "attack_cooldown", "skill_cooldown",
                "armor", "magic_resist", "cost", "unlock_cost", "is_boss_hero",
                "boss_class", "unlock_require_boss", "dmg_type", "skill_q_damage",
                "skill_w_damage", "skill_e_damage", "skill_r_damage")


def _round(value, digits=6):
    return round(float(value), digits)


def _inventory():
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    assigns = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = []
            for target in targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
                elif isinstance(target, ast.Tuple):
                    names.extend(element.id for element in target.elts
                                 if isinstance(element, ast.Name))
            if names:
                assigns.append((",".join(names), node.lineno))
    return {
        "file": "_system.py" if False else "hero_balance.py",
        "lines": len(source.splitlines()),
        "sections": len(SECTIONS),
        "classes": len(classes),
        "functions": len(functions),
        "assigns": len(assigns),
        "imports": 2,
    }, functions, assigns


def _section_of(line):
    for name, start, end in SECTIONS:
        if start <= line <= end:
            return name
    raise AssertionError("symbol di luar seksi: %d" % line)


def _symbols(functions, assigns):
    rows = []
    for name, line in assigns:
        rows.append(("assign:" + name, line))
    for node in functions:
        rows.append(("func:" + node.name, node.lineno))
    rows.append(("import:statistics", _import_line("statistics")))
    rows.append(("import:hero_archetypes", _import_line("hero_archetypes")))
    rows.sort(key=lambda row: row[1])
    return rows


def _import_line(module):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == module:
                    return node.lineno
        if isinstance(node, ast.ImportFrom) and node.module == module:
            return node.lineno
    raise AssertionError("impor %s tidak ketemu" % module)


def _catalog_snapshot():
    stubbed = ("settings", "sound_manager", "hero_items")
    saved = {name: sys.modules.get(name) for name in stubbed}
    literals = _install_stubs()
    try:
        catalog = _exec_catalog(literals)()
    finally:
        # `_install_stubs` injects fake modules; do not leak them into the
        # validator (it imports other source oracles in the same process).
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    pristine = hb.pristine_boss_stats()
    src = copy.deepcopy(catalog)
    for hero_type, stats in pristine.items():
        if hero_type in src:
            src[hero_type] = copy.deepcopy(stats)
    src_rows = {}
    for hero_type, stats in src.items():
        row = {}
        for key in CATALOG_KEYS:
            if key in stats:
                value = stats[key]
                if isinstance(value, float):
                    value = _round(value)
                row[key] = value
        src_rows[hero_type] = row
    pristine_rows = {}
    for hero_type, stats in pristine.items():
        row = {}
        for key in CATALOG_KEYS:
            if key in stats:
                value = stats[key]
                if isinstance(value, float):
                    value = _round(value)
                row[key] = value
        pristine_rows[hero_type] = row
    return catalog, src, src_rows, pristine, pristine_rows


def _sample_heroes():
    """One hero per archetype cell plus the two starter extremes."""
    cells = {}
    for hero_type in sorted(ha.ARCHETYPES):
        row = ha.ARCHETYPES[hero_type]
        key = (row["dmg_type"], row["playstyle"])
        cells.setdefault(key, hero_type)
    return cells, ["kaizen", "thorne"]


def _helpers(src_rows, pool):
    cells, starters = _sample_heroes()
    sample = {}
    for key in sorted(cells):
        hero_type = cells[key]
        stats = dict(src_rows[hero_type])
        stats["__hero_type__"] = hero_type
        metrics = hb.metrics(stats)
        target = hb.hero_target(stats, pool)
        multipliers = hb.stat_multipliers(stats, pool)
        sample[hero_type] = {
            "cell": "%s|%s" % key,
            "metrics": {key2: _round(value) for key2, value in metrics.items()},
            "target": None if target is None else {
                "ratio": _round(target[1]),
                "budget": _round(target[2]),
                "price_corr": _round(target[3], 8),
                "school": target[4],
                "style": target[5],
            },
            "multipliers": [_round(value) for value in multipliers[:3]],
        }
    for hero_type in starters:
        stats = dict(src_rows[hero_type])
        stats["__hero_type__"] = hero_type
        sample[hero_type] = {
            "cell": "starter",
            "metrics": {key: _round(value) for key, value in hb.metrics(stats).items()},
            "target": None,
            "multipliers": [_round(value) for value in
                            hb.stat_multipliers(stats, pool)[:3]],
        }
    return sample


def _starter_grid():
    grid = {}
    for hero_type in list(hb.STARTER_HEROES) + ["gornak"]:
        rows = {}
        for unlocks in (0, 3, 6, 12, 99):
            for level in (1, 4, 8, 12, 15):
                rows["%d|%d" % (unlocks, level)] = [
                    _round(value) for value in
                    hb.starter_catchup(hero_type, unlocks, level)
                ]
        grid[hero_type] = rows
    stats = {}
    base = {"hp": 520, "damage": 27}
    for unlocks in (0, 6, 12):
        stats["kaizen|%d|1" % unlocks] = list(
            hb.starter_catchup_stats("kaizen", base, unlocks, 1)
        )
    stats["kaizen|0|8"] = list(hb.starter_catchup_stats("kaizen", base, 0, 8))
    stats["sylara|0|1"] = list(hb.starter_catchup_stats("sylara", base, 0, 1))
    unlocked = {
        "[]": hb.boss_unlocks_for_purchases([]),
        "starters_only": hb.boss_unlocks_for_purchases(list(hb.STARTER_HEROES)),
        "mixed": hb.boss_unlocks_for_purchases(
            ["kaizen", "gornak", "abaddon", "vex"]
        ),
    }
    return {"catchup": grid, "stats": stats, "unlock_counts": unlocked,
            "level_factor": {str(level): _round(hb.starter_level_factor(level))
                             for level in (1, 2, 4, 6, 8, 12, 15)}}


def _calibrate_rows(src_rows, resolved):
    rows = []
    for hero_type in sorted(src_rows):
        stats = src_rows[hero_type]
        if not stats.get("is_boss_hero"):
            continue
        boss_type = stats.get("unlock_require_boss") or hero_type
        row = ha.BOSS_RESISTANCES.get(boss_type, {})
        rows.append({
            "boss_type": hero_type,
            "boss_class": stats.get("boss_class", "mini"),
            "profile": row.get("profile", "balanced"),
            "dmg_type": ha.get_archetype(hero_type, stats)["dmg_type"],
            "dps": _round(resolved[hero_type]["__dps"], 3),
        })
    return rows


def _apply_pipeline(catalog, pristine):
    """Run the whole pass on a pristine copy, then read `hero_balance.LAST`."""
    src = copy.deepcopy(catalog)
    for hero_type, stats in pristine.items():
        if hero_type in src:
            src[hero_type] = copy.deepcopy(stats)
    balanced = copy.deepcopy(src)
    hb.apply_to_catalog(balanced)
    table = hb.resolve_catalog(src)
    return src, balanced, table


def _tres_values(hero_type):
    path = GODOT / "data" / "heroes" / ("%s.tres" % hero_type)
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    out = {}
    for field in ("max_hp", "damage", "base_skill"):
        match = re.search(r"^%s = (-?\d+)$" % field, text, re.M)
        out[field] = int(match.group(1)) if match else None
    return out


def _boss_stats_rows():
    raw = json.loads((GODOT / "data/bosses/boss_stats.json").read_text(encoding="utf-8"))
    return raw["bosses"]


def build_fixture():
    inventory, functions, assigns = _inventory()
    symbols = _symbols(functions, assigns)
    for symbol, _line in symbols:
        assert symbol in CLASSIFICATION, "simbol belum terklasifikasi: %s" % symbol

    catalog, src, src_rows, pristine, pristine_rows = _catalog_snapshot()
    src_run, balanced, table = _apply_pipeline(catalog, pristine)

    pool = hb.pool_for(src_run) if hasattr(hb, "pool_for") else None
    if pool is None:
        # the source builds the pool inline inside resolve_catalog
        met = {ht: hb.metrics(stats) for ht, stats in
               [(k, v) for k, v in src_run.items() if v.get("is_boss_hero")]}
        ratios = sorted(m["ehp"] / m["dps"] for m in met.values()
                        if m["dps"] > 0 and m["ehp"] > 0)
        budgets = sorted(m["budget"] for m in met.values())
        pool = {
            "med_ratio": hb._median(ratios),
            "med_budget": hb._median(budgets),
            "p50_budget": budgets[len(budgets) // 2],
            "meta_med": 0.0,
            "eff_by_bucket": {},
            "med_dps": hb._median([m["dps"] for m in met.values()]) or 1.0,
            "med_ehp": hb._median([m["ehp"] for m in met.values()]) or 1.0,
        }
        buckets = {}
        for hero_type, m in met.items():
            if m["cost"] <= 0 or m["budget"] <= 0:
                continue
            bucket = int(round(m["cost"] / hb.COST_BUCKET)) * hb.COST_BUCKET
            buckets.setdefault(bucket, []).append(m["budget"] / m["cost"])
        pool["eff_by_bucket"] = {b: hb._median(v) for b, v in buckets.items()
                                 if len(v) >= hb.COST_EFF_MIN_GROUP}
        meta_costs = {}
        for stats in src_run.values():
            if stats.get("is_boss_hero"):
                meta_costs.setdefault(float(stats.get("unlock_cost", 0) or 0),
                                      []).append(hb.metrics(stats)["budget"])
        for cost, values in meta_costs.items():
            if cost > 0 and len(values) >= 20:
                pool["meta_med"] = hb._median(values)
                break

    resolved = {}
    for hero_type, mult in table.items():
        if mult is None:
            resolved[hero_type] = None
            continue
        dbg = dict(mult["dbg"])
        dbg.pop("raw", None)
        keep = ("ratio_from", "ratio_to", "price_corr", "playstyle", "dmg_type",
                "boss_class") if "ratio_from" in dbg else (
            "starter_unlocks", "playstyle", "dmg_type", "boss_class")
        resolved[hero_type] = {
            "hp": mult["hp"], "dmg": mult["dmg"], "skill": mult["skill"],
            "dbg": {key: dbg[key] for key in keep},
        }

    final_stats = {}
    tres_mismatch = []
    for hero_type, stats in balanced.items():
        if not stats.get("is_boss_hero"):
            continue
        values = {
            "hp": int(stats["hp"]),
            "damage": int(stats["damage"]),
            "skill_damage": int(stats["skill_damage"]),
        }
        for key in ("skill_q_damage", "skill_w_damage", "skill_e_damage",
                    "skill_r_damage"):
            if stats.get(key):
                values[key] = int(stats[key])
        final_stats[hero_type] = values
        tres = _tres_values(hero_type)
        if tres is None:
            tres_mismatch.append([hero_type, "no tres"])
            continue
        if (tres["max_hp"], tres["damage"], tres["base_skill"]) != (
                values["hp"], values["damage"], values["skill_damage"]):
            tres_mismatch.append([hero_type, tres, values])

    starter_tres = {}
    for hero_type in hb.STARTER_HEROES:
        tres = _tres_values(hero_type)
        stats = src_run[hero_type]
        expected = hb.starter_catchup_stats(hero_type, stats, 0, 1)
        starter_tres[hero_type] = {
            "tres": [tres["max_hp"], tres["damage"]],
            "catchup": [int(expected[0]), int(expected[1])],
        }
    starter_gap = [hero_type for hero_type, row in starter_tres.items()
                   if row["tres"] != row["catchup"]]

    bosses = _boss_stats_rows()
    resist_mismatch = []
    for boss_type, row in ha.BOSS_RESISTANCES.items():
        data = bosses.get(boss_type)
        if data is None:
            resist_mismatch.append([boss_type, "missing"])
            continue
        if (int(data.get("armor", -1)) != int(row["armor"])
                or abs(float(data.get("magic_resist", -1)) - float(row["magic_resist"]))
                > 1e-9):
            resist_mismatch.append([boss_type, data.get("armor"),
                                    data.get("magic_resist"), row["armor"],
                                    row["magic_resist"]])

    # The published rows are produced per class from the ZERO-MEANED profile
    # modifiers and the published scale; re-running that write step must land on
    # every row (magic_resist is published rounded to three decimals).
    per_class = {}
    for row in ha.BOSS_RESISTANCES.values():
        per_class.setdefault(row["boss_class"], []).append(row)
    zero_mean_mods = {}
    for boss_class, class_rows in per_class.items():
        count = len(class_rows) or 1
        mean_armor = sum(ha.BOSS_RESIST_PROFILE_MODS.get(
            row.get("profile", "balanced"), (0.0, 0.0))[0] for row in class_rows) / count
        mean_mr = sum(ha.BOSS_RESIST_PROFILE_MODS.get(
            row.get("profile", "balanced"), (0.0, 0.0))[1] for row in class_rows) / count
        zero_mean_mods[boss_class] = {
            profile: (value[0] - mean_armor, value[1] - mean_mr)
            for profile, value in ha.BOSS_RESIST_PROFILE_MODS.items()
        }
    scale_mismatch = []
    for boss_type, row in ha.BOSS_RESISTANCES.items():
        scales = ha.BOSS_RESIST_SCALE[row["boss_class"]]
        armor, mr = ha._resist_from_profile(
            row["profile"], row["boss_class"], ha.BOSS_RESIST_BASE,
            zero_mean_mods[row["boss_class"]],
            armor_scale=scales["armor"], mr_scale=scales["mr"])
        if int(armor) != int(row["armor"]) or round(float(mr), 3) != round(
                float(row["magic_resist"]), 3):
            scale_mismatch.append([boss_type, armor, mr, row["armor"],
                                   row["magic_resist"]])
    scale_mods = {key: {profile: list(value) for profile, value in mods.items()}
                  for key, mods in zero_mean_mods.items()}

    resolved_dps = {hero_type: {"__dps": hb.metrics(stats)["dps"]}
                    for hero_type, stats in balanced.items()
                    if stats.get("is_boss_hero")}
    rows = _calibrate_rows(pristine_rows, resolved_dps)
    resist_table, resist_report = hb.calibrate_boss_resistances(rows, n_step=8)

    cells, _starters = _sample_heroes()
    kinds = {}
    for kind, _target, _token, _note in CLASSIFICATION.values():
        kinds[kind] = kinds.get(kind, 0) + 1

    sections = []
    for name, start, end in SECTIONS:
        sections.append({"name": name, "start": start, "end": end,
                         "lines": end - start + 1})

    fixture = {
        "file": inventory,
        "sections": sections,
        "symbols": {"count": len(symbols), "kinds": dict(sorted(kinds.items()))},
        "classification": {
            symbol: {"kind": kind, "target": target, "token": token, "note": note}
            for symbol, (kind, target, token, note) in sorted(
                CLASSIFICATION.items(), key=lambda item: dict(symbols)[item[0]])
        },
        "duplicates": {},
        "switches": {name: bool(getattr(hb, name)) for name in SWITCHES},
        "archetypes": {
            "count": len(ha.ARCHETYPES),
            "kinds": {
                "dmg_type": {key: sum(1 for row in ha.ARCHETYPES.values()
                                      if row["dmg_type"] == key)
                             for key in ("MAGIC", "PHYSICAL")},
                "playstyle": {key: sum(1 for row in ha.ARCHETYPES.values()
                                       if row["playstyle"] == key)
                              for key in ("CARRY", "FIGHTER", "TANK")},
                "tier": {key: sum(1 for row in ha.ARCHETYPES.values()
                                  if row["tier"] == key)
                         for key in ("S", "A", "B", "C", "D")},
            },
            "rows": {hero_type: ha.ARCHETYPES[hero_type]
                     for hero_type in sorted(ha.ARCHETYPES)},
        },
        "boss_resist": {
            "count": len(ha.BOSS_RESISTANCES),
            "rows": {boss_type: ha.BOSS_RESISTANCES[boss_type]
                     for boss_type in sorted(ha.BOSS_RESISTANCES)},
            "base": {key: list(value) for key, value in ha.BOSS_RESIST_BASE.items()},
            "profile_mods": {key: list(value) for key, value in
                             ha.BOSS_RESIST_PROFILE_MODS.items()},
            "zero_mean_mods": scale_mods,
            "scale": ha.BOSS_RESIST_SCALE,
            "target_ratio": ha.BOSS_RESIST_TARGET_RATIO,
            "armor_factor": ha.ARMOR_FACTOR,
            "armor_max": ha.ARMOR_MAX,
            "mr_max": ha.MR_MAX,
            "mitigation": {str(armor): _round(ha.physical_mitigation(armor))
                           for armor in (0, 1, 5, 12, 18, 26, 32, 40)},
            "profile_pairs": {
                "mini|armored": list(ha._resist_from_profile("armored", "mini")),
                "mini|soft": list(ha._resist_from_profile("soft", "mini")),
                "true|magic": list(ha._resist_from_profile("magic", "true")),
                "unknown_profile": list(ha._resist_from_profile("nope", "mini")),
                "unknown_class": list(ha._resist_from_profile("balanced", "nope")),
            },
            "fallback": {
                "gornak": list(ha.get_boss_resistances("gornak")),
                "unknown|mini": list(ha.get_boss_resistances("not_a_boss", "mini")),
                "unknown|true": list(ha.get_boss_resistances("not_a_boss", "true")),
            },
            "data_mismatch": resist_mismatch,
            "scale_mismatch": scale_mismatch,
            "archetype_cells": ["%s|%s" % key for key in sorted(cells)],
            "overrides": {
                "forced_magic": ha.get_archetype("gornak", {"dmg_type": "magic"}),
                "forced_bogus": ha.get_archetype("gornak", {"dmg_type": "fire"}),
                "forced_unknown_hero": ha.get_archetype("nobody", {"dmg_type": "MAGIC"}),
                "plain": ha.get_archetype("gornak"),
                "derived": ha.get_archetype("nobody"),
                "school_of": ha.school_of("gornak"),
                "school_of_override": ha.school_of("gornak", {"dmg_type": "PHYSICAL"}),
            },
        },
        "pool": {
            "med_ratio": _round(pool["med_ratio"]),
            "med_budget": _round(pool["med_budget"]),
            "p50_budget": _round(pool["p50_budget"]),
            "meta_med": _round(pool["meta_med"]),
            "med_dps": _round(pool["med_dps"]),
            "med_ehp": _round(pool["med_ehp"]),
            "eff_by_bucket": {str(key): _round(value) for key, value in
                              sorted(pool["eff_by_bucket"].items())},
        },
        "helpers": _helpers(src_rows, pool),
        "starter": _starter_grid(),
        "calibrate": {
            "n_step": 8,
            "rows": rows,
            "table": {key: value for key, value in sorted(resist_table.items())},
            "scales": resist_report["_scales"],
        },
        "pristine": pristine_rows,
        "catalog_src": src_rows,
        "resolve": resolved,
        "apply": {
            "pool_means": hb.LAST["pool_means"],
            "pool_anchor": {key: _round(value, 9) for key, value in
                            hb.LAST["pool_anchor"].items()},
            "parity": hb.LAST["parity"],
            "fix": hb.LAST["fix"],
            "stats": final_stats,
            "tres_mismatch": tres_mismatch,
            "starter_tres": starter_tres,
            "starter_gap": starter_gap,
        },
        "checks": {
            "balance_gd": BALANCE_GD,
            "archetypes_gd": ARCH_GD,
            "heroes_gd": HEROES_GD,
            "tres_dir": "godot_rebuild/data/heroes",
            "boss_stats": "godot_rebuild/data/bosses/boss_stats.json",
        },
    }
    fixture["symbols"]["count"] = len(CLASSIFICATION)
    return fixture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    fixture = build_fixture()
    payload = json.dumps(fixture, indent=1, sort_keys=False) + "\n"
    if args.write:
        FIXTURE.write_text(payload, encoding="utf-8")
        print("wrote %s (%d bytes)" % (FIXTURE.name, len(payload)))
        return
    if args.check:
        current = FIXTURE.read_text(encoding="utf-8")
        if json.loads(current) != fixture:
            print("STALE: %s does not match live Python execution" % FIXTURE.name)
            raise SystemExit(1)
        print("OK: %s matches live Python execution" % FIXTURE.name)
        return
    print(json.dumps(fixture["symbols"], indent=1))
    print(json.dumps(fixture["apply"]["tres_mismatch"]))
    print(json.dumps(fixture["apply"]["starter_gap"]))


if __name__ == "__main__":
    main()
