extends RefCounted
## Layer 9bq6: replays the LAYER 1 and Q/W/E fixture of
## `urgharun_skill_fx_source_oracle.py` through `urgharun_skill_fx_layout.gd`. The oracle runs
## the REAL `_NS_urgharun` members from `bosses/level40.py` under the recording pygame shim, so
## every op below (kind, geometry, colour, alpha, order) comes from the source. The view must
## build each layer from live state only; `painter_scene_checks.gd` proves the live scene paints
## them.

const Layout = preload("res://scripts/ui/urgharun_skill_fx_layout.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/urgharun_skill_fx_source.json"
const COMPARED_KEYS := {
	"circle": ["center", "radius", "width", "color", "mult"],
	"ellipse": ["rect", "width", "color", "mult"],
	"rect": ["rect", "width", "radius", "color", "mult"],
	"line": ["a", "b", "width", "color", "mult"],
	"polygon": ["points", "width", "color", "mult"],
}
const ANCHOR := 640
const PULSE_ANCHOR := 0.0


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
	var mine := actual[index] if index < actual.size() else {}
	var theirs := expected[index] if index < expected.size() else {}
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
	check.call(data is Dictionary, "Urgharun skill FX fixture parses")
	if not (data is Dictionary):
		return
	var total := 0
	var grouped := [
		"aura_frames",
		"ring_frames",
		"earthshock_ground_frames",
		"earthshock_fx_frames",
		"overpower_frames",
		"furyswipes_frames"
	]
	for key in grouped:
		for frame in data[key]:
			total += frame["ops"].size()
	check.call(
		(
			total == 1236
			and int(data["aura_frames"].size()) == 5
			and int(data["earthshock_fx_frames"].size()) == 4
			and int(data["furyswipes_frames"].size()) == 5
		),
		"Urgharun skill FX oracle pins 27 source frames and 1236 draw ops (got %d)" % total
	)
	_check_palette(check, data)
	_check_aura(check, data)
	_check_ring(check, data)
	_check_earthshock(check, data)
	_check_overpower(check, data)
	_check_furyswipes(check, data)
	_check_gate(check)
	_check_view_wiring(check, data)


func _check_palette(check: Callable, data: Dictionary) -> void:
	var palette: Dictionary = data["palette"]
	check.call(
		(
			_value_equal(Layout.FURY_DARKEST, palette["fury_darkest"])
			and _value_equal(Layout.FURY_DARK, palette["fury_dark"])
			and _value_equal(Layout.FURY_MID, palette["fury_mid"])
			and _value_equal(Layout.FURY_LIGHT, palette["fury_light"])
			and _value_equal(Layout.FURY_HOT, palette["fury_hot"])
			and _value_equal(Layout.FURY_SHINE, palette["fury_shine"])
			and _value_equal(Layout.FUR_DARKEST, palette["fur_darkest"])
			and _value_equal(Layout.FUR_MID, palette["fur_mid"])
			and _value_equal(Layout.SHADOW_DEEP, palette["shadow_deep"])
		),
		"The skill FX layout uses urgharun's source palette"
	)
	var durations: Dictionary = data["durations"]
	check.call(
		(
			int(durations["q"]) == Layout.Q_DURATION
			and int(durations["w"]) == Layout.W_DURATION
			and int(durations["e"]) == Layout.E_DURATION
		),
		"The skill layers normalise each cast by the source's own window (55/50/40)"
	)


func _check_aura(check: Callable, data: Dictionary) -> void:
	for frame in data["aura_frames"]:
		var actual := Layout.aura_ops(ANCHOR, 360, float(frame["phase"]), bool(frame["enraged"]))
		check.call(
			_first_mismatch(actual, frame["ops"]) == -1,
			_report("Aura frame %s" % frame["label"], actual, frame["ops"])
		)
	var calm: Dictionary = _frame(data["aura_frames"], "aura_calm")
	var enraged: Dictionary = _frame(data["aura_frames"], "aura_enraged")
	check.call(
		(
			int(calm.get("ops", []).size()) == 54
			and int(enraged.get("ops", []).size()) == 62
			and int(enraged.get("ops", [{}])[0]["center"][0]) == ANCHOR
		),
		"The furious aura adds four embers (16 vs 12) and stays centred on the anchor"
	)


func _check_ring(check: Callable, data: Dictionary) -> void:
	for frame in data["ring_frames"]:
		var skill: Variant = frame["skill"]
		var actual := Layout.ground_ring_ops(
			ANCHOR, 360 + Layout.RING_Y_OFFSET, float(frame["phase"]), skill != null
		)
		check.call(
			_first_mismatch(actual, frame["ops"]) == -1,
			_report("Ground ring frame %s" % frame["label"], actual, frame["ops"])
		)
	var idle: Dictionary = _frame(data["ring_frames"], "ring_idle")
	var casting: Dictionary = _frame(data["ring_frames"], "ring_q")
	check.call(
		(
			int(idle.get("ops", []).size()) == 13
			and int(casting.get("ops", []).size()) == 14
			and casting.get("ops", [{}])[-1]["kind"] == "ellipse"
		),
		"An active cast adds the source's extra fury_hot ground ellipse"
	)


func _check_earthshock(check: Callable, data: Dictionary) -> void:
	for frame in data["earthshock_ground_frames"]:
		var actual := Layout.earthshock_ground_ops(
			ANCHOR, 360, int(frame["timer"]), float(frame["phase"])
		)
		check.call(
			_first_mismatch(actual, frame["ops"]) == -1,
			_report("Q ground frame %s" % frame["label"], actual, frame["ops"])
		)
	for frame in data["earthshock_fx_frames"]:
		var actual := Layout.earthshock_fx_ops(
			ANCHOR, 360, int(frame["timer"]), float(frame["phase"])
		)
		check.call(
			_first_mismatch(actual, frame["ops"]) == -1,
			_report("Q foreground frame %s" % frame["label"], actual, frame["ops"])
		)
	var first: Dictionary = _frame(data["earthshock_ground_frames"], "q_ground_first")
	var mid: Dictionary = _frame(data["earthshock_ground_frames"], "q_ground_mid")
	var debris: Dictionary = _frame(data["earthshock_fx_frames"], "q_fg_debris")
	check.call(
		int(first.get("ops", [1]).size()) == 0 and int(mid.get("ops", []).size()) == 9,
		"The Q ground rings only start once their radius passes 5 px"
	)
	var polygons := 0
	for op in debris.get("ops", []):
		if str(op.get("kind", "")) == "polygon":
			polygons += 1
	check.call(
		int(debris.get("ops", []).size()) == 168 and polygons == 24,
		"The Q foreground debris draws eight rocks as three source polygons each"
	)


func _check_overpower(check: Callable, data: Dictionary) -> void:
	for frame in data["overpower_frames"]:
		var target: Variant = frame["target"]
		var actual := Layout.overpower_ops(
			ANCHOR,
			360,
			int(frame["direction"]),
			int(frame["timer"]),
			float(frame["phase"]),
			[] if target == null else [int(target[0]), int(target[1])]
		)
		check.call(
			_first_mismatch(actual, frame["ops"]) == -1,
			_report("W frame %s" % frame["label"], actual, frame["ops"])
		)
	var with_target: Dictionary = _frame(data["overpower_frames"], "w_first")
	var without: Dictionary = _frame(data["overpower_frames"], "w_no_target")
	check.call(
		int(with_target.get("ops", []).size()) == 128 and int(without.get("ops", []).size()) == 128,
		"The W stun stars appear past half of the cast window only when a target exists"
	)


func _check_furyswipes(check: Callable, data: Dictionary) -> void:
	for frame in data["furyswipes_frames"]:
		var target: Variant = frame["target"]
		var actual := Layout.furyswipes_ops(
			ANCHOR,
			360,
			int(frame["direction"]),
			int(frame["timer"]),
			float(frame["phase"]),
			[] if target == null else [int(target[0]), int(target[1])]
		)
		check.call(
			_first_mismatch(actual, frame["ops"]) == -1,
			_report("E frame %s" % frame["label"], actual, frame["ops"])
		)
	var first: Dictionary = _frame(data["furyswipes_frames"], "e_first")
	var last: Dictionary = _frame(data["furyswipes_frames"], "e_last")
	var mid: Dictionary = _frame(data["furyswipes_frames"], "e_mid")
	check.call(
		(
			int(first.get("ops", [1]).size()) == 0
			and int(last.get("ops", [1]).size()) == 0
			and int(mid.get("ops", []).size()) == 26
		),
		"The E slashes skip the first and the fading tail of the cast window"
	)


func _check_gate(check: Callable) -> void:
	check.call(Layout.active("urgharun"), "Urgharun owns the remaining FX layers")
	check.call(
		not Layout.active("yhoranth") and not Layout.active("zulkhaven"),
		"Other bosses paint no urgharun FX"
	)


func _check_view_wiring(check: Callable, data: Dictionary) -> void:
	var view := PrototypeView.new()
	var boss := BossState.new()
	boss.boss_type = "urgharun"
	boss.position = Vector2(ANCHOR, 360)
	boss.pulse = PULSE_ANCHOR
	var calm: Dictionary = _frame(data["aura_frames"], "aura_calm")
	var idle: Dictionary = _frame(data["ring_frames"], "ring_idle")
	var expected_layer_one: Array = calm.get("ops", []).duplicate()
	expected_layer_one.append_array(idle.get("ops", []))
	check.call(
		_first_mismatch(view.urgharun_aura_draw_ops(boss), expected_layer_one) == -1,
		_report("Layer 1 wiring", view.urgharun_aura_draw_ops(boss), expected_layer_one)
	)
	boss.active_skill = "r"
	var enraged: Dictionary = _frame(data["aura_frames"], "aura_enraged")
	var casting: Dictionary = _frame(data["ring_frames"], "ring_q")
	var expected_enraged: Array = enraged.get("ops", []).duplicate()
	expected_enraged.append_array(casting.get("ops", []))
	check.call(
		_first_mismatch(view.urgharun_aura_draw_ops(boss), expected_enraged) == -1,
		_report("Enraged layer 1 wiring", view.urgharun_aura_draw_ops(boss), expected_enraged)
	)
	var ground_mid: Dictionary = _frame(data["earthshock_ground_frames"], "q_ground_mid")
	boss.active_skill = "q"
	boss.active_skill_timer = int(ground_mid["timer"])
	boss.pulse = float(ground_mid["phase"])
	check.call(
		_first_mismatch(view.urgharun_skill_ground_draw_ops(boss), ground_mid["ops"]) == -1,
		_report("Q ground wiring", view.urgharun_skill_ground_draw_ops(boss), ground_mid["ops"])
	)
	var q_fg: Dictionary = _frame(data["earthshock_fx_frames"], "q_fg_debris")
	check.call(
		_first_mismatch(view.urgharun_skill_fg_draw_ops(boss), q_fg["ops"]) == -1,
		_report("Q foreground wiring", view.urgharun_skill_fg_draw_ops(boss), q_fg["ops"])
	)
	var w_frame: Dictionary = _frame(data["overpower_frames"], "w_no_target")
	boss.active_skill = "w"
	boss.active_skill_timer = int(w_frame["timer"])
	boss.pulse = float(w_frame["phase"])
	boss.direction = int(w_frame["direction"])
	check.call(
		_first_mismatch(view.urgharun_skill_fg_draw_ops(boss), w_frame["ops"]) == -1,
		_report("W foreground wiring", view.urgharun_skill_fg_draw_ops(boss), w_frame["ops"])
	)
	var e_frame: Dictionary = _frame(data["furyswipes_frames"], "e_no_target")
	boss.active_skill = "e"
	boss.active_skill_timer = int(e_frame["timer"])
	boss.pulse = float(e_frame["phase"])
	boss.direction = int(e_frame["direction"])
	check.call(
		_first_mismatch(view.urgharun_skill_fg_draw_ops(boss), e_frame["ops"]) == -1,
		_report("E foreground wiring", view.urgharun_skill_fg_draw_ops(boss), e_frame["ops"])
	)
	boss.active_skill = "q"
	check.call(
		view.urgharun_target_point().is_empty(),
		"A view without a session reports no target for the W/E source branch"
	)
	view.free()
