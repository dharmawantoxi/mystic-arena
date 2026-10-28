extends RefCounted
## Layer 9bv14: replay `Tower.draw`'s selected range, upgrade flash, and archer muzzle glow.

const Layout = preload("res://scripts/ui/tower_fx_layout.gd")
const SiegeView = preload("res://scenes/siege/siege_view.gd")
const FIXTURE := "res://tests/fixtures/tower_fx_source.json"


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
	check.call(data is Dictionary, "Tower-FX source fixture parses")
	if not (data is Dictionary):
		return
	var frames: Array = data["frames"]
	var total_ops := 0
	for frame in frames:
		total_ops += frame["ops"].size()
	check.call(
		frames.size() == 7 and total_ops == 14,
		"Tower-FX oracle pins 7 frames and 14 ops (got %d)" % total_ops
	)
	var heights: Dictionary = data["bow_heights"]
	check.call(
		(
			heights.size() == Layout.BOW_HEIGHTS.size()
			and int(heights["1"]) == Layout.BOW_HEIGHTS[0]
			and int(heights["6"]) == Layout.BOW_HEIGHTS[5]
		),
		"Archer bow heights match the source level table"
	)
	for frame in frames:
		var state: Dictionary = frame["state"]
		var ops := Layout.ops(state)
		var detail := _mismatch_detail(ops, frame["ops"])
		check.call(
			detail == "none", "Tower-FX %s source-op parity: %s" % [String(frame["name"]), detail]
		)
	_check_view_wiring(check, frames)


func _check_view_wiring(check: Callable, frames: Array) -> void:
	var view := SiegeView.new()
	var combined: Dictionary = {}
	var quiet: Dictionary = {}
	for frame in frames:
		if String(frame["name"]) == "archer_all_fx":
			combined = frame
		elif String(frame["name"]) == "no_tower_fx":
			quiet = frame
	var detail := _mismatch_detail(view.tower_fx_ops(combined["state"]), combined["ops"])
	check.call(detail == "none", "SiegeView tower-FX source-op parity: %s" % detail)
	check.call(
		(
			view.tower_fx_before_ops(quiet["state"]).is_empty()
			and view.tower_fx_after_ops(quiet["state"]).is_empty()
		),
		"A quiet tower paints no range, upgrade, or muzzle FX"
	)
	var before := view.tower_fx_before_ops(combined["state"])
	var after := view.tower_fx_after_ops(combined["state"])
	check.call(
		before.size() == 3 and after.size() == 2,
		"Source order splits three pre-body ops and two post-body ops"
	)
	check.call(
		(
			Layout.color_for("archer") == [100, 220, 120]
			and Layout.color_for("mage") == [180, 80, 220]
		),
		"Tower range colours follow TOWER_TYPE_COLORS"
	)
	view.free()
