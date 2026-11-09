extends RefCounted

const Compare := preload("res://tests/ZephyrParticlesTest.gd")


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/zephyr_skill.json", FileAccess.READ)
	runner.check(file != null, "SkillFX oracle exists")
	if file == null:
		return
	var fixture: Dictionary = JSON.parse_string(file.get_as_text())
	for sample: Dictionary in fixture.cases:
		var skill := ZephyrSkill.new()
		skill.random_tape = fixture.random_tape
		var radius := float(sample.radius) if sample.radius != null else 0.0
		skill.spawn(sample.kind, -20.75, 13.25, radius, 1234)
		Compare._equal(runner, skill.snapshot(), sample.initial, "skill constructor")
		for index in sample.steps.size():
			var alive := skill.update(float(sample.steps[index]), bool(sample.connected))
			Compare._equal(
				runner,
				{
					"alive": alive,
					"state": skill.snapshot(),
					"events": skill.events,
					"random_index": skill.tape_index
				},
				sample.expected[index],
				"skill update"
			)
	for sample: Dictionary in fixture.front:
		var skill := ZephyrSkill.new().spawn(sample.kind, sample.x, sample.y)
		skill.age = str(sample.age_f64).hex_decode().decode_double(0)
		skill.phase = sample.phase
		skill.active = sample.active
		Compare._equal(
			runner, skill.front_commands(sample.detail), sample.commands, "skill front geometry"
		)
	runner.check(
		ZephyrSkill.python_round(4.5) == 4 and ZephyrSkill.python_round(5.5) == 6,
		"rune detail ties round to even"
	)
	for sample: Dictionary in fixture.ground:
		var skill := ZephyrSkill.new().spawn(sample.kind, sample.x, sample.y, 0.0, 1234)
		skill.age = str(sample.age_f64).hex_decode().decode_double(0)
		skill.phase = sample.phase
		skill.active = sample.active
		Compare._equal(
			runner, skill.ground_commands(sample.detail), sample.commands, "skill ground geometry"
		)
	runner.check(
		ZephyrSkill.new().spawn("q", 0, 0).ground_commands().is_empty(),
		"ground waits for first phase update"
	)
	_integration(runner)


static func _integration(runner) -> void:
	var fx := HeroLiveFx.new()
	var owner := BattleUnit.new()
	owner.unit_type = "zephyr"
	owner.pos = Vector2(30, 50)
	var key := owner.get_instance_id()
	fx.cast(owner, "q")
	var oldest: ZephyrSkill = fx.skills[key][0]
	for skill: String in ["w", "e", "r"]:
		fx.cast(owner, skill)
	runner.check(fx.skills[key].size() == 3, "skill cap is three per owner")
	runner.check(not fx.skills[key].has(oldest), "skill cap evicts oldest")
	runner.check(fx.skills[key][0].kind == "w", "skill eviction preserves order")
	runner.check(fx.skills[key][0].y == 68, "cast origin adds source offset")
	var feel := HeroCombatFeel.new()
	fx.update(feel, 1000)
	fx.update(feel, 1040)
	runner.check(fx.systems.has(key), "charge produces live particles")
	var age: float = fx.skills[key][0].age
	fx.update(feel, 1040)
	runner.check(fx.skills[key][0].age == age, "duplicate timestamp does not age skill")
	feel.hit_stop(0.08)
	fx.update(feel, 1056)
	runner.check(runner.near(fx.skills[key][0].age, age + 0.016 * 0.18), "skill uses slow FX clock")
	feel.reset()
	for index in 100:
		fx.update(feel, 1100 + index * 50)
	runner.check(fx.skills.is_empty(), "expired skills remove owner map")
	fx.configure({"particles": false})
	fx.cast(owner, "r")
	runner.check(fx.skills.is_empty(), "disabled skill does not allocate")
	fx.configure({"particles": true})
	fx.cast(owner, "q")
	fx.clear()
	runner.check(fx.skills.is_empty(), "teardown clears skill state")
	owner.unit_type = "default"
	fx.cast(owner, "q")
	runner.check(fx.skills.is_empty(), "other heroes do not emit Zephyr SkillFX")
