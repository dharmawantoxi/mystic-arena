extends RefCounted
## Layer 9bv8: replay the selected-hero panel and six item slots from the source oracle.
## The checks pin the panel/close/toggle/item/forge/upgrade rects and confirm the panel is
## painted immediately after the build popup, with the boss-death overlay still last.

const Layout = preload("res://scripts/ui/hero_panel_layout.gd")
const GoldHudChecks = preload("res://tests/gold_hud_draw_checks.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/hero_panel_draw_source.json"
const EXTRA_KEYS := ["alpha", "blend", "points"]


## The oracle's text metrics: `int(size * 0.55)` px per glyph, `size` px tall.
static func _fake_measure(text: String, font_size: int) -> Vector2i:
	return Vector2i(int(font_size * 0.55) * text.length(), font_size)


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


static func _rect_array(rect: Rect2i) -> Array:
	return [rect.position.x, rect.position.y, rect.size.x, rect.size.y]


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Hero panel draw fixture parses")
	if not (data is Dictionary):
		return
	var frames: Array = data["frames"]
	var ops_total := 0
	for frame in frames:
		ops_total += frame["ops"].size()
	check.call(
		frames.size() == 6 and ops_total == 440,
		"Hero panel oracle pins 6 source frames and 440 draw ops (got %d)" % ops_total
	)
	check.call(
		Layout.mobile_panel_origin(Rect2i(1280, 0, 344, 720)) == Vector2i(1312, 324),
		"Wide side-panel anchor matches panel_pos_bawah on a 344x720 dock"
	)
	check.call(
		Layout.mobile_panel_origin(Rect2i(1280, 0, 287, 720)) == null,
		"Narrow side dock keeps the hero panel in the arena"
	)
	check.call(
		Layout.mobile_panel_origin(Rect2i(1280, 50, 344, 600)) == Vector2i(1312, 254),
		"Short mobile dock clamps the hero panel above the bottom notification zone"
	)
	var colors: Dictionary = data["colors"]
	check.call(
		(
			GoldHudChecks._value_equal(Layout.PANEL_TOP, colors["panel_top"])
			and GoldHudChecks._value_equal(Layout.PANEL_FILL, colors["panel_fill"])
			and GoldHudChecks._value_equal(Layout.GOLD, colors["gold"])
			and GoldHudChecks._value_equal(Layout.GOLD_TEXT, colors["gold_text"])
			and GoldHudChecks._value_equal(Layout.TEXT_WHITE, colors["text_white"])
			and GoldHudChecks._value_equal(Layout.TEXT_BODY, colors["text_body"])
			and GoldHudChecks._value_equal(Layout.TEXT_DIM, colors["text_dim"])
			and GoldHudChecks._value_equal(Layout.SLATE, colors["slate"])
		),
		"Hero panel palette follows ui_theme"
	)
	var core_colors: Dictionary = data["core_colors"]
	check.call(
		(
			GoldHudChecks._value_equal(Layout.RED, core_colors["red"])
			and GoldHudChecks._value_equal(Layout.WHITE, core_colors["white"])
		),
		"Hero panel close and item-icon ink follow the source core palette"
	)
	for frame in frames:
		var state: Dictionary = frame["state"]
		var ops := Layout.ops(state, _fake_measure, bool(frame["cheap_alpha"]), int(state["ticks"]))
		var mismatch := _mismatch(ops, frame["ops"])
		check.call(
			mismatch == -1,
			"Hero panel %s matches the source ops (first mismatch %d)" % [frame["label"], mismatch]
		)
		_check_rects(check, state, frame)
	var dead_state: Dictionary = frames[0]["state"].duplicate(true)
	dead_state["alive"] = false
	check.call(
		Layout.ops(dead_state, _fake_measure).is_empty(), "A dead selected hero paints no panel"
	)
	_check_view_wiring(check, frames[2])


func _check_rects(check: Callable, state: Dictionary, frame: Dictionary) -> void:
	var buttons: Dictionary = frame["buttons"]
	var ui_rects: Dictionary = frame["ui_rects"]
	check.call(
		GoldHudChecks._value_equal(_rect_array(Layout.panel_rect(state)), ui_rects["hero_panel"]),
		"Hero panel rect matches the source ui_rects for %s" % frame["label"]
	)
	for pair in [
		["hero_close", Layout.close_rect(state)],
		["toggle_autocast", Layout.autocast_rect(state)],
		["hero_open_items", Layout.item_shop_rect(state)],
	]:
		var key := String(pair[0])
		var rect: Rect2i = pair[1]
		check.call(
			GoldHudChecks._value_equal(_rect_array(rect), buttons[key]),
			"%s rect matches the source ui_buttons for %s" % [key, frame["label"]]
		)
	for index in range(Layout.ITEM_COUNT):
		var key := "hero_item_slot_%d" % index
		check.call(
			GoldHudChecks._value_equal(
				_rect_array(Layout.item_slot_rect(state, index)), buttons[key]
			),
			"%s rect matches the source ui_buttons for %s" % [key, frame["label"]]
		)
	var max_level := int(state["max_level"])
	if int(state["level"]) < max_level:
		check.call(
			GoldHudChecks._value_equal(
				_rect_array(Layout.upgrade_rect(state)), buttons["popup_upgrade_hero"]
			),
			"Upgrade rect matches the source ui_buttons for %s" % frame["label"]
		)
	else:
		check.call(
			not buttons.has("popup_upgrade_hero"),
			"Max-level hero does not register an upgrade button"
		)


func _check_view_wiring(check: Callable, frame: Dictionary) -> void:
	var view := PrototypeView.new()
	var order: Array = view.overlay_paint_order()
	check.call(
		(
			order.find("hero_panel") == order.find("build_popup") + 1
			and order.find("end_overlay") == order.find("hero_panel") + 1
			and order.back() == "boss_death"
		),
		"Hero panel paints after the build popup, before the end overlay, with boss death last"
	)
	var world := Prototype.new()
	check.call(
		view.hero_panel_draw_ops(world, _fake_measure, 0, Vector2i.ZERO).is_empty(),
		"No selected-hero snapshot paints no hero panel"
	)
	var state: Dictionary = frame["state"]
	view.hero_panel_state = state
	var mouse: Array = frame["mouse"]
	var actual := view.hero_panel_draw_ops(
		world, _fake_measure, int(state["ticks"]), Vector2i(int(mouse[0]), int(mouse[1]))
	)
	check.call(
		_mismatch(actual, frame["ops"]) == -1,
		"The view builds the hero panel from the screen snapshot"
	)
	view.free()
