extends RefCounted

const BossAI = preload("res://scripts/match/boss_level_one_ai.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")

var fixture: Dictionary


func run(check: Callable) -> void:
	fixture = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/boss_level_one_ai_source.json")
	)
	for label in fixture.cases:
		_case(check, label, fixture.cases[label])
	_generic(check)
	_heal(check)


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
	if mode == "low":
		boss.hp = int(float(boss.max_hp) * 0.25)
	elif mode == "cluster":
		targets.append(_target(world, Vector2(60, 0)))
		targets.append(_target(world, Vector2(70, 0)))
	elif mode == "far":
		distance = 130.0
		targets[0].position.x = distance
	elif mode == "execute":
		targets[0].hp = 400
	elif mode == "mid_hp":
		boss.hp = int(float(boss.max_hp) * 0.5)
	elif mode == "q_only":
		boss.q_timer = 0
		boss.w_timer = 2
		boss.e_timer = 2
		boss.r_timer = 2
	BossAI.step(world, boss, targets, targets[0])
	check.call(boss.active_skill == String(expected.skill), "source smart priority " + label)
	(
		check
		. call(
			[boss.q_timer, boss.w_timer, boss.e_timer, boss.r_timer] == _ints(expected.timers),
			"source smart cooldowns " + label,
		)
	)
	(
		check
		. call(
			(
				is_equal_approx(boss.hp, float(expected.hp))
				and boss.damage == int(expected.damage)
				and boss.position.is_equal_approx(
					Vector2(expected.position[0], expected.position[1])
				)
			),
			"source smart self state " + label,
		)
	)
	(
		check
		. call(
			(
				boss.flux_active_timer == int(expected.flux_timer)
				and boss.clones_active_timer == int(expected.clones_timer)
				and boss.rage_timer == int(expected.rage_timer)
				and boss.defense_timer == int(expected.defense_timer)
			),
			"source smart persistent state " + label,
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
				"source smart victim %s:%d" % [label, index],
			)
		)


func _generic(check: Callable) -> void:
	var world := Prototype.new()
	world._spawn_boss("krobellus", false)
	var boss = world.active_boss
	boss.position = Vector2.ZERO
	var inside := _target(world, Vector2(50, 0))
	var outside := _target(world, Vector2(boss.ability_range + 1, 0))
	var enemies: Array[UnitState] = [inside, outside]
	BossAI.generic_ability(world, boss, enemies)
	var expected: Dictionary = fixture.generic
	(
		check
		. call(
			(
				boss.ability_timer == int(expected.ability[0])
				and boss.ability_active == bool(expected.ability[1])
				and boss.ability_active_timer == int(expected.ability[2])
			),
			"source generic ability clocks",
		)
	)
	(
		check
		. call(
			(
				inside.hp == float(expected.targets[0].hp)
				and inside.cooldown_ticks == int(expected.targets[0].attack_timer)
				and outside.hp == float(expected.targets[1].hp)
			),
			"source generic ability range, damage and attack hold",
		)
	)


func _heal(check: Callable) -> void:
	var world := Prototype.new()
	world._spawn_boss("abaddon", true)
	var boss = world.active_boss
	boss.hp = int(float(boss.max_hp) * 0.2)
	BossAI.heal_ability(boss)
	(
		check
		. call(
			boss.hp == float(fixture.heal.hp) and boss.ability2_timer == int(fixture.heal.timer),
			"source true-boss low-HP heal",
		)
	)


func _target(world: Prototype, position: Vector2) -> UnitState:
	var definition = GOBLIN.duplicate()
	definition.max_hp = 2000
	definition.armor = 0
	definition.magic_resist = 0.0
	var target := world.spawn_unit(definition, 0, 1)
	target.position = position
	target.hp = 2000
	return target


func _ints(values: Array) -> Array:
	var result: Array = []
	for value in values:
		result.append(int(value))
	return result
