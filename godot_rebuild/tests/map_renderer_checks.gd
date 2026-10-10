extends RefCounted
## Replays the source MapRenderer coordinator through the state-only port.
## Static/dynamic pygame drawing is intentionally outside this suite.

const MapRenderer = preload("res://scripts/ui/map_renderer.gd")
const FIXTURE := "res://tests/fixtures/map_renderer_source.json"


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Map renderer fixture parses")
	if not (parsed is Dictionary):
		return
	var data: Dictionary = parsed
	check.call(
		(
			int(data["map_width"]) == MapRenderer.MAP_WIDTH
			and int(data["map_height"]) == MapRenderer.MAP_HEIGHT
		),
		"Map renderer dimensions match source"
	)
	check.call(
		int(data["shop_size"]) == MapRenderer.SHOP_SIZE, "Map renderer shop radius matches source"
	)
	for case_value in data["cases"]:
		_replay_case(case_value as Dictionary, check)
	_check_default_state(check)


func _replay_case(case_data: Dictionary, check: Callable) -> void:
	var renderer := MapRenderer.new()
	(
		renderer
		. configure(
			String(case_data["theme_name"]),
			{
				"top": case_data["lanes"]["top"],
				"mid": case_data["lanes"]["mid"],
				"bot": case_data["lanes"]["bot"],
			},
			case_data["river"] as Array,
			case_data["decorations"] as Dictionary,
			case_data["snapshot"]["theme"] as Dictionary
		)
	)
	var label: String = String(case_data["name"])
	check.call(
		_deep_equal(renderer.get_state(), case_data["snapshot"] as Dictionary),
		"Map renderer initialization state matches source: %s" % label
	)
	var lane_queries: Dictionary = case_data["lane_queries"]
	for lane_name in lane_queries:
		check.call(
			_deep_equal(renderer.get_lane_path(String(lane_name)), lane_queries[lane_name]),
			"Lane getter matches source: %s %s" % [label, String(lane_name)]
		)
	check.call(
		_deep_equal(renderer.get_shop_positions(), case_data["snapshot"]["shop_positions"]),
		"Shop position getter matches source: %s" % label
	)
	check.call(
		_deep_equal(renderer.get_decoration_state(), case_data["decorations"]),
		"Decoration state getter matches source: %s" % label
	)
	var clicks: Array = case_data["clicks"]
	for index in range(clicks.size()):
		var expected: Dictionary = clicks[index]
		var click: Array = expected["click"]
		var x: float = float(click[0])
		var y: float = float(click[1])
		check.call(
			renderer.is_click_on_shop(x, y) == bool(expected["is_shop"]),
			"Shop hit-test matches source: %s #%d" % [label, index]
		)
		check.call(
			renderer.get_clicked_shop(x, y) == expected["clicked_shop"],
			"Clicked shop label matches source: %s #%d" % [label, index]
		)


func _check_default_state(check: Callable) -> void:
	var renderer := MapRenderer.new()
	renderer.configure()
	var state: Dictionary = renderer.get_state()
	check.call(
		(
			int(state["map_width"]) == MapRenderer.MAP_WIDTH
			and int(state["map_height"]) == MapRenderer.MAP_HEIGHT
			and String(state["theme_name"]) == "forest"
			and bool(state["static_map_ready"])
			and bool(state["dynamic_ready"])
		),
		"Default map renderer state is ready"
	)
	check.call(
		(
			renderer.get_lane_path("not-a-lane").is_empty()
			and renderer.get_clicked_shop(0.0, 0.0) == null
		),
		"Unknown lane and distant shop return empty state"
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
		equal = is_equal_approx(float(left), float(right))
	else:
		equal = left == right
	return equal
