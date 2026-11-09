extends RefCounted

const Compare := preload("res://tests/ZephyrParticlesTest.gd")


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/zephyr_trail.json", FileAccess.READ)
	runner.check(file != null, "Zephyr trail oracle exists")
	if file == null:
		return
	var fixture: Dictionary = JSON.parse_string(file.get_as_text())
	ZephyrSwingTrail.ensure_loaded()
	Compare._equal(
		runner,
		ZephyrSwingTrail.new().snapshot(),
		ZephyrSwingTrail.config.defaults,
		"source trail defaults"
	)
	for sample: Dictionary in fixture.cases:
		var trail := ZephyrSwingTrail.new()
		trail.samples = int(sample.samples)
		for index in sample.actions.size():
			var action: Array = sample.actions[index]
			match str(action[0]):
				"push":
					trail.push(action[1], action[2])
				"update":
					trail.update(float(action[1]))
				"width_boost":
					trail.width_boost = float(action[1])
				"reset":
					trail.reset()
			Compare._equal(
				runner, trail.snapshot(), sample.expected[index].state, "trail state %d" % index
			)
			Compare._equal(
				runner,
				trail.commands(),
				sample.expected[index].commands,
				"trail geometry %d" % index
			)
	for sample: Dictionary in fixture.world_attachments:
		var actual := ZephyrSwingTrail.attachment(
			int(sample.index), sample.position, int(sample.facing), float(sample.scale)
		)
		Compare._equal(runner, actual.inner, sample.inner, "source staff inner")
		Compare._equal(runner, actual.outer, sample.outer, "source staff outer")
	runner.check(
		ZephyrSwingTrail.attachment(-1, [0, 0], 1, 1.0).is_empty(), "invalid pose rejected"
	)
	_lifecycle(runner)


static func _lifecycle(runner) -> void:
	var fx := HeroLiveFx.new()
	var feel := HeroCombatFeel.new()
	var owner := BattleUnit.new()
	owner.kind = BattleUnit.Kind.HERO
	owner.unit_type = "zephyr"
	owner.pos = Vector2(100.25, 200.5)
	owner.attack_anim_timer = 18
	fx.update(feel, 1000)
	fx.capture_trails([owner], 1000)
	runner.check(fx.trails.is_empty(), "first clock timestamp has no fake FX delta")
	owner.attack_anim_timer = 11
	runner.check(ZephyrSwingTrail.pose_index(owner) == 3, "attack-local swing pose")
	runner.check(
		HeroVisuals.attack_frame([16, 8], owner) == 19, "body shares trail attack timeline"
	)
	fx.update(feel, 1016)
	fx.capture_trails([owner], 1016)
	var record: Dictionary = fx.trails[owner.get_instance_id()]
	var trail: ZephyrSwingTrail = record.trail
	runner.check(trail.points.size() == 1, "swing allocates one sample")
	fx.capture_trails([owner], 1016)
	runner.check(trail.points.size() == 1, "catch-up cannot duplicate trail sample")
	feel.hit_stop(0.08)
	owner.attack_anim_timer = 10
	owner.facing = -1
	fx.update(feel, 1032)
	fx.capture_trails([owner], 1032)
	runner.check(trail.points.size() == 2, "next timestamp samples facing change")
	runner.check(
		runner.near(float(trail.points[-1][2]), 0.016 * 0.18), "trail ages slowly during hit stop"
	)
	var anchor := ZephyrSwingTrail.attachment(
		3, [owner.pos.x, owner.pos.y], -1, float(ZephyrSwingTrail.config.hero_scale)
	)
	Compare._equal(runner, trail.points[-1][0], anchor.inner, "trail is attached to mirrored staff")
	owner.active_skill = "q"
	runner.check(
		ZephyrSwingTrail.pose_index(owner) == -1, "skill override suppresses attack attachment"
	)
	feel.reset()
	fx.update(feel, 1100)
	fx.capture_trails([owner], 1100)
	for index in 8:
		fx.update(feel, 1150 + index * 50)
		fx.capture_trails([], 1150 + index * 50)
	runner.check(fx.trails.is_empty(), "orphan trails expire without retaining owner references")
	owner.active_skill = ""
	fx.configure({"particles": false})
	fx.update(feel, 1600)
	fx.capture_trails([owner], 1600)
	runner.check(fx.trails.is_empty(), "quality disabled suppresses trail allocations")
	fx.clear()
	runner.check(
		fx.trail_ms == -1 and fx.trails.is_empty(), "teardown clears trail clock and state"
	)
