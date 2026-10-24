extends RefCounted
## Layer 9bv5: `Overlay.draw` replay. `end_overlay_draw_source_oracle.py` runs the REAL source
## overlay (cheap-alpha branch) under the recording pygame shim; `EndOverlayLayout` must
## rebuild every op (backdrop, rays, glow, title, sparkles, stats, action hint, achievements)
## and the arena view must paint the screen's end state in the source slot.

const Layout = preload("res://scripts/ui/end_overlay_layout.gd")
const GoldHudChecks = preload("res://tests/gold_hud_draw_checks.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/end_overlay_draw_source.json"
const EXTRA_KEYS := ["points", "rows", "alpha", "outline", "start", "end", "name"]


## The oracle's text metrics: `int(size * 0.55)` px per glyph, `size` px tall.
static func _fake_measure(text: String, font_size: int) -> Vector2i:
	return Vector2i(int(font_size * 0.55) * text.length(), font_size)


static func _state(frame: Dictionary, colors: Dictionary) -> Dictionary:
	var victory := String(frame["title"]).begins_with("VICTORY")
	return {
		"title": frame["title"],
		"victory": victory,
		"color": colors["victory"] if victory else colors["defeat"],
		"action": frame["action"],
		"animation_time": int(frame["animation_time"]),
		"stats": frame["stats"],
		"achievements": int(frame["achievements"]),
	}


## `_first_mismatch` plus the keys only these ops carry.
static func _mismatch(actual: Array, expected: Array) -> int:
	var index := GoldHudChecks._first_mismatch(actual, expected)
	if index != -1:
		return index
	for at in range(expected.size()):
		for key_name in EXTRA_KEYS:
			var want: Dictionary = expected[at]
			var got: Dictionary = actual[at]
			if want.has(key_name) != got.has(key_name):
				return at
			if want.has(key_name) and not GoldHudChecks._value_equal(got[key_name], want[key_name]):
				return at
	return -1


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "End overlay draw fixture parses")
	if not (data is Dictionary):
		return
	var frames: Array = data["frames"]
	var ops_total := 0
	for frame in frames:
		ops_total += frame["ops"].size()
	check.call(
		frames.size() == 4 and ops_total == 407,
		"End overlay oracle pins 4 source frames and 407 draw ops (got %d)" % ops_total
	)
	var colors: Dictionary = data["colors"]
	check.call(
		(
			GoldHudChecks._value_equal(Layout.VICTORY_COLOR, colors["victory"])
			and GoldHudChecks._value_equal(Layout.DEFEAT_COLOR, colors["defeat"])
		),
		"End overlay colours follow the source GOLD / RED"
	)
	for frame in frames:
		var ops := Layout.ops(_state(frame, colors), _fake_measure, int(frame["ticks"]))
		var mismatch := _mismatch(ops, frame["ops"])
		check.call(
			mismatch == -1,
			"End overlay %s matches the source ops (first mismatch %d)" % [frame["label"], mismatch]
		)
	check.call(
		(
			Layout.action_text(true, true, {}) == String(frames[0]["action"])
			and Layout.action_text(true, false, {}) == String(frames[1]["action"])
			and Layout.action_text(false, true, {"replay": "R"}) == String(frames[2]["action"])
		),
		"End overlay action lines follow Game.draw's keyboard labels"
	)
	_check_view_wiring(check, frames[2], colors)


func _check_view_wiring(check: Callable, frame: Dictionary, colors: Dictionary) -> void:
	var view := PrototypeView.new()
	var order: Array = view.overlay_paint_order()
	check.call(
		(
			order.find("end_overlay") == order.find("tactical_feedback") + 1
			and order.find("end_overlay") == order.find("input_hints") - 1
		),
		"The end overlay paints after the tactical banner and before the hint bar"
	)
	var world := Prototype.new()
	check.call(
		view.end_overlay_draw_ops(world, _fake_measure, 0).is_empty(),
		"A running match paints no end overlay"
	)
	var state := _state(frame, colors)
	state.erase("animation_time")
	view.end_overlay_state = state
	world.tick_count = int(frame["animation_time"])
	check.call(
		(
			_mismatch(
				view.end_overlay_draw_ops(world, _fake_measure, int(frame["ticks"])), frame["ops"]
			)
			== -1
		),
		"The view builds the overlay from the screen state and the frozen world tick count"
	)
	view.free()
