# gdlint:disable=max-file-lines
extends RefCounted
## Layer 9cj: port of `hero_balance.py` — the single place hero balance is
## calibrated. The module reads a hero catalog, computes one multiplier triple per
## hero (hp / damage / skill) and, in `apply_to_catalog`, writes the rounded stats
## back so the shop, the skill preview and the battle read the SAME numbers.
##
## Everything here is pool-relative and deterministic: median DPS/EHP for the power
## score, the mean multiplier anchor (`POOL_MEAN_ANCHOR`), the archetype-cell parity
## (`CELL_PARITY`), the per-boss-class school parity (`SCHOOL_PARITY`) and the final
## audit-formula fixpoint (`FINAL_FIXPOINT`). The order of those steps is load-bearing
## (see the source header's "PERINGATAN YANG DIBUANG" list), so the port keeps the
## same sequence and the same clamps.
##
## Deviations (documented in `docs/HERO_BALANCE_FOLDER_MIGRATION.md`):
##   D1 `pristine_boss_stats()` imports `bosses.boss_data` in Python; the port takes
##      the pristine catalog as a parameter (the runtime catalog is baked `.tres`
##      data, so there is no Python module to import at runtime).
##   D2 the starter branch reads `__main__.game_instance.purchased_heroes`; the port
##      takes `unlocks` explicitly, so no global game object is needed.
##   D3 `apply_to_catalog` wraps `resolve_catalog` in `try/except` and returns the
##      untouched catalog on error; GDScript has no equivalent, so a broken catalog
##      is a hard failure instead of a silent no-op.
##   D4 `LAST` is a module global in Python; the port exposes `last_result`, reset on
##      every `apply_to_catalog`/`resolve_catalog` call.
##   D5 the `MYSTIC_DEBUG_BALANCE` stderr logging is not ported (debug only).

const Archetypes = preload("res://scripts/data/hero_archetypes.gd")

# ─── SWITCHES ────────────────────────────────────────────────────────────
const ENABLE_REBUDGET := true          # A: tank/carry/fighter trade-off
const ENABLE_SCHOOL_MOD := false       # B: only used when parity is off
const ENABLE_STARTER_CATCHUP := true   # C: starters do not sink
const SCHOOL_PARITY := true            # school parity per boss class
const CELL_PARITY := true              # archetype-cell parity
const POOL_MEAN_ANCHOR := true         # pin the pool DPS/EHP mean to the old number
const FINAL_FIXPOINT := true           # final correction with the audit formula

# ─── A. RE-BUDGET: move power, never add power ───────────────────────────
const W_DPS := 0.72
const W_EHP := 0.28
const EHP_PER_HP := 1.0 / 6.0
const TARGET_RATIO: Dictionary = {
	"TANK": [9.5, 13.0],
	"FIGHTER": [6.0, 7.5],
	"CARRY": [3.4, 4.6],
}
const SCHOOL_RATIO_BONUS: Dictionary = {"PHYSICAL": -0.04, "MAGIC": 0.04}
const RATIO_BLEND := 0.55
const BUDGET_COMPRESS := 0.45
const STYLE_POWER: Dictionary = {"TANK": 0.74, "FIGHTER": 1.06, "CARRY": 1.08}

const HP_MULT_RANGE := [0.66, 1.50]
const DMG_MULT_RANGE := [0.68, 1.45]

const SCHOOL_PARITY_CAP := 1.45
const CELL_PARITY_CAP := 1.30
const POOL_MEAN_TOL_MAX := 0.18
const FINAL_CORR_CAP := 1.35

# ─── "worth it" guard: a cheap hero must not be the optimal pick ─────────
const COST_BUCKET := 1000
const COST_EFF_BAND := [0.78, 1.28]
const COST_EFF_DAMP := 0.60
const COST_EFF_MIN_GROUP := 8
const META_EFF_BAND := [0.80, 1.25]
const META_EFF_DAMP := 0.75

# ─── B. school modifier vs towers (only when parity is OFF) ──────────────
const TOWER_ARMOR_AT_L3 := 5.0
const ARMOR_FACTOR := 0.06
const TOWER_PHYS_FACTOR := 1.0 / (1.0 + TOWER_ARMOR_AT_L3 * ARMOR_FACTOR)
const SCHOOL_MOD_CAP := 1.06

# ─── C. STARTER CATCH-UP ─────────────────────────────────────────────────
const STARTER_CATCHUP_MAX := 1.32
const STARTER_CATCHUP_REF := 12
const STARTER_CATCHUP_LV0 := 1
const STARTER_CATCHUP_LV1 := 8
const STARTER_CATCHUP_DECAY := 0.20
const STARTER_HEROES: Array[String] = [
	"kaizen", "grimjaw", "sylara", "thorne", "vex", "zephyr"
]

## Audit/tools read the intermediate results from here (`hero_balance.LAST`).
static var last_result: Dictionary = {"table": {}, "pool": {}, "parity": {}}


# ─── small numeric helpers (Python semantics) ────────────────────────────
static func _num_zero(value: Variant) -> float:
	return 0.0 if value == null else float(value)


## `stats.get(key, default) or default`: 0 and None both fall back.
static func _num_or(value: Variant, fallback: float) -> float:
	if value == null:
		return fallback
	var number := float(value)
	return fallback if number == 0.0 else number


static func _clamp(value: float, band: Array) -> float:
	return maxf(float(band[0]), minf(float(band[1]), value))


static func _mean(values: Array) -> float:
	if values.is_empty():
		return 0.0
	var total := 0.0
	for value in values:
		total += float(value)
	return total / float(values.size())


static func _median(values: Array) -> float:
	if values.is_empty():
		return 0.0
	var sorted: Array = values.duplicate()
	sorted.sort()
	var index := sorted.size() / 2
	if sorted.size() % 2 == 1:
		return float(sorted[index])
	return 0.5 * (float(sorted[index - 1]) + float(sorted[index]))


## Python's `round(value, digits)`.
static func round_py(value: float, digits: int) -> float:
	var scale := pow(10.0, float(digits))
	return Archetypes.round_half_even(value * scale) / scale


# ─── METRICS (must equal what the audit reads) ───────────────────────────
## DPS/HP/EHP/budget from the RAW hero stats (before the melee buff).
static func metrics(stats: Dictionary) -> Dictionary:
	var hp := _num_zero(stats.get("hp"))
	var dmg := _num_zero(stats.get("damage"))
	var cd := maxf(1.0, _num_or(stats.get("attack_cooldown", 30), 30.0))
	var sk := _num_zero(stats.get("skill_damage"))
	var skcd := maxf(1.0, _num_or(stats.get("skill_cooldown", 240), 240.0))
	var basic_dps := dmg * 60.0 / cd
	var skill_dps := sk * 60.0 / skcd
	var dps := basic_dps + skill_dps
	var armor := _num_zero(stats.get("armor"))
	var mr := minf(0.75, maxf(0.0, _num_zero(stats.get("magic_resist"))))
	var ehp := hp * (1.0 + armor * 0.06) / maxf(0.25, 1.0 - mr)
	return {
		"hp": hp,
		"dmg": dmg,
		"skill": sk,
		"cd": cd,
		"skcd": skcd,
		"basic_dps": basic_dps,
		"skill_dps": skill_dps,
		"dps": dps,
		"ehp": ehp,
		"cost": _num_zero(stats.get("cost")),
		"burst": skill_dps / dps if dps > 0.0 else 0.0,
		"budget": W_DPS * dps + W_EHP * ehp * EHP_PER_HP,
	}


## `(m, ratio, budget, price_corr, school, style)` for one hero, or `null` when
## the hero has no damage or no EHP (the source skips those).
static func hero_target(stats: Dictionary, pool: Dictionary) -> Variant:
	var m := metrics(stats)
	var arch := Archetypes.get_archetype(String(stats.get("__hero_type__", "")), stats)
	if float(m["dps"]) <= 0.0 or float(m["ehp"]) <= 0.0:
		return null
	var style := String(arch.get("playstyle", ""))
	if style.is_empty():
		style = "FIGHTER"
	var school := String(arch.get("dmg_type", ""))
	if school.is_empty():
		school = "PHYSICAL"
	var band: Array = TARGET_RATIO.get(style, TARGET_RATIO["FIGHTER"])
	var tgt_ratio := 0.5 * (float(band[0]) + float(band[1])) \
		* (1.0 + float(SCHOOL_RATIO_BONUS.get(school, 0.0)))
	var cur_ratio := float(m["ehp"]) / float(m["dps"])
	var ratio := cur_ratio * (1.0 - RATIO_BLEND) + tgt_ratio * RATIO_BLEND
	var budget := float(m["budget"]) * float(STYLE_POWER.get(style, 1.0))
	var p50 := float(pool.get("p50_budget", 0.0))
	if BUDGET_COMPRESS > 0.0 and p50 > 0.0:
		budget = budget * pow(p50 / maxf(budget, 1e-9), BUDGET_COMPRESS)
	var price_corr := 1.0
	var meta_med := float(pool.get("meta_med", 0.0))
	if meta_med > 0.0:
		var rel := float(m["budget"]) / meta_med
		if rel > float(META_EFF_BAND[1]):
			budget *= pow(float(META_EFF_BAND[1]) / rel, META_EFF_DAMP)
		elif rel < float(META_EFF_BAND[0]):
			budget *= pow(float(META_EFF_BAND[0]) / rel, META_EFF_DAMP)
	var eff_by_bucket: Dictionary = pool.get("eff_by_bucket", {})
	var bucket := int(Archetypes.round_half_even(float(m["cost"]) / COST_BUCKET)) * COST_BUCKET
	if eff_by_bucket.has(bucket):
		var med_eff := float(eff_by_bucket[bucket])
		if med_eff != 0.0 and float(m["cost"]) > 0.0:
			var rel_eff := (float(m["budget"]) / float(m["cost"])) / med_eff
			if rel_eff > float(COST_EFF_BAND[1]):
				price_corr = pow(float(COST_EFF_BAND[1]) / rel_eff, COST_EFF_DAMP)
			elif rel_eff < float(COST_EFF_BAND[0]):
				price_corr = pow(float(COST_EFF_BAND[0]) / rel_eff, COST_EFF_DAMP)
			budget *= price_corr
	return [m, ratio, budget, price_corr, school, style]


## `(mult_hp, mult_damage, mult_skill, target)` for one hero.
static func stat_multipliers(stats: Dictionary, pool: Dictionary) -> Array:
	var target: Variant = hero_target(stats, pool)
	if target == null:
		return [1.0, 1.0, 1.0, null]
	var entry: Array = target
	var m: Dictionary = entry[0]
	var ratio := float(entry[1])
	var budget := float(entry[2])
	# Split the target budget along the TARGET ratio, not the old one — that is
	# where a tank is forced to buy its power with HP.
	var share := 1.0 / (1.0 + (W_EHP * EHP_PER_HP * ratio) / W_DPS)
	var new_dps := budget * share / W_DPS
	var new_ehp := budget * (1.0 - share) / (W_EHP * EHP_PER_HP)
	var x := new_dps / float(m["dps"]) if float(m["dps"]) > 0.0 else 1.0
	var y := new_ehp / float(m["ehp"]) if float(m["ehp"]) > 0.0 else 1.0
	# Burst-heavy heroes keep part of their damage in the skill, so it is not
	# cut twice (base + skill): move the weight to the dominant side.
	var burst := float(m["burst"])
	var x_dmg := 1.0 + (x - 1.0) * (1.0 - burst * 1.15)
	var x_sk := 1.0 + (x - 1.0) * (burst * 1.15)
	return [
		_clamp(y, HP_MULT_RANGE),
		_clamp(x_dmg, DMG_MULT_RANGE),
		_clamp(x_sk, DMG_MULT_RANGE),
		entry,
	]


## `hedge` for the physical damage of a hero when parity is off (towers have no
## magic resistance).
static func school_mod(school: String) -> float:
	if not ENABLE_SCHOOL_MOD or school != "physical":
		return 1.0
	return minf(SCHOOL_MOD_CAP, 1.0 / TOWER_PHYS_FACTOR)


# ─── C. STARTER CATCH-UP ─────────────────────────────────────────────────
## Remaining catch-up by level (1.0 at `lv<=STARTER_CATCHUP_LV0`, decaying to
## `STARTER_CATCHUP_DECAY` at `lv>=STARTER_CATCHUP_LV1`).
static func starter_level_factor(level: int) -> float:
	var lv := maxi(1, level)
	var t := float(lv - STARTER_CATCHUP_LV0) / float(
		maxi(1, STARTER_CATCHUP_LV1 - STARTER_CATCHUP_LV0)
	)
	t = minf(1.0, maxf(0.0, t))
	return 1.0 - (1.0 - STARTER_CATCHUP_DECAY) * t


## `(hp, damage)` multiplier for a starter hero; inverse to the unlocked roster.
static func starter_catchup(hero_type: String, boss_unlocks: int, level: int = 1) -> Array:
	if not ENABLE_STARTER_CATCHUP or not STARTER_HEROES.has(hero_type):
		return [1.0, 1.0]
	var t := minf(1.0, maxf(0.0, float(boss_unlocks) / float(STARTER_CATCHUP_REF)))
	var k := 1.0 + (STARTER_CATCHUP_MAX - 1.0) * (1.0 - t) * starter_level_factor(level)
	if k <= 1.001:
		return [1.0, 1.0]
	return [1.0 + (k - 1.0) * 1.25, 1.0 + (k - 1.0) * 0.85]


## The starter `(hp, damage)` the battle actually reads.
static func starter_catchup_stats(
	hero_type: String, stats: Dictionary, boss_unlocks: int, level: int = 1
) -> Array:
	var multiplier := starter_catchup(hero_type, boss_unlocks, level)
	var y := float(multiplier[0])
	var x := float(multiplier[1])
	return [
		maxi(1, int(Archetypes.round_half_even(_num_or(stats.get("hp", 1), 1.0) * y))),
		maxi(1, int(Archetypes.round_half_even(_num_or(stats.get("damage", 1), 1.0) * x))),
	]


## How many hero unlocks (not starters) the player already bought.
static func boss_unlocks_for_purchases(purchased: Array) -> int:
	var count := 0
	for hero_type in purchased:
		if not STARTER_HEROES.has(String(hero_type)):
			count += 1
	return count


# ─── B. SCHOOL CORRECTION: parity, not a buff ────────────────────────────
## DPS that actually lands on the boss this hero faces.
static func eff_dps(
	res: Dictionary, hero_type: String, stats: Dictionary, _m: Dictionary, dps: float
) -> float:
	var arch := Archetypes.get_archetype(hero_type, stats)
	var key := String(stats.get("unlock_require_boss", ""))
	if key.is_empty():
		key = hero_type
	var armor := 0.0
	var mr := 0.0
	if res.has(key):
		var row: Dictionary = res[key]
		armor = float(row["armor"])
		mr = float(row["magic_resist"])
	else:
		var pair := Archetypes.resist_from_profile(
			"balanced", String(stats.get("boss_class", "mini"))
		)
		armor = float(pair[0])
		mr = float(pair[1])
	var mult := (
		Archetypes.physical_mitigation(armor)
		if String(arch["dmg_type"]) == "PHYSICAL"
		else 1.0 - mr
	)
	return dps * mult


## Power score after the multipliers: `0.8 * DPS + 0.2 * EHP` relative to the pool
## medians — EXACTLY the formula `tools/balance_audit.py` measures.
static func final_power(
	m: Dictionary, y: float, x_dmg: float, x_sk: float, med_dps: float, med_ehp: float
) -> float:
	var dps := (float(m["dmg"]) * x_dmg) * 60.0 / float(m["cd"]) \
		+ (float(m["skill"]) * x_sk) * 60.0 / float(m["skcd"])
	var ehp := float(m["ehp"]) * y
	return 0.8 * dps / med_dps + 0.2 * ehp / med_ehp


## Damage multiplier per archetype cell (school x style); the mean power of every
## cell is pushed to the pool target while the total pool power is held.
static func cell_parity_factors(
	boss: Dictionary,
	met: Dictionary,
	raw: Dictionary,
	med_dps: float,
	med_ehp: float,
	iters: int = 18
) -> Array:
	var res: Dictionary = Archetypes.BOSS_RESISTANCES
	var cell := {}
	var base := {}
	var valid: Array = []
	for hero_type in boss:
		var m: Dictionary = met[hero_type]
		if float(m["dps"]) <= 0.0:
			continue
		var stats: Dictionary = boss[hero_type]
		var arch := Archetypes.get_archetype(hero_type, stats)
		var style := String(arch.get("playstyle", ""))
		if style.is_empty():
			style = "FIGHTER"
		cell[hero_type] = "%s|%s" % [String(arch["dmg_type"]), style]
		var triple: Array = raw[hero_type]
		base[hero_type] = [float(triple[0]), float(triple[1]), float(triple[2])]
		valid.append(hero_type)
	if valid.is_empty():
		return [{}, null]
	var powers: Array = []
	for hero_type in valid:
		var triple: Array = base[hero_type]
		powers.append(final_power(
			met[hero_type], float(triple[0]), float(triple[1]), float(triple[2]),
			med_dps, med_ehp
		))
	var target := _mean(powers)
	var factors := {}
	for hero_type in valid:
		factors[cell[hero_type]] = 1.0
	var by_cell := {}
	for hero_type in valid:
		var key: String = cell[hero_type]
		if not by_cell.has(key):
			by_cell[key] = []
		(by_cell[key] as Array).append(hero_type)
	for _iteration in range(iters):
		for key in by_cell:
			var members: Array = by_cell[key]
			var values: Array = []
			for hero_type in members:
				var triple: Array = base[hero_type]
				var g := float(factors[key])
				values.append(final_power(
					met[hero_type], float(triple[0]), float(triple[1]) * g,
					float(triple[2]) * g, med_dps, med_ehp
				))
			var cur := _mean(values)
			if cur > 0.0:
				factors[key] = float(factors[key]) * (target / cur)
				factors[key] = _clamp(
					float(factors[key]), [1.0 / CELL_PARITY_CAP, CELL_PARITY_CAP]
				)
		var every: Array = []
		for hero_type in valid:
			var triple2: Array = base[hero_type]
			var g2 := float(factors[cell[hero_type]])
			every.append(final_power(
				met[hero_type], float(triple2[0]), float(triple2[1]) * g2,
				float(triple2[2]) * g2, med_dps, med_ehp
			))
		var mean_all := _mean(every)
		if mean_all > 0.0:
			var g3 := pow(target / mean_all, 0.9)
			for key in factors:
				factors[key] = _clamp(
					float(factors[key]) * g3, [1.0 / CELL_PARITY_CAP, CELL_PARITY_CAP]
				)
	var cells := {}
	for key in factors:
		cells[key] = round_py(float(factors[key]), 4)
	return [factors, {"pool_target": round_py(target, 3), "cells": cells}]


## `pristine_boss_stats()`: the raw catalog before any balance pass.
##
## Python reads it back from `bosses.boss_data`; the port receives it from the
## caller (the runtime catalog is baked `.tres` data). Deviation D1.
static func pristine_boss_stats() -> Dictionary:
	return {}


# ─── POOL + RESOLVE ──────────────────────────────────────────────────────
## The pool statistics `resolve_catalog` derives from the boss-hero catalog.
static func pool_for(catalog: Dictionary) -> Dictionary:
	var met := {}
	for hero_type in catalog:
		var stats: Dictionary = catalog[hero_type]
		if not bool(stats.get("is_boss_hero", false)):
			continue
		met[hero_type] = metrics(stats)
	var ratios: Array = []
	var budgets: Array = []
	for hero_type in met:
		var m: Dictionary = met[hero_type]
		if float(m["dps"]) > 0.0 and float(m["ehp"]) > 0.0:
			ratios.append(float(m["ehp"]) / float(m["dps"]))
		budgets.append(float(m["budget"]))
	ratios.sort()
	budgets.sort()
	var buckets := {}
	for hero_type in met:
		var m2: Dictionary = met[hero_type]
		if float(m2["cost"]) <= 0.0 or float(m2["budget"]) <= 0.0:
			continue
		var bucket := int(Archetypes.round_half_even(float(m2["cost"]) / COST_BUCKET)) * COST_BUCKET
		if not buckets.has(bucket):
			buckets[bucket] = []
		(buckets[bucket] as Array).append(float(m2["budget"]) / float(m2["cost"]))
	var eff_by_bucket := {}
	for bucket2 in buckets:
		var values: Array = buckets[bucket2]
		if values.size() >= COST_EFF_MIN_GROUP:
			eff_by_bucket[bucket2] = _median(values)
	# Shop meta: every unlock hero costs the same, so "worth it" is measured
	# against the pool median, not an in-game price band.
	var meta_costs := {}
	for hero_type2 in catalog:
		var stats2: Dictionary = catalog[hero_type2]
		if not bool(stats2.get("is_boss_hero", false)):
			continue
		var cost := _num_zero(stats2.get("unlock_cost"))
		if not meta_costs.has(cost):
			meta_costs[cost] = []
		(meta_costs[cost] as Array).append(metrics(stats2)["budget"])
	var meta_med := 0.0
	for cost2 in meta_costs:
		var values2: Array = meta_costs[cost2]
		if float(cost2) > 0.0 and values2.size() >= 20:
			meta_med = _median(values2)
			break
	var n_b := budgets.size() if budgets.size() > 0 else 1
	var dps_values: Array = []
	var ehp_values: Array = []
	for hero_type3 in met:
		dps_values.append(float((met[hero_type3] as Dictionary)["dps"]))
		ehp_values.append(float((met[hero_type3] as Dictionary)["ehp"]))
	var med_dps := _median(dps_values)
	var med_ehp := _median(ehp_values)
	return {
		"met": met,
		"med_ratio": _median(ratios),
		"med_budget": _median(budgets),
		"p50_budget": float(budgets[n_b / 2]) if not budgets.is_empty() else 0.0,
		"eff_by_bucket": eff_by_bucket,
		"meta_med": meta_med,
		"med_dps": med_dps if med_dps != 0.0 else 1.0,
		"med_ehp": med_ehp if med_ehp != 0.0 else 1.0,
	}


## Final multiplier for EVERY hero at once — `hero_type -> {hp, dmg, skill, dbg}`.
##
## Must run on the whole pool: the power score medians, the archetype-cell parity
## and the price-group median are all pool-relative. Deviation D2: the starter
## unlock count is an argument instead of a read from `__main__.game_instance`.
static func resolve_catalog(catalog: Dictionary, unlocks: int = 0) -> Dictionary:
	var out := {}
	var boss := {}
	for hero_type in catalog:
		var stats: Dictionary = catalog[hero_type]
		if not bool(stats.get("is_boss_hero", false)):
			continue
		var copy: Dictionary = stats.duplicate(true)
		copy["__hero_type__"] = hero_type
		boss[hero_type] = copy
	if boss.is_empty():
		return out

	var pool := pool_for(catalog)
	var met: Dictionary = pool["met"]
	var med_dps := float(pool["med_dps"])
	var med_ehp := float(pool["med_ehp"])

	var raw := {}
	for hero_type2 in boss:
		raw[hero_type2] = stat_multipliers(boss[hero_type2], pool)

	# ── archetype-cell parity (role identity) ──
	if CELL_PARITY:
		var parity := cell_parity_factors(boss, met, raw, med_dps, med_ehp)
		last_result["parity"] = parity[1] if parity[1] != null else {}
		var factors: Dictionary = parity[0]
		if not factors.is_empty():
			for hero_type3 in raw:
				var entry: Array = raw[hero_type3]
				var target: Array = entry[3]
				var g := float(factors.get("%s|%s" % [String(target[4]), String(target[5])], 1.0))
				raw[hero_type3] = [
					float(entry[0]), float(entry[1]) * g, float(entry[2]) * g, target
				]

	# ── ANCHOR: the mean multiplier of every stat is 1.0 (redistribution) ──
	var fin := {}
	for hero_type4 in raw:
		var triple: Array = raw[hero_type4]
		fin[hero_type4] = [float(triple[0]), float(triple[1]), float(triple[2])]
	var bands := [HP_MULT_RANGE, DMG_MULT_RANGE, DMG_MULT_RANGE]
	for index in range(3):
		var values: Array = []
		for hero_type5 in fin:
			values.append(float((fin[hero_type5] as Array)[index]))
		var avg := _mean(values)
		if avg == 0.0:
			avg = 1.0
		for hero_type6 in fin:
			var anchored: Array = fin[hero_type6]
			anchored[index] = _clamp(float(anchored[index]) / avg, bands[index])
			fin[hero_type6] = anchored

	# ── SCHOOL parity on EFFECTIVE damage, per boss class ──
	if SCHOOL_PARITY:
		var res: Dictionary = Archetypes.BOSS_RESISTANCES
		for _pass in range(8):
			var eff := {}
			for hero_type7 in boss:
				var m: Dictionary = met[hero_type7]
				if float(m["dps"]) <= 0.0:
					continue
				var pair: Array = fin[hero_type7]
				var dps := (float(m["dmg"]) * float(pair[1])) * 60.0 / float(m["cd"]) \
					+ (float(m["skill"]) * float(pair[2])) * 60.0 / float(m["skcd"])
				var stats3: Dictionary = boss[hero_type7]
				var e := eff_dps(res, hero_type7, stats3, m, dps)
				var target2: Array = raw[hero_type7][3]
				var key := "%s|%s" % [
					String(stats3.get("boss_class", "mini")), String(target2[4])
				]
				if not eff.has(key):
					eff[key] = []
				(eff[key] as Array).append(e)
			var by_class := {}
			for key2 in eff:
				var dc := String(key2).get_slice("|", 0)
				if not by_class.has(dc):
					by_class[dc] = []
				(by_class[dc] as Array).append_array(eff[key2])
			var target_by_class := {}
			for dc2 in by_class:
				var values2: Array = by_class[dc2]
				if not values2.is_empty():
					target_by_class[dc2] = _mean(values2)
			if target_by_class.is_empty():
				break
			var moved := 0.0
			var f2 := {}
			for key3 in eff:
				var values3: Array = eff[key3]
				var cur := _mean(values3)
				var t_dc := float(target_by_class.get(key3.split("|")[0], 0.0))
				if t_dc <= 0.0 or cur <= 0.0:
					f2[key3] = 1.0
					continue
				var factor := _clamp(
					t_dc / cur, [1.0 / SCHOOL_PARITY_CAP, SCHOOL_PARITY_CAP]
				)
				f2[key3] = factor
				moved = maxf(moved, absf(factor - 1.0))
			# Hold the pool damage mean: divide by the hero-count weighted mean
			# per class, so parity never becomes a global buff.
			var wavg := {}
			for dc3 in by_class:
				var total := 0.0
				var count := 0
				for key4 in f2:
					if key4.split("|")[0] != dc3:
						continue
					var n: int = (eff[key4] as Array).size()
					total += float(f2[key4]) * float(n)
					count += n
				wavg[dc3] = total / float(count) if count > 0 else 1.0
			for hero_type8 in fin:
				var dc4 := String((boss[hero_type8] as Dictionary).get("boss_class", "mini"))
				var arch_key := "%s|%s" % [
					dc4, String((raw[hero_type8] as Array)[3][4])
				]
				var g2 := float(f2.get(arch_key, 1.0)) / float(wavg.get(dc4, 1.0))
				var scaled: Array = fin[hero_type8]
				scaled[1] = float(scaled[1]) * g2
				scaled[2] = float(scaled[2]) * g2
				fin[hero_type8] = scaled
			var parity_report: Dictionary = last_result.get("parity", {})
			var schools := {}
			for key5 in f2:
				schools[key5] = round_py(float(f2[key5]), 4)
			parity_report["schools"] = schools
			last_result["parity"] = parity_report
			if moved < 0.002:
				break

	for hero_type9 in fin:
		var triple2: Array = fin[hero_type9]
		var target3: Array = raw[hero_type9][3]
		var m2: Dictionary = target3[0]
		var s_mod := 1.0
		if not SCHOOL_PARITY:
			s_mod = school_mod(String(target3[4]).to_lower())
		var ratio_from := 0.0
		if float(m2["dps"]) > 0.0:
			ratio_from = round_py(float(m2["ehp"]) / float(m2["dps"]), 3)
		out[hero_type9] = {
			"hp": round_py(float(triple2[0]), 4),
			"dmg": round_py(float(triple2[1]) * s_mod, 4),
			"skill": round_py(float(triple2[2]) * s_mod, 4),
			"dbg": {
				"ratio_from": ratio_from,
				"ratio_to": round_py(float(target3[1]), 3),
				"price_corr": round_py(float(target3[3]), 4),
				"playstyle": target3[5],
				"dmg_type": target3[4],
				"boss_class": (boss[hero_type9] as Dictionary).get("boss_class"),
			},
		}

	# ── starters: catch-up only (their base stats are small, no re-budget) ──
	for hero_type10 in catalog:
		var stats4: Dictionary = catalog[hero_type10]
		if bool(stats4.get("is_boss_hero", false)):
			continue
		var multipliers := starter_catchup(hero_type10, unlocks, 1)
		out[hero_type10] = {
			"hp": round_py(float(multipliers[0]), 4),
			"dmg": round_py(float(multipliers[1]), 4),
			"skill": 1.0,
			"dbg": {
				"starter_unlocks": unlocks,
				"playstyle": null,
				"dmg_type": Archetypes.get_archetype(hero_type10, stats4)["dmg_type"],
				"boss_class": null,
			},
		}
	return out


# ─── boss resistances: profile calibration -> parity, no global buff ─────
## Calibrates armor/MR to `(table, report)`; both class means are pinned to their
## baselines, so calibration only moves WHO is resisted by WHAT.
static func calibrate_boss_resistances(
	rows: Array,
	target_ratio: float = 0.0,
	_scale_lo: float = 0.6,
	scale_hi: float = 1.8,
	n_step: int = 25
) -> Array:
	var base: Dictionary = Archetypes.BOSS_RESIST_BASE
	var raw_mods: Dictionary = Archetypes.BOSS_RESIST_PROFILE_MODS
	var target := target_ratio if target_ratio != 0.0 else Archetypes.BOSS_RESIST_TARGET_RATIO

	var by_class := {}
	for row in rows:
		var row_data: Dictionary = row
		var dc := String(row_data["boss_class"])
		if not by_class.has(dc):
			by_class[dc] = []
		(by_class[dc] as Array).append(row_data)

	var mods_by_class := {}
	var report := {}
	var scales := {}
	for dc2 in by_class:
		var class_rows: Array = by_class[dc2]
		var mods := _zero_mean(raw_mods, class_rows)
		var baseline: Array = base[dc2]
		var solved := _solve_scales(dc2, class_rows, base, mods, target, scale_hi, n_step)
		var sa := float(solved[0])
		var sm := float(solved[1])
		var ratio := float(solved[2])
		var av_a := float(solved[3])
		var av_mr := float(solved[4])
		for _iteration in range(6):
			var da := {}
			for profile in mods:
				var pair: Array = mods[profile]
				da[profile] = [float(pair[0]) - (av_a - float(baseline[0])), float(pair[1])]
			var db := {}
			for profile2 in da:
				var pair2: Array = da[profile2]
				db[profile2] = [
					float(pair2[0]), float(pair2[1]) - (av_mr - float(baseline[1]))
				]
			var next := _stats_for(dc2, class_rows, base, db, sa, sm, target)
			if absf(float(next[0]) - target) <= absf(ratio - target) + 0.02:
				mods = db
				ratio = float(next[0])
				av_a = float(next[1])
				av_mr = float(next[2])
				break
			var armor_first := _stats_for(dc2, class_rows, base, da, sa, sm, target)
			if absf(float(armor_first[1]) - float(baseline[0])) \
					< absf(av_a - float(baseline[0])):
				mods = da
				ratio = float(armor_first[0])
				av_a = float(armor_first[1])
				av_mr = float(armor_first[2])
		mods_by_class[dc2] = mods
		scales[dc2] = {"armor": sa, "mr": sm}
		report[dc2] = {
			"magic_over_phys": round_py(ratio, 3),
			"avg_armor": round_py(av_a, 1),
			"avg_mr": round_py(av_mr, 4),
			"scale": {"armor": sa, "mr": sm},
			"mods": mods,
		}
	var scale_report := {}
	for dc3 in scales:
		scale_report[dc3] = {
			"armor_scale": float(scales[dc3]["armor"]),
			"mr_scale": float(scales[dc3]["mr"]),
		}
	report["_scales"] = scale_report
	report["_mods_mini"] = (report.get("mini", {}) as Dictionary).get("mods", {})

	var res := {}
	for row2 in rows:
		var row_data2: Dictionary = row2
		var dc4 := String(row_data2["boss_class"])
		var scale_row: Dictionary = scales.get(dc4, {"armor": 1.0, "mr": 1.0})
		var pair3 := Archetypes.resist_from_profile(
			String(row_data2.get("profile", "balanced")),
			dc4,
			base,
			mods_by_class.get(dc4, {}),
			float(scale_row["armor"]),
			float(scale_row["mr"])
		)
		res[String(row_data2["boss_type"])] = {
			"armor": int(float(pair3[0])),
			"magic_resist": round_py(float(pair3[1]), 3),
			"profile": String(row_data2.get("profile", "balanced")),
			"boss_class": dc4,
		}
	return [res, report]


## Per-class zero mean of the profile modifiers.
static func _zero_mean(raw_mods: Dictionary, rows: Array) -> Dictionary:
	var n := rows.size() if rows.size() > 0 else 1
	var sum_armor := 0.0
	var sum_mr := 0.0
	for row in rows:
		var profile := String((row as Dictionary).get("profile", "balanced"))
		var pair: Array = raw_mods.get(profile, [0.0, 0.0])
		sum_armor += float(pair[0])
		sum_mr += float(pair[1])
	var mean_armor := sum_armor / float(n)
	var mean_mr := sum_mr / float(n)
	var out := {}
	for profile2 in raw_mods:
		var pair2: Array = raw_mods[profile2]
		out[profile2] = [float(pair2[0]) - mean_armor, float(pair2[1]) - mean_mr]
	return out


## `(ratio, avg_armor, avg_mr)` for one class and one profile-modifier table.
static func _stats_for(
	boss_class: String,
	rows: Array,
	base: Dictionary,
	mods: Dictionary,
	armor_scale: float,
	mr_scale: float,
	_target: float
) -> Array:
	var p_sum := 0.0
	var m_sum := 0.0
	var p_n := 0
	var m_n := 0
	var a_sum := 0.0
	var mr_sum := 0.0
	for row in rows:
		var row_data: Dictionary = row
		var pair := Archetypes.resist_from_profile(
			String(row_data.get("profile", "balanced")), boss_class, base, mods,
			armor_scale, mr_scale
		)
		var armor := float(pair[0])
		var mr := float(pair[1])
		a_sum += armor
		mr_sum += mr
		var dps := _num_zero(row_data.get("dps"))
		if String(row_data.get("dmg_type", "")) == "PHYSICAL":
			p_sum += dps * Archetypes.physical_mitigation(armor)
			p_n += 1
		else:
			m_sum += dps * (1.0 - mr)
			m_n += 1
	var n := rows.size() if rows.size() > 0 else 1
	var ratio := 1.0
	if p_n > 0 and m_n > 0:
		ratio = (m_sum / float(m_n)) / maxf(p_sum / float(p_n), 1e-9)
	return [ratio, a_sum / float(n), mr_sum / float(n)]


## Grid search over the two positive scales, with the baseline lock penalty.
static func _solve_scales(
	boss_class: String,
	rows: Array,
	base: Dictionary,
	mods: Dictionary,
	target: float,
	scale_hi: float,
	n_step: int
) -> Array:
	var baseline: Array = base[boss_class]
	var best_score := 9e9
	var best_armor := 1.0
	var best_mr := 1.0
	for i in range(n_step):
		for j in range(n_step):
			var sa := 1.0 + (scale_hi - 1.0) * float(i) / float(maxi(n_step - 1, 1))
			var sm := 1.0 + (scale_hi - 1.0) * float(j) / float(maxi(n_step - 1, 1))
			var stats := _stats_for(boss_class, rows, base, mods, sa, sm, target)
			var penalty := maxf(0.0, absf(float(stats[1]) - float(baseline[0])) - 0.6) * 0.5
			penalty += maxf(0.0, absf(float(stats[2]) - float(baseline[1])) - 0.006) * 120.0
			var score := absf(float(stats[0]) - target) + penalty
			if score < best_score:
				best_score = score
				best_armor = sa
				best_mr = sm
	var final_stats := _stats_for(boss_class, rows, base, mods, best_armor, best_mr, target)
	return [
		best_armor, best_mr,
		float(final_stats[0]), float(final_stats[1]), float(final_stats[2]),
	]


# ─── POOL MEAN ANCHOR + FINAL FIXPOINT ───────────────────────────────────
## Uniform multiplier so the pool mean (DPS or EHP) returns to its pre-balance
## number. Uniform = touches no parity, only the level; capped by
## `POOL_MEAN_TOL_MAX` so balance never becomes a silent global buff/nerf.
static func pool_mean_rescale(
	catalog: Dictionary, before: Dictionary, which: String = "dps", tol: float = 0.005
) -> float:
	if before.is_empty():
		return 1.0
	var ids: Array = []
	for hero_type in before:
		if catalog.has(hero_type) and bool((catalog[hero_type] as Dictionary).get(
				"is_boss_hero", false)):
			ids.append(hero_type)
	if ids.is_empty():
		return 1.0
	var key := "dps" if which == "dps" else "ehp"
	var current_values: Array = []
	var before_values: Array = []
	for hero_type2 in ids:
		current_values.append(float(metrics(catalog[hero_type2])[key]))
		before_values.append(float((before[hero_type2] as Dictionary)[key]))
	var cur := _mean(current_values)
	if cur == 0.0:
		cur = 1.0
	var want := _mean(before_values)
	if want <= 0.0 or cur <= 0.0:
		return 1.0
	var g := _clamp(want / cur, [1.0 - POOL_MEAN_TOL_MAX, 1.0 + POOL_MEAN_TOL_MAX])
	if absf(g - 1.0) < tol:
		return 1.0
	for hero_type3 in ids:
		var v: Dictionary = catalog[hero_type3]
		if which == "dps":
			for key2 in [
				"damage", "skill_damage", "skill_q_damage", "skill_w_damage",
				"skill_e_damage", "skill_r_damage",
			]:
				if _num_zero(v.get(key2)) != 0.0:
					v[key2] = maxi(0, int(Archetypes.round_half_even(
						_num_zero(v[key2]) * g
					)))
		else:
			v["hp"] = maxi(1, int(Archetypes.round_half_even(
				_num_or(v.get("hp", 1), 1.0) * g
			)))
		var b: Dictionary = v.get("__bal", {})
		if not b.is_empty():
			var bk := "dmg" if which == "dps" else "hp"
			b[bk] = round_py(float(b[bk]) * g, 4)
			if which == "dps":
				b["skill"] = round_py(float(b["skill"]) * g, 4)
	return g


## Small correction applied DIRECTLY to the final stats, measured with the audit
## formula: (a) physical effective DPS == magic per boss class and (b) every
## archetype cell's mean power == the pool mean, iterated together.
static func final_fixpoint(
	catalog: Dictionary,
	school_target: float = 1.0,
	cell_band: Variant = null,
	passes: int = 40,
	damp: float = 0.85,
	tol: float = 0.002
) -> Dictionary:
	var ids: Array = []
	for hero_type in catalog:
		var v: Dictionary = catalog[hero_type]
		if bool(v.get("is_boss_hero", false)) and float(metrics(v)["dps"]) > 0.0:
			ids.append(hero_type)
	if ids.size() < 20:
		return {"skipped": "hero terlalu sedikit"}
	var fac := {}
	for hero_type2 in ids:
		fac[hero_type2] = 1.0
	var info := {}
	for pass_index in range(passes):
		var f_sch := {}
		var f_cell := {}
		# (a) school parity: MITIGATED DPS per (boss class, school)
		var eff := {}
		for hero_type3 in ids:
			var v2: Dictionary = catalog[hero_type3]
			var m := metrics(v2)
			var pair := Archetypes.get_boss_resistances(
				String(v2.get("unlock_require_boss", "")) if not String(
					v2.get("unlock_require_boss", "")
				).is_empty() else hero_type3,
				String(v2.get("boss_class", "mini"))
			)
			var school := String(Archetypes.get_archetype(hero_type3, v2)["dmg_type"])
			var mit := (
				Archetypes.physical_mitigation(float(pair[0]))
				if school == "PHYSICAL"
				else 1.0 - float(pair[1])
			)
			var key := "%s|%s" % [String(v2.get("boss_class", "mini")), school]
			if not eff.has(key):
				eff[key] = []
			(eff[key] as Array).append(float(m["dps"]) * float(fac[hero_type3]) * mit)
		var by_class := {}
		for key2 in eff:
			var dc := String(key2).get_slice("|", 0)
			if not by_class.has(dc):
				by_class[dc] = []
			(by_class[dc] as Array).append_array(eff[key2])
		for key3 in eff:
			var values: Array = eff[key3]
			var cur := _mean(values)
			var tgt := _mean(by_class[key3.split("|")[0]]) * school_target \
				if by_class.has(key3.split("|")[0]) else cur
			if cur > 0.0 and tgt > 0.0:
				f_sch[key3] = pow(tgt / cur, damp)
		# (b) power per archetype cell -> pool mean. The audit compares a cell
		# MEAN against the MEDIAN of the same pool; using a mean on both sides
		# never converges on a skewed distribution, so both sides stay means.
		var dps_all: Array = []
		var ehp_all: Array = []
		for hero_type4 in ids:
			var m2 := metrics(catalog[hero_type4])
			dps_all.append(float(m2["dps"]))
			ehp_all.append(float(m2["ehp"]))
		var med_d := _mean(dps_all)
		if med_d == 0.0:
			med_d = 1.0
		var med_e := _mean(ehp_all)
		if med_e == 0.0:
			med_e = 1.0
		var cell := {}
		for hero_type5 in ids:
			var a := Archetypes.get_archetype(hero_type5, catalog[hero_type5])
			var m3 := metrics(catalog[hero_type5])
			var power := 0.8 * float(m3["dps"]) * float(fac[hero_type5]) / med_d \
				+ 0.2 * float(m3["ehp"]) / med_e
			var key4 := "%s|%s" % [String(a["dmg_type"]), String(a.get("playstyle", "FIGHTER"))]
			if not cell.has(key4):
				cell[key4] = []
			(cell[key4] as Array).append([hero_type5, power])
		var all_power: Array = []
		for key5 in cell:
			for pair2 in cell[key5]:
				all_power.append(float((pair2 as Array)[1]))
		var target_cell := _mean(all_power)
		if cell_band != null:
			for key6 in cell:
				var entries: Array = cell[key6]
				var powers: Array = []
				for pair3 in entries:
					powers.append(float((pair3 as Array)[1]))
				var cur_cell := _mean(powers)
				if cur_cell > 0.0:
					var g_cell := pow(target_cell / cur_cell, damp)
					f_cell[key6] = _clamp(g_cell, cell_band)
		var moved := 0.0
		for hero_type6 in ids:
			var v3: Dictionary = catalog[hero_type6]
			var a2 := Archetypes.get_archetype(hero_type6, v3)
			var g := float(f_sch.get("%s|%s" % [
				String(v3.get("boss_class", "mini")), String(a2["dmg_type"])
			], 1.0))
			var cell_key := "%s|%s" % [
				String(a2["dmg_type"]), String(a2.get("playstyle", "FIGHTER"))
			]
			g *= float(f_cell.get(cell_key, 1.0))
			g = _clamp(g, [1.0 / FINAL_CORR_CAP, FINAL_CORR_CAP])
			fac[hero_type6] = _clamp(
				float(fac[hero_type6]) * g, [1.0 / FINAL_CORR_CAP, FINAL_CORR_CAP]
			)
			moved = maxf(moved, absf(g - 1.0))
		info["passes_run"] = pass_index + 1
		info["last_move"] = round_py(moved, 4)
		if moved < tol:
			break
	for hero_type7 in ids:
		var g2 := float(fac[hero_type7])
		if absf(g2 - 1.0) < 1e-4:
			continue
		var v4: Dictionary = catalog[hero_type7]
		for key7 in [
			"damage", "skill_damage", "skill_q_damage", "skill_w_damage",
			"skill_e_damage", "skill_r_damage",
		]:
			if _num_zero(v4.get(key7)) != 0.0:
				v4[key7] = maxi(0, int(Archetypes.round_half_even(_num_zero(v4[key7]) * g2)))
		var b2: Dictionary = v4.get("__bal", {})
		if not b2.is_empty():
			b2["dmg"] = round_py(float(b2["dmg"]) * g2, 4)
			b2["skill"] = round_py(float(b2["skill"]) * g2, 4)
			var dbg: Dictionary = b2["dbg"]
			dbg["fix"] = round_py(g2, 4)
	var factors: Array = []
	for hero_type8 in fac:
		factors.append(float(fac[hero_type8]))
	info["factor_min"] = round_py(factors.min(), 4) if not factors.is_empty() else 1.0
	info["factor_max"] = round_py(factors.max(), 4) if not factors.is_empty() else 1.0
	info["n"] = ids.size()
	return info


## Apply `resolve_catalog()` to the catalog dict IN PLACE (the caller's dict is the
## one the shop, the preview and the battle read).
##
## Deviation D1: `pristine` is a parameter instead of a `bosses.boss_data` import;
## idempotence comes from that pristine reset, exactly like the source.
static func apply_to_catalog(catalog: Dictionary, pristine: Dictionary = {}) -> Dictionary:
	var src: Dictionary = catalog.duplicate(true)
	for key in pristine:
		if src.has(key):
			src[key] = (pristine[key] as Dictionary).duplicate(true)
	last_result["table"] = {}
	last_result["pool"] = {}
	last_result["parity"] = {}
	var table := resolve_catalog(src)
	var before := {}
	if POOL_MEAN_ANCHOR:
		for key2 in pristine:
			var mm := metrics(pristine[key2])
			if float(mm["dps"]) > 0.0:
				before[key2] = mm
	# Keep the RAW numbers in `dbg.raw` so the audit can compare before/after with
	# the exact same formula.
	for hero_type in pristine:
		if table.has(hero_type) and table[hero_type] != null:
			var entry: Dictionary = table[hero_type]
			var entry_dbg: Dictionary = entry["dbg"]
			entry_dbg["raw"] = {
				"hp": (pristine[hero_type] as Dictionary).get("hp"),
				"damage": (pristine[hero_type] as Dictionary).get("damage"),
				"skill_damage": (pristine[hero_type] as Dictionary).get("skill_damage"),
				"attack_cooldown": (pristine[hero_type] as Dictionary).get(
					"attack_cooldown"
				),
				"skill_cooldown": (pristine[hero_type] as Dictionary).get(
					"skill_cooldown"
				),
			}
	last_result["table"] = table
	for hero_type2 in table:
		var mult: Variant = table[hero_type2]
		if mult == null:
			continue
		if not catalog.has(hero_type2):
			continue
		var stats: Dictionary = catalog[hero_type2]
		if not bool(stats.get("is_boss_hero", false)):
			# Starters are deliberately NOT written to the catalog: their catch-up
			# depends on player state, so the only writer is the unit at spawn.
			continue
		var raw_stats: Dictionary = src.get(hero_type2, stats)
		stats["__bal"] = mult
		stats["hp"] = maxi(1, int(Archetypes.round_half_even(
			_num_or(raw_stats.get("hp", 1), 1.0) * float((mult as Dictionary)["hp"])
		)))
		stats["damage"] = maxi(1, int(Archetypes.round_half_even(
			_num_or(raw_stats.get("damage", 1), 1.0) * float((mult as Dictionary)["dmg"])
		)))
		stats["skill_damage"] = maxi(0, int(Archetypes.round_half_even(
			_num_zero(raw_stats.get("skill_damage")) * float((mult as Dictionary)["skill"])
		)))
		for key3 in [
			"skill_q_damage", "skill_w_damage", "skill_e_damage", "skill_r_damage"
		]:
			if _num_zero(raw_stats.get(key3)) != 0.0:
				stats[key3] = maxi(0, int(Archetypes.round_half_even(
					_num_zero(raw_stats[key3]) * float((mult as Dictionary)["skill"])
				)))

	# ── pool mean anchor: balance is REDISTRIBUTION, never a buff ──
	last_result["pool_anchor"] = {}
	if POOL_MEAN_ANCHOR and not before.is_empty():
		var dps_values: Array = []
		var ehp_values: Array = []
		for key4 in before:
			dps_values.append(float((before[key4] as Dictionary)["dps"]))
			ehp_values.append(float((before[key4] as Dictionary)["ehp"]))
		last_result["pool_means"] = {
			"dps": round_py(_mean(dps_values), 1),
			"ehp": round_py(_mean(ehp_values), 1),
			"n": before.size(),
		}
		var anchors := {}
		anchors["dps"] = pool_mean_rescale(catalog, before, "dps")
		anchors["ehp"] = pool_mean_rescale(catalog, before, "ehp")
		var kept := {}
		for key5 in anchors:
			var value := float(anchors[key5])
			if value != 0.0 and absf(value - 1.0) >= 0.005:
				kept[key5] = value
		last_result["pool_anchor"] = kept

	# ── final correction: school + cell parity with the audit formula ──
	if FINAL_FIXPOINT:
		last_result["fix"] = final_fixpoint(catalog)

	return catalog
