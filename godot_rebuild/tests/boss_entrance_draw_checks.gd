extends RefCounted
## Layer 9bq11: replays the fixture of `boss_entrance_draw_source_oracle.py` through
## `boss_entrance_layout.gd`. The oracle runs the REAL `Boss._draw_entrance` under the recording
## pygame shim, so the aura, the word wrap and every shadow/text position come from the source.
## Font metrics are the one thing the shim owns: `int(size * 0.55)` px per glyph and a height of
## `size`, which is exactly the stub measure handed to the layout here.

const Layout = preload("res://scripts/ui/boss_entrance_layout.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/boss_entrance_draw_source.json"
const COMPARED_KEYS := {
	"circle": ["center", "radius", "width", "color", "mult"],
	"text": ["text", "size", "style", "color", "mult", "pos"],
}
const TOTAL_OPS := 19
const ANCHOR := 640
const ANCHOR_Y := 360


## The recording shim's `Font.size`: `int(size * GLYPH_FACTOR) * len(text)` by `size`.
static func measure(text: String, size_px: int) -> Vector2:
	return Vector2(float(int(float(size_px) * 0.55) * text.length()), float(size_px))


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
	if str(actual.get("kind", "")) != str(expected.get("kind", "")):
		return false
	var keys: Array = COMPARED_KEYS.get(str(expected.get("kind", "")), [])
	for key_name in keys:
		if expected.has(key_name) != actual.has(key_name):
			return false
		if expected.has(key_name) and not _value_equal(actual[key_name], expected[key_name]):
			return false
	return true


static func _first_mismatch(actual: Array, expected: Array) -> int:
	for index in range(mini(actual.size(), expected.size())):
		if not _op_equal(actual[index], expected[index]):
			return index
	return -1 if actual.size() == expected.size() else mini(actual.size(), expected.size())


static func _report(label: String, actual: Array, expected: Array) -> String:
	var index := _first_mismatch(actual, expected)
	if index == -1:
		return "%s matches the source ops" % label
	var mine: Variant = actual[index] if index < actual.size() else {}
	var theirs: Variant = expected[index] if index < expected.size() else {}
	return (
		"%s differs at op %d/%d: %s vs source %s"
		% [label, index, expected.size(), str(mine), str(theirs)]
	)


static func _frame(frames: Array, label: String) -> Dictionary:
	for frame in frames:
		if String(frame["label"]) == label:
			return frame
	return {}


static func _from_frame(frame: Dictionary) -> Array:
	return Layout.ops(
		ANCHOR,
		ANCHOR_Y,
		int(frame["radius"]),
		int(frame["entrance_timer"]),
		int(frame["max_timer"]),
		frame["entrance_color"],
		String(frame["entrance_text"]),
		String(frame["boss_class"]) == "true",
		float(frame["anim_time"]),
		measure
	)


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Boss entrance fixture parses")
	if not (data is Dictionary):
		return
	var total := 0
	for frame in data["frames"]:
		total += frame["ops"].size()
	check.call(
		int(data["frames"].size()) == 8 and total == TOTAL_OPS,
		"Boss entrance oracle pins 8 frames and %d draw ops (got %d)" % [TOTAL_OPS, total]
	)
	_check_frames(check, data)
	_check_shape(check, data)
	_check_view_wiring(check, data)


func _check_frames(check: Callable, data: Dictionary) -> void:
	for frame in data["frames"]:
		var actual := _from_frame(frame)
		check.call(
			_first_mismatch(actual, frame["ops"]) == -1,
			_report("Entrance %s" % frame["label"], actual, frame["ops"])
		)


func _check_shape(check: Callable, data: Dictionary) -> void:
	var counts: Array = []
	for frame in data["frames"]:
		counts.append(frame["ops"].size())
	check.call(
		counts == [2, 3, 1, 1, 2, 3, 4, 3],
		"The aura appears once it has a radius and the title only above half the timer"
	)
	var quarter: Dictionary = _frame(data["frames"], "quarter_body")
	check.call(
		(
			int(quarter["ops"][0]["radius"]) == 16
			and _value_equal(quarter["ops"][0]["color"], [255, 200, 60, 150])
		),
		"`int(radius * progress * 2)` and `int(200 * (1 - progress))` drive the aura"
	)
	var half: Dictionary = _frame(data["frames"], "half_body_text_gone")
	check.call(
		int(half["ops"].size()) == 1 and str(half["ops"][0]["kind"]) == "circle",
		"`entrance_timer > max_timer // 2` hides the title, so only the aura remains"
	)
	var wrapped: Dictionary = _frame(data["frames"], "wrapped_body")
	check.call(
		(
			String(wrapped["ops"][1]["text"]) != String(wrapped["ops"][3]["text"])
			and String(wrapped["ops"][0]["text"]) == String(wrapped["ops"][1]["text"])
			and int(wrapped["ops"][3]["pos"][1]) - int(wrapped["ops"][1]["pos"][1]) == 34
		),
		"Long titles wrap per word into lines 34 px apart, shadow first"
	)
	var long_word: Dictionary = _frame(data["frames"], "long_word_true")
	check.call(
		int(long_word["ops"][1]["size"]) == 28 and int(long_word["ops"].size()) == 3,
		"A word wider than 1000 px keeps its own line and a true boss uses 28 px"
	)
	var shadow: Dictionary = _frame(data["frames"], "quarter_body")
	check.call(
		(
			_value_equal(shadow["ops"][1]["color"], [0, 0, 0, 255])
			and int(shadow["ops"][2]["pos"][0]) - int(shadow["ops"][1]["pos"][0]) == -2
			and int(shadow["ops"][2]["pos"][1]) - int(shadow["ops"][1]["pos"][1]) == -2
		),
		"The black shadow sits 2 px down-right of the text and leads it in the op list"
	)


func _check_view_wiring(check: Callable, data: Dictionary) -> void:
	var view := PrototypeView.new()
	var boss := BossState.new()
	boss.alive = true
	boss.position = Vector2(ANCHOR, ANCHOR_Y)
	boss.radius = 32.0
	boss.boss_class = "body"
	boss.entrance_timer = 0
	check.call(
		view.boss_entrance_draw_ops(boss, measure).is_empty(),
		"An entrance that already finished paints nothing"
	)
	var quarter: Dictionary = _frame(data["frames"], "quarter_body")
	boss.entrance_color = Color8(255, 200, 60)
	boss.entrance_text = String(quarter["entrance_text"])
	boss.entrance_timer = int(quarter["entrance_timer"])
	boss.anim_time = int(quarter["anim_time"])
	var actual := view.boss_entrance_draw_ops(boss, measure)
	check.call(
		_first_mismatch(actual, quarter["ops"]) == -1,
		_report("Entrance wiring", actual, quarter["ops"])
	)
	boss.boss_class = "true"
	check.call(
		(
			int(view.boss_entrance_draw_ops(boss, measure)[0]["radius"]) == 16
			and Layout.max_entrance(true) == 180
			and Layout.max_entrance(false) == 120
		),
		"A true boss uses the 180 tick entrance and keeps the body radius formula"
	)
	boss.alive = false
	check.call(
		view.boss_entrance_draw_ops(boss, measure).is_empty(), "A dead boss paints no entrance"
	)
	view.free()
