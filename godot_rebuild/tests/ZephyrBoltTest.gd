extends RefCounted

## Compare native command geometry with the real Python draw_bolt recorder.
## Does not assert rasterized pixel equality or RGB_ADD compositing equality.


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/zephyr_bolt.json", FileAccess.READ)
	runner.check(file != null, "Zephyr bolt Python geometry fixture exists")
	if file == null:
		return
	var fixture: Dictionary = JSON.parse_string(file.get_as_text())
	runner.check(
		fixture.cases.size() == 80, "Zephyr bolt angle/critical/age/radius/position coverage"
	)
	for index in fixture.cases.size():
		var sample: Dictionary = fixture.cases[index]
		var params: Dictionary = sample.params
		var actual := ZephyrBolt.commands(
			Vector2(params.px, params.py),
			float(params.angle),
			int(params.age),
			bool(params.crit),
			float(params.radius)
		)
		_equal(runner, actual, sample.commands, "Zephyr bolt case %d" % index)
	runner.check(
		ZephyrBolt.commands(Vector2.ZERO, 0.0, 0, false, 0.0).is_empty(), "zero radius rejected"
	)
	runner.check(
		ZephyrBolt.commands(Vector2.ZERO, 0.0, 0, false, -1.0).is_empty(),
		"negative radius rejected"
	)


static func _equal(runner, actual: Variant, expected: Variant, label: String) -> void:
	if expected is Array:
		runner.check(actual is Array, label + " array type")
		if not actual is Array:
			return
		runner.check(actual.size() == expected.size(), label + " array length")
		for index in mini(actual.size(), expected.size()):
			_equal(runner, actual[index], expected[index], label + "/%d" % index)
	elif expected is float or expected is int:
		runner.check(runner.near(float(actual), float(expected)), label + " numeric value")
	else:
		runner.check(actual == expected, label + " value")
