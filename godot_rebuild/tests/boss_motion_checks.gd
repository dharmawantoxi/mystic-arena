# gdlint:disable=max-file-lines
extends RefCounted
## Layers 8c/8i: boss lane movement, ranged kiting, target registry, basic
## attacks, cooldown/cleave and one-shot hero damage/death reward wiring.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const FIXTURE := "res://tests/fixtures/boss_motion_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(
		fixture is Dictionary and fixture.has("forward") and fixture.has("ranged_kiting"),
		"boss motion fixture parses"
	)
	if not fixture is Dictionary:
		return
	_motion(check, fixture)
	_ranged_kiting(check, fixture)
	_ranged_kiting_match_step(check)
	_attack_and_registry(check, fixture)


func _world() -> Prototype:
	var world := Prototype.new()
	world.setup_arena()
	return world


func _motion(check: Callable, fixture: Dictionary) -> void:
	var world := _world()
	var boss := BossState.new()
	check.call(
		boss.setup(
			"gornak",
			PackedVector2Array([Vector2(0, 0), Vector2(10, 0), Vector2(20, 0)]),
			world.boss_table
		),
		"boss motion fixture boss sets up"
	)
	boss.speed_px_per_tick = 3.0
	boss.position = Vector2(20, 0)
	boss.previous_position = boss.position
	boss.waypoint_index = 2
	boss.move_forward()
	var first: Array = fixture.forward.first
	check.call(
		(
			is_equal_approx(boss.position.x, float(first[0]))
			and is_equal_approx(boss.position.y, float(first[1]))
			and boss.waypoint_index == int(first[2])
		),
		"boss consumes speed budget at first waypoint"
	)
	boss.move_forward()
	var second: Array = fixture.forward.second
	check.call(
		(
			is_equal_approx(boss.position.x, float(second[0]))
			and is_equal_approx(boss.position.y, float(second[1]))
			and boss.waypoint_index == int(second[2])
		),
		"boss keeps moving after a waypoint without a stall tick"
	)
	boss.direction = 1
	boss.attack_facing = -1.0
	boss.attack_lock_timer = 3
	boss.face_motion(1.0, 0.0)
	check.call(boss.direction == -1, "boss attack lock preserves facing")
	boss.attack_lock_timer = 0
	boss.face_motion(0.01, 2.0)
	check.call(boss.direction == -1, "near-vertical lane movement does not flip facing")
	boss.atk_slow_amount = 0.5
	boss.atk_slow_timer = 4
	boss.attack_cooldown = 38
	check.call(boss.effective_attack_cooldown() == 76, "boss attack cooldown honors attack slow")


func _ranged_kiting(check: Callable, fixture: Dictionary) -> void:
	var world := _world()
	var cases: Array = fixture.get("ranged_kiting", [])
	check.call(cases.size() == 48, "ranged kiting oracle has four cases for all twelve bosses")
	var boss_counts := {}
	for entry in cases:
		var boss := BossState.new()
		var boss_type := String(entry.get("boss_type", ""))
		boss_counts[boss_type] = int(boss_counts.get(boss_type, 0)) + 1
		check.call(
			boss.setup(boss_type, PackedVector2Array(), world.boss_table),
			"ranged kiting boss data loads: %s" % boss_type
		)
		if boss.boss_type.is_empty():
			continue
		check.call(
			(
				is_equal_approx(boss.min_distance, float(entry.get("min_distance", -1.0)))
				and is_equal_approx(boss.prefer_distance, float(entry.get("prefer_distance", -1.0)))
			),
			"ranged kiting source distances match boss data: %s" % boss_type
		)
		boss.position = Vector2.ZERO
		boss.speed_px_per_tick = float(entry.get("speed", 0.0))
		boss.kite_mode = String(entry.get("kite_mode", "hold"))
		boss.direction = -1
		boss.facing = -1.0
		var steps: Array = entry.get("steps", [])
		check.call(not steps.is_empty(), "ranged kiting trace has movement steps: %s" % boss_type)
		for step_index in range(steps.size()):
			var step: Dictionary = steps[step_index]
			boss.attack_range = float(step.get("attack_range", 0.0))
			var distance := float(step.get("distance", 0.0))
			boss.move_ranged_kite(Vector2(boss.position.x + distance, boss.position.y))
			var expected: Dictionary = step.get("expected", {})
			var label := "%s/%s/%d" % [boss_type, String(entry.get("label", "unknown")), step_index]
			check.call(
				(
					is_equal_approx(boss.position.x, float(expected.get("x", 0.0)))
					and is_equal_approx(boss.position.y, float(expected.get("y", 0.0)))
				),
				"ranged kiting position matches source: %s" % label
			)
			check.call(
				boss.kite_mode == String(expected.get("kite_mode", "")),
				"ranged kiting mode matches source: %s" % label
			)
			check.call(
				boss.direction == int(expected.get("direction", -99)),
				"ranged kiting facing matches source: %s" % label
			)
	check.call(boss_counts.size() == 12, "ranged kiting oracle covers exactly twelve bosses")
	for boss_type in boss_counts:
		check.call(
			int(boss_counts[boss_type]) == 4,
			"ranged kiting oracle has exactly four cases for %s" % String(boss_type)
		)


func _ranged_kiting_match_step(check: Callable) -> void:
	var world := _world()
	var boss := world._spawn_boss("ancient_apparition")
	check.call(boss != null, "ranged kiting match boss spawns")
	if boss == null:
		return
	var target: HeroState = null
	for unit in world.units:
		if unit.team == world.BLUE and unit is HeroState:
			target = unit as HeroState
			break
	check.call(target != null, "ranged kiting match has a blue hero target")
	if target == null:
		return
	boss.entrance_timer = 0
	boss.position = Vector2(400, 300)
	boss.previous_position = boss.position
	boss.speed_px_per_tick = 3.0
	boss.attack_range = 150.0
	boss.timer = 999
	boss.ability_timer = 999
	boss.ability2_timer = 999
	boss.q_timer = 999
	boss.w_timer = 999
	boss.e_timer = 999
	boss.r_timer = 999
	boss.active_skill_timer = 999
	boss.kite_mode = "hold"
	target.position = Vector2(555, 300)
	world._step_active_boss()
	check.call(boss.target_id == target.id, "ranged kiting match selects the in-handoff target")
	check.call(
		boss.kite_mode == "in" and is_equal_approx(boss.position.x, 403.0),
		"ranged boss uses source kite movement in the live match step"
	)


func _attack_and_registry(check: Callable, fixture: Dictionary) -> void:
	var world := _world()
	var boss := world._spawn_boss("gornak")
	check.call(boss != null and world.get_unit(boss.id) == boss, "active boss has a registry id")
	if boss == null:
		return
	boss.entrance_timer = 0
	boss.position = Vector2(300, 500)
	boss.previous_position = boss.position
	boss.attack_range = 100.0
	boss.damage = 100
	boss.attack_cooldown = 30
	boss.timer = 0
	boss.cleave_radius = 80.0
	boss.cleave_ratio = 0.40
	var hero: UnitState = null
	for unit in world.units:
		if unit.team == world.BLUE and unit is HeroState:
			hero = unit
			break
	check.call(hero != null, "blue hero is available for boss target checks")
	if hero == null:
		return
	hero.position = boss.position + Vector2(30, 0)
	var second_hero := world.spawn_hero(
		Prototype.THORNE, world.BLUE, boss.position + Vector2(45, 0)
	)
	check.call(second_hero != null, "second blue hero is available for cleave")
	if second_hero == null:
		return
	var hero_hp := hero.hp
	var second_hp := second_hero.hp
	world._step_active_boss()
	var attack_fixture: Dictionary = fixture.attack
	check.call(boss.target_id == hero.id, "boss selects nearest hero target")
	check.call(boss.basic_attack_seq == 1, "boss emits one basic attack edge")
	check.call(hero.hp < hero_hp, "boss basic physical attack damages primary target")
	check.call(second_hero.hp < second_hp, "boss cleave damages nearby enemy")
	check.call(boss.timer == int(attack_fixture.timer), "boss starts source attack cooldown")
	check.call(boss.attack_facing == 1.0, "boss caches attack facing")
	var after_first := boss.basic_attack_seq
	world._step_active_boss()
	check.call(boss.basic_attack_seq == after_first, "boss cooldown blocks immediate second attack")
	check.call(
		boss.timer == int(attack_fixture.timer) - 1, "boss cooldown ticks once per match tick"
	)

	var picked := world._hero_pick_target(hero as HeroState, 300.0, false)
	check.call(picked == boss, "hero target selection includes active boss")
	var item_enemies: Array = world._hero_enemy_list()
	var boss_in_items := false
	for entry in item_enemies:
		if int(entry.get("id", -1)) == boss.id:
			boss_in_items = true
	check.call(boss_in_items, "hero item enemy list includes active boss")

	var boss_hp := boss.hp
	hero.position = boss.position + Vector2(-30, 0)
	hero.attack_timer = 0
	check.call(
		world.hero_basic_attack(hero.id, boss.id), "hero can deliver a basic hit to active boss"
	)
	check.call(
		boss.hp < boss_hp and boss.last_hit_source_id == hero.id, "boss records hero damage source"
	)
	boss.hp = 1.0
	boss.alive = true
	boss.defeated = false
	hero.attack_timer = 0
	var gold_before: int = world.economy.gold[world.BLUE]
	var reward: int = boss.gold_reward
	check.call(
		world.hero_basic_attack(hero.id, boss.id), "hero can deliver the killing hit to active boss"
	)
	check.call(not boss.alive and boss.defeated, "boss death sets defeated exactly once")
	world._process_boss_result()
	var gold_after: int = world.economy.gold[world.BLUE]
	check.call(
		(
			world.active_boss == null
			and world.get_unit(boss.id) == null
			and gold_after == gold_before + reward
			and world.boss_rewards.size() == 1
		),
		"boss death retires registry entry and credits one reward"
	)
	world._process_boss_result()
	check.call(
		world.economy.gold[world.BLUE] == gold_after and world.boss_rewards.size() == 1,
		"reprocessing boss death does not duplicate reward"
	)
