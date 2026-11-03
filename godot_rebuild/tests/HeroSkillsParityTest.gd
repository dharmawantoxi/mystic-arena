extends RefCounted

## Python-oracle parity for hero_skills/: registry, visual durations, BaseSkill
## helpers, geometry, cooldown triggers and the native runtime facade.


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/hero_skills_parity.json", FileAccess.READ)
	runner.check(file != null, "hero skills Python oracle fixture exists")
	if file == null:
		return
	var oracle: Dictionary = JSON.parse_string(file.get_as_text())
	var skills := HeroSkills.new()
	runner.check(skills.valid(), "native hero skills contract loads")
	if not skills.valid():
		return
	_contract(runner, skills, oracle)
	_classification(runner, skills, oracle.hero_kind_cases)
	_visual(runner, skills, oracle.visual_duration_cases)
	_recipes(runner, skills, oracle.registry_cases)
	_cooldowns(runner, skills, oracle.cooldown_cases)
	_ranges(runner, skills, oracle.skill_range_cases)
	_geometry(runner, skills, oracle.geometry_cases)
	_aoe(runner, skills, oracle.aoe_cases)
	_triggers(runner, skills, oracle.trigger_cases)
	_runtime(runner)
	_fail_closed(runner)


static func _near(a: float, b: float) -> bool:
	return absf(a - b) < 0.0005


static func _contract(runner, skills: HeroSkills, oracle: Dictionary) -> void:
	var cases: Dictionary = oracle.contract_cases
	runner.check(
		oracle.source_sha256 == skills.contract.source_sha256, "oracle source hash current"
	)
	runner.check(
		oracle.generated_kit_sha256 == skills.contract.generated_kit.sha256,
		"oracle generated kit hash current"
	)
	runner.check(skills.starters.size() == cases.starters.size(), "six starter handlers")
	runner.check(skills.registry.size() == int(cases.recipes), "66 boss-hero recipes")
	runner.check(skills.handler_map.size() == int(cases.hero_handlers), "222 hero handlers")
	runner.check(skills.state_keys.size() == int(cases.state_keys), "91 generated kit state keys")
	runner.check(
		skills.counts.kit_static_functions == int(cases.kit_static_functions),
		"generated kit static function coverage"
	)
	runner.check(skills.require_target == bool(cases.require_target), "source REQUIRE_TARGET")
	runner.check(_near(skills.target_range_slack, float(cases.target_range_slack)), "target slack")
	runner.check(
		_near(skills.skill_range_fallback, float(cases.skill_range_fallback)),
		"skill range fallback"
	)
	for key: String in cases.default_visual_duration:
		runner.check(
			int(skills.default_visual_duration[key]) == int(cases.default_visual_duration[key]),
			"default visual duration: " + key
		)


static func _classification(runner, skills: HeroSkills, cases: Array) -> void:
	for row: Dictionary in cases:
		var hero_type := str(row.hero_type)
		runner.check(skills.hero_kind(hero_type) == str(row.kind), "hero skill kind: " + hero_type)
		runner.check(
			skills.handler_class(hero_type) == str(row.handler), "hero skill handler: " + hero_type
		)


static func _visual(runner, skills: HeroSkills, cases: Array) -> void:
	for row: Dictionary in cases:
		var hero_type := str(row.hero_type)
		var key := str(row.key)
		runner.check(
			skills.visual_duration(hero_type, key) == int(row.frames),
			"visual duration: " + hero_type + "/" + key
		)
	runner.check(skills.visual_duration("kaizen", "x") == -1, "invalid skill slot rejected")


static func _recipes(runner, skills: HeroSkills, cases: Array) -> void:
	for row: Dictionary in cases:
		var hero_type := str(row.hero_type)
		var key := str(row.key)
		runner.check(
			skills.recipe_method(hero_type, key) == str(row.method),
			"boss hero recipe: " + hero_type + "/" + key
		)
	runner.check(skills.recipe_method("__unknown__", "q").is_empty(), "unknown recipe is empty")
	runner.check(skills.recipe_method("gornak", "q") == "_cast_q_mana_break", "gornak Q recipe")


static func _cooldowns(runner, skills: HeroSkills, cases: Array) -> void:
	for row: Dictionary in cases:
		var key := str(row.key)
		runner.check(
			skills.cooldown_ready(key, int(row.timer)) == bool(row.ready),
			"cooldown ready: " + key + "/" + str(row.timer)
		)
	runner.check(not skills.cooldown_ready("x", 0), "unknown cooldown slot rejected")


static func _ranges(runner, skills: HeroSkills, cases: Array) -> void:
	for row: Dictionary in cases:
		var actual := skills.skill_range(
			float(row.attack_range), row.skill_range, row.skill_data, float(row.fallback)
		)
		runner.check(
			_near(actual, float(row.expected)), "BaseSkill skill range: " + str(row.skill_range)
		)


static func _geometry(runner, skills: HeroSkills, cases: Array) -> void:
	for row: Dictionary in cases:
		var units: Array = []
		for unit: Dictionary in row.units:
			units.append(unit)
		var center := Vector2(float(row.center[0]), float(row.center[1]))
		var actual: Array = skills.enemies_in_range(center, float(row.range), units)
		var expected: Array = row.expected
		runner.check(actual.size() == expected.size(), "enemies-in-range count")
		runner.check(actual.size() == int(row.hit_count), "aoe hit count")
		if actual.size() != expected.size():
			continue
		for index in range(actual.size()):
			var actual_pair: Array = actual[index]
			var expected_pair: Array = expected[index]
			runner.check(
				int(actual_pair[0]) == int(expected_pair[0]), "enemy range index: " + str(index)
			)
			runner.check(
				_near(float(actual_pair[1]), float(expected_pair[1])),
				"enemy range distance: " + str(index)
			)


static func _aoe(runner, skills: HeroSkills, cases: Array) -> void:
	for row: Dictionary in cases:
		var damage := skills.aoe_damage(float(row.skill_damage), float(row.multiplier))
		runner.check(damage == int(row.expected_damage), "aoe damage truncation")
		runner.check(row.damage_events.size() == int(row.hit_count), "aoe damage event count")
		for event_damage in row.damage_events:
			runner.check(int(event_damage) == damage, "aoe per-target damage")


static func _triggers(runner, skills: HeroSkills, cases: Array) -> void:
	for row: Dictionary in cases:
		var expected: Dictionary = row.expected
		var actual := skills.trigger_plan(str(row.hero_type), str(row.key), int(row.cooldown_max))
		if expected.is_empty():
			runner.check(actual.is_empty(), "unknown handler has no cooldown trigger")
			continue
		runner.check(actual.size() == expected.size(), "trigger plan field count")
		for key: String in expected:
			if not actual.has(key):
				runner.check(false, "trigger plan field: " + key)
				continue
			match key:
				"shake", "sound_volume":
					runner.check(
						_near(float(actual[key]), float(expected[key])),
						"trigger plan float: " + key
					)
				"cooldown", "active_skill_timer":
					runner.check(int(actual[key]) == int(expected[key]), "trigger plan int: " + key)
				_:
					runner.check(
						str(actual[key]) == str(expected[key]), "trigger plan string: " + key
					)


static func _runtime(runner) -> void:
	var data := CoreData.new()
	runner.check(data.valid() and data.skills.valid(), "CoreData validates hero skills contract")
	runner.check(HeroSkills.shared().valid(), "shared native skill facade loads")
	var hero := BattleUnit.new()
	hero.setup_hero(data, "kaizen", "blue", Vector2(100.0, 100.0))
	runner.check(not hero.kit.is_empty(), "runtime init_state goes through the facade")
	runner.check(
		HeroSkills.shared().handler_class(hero.hero_type) == "KaizenSkills",
		"runtime hero handler lookup"
	)
	var unknown := BattleUnit.new()
	unknown.unit_type = "__unknown__"
	runner.check(
		not HeroSkills.shared().cast(unknown, "q", [], [], []),
		"unknown hero cannot enter the generated kit"
	)
	runner.check(
		_near(HeroSkills.shared().target_reach(100.0), 115.0),
		"runtime target slack matches BaseSkill"
	)


static func _fail_closed(runner) -> void:
	var stamp := Time.get_ticks_usec()
	var missing_path := "user://missing_hero_skills_%d.json" % stamp
	var missing := HeroSkills.new(missing_path)
	runner.check(
		not missing.valid() and not missing.load_error.is_empty(),
		"missing hero skills contract fails closed"
	)
	var invalid_core := CoreData.new(
		"res://data/core_data.json",
		HeroArchetypes.DEFAULT_PATH,
		HeroBalance.DEFAULT_PATH,
		HeroItems.DEFAULT_PATH,
		Localization.DEFAULT_PATH,
		BossCatalog.DEFAULT_PATH,
		"user://missing_hero_skills_core_%d.json" % stamp
	)
	runner.check(not invalid_core.valid(), "CoreData rejects missing hero skills contract")
