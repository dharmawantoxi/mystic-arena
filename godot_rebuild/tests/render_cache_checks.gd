extends RefCounted
## Replays the source RenderCache oracle through the state-only Godot port.
## Font and Surface objects are metadata placeholders; no pygame pixels are
## created or drawn by this suite.

const RenderCache = preload("res://scripts/ui/render_cache.gd")
const FIXTURE := "res://tests/fixtures/render_cache_source.json"


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Render cache fixture parses")
	if not (parsed is Dictionary):
		return
	var data: Dictionary = parsed
	check.call(
		(
			int(data["font_min"]) == RenderCache.FONT_MIN
			and int(data["font_max"]) == RenderCache.FONT_MAX
		),
		"Render cache font clamp limits match source"
	)
	check.call(bool(data["singleton_same_instance"]), "Source singleton construction is stable")
	RenderCache.reset_shared()
	var shared_one: RenderCache = RenderCache.get_shared()
	var shared_two: RenderCache = RenderCache.get_shared()
	check.call(shared_one == shared_two, "Godot shared render cache returns one instance")
	for case_value in data["cases"]:
		_replay_case(case_value as Dictionary, check)
	_check_shortcuts(check)


func _replay_case(case_data: Dictionary, check: Callable) -> void:
	var cache: RenderCache = RenderCache.new()
	var operations: Array = case_data["operations"]
	var outputs: Array = case_data["outputs"]
	var label: String = String(case_data["name"])
	for index in range(operations.size()):
		var operation: Dictionary = operations[index]
		var expected: Dictionary = outputs[index]
		var operation_label := "%s operation %d" % [label, index]
		var op: String = String(operation["op"])
		if op == "font":
			var font: Variant = cache.get_font(
				int(operation["size"]), String(operation["style"]), bool(operation["bold"])
			)
			_check_font(
				cache.get_font_snapshot(font),
				expected["font"] as Dictionary,
				check,
				operation_label
			)
		elif op == "circle":
			var circle: Variant = cache.get_circle_surface(
				int(operation["radius"]), operation["color"] as Array, int(operation["width"])
			)
			_check_surface(
				cache.get_surface_snapshot(circle),
				expected["surface"] as Dictionary,
				check,
				operation_label
			)
		elif op == "glow":
			var glow: Variant = cache.get_glow_surface(
				int(operation["radius"]), operation["color"] as Array, int(operation["layers"])
			)
			_check_surface(
				cache.get_surface_snapshot(glow),
				expected["surface"] as Dictionary,
				check,
				operation_label
			)
		elif op == "clear":
			cache.clear()
		elif op == "stats":
			pass
		else:
			check.call(false, "Unknown render cache operation: %s" % op)
		_check_font_creations(cache, expected, check, operation_label)
		_check_stats(cache, expected["stats"] as Dictionary, check, operation_label)


func _check_font(got: Dictionary, expected: Dictionary, check: Callable, label: String) -> void:
	check.call(
		(
			int(got["size"]) == int(expected["size"])
			and String(got["style"]) == String(expected["style"])
			and bool(got["bold"]) == bool(expected["bold"])
		),
		"Cached font state matches source: %s" % label
	)


func _check_surface(got: Dictionary, expected: Dictionary, check: Callable, label: String) -> void:
	check.call(
		(
			int(got["width"]) == int(expected["width"])
			and int(got["height"]) == int(expected["height"])
		),
		"Cached surface size matches source: %s" % label
	)
	check.call(
		_json_equal(got["draw_calls"], expected["draw_calls"]),
		"Cached draw metadata matches source: %s" % label
	)


func _check_font_creations(
	cache: RenderCache, expected: Dictionary, check: Callable, label: String
) -> void:
	check.call(
		int(cache.get_state()["font_creations"]) == int(expected["font_calls"]),
		"Font creation count matches source: %s" % label
	)


func _check_stats(cache: RenderCache, expected: Dictionary, check: Callable, label: String) -> void:
	var got: Dictionary = cache.get_stats()
	check.call(
		(
			int(got["fonts"]) == int(expected["fonts"])
			and int(got["circles"]) == int(expected["circles"])
			and int(got["surfaces"]) == int(expected["surfaces"])
		),
		"Render cache statistics match source: %s" % label
	)


func _check_shortcuts(check: Callable) -> void:
	RenderCache.reset_shared()
	var first_font: Variant = RenderCache.get_cached_font(6, "body", false)
	var second_font: Variant = RenderCache.get_cached_font(6, "body", false)
	var circle: Variant = RenderCache.get_cached_circle(4, [255, 10, 0, 300], 1)
	var glow: Variant = RenderCache.get_cached_glow(4, [10, 20, 30], 2)
	var shared: RenderCache = RenderCache.get_shared()
	check.call(
		(
			shared.get_font_snapshot(first_font) == shared.get_font_snapshot(second_font)
			and int(shared.get_state()["font_creations"]) == 1
			and shared.get_surface_snapshot(circle)["width"] == 12
			and shared.get_surface_snapshot(glow)["width"] == 12
		),
		"Shared render cache shortcuts reuse state"
	)
	RenderCache.clear_shared_cache()
	var stats: Dictionary = shared.get_stats()
	check.call(
		int(stats["fonts"]) == 1 and int(stats["circles"]) == 0 and int(stats["surfaces"]) == 0,
		"Shared render cache clear retains fonts"
	)


func _json_equal(left: Variant, right: Variant) -> bool:
	return JSON.stringify(left) == JSON.stringify(right)
