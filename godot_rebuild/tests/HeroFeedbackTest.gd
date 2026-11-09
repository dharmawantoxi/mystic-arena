extends RefCounted


class Recorder:
	extends HeroCombatFeel
	var events: Array = []

	func shake(strength := 5.0, duration := 0.22, _forward_to_camera := true) -> void:
		events.append(["shake", [strength, duration]])

	func hit_stop(seconds: Variant = 0.045) -> void:
		events.append(["hit_stop", [seconds]])


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/hero_feedback.json", FileAccess.READ)
	runner.check(file != null, "starter feedback oracle exists")
	if file == null:
		return
	var fixture: Dictionary = JSON.parse_string(file.get_as_text())
	for sample: Dictionary in fixture.cases:
		var bus := Recorder.new()
		var params: Dictionary = sample.params
		match str(sample.method):
			"on_cast":
				HeroFeedback.cast(bus, str(sample.hero), str(params.skill))
			"on_impact":
				HeroFeedback.impact(bus, str(sample.hero), float(params.power), bool(params.crit))
			"projectile_hit":
				HeroFeedback.projectile_hit(
					bus, str(sample.hero), float(params.damage), bool(params.crit)
				)
		var expected: Array = sample.events
		runner.check(bus.events.size() == expected.size(), "feedback event count " + str(sample))
		for index in mini(bus.events.size(), expected.size()):
			var actual: Array = bus.events[index]
			var event: Array = expected[index]
			runner.check(actual[0] == event[0], "feedback event order " + str(sample))
			runner.check(actual[1].size() == event[1].size(), "feedback event arity")
			for arg in mini(actual[1].size(), event[1].size()):
				runner.check(
					runner.near(float(actual[1][arg]), float(event[1][arg])),
					"feedback argument " + str(sample)
				)
	_projectiles(runner)


static func _projectiles(runner) -> void:
	var model := MatchModel.new()
	var owner := BattleUnit.new()
	owner.unit_type = "zephyr"
	var target := BattleUnit.new()
	var projectile := {"kind": "hero", "source": owner, "damage": 0.0, "is_skill": false}
	EntityProjectiles._hit(model, projectile, target)
	runner.check(model.feel.frames == 0, "basic projectile never freezes gameplay")
	runner.check(model.hero_fx.systems.is_empty(), "basic projectile never allocates live FX")
	runner.check(
		model.hero_fx.impacts.is_empty(), "basic projectile never allocates impact overlays"
	)
	projectile.is_skill = true
	EntityProjectiles._hit(model, projectile, target)
	runner.check(model.feel.frames > 0, "skill projectile routes to shared feedback bus")
	runner.check(
		not model.hero_fx.systems.is_empty(), "skill projectile allocates native impact FX"
	)
	runner.check(not model.hero_fx.impacts.is_empty(), "skill projectile allocates impact overlays")
	model.clear_unit_refs()
	runner.check(model.hero_fx.systems.is_empty(), "match teardown clears native impact FX")
	runner.check(model.hero_fx.impacts.is_empty(), "match teardown clears impact overlays")
