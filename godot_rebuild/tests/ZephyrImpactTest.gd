extends RefCounted

const Compare := preload("res://tests/ZephyrParticlesTest.gd")


static func _spawn(args: Array) -> ZephyrImpact:
	return ZephyrImpact.new().spawn(
		float(args[0]), float(args[1]), float(args[2]), float(args[3]), bool(args[4])
	)


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/zephyr_impact.json", FileAccess.READ)
	runner.check(file != null, "Zephyr ImpactFX Python oracle exists")
	if file == null:
		return
	var fixture: Dictionary = JSON.parse_string(file.get_as_text())
	for sample: Dictionary in fixture.cases:
		var impact := _spawn(sample.args)
		Compare._equal(runner, impact.snapshot(), sample.initial, "impact constructor")
		for frame: Dictionary in sample.frames:
			impact.age = float(frame.state.age)
			impact.active = bool(frame.state.active)
			Compare._equal(runner, impact.snapshot(), frame.state, "impact absolute age state")
			Compare._equal(
				runner, impact.commands(), frame.commands, "impact primitive/helper commands"
			)
		impact = _spawn(sample.args)
		for step: Dictionary in sample.lifecycle:
			runner.check(
				impact.update(float(step.dt)) == bool(step.result),
				"impact update returns source lifecycle"
			)
			Compare._equal(runner, impact.snapshot(), step.state, "impact update state")
	for sample: Dictionary in fixture.spark_helpers:
		Compare._equal(
			runner,
			ZephyrBolt.spark_commands(int(sample.size), sample.color),
			sample.commands,
			"source spark helper geometry"
		)
	for sample: Dictionary in fixture.ellipse_rotations:
		runner.check(
			runner.near(ZephyrBolt.ellipse_rotation(float(sample.degrees)), float(sample.expected)),
			"source ellipse angle quantization"
		)
	_lifecycle(runner, int(fixture.director_limit))


static func _lifecycle(runner, limit: int) -> void:
	var fx := HeroLiveFx.new()
	var owner := BattleUnit.new()
	owner.unit_type = "zephyr"
	for index in range(limit + 4):
		fx.projectile_impact(owner, Vector2(index, 0), 0.7, 0.0, false)
	var events: Array = fx.impacts[owner.get_instance_id()]
	runner.check(events.size() == limit, "impact list respects Python director cap")
	runner.check(runner.near(events[0].x, 4.0), "oldest impact evicted first")
	var feel := HeroCombatFeel.new()
	fx.update(feel, 1000)
	feel.hit_stop(0.08)
	fx.update(feel, 1016)
	runner.check(runner.near(events[0].age, 0.016 * 0.18), "impact ages slowly during hit stop")
	var age := float(events[0].age)
	fx.update(feel, 1016)
	runner.check(
		runner.near(events[0].age, age), "duplicate timestamp does not update impacts twice"
	)
	feel.reset()
	fx.update(feel, 1100)
	for index in 15:
		fx.update(feel, 1150 + index * 50)
	runner.check(fx.impacts.is_empty(), "orphan impacts expire and release owner IDs")
	fx.projectile_impact(owner, Vector2.ZERO, 0, 0, false)
	fx.configure({"particles": false})
	runner.check(fx.impacts.is_empty(), "quality disabled clears impact overlays")
	fx.projectile_impact(owner, Vector2.ZERO, 0, 0, false)
	runner.check(fx.impacts.is_empty(), "quality disabled allocates no impacts")
	fx.clear()
	runner.check(
		fx.impacts.is_empty() and fx.last_ms == -1, "teardown clears impact state and clock"
	)
