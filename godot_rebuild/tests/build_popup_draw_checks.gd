extends RefCounted
## Layer 9bv7: `BuildPopup.draw` replay. `build_popup_draw_source_oracle.py` runs the REAL
## source popup (cheap-alpha and flat branches) under the recording pygame shim; `BuildPopupLayout`
## must rebuild every op (connector line, shadow, gradient card, border, corner ticks, title,
## gold line, X button, four tower cards) and the arena view must paint the screen's build state
## in the source slot.

const Layout = preload("res://scripts/ui/build_popup_layout.gd")
const GoldHudChecks = preload("res://tests/gold_hud_draw_checks.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/build_popup_draw_source.json"
const EXTRA_KEYS := ["outline", "alpha", "points", "rows", "start", "end", "name"]


## The oracle's text metrics: `int(size * 0.55)` px per glyph, `size` px tall.
static func _fake_measure(text: String, font_size: int) -> Vector2i:
	return Vector2i(int(font_size * 0.55) * text.length(), font_size)


static func _state(frame: Dictionary) -> Dictionary:
	var mouse: Array = frame["mouse"]
	return {
		"x": int(frame["slot"][0]),
		"y": int(frame["slot"][1]),
		"gold": int(frame["gold"]),
		"mouse": Vector2i(int(mouse[0]), int(mouse[1])),
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
	check.call(data is Dictionary, "Build popup draw fixture parses")
	if not (data is Dictionary):
		return
	var frames: Array = data["frames"]
	var ops_total := 0
	for frame in frames:
		ops_total += frame["ops"].size()
	check.call(
		frames.size() == 9 and ops_total == 751,
		"Build popup oracle pins 9 source frames and 751 draw ops (got %d)" % ops_total
	)
	var colors: Dictionary = data["colors"]
	check.call(
		(
			GoldHudChecks._value_equal(Layout.GOLD, colors["gold"])
			and GoldHudChecks._value_equal(Layout.UI_GOLD, colors["ui_gold"])
			and GoldHudChecks._value_equal(Layout.GOLD_BRIGHT, colors["gold_bright"])
			and GoldHudChecks._value_equal(Layout.GOLD_TEXT, colors["gold_text"])
		),
		"Build popup colours follow the source GOLD / ui_theme.GOLD"
	)
	for frame in frames:
		var ops := Layout.ops(_state(frame), _fake_measure, bool(frame["cheap_alpha"]))
		var mismatch := _mismatch(ops, frame["ops"])
		check.call(
			mismatch == -1,
			"Build popup %s matches the source ops (first mismatch %d)" % [frame["label"], mismatch]
		)
	for frame in frames:
		var slot: Array = frame["slot"]
		var buttons: Dictionary = frame["buttons"]
		var want_close := Layout.close_rect(int(slot[0]), int(slot[1]))
		check.call(
			GoldHudChecks._value_equal(
				[
					want_close.position.x,
					want_close.position.y,
					want_close.size.x,
					want_close.size.y
				],
				buttons["build_close"]
			),
			"X close rect %s matches g.ui_buttons for %s" % [want_close, frame["label"]]
		)
		for index in range(4):
			var want := Layout.button_rect(int(slot[0]), int(slot[1]), index)
			var key := "build_%s" % Layout.TOWER_TYPES[index][0]
			check.call(
				GoldHudChecks._value_equal(
					[want.position.x, want.position.y, want.size.x, want.size.y], buttons[key]
				),
				"%s card rect matches g.ui_buttons for %s" % [key, frame["label"]]
			)
	_check_view_wiring(check, frames[0])


func _check_view_wiring(check: Callable, frame: Dictionary) -> void:
	var view := PrototypeView.new()
	var order: Array = view.overlay_paint_order()
	check.call(
		order.find("build_popup") == order.find("tactical_feedback") + 1,
		"The build popup paints right after the tactical banner"
	)
	var world := Prototype.new()
	check.call(
		view.build_popup_draw_ops(world, _fake_measure).is_empty(),
		"A match with no build slot paints no build popup"
	)
	var state := _state(frame)
	view.build_popup_state = state
	check.call(
		(
			_mismatch(view.build_popup_draw_ops(world, _fake_measure, state["mouse"]), frame["ops"])
			== -1
		),
		"The view builds the popup from the screen state"
	)
	view.free()
