extends RefCounted
## Layer 9bv11: replay the source tower-hover range and tooltip as view-only drawing.

const Layout = preload("res://scripts/ui/tower_hover_layout.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/tower_hover_source.json"


static func _fake_measure(text: String, font_size: int) -> Vector2i:
	return Vector2i(int(font_size * 0.55) * text.length(), font_size)


static func _mismatch_detail(actual: Array, expected: Array) -> String:
	if actual.size() != expected.size():
		return "size %d != %d" % [actual.size(), expected.size()]
	for index in range(expected.size()):
		if actual[index] != expected[index]:
			return "op %d got %s, expected %s" % [index, str(actual[index]), str(expected[index])]
	return "none"


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Tower-hover source fixture parses")
	if not (data is Dictionary):
		return
	var frames: Array = data["frames"]
	var total_ops := 0
	for frame in frames:
		total_ops += frame["ops"].size()
	check.call(
		frames.size() == 3 and total_ops == 66,
		"Tower-hover oracle pins 3 frames and 66 ops (got %d)" % total_ops
	)
	for frame in frames:
		var state: Variant = frame["state"]
		var ops: Array = []
		if state is Dictionary:
			ops = Layout.ops(state, _fake_measure)
		var detail := _mismatch_detail(ops, frame["ops"])
		check.call(
			detail == "none",
			"Tower-hover %s source-op parity: %s" % [String(frame["name"]), detail]
		)
	_check_view_wiring(check, frames[0])


func _check_view_wiring(check: Callable, frame: Dictionary) -> void:
	var view := PrototypeView.new()
	check.call(
		view.tower_hover_draw_ops(_fake_measure).is_empty(),
		"No tower-hover snapshot paints nothing"
	)
	view.tower_hover_state = frame["state"].duplicate(true)
	var actual := view.tower_hover_draw_ops(_fake_measure)
	var detail := _mismatch_detail(actual, frame["ops"])
	check.call(detail == "none", "PrototypeView tower-hover source-op parity: %s" % detail)
	view.free()
