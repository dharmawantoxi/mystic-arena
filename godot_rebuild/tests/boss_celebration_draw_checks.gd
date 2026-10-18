extends RefCounted
## Layer 9be: replays the `BossDeathAnimation._draw_celebration()` oracle fixture
## through `boss_celebration_layout.gd`. `boss_celebration_draw_source_oracle.py`
## runs the REAL class from `_render.py` (with the real `ui_theme.letter` /
## `draw_icon`) under a recording pygame shim (0.55*size px per glyph), so every
## op (kind, geometry, colour, surface alpha, order) below comes from the source.
## Each frame is replayed three ways: from the recorded state, from the production
## `BossDeathAnimation` ticked with `update()`, and through `PrototypeView`.

const Layout = preload("res://scripts/ui/boss_celebration_layout.gd")
const BossDeath = preload("res://scripts/ui/boss_death_animation.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/boss_celebration_draw_source.json"
const COMPARED_KEYS := [
	"kind",
	"alpha",
	"rect",
	"color",
	"mult",
	"blend",
	"width",
	"radius",
	"center",
	"a",
	"b",
	"text",
	"size",
	"style",
	"pos"
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


## Index of the first differing op, or -1 when both lists match exactly.
static func _first_mismatch(actual: Array, expected: Array) -> int:
	if actual.size() != expected.size():
		return mini(actual.size(), expected.size())
	for index in range(expected.size()):
		if not _op_equal(actual[index], expected[index]):
			return index
	return -1


static func _frame_key(label: String, tick: int) -> String:
	return "%s:%d" % [label, tick]


static func _animation_for(scenario: Dictionary) -> BossDeath:
	var anim := BossDeath.new()
	var screen: Array = scenario["screen"]
	anim.configure(scenario["boss"], int(screen[0]), int(screen[1]))
	return anim


## The celebration begins once the death phase has run its full duration.
static func _start_celebration(anim: BossDeath) -> void:
	for _step in range(anim.duration):
		anim.update()


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Boss celebration draw fixture parses")
	if not (data is Dictionary):
		return
	check.call(
		int(data["duration"]) == BossDeath.TRUE_DURATION, "Oracle death duration matches the port"
	)
	check.call(
		int(data["celebration_duration"]) == BossDeath.CELEBRATION_DURATION,
		"Oracle celebration duration matches the port"
	)
	check.call(absf(float(data["glyph_factor"]) - 0.55) < 1e-9, "Oracle fake glyph factor is 0.55")
	check.call(data["frames"].size() == 20, "Boss celebration oracle pins 20 source frames")
	_check_recorded_frames(check, data)
	_check_production_replay(check, data)
	_check_stages(check, data)
	_check_inactive(check)
	_check_view_wiring(check, data)


func _expect_ops(check: Callable, label: String, actual: Array, expected: Array) -> void:
	var bad := _first_mismatch(actual, expected)
	check.call(
		bad < 0,
		(
			"Boss celebration %s: %d ops match source (first mismatch #%d: got %s, want %s)"
			% [
				label,
				expected.size(),
				bad,
				str(actual[bad]) if 0 <= bad and bad < actual.size() else "",
				str(expected[bad]) if 0 <= bad and bad < expected.size() else ""
			]
		)
	)


func _frame_at(data: Dictionary, label: String, tick: int) -> Dictionary:
	for frame_value in data["frames"]:
		var frame: Dictionary = frame_value
		if String(frame["label"]) == label and int(frame["tick"]) == tick:
			return frame
	return {}


func _frame_ops(data: Dictionary, label: String, tick: int) -> Array:
	return _frame_at(data, label, tick).get("ops", [])


func _check_recorded_frames(check: Callable, data: Dictionary) -> void:
	var scenarios := {}
	for scenario_value in data["scenarios"]:
		scenarios[String(scenario_value["label"])] = scenario_value
	var drawn := 0
	for frame_value in data["frames"]:
		var frame: Dictionary = frame_value
		var anim := _animation_for(scenarios[String(frame["label"])])
		var state: Dictionary = frame["state"]
		anim.celebration_active = bool(state["celebration_active"])
		anim.celebration_timer = int(state["celebration_timer"])
		var key := _frame_key(String(frame["label"]), int(frame["tick"]))
		var ops: Array = Layout.ops(anim, int(frame["ticks"]), _measure, bool(frame["cheap_alpha"]))
		_expect_ops(check, key, ops, frame["ops"])
		drawn += frame["ops"].size()
	check.call(drawn == 547, "Boss celebration oracle pins 547 recorded draw ops")


func _check_production_replay(check: Callable, data: Dictionary) -> void:
	var replayed := 0
	for scenario_value in data["scenarios"]:
		var scenario: Dictionary = scenario_value
		var label := String(scenario["label"])
		var anim := _animation_for(scenario)
		_start_celebration(anim)
		check.call(
			anim.celebration_active, "Boss celebration %s starts after the death phase" % label
		)
		var last_tick := 0
		for frame_value in data["frames"]:
			if String(frame_value["label"]) == label:
				last_tick = maxi(last_tick, int(frame_value["tick"]))
		for tick in range(last_tick + 1):
			var frame := _frame_at(data, label, tick)
			if not frame.is_empty():
				var ops: Array = Layout.ops(
					anim, int(frame["ticks"]), _measure, bool(frame["cheap_alpha"])
				)
				_expect_ops(check, "production " + _frame_key(label, tick), ops, frame["ops"])
				replayed += 1
			anim.update()
	check.call(
		replayed == data["frames"].size(),
		"Boss celebration production state replays every recorded frame (%d)" % replayed
	)


func _count(ops: Array, kind: String) -> int:
	var total := 0
	for op_value in ops:
		if String(op_value["kind"]) == kind:
			total += 1
	return total


func _check_stages(check: Callable, data: Dictionary) -> void:
	var first := _frame_ops(data, "abaddon", 0)
	check.call(
		_count(first, "darken") == 0 and _count(first, "fill") == 1,
		"Celebration start: no darken at alpha 0, but the gold tint is already drawn"
	)
	check.call(
		int(first[1]["mult"]) == 0 and int(first[first.size() - 1]["mult"]) == 0,
		"Celebration start: the title texts are blitted at surface alpha 0"
	)
	var bounce := _frame_ops(data, "abaddon", 4)
	check.call(
		int(bounce[2]["pos"][1]) > int(_frame_ops(data, "abaddon", 36)[2]["pos"][1]) + 30,
		"Celebration bounce: the text starts far below its resting row"
	)
	var before_reward := _frame_ops(data, "abaddon", 36)
	var with_reward := _frame_ops(data, "abaddon", 37)
	check.call(
		_count(before_reward, "circle") == 0 and _count(with_reward, "circle") == 4,
		"Reward appears after 30 %: coin (2 circles) + star dots (2)"
	)
	check.call(
		with_reward.size() - before_reward.size() == 15 and _count(with_reward, "line") == 8,
		"Reward block adds coin, `$`, gold, HERO UNLOCKED! and two 4-line stars"
	)
	check.call(
		_frame_ops(data, "abaddon", 49).size() - _frame_ops(data, "abaddon", 48).size() == 12,
		"Six sparkles (two discs each) appear above 40 %"
	)
	check.call(
		_frame_ops(data, "abaddon", 61).size() - _frame_ops(data, "abaddon", 60).size() == 1,
		"The skip hint appears above 50 %"
	)
	var hint: Dictionary = _frame_ops(data, "abaddon", 61).back()
	check.call(
		String(hint["text"]) == "[SPACE] to continue" and int(hint["size"]) == 24,
		"Skip hint reads `[SPACE] to continue` at 24 px"
	)
	var unlock := ""
	for op_value in with_reward:
		if String(op_value["kind"]) == "text" and String(op_value["text"]).contains("U N L O C K"):
			unlock = String(op_value["text"])
	check.call(unlock == "H E R O   U N L O C K E D !", "`HERO UNLOCKED!` is letter-spaced")
	check.call(
		(
			_count(_frame_ops(data, "abaddon", 80), "fill") == 1
			and _count(_frame_ops(data, "abaddon", 102), "fill") == 0
		),
		"The gold tint ends at 85 %"
	)
	var cheap_off := _frame_ops(data, "abaddon", 40)
	var cheap_on := _frame_ops(data, "abaddon", 37)
	check.call(
		_count(cheap_on, "text") - _count(cheap_off, "text") == 5,
		"Without cheap_alpha the title keeps one shadow copy instead of six"
	)


func _check_inactive(check: Callable) -> void:
	var anim := BossDeath.new()
	check.call(Layout.ops(anim, 0, _measure).is_empty(), "A fresh animation draws no celebration")
	anim.configure({"name": "Test", "boss_class": "true"}, 1280, 720)
	check.call(Layout.ops(anim, 0, _measure).is_empty(), "The death phase draws no celebration")
	_start_celebration(anim)
	check.call(not Layout.ops(anim, 0, _measure).is_empty(), "Celebration draws once it starts")
	var skipped: bool = anim.handle_skip(KEY_SPACE)
	check.call(
		skipped and Layout.ops(anim, 0, _measure).is_empty(), "A skipped celebration draws nothing"
	)


func _check_view_wiring(check: Callable, data: Dictionary) -> void:
	var world := Prototype.new()
	var view := PrototypeView.new()
	check.call(
		view.boss_celebration_draw_ops(world, 0, _measure).is_empty(),
		"No boss death animation paints no celebration ops"
	)
	var anim := _animation_for(data["scenarios"][0])
	world.boss_death = anim
	check.call(
		view.boss_celebration_draw_ops(world, 0, _measure).is_empty(),
		"The death phase paints no celebration ops"
	)
	_start_celebration(anim)
	for _tick in range(61):
		anim.update()
	var frame := _frame_at(data, "abaddon", 61)
	var ops: Array = view.boss_celebration_draw_ops(world, int(frame["ticks"]), _measure)
	_expect_ops(check, "view abaddon:61", ops, frame["ops"])
	check.call(
		view.boss_celebration_draw_ops(world).size() == frame["ops"].size(),
		"The view's real font path lists the same ops as the fake metrics"
	)
	view.free()
