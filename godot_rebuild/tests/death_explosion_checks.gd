extends RefCounted
## Replays the source oracle fixture through the state-only DeathExplosion port.
## The source oracle executes the original constructor, update() and draw()
## under shims; this suite never asks the Godot port to draw pygame pixels.

const DeathExplosion = preload("res://scripts/ui/death_explosion.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/death_explosion_source.json"


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Death explosion fixture parses")
	if not (parsed is Dictionary):
		return
	var data: Dictionary = parsed
	check.call(
		int(data["flash_max"]) == DeathExplosion.FLASH_MAX,
		"Death explosion flash duration matches source"
	)
	var cases: Array = data["cases"]
	check.call(cases.size() == 3, "Death explosion fixture covers small, medium and large bursts")
	for case_value in cases:
		_replay(case_value as Dictionary, check)
	_random_branches(check)
	_runtime_view_wiring(check)


func _replay(case_data: Dictionary, check: Callable) -> void:
	var config: Dictionary = case_data["config"]
	var explosion := DeathExplosion.new()
	explosion.configure(
		float(config["x"]),
		float(config["y"]),
		String(config["team"]),
		String(config["size"]),
		case_data["particle_specs"] as Array
	)
	var label: String = String(case_data["name"])
	var specs: Array = case_data["particle_specs"]
	check.call(
		explosion.get_particle_count() == specs.size(), "Particle count matches source: %s" % label
	)
	for index in range(specs.size()):
		_compare_particle(
			explosion.get_particle_snapshot(index), specs[index] as Dictionary, check, label, index
		)

	var snapshots: Array = case_data["snapshots"]
	var current_tick := 0
	for snapshot_value in snapshots:
		var snapshot: Dictionary = snapshot_value
		var target_tick := int(snapshot["tick"])
		while current_tick < target_tick:
			explosion.update()
			current_tick += 1
		_check_snapshot(explosion, snapshot, check, label)


func _compare_particle(
	got: Dictionary, expected: Dictionary, check: Callable, label: String, index: int
) -> void:
	check.call(
		is_equal_approx(float(got["x"]), float(expected.get("x", got["x"]))),
		"Particle x matches source: %s #%d" % [label, index]
	)
	check.call(
		is_equal_approx(float(got["y"]), float(expected.get("y", got["y"]))),
		"Particle y matches source: %s #%d" % [label, index]
	)
	check.call(
		(
			is_equal_approx(float(got["vx"]), float(expected["vx"]))
			and is_equal_approx(float(got["vy"]), float(expected["vy"]))
		),
		"Particle velocity matches source: %s #%d" % [label, index]
	)
	check.call(
		(
			int(got["lifetime"]) == int(expected["lifetime"])
			and int(got["max_lifetime"]) == int(expected.get("max_lifetime", expected["lifetime"]))
		),
		"Particle lifetime matches source: %s #%d" % [label, index]
	)
	check.call(
		int(got["size"]) == int(expected["size"]),
		"Particle size matches source: %s #%d" % [label, index]
	)
	check.call(
		_same_rgb(got["color"], expected["color"]),
		"Particle colour matches source: %s #%d" % [label, index]
	)


func _check_snapshot(explosion, expected: Dictionary, check: Callable, label: String) -> void:
	check.call(
		explosion.get_particle_count() == int(expected["particle_count"]),
		"Particle removal matches source at tick %d: %s" % [int(expected["tick"]), label]
	)
	var flash: Dictionary = explosion.get_flash_state()
	check.call(
		int(flash["timer"]) == int(expected["flash_timer"]),
		"Flash timer matches source at tick %d: %s" % [int(expected["tick"]), label]
	)
	check.call(
		explosion.is_alive() == bool(expected["alive"]),
		"Alive state matches source at tick %d: %s" % [int(expected["tick"]), label]
	)
	var source_flash: Variant = expected.get("draw_flash", null)
	if source_flash is Dictionary:
		check.call(
			is_equal_approx(float(flash["intensity"]), float(source_flash["intensity"])),
			"Flash intensity matches source at tick %d: %s" % [int(expected["tick"]), label]
		)
		check.call(
			int(flash["size"]) == int(source_flash["size"]),
			"Flash size matches source at tick %d: %s" % [int(expected["tick"]), label]
		)
	else:
		check.call(
			int(flash["size"]) == 0,
			"Flash is absent after timer at tick %d: %s" % [int(expected["tick"]), label]
		)

	var first: Variant = expected.get("first", null)
	if first == null:
		check.call(explosion.get_particle_count() == 0, "Source has no first particle: %s" % label)
	else:
		_compare_particle(
			explosion.get_particle_snapshot(0),
			first as Dictionary,
			check,
			"%s first tick %d" % [label, int(expected["tick"])],
			0
		)
		var last_index: int = explosion.get_particle_count() - 1
		_compare_particle(
			explosion.get_particle_snapshot(last_index),
			expected["last"] as Dictionary,
			check,
			"%s last tick %d" % [label, int(expected["tick"])],
			last_index
		)


func _random_branches(check: Callable) -> void:
	var small := DeathExplosion.new()
	small.configure(0.0, 0.0, "blue", "small")
	check.call(small.get_particle_count() == 8, "Small explosion creates eight sparks")
	_check_ranges(small, [[100, 200, 255], [150, 220, 255], [200, 240, 255]], 2, 4, check)

	var medium := DeathExplosion.new()
	medium.configure(0.0, 0.0, "red", "medium")
	check.call(medium.get_particle_count() == 15, "Medium explosion creates fifteen sparks")
	_check_ranges(medium, [[255, 100, 100], [255, 150, 100], [255, 200, 100]], 3, 5, check)

	var fallback := DeathExplosion.new()
	fallback.configure(0.0, 0.0, "other", "boss")
	check.call(fallback.get_particle_count() == 25, "Unknown size takes the large burst branch")
	_check_ranges(fallback, [[255, 100, 100], [255, 150, 100], [255, 200, 100]], 4, 6, check)


func _check_ranges(
	explosion, palette: Array, min_size: int, max_size: int, check: Callable
) -> void:
	for index in range(explosion.get_particle_count()):
		var particle: Dictionary = explosion.get_particle_snapshot(index)
		var speed := Vector2(float(particle["vx"]), float(particle["vy"])).length()
		check.call(
			speed >= 1.5 - 0.00001 and speed <= 4.0 + 0.00001,
			"Random spark speed stays in source range"
		)
		check.call(
			int(particle["lifetime"]) >= 20 and int(particle["lifetime"]) <= 35,
			"Random spark lifetime stays in source range"
		)
		check.call(
			int(particle["size"]) >= min_size and int(particle["size"]) <= max_size,
			"Random spark size stays in source range"
		)
		check.call(palette.has(particle["color"]), "Random spark colour stays in source palette")


func _runtime_view_wiring(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var session := PrototypeSession.new()
	session.world = world
	var view := PrototypeView.new()
	view.session = session
	check.call(
		int(view.overlay_draw_summary().get("explosions", -1)) == 0,
		"PrototypeView.overlay_draw_summary starts with zero explosions"
	)
	var minion := world.spawn_minion(world.SOLDIER, world.RED, 1, Vector2(400.0, 360.0))
	world._on_death(world.BLUE, minion)
	check.call(
		int(view.overlay_draw_summary().get("explosions", 0)) == 1,
		"Prototype._on_death populates DeathExplosion in PrototypeView.overlay_draw_summary"
	)
	for _step in range(40):
		world._step_combo_clock()
	check.call(
		int(view.overlay_draw_summary().get("explosions", -1)) == 0,
		"DeathExplosion retires from PrototypeView.overlay_draw_summary after spark lifetime"
	)
	view.free()
	session.free()


func _same_rgb(got: Variant, expected: Variant) -> bool:
	if not (got is Array) or not (expected is Array):
		return false
	var got_rgb: Array = got
	var expected_rgb: Array = expected
	if got_rgb.size() < 3 or expected_rgb.size() < 3:
		return false
	return (
		int(got_rgb[0]) == int(expected_rgb[0])
		and int(got_rgb[1]) == int(expected_rgb[1])
		and int(got_rgb[2]) == int(expected_rgb[2])
	)
