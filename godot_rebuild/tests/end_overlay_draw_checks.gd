extends RefCounted
## Layers 9bv5 + 9bv6: `Overlay.draw` replay. `end_overlay_draw_source_oracle.py` runs the REAL
## source overlay (cheap-alpha branch) under the recording pygame shim; `EndOverlayLayout` must
## rebuild every op (backdrop, rays, glow, title, sparkles, stats, level unlock popup, action
## hint, achievements) and the arena view must paint the screen's end state in the source slot.

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
		"unlock": _unlock(frame),
	}


## What the screen hands over: empty unless this win opened a level never won before.
static func _unlock(frame: Dictionary) -> Dictionary:
	var unlock: Variant = frame.get("unlock")
	if not (unlock is Dictionary):
		return {}
	var completed: Array = unlock["completed"]
	var level := int(String(frame["title"]).get_slice(".", 1))
	if not completed.has(float(level)) or completed.has(float(unlock["level"])):
		return {}
	var timer := int(unlock["timer_before"])
	if timer < Layout.UNLOCK_DELAY:
		timer += 1
	var mouse: Array = unlock["mouse"]
	var button := Layout.play_button_rect(timer)
	return {
		"timer": timer,
		"level": int(unlock["level"]),
		"name": unlock["name"],
		"hp_mult": float(unlock["hp_mult"]),
		"difficulty": unlock["difficulty"],
		"hover": button.has_point(Vector2i(int(mouse[0]), int(mouse[1]))),
		"boss": unlock["boss"],
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
		frames.size() == 8 and ops_total == 2210,
		"End overlay oracle pins 8 source frames and 2210 draw ops (got %d)" % ops_total
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
	for frame in frames:
		var unlock: Variant = frame.get("unlock")
		if unlock is Dictionary and not _unlock(frame).is_empty():
			var rect := Layout.play_button_rect(int(_unlock(frame)["timer"]))
			var want: Array = unlock["button"]
			check.call(
				GoldHudChecks._value_equal(
					[rect.position.x, rect.position.y, rect.size.x, 30], want
				),
				"PLAY NEXT LEVEL rect %s matches g.ui_buttons for %s" % [rect, frame["label"]]
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
			order.find("end_overlay") > order.find("tactical_feedback")
			and order.find("end_overlay") < order.find("input_hints")
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
	check.call(view.unlock_play_rect() == Rect2(), "No unlock popup registers no PLAY button")
	view.end_overlay_state = {"victory": true, "unlock": {"level": 4}}
	view.unlock_popup_timer = Layout.UNLOCK_DELAY
	check.call(
		view.unlock_play_rect() == Rect2(1275, 440, 310, 30),
		"pygame's capped unlock timer leaves the PLAY button 400 px right (x = 1275)"
	)
	view.free()
