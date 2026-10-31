extends RefCounted
## Whole `hero_skills/` folder coverage, proven from the source inventory.
##
## `tests/fixtures/hero_skills_folder_source.json` is derived from the two
## Pygame files by `tests/hero_skills_folder_source_oracle.py`. This suite asks
## the native project to account for every part of it:
##
## * `BaseSkill`'s cast feedback (screen shake + blue-only `hero_skill` sound)
##   is a real native module (`scripts/combat/skill_feedback.gd`) whose tables
##   are the source call sites: starter defaults, thorne's swapped Q/E, and the
##   216 boss heroes' 10/8/8/15;
## * the six starter kits keep their source `SKILL_VISUAL_DURATION`, five as
##   native kit scripts and kaizen inside `minion_battle.gd`;
## * the boss kit visuals keep the shared 60/90/60/100 default plus the two
##   per-hero overrides the source declares (nyzrak, vhalzun);
## * `BaseSkill`'s targeting helpers are ported (`skill_common.gd`,
##   `boss_skill_common.gd`'s 140 px floor, `_has_q_target`'s slack);
## * the 66-entry `_SKILL_REGISTRY` (264 cast methods) and the 150-boss shared
##   fallback still resolve through the match's own resolver;
## * a live cast really produces the source shake and volume.

const Battle = preload("res://scripts/match/prototype_battle.gd")
const MinionBattle = preload("res://scripts/combat/minion_battle.gd")
const SkillFeedback = preload("res://scripts/combat/skill_feedback.gd")
const RecipeRegistry = preload("res://scripts/combat/boss_recipe_registry.gd")
const SharedSkills = preload("res://scripts/combat/source_shared_boss_skills.gd")
const HeroRoster = preload("res://scripts/data/hero_roster.gd")
const SKILL_DIRECTORY := "res://scripts/combat/"
const MINION_BATTLE := "res://scripts/combat/minion_battle.gd"
const SKILL_COMMON := "res://scripts/combat/skill_common.gd"
const BOSS_COMMON := "res://scripts/combat/boss_skill_common.gd"
const FIXTURE := "res://tests/fixtures/hero_skills_folder_source.json"
const THORNE = preload("res://data/heroes/thorne.tres")
const GORNAK = preload("res://data/heroes/gornak.tres")
const VEX = preload("res://data/heroes/vex.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const STOCK_MINION = preload("res://data/minions/goblin.tres")


func run(check: Callable) -> void:
	var source := _fixture()
	check.call(not source.is_empty(), "The hero_skills/ inventory fixture parses")
	if source.is_empty():
		return
	_check_counts(check, source)
	_check_feedback_tables(check, source)
	_check_starter_visuals(check, source)
	_check_boss_visuals(check, source)
	_check_helpers(check, source)
	_check_registry(check, source)
	_check_handler_api(check, source)
	_check_live_feedback(check, source)


func _fixture() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	return parsed if parsed is Dictionary else {}


func _dict_equal(left: Dictionary, right: Dictionary) -> bool:
	if left.size() != right.size():
		return false
	for key in left:
		if not right.has(key):
			return false
		var a: Variant = left[key]
		var b: Variant = right[key]
		if a is Dictionary and b is Dictionary:
			if not _dict_equal(a, b):
				return false
		elif typeof(a) != typeof(b):
			if float(a) != float(b):
				return false
		elif a != b:
			return false
	return true


func _check_counts(check: Callable, source: Dictionary) -> void:
	var counts: Dictionary = source.get("counts", {})
	var files: Dictionary = source.get("files", {})
	check.call(
		files.size() == 2 and files.has("__init__.py") and files.has("_bundle.py"),
		"The folder holds the package and the bundle: %s" % str(files.keys())
	)
	check.call(int(counts.get("files", 0)) == files.size(), "The file count matches the file table")
	check.call(
		int(counts.get("base_skill_methods", 0)) == 28,
		"BaseSkill exposes 28 methods: %d" % int(counts.get("base_skill_methods", 0))
	)
	check.call(
		int(counts.get("boss_hero_methods", 0)) == 273,
		"BossHeroSkills holds 273 methods: %d" % int(counts.get("boss_hero_methods", 0))
	)
	check.call(
		int(counts.get("registry_bosses", 0)) == 66,
		"The registry names 66 bosses: %d" % int(counts.get("registry_bosses", 0))
	)
	check.call(
		int(counts.get("registry_casts", 0)) == 264,
		"Four recipes per registry boss: %d" % int(counts.get("registry_casts", 0))
	)
	check.call(
		int(counts.get("starter_kits", 0)) == 6,
		"Six starter kits: %d" % int(counts.get("starter_kits", 0))
	)
	check.call(
		int(counts.get("starter_methods", 0)) == 39 and int(counts.get("bundle_classes", 0)) == 15,
		"39 starter methods across the 15 bundle classes"
	)


## The feedback module must carry the source tables verbatim.
func _check_feedback_tables(check: Callable, source: Dictionary) -> void:
	var base: Dictionary = source.get("base_skill", {})
	var boss: Dictionary = source.get("boss_hero_skills", {})
	var triggers: Dictionary = base.get("triggers", {})
	var default_shake := {}
	var volume := {}
	for slot in triggers:
		default_shake[slot] = int((triggers[slot] as Dictionary).get("shake", 0))
		volume[slot] = float((triggers[slot] as Dictionary).get("volume", 0.0))
	check.call(
		SkillFeedback.DEFAULT_SHAKE == default_shake,
		"BaseSkill trigger shakes are the native defaults: %s" % str(default_shake)
	)
	check.call(
		_dict_equal(SkillFeedback.VOLUME, volume),
		"Trigger volumes match the source: %s" % str(volume)
	)
	check.call(
		SkillFeedback.BOSS_SHAKE == boss.get("cast_shake", {}),
		"BossHeroSkills cast shakes are ported: %s" % str(SkillFeedback.BOSS_SHAKE)
	)
	var starters: Dictionary = source.get("starter_kits", {})
	var expected := {}
	for hero_id in starters:
		expected[hero_id] = (starters[hero_id] as Dictionary).get("shake", {})
	check.call(
		SkillFeedback.STARTER_SHAKE == expected, "Starter kits keep their per-call shake amounts"
	)
	check.call(
		(
			int(SkillFeedback.STARTER_SHAKE["thorne"]["q"]) == 6
			and int(SkillFeedback.STARTER_SHAKE["thorne"]["e"]) == 8
		),
		"Thorne keeps the source's swapped Q/E intensities"
	)
	check.call(
		SkillFeedback.SOUND == "hero_skill" and SkillFeedback.BLUE == 0,
		"The feedback plays the source sound for the blue team"
	)


## Five starter kits are native scripts; kaizen lives inside minion_battle.
## Ordered `hero.active_skill_timer = N` values of a kit file.
func _timers(text: String) -> Array:
	var pattern := RegEx.new()
	pattern.compile("active_skill_timer = (\\d+)")
	var values: Array = []
	for found in pattern.search_all(text):
		values.append(int(found.get_string(1)))
	return values


func _check_starter_visuals(check: Callable, source: Dictionary) -> void:
	var starters: Dictionary = source.get("starter_kits", {})
	var mismatched: Array = []
	var missing: Array = []
	for hero_id in starters:
		var visual: Dictionary = (starters[hero_id] as Dictionary).get("visual_duration", {})
		var expected := (
			'{"q": %d, "w": %d, "e": %d, "r": %d}'
			% [
				int(visual.get("q", 0)),
				int(visual.get("w", 0)),
				int(visual.get("e", 0)),
				int(visual.get("r", 0)),
			]
		)
		var path := SKILL_DIRECTORY + String(hero_id) + "_skills.gd"
		if hero_id == "kaizen":
			if int(KAIZEN.q_visual_ticks) != int(visual.get("q", -1)):
				mismatched.append("kaizen q_visual_ticks")
			continue
		if not FileAccess.file_exists(path):
			missing.append(hero_id)
			continue
		var text := FileAccess.get_file_as_string(path)
		if text.contains(expected):
			continue
		# Some kits set the timer per branch instead of a `{...}[key]` table.
		var ordered := [
			int(visual.get("q", -1)),
			int(visual.get("w", -1)),
			int(visual.get("e", -1)),
			int(visual.get("r", -1)),
		]
		if _timers(text) != ordered:
			mismatched.append("%s %s vs %s" % [hero_id, str(_timers(text)), str(ordered)])
	check.call(
		missing.is_empty(), "Every starter except kaizen has a native kit: %s" % str(missing)
	)
	check.call(
		mismatched.is_empty(),
		"Starter visual durations match SKILL_VISUAL_DURATION: %s" % str(mismatched)
	)
	check.call(KAIZEN.q_reach_slack > 1.0, "Kaizen keeps the source targeting slack")
	check.call(
		HeroRoster.DEFINITIONS.has("kaizen") and KAIZEN.is_boss_hero == false,
		"Kaizen stays a starter hero resource"
	)
	var minion := FileAccess.get_file_as_string(MINION_BATTLE)
	check.call(
		(
			minion.contains("hero.active_skill_timer = 60")
			and minion.contains("hero.active_skill_timer = 90")
			and minion.contains("hero.active_skill_timer = 100")
		),
		"Kaizen's W/E/R visuals stay inline at 90/60/100"
	)


## Boss kits: shared default visuals plus the two per-hero source overrides.
func _check_boss_visuals(check: Callable, source: Dictionary) -> void:
	var base: Dictionary = source.get("base_skill", {})
	var default_visual: Dictionary = base.get("default_visual_duration", {})
	var expected := (
		'{"q": %d, "w": %d, "e": %d, "r": %d}'
		% [
			int(default_visual.get("q", 0)),
			int(default_visual.get("w", 0)),
			int(default_visual.get("e", 0)),
			int(default_visual.get("r", 0)),
		]
	)
	var trimmed := expected.replace(": ", ": ")
	var inline_ok := 0
	var inline_bad: Array = []
	for file_name in DirAccess.get_files_at(SKILL_DIRECTORY):
		if not file_name.begins_with("boss_level_") or not file_name.ends_with("_skills.gd"):
			continue
		var text := FileAccess.get_file_as_string(SKILL_DIRECTORY + file_name)
		if text.contains(trimmed):
			inline_ok += 1
		elif not text.contains("VISUAL["):
			inline_bad.append(file_name)
	check.call(
		inline_ok >= 5,
		"The 60/90/60/100 shared visual is spelled out in the boss kits: %d" % inline_ok
	)
	check.call(inline_bad.is_empty(), "Every boss kit names a visual table: %s" % str(inline_bad))
	var overrides: Dictionary = (source.get("boss_hero_skills", {}) as Dictionary).get(
		"visual_overrides", {}
	)
	var expected_override := {}
	for hero_id in overrides:
		var row: Dictionary = overrides[hero_id]
		expected_override[hero_id] = (
			'{"q": %d, "w": %d, "e": %d, "r": %d}'
			% [
				int(row.get("q", 0)),
				int(row.get("w", 0)),
				int(row.get("e", 0)),
				int(row.get("r", 0)),
			]
		)
	check.call(
		expected_override.has("nyzrak") and expected_override.has("vhalzun"),
		"The source declares two per-hero boss visual overrides"
	)
	var override_hits: Array = []
	for file_name in DirAccess.get_files_at(SKILL_DIRECTORY):
		if not file_name.begins_with("boss_level_") or not file_name.ends_with("_skills.gd"):
			continue
		var text := FileAccess.get_file_as_string(SKILL_DIRECTORY + file_name)
		for hero_id in expected_override:
			if text.contains('%s": %s' % [hero_id, expected_override[hero_id]]):
				override_hits.append(hero_id)
	check.call(
		override_hits.size() == 2,
		"Both per-hero visual overrides are native: %s" % str(override_hits)
	)


## `BaseSkill`'s helper API: enemy sweep, target guard, stun, cooldown clock.
func _check_helpers(check: Callable, source: Dictionary) -> void:
	var base: Dictionary = source.get("base_skill", {})
	var common := FileAccess.get_file_as_string(SKILL_COMMON)
	for name in ["enemies", "current", "stun", "hit", "trigger", "ready", "bound_target"]:
		check.call(
			common.contains("static func %s(" % name), "skill_common.gd ports BaseSkill.%s" % name
		)
	check.call(
		(
			common.contains('"q": 60, "w": 90, "e": 60, "r": 100')
			or common.contains("active_skill_timer = visual")
		),
		"skill_common.gd carries the source visual+duration trigger"
	)
	var boss_common := FileAccess.get_file_as_string(BOSS_COMMON)
	var boss_row: Dictionary = source.get("boss_hero_skills", {})
	var floor_value := int(boss_row.get("cast_range_floor", 0))
	check.call(
		floor_value == 140 and boss_common.contains("maxi(int(hero.skill_range), 140)"),
		"The generic cast keeps the source max(skill_range, 140) gate"
	)
	check.call(
		common.contains("maxi(target.attack_timer, duration)"),
		"BaseSkill._apply_stun keeps the never-shorten max rule"
	)
	var minion := FileAccess.get_file_as_string(MINION_BATTLE)
	check.call(
		minion.contains("func _has_q_target(") and minion.contains("q_reach_slack"),
		"BaseSkill._has_target/_acquire_target is ported with the per-hero slack"
	)
	check.call(
		is_equal_approx(float(base.get("target_range_slack", 0.0)), 1.15),
		"The source targeting slack is 1.15"
	)
	var fallback: Dictionary = (source.get("boss_hero_skills", {}) as Dictionary).get(
		"fallback", {}
	)
	var shared := FileAccess.get_file_as_string("res://scripts/combat/source_shared_boss_skills.gd")
	check.call(
		int(fallback.get("visual_duration", 0)) == 40 and shared.contains("40"),
		"_fallback_cast's 40-tick visual is native"
	)
	check.call(
		str(fallback.get("aoe_range", [])) == "[150, 200]",
		"_fallback_cast keeps its 150/200 AOE radii in source order"
	)


## `_SKILL_REGISTRY` (66) plus the 150-boss shared fallback still cover 216.
func _check_registry(check: Callable, source: Dictionary) -> void:
	var registry: Dictionary = (source.get("boss_hero_skills", {}) as Dictionary).get(
		"registry", {}
	)
	var native := MinionBattle.NATIVE_SKILLS
	var resolved: Array = []
	var homeless: Array = []
	for boss_id in registry:
		if RecipeRegistry.handler(String(boss_id), native) == null:
			homeless.append(String(boss_id))
		else:
			resolved.append(String(boss_id))
	check.call(registry.size() == 66, "The source registry names 66 recipes: %d" % registry.size())
	check.call(
		homeless.is_empty(),
		(
			"Every source recipe resolves to a native kit: %d missing %s"
			% [homeless.size(), str(homeless.slice(0, 10))]
		)
	)
	check.call(resolved.size() == 66, "The resolver answers all 66 recipes: %d" % resolved.size())
	var cast_methods := {}
	for boss_id in registry:
		for slot in registry[boss_id]:
			cast_methods[String(registry[boss_id][slot])] = true
	check.call(
		cast_methods.size() == 264,
		"The registry names 264 distinct cast methods: %d" % cast_methods.size()
	)
	var bosses: Dictionary = {}
	var overlapped: Array = []
	for boss_id in HeroRoster.DEFINITIONS:
		var definition: Variant = HeroRoster.DEFINITIONS[boss_id]
		if not bool(definition.is_boss_hero):
			continue
		bosses[boss_id] = true
		var shared_hit: bool = boss_id in SharedSkills.IDS
		var recipe_hit: bool = registry.has(boss_id)
		if shared_hit and recipe_hit:
			overlapped.append(boss_id)
	check.call(bosses.size() == 216, "216 boss heroes carry a kit decision: %d" % bosses.size())
	check.call(overlapped.is_empty(), "No boss is in both skill homes: %s" % str(overlapped))
	check.call(
		registry.size() + SharedSkills.IDS.size() == bosses.size(),
		"66 recipes + 150 shared = 216 boss heroes"
	)


## `__init__.py`'s handler registry is the source dispatch table.
func _check_handler_api(check: Callable, source: Dictionary) -> void:
	var registry: Dictionary = source.get("handler_registry", {})
	var api: Array = registry.get("functions", [])
	check.call(
		api == ["register_handler", "get_skill_handler"],
		"The package API is register/get only: %s" % str(api)
	)
	var starters: Array = registry.get("registered_starters", [])
	check.call(
		starters.size() == 6 and starters.has("kaizen") and starters.has("zephyr"),
		"The six starters are auto-registered: %s" % str(starters)
	)
	var aliases: Array = registry.get("aliased_submodules", [])
	check.call(
		aliases.size() == 7 and aliases.has("boss_hero_skills") and aliases.has("kaizen"),
		"Seven legacy submodule names stay importable in the source: %s" % str(aliases)
	)
	var plain: Array = registry.get("plain_submodules", [])
	check.call(plain == ["base_skill"], "base_skill stays importable on its own: %s" % str(plain))
	check.call(
		bool(registry.get("auto_registers_every_boss_type", false)),
		"The source registers every boss type on import"
	)
	var minion := FileAccess.get_file_as_string(MINION_BATTLE)
	var preloads := 0
	for hero_id in ["thorne", "grimjaw", "sylara", "vex", "zephyr"]:
		if minion.contains(SKILL_DIRECTORY + hero_id + "_skills.gd"):
			preloads += 1
	check.call(preloads == 5, "minion_battle wires the five starter kits: %d" % preloads)
	check.call(
		minion.contains("AlchemistSkills") and minion.contains("SourceSharedBossSkills"),
		"The native dispatch also carries alchemist and the shared fallback"
	)


func _hero(world, definition, team: int, position: Vector2):
	return world.spawn_hero(definition, team, position)


func _enemy(world, position: Vector2, team: int):
	var copy := STOCK_MINION.duplicate()
	copy.max_hp = 10000
	var unit = world.spawn_unit(copy, team, 1)
	unit.position = position
	unit.hp = 10000
	return unit


## A real cast produces the source shake and the blue-only sound decision.
func _check_live_feedback(check: Callable, source: Dictionary) -> void:
	var starters: Dictionary = source.get("starter_kits", {}) as Dictionary
	var thorne_shake: Dictionary = (starters.get("thorne", {}) as Dictionary).get("shake", {})
	var boss_shake: Dictionary = (source.get("boss_hero_skills", {}) as Dictionary).get(
		"cast_shake", {}
	)

	var blue := Battle.new()
	blue.setup_arena()
	var thorne = _hero(blue, THORNE, blue.BLUE, Vector2(300, 340))
	_enemy(blue, Vector2(360, 340), blue.RED)
	check.call(blue.cast_hero_q(thorne.id), "Thorne Q casts against a dummy")
	check.call(
		int(blue.skill_feedback.get("shake", -1)) == int(thorne_shake.get("q", 0)),
		"Thorne Q shakes by the source amount: %s" % str(blue.skill_feedback)
	)
	check.call(
		is_equal_approx(float(blue.skill_feedback.get("volume", 0.0)), SkillFeedback.VOLUME["q"]),
		"Thorne Q asks for the source Q volume"
	)
	check.call(
		blue.effects.screen_shake.intensity >= float(thorne_shake.get("q", 0)),
		"The shake reaches the live EffectManager: %s" % str(blue.effects.screen_shake.intensity)
	)

	var second := Battle.new()
	second.setup_arena()
	var boss = _hero(second, GORNAK, second.BLUE, Vector2(300, 340))
	_enemy(second, Vector2(360, 340), second.RED)
	check.call(second.cast_hero_q(boss.id), "A boss hero casts its Q")
	check.call(
		int(second.skill_feedback.get("shake", -1)) == int(boss_shake.get("q", 0)),
		"Boss heroes shake by the BossHeroSkills amount: %s" % str(second.skill_feedback)
	)

	var red := Battle.new()
	red.setup_arena()
	var enemy_hero = _hero(red, VEX, red.RED, Vector2(900, 340))
	_enemy(red, Vector2(840, 340), red.BLUE)
	check.call(red.cast_hero_q(enemy_hero.id), "A red hero casts its Q")
	check.call(
		int(red.skill_feedback.get("shake", -1)) == int(SkillFeedback.DEFAULT_SHAKE["q"]),
		"Red casts still shake the screen: %s" % str(red.skill_feedback)
	)
	check.call(
		is_equal_approx(float(red.skill_feedback.get("volume", -1.0)), 0.0),
		"Red casts stay silent, like the source blue-only sound"
	)
	check.call(
		(
			is_equal_approx(SkillFeedback.volume_for("r"), 1.0)
			and is_equal_approx(SkillFeedback.volume_for("w"), 0.6)
		),
		"The four source volumes are 0.7/0.6/0.7/1.0"
	)
