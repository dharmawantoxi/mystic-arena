extends RefCounted
## Layer 9bg: replays the `DeathExplosion.draw()` / `HitParticle.draw()` oracle
## fixture through `death_explosion_layout.gd` and `hit_particle_layout.gd`.
## `death_explosion_draw_source_oracle.py` runs the REAL classes from `_render.py`
## under a recording pygame shim with seeded random sparks, so every op (kind,
## geometry, colour, surface alpha, order) below comes from the source. The
## fixture stores the created sparks: each frame is replayed from a production
## `DeathExplosion` / `HitParticle` configured with them and ticked with
## `update()`, and again through `PrototypeView`.

const ExplosionLayout = preload("res://scripts/ui/death_explosion_layout.gd")
const SparkLayout = preload("res://scripts/ui/hit_particle_layout.gd")
const DeathExplosion = preload("res://scripts/ui/death_explosion.gd")
const HitParticle = preload("res://scripts/ui/hit_particle.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/death_explosion_draw_source.json"
const COMPARED_KEYS := ["kind", "center", "radius", "color", "mult", "width"]


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


static func _explosion_for(scenario: Dictionary) -> DeathExplosion:
	var explosion := DeathExplosion.new()
	explosion.configure(
		float(scenario["x"]),
		float(scenario["y"]),
		String(scenario["team"]),
		String(scenario["size"]),
		scenario["particles"]
	)
	return explosion


static func _sparks_for(scenario: Dictionary) -> Array:
	var sparks: Array = []
	for spec_value in scenario["particles"]:
		var spec: Dictionary = spec_value
		var tint: Array = spec["color"]
		var spark := HitParticle.new()
		spark.configure(
			float(spec["x"]),
			float(spec["y"]),
			Color8(int(tint[0]), int(tint[1]), int(tint[2])),
			Vector2(float(spec["vx"]), float(spec["vy"])),
			int(spec["lifetime"]),
			int(spec["size"])
		)
		sparks.append(spark)
	return sparks


static func _spark_ops(sparks: Array) -> Array:
	var result: Array = []
	for spark in sparks:
		result.append_array(SparkLayout.ops(spark))
	return result


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Death explosion draw fixture parses")
	if not (data is Dictionary):
		return
	check.call(data["frames"].size() == 25, "Death explosion oracle pins 25 source frames")
	var ops_total := 0
	for frame_value in data["frames"]:
		ops_total += frame_value["ops"].size()
	check.call(ops_total == 582, "Death explosion oracle pins 582 recorded draw ops")
	check.call(
		int(data["flash_frames"]) == DeathExplosion.FLASH_MAX,
		"Oracle flash length matches the port"
	)
	_check_production_replay(check, data)
	_check_flash(check, data)
	_check_sparks(check, data)
	_check_view_wiring(check, data)


func _expect_ops(check: Callable, label: String, actual: Array, expected: Array) -> void:
	var bad := _first_mismatch(actual, expected)
	check.call(
		bad < 0,
		(
			"Death explosion %s: %d ops match source (first mismatch #%d: got %s, want %s)"
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
		var is_burst := String(scenario["kind"]) == "explosion"
		var explosion: DeathExplosion = null
		var sparks: Array = []
		if is_burst:
			explosion = _explosion_for(scenario)
		else:
			sparks = _sparks_for(scenario)
		for tick in range(int(scenario["ticks"].max()) + 1):
			var frame := _frame_at(data, label, tick)
			if not frame.is_empty():
				var key := _frame_key(label, tick)
				var ops: Array = ExplosionLayout.ops(explosion) if is_burst else _spark_ops(sparks)
				_expect_ops(check, "production " + key, ops, frame["ops"])
				if is_burst:
					var state: Dictionary = frame["state"]
					check.call(
						(
							explosion.flash_timer == int(state["flash_timer"])
							and explosion.get_particle_count() == int(state["particles"])
						),
						"Death explosion %s state matches the source" % key
					)
				replayed += 1
			if is_burst:
				explosion.update()
			else:
				for spark in sparks:
					spark.update()
	check.call(
		replayed == data["frames"].size(),
		"Death explosion production state replays every recorded frame (%d)" % replayed
	)


func _check_flash(check: Callable, data: Dictionary) -> void:
	var first := _frame_ops(data, "red_small", 0)
	check.call(
		(
			_value_equal(first[0]["radius"], 20)
			and _value_equal(first[0]["color"], [255, 255, 200, 200])
			and _value_equal(first[1]["radius"], 10)
			and _value_equal(first[1]["color"], [255, 255, 255, 255])
			and _value_equal(first[0]["center"], [120, 80])
		),
		"Flash: 20 px pale disc (alpha 200) under a 10 px white core at the truncated anchor"
	)
	var last := _frame_ops(data, "red_small", 7)
	check.call(
		(
			_value_equal(last[0]["radius"], 2)
			and int(last[0]["color"][3]) == 25
			and _value_equal(last[1]["radius"], 1)
			and int(last[1]["color"][3]) == 31
		),
		"Flash shrinks and fades with the timer (tick 7: 2 px, alpha 25 / 31)"
	)
	check.call(
		(
			_frame_ops(data, "red_small", 8).size() == 16
			and _frame_ops(data, "blue_large", 34).is_empty()
		),
		"No flash after 8 ticks, and a spent explosion draws nothing"
	)
	var flash_op: Dictionary = ExplosionLayout.ops(_burst_at(data, 0, 0))[0]
	check.call(
		int(flash_op["ring_inner"]) == 10, "The outer flash disc leaves the annulus around the core"
	)


## A production explosion of scenario `index` ticked `tick` times.
func _burst_at(data: Dictionary, index: int, tick: int) -> DeathExplosion:
	var explosion := _explosion_for(data["scenarios"][index])
	for _step in range(tick):
		explosion.update()
	return explosion


func _check_sparks(check: Callable, data: Dictionary) -> void:
	var sparks := _sparks_for(data["scenarios"][3])
	var ops := _spark_ops(sparks)
	check.call(ops.size() == 8, "Four live sparks draw a colour disc and a white core each")
	check.call(
		bool(ops[2]["covered"]) and not bool(ops[0]["covered"]),
		"A size-1 spark's white core hides its whole colour disc"
	)
	check.call(
		(
			float(ops[0]["ring_inner"]) == float(ops[1]["radius"])
			and ops[0]["center"] == ops[1]["center"]
		),
		"A spark's colour disc leaves the annulus around its core"
	)
	for _step in range(5):
		for spark in sparks:
			spark.update()
	var scaled: Array = _spark_ops(sparks)
	check.call(
		absf(float(scaled[6]["center"][0]) - 230.33333333333334) < 1e-6,
		"A shrunken sprite is scaled about its own centre before the int() blit offset"
	)
	for _step in range(4):
		for spark in sparks:
			spark.update()
	check.call(_spark_ops(sparks).size() == 6, "A spark whose lifetime ended is skipped")
	var dead := HitParticle.new()
	check.call(
		SparkLayout.ops(dead).is_empty(), "A particle that was never configured draws nothing"
	)


func _check_view_wiring(check: Callable, data: Dictionary) -> void:
	var view := PrototypeView.new()
	var explosion := _burst_at(data, 1, 12)
	_expect_ops(
		check,
		"view blue_medium:12",
		view.death_explosion_draw_ops(explosion),
		_frame_ops(data, "blue_medium", 12)
	)
	var sparks := _sparks_for(data["scenarios"][3])
	_expect_ops(
		check,
		"view sparks:0 (first spark)",
		view.hit_particle_draw_ops(sparks[0]),
		_frame_ops(data, "sparks", 0).slice(0, 2)
	)
	view.free()
