extends RefCounted
## Replays the `_render.py::AchievementPopup` source oracle fixture through the
## native port. `achievement_popup_source_oracle.py` runs the real `draw()`
## under a pygame shim and reads `x_offset` / `alpha` / `glow_alpha` off the
## frame with `settrace`, so the slide curve and the queue timing are the
## source's, not a re-implementation.

const AchievementPopup = preload("res://scripts/ui/achievement_popup.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const PopupFont = preload("res://assets/fonts/Barlow-SemiBold.ttf")
const FIXTURE := "res://tests/fixtures/achievement_popup_source.json"

const SHOWING := 0
const TIMER := 1
const QUEUE := 2
const CURVE := 3
const TITLE := 4

const PROGRESS := 0
const OFFSET_X := 1
const ALPHA := 2
const GLOW := 3


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Achievement popup fixture parses")
	if not (data is Dictionary):
		return

	var popup := AchievementPopup.new()
	check.call(
		is_equal_approx(float(data["duration"]), float(popup.duration)),
		"Achievement slot matches source"
	)
	_check_layout(check, popup)
	_check_defaults(check, popup)
	_check_icons(check, popup, data)
	_check_panel_visuals(check, data)
	_check_replay(check, popup, data)
	_check_view_wiring(check)


func _check_view_wiring(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var session := PrototypeSession.new()
	session.world = world
	var view := PrototypeView.new()
	view.session = session
	world.effects.unlock_achievement("GLOW TEST", "Early slot glow")
	world._step_combo_clock()
	check.call(
		(
			bool(view.overlay_draw_summary().get("achievement_showing", false))
			and bool(view.overlay_draw_summary().get("achievement_glow_active", false))
		),
		"PrototypeView.overlay_draw_summary reports active achievement glow during early slot"
	)
	for _step in range(60):
		world._step_combo_clock()
	check.call(
		(
			bool(view.overlay_draw_summary().get("achievement_showing", false))
			and not bool(view.overlay_draw_summary().get("achievement_glow_active", true))
		),
		"PrototypeView.overlay_draw_summary clears achievement glow after 30% slot threshold"
	)
	view.free()
	session.free()


func _check_layout(check: Callable, popup) -> void:
	# The source parks the panel top-right, 20px in, plus the slide offset.
	popup.current = {"title": "Layout", "description": "", "icon_type": "star"}
	popup.timer = popup.duration / 2
	check.call(popup.get_offset_x() == 0, "Held panel sits at zero offset")
	check.call(popup.panel_x(1280) == 1280 - 280 - 20, "Held panel parks 20px from the right edge")
	check.call(popup.panel_y() == 180, "Panel keeps the source's top offset")
	popup.current = {}
	popup.timer = 0


func _check_defaults(check: Callable, popup) -> void:
	popup.unlock("Solo", "No icon type given")
	var entry: Dictionary = popup.queue[0]
	check.call(String(entry["icon_type"]) == "star", "unlock() defaults the icon to star")
	check.call(String(entry["title"]) == "Solo", "unlock() stores the title")
	popup.queue.clear()


func _check_icons(check: Callable, popup, data: Dictionary) -> void:
	var icon_fixture: Dictionary = data.get("icons", {})
	var icon_types := ["star", "sword", "skull", "shield", "gold", "unknown"]
	check.call(
		icon_fixture.size() == icon_types.size(),
		"Oracle pins all achievement icon types and fallback"
	)
	for icon_type_value in icon_types:
		var icon_type: String = icon_type_value
		if not icon_fixture.has(icon_type):
			check.call(false, "Achievement icon oracle is missing %s" % icon_type)
			return
		var actual_ops: Array = popup.icon_ops(icon_type, Vector2(15.0, 30.0), 117)
		if not _values_match(actual_ops, icon_fixture[icon_type]):
			check.call(false, "Achievement %s icon geometry drifted from source" % icon_type)
			return
	check.call(true, "Achievement icons replay all source draw primitives")


func _check_panel_visuals(check: Callable, data: Dictionary) -> void:
	var samples: Array = data.get("panel_visuals", [])
	check.call(
		samples.size() == 3, "Achievement panel oracle pins fade-in, held, and clipped-text draws"
	)
	if samples.size() != 3:
		return
	var fade: Dictionary = samples[0]
	var held: Dictionary = samples[1]
	for sample_index in range(2):
		var sample: Dictionary = samples[sample_index]
		var ops: Array = sample.get("ops", [])
		var lines := _ops_of_type(ops, "line")
		var rects := _ops_of_type(ops, "rect")
		var circles := _ops_of_type(ops, "circle")
		var texts := _ops_of_type(ops, "text")
		var expected_alpha: int = 188 if sample_index == 0 else 255
		var expected_x: int = 960 if sample_index == 0 else 980
		check.call(
			lines.size() == 68, "Achievement panel draws 60 gradient rows and eight corner ticks"
		)
		check.call(
			rects.size() == (3 if sample_index == 0 else 2),
			"Achievement panel keeps its two rounded gold borders and timed glow"
		)
		check.call(
			circles.size() == 5, "Achievement panel preserves its badge and gold icon circles"
		)
		check.call(
			texts.size() == 4,
			"Achievement panel renders its icon, letter-spaced header, title, and description"
		)
		if lines.size() >= 68:
			var top_line: Dictionary = lines[0]
			var middle_gradient: Dictionary = lines[29]
			var bottom_gradient: Dictionary = lines[59]
			var first_tick: Dictionary = lines[60]
			check.call(
				(
					int(top_line["points"][0][0]) == expected_x
					and int(top_line["points"][0][1]) == 180
					and int(top_line["color"][3]) == expected_alpha
				),
				"Achievement gradient begins at source panel position with source opacity"
			)
			check.call(
				(
					int(middle_gradient["color"][0]) == 28
					and int(middle_gradient["color"][2]) == 14
					and int(middle_gradient["color"][3]) == expected_alpha
				),
				"Achievement gradient follows the source per-row dark-gold interpolation"
			)
			check.call(
				(
					int(bottom_gradient["color"][0]) == 37
					and int(bottom_gradient["color"][2]) == 18
					and int(bottom_gradient["color"][3]) == expected_alpha
				),
				"Achievement gradient reaches the source dark-gold endpoint"
			)
			check.call(
				(
					int(first_tick["points"][0][0]) == expected_x + 4
					and int(first_tick["points"][0][1]) == 184
					and int(first_tick["width"]) == 2
				),
				"Achievement gold corner ticks preserve their inset and stroke"
			)
		if rects.size() >= 2:
			check.call(
				int(rects[0]["radius"]) == 6 and int(rects[1]["radius"]) == 5,
				"Achievement panel keeps rounded outer and inner gold borders"
			)
		if sample_index == 0 and rects.size() == 3:
			check.call(
				(
					int(rects[2]["rect"][0]) == 950
					and int(rects[2]["rect"][1]) == 170
					and int(rects[2]["rect"][2]) == 300
					and int(rects[2]["rect"][3]) == 80
					and int(rects[2]["color"][3]) == 94
				),
				"Achievement gold glow preserves its source bounds and early alpha"
			)
		var header: Dictionary = texts[1] if texts.size() > 1 else {}
		check.call(
			String(header.get("text", "")) == "A C H I E V E M E N T",
			"Achievement header retains ui_theme letter spacing"
		)
	var clipped_ops: Array = samples[2].get("ops", [])
	var clipped_texts := _ops_of_type(clipped_ops, "text")
	check.call(
		(
			clipped_texts.size() == 4
			and String(clipped_texts[2].get("text", "")) == "Champion of the …"
			and String(clipped_texts[3].get("text", "")) == "A legendary victory a…"
		),
		"Achievement source oracle pins ellipsis truncation for long title and description"
	)
	var view := PrototypeView.new()
	var clipped_title: String = view.call(
		"_fit_achievement_label", "Champion of the Eternal Mystic Arena", 22, 213.0
	)
	var clipped_desc: String = view.call(
		"_fit_achievement_label",
		"A legendary victory awarded for mastering the ancient battlefield",
		17,
		213.0
	)
	check.call(
		(
			clipped_title.ends_with("…")
			and clipped_desc.ends_with("…")
			and (
				PopupFont.get_string_size(clipped_title, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 22).x
				<= 213.0
			)
			and (
				PopupFont.get_string_size(clipped_desc, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 17).x
				<= 213.0
			)
		),
		"Achievement label port clips long text to the available width"
	)
	view.free()
	check.call(
		fade.get("timer") == 160 and held.get("timer") == 126,
		"Achievement panel oracle samples cover fade-in and held phases"
	)


func _ops_of_type(ops: Array, kind: String) -> Array:
	var found := []
	for value in ops:
		var op: Dictionary = value
		if String(op.get("type", "")) == kind:
			found.append(op)
	return found


func _values_match(actual: Variant, expected: Variant) -> bool:
	if typeof(actual) in [TYPE_INT, TYPE_FLOAT] and typeof(expected) in [TYPE_INT, TYPE_FLOAT]:
		return is_equal_approx(float(actual), float(expected))
	if actual is Array and expected is Array:
		return _arrays_match(actual, expected)
	if actual is Dictionary and expected is Dictionary:
		return _dictionaries_match(actual, expected)
	return actual == expected


func _arrays_match(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size():
		return false
	for index in range(actual.size()):
		if not _values_match(actual[index], expected[index]):
			return false
	return true


func _dictionaries_match(actual: Dictionary, expected: Dictionary) -> bool:
	if actual.size() != expected.size():
		return false
	for key in expected:
		if not actual.has(key) or not _values_match(actual[key], expected[key]):
			return false
	return true


func _check_replay(check: Callable, popup, data: Dictionary) -> void:
	var steps: Array = data["steps"]
	check.call(steps.size() == 760, "Source fixture keeps the 760 replayed ticks")

	var unlocks: Array = data["unlocks"]
	check.call(unlocks.size() == 4, "Source fixture keeps the 4 scripted unlocks")
	var by_tick := {}
	for entry in unlocks:
		by_tick[int(entry[0])] = entry

	popup = AchievementPopup.new()
	for index in range(steps.size()):
		if by_tick.has(index):
			var unlock: Array = by_tick[index]
			popup.unlock(String(unlock[1]), String(unlock[2]), String(unlock[3]))
		popup.update()
		if not _matches(popup, steps[index]):
			check.call(false, "Achievement popup step %d drifted from source" % index)
			return

	check.call(true, "Achievement popup replays %d source ticks exactly" % steps.size())
	check.call(not popup.is_showing(), "Achievement popup retires once the queue drains")
	check.call(popup.queue.is_empty(), "Achievement queue is empty at the end")


func _matches(popup, expected: Array) -> bool:
	if popup.is_showing() != (int(expected[SHOWING]) == 1):
		return false
	if popup.timer != int(expected[TIMER]) or popup.queue.size() != int(expected[QUEUE]):
		return false
	if not popup.is_showing():
		return expected[CURVE] == null

	if String(popup.current.get("title", "")) != String(expected[TITLE]):
		return false
	var curve: Array = expected[CURVE]
	if not is_equal_approx(popup.progress(), float(curve[PROGRESS])):
		return false
	var glow: int = AchievementPopup.NO_GLOW if curve[GLOW] == null else int(curve[GLOW])
	return (
		popup.get_offset_x() == int(curve[OFFSET_X])
		and popup.get_alpha() == int(curve[ALPHA])
		and popup.get_glow_alpha() == glow
	)
