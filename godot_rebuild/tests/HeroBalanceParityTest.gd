extends RefCounted

## Python-oracle parity for hero_balance.py, kept out of run_all.gd so the
## runner stays under the project lint file-length cap.


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/hero_balance_parity.json", FileAccess.READ)
	runner.check(file != null, "balance Python oracle fixture exists")
	if file == null:
		return
	var oracle: Dictionary = JSON.parse_string(file.get_as_text())
	var data := CoreData.new()
	var balance := data.balance
	runner.check(balance.valid(), "native hero balance contract loads")
	runner.check(balance.pristine.size() == 216, "balance contract has 216 pristine bosses")
	runner.check(balance.starter_heroes.size() == 6, "balance contract has six starters")
	_helpers(runner, balance, oracle.helpers)
	_metrics(runner, balance, oracle)
	_catchup(runner, balance, oracle.catchup)
	var raw: Dictionary = oracle.raw_catalog.duplicate(true)
	var resolved := balance.resolve_catalog(raw, 0, 1)
	_table(runner, resolved, oracle.resolve_table, "resolve_catalog")
	_parity_report(runner, balance.last.get("parity", {}), oracle.last.get("parity", {}))
	var catalog: Dictionary = oracle.raw_catalog.duplicate(true)
	balance.apply_to_catalog(catalog)
	_final_stats(runner, catalog, oracle.final_stats)
	_table(runner, balance.last.table, oracle.table, "apply_to_catalog table")
	_parity_report(runner, balance.last.get("parity", {}), oracle.last.get("parity", {}))
	_pool_report(runner, balance.last, oracle.last)
	var starters_unchanged := true
	for hero: String in balance.starter_heroes:
		if catalog[hero] != oracle.raw_catalog[hero]:
			starters_unchanged = false
	runner.check(starters_unchanged, "apply_to_catalog leaves starter shop stats untouched")
	var second: Dictionary = oracle.raw_catalog.duplicate(true)
	balance.apply_to_catalog(second)
	var idempotent := true
	for hero: String in oracle.final_stats:
		for field: String in oracle.final_stats[hero]:
			if second[hero].get(field) != catalog[hero].get(field):
				idempotent = false
	runner.check(idempotent, "apply_to_catalog is idempotent from pristine baseline")
	_power_cases(runner, balance, oracle.helpers)
	_calibration(runner, balance, oracle.calibrate)
	_fix_band(runner, balance, catalog, oracle.fix_band)
	_variants(runner, balance, oracle)
	_runtime(runner, data)
	var missing_path := "user://missing_balance_%d.json" % Time.get_ticks_usec()
	var missing := HeroBalance.new(data.archetypes, missing_path)
	runner.check(
		not missing.valid() and not missing.load_error.is_empty(),
		"missing balance contract fails closed"
	)
	var invalid_core := CoreData.new(
		"res://data/core_data.json", HeroArchetypes.DEFAULT_PATH, missing_path
	)
	runner.check(not invalid_core.valid(), "CoreData rejects missing balance contract")


static func _helpers(runner, balance: HeroBalance, helpers: Dictionary) -> void:
	for row: Array in helpers.py_round:
		runner.check(
			HeroBalance.py_round(float(row[0])) == int(row[1]), "balance py_round %s" % row[0]
		)
	for row: Dictionary in helpers.py_round_n:
		runner.check(
			_near(HeroBalance.py_round_n(float(row["in"]), int(row.n)), float(row.out), 1e-9),
			"balance py_round_n %s/%s" % [row["in"], row.n]
		)
	for row: Dictionary in helpers.median:
		runner.check(_near(HeroBalance.median(row["in"]), float(row.out)), "balance median")
	for row: Dictionary in helpers.fmean:
		runner.check(_near(HeroBalance.mean(row["in"]), float(row.out)), "balance fmean")
	for row: Array in helpers.school_mod:
		runner.check(
			_near(balance.school_mod(str(row[0])), float(row[1])), "balance school_mod %s" % row[0]
		)
	for row: Array in helpers.level_factor:
		runner.check(
			_near(balance.starter_level_factor(row[0]), float(row[1])),
			"balance level_factor %s" % row[0]
		)
	runner.check(
		_near(balance.tower_phys_factor, float(helpers.tower_phys_factor)),
		"balance tower_phys_factor"
	)


static func _metrics(runner, balance: HeroBalance, oracle: Dictionary) -> void:
	for hero: String in oracle.metrics:
		var actual := balance.metrics(oracle.raw_catalog[hero])
		var expected: Dictionary = oracle.metrics[hero]
		var matches := true
		for key: String in expected:
			if not _near(float(actual[key]), float(expected[key])):
				matches = false
		runner.check(matches, "balance metrics parity: " + hero)


static func _catchup(runner, balance: HeroBalance, catchup: Dictionary) -> void:
	for row: Dictionary in catchup.mult_grid:
		var actual := balance.starter_catchup(row.hero, row.unlocks, row.level)
		runner.check(
			_near(float(actual[0]), float(row.hp)) and _near(float(actual[1]), float(row.dmg)),
			"balance catchup mult: %s/%s/%s" % [row.hero, row.unlocks, row.level]
		)
	for row: Dictionary in catchup.stat_cases:
		var actual := balance.starter_catchup_stats(
			row.hero, {"hp": row.base_hp, "damage": row.base_damage}, row.unlocks, row.level
		)
		runner.check(
			int(actual[0]) == int(row.hp) and int(actual[1]) == int(row.damage),
			"balance catchup stats: %s/%s/%s" % [row.hero, row.unlocks, row.level]
		)
	for row: Dictionary in catchup.unlock_counts:
		runner.check(
			balance.boss_unlocks_for_purchases(row.purchased) == int(row.unlocks),
			"balance boss_unlocks_for_purchases"
		)


static func _table(runner, actual: Dictionary, expected: Dictionary, label: String) -> void:
	runner.check(actual.size() == expected.size(), label + " table size")
	for hero: String in expected:
		if not actual.has(hero):
			runner.check(false, label + " missing hero " + hero)
			continue
		var row: Dictionary = actual[hero]
		var want: Dictionary = expected[hero]
		runner.check(
			(
				_near(float(row.hp), float(want.hp), 1e-6)
				and _near(float(row.dmg), float(want.dmg), 1e-6)
				and _near(float(row.skill), float(want.skill), 1e-6)
			),
			label + " multipliers: " + hero
		)


static func _parity_report(runner, actual: Dictionary, expected: Dictionary) -> void:
	runner.check(
		_near(float(actual.get("pool_target", 0)), float(expected.get("pool_target", 0)), 1e-6),
		"balance cell parity pool_target"
	)
	var cells: Dictionary = actual.get("cells", {})
	var want_cells: Dictionary = expected.get("cells", {})
	runner.check(cells.size() == want_cells.size(), "balance cell parity count")
	for key: String in want_cells:
		runner.check(
			_near(float(cells.get(key, 0)), float(want_cells[key]), 1e-6),
			"balance cell parity " + key
		)
	var schools: Dictionary = actual.get("schools", {})
	var want_schools: Dictionary = expected.get("schools", {})
	for key: String in want_schools:
		runner.check(
			_near(float(schools.get(key, 0)), float(want_schools[key]), 1e-6),
			"balance school parity " + key
		)


static func _pool_report(runner, actual: Dictionary, expected: Dictionary) -> void:
	var anchors: Dictionary = actual.get("pool_anchor", {})
	var want_anchors: Dictionary = expected.get("pool_anchor", {})
	runner.check(anchors.size() == want_anchors.size(), "balance pool anchor keys")
	for key: String in want_anchors:
		runner.check(
			_near(float(anchors.get(key, 0)), float(want_anchors[key]), 1e-6),
			"balance pool anchor " + key
		)
	var means: Dictionary = actual.get("pool_means", {})
	var want_means: Dictionary = expected.get("pool_means", {})
	for key: String in want_means:
		runner.check(
			_near(float(means.get(key, 0)), float(want_means[key]), 1e-6),
			"balance pool means " + key
		)
	var fix: Dictionary = actual.get("fix", {})
	var want_fix: Dictionary = expected.get("fix", {})
	for key: String in want_fix:
		runner.check(
			_near(float(fix.get(key, 0)), float(want_fix[key]), 1e-6), "balance fixpoint " + key
		)


static func _final_stats(runner, catalog: Dictionary, expected: Dictionary) -> void:
	for hero: String in expected:
		var matches := true
		for field: String in expected[hero]:
			var want: Variant = expected[hero][field]
			var actual: Variant = catalog[hero].get(field)
			if want == null:
				if actual != null:
					matches = false
			elif int(actual) != int(want):
				matches = false
		runner.check(matches, "balance final stats: " + hero)


static func _power_cases(runner, balance: HeroBalance, helpers: Dictionary) -> void:
	for row: Dictionary in helpers.final_power:
		var actual := balance.final_power(
			row.m,
			float(row.y),
			float(row.x_dmg),
			float(row.x_sk),
			float(row.med_dps),
			float(row.med_ehp)
		)
		runner.check(_near(actual, float(row.out)), "balance final_power " + row.hero)
	for row: Dictionary in helpers.eff_dps:
		var actual := balance.eff_dps(row.hero, row.stats, row.m, float(row.dps))
		runner.check(_near(actual, float(row.out)), "balance eff_dps " + row.hero)


static func _calibration(runner, balance: HeroBalance, calibrate: Dictionary) -> void:
	var result := balance.calibrate_boss_resistances(calibrate.rows)
	var res: Dictionary = result[0]
	var report: Dictionary = result[1]
	runner.check(res.size() == calibrate.res.size(), "balance calibration row count")
	for boss: String in calibrate.res:
		var want: Dictionary = calibrate.res[boss]
		var actual: Dictionary = res.get(boss, {})
		runner.check(
			(
				int(actual.get("armor", -1)) == int(want.armor)
				and _near(float(actual.get("magic_resist", -1)), float(want.magic_resist), 1e-6)
			),
			"balance calibration resistance: " + boss
		)
	for dc: String in calibrate.report._scales:
		var want: Dictionary = calibrate.report._scales[dc]
		var actual: Dictionary = report.get("_scales", {}).get(dc, {})
		runner.check(
			(
				_near(float(actual.get("armor_scale", 0)), float(want.armor_scale), 1e-6)
				and _near(float(actual.get("mr_scale", 0)), float(want.mr_scale), 1e-6)
			),
			"balance calibration scales: " + dc
		)


static func _fix_band(
	runner, balance: HeroBalance, catalog: Dictionary, fix_band: Dictionary
) -> void:
	var band_catalog := catalog.duplicate(true)
	var info := balance.final_fixpoint(band_catalog, 1.0, fix_band.cell_band)
	for key: String in fix_band.info:
		runner.check(
			_near(float(info.get(key, 0)), float(fix_band.info[key]), 1e-6),
			"balance fix_band info " + key
		)
	for hero: String in fix_band.damage:
		var want: Dictionary = fix_band.damage[hero]
		runner.check(
			(
				int(band_catalog[hero].damage) == int(want.damage)
				and int(band_catalog[hero].skill_damage) == int(want.skill_damage)
			),
			"balance fix_band damage: " + hero
		)


static func _variants(runner, balance: HeroBalance, oracle: Dictionary) -> void:
	for row: Dictionary in oracle.resolve_variants:
		var resolved := balance.resolve_catalog(
			oracle.raw_catalog.duplicate(true), int(row.unlocks), int(row.level)
		)
		for hero: String in row.starters:
			var want: Dictionary = row.starters[hero]
			var actual: Dictionary = resolved[hero]
			runner.check(
				(
					_near(float(actual.hp), float(want.hp), 1e-6)
					and _near(float(actual.dmg), float(want.dmg), 1e-6)
				),
				"balance resolve variant: %s/%s" % [hero, row.unlocks]
			)


static func _runtime(runner, data: CoreData) -> void:
	var balance := data.balance
	runner.check(
		balance.is_starter("kaizen") and not balance.is_starter("gornak"),
		"runtime starter membership"
	)
	var fresh := BattleUnit.new()
	fresh.setup_hero(data, "kaizen", "blue", Vector2(300, 300), 0)
	var full := BattleUnit.new()
	full.setup_hero(data, "kaizen", "blue", Vector2(300, 300), 216)
	runner.check(
		fresh.base_hp > full.base_hp and fresh.base_damage > full.base_damage,
		"runtime starter catch-up decays with roster"
	)
	runner.check(
		_near(full.base_hp, float(data.hero("kaizen").hp) * 1.15),
		"runtime full roster keeps raw starter base plus melee compensation"
	)
	var boss_hero := BattleUnit.new()
	boss_hero.setup_hero(data, "gornak", "blue", Vector2(300, 300), 0)
	runner.check(
		_near(boss_hero.base_hp, float(data.hero("gornak").hp) * 1.15),
		"runtime non-starter is not catch-up scaled"
	)
	var model := MatchModel.new()
	model.setup(
		data.level(1), {"purchased_heroes": ["kaizen", "gornak", "abaddon"]}, "normal", false, 7
	)
	runner.check(
		balance.boss_unlocks_for_purchases(model.purchased_heroes) == 2,
		"runtime match purchases count only boss unlocks"
	)
	var expected := balance.starter_catchup_stats(
		"kaizen",
		{
			"hp": float(data.hero("kaizen").hp) * 1.15,
			"damage": float(data.hero("kaizen").damage) * 1.2
		},
		2,
		1
	)
	runner.check(
		(
			_near(model.heroes[0].base_hp, float(expected[0]))
			and _near(model.heroes[0].base_damage, float(expected[1]))
		),
		"runtime MatchModel.setup applies starter catch-up from the saved roster"
	)
	model.ai.purchase_target = "kaizen"
	model.ai.purchase_cost = int(data.hero("kaizen").cost)
	model.ai_gold = 10000
	runner.check(model.ai._buy_hero(), "runtime enemy AI can buy a starter")
	runner.check(
		(
			_near(model.enemy_heroes[0].base_hp, float(expected[0]))
			and _near(model.enemy_heroes[0].base_damage, float(expected[1]))
		),
		"runtime enemy AI applies the same starter catch-up"
	)
	model.clear_unit_refs()


static func _near(a: float, b: float, tol := 1e-6) -> bool:
	return absf(a - b) <= tol
