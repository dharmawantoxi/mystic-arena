extends RefCounted
## Layer 9bv12: replay the source build-slot hover glow and hint as view-only drawing.

const Layout = preload("res://scripts/ui/slot_hover_layout.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/slot_hover_source.json"


static func _fake_measure(text: String, font_size: int) -> Vector2i:
	return Vector2i(int(font_size * 0.55) * text.length(), font_size)


static func _value_equal(actual: Variant, expected: Variant) -> bool:
	if expected is Dictionary:
		if not (actual is Dictionary) or actual.size() != expected.size():
			return false
		for key in expected:
			if not actual.has(key) or not _value_equal(actual[key], expected[key]):
				return false
		return true
	if expected is Array:
		if not (actual is Array) or actual.size() != expected.size():
			return false
		for index in range(expected.size()):
			if not _value_equal(actual[index], expected[index]):
				return false
		return true
	if expected is float or expected is int:
		return (actual is float or actual is int) and absf(float(actual) - float(expected)) < 1e-6
	return actual == expected


static func _mismatch_detail(actual: Array, expected: Array) -> String:
	if actual.size() != expected.size():
		return "size %d != %d" % [actual.size(), expected.size()]
	for index in range(expected.size()):
		if not _value_equal(actual[index], expected[index]):
			return "op %d got %s, expected %s" % [index, str(actual[index]), str(expected[index])]
	return "none"


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Slot-hover source fixture parses")
	if not (data is Dictionary):
		return
	var frames: Array = data["frames"]
	var total_ops := 0
	for frame in frames:
		total_ops += frame["ops"].size()
	check.call(
		frames.size() == 4 and total_ops == 27,
		"Slot-hover oracle pins 4 frames and 27 ops (got %d)" % total_ops
	)
	for frame in frames:
		var state: Variant = frame["state"]
		var ops: Array = []
		if state is Dictionary:
			ops = Layout.ops(state, _fake_measure)
		var detail := _mismatch_detail(ops, frame["ops"])
		check.call(
			detail == "none", "Slot-hover %s source-op parity: %s" % [String(frame["name"]), detail]
		)
	_check_view_wiring(check, frames[0], frames[2])


func _check_view_wiring(check: Callable, frame: Dictionary, fraction: Dictionary) -> void:
	var view := PrototypeView.new()
	check.call(
		view.slot_hover_draw_ops(_fake_measure).is_empty(), "No slot-hover snapshot paints nothing"
	)
	view.slot_hover_state = frame["state"].duplicate(true)
	var detail := _mismatch_detail(view.slot_hover_draw_ops(_fake_measure), frame["ops"])
	check.call(detail == "none", "PrototypeView slot-hover source-op parity: %s" % detail)
	view.slot_hover_state = fraction["state"].duplicate(true)
	detail = _mismatch_detail(view.slot_hover_draw_ops(_fake_measure), fraction["ops"])
	check.call(detail == "none", "PrototypeView pins fractional slot anchors: %s" % detail)
	view.free()
