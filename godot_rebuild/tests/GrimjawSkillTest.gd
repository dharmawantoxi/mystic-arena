extends RefCounted

const Compare := preload("res://tests/ZephyrParticlesTest.gd")


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/grimjaw_skill.json", FileAccess.READ)
	runner.check(file != null, "Grimjaw SkillFX oracle exists")
	if file == null:
		return
	var fixture: Dictionary = JSON.parse_string(file.get_as_text())
	for sample: Dictionary in fixture.cases:
		var skill := GrimjawSkill.new()
		skill.random_tape = fixture.random_tape
		var radius := float(sample.radius) if sample.radius != null else 0.0
		skill.spawn(sample.key, -20.75, 13.25, radius, 1234)
		Compare._equal(runner, skill.snapshot(), sample.initial, "Grimjaw skill constructor")
		for index in sample.steps.size():
			var alive := skill.update(sample.steps[index], sample.connected)
			Compare._equal(
				runner,
				{
					"alive": alive,
					"state": skill.snapshot(),
					"events": skill.events,
					"random_index": skill.tape_index
				},
				sample.expected[index],
				"Grimjaw skill emission"
			)
		runner.check(
			skill.ground_commands().is_empty(), "Grimjaw ground skill geometry is still pending"
		)
	for sample: Dictionary in fixture.front:
		var skill := GrimjawSkill.new()
		skill.spawn(sample.key, sample.x, sample.y)
		skill.age = str(sample.age_f64).hex_decode().decode_double(0)
		skill.phase = sample.phase
		skill.active = sample.active
		skill.facing = int(sample.facing)
		skill.glow_allowed = sample.glow
		Compare._equal(
			runner,
			skill.front_commands(sample.detail),
			sample.commands,
			"Grimjaw front primitive geometry"
		)
	_adapter(runner)


static func _adapter(runner) -> void:
	var fx := HeroLiveFx.new()
	var owner := BattleUnit.new()
	owner.unit_type = "grimjaw"
	owner.pos = Vector2(30, 50)
	owner.skill_range = 140
	var key := owner.get_instance_id()
	fx.cast(owner, "q")
	var first: ZephyrSkill = fx.skills[key][0]
	runner.check(first is GrimjawSkill, "Grimjaw cast uses its own SkillFX")
	runner.check(first.radius == 140 and first.y == 66, "Grimjaw Q source range and cast y+16")
	for name: String in ["w", "e", "r"]:
		fx.cast(owner, name)
	runner.check(
		fx.skills[key].size() == 3 and not fx.skills[key].has(first),
		"Grimjaw skill cap evicts oldest"
	)
	var feel := HeroCombatFeel.new()
	fx.update(feel, 1000)
	fx.update(feel, 1040)
	runner.check(
		fx.systems[key] is GrimjawParticlePool, "Grimjaw skill emissions reach Grimjaw pool"
	)
	runner.check(fx.systems[key].live.size() == 3, "three charging effects each emit once")
	var age: float = fx.skills[key][0].age
	fx.update(feel, 1040)
	runner.check(fx.skills[key][0].age == age, "duplicate timestamp does not age Grimjaw skill")
	feel.hit_stop(0.08)
	fx.update(feel, 1056)
	runner.check(
		runner.near(fx.skills[key][0].age, age + .016 * .18), "Grimjaw skill uses slow FX clock"
	)
	feel.reset()
	for index in 100:
		fx.update(feel, 1100 + index * 50)
	runner.check(
		fx.skills.is_empty() and fx.systems.is_empty(), "Grimjaw skill and particles expire"
	)
	fx.configure({"particles": false})
	fx.cast(owner, "r")
	runner.check(fx.skills.is_empty(), "quality-off blocks Grimjaw skill")
	fx.configure({"particles": true})
	fx.cast(owner, "q")
	fx.clear()
	runner.check(fx.skills.is_empty(), "teardown clears Grimjaw skill")
