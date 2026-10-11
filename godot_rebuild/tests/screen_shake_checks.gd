extends RefCounted
## Replays the `_render.py::ScreenShake` source oracle fixture through the
## native port. The intensity decay is fully deterministic; `get_offset()`
## draws from an RNG, so the suite asserts the real invariant instead of
## exact values: both components are integers inside +/- int(intensity).

const ScreenShake = preload("res://scripts/ui/screen_shake.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/screen_shake_source.json"


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Screen shake fixture parses")
	if not (data is Dictionary):
		return
	check.call(
		is_equal_approx(float(data["decay"]), ScreenShake.DECAY), "Shake decay matches source"
	)
	for entry in data["cases"]:
		_replay(entry as Dictionary, check)
	_stacking(data, check)
	_offsets(data, check)
	_runtime_wiring(check)


func _replay(entry: Dictionary, check: Callable) -> void:
	var label: String = entry["name"]
	var item := ScreenShake.new()
	item.add_shake(float(entry["shake"]))
	var steps: Array = entry["intensity"]
	for index in range(steps.size()):
		item.update()
		check.call(
			is_equal_approx(item.intensity, float(steps[index])),
			"Intensity matches source step %d: %s" % [index, label]
		)


func _stacking(data: Dictionary, check: Callable) -> void:
	var expected: Dictionary = data["stacking"]
	var item := ScreenShake.new()
	item.add_shake(5.0)
	item.add_shake(12.0)
	check.call(
		is_equal_approx(item.intensity, float(expected["after_bigger"])),
		"add_shake keeps the larger request"
	)
	item.add_shake(3.0)
	check.call(
		is_equal_approx(item.intensity, float(expected["after_smaller"])),
		"A smaller request never lowers the shake"
	)
	var disabled := ScreenShake.new()
	disabled.enabled = false
	disabled.add_shake(9.0)
	check.call(
		is_equal_approx(disabled.intensity, float(data["disabled_intensity"])),
		"A disabled shake stays flat"
	)
	check.call(disabled.get_offset() == Vector2i.ZERO, "A flat shake returns no offset")


func _offsets(data: Dictionary, check: Callable) -> void:
	var samples: Array = data["offset_samples"]
	check.call(samples.size() > 0, "Source fixture samples the random offsets")
	for sample in samples:
		var values: Array = sample
		var limit := int(values[2])
		check.call(
			absi(int(values[0])) <= limit and absi(int(values[1])) <= limit,
			"Source offset stays inside the intensity bound"
		)
	for _attempt in range(40):
		var item := ScreenShake.new()
		item.add_shake(12.0)
		item.update()
		var limit := int(item.intensity)
		var offset := item.get_offset()
		check.call(
			absi(offset.x) <= limit and absi(offset.y) <= limit,
			"Native offset stays inside the intensity bound"
		)


func _runtime_wiring(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	check.call(
		world.current_screen_shake_offset() == Vector2.ZERO,
		"Idle world returns zero screen shake offset"
	)
	world.effects.shake_screen(10.0)
	var limit: int = int(world.effects.screen_shake.intensity)
	var sample_offset: Vector2 = world.current_screen_shake_offset()
	check.call(
		(
			limit == 10
			and absf(sample_offset.x) <= float(limit)
			and absf(sample_offset.y) <= float(limit)
			and is_equal_approx(sample_offset.x, roundf(sample_offset.x))
			and is_equal_approx(sample_offset.y, roundf(sample_offset.y))
		),
		"Prototype.current_screen_shake_offset delegates to EffectManager.screen_shake"
	)
	var session := PrototypeSession.new()
	session.world = world
	var view := PrototypeView.new()
	view.session = session
	check.call(
		bool(view.overlay_draw_summary().get("screen_shake_active", false)),
		"PrototypeView.overlay_draw_summary reports active screen shake"
	)
	world.boss_screen_shake_intensity = 20.0
	world.boss_screen_shake_timer = 8
	world.tick_count = 3
	check.call(
		world.current_screen_shake_offset().is_equal_approx(world.boss_presentation_offset()),
		"Prototype.current_screen_shake_offset preserves 8-tick boss presentation offset gate"
	)
	world.boss_screen_shake_timer = 0
	world.boss_screen_shake_intensity = 0.0
	for _step in range(30):
		world._step_combo_clock()
	check.call(
		(
			is_equal_approx(world.effects.screen_shake.intensity, 0.0)
			and world.current_screen_shake_offset() == Vector2.ZERO
			and not bool(view.overlay_draw_summary().get("screen_shake_active", true))
		),
		"ScreenShake decays to zero across Prototype._step_combo_clock updates"
	)
	view.free()
	session.free()
