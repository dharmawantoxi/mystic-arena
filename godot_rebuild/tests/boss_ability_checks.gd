# gdlint:disable=max-file-lines,max-line-length
extends RefCounted
## Layer 8d native suite: source ability casts and smart-AI dispatch.
## The fixture is produced by executing the original Boss methods; these checks
## replay the same first-slice cases through BossAI and the live combat hit path.

const BossAI = preload("res://scripts/match/boss_ai.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const THORNE = preload("res://data/heroes/thorne.tres")
const FIXTURE := "res://tests/fixtures/boss_ability_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("cases"), "boss ability fixture parses")
	if not fixture is Dictionary or not fixture.has("cases"):
		return
	var cases: Array = fixture["cases"]
	check.call(cases.size() == 67, "boss ability fixture has all first-slice cases")
	_case(check, cases, "gornak_q", "gornak", 1.0, [[80, 0, 10000, "target"]], 80.0)
	_case(check, cases, "gornak_blink", "gornak", 1.0, [[200, 0, 10000, "target"]], 200.0)
	_case(
		check,
		cases,
		"gornak_counterspell",
		"gornak",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "gornak_mana_void", "gornak", 0.3, [[20, 0, 10000, "target"]], 20.0)
	_case(check, cases, "morgath_spark", "morgath", 1.0, [[330, 0, 10000, "target"]], 330.0)
	_case(check, cases, "morgath_flux", "morgath", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(
		check,
		cases,
		"morgath_field",
		"morgath",
		1.0,
		[[20, 0, 10000, "a"], [30, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "morgath_clones", "morgath", 0.4, [[20, 0, 10000, "target"]], 20.0)
	_persistent_flux(check, cases)
	_case(check, cases, "drakar_rage", "drakar", 0.3, [[200, 0, 10000, "target"]], 200.0)
	_case(
		check,
		cases,
		"drakar_counter_helix",
		"drakar",
		1.0,
		[[20, 0, 10000, "a"], [30, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "drakar_call", "drakar", 0.5, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "drakar_culling", "drakar", 1.0, [[50, 0, 1000, "target", 10000]], 50.0)
	_case(check, cases, "abaddon_coil", "abaddon", 1.0, [[100, 0, 10000, "target"]], 100.0)
	# The source fixture isolates _smart_ai_abaddon. The live Boss.update heal
	# runs before that method, so hold its cooldown here to replay the cast.
	_case(check, cases, "abaddon_shield", "abaddon", 0.2, [[20, 0, 10000, "target"]], 20.0, true)
	_case(check, cases, "abaddon_gale", "abaddon", 1.0, [[200, 0, 10000, "target"]], 200.0)
	_case(
		check,
		cases,
		"abaddon_death_sever",
		"abaddon",
		1.0,
		[[20, 0, 10000, "a"], [30, 0, 10000, "b"], [40, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"alchemist_greevils_greed",
		"alchemist",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"alchemist_chemical_rage",
		"alchemist",
		0.5,
		[[300, 0, 10000, "target"]],
		300.0
	)
	_case(
		check,
		cases,
		"alchemist_unstable_concoction",
		"alchemist",
		1.0,
		[[100, 0, 10000, "a"], [150, 0, 10000, "b"]],
		100.0
	)
	_case(
		check, cases, "alchemist_acid_spray", "alchemist", 1.0, [[100, 0, 10000, "target"]], 100.0
	)
	_case(
		check,
		cases,
		"malzareth_death_pulse",
		"malzareth",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"malzareth_shadow_word",
		"malzareth",
		1.0,
		[[100, 0, 10000, "target"], [140, 0, 10000, "splash"]],
		100.0
	)
	_case(
		check, cases, "malzareth_nether_blast", "malzareth", 1.0, [[100, 0, 10000, "target"]], 100.0
	)
	_case(check, cases, "malzareth_void", "malzareth", 1.0, [[270, 0, 10000, "target"]], 270.0)
	_case(
		check,
		cases,
		"akashari_sonic_scream",
		"akashari",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"akashari_scream_of_pain",
		"akashari",
		1.0,
		[[100, 0, 10000, "a"], [120, 0, 10000, "b"], [140, 0, 10000, "c"]],
		100.0
	)
	_case(
		check,
		cases,
		"akashari_shadow_strike",
		"akashari",
		0.5,
		[[200, 0, 10000, "target"], [220, 0, 10000, "near"]],
		200.0
	)
	_case(check, cases, "akashari_scream", "akashari", 1.0, [[270, 0, 10000, "target"]], 270.0)
	_case(
		check,
		cases,
		"vorenmarr_chaos_storm",
		"vorenmarr",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check, cases, "vorenmarr_shadow_word", "vorenmarr", 0.5, [[300, 0, 10000, "target"]], 300.0
	)
	_case(
		check,
		cases,
		"vorenmarr_rain_of_fire",
		"vorenmarr",
		1.0,
		[[100, 0, 10000, "target"], [150, 0, 10000, "near"]],
		100.0
	)
	_case(
		check, cases, "vorenmarr_chaos_bolt", "vorenmarr", 1.0, [[270, 0, 10000, "target"]], 270.0
	)
	_case(
		check,
		cases,
		"nyxarath_requiem",
		"nyxarath",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "nyxarath_presence", "nyxarath", 0.5, [[300, 0, 10000, "target"]], 300.0)
	_case(
		check,
		cases,
		"nyxarath_necromastery",
		"nyxarath",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "nyxarath_shadowraze", "nyxarath", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(
		check,
		cases,
		"thalgryn_replicate",
		"thalgryn",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "thalgryn_morph", "thalgryn", 0.5, [[300, 0, 10000, "target"]], 300.0)
	_case(
		check,
		cases,
		"thalgryn_waveform",
		"thalgryn",
		1.0,
		[[300, 0, 10000, "target"], [100, 0, 10000, "path"]],
		300.0
	)
	_case(
		check,
		cases,
		"thalgryn_adaptive_strike",
		"thalgryn",
		1.0,
		[[100, 0, 10000, "target"], [150, 0, 10000, "splash"]],
		100.0
	)
	_case(
		check,
		cases,
		"syrentha_song_of_siren",
		"syrentha",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check, cases, "syrentha_mirror_image", "syrentha", 0.5, [[300, 0, 10000, "target"]], 300.0
	)
	_case(
		check,
		cases,
		"syrentha_enchanting_song",
		"syrentha",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"syrentha_riptide",
		"syrentha",
		1.0,
		[[100, 0, 10000, "target"], [150, 50, 10000, "splash"]],
		100.0
	)
	_case(
		check,
		cases,
		"gravewake_ravage",
		"gravewake",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check, cases, "gravewake_kraken_shell", "gravewake", 0.5, [[300, 0, 10000, "target"]], 300.0
	)
	_case(
		check,
		cases,
		"gravewake_tidebringer",
		"gravewake",
		1.0,
		[[100, 0, 10000, "target"], [150, 60, 10000, "near"], [300, 0, 10000, "far"]],
		100.0
	)
	_case(
		check,
		cases,
		"gravewake_anchor_smash",
		"gravewake",
		1.0,
		[[100, 0, 10000, "target"], [190, 0, 10000, "wave"]],
		100.0
	)
	_case(
		check,
		cases,
		"kunkka_torrent",
		"kunkka",
		0.35,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"kunkka_ghost_ship",
		"kunkka",
		0.5,
		[[250, 0, 10000, "target"], [200, 100, 10000, "off_path"]],
		250.0
	)
	_case(
		check,
		cases,
		"kunkka_x_marks",
		"kunkka",
		1.0,
		[[100, 0, 10000, "target"], [150, 60, 10000, "near"]],
		100.0
	)
	_case(
		check,
		cases,
		"kunkka_tide_bringer",
		"kunkka",
		1.0,
		[[100, 0, 10000, "target"], [240, 0, 10000, "wave"]],
		100.0
	)
	# The X Marks the Spot burst lands on a later tick, so hold every cooldown
	# and expire the mark, mirroring the Morgath flux tick case.
	_case(
		check,
		cases,
		"kunkka_x_mark_burst",
		"kunkka",
		1.0,
		[[60, 0, 10000, "marked"], [150, 0, 10000, "near"], [400, 0, 10000, "far"]],
		60.0
	)
	_case(
		check,
		cases,
		"razak_firestorm",
		"razak",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"razak_firefly",
		"razak",
		1.0,
		[[200, 0, 10000, "target"], [60, 0, 10000, "near"]],
		200.0
	)
	_case(
		check,
		cases,
		"razak_flame_cone",
		"razak",
		1.0,
		[[100, 0, 10000, "target"], [150, 40, 10000, "near"]],
		100.0
	)
	_case(
		check,
		cases,
		"razak_molotov",
		"razak",
		1.0,
		[[260, 0, 10000, "target"], [100, 0, 10000, "near"], [300, 40, 10000, "splash"]],
		260.0
	)
	_case(
		check,
		cases,
		"kenshiro_supremacy",
		"kenshiro",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "kenshiro_assault", "kenshiro", 0.5, [[200, 0, 10000, "target"]], 200.0)
	_case(
		check,
		cases,
		"kenshiro_gale",
		"kenshiro",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "kenshiro_swiftslash", "kenshiro", 1.0, [[80, 0, 10000, "target"]], 80.0)
	_case(
		check,
		cases,
		"khazan_vanishing_execution",
		"khazan",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"khazan_spin_carnage",
		"khazan",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "khazan_leap_smash", "khazan", 1.0, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "khazan_chained_blade", "khazan", 1.0, [[80, 0, 10000, "target"]], 80.0)
	_generic(check, cases)
	_true_boss_heal(check)


func _world(kind: String, hp_ratio: float) -> Array:
	var world := Prototype.new()
	world.setup_arena()
	var boss := world._spawn_boss(kind)
	boss.position = Vector2.ZERO
	boss.previous_position = boss.position
	boss.hp = float(int(float(boss.max_hp) * hp_ratio))
	return [world, boss]


func _target(world: Prototype, spec: Array) -> HeroState:
	var target := world.spawn_hero(THORNE, world.BLUE, Vector2(float(spec[0]), float(spec[1])))
	target.max_hp = float(int(spec[4]) if spec.size() > 4 else int(spec[2]))
	target.hp = float(int(spec[2]))
	target.alive = target.hp > 0.0
	target.attack_timer = 0
	return target


func _case(
	check: Callable,
	cases: Array,
	label: String,
	kind: String,
	hp_ratio: float,
	specs: Array,
	distance: float,
	hold_true_heal: bool = false
) -> void:
	var expected := _fixture_case(cases, label)
	check.call(not expected.is_empty(), "%s fixture row exists" % label)
	if expected.is_empty():
		return
	var pair := _world(kind, hp_ratio)
	var world: Prototype = pair[0]
	var boss = pair[1]
	var enemies: Array[UnitState] = []
	for spec in specs:
		var target := _target(world, spec)
		enemies.append(target)
	if hold_true_heal:
		boss.ability2_timer = 999
	if label == "morgath_flux_tick":
		boss.q_timer = 999
		boss.w_timer = 999
		boss.e_timer = 999
		boss.r_timer = 999
		boss.flux_target_id = enemies[0].id
		boss.flux_active_timer = 31
	if label == "kunkka_x_mark_burst":
		boss.q_timer = 999
		boss.w_timer = 999
		boss.e_timer = 999
		boss.r_timer = 999
		boss.x_mark_target_id = enemies[0].id
		boss.x_mark_timer = 1
	BossAI.tick(world, boss, enemies, enemies[0], distance)
	_compare(check, expected["result"], boss, enemies)


func _persistent_flux(check: Callable, cases: Array) -> void:
	_case(check, cases, "morgath_flux_tick", "morgath", 1.0, [[400, 0, 10000, "flux"]], 400.0)


func _generic(check: Callable, cases: Array) -> void:
	var expected := _fixture_case(cases, "generic_ability")
	var pair := _world("abaddon", 1.0)
	var world: Prototype = pair[0]
	var boss = pair[1]
	boss.ability_cooldown = 180
	boss.ability_damage_value = 270
	boss.ability_range = 50.0
	boss.ability_timer = 0
	var enemies: Array[UnitState] = []
	for spec in [[20, 0, 10000, "near"], [100, 0, 10000, "far"]]:
		enemies.append(_target(world, spec))
	BossAI._generic(world, boss, enemies)
	_compare(check, expected["result"], boss, enemies)
	check.call(boss.ability_active_timer == 60, "generic ability active window is sixty ticks")


func _true_boss_heal(check: Callable) -> void:
	var pair := _world("abaddon", 0.2)
	var world: Prototype = pair[0]
	var boss = pair[1]
	var enemies: Array[UnitState] = [_target(world, [200, 0, 10000, "target"])]
	BossAI.tick(world, boss, enemies, enemies[0], 200.0)
	check.call(boss.hp == 18000.0, "true boss heal uses source percentage")
	check.call(boss.ability2_timer == boss.ability2_cooldown, "true boss heal starts cooldown")
	check.call(boss.active_skill == "e", "true boss heals before smart ability selection")


func _fixture_case(cases: Array, label: String) -> Dictionary:
	for entry in cases:
		if String(entry.get("label", "")) == label:
			return entry
	return {}


func _compare(check: Callable, expected: Dictionary, boss, enemies: Array[UnitState]) -> void:
	var expected_skill: Variant = expected.get("skill", null)
	var actual_skill: Variant = boss.active_skill if not boss.active_skill.is_empty() else null
	check.call(actual_skill == expected_skill, "%s active skill" % expected["type"])
	check.call(
		boss.active_skill_timer == int(expected["active_skill_timer"]),
		"%s active skill timer" % expected["type"]
	)
	for field in [
		"q_timer",
		"w_timer",
		"e_timer",
		"r_timer",
		"ability_timer",
		"hp",
		"damage",
		"rage_timer",
		"necro_buff_timer",
		"presence_timer",
		"morph_buff_timer",
		"mirror_buff_timer",
		"shell_timer",
		"rum_buff_timer",
		"x_mark_timer",
		"defense_timer",
		"flux_active_timer",
		"clones_active_timer"
	]:
		var actual: Variant = boss.hp if field == "hp" else boss.get(field)
		check.call(int(actual) == int(expected[field]), "%s %s" % [expected["type"], field])
	check.call(
		boss.ability_active == bool(expected["ability_active"]),
		"%s generic active flag" % expected["type"]
	)
	check.call(
		(
			is_equal_approx(boss.position.x, float(expected["x"]))
			and is_equal_approx(boss.position.y, float(expected["y"]))
		),
		"%s position" % expected["type"]
	)
	check.call(boss.rage_active == bool(expected["rage_active"]), "rage flag")
	check.call(boss.necro_buff_active == bool(expected["necro_buff_active"]), "necromastery flag")
	check.call(boss.presence_active == bool(expected["presence_active"]), "presence flag")
	check.call(boss.morph_buff_active == bool(expected["morph_buff_active"]), "morph flag")
	check.call(boss.mirror_buff_active == bool(expected["mirror_buff_active"]), "mirror flag")
	check.call(boss.shell_active == bool(expected["shell_active"]), "kraken shell flag")
	check.call(boss.rum_buff_active == bool(expected["rum_buff_active"]), "rum buff flag")
	check.call(boss.defense_boost == bool(expected["defense_boost"]), "defense flag")
	var expected_targets: Array = expected["targets"]
	check.call(enemies.size() == expected_targets.size(), "target count")
	for index in range(mini(enemies.size(), expected_targets.size())):
		var target := enemies[index] as HeroState
		var row: Dictionary = expected_targets[index]
		var expected_hits: Array = row["hits"]
		var start_hp := 10000
		if row["name"] == "target" and expected["type"] == "drakar" and row["hp"] == 0:
			start_hp = 1000
		check.call(target.hp == float(row["hp"]), "%s target hp" % row["name"])
		check.call(target.alive == bool(row["alive"]), "%s target alive" % row["name"])
		var damage_taken := start_hp - int(target.hp)
		var expected_damage := 0
		for hit in expected_hits:
			expected_damage += int(hit)
		check.call(
			damage_taken == mini(start_hp, expected_damage), "%s target damage" % row["name"]
		)
		check.call(target.attack_timer == int(row["attack_timer"]), "%s attack lock" % row["name"])
		var slows: Array = row["slows"]
		if slows.is_empty():
			check.call(target.slow_timer == 0, "%s has no slow" % row["name"])
		else:
			check.call(
				(
					is_equal_approx(target.slow_amount, float(slows[0][0]))
					and target.slow_timer == int(slows[0][1])
				),
				"%s slow" % row["name"]
			)
