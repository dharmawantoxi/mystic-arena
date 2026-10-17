extends RefCounted
## Layer 9av: replays the `LevelIntroScreen.draw()` oracle fixture through
## `level_intro_layout.gd`. `level_intro_draw_source_oracle.py` runs the REAL
## class from `_render.py` under a recording pygame shim (0.55*size px per
## glyph), so every op (kind, geometry, colour, surface alpha, order) below
## comes from the source.

const Layout = preload("res://scripts/ui/level_intro_layout.gd")
const FIXTURE := "res://tests/fixtures/level_intro_draw_source.json"
const COMPARED_KEYS := [
	"kind",
	"alpha",
	"rect",
	"color",
	"mult",
	"width",
	"radius",
	"center",
	"a",
	"b",
	"points",
	"text",
	"size",
	"pos",
	"w",
	"h"
]


static func _measure(text: String, font_size: int) -> Vector2i:
	return Vector2i(int(float(font_size) * 0.55) * text.length(), font_size)


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


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Level intro draw fixture parses")
	if not (data is Dictionary):
		return
	var screen := Vector2i(int(data["screen"][0]), int(data["screen"][1]))
	check.call(is_equal_approx(float(data["glyph_factor"]), 0.55), "oracle glyph factor is 0.55")
	for timer in [0, 1, 15, 29, 30, 31, 90]:
		var expected := int(255.0 * (float(timer) / 30.0)) if timer < 30 else 255
		check.call(Layout.fade_alpha(timer) == expected, "fade_alpha(%d) = %d" % [timer, expected])
	check.call(Layout.theme_tint("desert") == [100, 60, 20], "desert tint")
	check.call(Layout.theme_tint("mystery") == [20, 40, 20], "unknown theme falls back to forest")
	check.call(Layout.THEME_TINTS.size() == 33, "33 named theme tints + forest fallback")
	check.call(Layout.letter("ABC") == "A B C", "letter() spaces glyphs")
	for frame in data["frames"]:
		var label := "%s t=%d ms=%d" % [frame["label"], int(frame["timer"]), int(frame["ticks"])]
		var expected_ops: Array = frame["ops"]
		var actual_ops := Layout.ops(
			frame["state"], int(frame["timer"]), int(frame["ticks"]), _measure, screen
		)
		check.call(
			actual_ops.size() == expected_ops.size(),
			"%s: %d ops (got %d)" % [label, expected_ops.size(), actual_ops.size()]
		)
		var first_bad := -1
		for index in range(mini(actual_ops.size(), expected_ops.size())):
			if not _op_equal(actual_ops[index], expected_ops[index]):
				first_bad = index
				break
		check.call(
			first_bad < 0,
			(
				"%s: ops match (first mismatch #%d: got %s, want %s)"
				% [
					label,
					first_bad,
					str(actual_ops[first_bad]) if first_bad >= 0 else "",
					str(expected_ops[first_bad]) if first_bad >= 0 else ""
				]
			)
		)
		var kinds := {}
		for op in expected_ops:
			kinds[op["kind"]] = int(kinds.get(op["kind"], 0)) + 1
		var prompt_drawn := int(frame["timer"]) > 30
		var has_prompt := false
		for op in actual_ops:
			if op["kind"] == "text" and String(op["text"]) == "PRESS SPACE TO BEGIN":
				has_prompt = true
		check.call(has_prompt == prompt_drawn, "%s: prompt only after the fade" % label)
		check.call(
			int(kinds.get("darken", 0)) == 1 and int(kinds.get("fill", 0)) == 1,
			"%s: darken + tint" % label
		)
	# ring semantics: the aura discs carry the annulus the overwrite leaves
	var sample: Dictionary = data["frames"][2]
	var ops := Layout.ops(
		sample["state"], int(sample["timer"]), int(sample["ticks"]), _measure, screen
	)
	var rings := 0
	var innermost_zero := false
	for op in ops:
		if op["kind"] == "circle" and op.has("ring_inner"):
			rings += 1
			if int(op["ring_inner"]) == 0:
				innermost_zero = true
	check.call(rings > 10 and innermost_zero, "aura / glow discs expose ring_inner (innermost = 0)")
