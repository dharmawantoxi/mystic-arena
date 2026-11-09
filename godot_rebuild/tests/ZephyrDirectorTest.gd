extends RefCounted

const Compare := preload("res://tests/ZephyrParticlesTest.gd")


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/zephyr_director.json", FileAccess.READ)
	runner.check(file != null, "Zephyr director oracle exists")
	if file == null:
		return
	var fixture: Dictionary = JSON.parse_string(file.get_as_text())
	for sequence: Array in fixture.cases:
		var director := ZephyrDirectorState.new()
		for row: Dictionary in sequence:
			director.update(row.dt, row.input)
			Compare._equal(
				runner, director.snapshot(), row.expected, "director state and swing edge"
			)
	_integration(runner)


static func _integration(runner) -> void:
	var owner := BattleUnit.new()
	owner.kind = BattleUnit.Kind.HERO
	owner.unit_type = "zephyr"
	owner.attack_anim_timer = 60
	owner.attack_anim_duration = 100
	owner.pos = Vector2(30, 50)
	var key := owner.get_instance_id()
	var fx := HeroLiveFx.new()
	var feel := HeroCombatFeel.new()
	fx.update(feel, 1000, [owner])
	fx.capture_trails([owner], 1000)
	fx.update(feel, 1016, [owner])
	fx.capture_trails([owner], 1016)
	runner.check(fx.directors[key].state == "SWING", "director reads normalized attack timeline")
	runner.check(fx.systems[key].live.size() == 2, "swing edge emits two anticipation particles")
	var state_time: float = fx.directors[key].state_time
	fx.capture_trails([owner], 1016)
	runner.check(fx.systems[key].live.size() == 2, "duplicate capture cannot repeat dust")
	runner.check(
		fx.directors[key].state_time == state_time, "duplicate capture cannot age director"
	)
	fx.update(feel, 1032, [owner])
	fx.capture_trails([owner], 1032)
	runner.check(fx.systems[key].live.size() == 2, "continuous swing does not repeat edge")
	owner.attack_anim_timer = 20
	owner.attack_anim_duration = 100
	fx.update(feel, 1048, [owner])
	fx.capture_trails([owner], 1048)
	runner.check(fx.directors[key].edge == "end", "leaving swing emits end edge")
	owner.attack_anim_timer = 50
	owner.attack_anim_duration = 100
	fx.update(feel, 1064, [owner])
	fx.capture_trails([owner], 1064)
	runner.check(fx.systems[key].live.size() == 4, "new swing emits another pair")
	fx.update(feel, 1080, [])
	fx.capture_trails([], 1080)
	runner.check(fx.directors.is_empty(), "removed owner drops director")
	fx.update(feel, 1096, [owner])
	fx.capture_trails([owner], 1096)
	fx.configure({"particles": false})
	runner.check(fx.directors.is_empty(), "quality-off clears directors")
	fx.clear()
	runner.check(fx.directors.is_empty(), "teardown clears directors")
