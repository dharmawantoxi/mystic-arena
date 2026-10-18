extends RefCounted
## Layer 9bc: replays the `ComboCounter.draw()` oracle fixture through
## `combo_counter_layout.gd`. `combo_counter_draw_source_oracle.py` runs the REAL
## class from `_render.py` under a recording pygame shim (0.55*size px per
## glyph), so every op (kind, geometry, colour, order) below comes from the
## source. Each frame is replayed twice: from the recorded state, and from the
## production `ComboCounter` state machine fed the same scripted kills.

const Layout = preload("res://scripts/ui/combo_counter_layout.gd")
const ComboCounter = preload("res://scripts/ui/combo_counter.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/combo_counter_draw_source.json"
const COMPARED_KEYS := [
	"kind", "rect", "color", "mult", "width", "radius", "text", "size", "style", "pos", "w", "h"
]
## [count, tier label] read off recorded source frames (every boundary pair).
const TIER_LABELS := [
	[0, "COMBO"],
	[4, "COMBO"],
	[5, "KILLING SPREE!"],
	[9, "KILLING SPREE!"],
	[10, "RAMPAGE!"],
	[14, "RAMPAGE!"],
	[15, "UNSTOPPABLE!"],
	[19, "UNSTOPPABLE!"],
	[20, "GODLIKE!"],
	[22, "GODLIKE!"],
]


static func _measure(text: String, font_size: int) -> Vector2i:
	return Vector2i(int(float(font_size) * 0.55) * text.length(), font_size)


static func _value_equal(actual: Variant, expected: Variant) -> bool:
	if expected is Array:
		if not (actual is Array) or actual.size() != expected.size():
			return false
		for index in range(expected.size()):
			if not _value_equal(actual[index], expected[index]):
				return false
		return true
	if expected is float or expected is int:
		return (actual is float or actual is int) and absf(float(actual) - float(expected)) < 1e-6
	return str(actual) == str(expected)


static func _op_equal(actual: Dictionary, expected: Dictionary) -> bool:
	for key_name in COMPARED_KEYS:
		if expected.has(key_name) != actual.has(key_name):
			return false
		if expected.has(key_name) and not _value_equal(actual[key_name], expected[key_name]):
			return false
	return true


## Index of the first differing op, or -1 when both lists match exactly.
static func _first_mismatch(actual: Array, expected: Array) -> int:
	if actual.size() != expected.size():
		return mini(actual.size(), expected.size())
	for index in range(expected.size()):
		if not _op_equal(actual[index], expected[index]):
			return index
	return -1


static func _has_tick(ticks: Array, tick: int) -> bool:
	for value in ticks:
		if int(value) == tick:
			return true
	return false


static func _frame_key(label: String, tick: int, phase: String, cheap_alpha: bool) -> String:
	return "%s:%d:%s:%d" % [label, tick, phase, 1 if cheap_alpha else 0]


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Combo counter draw fixture parses")
	if not (data is Dictionary):
		return
	var screen := Vector2i(int(data["screen"][0]), int(data["screen"][1]))
	check.call(is_equal_approx(float(data["glyph_factor"]), 0.55), "Combo oracle glyph is 0.55")
	check.call(data["frames"].size() == 52, "Combo counter draw oracle pins 52 source frames")
	_check_helpers(check)
	_check_recorded_frames(check, data, screen)
	_check_production_replay(check, data, screen)
	_check_view_wiring(check)


func _check_helpers(check: Callable) -> void:
	for row_value in TIER_LABELS:
		var row: Array = row_value
		var entry := Layout.tier(int(row[0]))
		check.call(
			String(entry[1]) == String(row[1]),
			"Combo draw tier at count %d is %s" % [int(row[0]), String(row[1])]
		)
	var green := [100, 255, 100]
	check.call(Layout.flash_color(green, 0) == green, "No flash keeps the tier colour")
	check.call(Layout.flash_color(green, 20) == [255, 255, 255], "Full flash lerps to white")
	check.call(Layout.flash_color(green, 19) == [247, 255, 247], "Flash 19 truncates like source")
	check.call(Layout.flash_color([255, 50, 50], 18) == [255, 234, 234], "Flash 18 on GODLIKE red")


func _expect_ops(check: Callable, label: String, actual: Array, expected: Array) -> void:
	var bad := _first_mismatch(actual, expected)
	check.call(
		bad < 0,
		(
			"Combo %s: %d ops match source (first mismatch #%d: got %s, want %s)"
			% [
				label,
				expected.size(),
				bad,
				str(actual[bad]) if 0 <= bad and bad < actual.size() else "",
				str(expected[bad]) if 0 <= bad and bad < expected.size() else ""
			]
		)
	)


func _check_recorded_frames(check: Callable, data: Dictionary, screen: Vector2i) -> void:
	var drawn := 0
	for frame_value in data["frames"]:
		var frame: Dictionary = frame_value
		var cheap_alpha := bool(frame["cheap_alpha"])
		var label := _frame_key(
			String(frame["label"]), int(frame["tick"]), String(frame["phase"]), cheap_alpha
		)
		var state: Dictionary = frame["state"]
		_expect_ops(check, label, Layout.ops(state, screen.x, _measure, cheap_alpha), frame["ops"])
		drawn += frame["ops"].size()
	check.call(drawn == 426, "Combo counter oracle pins 426 recorded draw ops")


func _check_production_replay(check: Callable, data: Dictionary, screen: Vector2i) -> void:
	var frames := {}
	for frame_value in data["frames"]:
		var frame: Dictionary = frame_value
		var key := _frame_key(
			String(frame["label"]),
			int(frame["tick"]),
			String(frame["phase"]),
			bool(frame["cheap_alpha"])
		)
		frames[key] = frame
	var replayed := 0
	for scenario_value in data["scenarios"]:
		var scenario: Dictionary = scenario_value
		var counter := ComboCounter.new()
		var last_tick := 0
		for tick_value in scenario["post"]:
			last_tick = maxi(last_tick, int(tick_value))
		for tick in range(last_tick + 1):
			for kill_tick in scenario["kills"]:
				if int(kill_tick) == tick:
					counter.add_kill()
			if _has_tick(scenario["pre"], tick):
				replayed += _replay_frame(
					check, frames, scenario, tick, "pre", true, counter, screen
				)
			counter.update()
			if _has_tick(scenario["post"], tick):
				replayed += _replay_frame(
					check, frames, scenario, tick, "post", true, counter, screen
				)
			if _has_tick(scenario["single_shadow"], tick):
				replayed += _replay_frame(
					check, frames, scenario, tick, "post", false, counter, screen
				)
	check.call(
		replayed == data["frames"].size(),
		"Combo production state replays every recorded frame (%d)" % replayed
	)


func _replay_frame(
	check: Callable,
	frames: Dictionary,
	scenario: Dictionary,
	tick: int,
	phase: String,
	cheap_alpha: bool,
	counter: ComboCounter,
	screen: Vector2i
) -> int:
	var key := _frame_key(String(scenario["label"]), tick, phase, cheap_alpha)
	check.call(frames.has(key), "Combo fixture has frame %s" % key)
	if not frames.has(key):
		return 0
	var expected: Array = frames[key]["ops"]
	var state := Layout.state_of(counter)
	_expect_ops(
		check, "production " + key, Layout.ops(state, screen.x, _measure, cheap_alpha), expected
	)
	return 1


func _main_text(ops: Array, text: String) -> Dictionary:
	var found := {}
	for op_value in ops:
		var op: Dictionary = op_value
		var color: Array = op.get("color", [0, 0, 0, 0])
		var is_shadow: bool = int(color[0]) + int(color[1]) + int(color[2]) == 0
		if String(op.get("text", "")) == text and not is_shadow:
			found = op
	return found


func _check_view_wiring(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var session := PrototypeSession.new()
	session.world = world
	var view := PrototypeView.new()
	view.session = session
	check.call(view.combo_counter_draw_ops(world).is_empty(), "Idle combo counter paints no ops")
	for _kill in range(5):
		world.effects.combo_counter.add_kill()
	world._step_combo_clock()
	var ops: Array = view.combo_counter_draw_ops(world)
	var count_op := _main_text(ops, "x5")
	var label_op := _main_text(ops, "KILLING SPREE!")
	check.call(not count_op.is_empty(), "Five kills paint the x5 count")
	check.call(not label_op.is_empty(), "Five kills paint the KILLING SPREE! label")
	if not count_op.is_empty():
		check.call(
			int(count_op["pos"][0]) + (int(count_op["w"]) >> 1) == 1280 - Layout.RIGHT_INSET,
			"Real-font count text stays centred on screen_w - 100"
		)
		check.call(int(count_op["w"]) > 0, "Real font measures the production count text")
	var bars := 0
	for op_value in ops:
		var op: Dictionary = op_value
		if String(op["kind"]) == "rect":
			bars += 1
	check.call(bars == 2, "Five kills paint the timer bar track and fill")
	for _tick in range(260):
		world._step_combo_clock()
	check.call(view.combo_counter_draw_ops(world).is_empty(), "Expired combo fades to no ops")
	view.free()
	session.free()
