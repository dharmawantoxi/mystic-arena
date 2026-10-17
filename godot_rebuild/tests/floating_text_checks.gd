extends RefCounted
## Replays the `_render.py::FloatingText` source oracle fixture through the
## native port. `floating_text_source_oracle.py` executes the real source
## class to build the fixture, so these numbers are not hand-written.

const FloatingText = preload("res://scripts/ui/floating_text.gd")
const FIXTURE := "res://tests/fixtures/floating_text_source.json"


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Floating text fixture parses")
	if not (data is Dictionary):
		return
	var cases: Array = data["cases"]
	check.call(cases.size() == 3, "Source fixture covers the sampled cases")
	for entry in cases:
		_replay(entry as Dictionary, check)
	_defaults(check)


func _replay(entry: Dictionary, check: Callable) -> void:
	var label: String = entry["name"]
	var config: Dictionary = entry["config"]
	var velocity: Array = config["velocity"]
	var tint: Array = config["color"]
	var item := FloatingText.new()
	item.configure(
		float(config["x"]),
		float(config["y"]),
		String(config["text"]),
		Color8(int(tint[0]), int(tint[1]), int(tint[2])),
		String(config["size"]),
		Vector2(float(velocity[0]), float(velocity[1])),
		int(config["lifetime"]),
		bool(config["critical"]),
		float(entry["x_drift"])
	)
	check.call(item.font_size == int(entry["font_size"]), "Font size matches source: %s" % label)
	check.call(
		is_equal_approx(item.x_drift, float(entry["x_drift"])), "Drift is pinned: %s" % label
	)
	var draw_by_tick := {}
	for sample_value in entry["draw_samples"]:
		var sample: Dictionary = sample_value
		draw_by_tick[int(sample["tick"])] = sample["blits"]
	var steps: Array = entry["steps"]
	for index in range(steps.size()):
		item.update()
		var expected: Array = steps[index]
		check.call(
			(
				is_equal_approx(item.x, float(expected[0]))
				and is_equal_approx(item.y, float(expected[1]))
				and is_equal_approx(item.velocity_y, float(expected[2]))
				and is_equal_approx(item.scale, float(expected[3]))
			),
			"Motion matches source step %d: %s" % [index, label]
		)
		check.call(
			item.lifetime == int(expected[4]), "Lifetime matches step %d: %s" % [index, label]
		)
		check.call(
			item.alive == (int(expected[5]) == 1), "Alive matches step %d: %s" % [index, label]
		)
		check.call(item.alpha() == int(expected[6]), "Alpha matches step %d: %s" % [index, label])
		if draw_by_tick.has(index) and not _visual_matches(item, draw_by_tick[index]):
			check.call(false, "Source draw commands differ at tick %d: %s" % [index, label])
			return


func _visual_matches(item, expected_blits: Array) -> bool:
	var state: Dictionary = item.presentation_state()
	if expected_blits.is_empty():
		return state.is_empty()
	if expected_blits.size() != 2 or state.is_empty():
		return false
	var shadow: Dictionary = expected_blits[0]
	var foreground: Dictionary = expected_blits[1]
	var center: Array = state["center"]
	var shadow_center: Array = state["shadow_center"]
	return (
		int(state["font_size"]) == int(foreground["font_size"])
		and int(state["alpha"]) == int(foreground["alpha"])
		and int(state["shadow_alpha"]) == int(shadow["alpha"])
		and int(center[0]) == int(foreground["center"][0])
		and int(center[1]) == int(foreground["center"][1])
		and int(shadow_center[0]) == int(shadow["center"][0])
		and int(shadow_center[1]) == int(shadow["center"][1])
		and String(state["text"]) == String(foreground["text"])
		and String(state["style"]) == String(foreground["style"])
		and _int_arrays_match(state["color"], foreground["color"])
		and _int_arrays_match(state["shadow_color"], shadow["color"])
	)


func _int_arrays_match(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size():
		return false
	for index in range(actual.size()):
		if int(actual[index]) != int(expected[index]):
			return false
	return true


## Behaviour the fixture cannot cover because the source draws it from `random`.
func _defaults(check: Callable) -> void:
	var item := FloatingText.new()
	item.configure(0.0, 0.0, "1", Color.WHITE)
	check.call(
		item.x_drift >= -FloatingText.DRIFT_RANGE and item.x_drift <= FloatingText.DRIFT_RANGE,
		"Default drift stays inside the source range"
	)
	check.call(item.font_size == 18, "Unknown size falls back to the medium font")
	check.call(
		FloatingText.font_size_for("huge") == 32 and FloatingText.font_size_for("bogus") == 18,
		"Font size table matches the source"
	)
	item.lifetime = 1
	item.update()
	check.call(not item.alive and item.lifetime == 0, "Last tick retires the number")
	var before := item.y
	item.update()
	check.call(is_equal_approx(item.y, before), "A dead number stops moving")
