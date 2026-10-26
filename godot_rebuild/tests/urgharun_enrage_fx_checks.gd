extends RefCounted
## Layer 9bq4: replays the `_NS_urgharun._draw_enrage_fx` oracle fixture through
## `urgharun_enrage_fx_layout.gd`. `urgharun_enrage_fx_source_oracle.py` runs the REAL
## function from `bosses/level40.py` under the recording pygame shim, so every op (kind,
## geometry, colour, alpha, order) below comes from the source. The view must build the
## layer only for urgharun's R, from the live skill timer and pulse; `painter_scene_checks.gd`
## proves the live scene paints it over the body.

const Layout = preload("res://scripts/ui/urgharun_enrage_fx_layout.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/urgharun_enrage_fx_source.json"
const COMPARED_KEYS := {
	"circle": ["center", "radius", "width", "color", "mult"],
	"rect": ["rect", "width", "radius", "color", "mult"],
}


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


## Index of the first differing op, or -1 when both lists match exactly.
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
	check.call(data is Dictionary, "Urgharun enrage FX fixture parses")
	if not (data is Dictionary):
		return
	var frames: Array = data["frames"]
	var ops_total := 0
	for frame in frames:
		ops_total += frame["ops"].size()
	check.call(
		frames.size() == 7 and ops_total == 476,
		"Urgharun enrage oracle pins 7 source frames and 476 draw ops"
	)
	_check_palette(check, data)
	_check_frames(check, frames)
	_check_timing(check, frames)
	_check_gate(check)
	_check_view_wiring(check, frames)


func _check_palette(check: Callable, data: Dictionary) -> void:
	var palette: Dictionary = data["palette"]
	check.call(
		(
			_value_equal(Layout.FURY_DARK, palette["fury_dark"])
			and _value_equal(Layout.FURY_MID, palette["fury_mid"])
			and _value_equal(Layout.FURY_LIGHT, palette["fury_light"])
			and _value_equal(Layout.FURY_HOT, palette["fury_hot"])
			and _value_equal(Layout.FURY_SHINE, palette["fury_shine"])
		),
		"The enrage layout uses urgharun's source fury palette"
	)
	check.call(
		String(data["boss_type"]) == Layout.BOSS_TYPE and String(data["skill"]) == Layout.SKILL,
		"The layer belongs to urgharun's R cast"
	)
	check.call(
		int(data["duration"]) == Layout.DURATION,
		"The layer normalises the cast by the source's own 80 ticks"
	)


func _check_frames(check: Callable, frames: Array) -> void:
	for frame in frames:
		var anchor: Array = frame["anchor"]
		var actual := Layout.ops(
			int(anchor[0]), int(anchor[1]), int(frame["timer"]), float(frame["pulse"])
		)
		var mismatch := _first_mismatch(actual, frame["ops"])
		check.call(
			mismatch == -1,
			(
				"Enrage frame %s matches the source ops (first mismatch %d)"
				% [frame["label"], mismatch]
			)
		)
	var cast: Dictionary = _frame(frames, "cast")
	var cast_ops: Array = cast.get("ops", [])
	# Ten flames = 50 ops, the six-step aura ring, then six embers = 12 ops.
	check.call(
		(
			cast_ops.size() == 68
			and cast_ops[0]["kind"] == "circle"
			and int(cast_ops[0]["radius"]) == 3
			and cast_ops[3]["kind"] == "rect"
			and int(cast_ops[3]["rect"][2]) == 1
			and int(cast_ops[3]["rect"][3]) == 1
			and cast_ops[50]["kind"] == "circle"
			and int(cast_ops[50]["width"]) == 1
			and cast_ops[56]["kind"] == "rect"
			and int(cast_ops[56]["rect"][2]) == 2
			and int(cast_ops[56]["rect"][3]) == 2
		),
		"The layer keeps the source order: ten flames, the aura ring, then six embers"
	)
	var aura_radii: Array = []
	for index in range(50, 56):
		aura_radii.append(int(cast_ops[index]["radius"]))
	check.call(
		aura_radii == [38, 37, 36, 35, 34, 33],
		"The aura ring walks range(38, 32, -1) from the outside in"
	)
	var flame_alphas: Array = []
	for index in range(10):
		flame_alphas.append(int(cast_ops[index * 5]["color"][3]))
	check.call(
		(
			flame_alphas[0] == 220
			and flame_alphas[1] == 187
			and flame_alphas[6] == 22
			and flame_alphas[7] == 209
		),
		"Flame alpha follows 220 * (1 - flame_t) and wraps at 1.0 like the source modulo"
	)


## The source computes `progress` from the timer and never reads it: the picture is a
## function of `pulse` only. Both the fixture and the layout must keep that quirk.
func _check_timing(check: Callable, frames: Array) -> void:
	var mid: Dictionary = _frame(frames, "mid")
	var ignored: Dictionary = _frame(frames, "timer_ignored")
	check.call(
		(
			not mid.is_empty()
			and not ignored.is_empty()
			and int(mid["timer"]) != int(ignored["timer"])
			and mid["ops"] == ignored["ops"]
		),
		"The elapsed cast time does not change a single op (source drops progress)"
	)
	var first := Layout.ops(640, 360, Layout.DURATION, float(mid.get("pulse", 0.0)))
	var last := Layout.ops(640, 360, 1, float(mid.get("pulse", 0.0)))
	check.call(
		_first_mismatch(first, last) == -1,
		"The layer paints the same ops on the first and the last cast tick"
	)
	var early := _first_mismatch(Layout.ops(640, 360, 40, 0.0), Layout.ops(640, 360, 40, 2.5))
	check.call(early != -1, "The pulse alone advances the flames, the aura and the embers")


func _check_gate(check: Callable) -> void:
	check.call(Layout.active("urgharun", "r"), "Urgharun's R opens the enrage layer")
	check.call(
		(
			not Layout.active("urgharun", "q")
			and not Layout.active("urgharun", "w")
			and not Layout.active("urgharun", "e")
			and not Layout.active("urgharun", "")
			and not Layout.active("yhoranth", "r")
		),
		"Other urgharun skills and other bosses paint no enrage layer"
	)


func _check_view_wiring(check: Callable, frames: Array) -> void:
	var expected: Dictionary = _frame(frames, "mid")
	var anchor: Array = expected.get("anchor", [640, 360])
	var view := PrototypeView.new()
	var boss := BossState.new()
	boss.boss_type = "urgharun"
	boss.position = Vector2(float(anchor[0]), float(anchor[1]))
	boss.active_skill_timer = int(expected.get("timer", 40))
	boss.pulse = float(expected.get("pulse", 0.0))
	boss.active_skill = "q"
	check.call(view.urgharun_enrage_draw_ops(boss).is_empty(), "Urgharun's Q paints no enrage FX")
	boss.active_skill = "r"
	check.call(
		_first_mismatch(view.urgharun_enrage_draw_ops(boss), expected.get("ops", [])) == -1,
		"The view builds the enrage layer from the live anchor, skill timer and pulse"
	)
	boss.boss_type = "yhoranth"
	check.call(
		view.urgharun_enrage_draw_ops(boss).is_empty(),
		"Another boss's R paints no urgharun enrage FX"
	)
	view.free()
