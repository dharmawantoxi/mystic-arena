extends RefCounted
## Layer 9an native suite: the four buff damage writes (nyxarath, thalgryn,
## syrentha, kunkka) read the SCALED catalog damage like the source
## `_get_boss_stats()["damage"]` - single-rounded, with skill_down, difficulty
## and enrage multipliers - instead of the difficulty-baked base_damage.

const BossAI = preload("res://scripts/match/boss_ai.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const FIXTURE := "res://tests/fixtures/boss_buff_scaling_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("rows"), "buff scaling fixture parses")
	if not fixture is Dictionary:
		return
	_shape_check(check, fixture)
	var shape: Dictionary = fixture.get("shape", {})
	for row in fixture.rows:
		_replay_row(check, row, shape)


func _shape_check(check: Callable, fixture: Dictionary) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	check.call(
		bool(shape.get("stats_scale_segment", false)),
		"the source scales damage keys with int(round(v * mult))"
	)
	check.call(
		int(shape.get("base_damage_bake_writes", 0)) == 2,
		"the source bakes base_damage at init and at difficulty scaling only"
	)
	var buffs: Dictionary = shape.get("buffs", {})
	for boss in ["nyxarath", "thalgryn", "syrentha", "kunkka"]:
		var pin: Dictionary = buffs.get(boss, {})
		check.call(
			String(pin.get("expiry_damage_segment", "")).begins_with('stats.get("damage"'),
			"%s expiry resets through the scaled stats read" % boss
		)
		check.call(
			String(pin.get("cast_damage_segment", "")).begins_with("int(base_damage *"),
			"%s cast buffs off the scaled stats read" % boss
		)
	var xerathis: Dictionary = shape.get("xerathis", {})
	check.call(
		(
			String(xerathis.get("expiry_damage_segment", "")) == "self.base_damage"
			and String(xerathis.get("cast_damage_segment", "")) == "int(self.base_damage * 1.3)"
		),
		"the xerathis arcane pair stays on the verbatim base_damage attribute"
	)


func _replay_row(check: Callable, row: Dictionary, shape: Dictionary) -> void:
	var label := String(row.get("name", "unknown"))
	var boss_type := String(row.get("boss", ""))
	var column: Dictionary = row.get("expected", {})
	var input: Dictionary = column.get("input", {})
	var output: Dictionary = column.get("output", {})
	var world := Prototype.new()
	world.setup_arena()
	var boss := world._spawn_boss(boss_type)
	check.call(boss != null, "buff scaling probe spawns: %s" % label)
	if boss == null:
		return
	var catalog: Dictionary = shape.get("bosses", {}).get(boss_type, {})
	check.call(
		boss.catalog_damage == int(float(catalog.get("damage", -1))),
		"setup snapshots the raw catalog damage: %s" % label
	)
	_apply(boss, input)
	var enemies: Array[UnitState] = []
	var enemy_count := int(float(input.get("enemy_count", 0)))
	for index in enemy_count:
		var minion: UnitState = world.spawn_unit(GOBLIN, world.RED, 0)
		if minion == null:
			continue
		minion.position = boss.position + Vector2(100.0 if index == 0 else -50.0, 0.0)
		enemies.append(minion)
	check.call(enemies.size() == enemy_count, "buff scaling probe fields enemies: %s" % label)
	var target: UnitState = null
	var distance := float(input.get("target_distance", 999.0))
	if bool(input.get("has_target", false)):
		target = world.spawn_hero(
			Prototype.KAIZEN, world.BLUE, boss.position + Vector2(distance, 0.0)
		)
	match boss_type:
		"nyxarath":
			BossAI._nyxarath(world, boss, enemies, target, distance)
		"thalgryn":
			BossAI._thalgryn(world, boss, enemies, target, distance)
		"syrentha":
			BossAI._syrentha(world, boss, enemies, target, distance)
		"kunkka":
			BossAI._kunkka(world, boss, enemies, target, distance)
		_:
			check.call(false, "%s: unknown boss recipe" % label)
	for key in output:
		_compare(check, boss, String(key), output[key], label)
	if bool(row.get("divergent", false)):
		check.call(
			column != row.get("native_old", {}),
			"the source column differs from the pre-9an port: %s" % label
		)


func _apply(boss, input: Dictionary) -> void:
	for key in input:
		var value = input[key]
		match String(key):
			"hp":
				boss.hp = float(value)
			"max_hp":
				boss.max_hp = int(float(value))
			"damage":
				boss.damage = int(float(value))
			"base_damage":
				boss.base_damage = int(float(value))
			"dmg_scaling_mult":
				boss.dmg_scaling_mult = float(value)
			"is_enraged":
				boss.is_enraged = bool(value)
			"skill_down_timer":
				boss.skill_down_timer = int(float(value))
			"skill_down_amount":
				boss.skill_down_amount = float(value)
			"q_timer":
				boss.q_timer = int(float(value))
			"w_timer":
				boss.w_timer = int(float(value))
			"e_timer":
				boss.e_timer = int(float(value))
			"r_timer":
				boss.r_timer = int(float(value))
			"necro_buff_active":
				boss.necro_buff_active = bool(value)
			"necro_buff_timer":
				boss.necro_buff_timer = int(float(value))
			"morph_buff_active":
				boss.morph_buff_active = bool(value)
			"morph_buff_timer":
				boss.morph_buff_timer = int(float(value))
			"mirror_buff_active":
				boss.mirror_buff_active = bool(value)
			"mirror_buff_timer":
				boss.mirror_buff_timer = int(float(value))
			"rum_buff_active":
				boss.rum_buff_active = bool(value)
			"rum_buff_timer":
				boss.rum_buff_timer = int(float(value))
			"enemy_count", "has_target", "target_distance":
				pass


func _compare(check: Callable, boss, key: String, expected, label: String) -> void:
	match key:
		"damage":
			check.call(boss.damage == int(expected), "%s: damage follows the source" % label)
		"hp":
			check.call(boss.hp == float(expected), "%s: hp follows the source" % label)
		"necro_buff_active":
			check.call(
				boss.necro_buff_active == bool(expected),
				"%s: necro flag follows the source" % label
			)
		"morph_buff_active":
			check.call(
				boss.morph_buff_active == bool(expected),
				"%s: morph flag follows the source" % label
			)
		"mirror_buff_active":
			check.call(
				boss.mirror_buff_active == bool(expected),
				"%s: mirror flag follows the source" % label
			)
		"rum_buff_active":
			check.call(
				boss.rum_buff_active == bool(expected), "%s: rum flag follows the source" % label
			)
		"necro_buff_timer":
			check.call(
				boss.necro_buff_timer == int(expected), "%s: necro timer follows the source" % label
			)
		"morph_buff_timer":
			check.call(
				boss.morph_buff_timer == int(expected), "%s: morph timer follows the source" % label
			)
		"mirror_buff_timer":
			check.call(
				boss.mirror_buff_timer == int(expected),
				"%s: mirror timer follows the source" % label
			)
		"rum_buff_timer":
			check.call(
				boss.rum_buff_timer == int(expected), "%s: rum timer follows the source" % label
			)
		"w_timer":
			check.call(boss.w_timer == int(expected), "%s: w timer follows the source" % label)
		"e_timer":
			check.call(boss.e_timer == int(expected), "%s: e timer follows the source" % label)
		_:
			check.call(false, "%s: unpinned output key %s" % [label, key])
