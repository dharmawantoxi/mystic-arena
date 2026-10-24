extends RefCounted
## Layer 9bv4: `ControllerManager.draw_hint_bar` replay. `input_hint_draw_source_oracle.py`
## runs the REAL source method under the recording pygame shim; `InputHintLayout` must rebuild
## every op from the hint pairs, and the arena view must paint the controller's live hints in
## the source slot (after the tactical banner, before the level intro).

const Layout = preload("res://scripts/ui/input_hint_layout.gd")
const GoldHudChecks = preload("res://tests/gold_hud_draw_checks.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const Runtime = preload("res://scripts/input/controller_runtime.gd")
const FIXTURE := "res://tests/fixtures/input_hint_draw_source.json"


## The oracle's text metrics: `int(size * 0.55)` px per glyph, `size` px tall.
static func _fake_measure(text: String, font_size: int) -> Vector2i:
	return Vector2i(int(font_size * 0.55) * text.length(), font_size)


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Input hint draw fixture parses")
	if not (data is Dictionary):
		return
	var frames: Array = data["frames"]
	var ops_total := 0
	for frame in frames:
		ops_total += frame["ops"].size()
	check.call(
		frames.size() == 6 and ops_total == 89,
		"Input hint oracle pins 6 source frames and 89 draw ops"
	)
	for frame in frames:
		var ops := Layout.ops(frame["hints"], _fake_measure)
		var mismatch := GoldHudChecks._first_mismatch(ops, frame["ops"])
		check.call(
			mismatch == -1,
			"Input hints %s match the source ops (first mismatch %d)" % [frame["label"], mismatch]
		)
	_check_view_wiring(check)


func _check_view_wiring(check: Callable) -> void:
	var view := PrototypeView.new()
	var order: Array = view.overlay_paint_order()
	check.call(
		(
			order.find("input_hints") == order.find("tactical_feedback") + 1
			and order.find("input_hints") == order.find("level_intro") - 1
		),
		"The hint bar paints after the tactical banner and right before the level intro"
	)
	var world := Prototype.new()
	check.call(
		view.input_hints.is_empty() and view.input_hint_draw_ops(world, _fake_measure).is_empty(),
		"Mouse / keyboard mode (no hints) paints no hint bar"
	)
	var runtime := Runtime.new()
	var hints: Array = runtime.get_hints("game")
	view.input_hints = hints
	var expected: Array = []
	if not view.input_hints_blocked(world):
		expected = Layout.ops(hints, _fake_measure)
	check.call(
		(
			not hints.is_empty()
			and (
				GoldHudChecks._first_mismatch(
					view.input_hint_draw_ops(world, _fake_measure), expected
				)
				== -1
			)
		),
		"The view paints the controller's live get_hints pairs unless a cinematic runs"
	)
	runtime.free()
	view.free()
