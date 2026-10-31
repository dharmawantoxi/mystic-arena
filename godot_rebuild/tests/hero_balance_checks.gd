extends RefCounted
## Layer 9cj: `hero_balance.py` (935 lines) — the whole balance calibration pass.
##
## The source module reads the hero catalog, computes one multiplier triple per hero
## and writes the rounded stats back in place. This layer ports the pipeline (plus the
## `hero_archetypes.py` tables and resistance arithmetic it depends on) and replays the
## source numbers:
##
## * the inventory (13 sections, 20 functions, 37 assigns, two imports) and the 59
##   classified symbols — 35 data constants, 20 ported functions, one folded import and
##   the three documented deviations (`pristine_boss_stats`, `LAST`, `_DBG`);
## * the archetype tables (222 rows: MAGIC 120 / PHYSICAL 102, FIGHTER 137 / TANK 64 /
##   CARRY 21) with the manual `dmg_type` override and the `derived` fallback;
## * the boss resistance arithmetic (216 baked rows, the 80..`0.45` clamps, the profile
##   deltas scaled per class) and the `.tres` proof: the source post-balance
##   hp/damage/skill of all 216 boss heroes equals `data/heroes/*.tres`, and the starter
##   `.tres` numbers equal `starter_catchup_stats(..., unlocks 0, level 1)`;
## * the executable pipeline on the real catalog: `pool_for` medians, `metrics` /
##   `hero_target` / `stat_multipliers` for one hero per archetype cell, the starter
##   catch-up grid, `resolve_catalog` (222 multiplier rows), `apply_to_catalog` (216
##   final stat rows + the pool anchor + the audit-formula fixpoint) and the offline
##   `calibrate_boss_resistances` replay.
##
## Sync: python3 godot_rebuild/tests/hero_balance_source_oracle.py --write

const Archetypes = preload("res://scripts/data/hero_archetypes.gd")
const HeroBalance = preload("res://scripts/data/hero_balance.gd")
const FIXTURE := "res://tests/fixtures/hero_balance_source.json"

const TOTALS := {
	"lines": 935,
	"sections": 13,
	"classes": 0,
	"functions": 20,
	"assigns": 37,
	"imports": 2,
}
const SECTION_NAMES := [
	"header",
	"switches",
	"rebudget",
	"guards",
	"school_mod_constants",
	"starter_constants",
	"metrics",
	"targets",
	"parity",
	"resolve",
	"calibrate",
	"anchors",
	"apply",
]
const KINDS := {"data": 35, "deviation": 3, "folded": 1, "ported": 20}
const SYMBOL_COUNT := 59
const TARGET_SOURCE_ONLY := ["dead", "deviation", "meta"]
const DEVIATION_SYMBOLS := [
	"assign:_DBG",
	"assign:LAST",
	"func:pristine_boss_stats",
]
const SWITCHES := {
	"ENABLE_REBUDGET": true,
	"ENABLE_SCHOOL_MOD": false,
	"ENABLE_STARTER_CATCHUP": true,
	"SCHOOL_PARITY": true,
	"CELL_PARITY": true,
	"POOL_MEAN_ANCHOR": true,
	"FINAL_FIXPOINT": true,
}
const POOL_TOL := 1e-6


static func _json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}


static func _target_text(path: String) -> String:
	if not path.begins_with("godot_rebuild/"):
		return ""
	var local: String = "res://" + path.trim_prefix("godot_rebuild/")
	if not FileAccess.file_exists(local):
		return ""
	return FileAccess.get_file_as_string(local)


static func _close(actual: float, expected: float, tol: float = POOL_TOL) -> bool:
	return absf(actual - expected) <= tol * maxf(1.0, absf(expected))


static func _row(rows: Dictionary, key: String) -> Dictionary:
	var value: Variant = rows.get(key, {})
	return value if value is Dictionary else {}


func run(check: Callable) -> void:
	var data: Dictionary = _json(FIXTURE)
	check.call(not data.is_empty(), "the hero_balance fixture parses")
	if data.is_empty():
		return
	_check_inventory(check, data)
	_check_classification(check, data)
	_check_archetypes(check, data)
	_check_starters(check, data)
	_check_pool(check, data)
	_check_helpers(check, data)
	_check_resolve(check, data)
	_check_apply(check, data)
	_check_calibrate(check, data)


## The file really is the balance pass this layer claims: 13 sections, no class.
func _check_inventory(check: Callable, data: Dictionary) -> void:
	var file: Dictionary = data["file"]
	for key in TOTALS:
		check.call(
			int(file.get(key, -1)) == int(TOTALS[key]),
			"hero_balance %s is %d (got %s)" % [key, int(TOTALS[key]), str(file.get(key))]
		)
	check.call(
		String(file.get("file", "")) == "hero_balance.py",
		"the oracle reads hero_balance.py"
	)
	var sections: Array = data["sections"]
	check.call(sections.size() == SECTION_NAMES.size(), "the balance pass keeps 13 sections")
	var names: Array = []
	var cursor := 1
	for raw in sections:
		var section: Dictionary = raw
		names.append(String(section["name"]))
		check.call(
			int(section["start"]) == cursor,
			"section %s starts where the previous one ends" % section["name"]
		)
		check.call(
			int(section["lines"]) == int(section["end"]) - int(section["start"]) + 1,
			"section %s spans its own range" % section["name"]
		)
		cursor = int(section["end"]) + 1
	check.call(names == SECTION_NAMES, "the sections keep the source order")
	check.call(cursor - 1 == 935, "the sections cover the whole file")


## Every one of the 59 symbols carries a kind and a live target + token.
func _check_classification(check: Callable, data: Dictionary) -> void:
	var symbols: Dictionary = data["symbols"]
	check.call(int(symbols["count"]) == SYMBOL_COUNT, "59 symbols are classified")
	check.call(
		int(symbols["count"]) == (data["classification"] as Dictionary).size(),
		"every symbol has one classification row"
	)
	var kinds: Dictionary = symbols["kinds"]
	for kind in KINDS:
		check.call(
			int(kinds.get(kind, -1)) == int(KINDS[kind]),
			"kind %s counts %d (got %s)" % [kind, int(KINDS[kind]), str(kinds.get(kind))]
		)
	var rows: Dictionary = data["classification"]
	var broken: Array = []
	var untargeted: Array = []
	for symbol in rows:
		var row: Dictionary = rows[symbol]
		var target := String(row["target"])
		var token := String(row["token"])
		if target.is_empty() or token.is_empty():
			if not TARGET_SOURCE_ONLY.has(String(row["kind"])):
				untargeted.append(symbol)
			continue
		if not _target_text(target).contains(token):
			broken.append("%s -> %s" % [symbol, target])
	check.call(
		broken.is_empty(),
		"every classification token is present in its target (%s)" % str(broken.slice(0, 5))
	)
	check.call(
		untargeted.is_empty(),
		"only dead/deviation/meta rows may skip a Godot target (%s)" % str(untargeted)
	)
	var deviations: Array = []
	for symbol in rows:
		if String((rows[symbol] as Dictionary)["kind"]) == "deviation":
			deviations.append(symbol)
	deviations.sort()
	check.call(
		deviations == DEVIATION_SYMBOLS,
		"the three deviations stay named, not quietly dropped (%s)" % str(deviations)
	)
	check.call(
		(data["duplicates"] as Dictionary).is_empty(),
		"hero_balance.py stays free of duplicated symbols"
	)


## `hero_archetypes.py`: the two tables plus every resistance helper.
func _check_archetypes(check: Callable, data: Dictionary) -> void:
	var arch: Dictionary = data["archetypes"]
	check.call(int(arch["count"]) == 222, "222 heroes carry an archetype row")
	check.call(
		Archetypes.ARCHETYPES.size() == int(arch["count"]),
		"the native archetype table has the same 222 rows"
	)
	var row_errors: Array = []
	var rows: Dictionary = arch["rows"]
	for hero_type in rows:
		var expected: Dictionary = rows[hero_type]
		var actual := Archetypes.get_archetype(String(hero_type))
		if String(actual["dmg_type"]) != String(expected["dmg_type"]) \
				or String(actual["playstyle"]) != String(expected["playstyle"]) \
				or String(actual["tier"]) != String(expected["tier"]) \
				or int(actual["power"]) != int(expected["power"]):
			row_errors.append(hero_type)
	check.call(
		row_errors.is_empty(),
		"every archetype row matches the source table (%s)" % str(row_errors.slice(0, 5))
	)
	var kinds: Dictionary = arch["kinds"]
	var schools := {"MAGIC": 0, "PHYSICAL": 0}
	var styles := {"CARRY": 0, "FIGHTER": 0, "TANK": 0}
	for hero_type2 in Archetypes.ARCHETYPES:
		var row2: Dictionary = Archetypes.ARCHETYPES[hero_type2]
		schools[String(row2["dmg_type"])] += 1
		styles[String(row2["playstyle"])] += 1
	check.call(
		schools == kinds["dmg_type"] and styles == kinds["playstyle"],
		"the school/style split stays 120/102 and 137/64/21"
	)

	var resist: Dictionary = data["boss_resist"]
	check.call(int(resist["count"]) == 216, "216 bosses carry a resistance row")
	check.call(
		Archetypes.BOSS_RESISTANCES.size() == int(resist["count"]),
		"the native resistance table has the same 216 rows"
	)
	var boss_errors: Array = []
	var resist_rows: Dictionary = resist["rows"]
	for boss_type in resist_rows:
		var expected2: Dictionary = resist_rows[boss_type]
		var actual2 := Archetypes.get_boss_resistances(String(boss_type))
		if int(actual2[0]) != int(expected2["armor"]) \
				or not _close(float(actual2[1]), float(expected2["magic_resist"]), 1e-9):
			boss_errors.append(boss_type)
	check.call(
		boss_errors.is_empty(),
		"every boss resistance row matches the source (%s)" % str(boss_errors.slice(0, 5))
	)
	check.call(
		(resist["data_mismatch"] as Array).is_empty(),
		"the baked boss_stats.json armor/MR still equals hero_archetypes"
	)
	check.call(
		(resist["scale_mismatch"] as Array).is_empty(),
		"BOSS_RESIST_SCALE reproduces every published resistance row"
	)

	# The published rows are the per-class write step of `calibrate_boss_resistances`:
	# zero-meaned profile modifiers, the published scale, mr published to 3 decimals.
	var zero_mods: Dictionary = resist["zero_mean_mods"]
	var scale_rows: Dictionary = resist["scale"]
	var scale_errors: Array = []
	for boss_type2 in resist_rows:
		var row3: Dictionary = resist_rows[boss_type2]
		var boss_class := String(row3["boss_class"])
		var scale: Dictionary = scale_rows[boss_class]
		var pair := Archetypes.resist_from_profile(
			String(row3["profile"]), boss_class, {},
			zero_mods[boss_class], float(scale["armor"]), float(scale["mr"])
		)
		if int(pair[0]) != int(row3["armor"]) \
				or not _close(float(pair[1]), float(row3["magic_resist"]), 5e-4):
			scale_errors.append(boss_type2)
	check.call(
		scale_errors.is_empty(),
		"the scale + zero-meaned modifiers reproduce every resistance row (%s)"
		% str(scale_errors.slice(0, 4))
	)

	var interactions: Dictionary = resist["profile_pairs"]
	var profiles: Dictionary = resist["profile_mods"]
	check.call(
		Archetypes.BOSS_RESIST_PROFILE_MODS.size() == profiles.size(),
		"the profile modifier table keeps five themes"
	)
	for key in interactions:
		var wanted: Array = interactions[key]
		var parts := String(key).split("|")
		var got: Array
		if String(key) == "unknown_profile":
			got = Archetypes.resist_from_profile("nope", "mini")
		elif String(key) == "unknown_class":
			got = Archetypes.resist_from_profile("balanced", "nope")
		else:
			got = Archetypes.resist_from_profile(parts[1], parts[0])
		check.call(
			int(got[0]) == int(wanted[0]) and _close(float(got[1]), float(wanted[1]), 1e-9),
			"resist_from_profile(%s) keeps the source pair" % key
		)
	var fallbacks: Dictionary = resist["fallback"]
	for key2 in fallbacks:
		var expected3: Array = fallbacks[key2]
		var parts2 := String(key2).split("|")
		var got2 := Archetypes.get_boss_resistances(
			parts2[0], parts2[1] if parts2.size() > 1 else "mini"
		)
		check.call(
			int(got2[0]) == int(expected3[0])
			and _close(float(got2[1]), float(expected3[1]), 1e-9),
			"get_boss_resistances(%s) falls back like the source" % key2
		)
	var mitigation: Dictionary = resist["mitigation"]
	for armor_key in mitigation:
		check.call(
			_close(Archetypes.physical_mitigation(float(armor_key)),
				float(mitigation[armor_key]), 1e-6),
			"physical_mitigation(%s) keeps the armor curve" % armor_key
		)
	check.call(
		_close(Archetypes.ARMOR_FACTOR, float(resist["armor_factor"]), 1e-12)
		and int(Archetypes.ARMOR_MAX) == int(resist["armor_max"])
		and _close(Archetypes.MR_MAX, float(resist["mr_max"]), 1e-12),
		"the armor/resist caps stay 0.06 / 40 / 0.45"
	)

	var overrides: Dictionary = resist["overrides"]
	var forced_magic: Dictionary = overrides["forced_magic"]
	check.call(
		String(forced_magic["dmg_type"]) == "MAGIC"
		and String(Archetypes.get_archetype("gornak", {"dmg_type": "magic"})["dmg_type"])
		== "MAGIC",
		"a manual dmg_type override wins over the table"
	)
	check.call(
		String(Archetypes.get_archetype("gornak", {"dmg_type": "fire"})["dmg_type"])
		== "PHYSICAL",
		"an unknown override falls back to PHYSICAL"
	)
	var derived: Dictionary = overrides["derived"]
	var derived_got := Archetypes.get_archetype("nobody")
	check.call(
		bool(derived_got.get("derived", false)) and int(derived_got["power"]) == 0
		and String(derived_got["tier"]).is_empty()
		and String(derived_got["dmg_type"]) == String(derived["dmg_type"]),
		"an unanalysed hero is a derived physical fighter"
	)
	check.call(
		String(overrides["school_of"]) == Archetypes.school_of("gornak")
		and String(overrides["school_of_override"])
		== Archetypes.school_of("gornak", {"dmg_type": "PHYSICAL"}),
		"school_of returns the lowercase pipeline form"
	)


## Starter catch-up: inverse to the roster, decaying with level, split 1.25 / 0.85.
func _check_starters(check: Callable, data: Dictionary) -> void:
	var starter: Dictionary = data["starter"]
	var grid: Dictionary = starter["catchup"]
	var errors: Array = []
	for hero_type in grid:
		var rows: Dictionary = grid[hero_type]
		for key in rows:
			var parts := String(key).split("|")
			var got := HeroBalance.starter_catchup(
				String(hero_type), int(parts[0]), int(parts[1])
			)
			var wanted: Array = rows[key]
			if not _close(float(got[0]), float(wanted[0]), 1e-9) \
					or not _close(float(got[1]), float(wanted[1]), 1e-9):
				errors.append("%s|%s" % [hero_type, key])
	check.call(
		errors.is_empty(),
		"the starter catch-up grid matches the source (%s)" % str(errors.slice(0, 5))
	)
	var stats_cases: Dictionary = starter["stats"]
	var stat_errors: Array = []
	var base := {"hp": 520, "damage": 27}
	for key2 in stats_cases:
		var parts2 := String(key2).split("|")
		var wanted2: Array = stats_cases[key2]
		var got2 := HeroBalance.starter_catchup_stats(
			parts2[0], base, int(parts2[1]), int(parts2[2])
		)
		if int(got2[0]) != int(wanted2[0]) or int(got2[1]) != int(wanted2[1]):
			stat_errors.append(key2)
	check.call(
		stat_errors.is_empty(),
		"starter_catchup_stats rounds like the source (%s)" % str(stat_errors)
	)
	var unlocked: Dictionary = starter["unlock_counts"]
	check.call(
		HeroBalance.boss_unlocks_for_purchases([]) == int(unlocked["[]"])
		and HeroBalance.boss_unlocks_for_purchases(HeroBalance.STARTER_HEROES)
		== int(unlocked["starters_only"])
		and HeroBalance.boss_unlocks_for_purchases(
			["kaizen", "gornak", "abaddon", "vex"]
		) == int(unlocked["mixed"]),
		"boss_unlocks_for_purchases ignores the starters"
	)
	var factors: Dictionary = starter["level_factor"]
	for level in factors:
		check.call(
			_close(HeroBalance.starter_level_factor(int(level)), float(factors[level]), 1e-9),
			"starter_level_factor(%s) keeps its decay" % level
		)
	check.call(
		HeroBalance.school_mod("physical") == 1.0
		and not HeroBalance.ENABLE_SCHOOL_MOD,
		"the school modifier stays off while parity is on"
	)


## The pool statistics `resolve_catalog` derives from the boss-hero catalog.
func _check_pool(check: Callable, data: Dictionary) -> void:
	var catalog: Dictionary = data["catalog_src"]
	var pool := HeroBalance.pool_for(catalog)
	var expected: Dictionary = data["pool"]
	check.call(
		_close(float(pool["med_ratio"]), float(expected["med_ratio"]))
		and _close(float(pool["med_budget"]), float(expected["med_budget"]))
		and _close(float(pool["p50_budget"]), float(expected["p50_budget"]))
		and _close(float(pool["med_dps"]), float(expected["med_dps"]))
		and _close(float(pool["med_ehp"]), float(expected["med_ehp"]))
		and _close(float(pool["meta_med"]), float(expected["meta_med"])),
		"the pool medians stay 5.14 / 462.37 / 486.62 / 2350"
	)
	var buckets: Dictionary = expected["eff_by_bucket"]
	var native_buckets: Dictionary = pool["eff_by_bucket"]
	check.call(
		native_buckets.size() == buckets.size(),
		"the price buckets keep their count (%d)" % native_buckets.size()
	)
	var bucket_errors: Array = []
	for key in buckets:
		if not _close(float(native_buckets.get(int(key), 0.0)), float(buckets[key])):
			bucket_errors.append(key)
	check.call(
		bucket_errors.is_empty(),
		"the per-bucket cost efficiency medians match (%s)" % str(bucket_errors)
	)
	for key2 in SWITCHES:
		var native_value: bool = (
			HeroBalance.ENABLE_REBUDGET if key2 == "ENABLE_REBUDGET" else
			HeroBalance.ENABLE_SCHOOL_MOD if key2 == "ENABLE_SCHOOL_MOD" else
			HeroBalance.ENABLE_STARTER_CATCHUP if key2 == "ENABLE_STARTER_CATCHUP" else
			HeroBalance.SCHOOL_PARITY if key2 == "SCHOOL_PARITY" else
			HeroBalance.CELL_PARITY if key2 == "CELL_PARITY" else
			HeroBalance.POOL_MEAN_ANCHOR if key2 == "POOL_MEAN_ANCHOR" else
			HeroBalance.FINAL_FIXPOINT
		)
		check.call(
			native_value == bool(data["switches"][key2]),
			"switch %s keeps the source value (%s)" % [key2, str(native_value)]
		)


## `metrics` / `hero_target` / `stat_multipliers` on one hero per archetype cell.
func _check_helpers(check: Callable, data: Dictionary) -> void:
	var catalog: Dictionary = data["catalog_src"]
	var pool := HeroBalance.pool_for(catalog)
	var helpers: Dictionary = data["helpers"]
	var metric_errors: Array = []
	var target_errors: Array = []
	var mult_errors: Array = []
	for hero_type in helpers:
		var expected: Dictionary = helpers[hero_type]
		var stats: Dictionary = (catalog[hero_type] as Dictionary).duplicate(true)
		stats["__hero_type__"] = hero_type
		var metrics := HeroBalance.metrics(stats)
		var wanted_metrics: Dictionary = expected["metrics"]
		for key in wanted_metrics:
			if not _close(float(metrics[key]), float(wanted_metrics[key]), 1e-9):
				metric_errors.append("%s.%s" % [hero_type, key])
		var multipliers := HeroBalance.stat_multipliers(stats, pool)
		var wanted_mult: Array = expected["multipliers"]
		for index in range(3):
			if not _close(float(multipliers[index]), float(wanted_mult[index]), 1e-9):
				mult_errors.append("%s[%d]" % [hero_type, index])
		if expected["target"] == null:
			if HeroBalance.hero_target(stats, pool) == null:
				target_errors.append("%s null target" % hero_type)
			continue
		var target: Variant = HeroBalance.hero_target(stats, pool)
		if target == null:
			target_errors.append("%s null" % hero_type)
			continue
		var got: Array = target
		var wanted: Dictionary = expected["target"]
		if not _close(float(got[1]), float(wanted["ratio"])) \
				or not _close(float(got[2]), float(wanted["budget"])) \
				or not _close(float(got[3]), float(wanted["price_corr"]), 1e-6) \
				or String(got[4]) != String(wanted["school"]) \
				or String(got[5]) != String(wanted["style"]):
			target_errors.append(hero_type)
	check.call(
		metric_errors.is_empty(),
		"metrics matches DPS/EHP/budget per archetype cell (%s)" % str(metric_errors)
	)
	check.call(
		mult_errors.is_empty(),
		"stat_multipliers keeps the source clamps (%s)" % str(mult_errors)
	)
	check.call(
		target_errors.is_empty(),
		"hero_target keeps the style/school targets (%s)" % str(target_errors)
	)
	var gornak_metrics := HeroBalance.metrics((catalog["gornak"] as Dictionary))
	var expected_power: float = 0.8 * float(gornak_metrics["dps"]) / float(pool["med_dps"]) \
		+ 0.2 * float(gornak_metrics["ehp"]) / float(pool["med_ehp"])
	check.call(
		_close(HeroBalance.final_power(
			gornak_metrics, 1.0, 1.0, 1.0,
			float(pool["med_dps"]), float(pool["med_ehp"])
		), expected_power, 1e-9),
		"final_power is 0.8 DPS + 0.2 EHP against the pool medians"
	)


## `resolve_catalog` on the real catalog: all 222 multiplier rows.
func _check_resolve(check: Callable, data: Dictionary) -> void:
	var catalog: Dictionary = data["catalog_src"]
	var table := HeroBalance.resolve_catalog(catalog, 0)
	var expected: Dictionary = data["resolve"]
	check.call(
		table.size() == expected.size(),
		"resolve_catalog returns one row per hero (%d)" % table.size()
	)
	var errors: Array = []
	var dbg_errors: Array = []
	for hero_type in expected:
		if not table.has(hero_type):
			errors.append("%s missing" % hero_type)
			continue
		var wanted: Dictionary = expected[hero_type]
		if wanted == null:
			continue
		var got: Dictionary = table[hero_type]
		if not _close(float(got["hp"]), float(wanted["hp"])) \
				or not _close(float(got["dmg"]), float(wanted["dmg"])) \
				or not _close(float(got["skill"]), float(wanted["skill"])):
			errors.append(hero_type)
		var got_dbg: Dictionary = got["dbg"]
		var wanted_dbg: Dictionary = wanted["dbg"]
		for key in wanted_dbg:
			var want: Variant = wanted_dbg[key]
			var have: Variant = got_dbg.get(key)
			if want == null:
				if have != null:
					dbg_errors.append("%s.%s" % [hero_type, key])
				continue
			if want is float or want is int:
				if not _close(float(have), float(want), 1e-6):
					dbg_errors.append("%s.%s" % [hero_type, key])
			elif String(have) != String(want):
				dbg_errors.append("%s.%s" % [hero_type, key])
	check.call(
		errors.is_empty(),
		"every multiplier triple matches the source (%s)" % str(errors.slice(0, 5))
	)
	check.call(
		dbg_errors.is_empty(),
		"the dbg ratios/playstyle/school match too (%s)" % str(dbg_errors.slice(0, 5))
	)
	var gornak: Dictionary = table["gornak"]
	check.call(
		_close(float(gornak["hp"]), 1.2731, 1e-9)
		and _close(float(gornak["dmg"]), 1.1409, 1e-9)
		and _close(float(gornak["skill"]), 1.1409, 1e-9),
		"gornak keeps the source triple 1.2731 / 1.1409 / 1.1409"
	)
	check.call(
		_close(float(table["kaizen"]["hp"]), 1.4, 1e-9)
		and _close(float(table["kaizen"]["dmg"]), 1.272, 1e-9)
		and _close(float(table["kaizen"]["skill"]), 1.0, 1e-9),
		"a starter only gets its catch-up triple 1.4 / 1.272 / 1.0"
	)
	var parity: Dictionary = HeroBalance.last_result["parity"]
	var wanted_parity: Dictionary = data["apply"]["parity"]
	check.call(
		_close(float(parity["pool_target"]), float(wanted_parity["pool_target"]),
			1e-6),
		"the archetype-cell parity target stays %.3f" % float(wanted_parity["pool_target"])
	)
	var cell_errors: Array = []
	var cells: Dictionary = wanted_parity["cells"]
	for key2 in cells:
		if not _close(float((parity["cells"] as Dictionary).get(key2, 0.0)),
				float(cells[key2]), 1e-6):
			cell_errors.append(key2)
	check.call(
		cell_errors.is_empty(),
		"the six cell factors match (%s)" % str(cell_errors)
	)


## `apply_to_catalog`: 216 final stat rows, the pool anchor and the fixpoint.
func _check_apply(check: Callable, data: Dictionary) -> void:
	var catalog: Dictionary = (data["catalog_src"] as Dictionary).duplicate(true)
	HeroBalance.apply_to_catalog(catalog, data["pristine"])
	var expected: Dictionary = data["apply"]
	var stats_rows: Dictionary = expected["stats"]
	var errors: Array = []
	for hero_type in stats_rows:
		var wanted: Dictionary = stats_rows[hero_type]
		var got: Dictionary = catalog[hero_type]
		if int(got["hp"]) != int(wanted["hp"]) \
				or int(got["damage"]) != int(wanted["damage"]) \
				or int(got["skill_damage"]) != int(wanted["skill_damage"]):
			errors.append("%s %d/%d/%d vs %d/%d/%d" % [
				hero_type, int(got["hp"]), int(got["damage"]),
				int(got["skill_damage"]), int(wanted["hp"]), int(wanted["damage"]),
				int(wanted["skill_damage"]),
			])
	check.call(
		errors.is_empty(),
		"all 216 final stat rows match the source (%s)" % str(errors.slice(0, 4))
	)
	var wanted_means: Dictionary = expected["pool_means"]
	var means: Dictionary = HeroBalance.last_result["pool_means"]
	check.call(
		_close(float(means["dps"]), float(wanted_means["dps"]), 1e-6)
		and _close(float(means["ehp"]), float(wanted_means["ehp"]), 1e-6)
		and int(means["n"]) == int(wanted_means["n"]),
		"the pre-balance pool means stay 486.1 / 2495.4 over 216 heroes"
	)
	var wanted_anchor: Dictionary = expected["pool_anchor"]
	var anchor: Dictionary = HeroBalance.last_result["pool_anchor"]
	check.call(
		anchor.size() == wanted_anchor.size()
		and _close(float(anchor["dps"]), float(wanted_anchor["dps"]), 1e-9)
		and _close(float(anchor["ehp"]), float(wanted_anchor["ehp"]), 1e-9),
		"the pool anchor keeps 1.0937 / 1.0893"
	)
	var fix: Dictionary = HeroBalance.last_result["fix"]
	var wanted_fix: Dictionary = expected["fix"]
	check.call(
		int(fix["n"]) == int(wanted_fix["n"])
		and int(fix["passes_run"]) == int(wanted_fix["passes_run"])
		and _close(float(fix["factor_min"]), float(wanted_fix["factor_min"]), 1e-6)
		and _close(float(fix["factor_max"]), float(wanted_fix["factor_max"]), 1e-6),
		"the fixpoint reports the source pass count and factor range"
	)
	check.call(
		(expected["tres_mismatch"] as Array).is_empty(),
		"the source post-balance stats equal all 216 data/heroes/*.tres files"
	)
	var starter_tres: Dictionary = expected["starter_tres"]
	var starter_errors: Array = []
	for hero_type2 in starter_tres:
		var row: Dictionary = starter_tres[hero_type2]
		if (row["tres"] as Array) != (row["catchup"] as Array):
			starter_errors.append(hero_type2)
	check.call(
		starter_errors.is_empty() and (expected["starter_gap"] as Array).is_empty(),
		"each starter .tres equals starter_catchup_stats at unlocks 0 / level 1"
	)
	var kaizen: Dictionary = catalog["kaizen"]
	check.call(
		int(kaizen["hp"]) == int((data["catalog_src"] as Dictionary)["kaizen"]["hp"])
		and int(kaizen["damage"])
		== int((data["catalog_src"] as Dictionary)["kaizen"]["damage"]),
		"starters are left untouched by apply_to_catalog"
	)
	HeroBalance.last_result["table"] = {}
	HeroBalance.last_result["pool"] = {}
	HeroBalance.last_result["parity"] = {}


## The offline calibration: the same two scales from the same rows.
func _check_calibrate(check: Callable, data: Dictionary) -> void:
	var calibrate: Dictionary = data["calibrate"]
	var rows: Array = calibrate["rows"]
	var result := HeroBalance.calibrate_boss_resistances(
		rows, 0.0, 0.6, 1.8, int(calibrate["n_step"])
	)
	var table: Dictionary = result[0]
	var report: Dictionary = result[1]
	var expected: Dictionary = calibrate["table"]
	var errors: Array = []
	for boss_type in expected:
		var wanted: Dictionary = expected[boss_type]
		var got: Dictionary = table.get(boss_type, {})
		if int(got.get("armor", -1)) != int(wanted["armor"]) \
				or not _close(float(got.get("magic_resist", -1.0)),
					float(wanted["magic_resist"]), 1e-9):
			errors.append(boss_type)
	check.call(
		table.size() == expected.size() and errors.is_empty(),
		"calibrate_boss_resistances reproduces the 216 calibrated rows (%s)"
		% str(errors.slice(0, 4))
	)
	var scales: Dictionary = calibrate["scales"]
	var wanted_mini: Dictionary = scales["mini"]
	var wanted_true: Dictionary = scales["true"]
	var native_mini: Dictionary = (report["_scales"] as Dictionary)["mini"]
	var native_true: Dictionary = (report["_scales"] as Dictionary)["true"]
	check.call(
		_close(float(native_mini["armor_scale"]), float(wanted_mini["armor_scale"]), 1e-9)
		and _close(float(native_mini["mr_scale"]), float(wanted_mini["mr_scale"]), 1e-9)
		and _close(float(native_true["armor_scale"]),
			float(wanted_true["armor_scale"]), 1e-9)
		and _close(float(native_true["mr_scale"]), float(wanted_true["mr_scale"]), 1e-9),
		"the calibration grid returns the source armor/mr scales"
	)
	check.call(
		(report["_mods_mini"] as Dictionary).size() == Archetypes.BOSS_RESIST_PROFILE_MODS.size(),
		"the calibration keeps one modifier per boss theme"
	)
