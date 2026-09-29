extends RefCounted

const UnitState = preload("res://scripts/combat/unit_state.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")

var table: Dictionary
var fixture: Dictionary


func run(check: Callable) -> void:
	table = JSON.parse_string(FileAccess.get_file_as_string("res://data/bosses/boss_stats.json"))
	fixture = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/boss_movement_source.json")
	)
	_walk_and_chase(check)
	_attack_state(check)
	_kite(check)
	_world_attack_and_cleave(check)


func _boss(kind: String, lane: PackedVector2Array) -> BossState:
	var boss := BossState.new()
	boss.setup(kind, lane, table)
	return boss


func _walk_and_chase(check: Callable) -> void:
	var lane := PackedVector2Array([Vector2.ZERO, Vector2(10, 0), Vector2(20, 0)])
	var walker := _boss("gornak", lane)
	for index in range(fixture.walk.size()):
		walker.tick_basic_attack()
		walker.move_forward()
		var expected: Dictionary = fixture.walk[index]
		(
			check
			. call(
				(
					walker.position.is_equal_approx(
						Vector2(expected.position[0], expected.position[1])
					)
					and walker.waypoint_index == int(expected.waypoint)
					and walker.direction == int(expected.direction)
				),
				"source boss lane movement tick %d" % index,
			)
		)
	var chaser := _boss("gornak", lane)
	var quarry := UnitState.new()
	quarry.team = 0
	quarry.alive = true
	quarry.position = chaser.position - Vector2(chaser.attack_range + 40.0, 0)
	var enemies: Array[UnitState] = [quarry]
	var picked := chaser.pick_target(enemies)
	chaser.move_for_target(picked)
	(
		check
		. call(
			chaser.position.is_equal_approx(
				Vector2(fixture.chase.position[0], fixture.chase.position[1])
			),
			"source boss clamps chase step",
		)
	)


func _attack_state(check: Callable) -> void:
	var boss := _boss("gornak", PackedVector2Array([Vector2.ZERO, Vector2(20, 0)]))
	var target := UnitState.new()
	target.team = 0
	target.alive = true
	target.position = boss.position - Vector2(10, 0)
	check.call(boss.begin_basic_attack(target), "boss basic attack begins in range")
	(
		check
		. call(
			(
				boss.timer == int(fixture.attack.boss.timer)
				and boss.basic_attack_seq == int(fixture.attack.boss.attack_seq)
				and boss.attack_lock_timer == int(fixture.attack.boss.lock)
			),
			"source basic attack cooldown and swing lock",
		)
	)
	var slowed := _boss("gornak", PackedVector2Array([Vector2.ZERO, Vector2(20, 0)]))
	slowed.atk_slow_amount = 0.25
	slowed.atk_slow_timer = 9  # Source update ticks 10 to 9 before attacking.
	check.call(slowed.begin_basic_attack(target), "attack-slowed boss still attacks")
	check.call(slowed.timer == int(fixture.attack_slow_timer), "source Ice-slow cooldown rounding")


func _kite(check: Callable) -> void:
	var boss := _boss("morgath", PackedVector2Array([Vector2.ZERO, Vector2(20, 0)]))
	var target := UnitState.new()
	target.team = 0
	target.alive = true
	target.position = boss.position - Vector2(200, 0)
	boss.move_for_target(target)
	(
		check
		. call(
			(
				boss.position.is_equal_approx(
					Vector2(fixture.kite.position[0], fixture.kite.position[1])
				)
				and boss.kite_mode == fixture.kite.kite
			),
			"source ranged boss kiting hysteresis",
		)
	)


func _world_attack_and_cleave(check: Callable) -> void:
	var world := Prototype.new()
	check.call(world._spawn_boss("gornak", false), "movement fixture spawns boss")
	world.active_boss.position = Vector2(500, 500)
	world.active_boss.q_timer = 999
	world.active_boss.w_timer = 999
	world.active_boss.e_timer = 999
	world.active_boss.r_timer = 999
	var main := world.spawn_unit(GOBLIN, 0, 1)
	var splash := world.spawn_unit(GOBLIN, 0, 1)
	var far := world.spawn_unit(GOBLIN, 0, 1)
	main.position = world.active_boss.position - Vector2(10, 0)
	check.call(
		world.get_unit(world.active_boss.id) == world.active_boss, "active boss is targetable"
	)
	check.call(world._find_target(main) == world.active_boss, "blue minion acquires active boss")
	var boss_hp := world.active_boss.hp
	(
		check
		. call(
			(
				world._deliver_hit(main.id, 0, world.active_boss, 100, "physical", main.position)
				and world.active_boss.hp < boss_hp
				and world.active_boss.hp > boss_hp - 100
			),
			"incoming basics use boss mitigation exactly once",
		)
	)
	splash.position = world.active_boss.position - Vector2(20, 0)
	far.position = world.active_boss.position - Vector2(100, 0)
	main.hp = 1000
	splash.hp = 1000
	far.hp = 1000
	world._step_boss_combat()
	check.call(1000 - main.hp == int(fixture.attack.main[0].damage), "boss physical basic hit")
	check.call(1000 - splash.hp == int(fixture.attack.splash[0].damage), "boss neutral cleave")
	check.call(far.hp == 1000, "cleave excludes enemies outside source radius")
	var timer := world.active_boss.timer
	world._step_boss_combat()
	(
		check
		. call(
			(
				world.active_boss.timer == timer - 1
				and main.hp == 1000 - int(fixture.attack.main[0].damage)
			),
			"boss cannot attack again during cooldown",
		)
	)
