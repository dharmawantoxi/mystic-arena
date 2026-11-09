extends RefCounted

const Compare := preload("res://tests/ZephyrParticlesTest.gd")


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/zephyr_projectile.json", FileAccess.READ)
	runner.check(file != null, "Zephyr independent projectile oracle exists")
	if file == null:
		return
	var fixture: Dictionary = JSON.parse_string(file.get_as_text())
	for sample: Dictionary in fixture.cases:
		var a: Array = sample.args
		var projectile := ZephyrVisualProjectile.new().spawn(a[0], a[1], a[2], a[3], sample.options)
		projectile.random_tape = fixture.random_tape
		Compare._equal(
			runner, projectile.snapshot(), sample.initial, "visual projectile constructor"
		)
		var target: Dictionary = {}
		for index in sample.actions.size():
			var action: Dictionary = sample.actions[index]
			projectile.events.clear()
			projectile.hits.clear()
			if action.has("target"):
				target = action.target
			var alive: Variant = null
			if action.has("kill"):
				projectile.kill(action.kill)
			else:
				alive = projectile.update(action.dt, target, sample.connected)
			Compare._equal(
				runner,
				{
					"alive": alive,
					"state": projectile.snapshot(),
					"events": projectile.events,
					"hits": projectile.hits,
					"commands": projectile.commands(),
					"random_index": projectile.tape_index
				},
				sample.expected[index],
				"visual projectile step"
			)
	runner.check(
		ZephyrVisualProjectileSystem.new().cap == int(fixture.default_capacity),
		"visual cap comes from source"
	)
	_manager(runner, fixture.manager)
	_adapter(runner)


static func _manager(runner, sample: Dictionary) -> void:
	var manager := ZephyrVisualProjectileSystem.new()
	manager.cap = int(sample.cap)
	for index in sample.actions.size():
		var action: Array = sample.actions[index]
		var result: Variant = null
		match str(action[0]):
			"spawn":
				result = manager.spawn(action[1], action[2], action[3], action[4]) != null
			"update":
				manager.update(action[1])
			"clear":
				manager.clear()
		var states: Array = []
		for projectile: ZephyrVisualProjectile in manager.projectiles:
			states.append(projectile.snapshot())
		Compare._equal(
			runner,
			{"result": result, "states": states},
			sample.expected[index],
			"visual projectile manager"
		)


static func _adapter(runner) -> void:
	var owner := BattleUnit.new()
	owner.unit_type = "zephyr"
	var fx := HeroLiveFx.new()
	var feel := HeroCombatFeel.new()
	var projectile := fx.spawn_visual_projectile(owner, Vector2.ZERO, Vector2(1000, 0))
	runner.check(projectile != null, "visual spawn API accepts Zephyr")
	fx.update(feel, 1000)
	fx.update(feel, 1040)
	var x: float = projectile.position[0]
	runner.check(runner.near(x, 520.0 * 0.04), "visual projectile follows FX seconds")
	runner.check(
		fx.systems[owner.get_instance_id()].live.size() == 1, "visual tail emission reaches pool"
	)
	fx.update(feel, 1040)
	runner.check(projectile.position[0] == x, "duplicate clock cannot move visual twice")
	feel.hit_stop(0.08)
	fx.update(feel, 1056)
	runner.check(
		runner.near(projectile.position[0], x + 520.0 * 0.016 * 0.18),
		"visual projectile uses slow clock"
	)
	for index in 80:
		fx.update(feel, 1100 + index * 50)
	runner.check(fx.visual_projectiles.is_empty(), "expired visual manager is removed")
	fx.spawn_visual_projectile(owner, Vector2.ZERO, Vector2.ONE)
	fx.configure({"particles": false})
	runner.check(fx.visual_projectiles.is_empty(), "quality-off clears independent visuals")
	runner.check(
		fx.spawn_visual_projectile(owner, Vector2.ZERO, Vector2.ONE) == null,
		"quality-off blocks visual allocation"
	)
	fx.configure({"particles": true})
	fx.spawn_visual_projectile(owner, Vector2.ZERO, Vector2.ONE)
	fx.clear()
	runner.check(fx.visual_projectiles.is_empty(), "teardown clears independent visuals")
