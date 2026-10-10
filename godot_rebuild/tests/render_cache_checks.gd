extends RefCounted
## Replays the source RenderCache oracle through the state-only Godot port.
## Font and Surface objects are metadata placeholders; no pygame pixels are
## created or drawn by this suite.

const RenderCache = preload("res://scripts/ui/render_cache.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
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
	_check_runtime_wiring(check)


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


func _check_runtime_wiring(check: Callable) -> void:
	RenderCache.reset_shared()
	var world := Prototype.new()
	var shared: RenderCache = RenderCache.get_shared()
	var init_state: Dictionary = world.render_cache.get_state()
	check.call(
		(
			world.render_cache == shared
			and world.effects.render_cache == shared
			and int(init_state["fonts"]) == 1
			and int(init_state["surfaces"]) == 2
		),
		"Prototype wires shared RenderCache and caches shop font and glows on init"
	)
	check.call(world.setup_arena(), "Arena setup succeeds for RenderCache hero ring wiring")
	var after_arena: Dictionary = world.render_cache.get_state()
	check.call(
		int(after_arena["circles"]) == 2,
		"Arena setup caches blue and red hero ring circles in RenderCache"
	)
	world.effects.add_damage_number(100.0, 100.0, 42, false, "physical")
	world.effects.add_damage_number(120.0, 100.0, 55, false, "physical")
	var first_text = world.effects.floating_texts[0]
	var after_damage: Dictionary = world.render_cache.get_state()
	check.call(
		(
			int(first_text.cached_font.get("size", 0)) == 18
			and bool(first_text.cached_font.get("bold", false))
			and int(after_damage["font_creations"]) == 2
		),
		"FloatingText damage numbers reuse cached bold body font from RenderCache"
	)
	world.effects.announce_wave(1)
	world.effects.unlock_achievement("FIRST", "Desc", "star")
	var boss = world._spawn_boss("gornak")
	var final_state: Dictionary = world.cache_stats()["render_cache"]
	check.call(
		boss != null and int(final_state["fonts"]) >= 4 and int(final_state["surfaces"]) >= 3,
		"Wave banner, achievement popup and boss spawn populate RenderCache fonts and glows"
	)


func _json_equal(left: Variant, right: Variant) -> bool:
	var equal := false
	if left is Dictionary and right is Dictionary:
		var left_dict: Dictionary = left
		var right_dict: Dictionary = right
		equal = left_dict.size() == right_dict.size()
		if equal:
			for key in left_dict:
				if not right_dict.has(key) or not _json_equal(left_dict[key], right_dict[key]):
					equal = false
					break
	elif left is Array and right is Array:
		var left_array: Array = left
		var right_array: Array = right
		equal = left_array.size() == right_array.size()
		if equal:
			for index in range(left_array.size()):
				if not _json_equal(left_array[index], right_array[index]):
					equal = false
					break
	elif (left is int or left is float) and (right is int or right is float):
		equal = is_equal_approx(float(left), float(right))
	else:
		equal = left == right
	return equal
