extends RefCounted

## Action-by-action oracle executes the actual Python module with a fake clock.


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/hero_combat_feel.json", FileAccess.READ)
	runner.check(file != null, "combat feel oracle exists")
	if file == null:
		return
	var fixture: Dictionary = JSON.parse_string(file.get_as_text())
	for scenario: Dictionary in fixture.cases:
		var bus := HeroCombatFeel.new()
		for index in scenario.actions.size():
			var action: Array = scenario.actions[index]
			var expected: Dictionary = scenario.expected[index]
			var result: Variant = null
			match str(action[0]):
				"hit_stop":
					bus.hit_stop(action[1])
				"freeze":
					result = bus.should_freeze_frame()
				"hit_stop_enabled":
					bus.hit_stop_enabled = bool(action[1])
				"shake_enabled":
					bus.shake_enabled = bool(action[1])
				"shake":
					bus.shake(float(action[1]), float(action[2]), bool(action[3]))
				"add_shake":
					bus.add_shake(float(action[1]), float(action[2]))
				"update_shake":
					bus.update_shake(float(action[1]))
				"frame_dt":
					result = bus.frame_dt(int(action[1]))
				"fx_dt":
					result = bus.fx_dt(int(action[1]))
				"reset":
					bus.reset()
				_:
					runner.check(false, "unknown combat feel oracle action")
			var label := "%s step %d" % [scenario.name, index]
			if expected.result is float:
				runner.check(runner.near(float(result), float(expected.result)), label + " result")
			else:
				runner.check(result == expected.result, label + " result")
			var state := bus.stats()
			for key: String in expected.stats:
				runner.check(
					runner.near(float(state[key]), float(expected.stats[key])), label + " " + key
				)
			for key: String in ["shake_strength", "shake_duration", "max_duration"]:
				runner.check(
					runner.near(float(bus.get(key)), float(expected[key])), label + " " + key
				)
			runner.check(runner.near(bus.progress(), float(expected.progress)), label + " progress")
	_forwarding(runner)
	_match_lifecycle(runner)


static func _forwarding(runner) -> void:
	var bus := HeroCombatFeel.new()
	var forwarded: Array[float] = []
	bus.camera_shake.connect(func(strength: float) -> void: forwarded.append(strength))
	bus.shake(3.9)
	bus.shake(8.0)
	bus.shake(8.0, 0.22, false)
	runner.check(forwarded == [2.0], "one scaled camera forward, no second offset")


static func _match_lifecycle(runner) -> void:
	var model := MatchModel.new()
	model.feel.hit_stop(0.03)
	model.step()
	runner.check(model.frame == 0, "hit stop freezes match simulation")
	model.clear_unit_refs()
	runner.check(model.feel.frames == 0, "match teardown clears hit stop")
	runner.check(model.feel.frame_ms == -1, "match teardown clears clock")
