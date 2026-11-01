class_name HeroBalance
extends RefCounted

## Native port of hero_balance.py. Python remains the calibration oracle;
## tools/prepare_godot_balance.py bakes constants/pristine stats and a fixture.
const DEFAULT_PATH := "res://data/hero_balance.json"

var archetypes: HeroArchetypes
var load_error := ""
var pristine: Dictionary = {}
var starter_heroes: Array = []
var last: Dictionary = {"table": {}, "pool": {}, "parity": {}}
var enable_rebudget := true
var enable_school_mod := false
var enable_starter_catchup := true
var school_parity := true
var cell_parity := true
var pool_mean_anchor := true
var final_fixpoint_enabled := true
var w_dps := 0.72
var w_ehp := 0.28
var ehp_per_hp := 1.0 / 6.0
var target_ratio: Dictionary = {"TANK": [9.5, 13.0], "FIGHTER": [6.0, 7.5], "CARRY": [3.4, 4.6]}
var school_ratio_bonus: Dictionary = {"PHYSICAL": -0.04, "MAGIC": 0.04}
var ratio_blend := 0.55
var budget_compress := 0.45
var style_power: Dictionary = {"TANK": 0.74, "FIGHTER": 1.06, "CARRY": 1.08}
var hp_mult_range: Array = [0.66, 1.50]
var dmg_mult_range: Array = [0.68, 1.45]
var school_parity_cap := 1.45
var cell_parity_cap := 1.30
var pool_mean_tol_max := 0.18
var final_corr_cap := 1.35
var cost_bucket := 1000
var cost_eff_band: Array = [0.78, 1.28]
var cost_eff_damp := 0.60
var cost_eff_min_group := 8
var meta_eff_band: Array = [0.80, 1.25]
var meta_eff_damp := 0.75
var tower_armor_at_l3 := 5.0
var armor_factor := 0.06
var tower_phys_factor := 1.0 / (1.0 + 5.0 * 0.06)
var school_mod_cap := 1.06
var starter_catchup_max := 1.32
var starter_catchup_ref := 12
var starter_catchup_lv0 := 1
var starter_catchup_lv1 := 8
var starter_catchup_decay := 0.20


func _init(archetypes_ref: HeroArchetypes, path := DEFAULT_PATH) -> void:
	archetypes = archetypes_ref
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		load_error = "Cannot open %s" % path
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary or int(parsed.get("schema", 0)) != 1:
		load_error = "Invalid hero balance JSON: %s" % path
		return
	for key: String in ["constants", "switches", "starter_heroes", "pristine_boss_stats"]:
		if not parsed.has(key):
			load_error = "Missing hero balance field: %s" % key
			return
	var constants: Dictionary = parsed.constants
	var switches: Dictionary = parsed.switches
	pristine = parsed.pristine_boss_stats
	starter_heroes = parsed.starter_heroes
	enable_rebudget = bool(switches.get("enable_rebudget", true))
	enable_school_mod = bool(switches.get("enable_school_mod", false))
	enable_starter_catchup = bool(switches.get("enable_starter_catchup", true))
	school_parity = bool(switches.get("school_parity", true))
	cell_parity = bool(switches.get("cell_parity", true))
	pool_mean_anchor = bool(switches.get("pool_mean_anchor", true))
	final_fixpoint_enabled = bool(switches.get("final_fixpoint", true))
	w_dps = float(constants.get("w_dps", w_dps))
	w_ehp = float(constants.get("w_ehp", w_ehp))
	ehp_per_hp = float(constants.get("ehp_per_hp", ehp_per_hp))
	target_ratio = constants.get("target_ratio", target_ratio)
	school_ratio_bonus = constants.get("school_ratio_bonus", school_ratio_bonus)
	ratio_blend = float(constants.get("ratio_blend", ratio_blend))
	budget_compress = float(constants.get("budget_compress", budget_compress))
	style_power = constants.get("style_power", style_power)
	hp_mult_range = constants.get("hp_mult_range", hp_mult_range)
	dmg_mult_range = constants.get("dmg_mult_range", dmg_mult_range)
	school_parity_cap = float(constants.get("school_parity_cap", school_parity_cap))
	cell_parity_cap = float(constants.get("cell_parity_cap", cell_parity_cap))
	pool_mean_tol_max = float(constants.get("pool_mean_tol_max", pool_mean_tol_max))
	final_corr_cap = float(constants.get("final_corr_cap", final_corr_cap))
	cost_bucket = int(constants.get("cost_bucket", cost_bucket))
	cost_eff_band = constants.get("cost_eff_band", cost_eff_band)
	cost_eff_damp = float(constants.get("cost_eff_damp", cost_eff_damp))
	cost_eff_min_group = int(constants.get("cost_eff_min_group", cost_eff_min_group))
	meta_eff_band = constants.get("meta_eff_band", meta_eff_band)
	meta_eff_damp = float(constants.get("meta_eff_damp", meta_eff_damp))
	tower_armor_at_l3 = float(constants.get("tower_armor_at_l3", tower_armor_at_l3))
	armor_factor = float(constants.get("armor_factor", armor_factor))
	tower_phys_factor = float(constants.get("tower_phys_factor", tower_phys_factor))
	school_mod_cap = float(constants.get("school_mod_cap", school_mod_cap))
	starter_catchup_max = float(constants.get("starter_catchup_max", starter_catchup_max))
	starter_catchup_ref = int(constants.get("starter_catchup_ref", starter_catchup_ref))
	starter_catchup_lv0 = int(constants.get("starter_catchup_lv0", starter_catchup_lv0))
	starter_catchup_lv1 = int(constants.get("starter_catchup_lv1", starter_catchup_lv1))
	starter_catchup_decay = float(constants.get("starter_catchup_decay", starter_catchup_decay))
	if (
		pristine.is_empty()
		or starter_heroes.is_empty()
		or archetypes == null
		or not archetypes.valid()
	):
		load_error = "Hero balance contract requires pristine bosses, starters and valid archetypes"


func valid() -> bool:
	return load_error.is_empty() and not pristine.is_empty()


func metrics(stats: Dictionary) -> Dictionary:
	var hp := _num(stats, "hp", 0.0)
	var dmg := _num(stats, "damage", 0.0)
	var cd := maxf(1.0, _num(stats, "attack_cooldown", 30.0))
	var sk := _num(stats, "skill_damage", 0.0)
	var skcd := maxf(1.0, _num(stats, "skill_cooldown", 240.0))
	var basic_dps := dmg * 60.0 / cd
	var skill_dps := sk * 60.0 / skcd
	var dps := basic_dps + skill_dps
	var armor := _num(stats, "armor", 0.0)
	var mr := clampf(_num(stats, "magic_resist", 0.0), 0.0, 0.75)
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
		"cost": _num(stats, "cost", 0.0),
		"burst": (skill_dps / dps) if dps > 0.0 else 0.0,
		"budget": w_dps * dps + w_ehp * ehp * ehp_per_hp,
	}


func hero_target(stats: Dictionary, pool: Dictionary) -> Variant:
	var m := metrics(stats)
	var arch := archetypes.get_archetype(str(stats.get("__hero_type__", "")), stats)
	if float(m.dps) <= 0.0 or float(m.ehp) <= 0.0:
		return null
	var style := str(arch.get("playstyle", "FIGHTER"))
	if style.is_empty():
		style = "FIGHTER"
	var school := str(arch.get("dmg_type", "PHYSICAL"))
	if school.is_empty():
		school = "PHYSICAL"
	var tr: Array = target_ratio.get(style, target_ratio["FIGHTER"])
	var tgt_ratio := (
		0.5 * (float(tr[0]) + float(tr[1])) * (1.0 + float(school_ratio_bonus.get(school, 0.0)))
	)
	var cur_ratio := float(m.ehp) / float(m.dps)
	var ratio := cur_ratio * (1.0 - ratio_blend) + tgt_ratio * ratio_blend
	var b := float(m.budget) * float(style_power.get(style, 1.0))
	if budget_compress > 0.0 and float(pool.get("p50_budget", 0.0)) > 0.0:
		b *= pow(float(pool.p50_budget) / maxf(b, 1e-9), budget_compress)
	var price_corr := 1.0
	var meta_med := float(pool.get("meta_med", 0.0))
	if meta_med > 0.0:
		var rel := float(m.budget) / meta_med
		if rel > float(meta_eff_band[1]):
			b *= pow(float(meta_eff_band[1]) / rel, meta_eff_damp)
		elif rel < float(meta_eff_band[0]):
			b *= pow(float(meta_eff_band[0]) / rel, meta_eff_damp)
	var eff_by_bucket: Dictionary = pool.get("eff_by_bucket", {})
	var bucket := py_round(float(m.cost) / float(cost_bucket)) * cost_bucket
	var med_eff: Variant = eff_by_bucket.get(bucket)
	if _truthy(med_eff) and float(m.cost) > 0.0:
		var rel := (float(m.budget) / float(m.cost)) / float(med_eff)
		if rel > float(cost_eff_band[1]):
			price_corr = pow(float(cost_eff_band[1]) / rel, cost_eff_damp)
		elif rel < float(cost_eff_band[0]):
			price_corr = pow(float(cost_eff_band[0]) / rel, cost_eff_damp)
		b *= price_corr
	return [m, ratio, b, price_corr, school, style]


func stat_multipliers(stats: Dictionary, pool: Dictionary) -> Array:
	var t: Variant = hero_target(stats, pool)
	if t == null:
		return [1.0, 1.0, 1.0, null]
	var m: Dictionary = t[0]
	var ratio := float(t[1])
	var b := float(t[2])
	var share := 1.0 / (1.0 + (w_ehp * ehp_per_hp * ratio) / w_dps)
	var new_dps := b * share / w_dps
	var new_ehp := b * (1.0 - share) / (w_ehp * ehp_per_hp)
	var x := new_dps / float(m.dps) if float(m.dps) > 0.0 else 1.0
	var y := new_ehp / float(m.ehp) if float(m.ehp) > 0.0 else 1.0
	var x_dmg := 1.0 + (x - 1.0) * (1.0 - float(m.burst) * 1.15)
	var x_sk := 1.0 + (x - 1.0) * (float(m.burst) * 1.15)
	return [
		_clamp(y, hp_mult_range), _clamp(x_dmg, dmg_mult_range), _clamp(x_sk, dmg_mult_range), t
	]


func school_mod(school: String) -> float:
	if not enable_school_mod or school != "physical":
		return 1.0
	return minf(school_mod_cap, 1.0 / tower_phys_factor)


func is_starter(hero_type: String) -> bool:
	return hero_type in starter_heroes


func starter_level_factor(level: Variant) -> float:
	var lv := maxi(1, int(level) if _truthy(level) else 1)
	var t := (
		float(lv - starter_catchup_lv0) / float(maxi(1, starter_catchup_lv1 - starter_catchup_lv0))
	)
	t = clampf(t, 0.0, 1.0)
	return 1.0 - (1.0 - starter_catchup_decay) * t


func starter_catchup(hero_type: String, boss_unlocks: Variant, level: Variant = 1) -> Array:
	if not enable_starter_catchup or not is_starter(hero_type):
		return [1.0, 1.0]
	var unlocks := float(boss_unlocks) if _truthy(boss_unlocks) else 0.0
	var t := clampf(unlocks / float(starter_catchup_ref), 0.0, 1.0)
	var k := 1.0 + (starter_catchup_max - 1.0) * (1.0 - t) * starter_level_factor(level)
	if k <= 1.001:
		return [1.0, 1.0]
	return [1.0 + (k - 1.0) * 1.25, 1.0 + (k - 1.0) * 0.85]


func starter_catchup_stats(
	hero_type: String, stats: Dictionary, boss_unlocks: Variant, level: Variant = 1
) -> Array:
	var mult := starter_catchup(hero_type, boss_unlocks, level)
	var hp := maxi(1, py_round(_num(stats, "hp", 1.0) * float(mult[0])))
	var dmg := maxi(1, py_round(_num(stats, "damage", 1.0) * float(mult[1])))
	return [hp, dmg]


func boss_unlocks_for_purchases(purchased: Variant) -> int:
	if not _truthy(purchased):
		return 0
	var count := 0
	for hero: Variant in purchased:
		if str(hero) not in starter_heroes:
			count += 1
	return maxi(0, count)


func eff_dps(hero_type: String, stats: Dictionary, _m: Dictionary, dps: float) -> float:
	var arch := archetypes.get_archetype(hero_type, stats)
	var require_boss: Variant = stats.get("unlock_require_boss")
	var boss_key := str(require_boss) if _truthy(require_boss) else hero_type
	var entry: Dictionary = archetypes.boss_resistances.get(boss_key, {})
	var armor_value: float
	var mr: float
	if entry.is_empty():
		var fallback := archetypes.resist_from_profile("balanced", _boss_class(stats))
		armor_value = float(fallback[0])
		mr = float(fallback[1])
	else:
		armor_value = float(entry.armor)
		mr = float(entry.magic_resist)
	var mult := (
		archetypes.physical_mitigation(armor_value)
		if str(arch.dmg_type) == "PHYSICAL"
		else 1.0 - mr
	)
	return dps * mult


func final_power(
	m: Dictionary, y: float, x_dmg: float, x_sk: float, med_dps: float, med_ehp: float
) -> float:
	var dps := (
		(float(m.dmg) * x_dmg) * 60.0 / float(m.cd) + (float(m.skill) * x_sk) * 60.0 / float(m.skcd)
	)
	var ehp := float(m.ehp) * y
	return 0.8 * dps / med_dps + 0.2 * ehp / med_ehp


func cell_parity_factors(
	boss: Dictionary, met: Dictionary, raw: Dictionary, med_dps: float, med_ehp: float, iters := 18
) -> Array:
	var cell: Dictionary = {}
	var base: Dictionary = {}
	var valid: Array[String] = []
	for ht: String in boss:
		var m: Dictionary = met[ht]
		if float(m.dps) <= 0.0:
			continue
		var arch := archetypes.get_archetype(ht, boss[ht])
		var style := str(arch.get("playstyle", "FIGHTER"))
		if style.is_empty():
			style = "FIGHTER"
		var key := str(arch.dmg_type) + "|" + style
		cell[ht] = key
		var row: Array = raw[ht]
		base[ht] = [row[0], row[1], row[2]]
		valid.append(ht)
	if valid.is_empty():
		return [{}, null]
	var powers: Array[float] = []
	for ht: String in valid:
		var b: Array = base[ht]
		powers.append(final_power(met[ht], float(b[0]), float(b[1]), float(b[2]), med_dps, med_ehp))
	var target := mean(powers)
	var factors: Dictionary = {}
	var by_cell: Dictionary = {}
	for ht: String in valid:
		var key: String = cell[ht]
		factors[key] = 1.0
		if not by_cell.has(key):
			by_cell[key] = []
		by_cell[key].append(ht)
	for _iteration in range(iters):
		for key: String in by_cell:
			var values: Array[float] = []
			for ht: String in by_cell[key]:
				values.append(_cell_power(ht, base, cell, factors, met, med_dps, med_ehp))
			var cur := mean(values)
			if cur > 0.0:
				factors[key] = _clamp(
					float(factors[key]) * (target / cur), [1.0 / cell_parity_cap, cell_parity_cap]
				)
		var all_values: Array[float] = []
		for ht: String in valid:
			all_values.append(_cell_power(ht, base, cell, factors, met, med_dps, med_ehp))
		var mean_all := mean(all_values)
		if mean_all > 0.0:
			var g := pow(target / mean_all, 0.9)
			for key: String in factors:
				factors[key] = _clamp(
					float(factors[key]) * g, [1.0 / cell_parity_cap, cell_parity_cap]
				)
	var cells: Dictionary = {}
	for key: String in factors:
		cells[key] = py_round_n(float(factors[key]), 4)
	return [factors, {"pool_target": py_round_n(target, 3), "cells": cells}]


func pristine_boss_stats() -> Dictionary:
	return pristine.duplicate(true)


func resolve_catalog(catalog: Dictionary, starter_unlocks := 0, starter_level := 1) -> Dictionary:
	var out: Dictionary = {}
	var boss: Dictionary = {}
	for ht: String in catalog:
		var stats: Dictionary = catalog[ht]
		if not bool(stats.get("is_boss_hero", false)):
			continue
		var copy_stats := stats.duplicate(true)
		copy_stats["__hero_type__"] = ht
		boss[ht] = copy_stats
	if boss.is_empty():
		return out
	var met: Dictionary = {}
	for ht: String in boss:
		met[ht] = metrics(boss[ht])
	var ratios: Array[float] = []
	var budgets: Array[float] = []
	var buckets: Dictionary = {}
	for ht: String in met:
		var m: Dictionary = met[ht]
		budgets.append(float(m.budget))
		if float(m.dps) > 0.0 and float(m.ehp) > 0.0:
			ratios.append(float(m.ehp) / float(m.dps))
		if float(m.cost) <= 0.0 or float(m.budget) <= 0.0:
			continue
		var bucket := py_round(float(m.cost) / float(cost_bucket)) * cost_bucket
		if not buckets.has(bucket):
			buckets[bucket] = []
		buckets[bucket].append(float(m.budget) / float(m.cost))
	ratios.sort()
	budgets.sort()
	var eff_by_bucket: Dictionary = {}
	for bucket: int in buckets:
		if buckets[bucket].size() >= cost_eff_min_group:
			eff_by_bucket[bucket] = median(buckets[bucket])
	var meta_costs: Dictionary = {}
	for ht: String in catalog:
		var stats: Dictionary = catalog[ht]
		if not bool(stats.get("is_boss_hero", false)):
			continue
		var cost := _num(stats, "unlock_cost", 0.0)
		if not meta_costs.has(cost):
			meta_costs[cost] = []
		meta_costs[cost].append(float(metrics(stats).budget))
	var meta_med := 0.0
	for cost: float in meta_costs:
		if cost > 0.0 and meta_costs[cost].size() >= 20:
			meta_med = median(meta_costs[cost])
			break
	var n_b := budgets.size() if not budgets.is_empty() else 1
	var pool := {
		"med_ratio": median(ratios),
		"med_budget": median(budgets),
		"p50_budget": budgets[n_b / 2] if not budgets.is_empty() else 0.0,
		"eff_by_bucket": eff_by_bucket,
		"meta_med": meta_med,
	}
	var med_dps := median(_values(met, "dps"))
	if med_dps == 0.0:
		med_dps = 1.0
	var med_ehp := median(_values(met, "ehp"))
	if med_ehp == 0.0:
		med_ehp = 1.0
	pool["med_dps"] = med_dps
	pool["med_ehp"] = med_ehp
	var raw: Dictionary = {}
	for ht: String in boss:
		raw[ht] = stat_multipliers(boss[ht], pool)
	if cell_parity:
		var parity := cell_parity_factors(boss, met, raw, med_dps, med_ehp)
		var fac: Dictionary = parity[0]
		last["parity"] = parity[1] if parity[1] != null else {}
		if not fac.is_empty():
			for ht: String in raw:
				var row: Array = raw[ht]
				var t: Array = row[3]
				var g := float(fac.get(str(t[4]) + "|" + str(t[5]), 1.0))
				raw[ht] = [row[0], float(row[1]) * g, float(row[2]) * g, t]
	var fin: Dictionary = {}
	for ht: String in raw:
		var row: Array = raw[ht]
		fin[ht] = [float(row[0]), float(row[1]), float(row[2])]
	var ranges := [hp_mult_range, dmg_mult_range, dmg_mult_range]
	for index in range(3):
		var values: Array[float] = []
		for ht: String in fin:
			values.append(float(fin[ht][index]))
		var avg := mean(values)
		if avg == 0.0:
			avg = 1.0
		for ht: String in fin:
			fin[ht][index] = _clamp(float(fin[ht][index]) / avg, ranges[index])
	if school_parity:
		_school_parity_passes(boss, met, raw, fin)
	for ht: String in fin:
		var t: Array = raw[ht][3]
		var m: Dictionary = t[0]
		var s_mod := school_mod(str(t[4]).to_lower()) if not school_parity else 1.0
		var ratio_from := py_round_n(float(m.ehp) / float(m.dps), 3) if float(m.dps) > 0.0 else 0.0
		out[ht] = {
			"hp": py_round_n(float(fin[ht][0]), 4),
			"dmg": py_round_n(float(fin[ht][1]) * s_mod, 4),
			"skill": py_round_n(float(fin[ht][2]) * s_mod, 4),
			"dbg":
			{
				"ratio_from": ratio_from,
				"ratio_to": py_round_n(float(t[1]), 3),
				"price_corr": py_round_n(float(t[3]), 4),
				"playstyle": t[5],
				"dmg_type": t[4],
				"boss_class": boss[ht].get("boss_class"),
			},
		}
	for ht: String in catalog:
		var stats: Dictionary = catalog[ht]
		if bool(stats.get("is_boss_hero", false)):
			continue
		var mult := starter_catchup(ht, starter_unlocks, starter_level)
		out[ht] = {
			"hp": py_round_n(float(mult[0]), 4),
			"dmg": py_round_n(float(mult[1]), 4),
			"skill": 1.0,
			"dbg":
			{
				"starter_unlocks": starter_unlocks,
				"playstyle": null,
				"dmg_type": archetypes.get_archetype(ht, stats).dmg_type,
				"boss_class": null,
			},
		}
	return out


func calibrate_boss_resistances(
	rows: Array, target_ratio: Variant = null, _scale_lo := 0.6, scale_hi := 1.8, n_step := 25
) -> Array:
	var target := float(target_ratio) if _truthy(target_ratio) else archetypes.resist_target_ratio
	var by_class: Dictionary = {}
	for row: Dictionary in rows:
		var dc := str(row.boss_class)
		if not by_class.has(dc):
			by_class[dc] = []
		by_class[dc].append(row)
	var mods_by_class: Dictionary = {}
	var report: Dictionary = {}
	var scales: Dictionary = {}
	for dc: String in by_class:
		var mods := _cal_zero_mean(by_class[dc])
		var solved := _cal_solve(dc, mods, true, by_class, target, scale_hi, n_step)
		var sa := float(solved[0])
		var sm := float(solved[1])
		var ratio := float(solved[2][0])
		var av_a := float(solved[2][1])
		var av_mr := float(solved[2][2])
		var baseline: Array = archetypes.resist_base[dc]
		for _attempt in range(6):
			var da: Dictionary = {}
			for profile: String in mods:
				da[profile] = [
					float(mods[profile][0]) - (av_a - float(baseline[0])), float(mods[profile][1])
				]
			var db: Dictionary = {}
			for profile: String in da:
				db[profile] = [
					float(da[profile][0]), float(da[profile][1]) - (av_mr - float(baseline[1]))
				]
			var r2 := _cal_stats_for(dc, db, sa, sm, by_class)
			if absf(float(r2[0]) - target) <= absf(ratio - target) + 0.02:
				mods = db
				ratio = float(r2[0])
				av_a = float(r2[1])
				av_mr = float(r2[2])
				break
			var r3 := _cal_stats_for(dc, da, sa, sm, by_class)
			if absf(float(r3[1]) - float(baseline[0])) < absf(av_a - float(baseline[0])):
				mods = da
				ratio = float(r3[0])
				av_a = float(r3[1])
				av_mr = float(r3[2])
		mods_by_class[dc] = mods
		scales[dc] = {"armor": sa, "mr": sm}
		report[dc] = {
			"magic_over_phys": py_round_n(ratio, 3),
			"avg_armor": py_round_n(av_a, 1),
			"avg_mr": py_round_n(av_mr, 4),
			"scale": {"armor": sa, "mr": sm},
			"mods": mods,
		}
	var scale_report: Dictionary = {}
	for dc: String in scales:
		scale_report[dc] = {"armor_scale": scales[dc].armor, "mr_scale": scales[dc].mr}
	report["_scales"] = scale_report
	report["_mods_mini"] = report.get("mini", {}).get("mods", {})
	var res: Dictionary = {}
	for row: Dictionary in rows:
		var dc := str(row.boss_class)
		var sc: Dictionary = scales.get(dc, {"armor": 1.0, "mr": 1.0})
		var values := archetypes.resist_from_profile(
			str(row.get("profile", "balanced")),
			dc,
			archetypes.resist_base,
			mods_by_class.get(dc, {}),
			float(sc.armor),
			float(sc.mr)
		)
		res[str(row.boss_type)] = {
			"armor": py_round(float(values[0])),
			"magic_resist": py_round_n(float(values[1]), 3),
			"profile": row.get("profile", "balanced"),
			"boss_class": dc,
		}
	return [res, report]


func pool_mean_rescale(
	catalog: Dictionary, before: Dictionary, which := "dps", tol := 0.005
) -> float:
	if before.is_empty():
		return 1.0
	var ids: Array[String] = []
	for key: String in before:
		if catalog.has(key) and bool(catalog[key].get("is_boss_hero", false)):
			ids.append(key)
	if ids.is_empty():
		return 1.0
	var metric_key := "dps" if which == "dps" else "ehp"
	var current: Array[float] = []
	var wanted: Array[float] = []
	for key: String in ids:
		current.append(float(metrics(catalog[key])[metric_key]))
		wanted.append(float(before[key][metric_key]))
	var cur := mean(current)
	if cur == 0.0:
		cur = 1.0
	var want := mean(wanted)
	if want <= 0.0 or cur <= 0.0:
		return 1.0
	var g := _clamp(want / cur, [1.0 - pool_mean_tol_max, 1.0 + pool_mean_tol_max])
	if absf(g - 1.0) < tol:
		return 1.0
	for key: String in ids:
		var stats: Dictionary = catalog[key]
		if which == "dps":
			for field: String in [
				"damage",
				"skill_damage",
				"skill_q_damage",
				"skill_w_damage",
				"skill_e_damage",
				"skill_r_damage"
			]:
				if _truthy(stats.get(field)):
					stats[field] = maxi(0, py_round(float(stats[field]) * g))
		else:
			stats["hp"] = maxi(1, py_round(_num(stats, "hp", 1.0) * g))
		var bal: Dictionary = stats.get("__bal", {})
		if not bal.is_empty():
			var bal_key := "dmg" if which == "dps" else "hp"
			bal[bal_key] = py_round_n(float(bal[bal_key]) * g, 4)
			if which == "dps":
				bal["skill"] = py_round_n(float(bal.skill) * g, 4)
	return g


func final_fixpoint(
	catalog: Dictionary,
	school_target := 1.0,
	cell_band: Variant = null,
	passes := 40,
	damp := 0.85,
	tol := 0.002
) -> Dictionary:
	var ids: Array[String] = []
	for ht: String in catalog:
		if bool(catalog[ht].get("is_boss_hero", false)) and float(metrics(catalog[ht]).dps) > 0.0:
			ids.append(ht)
	if ids.size() < 20:
		return {"skipped": "hero terlalu sedikit"}
	var fac: Dictionary = {}
	for ht: String in ids:
		fac[ht] = 1.0
	var info: Dictionary = {}
	for pass_index in range(passes):
		var eff: Dictionary = {}
		for ht: String in ids:
			var stats: Dictionary = catalog[ht]
			var m := metrics(stats)
			var require_boss: Variant = stats.get("unlock_require_boss")
			var boss_key := str(require_boss) if _truthy(require_boss) else ht
			var resist := archetypes.get_boss_resistances(boss_key, _boss_class(stats))
			var school := str(archetypes.get_archetype(ht, stats).dmg_type)
			var mit := (
				archetypes.physical_mitigation(float(resist[0]))
				if school == "PHYSICAL"
				else 1.0 - float(resist[1])
			)
			var key := _boss_class(stats) + "|" + school
			if not eff.has(key):
				eff[key] = []
			eff[key].append(float(m.dps) * float(fac[ht]) * mit)
		var by_cls: Dictionary = {}
		for key: String in eff:
			var dc := key.get_slice("|", 0)
			if not by_cls.has(dc):
				by_cls[dc] = []
			by_cls[dc].append_array(eff[key])
		var f_sch: Dictionary = {}
		for key: String in eff:
			var cur := mean(eff[key])
			var dc := key.get_slice("|", 0)
			var tgt := mean(by_cls[dc]) * school_target if by_cls.has(dc) else cur
			if cur > 0.0 and tgt > 0.0:
				f_sch[key] = pow(tgt / cur, damp)
		var dps_values: Array[float] = []
		var ehp_values: Array[float] = []
		for ht: String in ids:
			var m := metrics(catalog[ht])
			dps_values.append(float(m.dps))
			ehp_values.append(float(m.ehp))
		var med_d := mean(dps_values)
		if med_d == 0.0:
			med_d = 1.0
		var med_e := mean(ehp_values)
		if med_e == 0.0:
			med_e = 1.0
		var cell: Dictionary = {}
		for ht: String in ids:
			var arch := archetypes.get_archetype(ht, catalog[ht])
			var m := metrics(catalog[ht])
			var pw := 0.8 * float(m.dps) * float(fac[ht]) / med_d + 0.2 * float(m.ehp) / med_e
			var style := str(arch.get("playstyle", "FIGHTER"))
			var key := str(arch.dmg_type) + "|" + style
			if not cell.has(key):
				cell[key] = []
			cell[key].append(pw)
		var allpw: Array[float] = []
		for key: String in cell:
			allpw.append_array(cell[key])
		var tgt_cell := mean(allpw) if not allpw.is_empty() else 1.0
		var f_cell: Dictionary = {}
		if cell_band != null:
			for key: String in cell:
				var cur := mean(cell[key])
				if cur > 0.0:
					f_cell[key] = _clamp(pow(tgt_cell / cur, damp), cell_band)
		var moved := 0.0
		for ht: String in ids:
			var stats: Dictionary = catalog[ht]
			var arch := archetypes.get_archetype(ht, stats)
			var school := str(arch.dmg_type)
			var style := str(arch.get("playstyle", "FIGHTER"))
			var g := float(f_sch.get(_boss_class(stats) + "|" + school, 1.0))
			g *= float(f_cell.get(school + "|" + style, 1.0))
			g = _clamp(g, [1.0 / final_corr_cap, final_corr_cap])
			fac[ht] = _clamp(float(fac[ht]) * g, [1.0 / final_corr_cap, final_corr_cap])
			moved = maxf(moved, absf(g - 1.0))
		info["passes_run"] = pass_index + 1
		info["last_move"] = py_round_n(moved, 4)
		if moved < tol:
			break
	for ht: String in ids:
		var g := float(fac[ht])
		if absf(g - 1.0) < 1e-4:
			continue
		var stats: Dictionary = catalog[ht]
		for field: String in [
			"damage",
			"skill_damage",
			"skill_q_damage",
			"skill_w_damage",
			"skill_e_damage",
			"skill_r_damage"
		]:
			if _truthy(stats.get(field)):
				stats[field] = maxi(0, py_round(float(stats[field]) * g))
		var bal: Dictionary = stats.get("__bal", {})
		if not bal.is_empty():
			bal["dmg"] = py_round_n(float(bal.dmg) * g, 4)
			bal["skill"] = py_round_n(float(bal.skill) * g, 4)
			bal["dbg"]["fix"] = py_round_n(g, 4)
		fac[ht] = g
	var factors: Array[float] = []
	for ht: String in fac:
		factors.append(float(fac[ht]))
	info["factor_min"] = py_round_n(factors.min(), 4)
	info["factor_max"] = py_round_n(factors.max(), 4)
	info["n"] = ids.size()
	return info


func apply_to_catalog(catalog: Dictionary) -> Dictionary:
	var source := catalog.duplicate()
	var baseline := pristine_boss_stats()
	for key: String in baseline:
		if source.has(key):
			source[key] = baseline[key]
	var table := resolve_catalog(source)
	var before: Dictionary = {}
	if pool_mean_anchor:
		for key: String in baseline:
			var m := metrics(baseline[key])
			if float(m.dps) > 0.0:
				before[key] = m
	for key: String in baseline:
		if table.has(key) and table[key] != null:
			table[key]["dbg"]["raw"] = {
				"hp": baseline[key].get("hp"),
				"damage": baseline[key].get("damage"),
				"skill_damage": baseline[key].get("skill_damage"),
				"attack_cooldown": baseline[key].get("attack_cooldown"),
				"skill_cooldown": baseline[key].get("skill_cooldown"),
			}
	last["table"] = table
	for ht: String in table:
		var mult: Dictionary = table[ht]
		if mult.is_empty() or not catalog.has(ht):
			continue
		var stats: Dictionary = catalog[ht]
		if not bool(stats.get("is_boss_hero", false)):
			continue
		var raw: Dictionary = source.get(ht, stats)
		stats["__bal"] = mult
		stats["hp"] = maxi(1, py_round(float(raw.get("hp", 1)) * float(mult.hp)))
		stats["damage"] = maxi(1, py_round(float(raw.get("damage", 1)) * float(mult.dmg)))
		stats["skill_damage"] = maxi(
			0, py_round(float(raw.get("skill_damage", 0)) * float(mult.skill))
		)
		for field: String in [
			"skill_q_damage", "skill_w_damage", "skill_e_damage", "skill_r_damage"
		]:
			if _truthy(raw.get(field)):
				stats[field] = maxi(0, py_round(float(raw[field]) * float(mult.skill)))
	last["pool_anchor"] = {}
	if pool_mean_anchor and not before.is_empty():
		var dps_values: Array[float] = []
		var ehp_values: Array[float] = []
		for key: String in before:
			dps_values.append(float(before[key].dps))
			ehp_values.append(float(before[key].ehp))
		last["pool_means"] = {
			"dps": py_round_n(mean(dps_values), 1),
			"ehp": py_round_n(mean(ehp_values), 1),
			"n": before.size()
		}
		var anchors := {
			"dps": pool_mean_rescale(catalog, before, "dps"),
			"ehp": pool_mean_rescale(catalog, before, "ehp"),
		}
		for key: String in anchors:
			if absf(float(anchors[key]) - 1.0) >= 0.005:
				last["pool_anchor"][key] = anchors[key]
	if final_fixpoint_enabled:
		last["fix"] = final_fixpoint(catalog)
	return catalog


static func py_round(value: float) -> int:
	var lower := floorf(value)
	if value - lower == 0.5:
		var low := int(lower)
		return low if low % 2 == 0 else low + 1
	return int(roundf(value))


static func py_round_n(value: float, digits: int) -> float:
	# Godot's decimal formatting matches Python round(x, n) for the binary
	# double cases in the oracle; scaling by 10^n first rounds exact ties wrong.
	return String.num(value, digits).to_float()


static func median(values: Array) -> float:
	if values.is_empty():
		return 0.0
	var sorted := values.duplicate()
	sorted.sort()
	var mid := sorted.size() / 2
	if sorted.size() % 2 == 1:
		return float(sorted[mid])
	return (float(sorted[mid - 1]) + float(sorted[mid])) / 2.0


static func mean(values: Array) -> float:
	if values.is_empty():
		return 0.0
	var total := 0.0
	for value: Variant in values:
		total += float(value)
	return total / float(values.size())


func _school_parity_passes(
	boss: Dictionary, met: Dictionary, raw: Dictionary, fin: Dictionary
) -> void:
	for _pass in range(8):
		var eff: Dictionary = {}
		for ht: String in boss:
			var m: Dictionary = met[ht]
			if float(m.dps) <= 0.0:
				continue
			var dps := (float(m.dmg) * float(fin[ht][1])) * 60.0 / float(m.cd)
			dps += (float(m.skill) * float(fin[ht][2])) * 60.0 / float(m.skcd)
			var school := str(raw[ht][3][4])
			var key := _boss_class(boss[ht]) + "|" + school
			if not eff.has(key):
				eff[key] = []
			eff[key].append(eff_dps(ht, boss[ht], m, dps))
		var by_cls: Dictionary = {}
		for key: String in eff:
			var dc := key.get_slice("|", 0)
			if not by_cls.has(dc):
				by_cls[dc] = []
			by_cls[dc].append_array(eff[key])
		var tgt: Dictionary = {}
		for dc: String in by_cls:
			if not by_cls[dc].is_empty():
				tgt[dc] = mean(by_cls[dc])
		if tgt.is_empty():
			break
		var moved := 0.0
		var f2: Dictionary = {}
		for key: String in eff:
			var cur := mean(eff[key])
			var t_dc := float(tgt.get(key.get_slice("|", 0), 0.0))
			if t_dc <= 0.0 or cur <= 0.0:
				f2[key] = 1.0
				continue
			var f := _clamp(t_dc / cur, [1.0 / school_parity_cap, school_parity_cap])
			f2[key] = f
			moved = maxf(moved, absf(f - 1.0))
		var wavg: Dictionary = {}
		for dc: String in by_cls:
			var total := 0
			var weighted := 0.0
			for key: String in f2:
				if key.get_slice("|", 0) == dc:
					var n: int = eff[key].size()
					total += n
					weighted += float(f2[key]) * float(n)
			wavg[dc] = weighted / float(total if total > 0 else 1)
		for ht: String in fin:
			var dc := _boss_class(boss[ht])
			var school := str(raw[ht][3][4])
			var g := float(f2.get(dc + "|" + school, 1.0)) / float(wavg.get(dc, 1.0))
			fin[ht][1] = float(fin[ht][1]) * g
			fin[ht][2] = float(fin[ht][2]) * g
		var parity: Dictionary = last.get("parity", {})
		var schools: Dictionary = {}
		for key: String in f2:
			schools[key] = py_round_n(float(f2[key]), 4)
		parity["schools"] = schools
		last["parity"] = parity
		if moved < 0.002:
			break


func _cell_power(
	ht: String,
	base: Dictionary,
	cell: Dictionary,
	factors: Dictionary,
	met: Dictionary,
	med_dps: float,
	med_ehp: float
) -> float:
	var b: Array = base[ht]
	var g := float(factors[cell[ht]])
	return final_power(met[ht], float(b[0]), float(b[1]) * g, float(b[2]) * g, med_dps, med_ehp)


func _cal_zero_mean(rows: Array) -> Dictionary:
	var n := rows.size() if not rows.is_empty() else 1
	var sums := [0.0, 0.0]
	for row: Dictionary in rows:
		var delta: Array = archetypes.resist_profile_mods.get(
			str(row.get("profile", "balanced")), [0.0, 0.0]
		)
		sums[0] = float(sums[0]) + float(delta[0])
		sums[1] = float(sums[1]) + float(delta[1])
	var result: Dictionary = {}
	for profile: String in archetypes.resist_profile_mods:
		var value: Array = archetypes.resist_profile_mods[profile]
		result[profile] = [
			float(value[0]) - float(sums[0]) / float(n), float(value[1]) - float(sums[1]) / float(n)
		]
	return result


func _cal_stats_for(
	dc: String, mods: Dictionary, sa: float, sm: float, by_class: Dictionary
) -> Array:
	var p_sum := 0.0
	var m_sum := 0.0
	var p_n := 0
	var m_n := 0
	var a_sum := 0.0
	var mr_sum := 0.0
	var rows: Array = by_class.get(dc, [])
	for row: Dictionary in rows:
		var values := archetypes.resist_from_profile(
			str(row.get("profile", "balanced")), dc, archetypes.resist_base, mods, sa, sm
		)
		a_sum += float(values[0])
		mr_sum += float(values[1])
		var dps := _num(row, "dps", 0.0)
		if str(row.get("dmg_type", "")) == "PHYSICAL":
			p_sum += dps * archetypes.physical_mitigation(float(values[0]))
			p_n += 1
		else:
			m_sum += dps * (1.0 - float(values[1]))
			m_n += 1
	var n := rows.size() if not rows.is_empty() else 1
	var ratio := 1.0
	if p_n > 0 and m_n > 0:
		ratio = (m_sum / float(maxi(m_n, 1))) / maxf(p_sum / float(maxi(p_n, 1)), 1e-9)
	return [ratio, a_sum / float(n), mr_sum / float(n)]


func _cal_solve(
	dc: String,
	mods: Dictionary,
	lock: bool,
	by_class: Dictionary,
	target: float,
	scale_hi: float,
	n_step: int
) -> Array:
	var baseline: Array = archetypes.resist_base[dc]
	var best := [9e9, 1.0, 1.0]
	for i in range(n_step):
		for j in range(n_step):
			var sa := 1.0 + (scale_hi - 1.0) * float(i) / float(maxi(n_step - 1, 1))
			var sm := 1.0 + (scale_hi - 1.0) * float(j) / float(maxi(n_step - 1, 1))
			var stats := _cal_stats_for(dc, mods, sa, sm, by_class)
			var penalty := 0.0
			if lock:
				penalty += maxf(0.0, absf(float(stats[1]) - float(baseline[0])) - 0.6) * 0.5
				penalty += maxf(0.0, absf(float(stats[2]) - float(baseline[1])) - 0.006) * 120.0
			var score := absf(float(stats[0]) - target) + penalty
			if score < float(best[0]):
				best = [score, sa, sm]
	var result := _cal_stats_for(dc, mods, float(best[1]), float(best[2]), by_class)
	return [best[1], best[2], result]


func _values(table: Dictionary, key: String) -> Array:
	var result: Array[float] = []
	for item: String in table:
		result.append(float(table[item][key]))
	return result


func _boss_class(stats: Dictionary) -> String:
	var value: Variant = stats.get("boss_class", "mini")
	return str(value) if _truthy(value) else "mini"


func _clamp(value: float, lo_hi: Array) -> float:
	return maxf(float(lo_hi[0]), minf(float(lo_hi[1]), value))


func _num(stats: Dictionary, key: String, fallback: float) -> float:
	var value: Variant = stats.get(key, fallback)
	if not _truthy(value):
		return fallback
	return float(value)


static func _truthy(value: Variant) -> bool:
	if value == null:
		return false
	if value is bool:
		return value
	if value is int or value is float:
		return float(value) != 0.0
	if value is String or value is Array or value is Dictionary:
		return not value.is_empty()
	return true
