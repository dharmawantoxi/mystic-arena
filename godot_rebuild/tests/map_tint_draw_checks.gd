extends RefCounted
## Layer 9bh: replays the ambient-tint oracle fixture through `map_tint_layout.gd`.
## `map_tint_draw_source_oracle.py` runs the REAL `MapRenderer.draw()` from
## `_render.py` under a recording pygame shim, with the `ambient_tint` of every theme
## read from the real theme literals of `map_components/_bundle.py`, in both the
## `cheap_alpha` (alpha blit) and the multiply paths.

const Layout = preload("res://scripts/ui/map_tint_layout.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/map_tint_draw_source.json"
const COMPARED_KEYS := ["kind", "rect", "color", "mult", "blend"]


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


## Index of the first differing op, or -1 when both lists match exactly.
static func _first_mismatch(actual: Array, expected: Array) -> int:
	if actual.size() != expected.size():
		return mini(actual.size(), expected.size())
	for index in range(expected.size()):
		if not _op_equal(actual[index], expected[index]):
			return index
	return -1


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Map tint draw fixture parses")
	if not (data is Dictionary):
		return
	check.call(
		data["frames"].size() == 108, "Map tint oracle pins 108 frames (54 themes x 2 paths)"
	)
	_check_table(check, data)
	_check_frames(check, data)
	_check_quirks(check, data)
	_check_view_wiring(check)


func _check_table(check: Callable, data: Dictionary) -> void:
	var tints: Dictionary = data["tints"]
	check.call(
		tints.size() == 54 and Layout.TINTS.size() == tints.size(), "54 themes carry a tint entry"
	)
	var wrong: Array = []
	for theme_value in tints:
		var theme := String(theme_value)
		var expected: Variant = tints[theme]
		var actual: Variant = Layout.tint_for(theme)
		var same: bool = Layout.TINTS.has(theme)
		if expected == null:
			same = same and actual == null
		else:
			same = same and _value_equal(actual, expected)
		if not same:
			wrong.append(theme)
	check.call(wrong.is_empty(), "Every theme tint matches the source table: %s" % str(wrong))


func _check_frames(check: Callable, data: Dictionary) -> void:
	var screen := Vector2i(int(data["screen"][0]), int(data["screen"][1]))
	var drawn := 0
	for frame_value in data["frames"]:
		var frame: Dictionary = frame_value
		var ops: Array = Layout.ops(String(frame["theme"]), screen, bool(frame["cheap_alpha"]))
		var bad := _first_mismatch(ops, frame["ops"])
		check.call(
			bad < 0,
			(
				"Map tint %s (cheap_alpha %s): %d ops match source (got %s)"
				% [frame["theme"], str(frame["cheap_alpha"]), frame["ops"].size(), str(ops)]
			)
		)
		drawn += frame["ops"].size()
	check.call(drawn == 106, "Map tint oracle pins 106 recorded draw ops")


func _check_quirks(check: Callable, data: Dictionary) -> void:
	var desert: Array = Layout.ops("desert")
	check.call(
		(
			desert.size() == 1
			and _value_equal(desert[0]["color"], [255, 220, 150, 15])
			and int(desert[0]["blend"]) == 0
		),
		"cheap_alpha blits the theme tint as is (desert warm yellow, alpha 15)"
	)
	var multiply: Array = Layout.ops("desert", Vector2i(1280, 720), false)
	check.call(
		(
			_value_equal(multiply[0]["color"], [255, 252, 248, 255])
			and int(multiply[0]["blend"]) == Layout.BLEND_RGB_MULT
		),
		"Without cheap_alpha the screen is multiplied by 255 - (255 - c) * a / 255"
	)
	check.call(
		(
			Layout.ops("forest").is_empty()
			and Layout.ops("forest", Vector2i(1280, 720), false).is_empty()
		),
		"Forest has no ambient tint"
	)
	check.call(
		Layout.ops("mystery").is_empty() and Layout.ops("").is_empty(),
		"An unknown theme falls back to forest and draws nothing"
	)
	var small: Array = Layout.ops("ice", Vector2i(960, 540))
	check.call(
		_value_equal(small[0]["rect"], [0, 0, 960, 540]), "The tint covers the whole map surface"
	)
	var tinted := 0
	for theme in data["tints"]:
		if data["tints"][theme] != null:
			tinted += 1
	check.call(tinted == 53, "53 of 54 themes tint the map (forest does not)")


func _check_view_wiring(check: Callable) -> void:
	var world := Prototype.new()
	var view := PrototypeView.new()
	world.level_config = {"map_theme": "desert"}
	check.call(
		_value_equal(view.map_tint_draw_ops(world)[0]["color"], [255, 220, 150, 15]),
		"PrototypeView tints the map with the level's theme"
	)
	world.level_config = {"map_theme": "forest"}
	check.call(view.map_tint_draw_ops(world).is_empty(), "A forest level paints no tint")
	world.level_config = {}
	check.call(view.map_tint_draw_ops(world).is_empty(), "A level without a theme paints no tint")
	view.free()
