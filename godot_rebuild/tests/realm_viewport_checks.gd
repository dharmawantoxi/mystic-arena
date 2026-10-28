extends RefCounted
## Layer 9bv16: the source realm layer calls `surface.get_size()` every frame.
## `nyxareth_realm_draw_source_oracle.py` records a widened 1560x720 display as
## the `wide_display` frame; this suite replays it through the layout AND the
## live view, proving the stars now wrap on the real viewport instead of the
## hard-coded 1280x720 arena. The default surface is still pinned to 1280x720.

const Layout = preload("res://scripts/ui/nyxareth_realm_layout.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const FIXTURE := "res://tests/fixtures/nyxareth_realm_draw_source.json"
const COMPARED_KEYS := ["kind", "rect", "color", "mult", "width", "radius", "blend"]


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
	for key_name in COMPARED_KEYS:
		if expected.has(key_name) != actual.has(key_name):
			return false
		if expected.has(key_name) and not _value_equal(actual[key_name], expected[key_name]):
			return false
	return true


static func _first_mismatch(actual: Array, expected: Array) -> int:
	if actual.size() != expected.size():
		return mini(actual.size(), expected.size())
	for index in range(expected.size()):
		if not _op_equal(actual[index], expected[index]):
			return index
	return -1


static func _frame(frames: Array, label: String) -> Dictionary:
	for frame in frames:
		if String(frame["label"]) == label:
			return frame
	return {}


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Nyxareth realm fixture parses for the viewport suite")
	if not (data is Dictionary):
		return
	var wide: Dictionary = _frame(data["frames"], "wide_display")
	var default: Dictionary = _frame(data["frames"], "layer_full")
	check.call(
		not wide.is_empty() and not default.is_empty(),
		"The oracle pins both a wide and the default arena frame"
	)
	# JSON numbers are floats in Godot; `_value_equal` compares them numerically
	# against the integer literals below (a raw Array == would fail on the type).
	check.call(
		_value_equal(wide["screen"], [1560, 720]) and _value_equal(default["screen"], [1280, 720]),
		"The oracle pins a 1560x720 wide display and a 1280x720 arena"
	)
	check.call(
		Layout.SCREEN_SIZE == Vector2i(1280, 720), "The baked default surface stays 1280x720"
	)

	check.call(
		Layout.size_for_viewport(Vector2(1560, 720)) == Vector2i(1560, 720),
		"A widened viewport sizes the realm to 1560x720"
	)
	check.call(
		Layout.size_for_viewport(Vector2(1280, 720)) == Vector2i(1280, 720),
		"The arena viewport sizes the realm to 1280x720"
	)
	check.call(
		(
			Layout.size_for_viewport(Vector2.ZERO) == Layout.SCREEN_SIZE
			and Layout.size_for_viewport(Vector2(-8, 720)) == Layout.SCREEN_SIZE
		),
		"A detached or zero-sized viewport falls back to the baked default"
	)

	var wide_ops: Array = Layout.ops(
		int(wide["timer"]), float(wide["phase"]), Layout.size_for_viewport(Vector2(1560, 720))
	)
	check.call(
		_first_mismatch(wide_ops, wide["ops"]) == -1,
		"The layout replays the source's wide-display star field exactly"
	)
	check.call(
		_value_equal(wide_ops[0]["rect"], [0, 0, 1560, 720]),
		"The wide cosmic fill covers the whole 1560x720 surface"
	)
	var arena_ops: Array = Layout.ops(
		int(default["timer"]), float(default["phase"]), Layout.SCREEN_SIZE
	)
	check.call(
		_first_mismatch(arena_ops, default["ops"]) == -1,
		"The layout still replays the default arena star field exactly"
	)
	check.call(
		_first_mismatch(wide_ops, arena_ops) != -1,
		"The wide display really changes the star wrap, not just the fill"
	)

	var view := PrototypeView.new()
	check.call(
		view.realm_screen_size == Layout.SCREEN_SIZE,
		"A freshly built view starts on the default arena surface"
	)
	var boss := BossState.new()
	boss.boss_type = "nyxareth"
	boss.active_skill = "4"
	boss.active_skill_timer = int(wide["timer"])
	boss.pulse = float(wide["phase"])
	view.realm_screen_size = Layout.size_for_viewport(Vector2(1560, 720))
	check.call(
		_first_mismatch(view.nyxareth_realm_draw_ops(boss), wide["ops"]) == -1,
		"The live view paints the wide star field from its viewport size"
	)
	boss.active_skill = "3"
	check.call(
		view.nyxareth_realm_draw_ops(boss).is_empty(),
		"Another nyxareth skill paints no realm even on a wide display"
	)
	view.free()
