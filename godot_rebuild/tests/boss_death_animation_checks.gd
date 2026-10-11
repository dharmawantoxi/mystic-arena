# gdlint:disable=max-file-lines
extends RefCounted
## Replays `_render.py::BossDeathAnimation` state through the native port.
## The source oracle executes the original draw under shims and records draw
## locals; no pygame drawing is reproduced here.

const BossDeathAnimation = preload("res://scripts/ui/boss_death_animation.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const FIXTURE := "res://tests/fixtures/boss_death_animation_source.json"
const KEY_BY_NAME := {"space": KEY_SPACE, "escape": KEY_ESCAPE, "letter": KEY_A}


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Boss death animation fixture parses")
	if not (parsed is Dictionary):
		return
	var data: Dictionary = parsed
	var constants: Dictionary = data["constants"]
	check.call(
		(
			int(constants["true_duration"]) == BossDeathAnimation.TRUE_DURATION
			and int(constants["mini_duration"]) == BossDeathAnimation.MINI_DURATION
		),
		"Boss death tier durations match source"
	)
	check.call(
		int(constants["celebration_duration"]) == BossDeathAnimation.CELEBRATION_DURATION,
		"Boss death celebration duration matches source"
	)
	for case_value in data["cases"]:
		_replay_case(case_value as Dictionary, check)
	for case_name in data["skip_cases"]:
		_check_skips(String(case_name), data["skip_cases"][case_name] as Array, data, check)
	_random_branches(check)
	_check_runtime_wiring(check)


func _replay_case(case_data: Dictionary, check: Callable) -> void:
	var config: Dictionary = case_data["config"]
	var animation := BossDeathAnimation.new()
	animation.configure(
		config,
		int(1280),
		int(720),
		case_data["fragment_specs"] as Array,
		case_data["rising_specs"] as Array
	)
	var label: String = String(case_data["name"])
	check.call(
		animation.get_fragment_count() == (case_data["fragment_specs"] as Array).size(),
		"Fragment count matches source: %s" % label
	)
	check.call(
		animation.get_rising_particle_count() == (case_data["rising_specs"] as Array).size(),
		"Rising particle count matches source: %s" % label
	)
	_check_config(animation, case_data, check, label)
	for index in range(animation.get_fragment_count()):
		_compare_fragment(
			animation.get_fragment_snapshot(index),
			case_data["fragment_specs"][index] as Dictionary,
			check,
			label,
			index
		)
	for index in range(animation.get_rising_particle_count()):
		_compare_rising(
			animation.get_rising_particle_snapshot(index),
			case_data["rising_specs"][index] as Dictionary,
			check,
			label,
			index
		)

	var current_tick := 0
	for snapshot_value in case_data["snapshots"]:
		var snapshot: Dictionary = snapshot_value
		var target_tick: int = int(snapshot["tick"])
		while current_tick < target_tick:
			animation.update()
			current_tick += 1
		_check_snapshot(animation, snapshot, check, label)


func _check_config(animation, case_data: Dictionary, check: Callable, label: String) -> void:
	var config: Dictionary = case_data["config"]
	var state: Dictionary = animation.get_state()
	var is_true: bool = String(config["boss_class"]) == "true"
	check.call(
		(
			int(state["duration"]) == (90 if is_true else 60)
			and bool(state["show_celebration"]) == is_true
		),
		"Boss tier state matches source: %s" % label
	)
	var waves: Array = animation.get_explosion_waves()
	check.call(
		waves.size() == (3 if is_true else 2), "Explosion wave count matches source: %s" % label
	)
	check.call(
		(
			animation.boss_name == String(config["name"])
			and animation.boss_title == String(config["title"])
			and is_equal_approx(animation.boss_radius, float(config["radius"]))
		),
		"Cached boss data matches source: %s" % label
	)


func _check_snapshot(animation, expected: Dictionary, check: Callable, label: String) -> void:
	var state: Dictionary = animation.get_state()
	check.call(
		(
			bool(state["active"]) == bool(expected["active"])
			and int(state["timer"]) == int(expected["timer"])
			and int(state["celebration_timer"]) == int(expected["celebration_timer"])
			and bool(state["celebration_active"]) == bool(expected["celebration_active"])
			and bool(state["sound_played"]) == bool(expected["sound_played"])
		),
		"Animation timeline matches source at tick %d: %s" % [int(expected["tick"]), label]
	)
	check.call(
		(
			(
				animation.is_active()
				== (bool(expected["active"]) or bool(expected["celebration_active"]))
			)
			and animation.is_death_active() == bool(expected["active"])
		),
		"Animation activity getters match source at tick %d: %s" % [int(expected["tick"]), label]
	)
	check.call(
		(
			animation.get_fragment_count() == int(expected["fragment_count"])
			and animation.get_rising_particle_count() == int(expected["rising_particle_count"])
		),
		"Particle retention matches source at tick %d: %s" % [int(expected["tick"]), label]
	)
	var first_fragment: Variant = expected.get("first_fragment", null)
	if first_fragment != null:
		_compare_fragment(
			animation.get_fragment_snapshot(0),
			first_fragment as Dictionary,
			check,
			"%s first fragment tick %d" % [label, int(expected["tick"])],
			0,
			false
		)
		_compare_fragment(
			animation.get_fragment_snapshot(animation.get_fragment_count() - 1),
			expected["last_fragment"] as Dictionary,
			check,
			"%s last fragment tick %d" % [label, int(expected["tick"])],
			animation.get_fragment_count() - 1,
			false
		)
	var first_rising: Variant = expected.get("first_rising", null)
	if first_rising != null:
		_compare_rising(
			animation.get_rising_particle_snapshot(0),
			first_rising as Dictionary,
			check,
			"%s first rising tick %d" % [label, int(expected["tick"])],
			0,
			false
		)
		_compare_rising(
			animation.get_rising_particle_snapshot(animation.get_rising_particle_count() - 1),
			expected["last_rising"] as Dictionary,
			check,
			"%s last rising tick %d" % [label, int(expected["tick"])],
			animation.get_rising_particle_count() - 1,
			false
		)
	_check_draw_state(animation, expected.get("draw", null), check, label, int(expected["tick"]))


func _check_draw_state(
	animation, expected_value: Variant, check: Callable, label: String, tick: int
) -> void:
	var draw_state: Dictionary
	if animation.is_death_active():
		draw_state = animation.get_death_visual_state()
		var source_container: Variant = expected_value
		var source_death: Variant = null
		if source_container is Dictionary:
			source_death = (source_container as Dictionary).get("death", null)
		if source_death == null:
			check.call(false, "Source death draw trace exists at tick %d: %s" % [tick, label])
			return
		var source: Dictionary = source_death
		check.call(
			(
				int(draw_state["elapsed"]) == int(source["elapsed"])
				and is_equal_approx(float(draw_state["progress"]), float(source["progress"]))
			),
			"Death draw timing locals match source at tick %d: %s" % [tick, label]
		)
		check.call(
			int(draw_state["flash_alpha"]) == int(source.get("flash_alpha", 0)),
			"Death flash local matches source at tick %d: %s" % [tick, label]
		)
		var body_expected := source.has("dissolve_size")
		check.call(
			bool(draw_state["body_visible"]) == body_expected,
			"Death dissolve visibility matches source at tick %d: %s" % [tick, label]
		)
		if body_expected:
			check.call(
				(
					int(draw_state["dissolve_alpha"]) == int(source["dissolve_alpha"])
					and int(draw_state["dissolve_size"]) == int(source["dissolve_size"])
				),
				"Death dissolve locals match source at tick %d: %s" % [tick, label]
			)
		var source_waves: Array = source.get("waves", [])
		var got_waves: Array = draw_state["waves"]
		check.call(
			got_waves.size() == source_waves.size(),
			"Death wave count matches source at tick %d: %s" % [tick, label]
		)
		for index in range(mini(got_waves.size(), source_waves.size())):
			var got_wave: Dictionary = got_waves[index]
			var source_wave: Dictionary = source_waves[index]
			check.call(
				(
					int(got_wave["radius"]) == int(source_wave["radius"])
					and int(got_wave["alpha"]) == int(source_wave["alpha"])
					and is_equal_approx(
						float(got_wave["wave_progress"]), float(source_wave["wave_progress"])
					)
				),
				"Death wave locals match source at tick %d #%d: %s" % [tick, index, label]
			)
	else:
		draw_state = animation.get_celebration_visual_state(0)
		var source_container: Variant = expected_value
		var source_celebration: Variant = null
		if source_container is Dictionary:
			source_celebration = (source_container as Dictionary).get("celebration", null)
		if source_celebration == null:
			check.call(
				not bool(draw_state.get("visible", false)), "Celebration draw is absent: %s" % label
			)
			return
		var source: Dictionary = source_celebration
		check.call(
			(
				bool(draw_state["visible"])
				and int(draw_state["overlay_alpha"]) == int(source["overlay_alpha"])
				and int(draw_state["text_alpha"]) == int(source["text_alpha"])
				and int(draw_state["text_offset_y"]) == int(source["text_offset_y"])
			),
			"Celebration draw locals match source at tick %d: %s" % [tick, label]
		)
		if source.has("reward_alpha"):
			check.call(
				int(draw_state["reward_alpha"]) == int(source["reward_alpha"]),
				"Celebration reward local matches source at tick %d: %s" % [tick, label]
			)


func _compare_fragment(
	got: Dictionary,
	expected: Dictionary,
	check: Callable,
	label: String,
	index: int,
	check_color: bool = true
) -> void:
	check.call(
		(
			is_equal_approx(float(got["x"]), float(expected["x"]))
			and is_equal_approx(float(got["y"]), float(expected["y"]))
			and is_equal_approx(float(got["vx"]), float(expected["vx"]))
			and is_equal_approx(float(got["vy"]), float(expected["vy"]))
		),
		"Fragment motion matches source: %s #%d" % [label, index]
	)
	check.call(
		(
			int(got["size"]) == int(expected["size"])
			and int(got["life"]) == int(expected["life"])
			and int(got["max_life"]) == int(expected["max_life"])
		),
		"Fragment lifetime matches source: %s #%d" % [label, index]
	)
	check.call(
		(
			is_equal_approx(float(got["rotation"]), float(expected["rotation"]))
			and is_equal_approx(float(got["rot_speed"]), float(expected["rot_speed"]))
		),
		"Fragment rotation matches source: %s #%d" % [label, index]
	)
	if check_color:
		check.call(
			_same_rgb(got["color"], expected["color"]),
			"Fragment colour matches source: %s #%d" % [label, index]
		)


func _compare_rising(
	got: Dictionary,
	expected: Dictionary,
	check: Callable,
	label: String,
	index: int,
	check_color: bool = true
) -> void:
	check.call(
		(
			is_equal_approx(float(got["x"]), float(expected["x"]))
			and is_equal_approx(float(got["y"]), float(expected["y"]))
			and is_equal_approx(float(got["vx"]), float(expected["vx"]))
			and is_equal_approx(float(got["vy"]), float(expected["vy"]))
		),
		"Rising particle motion matches source: %s #%d" % [label, index]
	)
	check.call(
		(
			int(got["size"]) == int(expected["size"])
			and int(got["life"]) == int(expected["life"])
			and int(got["max_life"]) == int(expected["max_life"])
		),
		"Rising particle lifetime matches source: %s #%d" % [label, index]
	)
	check.call(
		is_equal_approx(float(got["phase"]), float(expected["phase"])),
		"Rising particle phase matches source: %s #%d" % [label, index]
	)
	if check_color:
		check.call(
			_same_rgb(got["color"], expected["color"]),
			"Rising particle colour matches source: %s #%d" % [label, index]
		)


func _check_skips(label: String, rows: Array, _data: Dictionary, check: Callable) -> void:
	for row_value in rows:
		var row: Dictionary = row_value
		var row_label: String = String(row["label"])
		var animation := BossDeathAnimation.new()
		var config := {
			"x": 0.0,
			"y": 0.0,
			"name": "Skip",
			"title": "Test",
			"boss_class": "true" if label == "true" else "mini",
			"color": [180, 90, 80],
			"color_dark": [90, 45, 40],
			"entrance_color": [255, 140, 80],
			"gold_reward": 100,
			"radius": 40.0,
		}
		animation.configure(config, 1280, 720)
		if row_label.begins_with("celebration"):
			for _index in range(animation.duration):
				animation.update()
		var keycode := -1
		if row_label.ends_with("space"):
			keycode = KEY_SPACE
		elif row_label.ends_with("escape"):
			keycode = KEY_ESCAPE
		elif row_label.ends_with("letter"):
			keycode = KEY_A
		var clicked: bool = row_label.ends_with("click")
		var result: bool = animation.handle_skip(keycode, clicked)
		check.call(
			result == bool(row["result"]), "Skip result matches source: %s %s" % [label, row_label]
		)
		check.call(
			(
				animation.active == bool(row["active"])
				and animation.celebration_active == bool(row["celebration_active"])
			),
			"Skip state matches source: %s %s" % [label, row_label]
		)


func _random_branches(check: Callable) -> void:
	var mini := BossDeathAnimation.new()
	(
		mini
		. configure(
			{
				"x": 10.0,
				"y": 20.0,
				"name": "Mini",
				"title": "",
				"boss_class": "mini",
				"color": [180, 90, 80],
				"color_dark": [90, 45, 40],
				"entrance_color": [255, 140, 80],
				"gold_reward": 1,
				"radius": 40.0,
			},
			1280,
			720
		)
	)
	check.call(mini.get_fragment_count() == 15, "Mini boss creates fifteen fragments")
	check.call(mini.get_rising_particle_count() == 15, "Mini boss creates fifteen rising particles")
	_check_random_ranges(mini, false, check)

	var true_boss := BossDeathAnimation.new()
	(
		true_boss
		. configure(
			{
				"x": 10.0,
				"y": 20.0,
				"name": "True",
				"title": "",
				"boss_class": "true",
				"color": [180, 90, 80],
				"color_dark": [90, 45, 40],
				"entrance_color": [255, 140, 80],
				"gold_reward": 1,
				"radius": 60.0,
			},
			1280,
			720
		)
	)
	check.call(true_boss.get_fragment_count() == 25, "True boss creates twenty-five fragments")
	check.call(
		true_boss.get_rising_particle_count() == 30, "True boss creates thirty rising particles"
	)
	_check_random_ranges(true_boss, true, check)


func _check_random_ranges(animation, is_true: bool, check: Callable) -> void:
	for index in range(animation.get_fragment_count()):
		var fragment: Dictionary = animation.get_fragment_snapshot(index)
		check.call(
			(
				int(fragment["size"]) >= 3
				and int(fragment["size"]) <= 8
				and int(fragment["life"]) == 60
			),
			"Random fragment stays in source ranges"
		)
		check.call(
			animation.boss_color == [180, 90, 80] or animation.boss_color_dark == [90, 45, 40],
			"Random branch keeps boss colours"
		)
	for index in range(animation.get_rising_particle_count()):
		var particle: Dictionary = animation.get_rising_particle_snapshot(index)
		check.call(
			(
				int(particle["size"]) >= 2
				and int(particle["size"]) <= 5
				and int(particle["life"]) >= 60
				and int(particle["life"]) <= 100
			),
			"Random rising particle stays in source ranges"
		)
	check.call(
		animation.get_fragment_count() == (25 if is_true else 15),
		"Random fragment tier count matches source"
	)


func _check_runtime_wiring(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	world.set_ai_enabled(false)
	world.ai_hero_control_enabled = false
	check.call(
		world.boss_death == null and not bool(world.boss_death_state().get("active", true)),
		"Prototype starts without an active boss death animation"
	)
	var hero: HeroState = world.blue_hero()
	var mini := world._spawn_boss("gornak")
	check.call(hero != null and mini != null, "Runtime wiring test spawns hero and mini-boss")
	if hero == null or mini == null:
		return
	mini.entrance_timer = 0
	mini.hp = 1.0
	mini.alive = true
	mini.defeated = false
	check.call(
		world._deliver_hit(hero.id, world.BLUE, mini, 99999, "physical", mini.position),
		"Hero lethal hit lands on mini-boss"
	)
	world._process_boss_result()
	var session := PrototypeSession.new()
	session.world = world
	var view := PrototypeView.new()
	view.session = session
	check.call(
		(
			world.boss_death != null
			and world.boss_death.is_death_active()
			and world.boss_death.timer == BossDeathAnimation.MINI_DURATION
			and bool(world.boss_death_state().get("death_active", false))
			and bool(view.overlay_draw_summary().get("boss_death_active", false))
			and int(view.overlay_draw_summary().get("explosions", 0)) >= 1
		),
		"Boss defeat configures BossDeathAnimation on Prototype and PrototypeView summary"
	)
	for _tick in range(BossDeathAnimation.MINI_DURATION):
		world.step_tick()
	check.call(
		(
			not world.boss_death.is_death_active()
			and not world.boss_death.is_active()
			and world.boss_death_pause_ticks == 0
			and not bool(view.overlay_draw_summary().get("boss_death_active", true))
		),
		"Mini-boss death animation completes alongside the 60-tick pause"
	)
	var true_boss := world._spawn_boss("abaddon")
	check.call(true_boss != null, "Runtime wiring test spawns true boss")
	if true_boss == null:
		view.free()
		session.free()
		return
	true_boss.entrance_timer = 0
	true_boss.hp = 1.0
	true_boss.alive = true
	true_boss.defeated = false
	check.call(
		world._deliver_hit(hero.id, world.BLUE, true_boss, 99999, "physical", true_boss.position),
		"Hero lethal hit lands on true boss"
	)
	world._process_boss_result()
	for _tick in range(BossDeathAnimation.TRUE_DURATION):
		world.step_tick()
	check.call(
		(
			not world.boss_death.is_death_active()
			and world.boss_death.celebration_active
			and world.boss_death.celebration_timer == BossDeathAnimation.CELEBRATION_DURATION
		),
		"True-boss death transitions into celebration after the 90-tick pause"
	)
	world.step_tick()
	check.call(
		world.boss_death.celebration_timer == BossDeathAnimation.CELEBRATION_DURATION - 1,
		"Normal gameplay tick advances true-boss celebration timer"
	)
	for _tick in range(65):
		world.step_tick()
	check.call(
		(
			bool(view.overlay_draw_summary().get("boss_celebration_reward_visible", false))
			and bool(view.overlay_draw_summary().get("boss_celebration_hint_visible", false))
		),
		"PrototypeView.overlay_draw_summary exposes celebration reward and skip hint visibility"
	)
	check.call(
		(
			world.skip_boss_death(KEY_SPACE)
			and not world.boss_death.celebration_active
			and not bool(world.boss_death_state().get("active", true))
		),
		"Prototype.skip_boss_death dismisses active true-boss celebration"
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
