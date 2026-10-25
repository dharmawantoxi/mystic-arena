extends RefCounted
## Layer 9bq5: replays the `_NS_urgharun._draw_enrage_ground` oracle fixture through
## `urgharun_enrage_ground_layout.gd`. `urgharun_enrage_ground_source_oracle.py` runs the REAL
## function from `bosses/level40.py` under the recording pygame shim, so every op (kind,
## geometry, colour, alpha, order) below comes from the source. The view must build the layer
## only for urgharun's R, from the live skill timer and pulse, and paint it under the body;
## `painter_scene_checks.gd` proves the live scene reaches it.

const Layout = preload("res://scripts/ui/urgharun_enrage_ground_layout.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/urgharun_enrage_ground_source.json"
const COMPARED_KEYS := {
	"ellipse": ["rect", "width", "color", "mult"],
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
	check.call(data is Dictionary, "Urgharun enrage ground fixture parses")
	if not (data is Dictionary):
		return
	var frames: Array = data["frames"]
	var ops_total := 0
	for frame in frames:
		ops_total += frame["ops"].size()
	check.call(
		frames.size() == 8 and ops_total == 208,
		"Urgharun enrage ground oracle pins 8 source frames and 208 draw ops"
	)
	_check_palette(check, data)
	_check_frames(check, frames)
	_check_rings(check, frames)
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
		"The ground layout uses urgharun's source fury palette"
	)
	check.call(
		String(data["boss_type"]) == Layout.BOSS_TYPE and String(data["skill"]) == Layout.SKILL,
		"The ground layer belongs to urgharun's R cast"
	)
	check.call(
		int(data["duration"]) == Layout.DURATION,
		"The ground layer normalises the cast by the source's own 80 ticks"
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
				"Ground frame %s matches the source ops (first mismatch %d)"
				% [frame["label"], mismatch]
			)
		)
	var cast: Dictionary = _frame(frames, "cast")
	var cast_ops: Array = cast.get("ops", [])
	# Six ring outlines (two rings x three nested ellipses), then ten rune pairs.
	check.call(
		(
			cast_ops.size() == 26
			and cast_ops[0]["kind"] == "ellipse"
			and int(cast_ops[0]["width"]) == 3
			and cast_ops[1]["kind"] == "ellipse"
			and int(cast_ops[1]["width"]) == 2
			and cast_ops[2]["kind"] == "ellipse"
			and int(cast_ops[2]["width"]) == 1
			and cast_ops[6]["kind"] == "rect"
			and int(cast_ops[6]["rect"][2]) == 3
			and cast_ops[7]["kind"] == "rect"
			and int(cast_ops[7]["rect"][2]) == 1
		),
		"The layer keeps the source order: six ring outlines, then ten rune squares with cores"
	)
	var first_rect: Array = cast_ops[0]["rect"]
	var inset_rect: Array = cast_ops[1]["rect"]
	check.call(
		(
			int(inset_rect[0]) == int(first_rect[0]) + 3
			and int(inset_rect[1]) == int(first_rect[1]) + 2
			and int(inset_rect[2]) == int(first_rect[2]) - 6
			and int(inset_rect[3]) == int(first_rect[3]) - 4
		),
		"The inner ring outlines are inset by (3, 2) and (6, 4) like the source"
	)
	check.call(
		int(cast_ops[0]["color"][3]) == 154 and int(cast_ops[3]["color"][3]) == 114,
		"Ring alpha follows 220 * pulse - i * 40"
	)


## The rune cores keep their raw palette tuple (alpha 255) while the 3x3 square fades.
func _check_rings(check: Callable, frames: Array) -> void:
	var mid: Dictionary = _frame(frames, "mid")
	var mid_ops: Array = mid.get("ops", [])
	var cores_opaque := true
	var squares_faded := true
	for index in range(6, mid_ops.size(), 2):
		if int(mid_ops[index + 1]["color"][3]) != 255:
			cores_opaque = false
		if int(mid_ops[index]["color"][3]) != int(mid_ops[6]["color"][3]):
			squares_faded = false
	check.call(
		cores_opaque and squares_faded and int(mid_ops[6]["color"][3]) == 238,
		"Rune squares fade with 240 * pulse while their 1 px cores stay opaque"
	)
	var negative: Dictionary = _frame(frames, "negative_sin")
	var radii: Array = []
	for index in range(0, 6, 3):
		var rect: Array = negative.get("ops", [{}])[index]["rect"]
		radii.append(int(rect[2]) / 2)
	check.call(
		radii.size() == 2 and int(radii[0]) < 35 and int(radii[1]) < 43,
		"A negative sin(phase * 2) pulls both ring radii below their 35/43 base"
	)
	# At y = 680 the outer ring runs past the 720 px source surface, so pygame clips it; the
	# fixture records the op as issued and the Godot viewport clips it the same way.
	var edge: Dictionary = _frame(frames, "edge_anchor")
	var edge_rect: Array = edge.get("ops", [{}])[0]["rect"]
	check.call(
		(
			int(edge.get("anchor", [0, 0])[1]) == 680
			and int(edge_rect[1]) + int(edge_rect[3]) > 720
			and int(edge.get("ops", [{}])[0]["rect"][2]) == 66
		),
		"The bottom-edge frame keeps the source rect that the surface clips"
	)


## The source computes `progress` from the timer and never reads it: both enrage layers are
## functions of the pulse only. The fixture and the layout must keep that quirk.
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
		"The elapsed cast time does not change a single ground op (source drops progress)"
	)
	var anchor: Array = mid.get("anchor", [640, 360])
	var first := Layout.ops(
		int(anchor[0]), int(anchor[1]), Layout.DURATION, float(mid.get("pulse", 0.0))
	)
	var last := Layout.ops(int(anchor[0]), int(anchor[1]), 1, float(mid.get("pulse", 0.0)))
	check.call(
		_first_mismatch(first, last) == -1,
		"The ground layer paints the same ops on the first and the last cast tick"
	)


func _check_gate(check: Callable) -> void:
	check.call(Layout.active("urgharun", "r"), "Urgharun's R opens the ground layer")
	check.call(
		(
			not Layout.active("urgharun", "q")
			and not Layout.active("urgharun", "w")
			and not Layout.active("urgharun", "e")
			and not Layout.active("urgharun", "")
			and not Layout.active("yhoranth", "r")
		),
		"Other urgharun skills and other bosses paint no ground layer"
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
	boss.active_skill = "e"
	check.call(
		view.urgharun_enrage_ground_draw_ops(boss).is_empty(),
		"Urgharun's E paints no enrage ground FX"
	)
	boss.active_skill = "r"
	check.call(
		_first_mismatch(view.urgharun_enrage_ground_draw_ops(boss), expected.get("ops", [])) == -1,
		"The view builds the ground layer from the live anchor, skill timer and pulse"
	)
	boss.boss_type = "yhoranth"
	check.call(
		view.urgharun_enrage_ground_draw_ops(boss).is_empty(),
		"Another boss's R paints no urgharun ground FX"
	)
	view.free()
