extends RefCounted
## Layer 9bd: replays the `BossIntroCinematic.draw()` oracle fixture through
## `boss_intro_layout.gd`. `boss_intro_draw_source_oracle.py` runs the REAL class
## from `_render.py` (and the real `ui_theme.corner_ticks`) under a recording
## pygame shim, so every op (kind, geometry, colour, alpha, order) below comes
## from the source. Each frame is replayed twice: from the recorded state, and
## from the production `BossIntroCinematic` ticked with `update()`. The layout
## needs no font metrics, so the view path must equal the fixture exactly.

const Layout = preload("res://scripts/ui/boss_intro_layout.gd")
const BossIntro = preload("res://scripts/ui/boss_intro_cinematic.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/boss_intro_draw_source.json"
const COMPARED_KEYS := [
	"kind", "rect", "color", "mult", "width", "radius", "a", "b", "text", "size", "style", "pos"
]


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


static func _has_tick(ticks: Array, tick: int) -> bool:
	for value in ticks:
		if int(value) == tick:
			return true
	return false


static func _frame_key(label: String, tick: int) -> String:
	return "%s:%d" % [label, tick]


static func _intro_for(scenario: Dictionary) -> BossIntro:
	var intro := BossIntro.new()
	var screen: Array = scenario["screen"]
	intro.setup(scenario["boss"], int(screen[0]), int(screen[1]))
	return intro


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Boss intro draw fixture parses")
	if not (data is Dictionary):
		return
	check.call(int(data["duration"]) == BossIntro.DURATION, "Oracle duration matches the port")
	check.call(data["frames"].size() == 22, "Boss intro draw oracle pins 22 source frames")
	_check_recorded_frames(check, data)
	_check_production_replay(check, data)
	_check_quirks(check, data)
	_check_view_wiring(check, data)


func _expect_ops(check: Callable, label: String, actual: Array, expected: Array) -> void:
	var bad := _first_mismatch(actual, expected)
	check.call(
		bad < 0,
		(
			"Boss intro %s: %d ops match source (first mismatch #%d: got %s, want %s)"
			% [
				label,
				expected.size(),
				bad,
				str(actual[bad]) if 0 <= bad and bad < actual.size() else "",
				str(expected[bad]) if 0 <= bad and bad < expected.size() else ""
			]
		)
	)


func _frame_ops(data: Dictionary, label: String, tick: int) -> Array:
	for frame_value in data["frames"]:
		var frame: Dictionary = frame_value
		if String(frame["label"]) == label and int(frame["tick"]) == tick:
			return frame["ops"]
	return []


func _check_recorded_frames(check: Callable, data: Dictionary) -> void:
	var scenarios := {}
	for scenario_value in data["scenarios"]:
		scenarios[String(scenario_value["label"])] = scenario_value
	var drawn := 0
	for frame_value in data["frames"]:
		var frame: Dictionary = frame_value
		var intro := _intro_for(scenarios[String(frame["label"])])
		var state: Dictionary = frame["state"]
		intro.timer = int(state["timer"])
		intro.active = bool(state["active"])
		var key := _frame_key(String(frame["label"]), int(frame["tick"]))
		_expect_ops(check, key, Layout.ops(intro), frame["ops"])
		drawn += frame["ops"].size()
	check.call(drawn == 279, "Boss intro oracle pins 279 recorded draw ops")


func _check_production_replay(check: Callable, data: Dictionary) -> void:
	var replayed := 0
	for scenario_value in data["scenarios"]:
		var scenario: Dictionary = scenario_value
		var intro := _intro_for(scenario)
		var last_tick := 0
		for tick_value in scenario["ticks"]:
			last_tick = maxi(last_tick, int(tick_value))
		for tick in range(last_tick + 1):
			if _has_tick(scenario["ticks"], tick):
				var key := _frame_key(String(scenario["label"]), tick)
				var expected := _frame_ops(data, String(scenario["label"]), tick)
				_expect_ops(check, "production " + key, Layout.ops(intro), expected)
				replayed += 1
			intro.update()
	check.call(
		replayed == data["frames"].size(),
		"Boss intro production state replays every recorded frame (%d)" % replayed
	)


func _check_quirks(check: Callable, data: Dictionary) -> void:
	var first := _frame_ops(data, "true_boss", 0)
	check.call(first.size() == 7, "Alpha-0 start frame still lists banner, text and bar ops")
	check.call(
		int(first[0]["color"][3]) == 0 and int(first[first.size() - 1]["color"][3]) == 255,
		"The HP bar is opaque while the banner is still at alpha 0"
	)
	var faded := _frame_ops(data, "true_boss", 99)
	check.call(
		int(faded[faded.size() - 1]["color"][3]) == 255 and int(faded[0]["color"][3]) == 9,
		"The HP bar stays opaque while the banner fades out"
	)
	check.call(_frame_ops(data, "true_boss", 100).is_empty(), "A finished intro draws nothing")
	var intro := BossIntro.new()
	intro.setup({"name": "Test", "title": "Skip"}, 1280, 720)
	intro.update()
	intro.handle_skip(KEY_SPACE)
	check.call(Layout.ops(intro).is_empty(), "A skipped intro draws nothing")


func _check_view_wiring(check: Callable, data: Dictionary) -> void:
	var world := Prototype.new()
	var view := PrototypeView.new()
	check.call(view.boss_intro_draw_ops(world).is_empty(), "No boss intro paints no ops")
	var intro := _intro_for(data["scenarios"][0])
	world.boss_intro = intro
	for _tick in range(40):
		intro.update()
	var expected := _frame_ops(data, "true_boss", 40)
	_expect_ops(check, "view true_boss:40", view.boss_intro_draw_ops(world), expected)
	for _tick in range(60):
		intro.update()
	check.call(view.boss_intro_draw_ops(world).is_empty(), "Finished boss intro paints no ops")
	view.free()
