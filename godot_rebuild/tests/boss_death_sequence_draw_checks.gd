extends RefCounted
## Layer 9bf: replays the `BossDeathAnimation._draw_death_sequence()` oracle fixture
## through `boss_death_sequence_layout.gd`. `boss_death_sequence_draw_source_oracle.py`
## runs the REAL class from `_render.py` under a recording pygame shim with seeded
## random fragments / rising particles, so every op (kind, geometry, colour, surface
## alpha, order) below comes from the source. The fixture stores the created
## particle dictionaries: each frame is replayed from a production
## `BossDeathAnimation` configured with them and ticked with `update()`, and again
## through `PrototypeView`.

const Layout = preload("res://scripts/ui/boss_death_sequence_layout.gd")
const BossDeath = preload("res://scripts/ui/boss_death_animation.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/boss_death_sequence_draw_source.json"
const COMPARED_KEYS := ["kind", "alpha", "center", "radius", "color", "mult", "width", "points"]


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
	anim.configure(
		scenario["boss"], int(screen[0]), int(screen[1]), scenario["fragments"], scenario["rising"]
	)
	return anim


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Boss death sequence draw fixture parses")
	if not (data is Dictionary):
		return
	check.call(data["frames"].size() == 12, "Boss death sequence oracle pins 12 source frames")
	var ops_total := 0
	for frame_value in data["frames"]:
		ops_total += frame_value["ops"].size()
	check.call(ops_total == 2299, "Boss death sequence oracle pins 2299 recorded draw ops")
	_check_production_replay(check, data)
	_check_stages(check, data)
	_check_overwrite_hints(check, data)
	_check_inactive(check, data)
	_check_view_wiring(check, data)


func _expect_ops(check: Callable, label: String, actual: Array, expected: Array) -> void:
	var bad := _first_mismatch(actual, expected)
	check.call(
		bad < 0,
		(
			"Boss death %s: %d ops match source (first mismatch #%d: got %s, want %s)"
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


func _check_production_replay(check: Callable, data: Dictionary) -> void:
	var replayed := 0
	for scenario_value in data["scenarios"]:
		var scenario: Dictionary = scenario_value
		var label := String(scenario["label"])
		var anim := _animation_for(scenario)
		check.call(anim.duration == int(scenario["duration"]), "Boss death %s duration" % label)
		for tick in range(int(scenario["ticks"].max()) + 1):
			var frame := _frame_at(data, label, tick)
			if not frame.is_empty():
				var state: Dictionary = frame["state"]
				check.call(
					anim.timer == int(state["timer"]) and anim.active == bool(state["active"]),
					"Boss death %s state matches the source timer" % _frame_key(label, tick)
				)
				_expect_ops(check, _frame_key(label, tick), Layout.ops(anim), frame["ops"])
				replayed += 1
			anim.update()
	check.call(
		replayed == data["frames"].size(),
		"Boss death production state replays every recorded frame (%d)" % replayed
	)


func _count(ops: Array, kind: String, width: int = -1) -> int:
	var total := 0
	for op_value in ops:
		var op: Dictionary = op_value
		if String(op["kind"]) == kind and (width < 0 or int(op["width"]) == width):
			total += 1
	return total


func _check_stages(check: Callable, data: Dictionary) -> void:
	check.call(
		(
			_count(_frame_ops(data, "abaddon_true", 0), "flash") == 1
			and int(_frame_ops(data, "abaddon_true", 0)[0]["alpha"]) == 200
		),
		"The white flash starts at alpha 200"
	)
	check.call(
		(
			int(_frame_ops(data, "abaddon_true", 7)[0]["alpha"]) == 106
			and _count(_frame_ops(data, "abaddon_true", 15), "flash") == 0
		),
		"The flash fades over 15 ticks"
	)
	check.call(
		_count(_frame_ops(data, "abaddon_true", 0), "circle", 3) == 0,
		"A radius-0 wave draws nothing on the first tick"
	)
	var early_ring: Dictionary = _frame_ops(data, "abaddon_true", 7)[1]
	check.call(
		_value_equal(early_ring["center"], [642, 362]) and int(early_ring["width"]) == 3,
		"A wave sits 2 px off the boss (the temp surface is 4 px larger)"
	)
	check.call(
		(
			_count(_frame_ops(data, "abaddon_true", 7), "circle", 3) == 4
			and _count(_frame_ops(data, "abaddon_true", 25), "circle", 3) == 14
			and _count(_frame_ops(data, "abaddon_true", 60), "circle", 3) == 7
			and _count(_frame_ops(data, "abaddon_true", 89), "circle", 3) == 0
		),
		"Waves overlap: 1, 2, then 1 ring set (4 / 7 rings each) and none at the end"
	)
	check.call(
		(
			_count(_frame_ops(data, "abaddon_true", 25), "polygon") == 50
			and _count(_frame_ops(data, "abaddon_true", 60), "polygon") == 0
			and _count(_frame_ops(data, "drakar_mini", 58), "polygon") == 0
		),
		"25 fragments (fill + edge) shatter, then vanish once life or alpha runs out"
	)
	check.call(
		_count(_frame_ops(data, "drakar_mini", 2), "polygon") == 30,
		"A mini boss shatters into 15 fragments"
	)
	check.call(
		(
			_body_ops(_frame_ops(data, "abaddon_true", 44)).size() == 2
			and _body_ops(_frame_ops(data, "abaddon_true", 45)).is_empty()
		),
		"The body dissolve ends at progress 0.5"
	)
	check.call(
		(
			_body_ops(_frame_ops(data, "drakar_mini", 30)).is_empty()
			and _body_ops(_frame_ops(data, "drakar_mini", 2)).size() == 2
		),
		"A mini boss body is gone by tick 30 of 60"
	)


## The two body discs: filled circles bigger than any rising-particle glow.
func _body_ops(ops: Array) -> Array:
	var body: Array = []
	for op_value in ops:
		var op: Dictionary = op_value
		if (
			String(op["kind"]) == "circle"
			and int(op["width"]) == 0
			and int(op["radius"]) >= 15
			and _value_equal(op["center"], [640, 360])
		):
			body.append(op)
	return body


func _check_overwrite_hints(check: Callable, data: Dictionary) -> void:
	var covered := 0
	for op_value in Layout.ops(_animation_at(data, 0, 60)):
		var op: Dictionary = op_value
		if int(op["width"]) == 3 and bool(op.get("covered", false)):
			covered += 1
	check.call(covered == 2, "The wave core (radius - 15) hides the two innermost rings")
	var early := Layout.ops(_animation_at(data, 0, 7))
	var body := _body_ops(early)
	check.call(
		body.size() == 2 and int(body[0]["ring_inner"]) == floori(float(body[0]["radius"]) / 2.0),
		"The body's outer disc leaves the annulus around the core"
	)
	var glow_ok := true
	var hidden := 0
	for op_value in early:
		var op: Dictionary = op_value
		if op.has("ring_inner") and int(op["radius"]) < 8:
			glow_ok = glow_ok and int(op["ring_inner"]) == int(op["radius"]) - 1
			if bool(op.get("covered", false)):
				hidden += 1
	check.call(glow_ok, "Each glow disc leaves a 1 px band around the next one")
	check.call(hidden == 30, "Only the radius-1 glow disc of each of the 30 particles is covered")


## A production animation ticked up to `tick` of scenario `index`.
func _animation_at(data: Dictionary, index: int, tick: int) -> BossDeath:
	var anim := _animation_for(data["scenarios"][index])
	for _step in range(tick):
		anim.update()
	return anim


func _check_inactive(check: Callable, data: Dictionary) -> void:
	var anim := _animation_at(data, 1, 0)
	check.call(not Layout.ops(anim).is_empty(), "A fresh death phase draws")
	for _step in range(anim.duration):
		anim.update()
	check.call(not anim.active and Layout.ops(anim).is_empty(), "A finished death phase is silent")


func _check_view_wiring(check: Callable, data: Dictionary) -> void:
	var world := Prototype.new()
	var view := PrototypeView.new()
	check.call(view.boss_death_draw_ops(world).is_empty(), "No boss death paints no ops")
	var anim := _animation_for(data["scenarios"][0])
	world.boss_death = anim
	for _tick in range(25):
		anim.update()
	_expect_ops(
		check,
		"view abaddon_true:25",
		view.boss_death_draw_ops(world),
		_frame_ops(data, "abaddon_true", 25)
	)
	for _tick in range(70):
		anim.update()
	check.call(view.boss_death_draw_ops(world).is_empty(), "A finished death phase paints no ops")
	view.free()
