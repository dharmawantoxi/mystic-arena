extends RefCounted
## Layer 9bv2: `Game._draw_gold_hud` replay. `gold_hud_draw_source_oracle.py` runs the REAL
## source method (plus `ui_theme.draw_icon` and `format_gold_rate`) under the recording pygame
## shim; `GoldHudLayout` must rebuild every op from the gold, income rate, difficulty and the
## `cheap_alpha()` branch, and the arena view must feed it the live economy.

const Layout = preload("res://scripts/ui/gold_hud_layout.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/gold_hud_draw_source.json"
const COMPARED_KEYS := [
	"kind", "rect", "center", "radius", "a", "b", "color", "mult", "width", "top", "bottom", "text"
]
const TEXT_KEYS := ["size", "style", "pos"]


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
	for key_name in COMPARED_KEYS + TEXT_KEYS:
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


## The oracle's text metrics: `int(size * 0.55)` px per glyph, `size` px tall.
static func _fake_measure(text: String, font_size: int) -> Vector2i:
	return Vector2i(int(font_size * 0.55) * text.length(), font_size)


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Gold HUD draw fixture parses")
	if not (data is Dictionary):
		return
	var frames: Array = data["frames"]
	var ops_total := 0
	for frame in frames:
		ops_total += frame["ops"].size()
	check.call(
		frames.size() == 6 and ops_total == 102,
		"Gold HUD oracle pins 6 source frames and 102 draw ops"
	)
	for frame in frames:
		var ops := Layout.ops(
			int(frame["gold"]),
			float(frame["rate"]),
			String(frame["difficulty"]),
			_fake_measure,
			bool(frame["cheap_alpha"])
		)
		var mismatch := _first_mismatch(ops, frame["ops"])
		check.call(
			mismatch == -1,
			"Gold HUD %s matches the source ops (first mismatch %d)" % [frame["label"], mismatch]
		)
	check.call(
		(
			Layout.gold_text(0) == "0"
			and Layout.gold_text(999) == "999"
			and Layout.gold_text(1000) == "1,000"
			and Layout.gold_text(1234567) == "1,234,567"
		),
		"Gold HUD groups thousands like f'{gold:,}'"
	)
	_check_view_wiring(check, frames)


func _check_view_wiring(check: Callable, frames: Array) -> void:
	var view := PrototypeView.new()
	var order: Array = view.overlay_paint_order()
	check.call(
		(
			order.find("gold_hud") == order.find("shop_hints") + 1
			and order.find("gold_hud") < order.find("boss_intro")
		),
		"The gold HUD paints right after the shop hints and before the boss banner"
	)
	check.call(view.gold_hud_visible, "The gold HUD shows by default (no side panel)")
	var world := Prototype.new()
	var frame: Dictionary = frames[2]
	world.economy.gold[0] = int(frame["gold"])
	world.economy.income_per_second = float(frame["rate"])
	world.difficulty = String(frame["difficulty"])
	check.call(
		_first_mismatch(view.gold_hud_draw_ops(world, _fake_measure), frame["ops"]) == -1,
		"The view builds the chip from the live gold, income rate and difficulty"
	)
	var chip: Array = Layout.chip_rect(world.economy.gold[0], 3.75, _fake_measure)
	check.call(
		chip == [18, 22, 210, 40],
		"The chip rect follows max(150, val_w + inc_w + 78) = %s" % [chip]
	)
	view.free()
