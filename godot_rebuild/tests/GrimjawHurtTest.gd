extends RefCounted

const Compare := preload("res://tests/ZephyrParticlesTest.gd")


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/grimjaw_hurt.json", FileAccess.READ)
	runner.check(file != null, "Grimjaw hurt oracle exists")
	if file == null:
		return
	var fixture: Dictionary = JSON.parse_string(file.get_as_text())
	for sample: Dictionary in fixture.cases:
		var hurt := GrimjawHurt.new()
		for index in sample.steps.size():
			var row: Array = sample.steps[index]
			var bursts: Array = []
			if hurt.observe(row[0], row[1], row[2], row[3]):
				var recipe := GrimjawHurt.hurt_recipe()
				bursts.append(
					{
						"position": [row[1], row[2] - 10],
						"count": recipe.count,
						"options": recipe.options
					}
				)
			Compare._equal(
				runner,
				{"hit_flash": hurt.hit_flash, "bursts": bursts, "commands": hurt.commands()},
				sample.expected[index],
				"Grimjaw hurt source"
			)
	for row: Dictionary in fixture.budgets:
		runner.check(
			GrimjawHurt.budget_count(row.budget) == int(row.count), "Grimjaw budget round parity"
		)
	for sample: Dictionary in fixture.trajectories:
		var a: Array = sample.args
		var particle := ZephyrParticle.new().spawn(
			a[0], a[1], a[2], a[3], a[4], a[5], a[6], sample.options
		)
		for index in sample.steps.size():
			particle.update(sample.steps[index])
			Compare._equal(
				runner,
				{"state": particle.snapshot(), "commands": particle.commands()},
				sample.expected[index],
				"Grimjaw shared streak backend"
			)
	_death_particles(runner, fixture)
	_adapter(runner)


static func _adapter(runner) -> void:
	var owner := BattleUnit.new()
	owner.unit_type = "grimjaw"
	owner.hp = 100
	var key := owner.get_instance_id()
	var fx := HeroLiveFx.new()
	var feel := HeroCombatFeel.new()
	fx.update(feel, 1000, [owner])
	runner.check(fx.systems.is_empty(), "Grimjaw first HP sample is baseline")
	owner.hp = 90
	fx.update(feel, 1016, [owner])
	runner.check(fx.systems[key].cap == 108, "Grimjaw source pool cap")
	runner.check(fx.systems[key].live.size() == 3, "Grimjaw hurt emits three streaks")
	runner.check(fx.hurts.is_empty(), "Grimjaw never enters Zephyr observer map")
	fx.update(feel, 1016, [owner])
	runner.check(fx.systems[key].live.size() == 3, "Grimjaw duplicate timestamp is ignored")
	feel.hit_stop(0.08)
	var flash: float = fx.grimjaw_hurts[key].hit_flash
	fx.update(feel, 1032, [owner])
	runner.check(
		runner.near(fx.grimjaw_hurts[key].hit_flash, flash - .016 * .18),
		"Grimjaw flash uses slow FX clock"
	)
	fx.update(feel, 1048, [])
	runner.check(fx.grimjaw_hurts.is_empty(), "removed Grimjaw drops HP observer")
	fx.configure({"particles": false})
	fx.update(feel, 1064, [owner])
	runner.check(fx.grimjaw_hurts.is_empty(), "quality-off blocks Grimjaw observer")
	fx.clear()
	runner.check(
		fx.grimjaw_hurts.is_empty() and fx.systems.is_empty(), "Grimjaw teardown clears all state"
	)
	fx.configure({"particles": true, "particle_ratio": 0.5})
	feel.reset()
	fx.update(feel, 2000, [owner])
	owner.hp = 80
	fx.update(feel, 2016, [owner])
	runner.check(fx.systems[key].live.size() == 2, "Grimjaw budget applied once with ties-to-even")


static func _death_particles(runner, fixture: Dictionary) -> void:
	var observer := GrimjawHurt.new()
	for row: Dictionary in fixture.death:
		var triggered := observer.observe_death(row.alive)
		runner.check(triggered == (not row.bursts.is_empty()), "Grimjaw death edge parity")
	for sample: Dictionary in fixture.particles:
		var a: Array = sample.args
		var particle := GrimjawParticle.new().spawn(
			a[0], a[1], a[2], a[3], a[4], a[5], a[6], sample.options
		)
		particle.glow_allowed = sample.glow_allowed
		for index in sample.steps.size():
			particle.update(sample.steps[index])
			Compare._equal(
				runner,
				{"state": particle.snapshot(), "commands": particle.commands()},
				sample.expected[index],
				"Grimjaw death particle geometry"
			)
	for sample: Dictionary in fixture.pools:
		var pool := GrimjawParticlePool.new()
		pool.cap = 5
		pool.budget = sample.budget
		pool.random_tape = fixture.random_tape
		for index in sample.actions.size():
			var action: Array = sample.actions[index]
			var result: Variant = null
			match str(action[0]):
				"burst":
					result = pool.burst(action[1], action[2], int(action[3]), action[4])
				"stream":
					result = pool.stream(
						action[1], action[2], action[3], action[4], int(action[5]), action[6]
					)
				"update":
					pool.update(action[1])
				"clear":
					pool.clear()
			var live: Array = []
			for particle: ZephyrParticle in pool.live:
				live.append(particle.snapshot())
			Compare._equal(
				runner,
				{
					"result": result,
					"live": live,
					"pooled": pool.pool.size(),
					"random_index": pool.tape_index
				},
				sample.expected[index],
				"Grimjaw death pool"
			)
	var owner := BattleUnit.new()
	owner.unit_type = "grimjaw"
	var key := owner.get_instance_id()
	var fx := HeroLiveFx.new()
	var feel := HeroCombatFeel.new()
	fx.update(feel, 3000, [owner])
	owner.alive = false
	fx.update(feel, 3016, [owner])
	runner.check(fx.systems[key].live.size() == 13, "death emits eight ember plus five smoke")
	var back := 0
	for particle: ZephyrParticle in fx.systems[key].live:
		if particle.is_back():
			back += 1
	runner.check(back == 5, "smoke is routed behind characters")
	fx.update(feel, 3032, [owner])
	runner.check(fx.systems[key].live.size() == 13, "dead corpse cannot repeat death burst")
	for index in 30:
		fx.update(feel, 3080 + index * 50, [owner])
	runner.check(fx.systems.is_empty(), "death particles expire without leaking pools")
