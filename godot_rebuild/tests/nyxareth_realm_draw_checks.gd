extends RefCounted
## Layer 9bq3: replays the `_NS_nyxareth._draw_astro_realm_bg` oracle fixture through
## `nyxareth_realm_layout.gd`. `nyxareth_realm_draw_source_oracle.py` runs the REAL function
## from `bosses/level17.py` under the recording pygame shim, so every op (kind, geometry,
## colour, order) below comes from the source. The view must build the layer only for
## nyxareth's ultimate "4", from the live skill timer and pulse; `painter_scene_checks.gd`
## proves the live scene paints it.

const Layout = preload("res://scripts/ui/nyxareth_realm_layout.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/nyxareth_realm_draw_source.json"
const COMPARED_KEYS := ["kind", "rect", "color", "mult", "width", "radius", "blend"]


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


static func _frame(frames: Array, label: String) -> Dictionary:
	for frame in frames:
		if String(frame["label"]) == label:
			return frame
	return {}


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Nyxareth realm draw fixture parses")
	if not (data is Dictionary):
		return
	var frames: Array = data["frames"]
	var ops_total := 0
	for frame in frames:
		ops_total += frame["ops"].size()
	check.call(
		frames.size() == 7 and ops_total == 763,
		"Nyxareth realm oracle pins 7 source frames and 763 draw ops"
	)
	_check_palette(check, data)
	_check_frames(check, frames)
	_check_gate(check)
	_check_view_wiring(check, frames)


func _check_palette(check: Callable, data: Dictionary) -> void:
	var palette: Dictionary = data["palette"]
	check.call(
		(
			_value_equal(Layout.COSMIC_DARKEST, palette["cosmic_darkest"])
			and _value_equal(Layout.STAR_MID, palette["star_mid"])
			and _value_equal(Layout.STAR_BRIGHT, palette["star_bright"])
		),
		"The realm layout uses nyxareth's source palette"
	)
	check.call(String(data["skill"]) == Layout.SKILL, "The realm belongs to the smart ultimate 4")


func _check_frames(check: Callable, frames: Array) -> void:
	for frame in frames:
		var screen: Array = frame["screen"]
		var actual := Layout.ops(
			int(frame["timer"]), float(frame["phase"]), Vector2i(int(screen[0]), int(screen[1]))
		)
		var mismatch := _first_mismatch(actual, frame["ops"])
		check.call(
			mismatch == -1,
			"Realm frame %s matches the source ops (first mismatch %d)" % [frame["label"], mismatch]
		)
	var cast: Dictionary = _frame(frames, "cast")
	var full: Dictionary = _frame(frames, "layer_full")
	check.call(
		(
			not cast.is_empty()
			and not full.is_empty()
			and int(cast["ops"][0]["color"][3]) == 50
			and int(full["ops"][0]["color"][3]) == 80
		),
		"The cosmic layer fades in from alpha 50 on the first cast tick to 80"
	)


func _check_gate(check: Callable) -> void:
	check.call(Layout.active("nyxareth", "4"), "Nyxareth's ultimate 4 opens the realm")
	check.call(
		(
			not Layout.active("nyxareth", "3")
			and not Layout.active("nyxareth", "")
			and not Layout.active("nyxareth", "r")
			and not Layout.active("abaddon", "4")
		),
		"Other nyxareth skills and other bosses open no realm"
	)


func _check_view_wiring(check: Callable, frames: Array) -> void:
	var expected: Dictionary = _frame(frames, "layer_full")
	var view := PrototypeView.new()
	var boss := BossState.new()
	boss.boss_type = "nyxareth"
	boss.active_skill = "3"
	boss.active_skill_timer = int(expected.get("timer", 60))
	boss.pulse = float(expected.get("phase", 0.0))
	check.call(view.nyxareth_realm_draw_ops(boss).is_empty(), "Nyxareth's skill 3 paints no realm")
	boss.active_skill = "4"
	check.call(
		_first_mismatch(view.nyxareth_realm_draw_ops(boss), expected.get("ops", [])) == -1,
		"The view builds the realm from the live skill timer and pulse"
	)
	boss.boss_type = "abaddon"
	check.call(
		view.nyxareth_realm_draw_ops(boss).is_empty(), "Another boss's skill 4 paints no realm"
	)
	view.free()
