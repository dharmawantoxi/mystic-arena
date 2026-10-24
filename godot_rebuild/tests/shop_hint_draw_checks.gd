extends RefCounted
## Layer 9bv3: `ShopHints.draw` replay. `shop_hint_draw_source_oracle.py` runs the REAL source
## component (plus `ui_theme.letter`) under the recording pygame shim; `ShopHintLayout` must
## rebuild every op from `animation_time` and the `cheap_alpha()` branch, and the arena view
## must open its UI pass with the pills.

const Layout = preload("res://scripts/ui/shop_hint_layout.gd")
const GoldHudChecks = preload("res://tests/gold_hud_draw_checks.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/shop_hint_draw_source.json"


## The oracle's text metrics: `int(size * 0.55)` px per glyph, `size` px tall.
static func _fake_measure(text: String, font_size: int) -> Vector2i:
	return Vector2i(int(font_size * 0.55) * text.length(), font_size)


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Shop hint draw fixture parses")
	if not (data is Dictionary):
		return
	var frames: Array = data["frames"]
	var ops_total := 0
	for frame in frames:
		ops_total += frame["ops"].size()
	check.call(
		frames.size() == 6 and ops_total == 36,
		"Shop hint oracle pins 6 source frames and 36 draw ops"
	)
	var shops: Dictionary = data["shops"]
	check.call(
		(
			GoldHudChecks._value_equal(Layout.HINTS[0][0], shops["radiant_shop_pos"])
			and GoldHudChecks._value_equal(Layout.HINTS[1][0], shops["dire_shop_pos"])
		),
		"Shop hints sit on MapRenderer's radiant and dire shop positions"
	)
	for frame in frames:
		var ops := Layout.ops(
			int(frame["animation_time"]), _fake_measure, bool(frame["cheap_alpha"])
		)
		var mismatch := GoldHudChecks._first_mismatch(ops, frame["ops"])
		check.call(
			mismatch == -1,
			"Shop hints %s match the source ops (first mismatch %d)" % [frame["label"], mismatch]
		)
	check.call(
		(
			Layout.letter("HERO SHOP") == "H E R O   S H O P"
			and Layout.pulse(0) == 0
			and Layout.pulse(13) == 1
			and Layout.pulse(60) == 0
			and Layout.pulse(70) == -1
		),
		"Shop hints letter-space the label and truncate the bob toward zero"
	)
	_check_view_wiring(check, frames)


func _check_view_wiring(check: Callable, frames: Array) -> void:
	var view := PrototypeView.new()
	var order: Array = view.overlay_paint_order()
	check.call(
		order.find("shop_hints") == 0 and order.find("gold_hud") == 1,
		"The shop hints open the UI pass, right before the gold HUD"
	)
	var world := Prototype.new()
	var frame: Dictionary = frames[3]
	world.tick_count = int(frame["animation_time"])
	check.call(
		(
			GoldHudChecks._first_mismatch(
				view.shop_hint_draw_ops(world, _fake_measure), frame["ops"]
			)
			== -1
		),
		"The view bobs the pills with the live world tick count"
	)
	view.free()
