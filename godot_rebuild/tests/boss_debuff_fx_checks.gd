extends RefCounted
## Layer 9bq9: replays the fixture of `boss_debuff_fx_source_oracle.py` through
## `boss_debuff_fx_layout.gd`. The oracle runs the REAL
## `_core.py::TowerDebuffMixin._draw_tower_debuff_fx` under the recording pygame shim, so every op
## (slow ellipse, flame tongues, pip blocks) comes from the source.
## `painter_scene_checks.gd` proves the live scene paints the indicator on a debuffed boss.

const Layout = preload("res://scripts/ui/boss_debuff_fx_layout.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/boss_debuff_fx_source.json"
const COMPARED_KEYS := {
	"circle": ["center", "radius", "width", "color", "mult"],
	"ellipse": ["rect", "width", "color", "mult"],
	"rect": ["rect", "width", "radius", "color", "mult"],
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
		36,
		int(frame["slow"]),
		int(frame["atk_slow"]),
		int(frame["skill_down"]),
		int(frame["anti_heal"]),
		int(frame["burn"]),
		float(frame["anim_time"]),
		bool(frame["include_rings"])
	)


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Boss debuff fixture parses")
	if not (data is Dictionary):
		return
	var total := 0
	for frame in data["frames"]:
		total += frame["ops"].size()
	check.call(
		int(data["frames"].size()) == 8 and total == 69 and int(data["radius"]) == 36,
		"Boss debuff oracle pins 8 frames and 69 draw ops (got %d)" % total
	)
	_check_frames(check, data)
	_check_shape(check, data)
	_check_view_wiring(check, data)


func _check_frames(check: Callable, data: Dictionary) -> void:
	for frame in data["frames"]:
		var actual: Array = []
		if bool(frame["alive"]):
			actual = _from_frame(frame)
		check.call(
			_first_mismatch(actual, frame["ops"]) == -1,
			_report("Debuff %s" % frame["label"], actual, frame["ops"])
		)


func _check_shape(check: Callable, data: Dictionary) -> void:
	var counts: Array = []
	for frame in data["frames"]:
		counts.append(frame["ops"].size())
	check.call(
		counts == [0, 3, 8, 8, 17, 17, 16, 0],
		"Only the active debuffs paint: slow ring, three flames and one pip pair each"
	)
	var slow: Dictionary = _frame(data["frames"], "slow_only")
	check.call(
		(
			str(slow["ops"][0]["kind"]) == "ellipse"
			and int(slow["ops"][0]["width"]) == 1
			and _value_equal(slow["ops"][0]["rect"], [602, 389, 76, 10])
			and int(slow["ops"][1]["rect"][2]) == 5
			and int(slow["ops"][2]["rect"][2]) == 4
		),
		"The slow ring is a 1 px ellipse at the feet with a 5x5 backing under a 4x4 pip"
	)
	var burn: Dictionary = _frame(data["frames"], "burn_only_anim0")
	check.call(
		(
			int(burn["ops"][0]["radius"]) == 3
			and int(burn["ops"][1]["radius"]) == 2
			and int(burn["ops"][2]["radius"]) == 2
			and int(burn["ops"][4]["radius"]) == 4
			and int(burn["ops"][5]["radius"]) == 3
		),
		"The flames flicker with `int(1.5 + 1.5 * sin(anim * 0.6))`"
	)
	var no_rings: Dictionary = _frame(data["frames"], "all_without_rings")
	check.call(
		int(no_rings["ops"].size()) == 16, "`include_rings=False` drops only the slow ellipse"
	)
	var dead: Dictionary = _frame(data["frames"], "dead_ignores_everything")
	check.call(
		int(dead["ops"].size()) == 0 and not bool(dead["alive"]),
		"A dead unit paints no indicator at all"
	)


func _check_view_wiring(check: Callable, data: Dictionary) -> void:
	var view := PrototypeView.new()
	var boss := BossState.new()
	boss.alive = true
	boss.position = Vector2(ANCHOR, ANCHOR_Y)
	boss.radius = 36.0
	check.call(
		view.boss_debuff_draw_ops(boss).is_empty(), "A clean boss paints no debuff indicator"
	)
	var all: Dictionary = _frame(data["frames"], "all_debuffs_int_anim")
	boss.slow_timer = int(all["slow"])
	boss.atk_slow_timer = int(all["atk_slow"])
	boss.skill_down_timer = int(all["skill_down"])
	boss.anti_heal_timer = int(all["anti_heal"])
	boss.burn_timer = int(all["burn"])
	boss.anim_time = int(all["anim_time"])
	check.call(
		_first_mismatch(view.boss_debuff_draw_ops(boss), all["ops"]) == -1,
		_report("Debuff wiring", view.boss_debuff_draw_ops(boss), all["ops"])
	)
	boss.slow_timer = 0
	boss.atk_slow_timer = 0
	boss.skill_down_timer = 0
	boss.anti_heal_timer = 0
	check.call(
		view.boss_debuff_draw_ops(boss).size() == 8,
		"Burn alone keeps the three flames and its own pip"
	)
	boss.burn_timer = 0
	check.call(
		view.boss_debuff_draw_ops(boss).is_empty(), "Clearing every timer clears the indicator"
	)
	boss.alive = false
	boss.burn_timer = 20
	check.call(view.boss_debuff_draw_ops(boss).is_empty(), "A dead boss paints no indicator")
	view.free()
