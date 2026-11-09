extends RefCounted


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/zephyr_particles.json", FileAccess.READ)
	runner.check(file != null, "Zephyr particle oracle exists")
	if file == null:
		return
	var fixture: Dictionary = JSON.parse_string(file.get_as_text())
	runner.check(
		ZephyrParticlePool.new().cap == int(fixture.default_capacity),
		"particle cap comes from Python source"
	)
	for sample: Dictionary in fixture.particles:
		var particle := ZephyrParticle.new()
		var args: Array = sample.args
		particle.spawn(
			args[0], args[1], args[2], args[3], args[4], args[5], args[6], sample.options
		)
		_equal(runner, particle.snapshot(), sample.expected[0].state, "particle spawn")
		_equal(runner, particle.commands(), sample.expected[0].commands, "particle spawn geometry")
		for index in sample.steps.size():
			particle.update(float(sample.steps[index]))
			_equal(runner, particle.snapshot(), sample.expected[index + 1].state, "particle motion")
			_equal(
				runner,
				particle.commands(),
				sample.expected[index + 1].commands,
				"particle geometry"
			)
	for sample: Dictionary in fixture.pools:
		var system := ZephyrParticlePool.new()
		system.cap = int(sample.cap)
		system.budget = float(sample.budget)
		system.random_tape = fixture.random_tape
		for index in sample.actions.size():
			var action: Array = sample.actions[index]
			var result: Variant = null
			match str(action[0]):
				"burst":
					result = system.burst(action[1], action[2], int(action[3]), action[4])
				"spawn":
					result = (
						system.spawn(
							action[1],
							action[2],
							action[3],
							action[4],
							action[5],
							action[6],
							action[7],
							action[8]
						)
						!= null
					)
				"budget":
					system.budget = float(action[1])
				"update":
					system.update(float(action[1]))
				"clear":
					system.clear()
			var live: Array = []
			var commands: Array = []
			for particle: ZephyrParticle in system.live:
				live.append(particle.snapshot())
				commands.append(particle.commands())
			_equal(
				runner,
				{
					"result": result,
					"live": live,
					"commands": commands,
					"pooled": system.pool.size(),
					"random_index": system.tape_index
				},
				sample.expected[index],
				"pool action %d" % index
			)
	for sample: Dictionary in fixture.recipes:
		_equal(
			runner,
			HeroLiveFx.impact_recipe(
				float(sample.power), bool(sample.critical), float(sample.angle)
			),
			sample.expected,
			"source impact recipe"
		)
	_hurt(runner, fixture.hurt)
	_shape_edges(runner)
	_lifecycle(runner)


static func _equal(runner, actual: Variant, expected: Variant, label: String) -> void:
	if expected is Dictionary:
		runner.check(actual is Dictionary, label + " dictionary")
		if not actual is Dictionary:
			return
		runner.check(actual.size() == expected.size(), label + " dictionary size")
		for key: String in expected:
			runner.check(actual.has(key), label + " key " + key)
			if actual.has(key):
				_equal(runner, actual[key], expected[key], label + "/" + key)
	elif expected is Array:
		runner.check(actual is Array, label + " array")
		if not actual is Array:
			return
		runner.check(actual.size() == expected.size(), label + " array size")
		for index in mini(actual.size(), expected.size()):
			_equal(runner, actual[index], expected[index], label + "/%d" % index)
	elif expected is float or expected is int:
		runner.check(runner.near(float(actual), float(expected)), label + " number")
	else:
		runner.check(actual == expected, label + " value")


static func _lifecycle(runner) -> void:
	var fx := HeroLiveFx.new()
	var owner := BattleUnit.new()
	owner.unit_type = "zephyr"
	for index in 100:
		fx.projectile_impact(owner, Vector2.ZERO, 0.7, 0.0, false)
	var system: ZephyrParticlePool = fx.systems[owner.get_instance_id()]
	runner.check(system.live.size() == 96, "particle cap is per owner")
	var feel := HeroCombatFeel.new()
	fx.update(feel, 1000)
	var life := system.live[0].life
	feel.hit_stop(0.08)
	fx.update(feel, 1016)
	runner.check(
		runner.near(system.live[0].life, life - 0.016 * 0.18), "particles slow during hit stop"
	)
	var after := system.live[0].life
	fx.update(feel, 1016)
	runner.check(runner.near(system.live[0].life, after), "catch-up cannot age FX twice")
	fx.clear()
	runner.check(fx.systems.is_empty() and fx.last_ms == -1, "FX teardown clears pools and clock")
	var reusable := ZephyrParticlePool.new()
	var first := reusable.spawn(0, 0, 1, 2, 0.02, 3, [10, 20, 30])
	reusable.update(0.03)
	var second := reusable.spawn(5, 6, 0, 0, 1.0, 4, [40, 50, 60])
	runner.check(first == second, "expired particle objects are reused")
	_equal(runner, second.snapshot().pos, [5, 6], "reused particle position resets")
	fx.configure({"particles": false})
	fx.projectile_impact(owner, Vector2.ZERO, 0.0, 0.0, false)
	runner.check(fx.systems.is_empty(), "disabled particles never allocate a pool")
	fx.configure({"particles": true, "particle_ratio": 1.0})
	fx.projectile_impact(owner, Vector2.ZERO, 0.0, 0.0, false)
	feel.reset()
	fx.update(feel, 2000)
	for index in 20:
		fx.update(feel, 2050 + index * 50)
	runner.check(fx.systems.is_empty(), "expired owner pools are removed without retaining units")


static func _shape_edges(runner) -> void:
	for shape: String in ["spark", "glow", "pixel"]:
		for alpha: int in [0, 3, 4]:
			var particle := ZephyrParticle.new().spawn(
				0, 0, 0, 0, 1, 1, [10, 20, 30], {"shape": shape, "alpha": alpha}
			)
			runner.check(particle.commands().is_empty() == (alpha <= 3), "alpha gate " + shape)
	var pool := ZephyrParticlePool.new()
	for shape: String in ["spark", "glow"]:
		var particle := pool.spawn(0, 0, 0, 0, 0.1, 4, [30, 60, 90], {"shape": shape})
		runner.check(particle.commands()[0][0] == shape, "pool routes " + shape)
	pool.update(0.2)
	runner.check(pool.live.is_empty() and pool.pool.size() == 2, "helper particles recycled")


static func _hurt(runner, cases: Array) -> void:
	for sample: Dictionary in cases:
		var hurt := ZephyrHurt.new()
		for index in sample.steps.size():
			var row: Array = sample.steps[index]
			var triggered := hurt.observe(row[0], row[1], row[2], row[3])
			var bursts: Array = []
			if triggered:
				var recipe := ZephyrHurt.recipe()
				bursts.append(
					{
						"position": [row[1], row[2] - 8],
						"count": recipe.count,
						"options": recipe.options
					}
				)
			_equal(
				runner,
				{"hit_flash": hurt.hit_flash, "bursts": bursts, "commands": hurt.commands()},
				sample.expected[index],
				"hurt source prefix"
			)
	var owner := BattleUnit.new()
	owner.unit_type = "zephyr"
	owner.hp = 100
	var feel := HeroCombatFeel.new()
	var fx := HeroLiveFx.new()
	fx.update(feel, 1000, [owner])
	runner.check(fx.systems.is_empty(), "first HP sample is baseline only")
	owner.hp = 85
	fx.update(feel, 1016, [owner])
	var key := owner.get_instance_id()
	runner.check(fx.systems[key].live.size() == 3, "HP loss emits hurt streaks")
	runner.check(fx.hurts[key].hit_flash > 0.0, "HP loss starts flash")
	owner.hp = 70
	fx.update(feel, 1016, [owner])
	runner.check(fx.systems[key].live.size() == 3, "duplicate timestamp cannot repeat burst")
	fx.update(feel, 1032, [owner])
	runner.check(fx.systems[key].live.size() == 6, "next timestamp observes later HP loss")
	fx.update(feel, 1048, [])
	runner.check(fx.hurts.is_empty(), "removed owner drops HP observer and flash")
	fx.update(feel, 1064, [owner])
	fx.configure({"particles": false})
	runner.check(fx.hurts.is_empty(), "quality-off clears hurt observer")
	fx.clear()
	runner.check(fx.hurts.is_empty(), "teardown clears hurt observer")
