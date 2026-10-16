extends RefCounted
## Layer 9am native suite: boss self-buff stat lifecycles replayed through the
## production BossAI - Chemical Rage keeps and compounds its 1.5x damage after
## expiry, and Shukuchi writes/restores speed off the raw catalog value.

const BossAI = preload("res://scripts/match/boss_ai.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const FIXTURE := "res://tests/fixtures/boss_buff_expiry_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("rows"), "buff expiry fixture parses")
	if not fixture is Dictionary:
		return
	_shape_check(check, fixture)
	var shape: Dictionary = fixture.get("shape", {})
	for row in fixture.rows:
		_replay_row(check, row, shape)


func _shape_check(check: Callable, fixture: Dictionary) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	check.call(
		Array(shape.get("rage_expiry_writes", [])) == ["rage_active"],
		"source rage expiry writes only the flag"
	)
	check.call(
		not bool(shape.get("rage_expiry_has_damage_write", true)),
		"source rage expiry never rewrites damage"
	)
	check.call(
		Array(shape.get("shukuchi_expiry_writes", [])) == ["shukuchi_active", "speed"],
		"source shukuchi expiry writes the flag and speed"
	)
	check.call(
		String(shape.get("shukuchi_expiry_speed_segment", "")) == 'stats.get("speed", 1.15)',
		"shukuchi expiry restores the raw catalog speed"
	)
	check.call(
		String(shape.get("q_cast_base_speed_segment", "")) == 'stats.get("speed", 1.15)',
		"shukuchi cast reads the raw catalog speed"
	)
	check.call(
		String(shape.get("q_cast_speed_segment", "")) == "base_speed * 1.8",
		"shukuchi cast multiplies speed by 1.8"
	)
	check.call(
		String(shape.get("rage_cast_damage_segment", "")) == "int(self.damage * 1.5)",
		"rage cast compounds on the current damage"
	)


func _replay_row(check: Callable, row: Dictionary, shape: Dictionary) -> void:
	var label := String(row.get("name", "unknown"))
	var column: Dictionary = row.get("expected", {})
	var input: Dictionary = column.get("input", {})
	var output: Dictionary = column.get("output", {})
	var world := Prototype.new()
	world.setup_arena()
	var boss := world._spawn_boss(String(row.get("boss", "")))
	check.call(boss != null, "buff expiry probe spawns: %s" % label)
	if boss == null:
		return
	if String(row.get("boss", "")) == "xirthalis":
		check.call(
			boss.catalog_speed == float(shape.get("catalog_speed_xirthalis", -1.0)),
			"setup snapshots the raw catalog speed"
		)
	_apply(boss, input)
	var enemies: Array[UnitState] = []
	var distance := float(input.get("target_distance", 999.0))
	BossAI._tick_smart_clocks(world, boss, null)
	if String(row.get("arm", "")) == "recipe":
		if String(row.get("boss", "")) == "xirthalis":
			BossAI._xirthalis(world, boss, enemies, null, distance)
		else:
			BossAI._alchemist(world, boss, enemies, null, distance)
	for key in output:
		_compare(check, boss, String(key), output[key], label)
	if bool(row.get("divergent", false)):
		check.call(
			column != row.get("native_old", {}),
			"the source column differs from the pre-9am port: %s" % label
		)
	if label == "xirthalis_shukuchi_expiry":
		check.call(
			boss.speed_px_per_tick == boss.catalog_speed,
			"expiry restores the catalog speed field itself"
		)
		check.call(
			boss.speed_px_per_tick != boss.base_speed,
			"the hard-difficulty base_speed is lost after one cycle, like the source"
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
			"speed":
				boss.speed_px_per_tick = float(value)
			"base_speed":
				boss.base_speed = float(value)
			"q_timer":
				boss.q_timer = int(float(value))
			"w_timer":
				boss.w_timer = int(float(value))
			"e_timer":
				boss.e_timer = int(float(value))
			"r_timer":
				boss.r_timer = int(float(value))
			"rage_active":
				boss.rage_active = bool(value)
			"rage_timer":
				boss.rage_timer = int(float(value))
			"shukuchi_active":
				boss.shukuchi_active = bool(value)
			"shukuchi_timer":
				boss.shukuchi_timer = int(float(value))
			"target_distance":
				pass


func _compare(check: Callable, boss, key: String, expected, label: String) -> void:
	match key:
		"speed":
			check.call(
				boss.speed_px_per_tick == float(expected), "%s: speed follows the source" % label
			)
		"damage":
			check.call(boss.damage == int(expected), "%s: damage follows the source" % label)
		"hp":
			check.call(boss.hp == float(expected), "%s: hp follows the source" % label)
		"rage_active":
			check.call(
				boss.rage_active == bool(expected), "%s: rage flag follows the source" % label
			)
		"shukuchi_active":
			check.call(
				boss.shukuchi_active == bool(expected),
				"%s: shukuchi flag follows the source" % label
			)
		"rage_timer":
			check.call(
				boss.rage_timer == int(expected), "%s: rage timer follows the source" % label
			)
		"shukuchi_timer":
			check.call(
				boss.shukuchi_timer == int(expected),
				"%s: shukuchi timer follows the source" % label
			)
		"q_timer":
			check.call(boss.q_timer == int(expected), "%s: q timer follows the source" % label)
		"e_timer":
			check.call(boss.e_timer == int(expected), "%s: e timer follows the source" % label)
		_:
			check.call(false, "%s: unpinned output key %s" % [label, key])
