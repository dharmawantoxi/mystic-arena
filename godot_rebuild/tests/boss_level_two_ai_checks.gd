extends RefCounted

const BossAI = preload("res://scripts/match/boss_level_two_ai.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")

var fixture: Dictionary


func run(check: Callable) -> void:
	fixture = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/boss_level_two_ai_source.json")
	)
	for label in fixture.cases:
		_case(check, label, fixture.cases[label])


func _case(check: Callable, label: String, expected: Dictionary) -> void:
	var parts := label.split(":")
	var kind := parts[0]
	var mode := parts[1]
	var world := Prototype.new()
	world._spawn_boss(kind, false)
	var boss = world.active_boss
	boss.position = Vector2.ZERO
	var distance := 50.0
	var targets: Array[UnitState] = [_target(world, Vector2(distance, 0))]
	if mode == "cluster":
		targets.append(_target(world, Vector2(60, 0)))
		targets.append(_target(world, Vector2(70, 0)))
	elif mode == "far":
		distance = 130.0
		targets[0].position.x = distance
	elif mode == "low":
		boss.hp = int(float(boss.max_hp) * 0.5)
	elif mode == "critical_cluster":
		boss.hp = int(float(boss.max_hp) * 0.25)
		targets.append(_target(world, Vector2(60, 0), 200))
		targets.append(_target(world, Vector2(70, 0), 200))
	elif mode == "execute":
		targets[0].hp = 400
	elif mode == "q_only":
		boss.q_timer = 0
		boss.w_timer = 2
		boss.e_timer = 2
		boss.r_timer = 2
	BossAI.step(world, boss, targets, targets[0])
	check.call(boss.active_skill == String(expected.skill), "source level-2 priority " + label)
	(
		check
		. call(
			[boss.q_timer, boss.w_timer, boss.e_timer, boss.r_timer] == _ints(expected.timers),
			"source level-2 cooldowns " + label,
		)
	)
	(
		check
		. call(
			(
				is_equal_approx(boss.hp, float(expected.hp))
				and boss.damage == int(expected.damage)
				and is_equal_approx(boss.speed_px_per_tick, float(expected.speed))
				and boss.position.is_equal_approx(
					Vector2(expected.position[0], expected.position[1])
				)
				and boss.rage_active == bool(expected.rage[0])
				and boss.rage_timer == int(expected.rage[1])
			),
			"source level-2 self state " + label,
		)
	)
	for index in range(targets.size()):
		var target := targets[index]
		var target_expected: Dictionary = expected.targets[index]
		(
			check
			. call(
				(
					is_equal_approx(target.hp, float(target_expected.hp))
					and target.cooldown_ticks == int(target_expected.attack_timer)
					and is_equal_approx(target.slow_amount, float(target_expected.slow[0]))
					and target.slow_timer == int(target_expected.slow[1])
				),
				"source level-2 victim %s:%d" % [label, index],
			)
		)


func _target(world: Prototype, position: Vector2, hp: int = 2000) -> UnitState:
	var definition = GOBLIN.duplicate()
	definition.max_hp = 2000
	definition.armor = 0
	definition.magic_resist = 0.0
	var target := world.spawn_unit(definition, 0, 1)
	target.position = position
	target.hp = hp
	return target


func _ints(values: Array) -> Array:
	var result: Array = []
	for value in values:
		result.append(int(value))
	return result
