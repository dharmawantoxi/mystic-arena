extends RefCounted
## Layer 9bq7: replays the aura fixture of `boss_aura_fx_source_oracle.py` through
## `boss_aura_fx_layout.gd`. The oracle runs the REAL `Boss.draw` aura block, `_draw_enrage_aura`,
## `_draw_true_boss_aura` and their cache helpers from `bosses/base_boss.py` under the recording
## pygame shim, so every op below (kind, geometry, colour, alpha, order) comes from the source.
## `painter_scene_checks.gd` proves the live scene paints the three layers.

const Layout = preload("res://scripts/ui/boss_aura_fx_layout.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/boss_aura_fx_source.json"
const COMPARED_KEYS := {
	"circle": ["center", "radius", "width", "color", "mult"],
}
const ANCHOR := 640
const ANCHOR_Y := 360


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


## Index of the first differing op, or the shared length when one list is longer.
static func _first_mismatch(actual: Array, expected: Array) -> int:
	for index in range(mini(actual.size(), expected.size())):
		if not _op_equal(actual[index], expected[index]):
			return index
	return -1 if actual.size() == expected.size() else mini(actual.size(), expected.size())


## Frame label + first differing op pair, so a CI failure names the exact source op.
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


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Boss aura fixture parses")
	if not (data is Dictionary):
		return
	var total := 0
	var grouped := ["ability_frames", "enrage_frames", "true_boss_frames"]
	for key in grouped:
		for frame in data[key]:
			total += frame["ops"].size()
	check.call(
		(
			total == 69
			and int(data["ability_frames"].size()) == 4
			and int(data["enrage_frames"].size()) == 5
			and int(data["true_boss_frames"].size()) == 3
		),
		"Boss aura oracle pins 12 source frames and 69 draw ops (got %d)" % total
	)
	_check_ability(check, data)
	_check_enrage(check, data)
	_check_true_boss(check, data)
	_check_view_wiring(check, data)


func _check_ability(check: Callable, data: Dictionary) -> void:
	for frame in data["ability_frames"]:
		var actual := Layout.ability_aura_ops(
			ANCHOR,
			ANCHOR_Y,
			float(frame["ability_range"]),
			int(frame["anim_time"]),
			frame["entrance_color"]
		)
		check.call(
			_first_mismatch(actual, frame["ops"]) == -1,
			_report("Ability aura %s" % frame["label"], actual, frame["ops"])
		)
	# `alpha = int((aura_r - ar) * 8 * pulse)`: the outermost ring always lands on alpha 0 and the
	# source skips it, so a seven-ring band paints six ops, all of them filled.
	var full: Dictionary = _frame(data["ability_frames"], "ability_full")
	check.call(
		(
			int(full["ops"].size()) == 6
			and int(full["ops"][0]["radius"]) == 241
			and int(full["ops"][0]["color"][3]) == 16
			and int(full["ops"][0]["width"]) == 0
		),
		"The ability aura skips its transparent outer ring and fades inwards"
	)


func _check_enrage(check: Callable, data: Dictionary) -> void:
	for frame in data["enrage_frames"]:
		var actual := Layout.enrage_aura_ops(
			ANCHOR,
			ANCHOR_Y,
			int(frame["radius"]),
			float(frame["enrage_pulse"]),
			String(frame["boss_class"]) == "true"
		)
		check.call(
			_first_mismatch(actual, frame["ops"]) == -1,
			_report("Enrage aura %s" % frame["label"], actual, frame["ops"])
		)
	var mini: Dictionary = _frame(data["enrage_frames"], "enrage_mini")
	var true_boss: Dictionary = _frame(data["enrage_frames"], "enrage_true")
	check.call(
		(
			int(mini["ops"].size()) == 5
			and int(mini["ops"][0]["width"]) == 2
			and _value_equal(mini["ops"][0]["color"], [255, 140, 30, 25])
			and _value_equal(true_boss["ops"][0]["color"], [255, 50, 40, 29])
		),
		"The enrage aura strokes width-2 rings, amber for a mini boss and red for a true one"
	)
	# `range(aura_r, max(5, aura_r - 18), -3)` stops at 5 when the boss is tiny.
	var tiny: Dictionary = _frame(data["enrage_frames"], "enrage_tiny_radius")
	check.call(
		int(tiny["ops"].size()) == 4 and int(tiny["ops"][-1]["radius"]) == 6,
		"The enrage band clamps at radius 5 for a tiny boss"
	)


func _check_true_boss(check: Callable, data: Dictionary) -> void:
	for frame in data["true_boss_frames"]:
		var actual := Layout.true_boss_aura_ops(
			ANCHOR, ANCHOR_Y, int(frame["radius"]), float(frame["pulse"]), frame["color"]
		)
		check.call(
			_first_mismatch(actual, frame["ops"]) == -1,
			_report("True boss aura %s" % frame["label"], actual, frame["ops"])
		)
	var peak: Dictionary = _frame(data["true_boss_frames"], "true_aura_peak")
	check.call(
		(
			int(peak["ops"].size()) == 7
			and int(peak["ops"][0]["width"]) == 0
			and int(peak["ops"][0]["radius"]) == 49
			and _value_equal(peak["ops"][0]["color"], [255, 140, 60, 9])
		),
		"The true-boss aura fills its rings in the boss body colour"
	)


func _check_view_wiring(check: Callable, data: Dictionary) -> void:
	var view := PrototypeView.new()
	var boss := BossState.new()
	boss.position = Vector2(ANCHOR, ANCHOR_Y)
	var ability: Dictionary = _frame(data["ability_frames"], "ability_full")
	boss.ability_active = true
	boss.ability_range = float(ability["ability_range"])
	boss.anim_time = int(ability["anim_time"])
	boss.entrance_color = Color8(
		int(ability["entrance_color"][0]),
		int(ability["entrance_color"][1]),
		int(ability["entrance_color"][2])
	)
	check.call(
		_first_mismatch(view.boss_ability_aura_draw_ops(boss), ability["ops"]) == -1,
		_report("Ability aura wiring", view.boss_ability_aura_draw_ops(boss), ability["ops"])
	)
	boss.ability_active = false
	check.call(
		view.boss_ability_aura_draw_ops(boss).is_empty(),
		"No ability aura without an active ability"
	)
	var enrage: Dictionary = _frame(data["enrage_frames"], "enrage_true_peak")
	boss.boss_class = String(enrage["boss_class"])
	boss.is_enraged = true
	boss.radius = float(enrage["radius"])
	boss.enrage_pulse = float(enrage["enrage_pulse"])
	check.call(
		_first_mismatch(view.boss_enrage_aura_draw_ops(boss), enrage["ops"]) == -1,
		_report("Enrage aura wiring", view.boss_enrage_aura_draw_ops(boss), enrage["ops"])
	)
	boss.is_enraged = false
	check.call(
		view.boss_enrage_aura_draw_ops(boss).is_empty(),
		"No enrage aura before the enrage transition"
	)
	var true_aura: Dictionary = _frame(data["true_boss_frames"], "true_aura_late")
	boss.radius = float(true_aura["radius"])
	boss.pulse = float(true_aura["pulse"])
	boss.color = Color8(
		int(true_aura["color"][0]), int(true_aura["color"][1]), int(true_aura["color"][2])
	)
	check.call(
		_first_mismatch(view.boss_true_aura_draw_ops(boss), true_aura["ops"]) == -1,
		_report("True boss aura wiring", view.boss_true_aura_draw_ops(boss), true_aura["ops"])
	)
	boss.boss_class = "mini"
	check.call(
		view.boss_true_aura_draw_ops(boss).is_empty(), "Only a true boss paints the extra aura"
	)
	boss.boss_class = "true"
	check.call(
		not view.boss_true_aura_draw_ops(boss).is_empty(), "A true boss keeps its extra aura"
	)
	view.free()
