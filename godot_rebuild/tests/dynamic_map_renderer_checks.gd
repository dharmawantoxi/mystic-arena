extends RefCounted
## Layer 9d0: replay every DynamicRenderer source op and post-update state.

const DynamicMap = preload("res://scripts/ui/dynamic_map_renderer.gd")
const DynamicLayout = preload("res://scripts/ui/dynamic_map_layout.gd")
const FIXTURE := "res://tests/fixtures/dynamic_renderer_source.json"
const PALETTE := "res://data/levels/theme_palette.json"


func run(check: Callable) -> void:
	_check_manifest(check)
	_check_runtime_presets(check)
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Dynamic renderer fixture parses")
	if not (parsed is Dictionary):
		return
	var fixture: Dictionary = parsed
	for case_value in fixture["cases"]:
		_replay_case(case_value as Dictionary, check)
	for case_value in fixture["torch_cases"]:
		_check_torch_case(case_value as Dictionary, check)


func _check_manifest(check: Callable) -> void:
	var manifest := DynamicMap.manifest()
	check.call(not manifest.is_empty(), "Dynamic map manifest parses")
	if manifest.is_empty():
		return
	var palette: Variant = JSON.parse_string(FileAccess.get_file_as_string(PALETTE))
	check.call(palette is Dictionary, "Dynamic map palette still parses")
	if not (palette is Dictionary):
		return
	var expected: Array = (palette as Dictionary).keys()
	expected.sort()
	check.call(DynamicMap.themes() == expected, "Dynamic map covers all 54 palette themes")
	check.call(DynamicMap.themes().size() == 54, "Dynamic map theme count")
	check.call(manifest["layout"]["river_points"].size() == 61, "Source river has 61 points")
	check.call(manifest["layout"]["torch_stones"].size() == 18, "Source border has 18 torches")
	var missing_states: Array = []
	var draw_failures: Array = []
	for theme_name in DynamicMap.themes():
		var entry: Dictionary = manifest["themes"][theme_name]
		for level in ["low", "medium", "high"]:
			if not entry["states"].has(level):
				missing_states.append("%s:%s" % [theme_name, level])
		var renderer := DynamicMap.new()
		renderer.configure(String(theme_name))
		if renderer.particles.size() != entry["states"]["high"]["particles"].size():
			draw_failures.append("%s:particles" % theme_name)
		if renderer.frame(0).is_empty():
			draw_failures.append("%s:empty" % theme_name)
	check.call(missing_states.is_empty(), "Every theme has low/medium/high source states")
	check.call(
		draw_failures.is_empty(), "Every theme configures and draws: %s" % str(draw_failures)
	)


func _check_runtime_presets(check: Callable) -> void:
	var high := DynamicMap.new()
	high.configure("forest")
	check.call(
		high.particles.size() == 21 and high.fog_particles.size() == 10, "Forest HIGH counts"
	)
	var medium := DynamicMap.new()
	medium.configure("forest", "medium")
	check.call(
		medium.particles.size() == 12 and medium.fog_particles.size() == 6, "Forest MEDIUM counts"
	)
	var low := DynamicMap.new()
	low.configure("forest", "low")
	check.call(
		low.particles.is_empty() and low.fog_particles.is_empty(),
		"Forest LOW disables particles and fog"
	)
	var fallback := DynamicMap.new()
	fallback.configure("not_a_theme")
	check.call(fallback.theme_name == "forest", "Unknown dynamic theme falls back to forest")


func _replay_case(case_data: Dictionary, check: Callable) -> void:
	var renderer := DynamicMap.new()
	renderer.configure_state(case_data["initial"])
	var label := String(case_data["name"])
	for frame_value in case_data["frames"]:
		var frame: Dictionary = frame_value
		renderer.set_random_replay(frame["random"])
		var operations := renderer.frame(int(frame["t"]))
		check.call(
			_deep_equal(renderer.snapshot()["particles"], frame["particles"]),
			"Dynamic particles match source: %s t=%d" % [label, int(frame["t"])]
		)
		check.call(
			_deep_equal(renderer.snapshot()["fog_particles"], frame["fog_particles"]),
			"Dynamic fog matches source: %s t=%d" % [label, int(frame["t"])]
		)
		check.call(renderer.random_replay_complete(), "Random replay fully consumed: %s" % label)
		check.call(
			_deep_equal(operations, frame["ops"]),
			(
				"Dynamic draw ops match source: %s t=%d (%d ops)"
				% [label, int(frame["t"]), operations.size()]
			)
		)


func _check_torch_case(case_data: Dictionary, check: Callable) -> void:
	var renderer := DynamicMap.new()
	renderer.theme = (case_data["theme"] as Dictionary).duplicate(true)
	renderer.torch_stones = (case_data["torch_stones"] as Array).duplicate(true)
	var operations := DynamicLayout.torch_ops(renderer, int(case_data["t"]))
	check.call(
		_deep_equal(operations, case_data["ops"]),
		"Torch palette matches source: %s" % String(case_data["theme_key"])
	)


func _deep_equal(left: Variant, right: Variant) -> bool:
	var equal := false
	if left is Dictionary and right is Dictionary:
		var left_dict: Dictionary = left
		var right_dict: Dictionary = right
		equal = left_dict.size() == right_dict.size()
		if equal:
			for key in left_dict:
				if not right_dict.has(key) or not _deep_equal(left_dict[key], right_dict[key]):
					equal = false
					break
	elif left is Array and right is Array:
		var left_array: Array = left
		var right_array: Array = right
		equal = left_array.size() == right_array.size()
		if equal:
			for index in range(left_array.size()):
				if not _deep_equal(left_array[index], right_array[index]):
					equal = false
					break
	elif (left is int or left is float) and (right is int or right is float):
		equal = absf(float(left) - float(right)) <= 0.00001
	else:
		equal = left == right
	return equal
