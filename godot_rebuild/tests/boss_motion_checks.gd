# gdlint:disable=max-file-lines
extends RefCounted
## Layers 8c/8i/8j: lane movement, ranged kiting/AI range gate, target
## registry, basic attacks, cooldown/cleave and one-shot death reward wiring.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const THORNE = preload("res://data/heroes/thorne.tres")
const FIXTURE := "res://tests/fixtures/boss_motion_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(
		(
			fixture is Dictionary
			and fixture.has("forward")
			and fixture.has("ranged_kiting")
			and fixture.has("smart_ai_dispatch")
			and fixture.has("basic_attack_source")
		),
		"boss motion fixture parses"
	)
	if not fixture is Dictionary:
		return
	_motion(check, fixture)
	_ranged_kiting(check, fixture)
	_smart_ai_dispatch(check, fixture)
	_basic_attack_source(check, fixture)
	_basic_attack_reactive_reflect(check)
	_ranged_kiting_match_step(check)
	_ranged_ai_dispatch_match_step(check)
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


func _smart_ai_dispatch(check: Callable, fixture: Dictionary) -> void:
	var world := _world()
	var cases: Array = fixture.get("smart_ai_dispatch", [])
	check.call(cases.size() == 316, "smart-AI range gate has four source cases for 79 boss recipes")
	var boss_counts := {}
	for entry in cases:
		var boss := BossState.new()
		var boss_type := String(entry.get("boss_type", ""))
		boss_counts[boss_type] = int(boss_counts.get(boss_type, 0)) + 1
		check.call(
			boss.setup(boss_type, PackedVector2Array(), world.boss_table),
			"smart-AI gate boss data loads: %s" % boss_type
		)
		if boss.boss_type.is_empty():
			continue
		check.call(
			is_equal_approx(boss.attack_range, float(entry.get("attack_range", -1.0))),
			"smart-AI gate range matches source stats: %s" % boss_type
		)
		boss.position = Vector2.ZERO
		world.active_boss = boss
		var distance := float(entry.get("distance", 0.0))
		var enemy := UnitState.new()
		enemy.team = world.BLUE
		enemy.alive = true
		enemy.position = Vector2(distance, 0.0)
		var enemies: Array[UnitState] = []
		enemies.append(enemy)
		var selected := world._boss_target(enemies) != null
		var dispatch := selected and boss.is_in_attack_range(distance)
		var expected: Dictionary = entry.get("expected", {})
		var label := "%s/%s" % [boss_type, String(entry.get("label", "unknown"))]
		check.call(
			selected == bool(expected.get("target_selected", false)),
			"smart-AI target window matches source: %s" % label
		)
		check.call(
			boss.is_in_attack_range(distance) == (distance <= boss.attack_range),
			"smart-AI inclusive attack-range predicate: %s" % label
		)
		check.call(
			(
				dispatch == bool(expected.get("smart_ai_dispatched", false))
				and int(expected.get("smart_ai_call_count", -1)) == (1 if dispatch else 0)
			),
			"smart-AI dispatch decision matches source: %s" % label
		)
	check.call(boss_counts.size() == 79, "smart-AI range gate covers all 79 source recipes")
	for boss_type in boss_counts:
		check.call(
			int(boss_counts[boss_type]) == 4,
			"smart-AI range gate has exactly four cases for %s" % String(boss_type)
		)


func _basic_attack_source(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("basic_attack_source", [])
	check.call(
		cases.size() == 864, "basic boss attack has four source cases for all 216 boss types"
	)
	var boss_counts := {}
	var world := _world()
	world.units.clear()
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		boss_counts[boss_type] = int(boss_counts.get(boss_type, 0)) + 1
		world.active_boss = null
		world.units.clear()
		world.recent_events.clear()
		var boss: BossState = world._spawn_boss(boss_type)
		check.call(boss != null, "basic attack source boss data loads: %s" % boss_type)
		if boss == null:
			continue
		boss.team = world.RED
		boss.position = Vector2(700.0, 300.0)
		boss.previous_position = boss.position
		boss.entrance_timer = 0
		boss.timer = int(entry.get("initial_timer", 0))
		boss.ability_timer = 999
		boss.ability2_timer = 999
		boss.q_timer = 999
		boss.w_timer = 999
		boss.e_timer = 999
		boss.r_timer = 999
		boss.active_skill = ""
		boss.active_skill_timer = 0
		var distance := float(entry.get("distance", 0.0))
		var target := world.spawn_hero(KAIZEN, world.BLUE, boss.position + Vector2(distance, 0.0))
		check.call(target != null, "basic attack source target spawns: %s" % boss_type)
		if target == null:
			continue
		var expected: Dictionary = entry.get("expected", {})
		var expected_cleave: Array = expected.get("cleave_calls", [])
		var cleave: HeroState = null
		if not expected_cleave.is_empty():
			cleave = world.spawn_hero(KAIZEN, world.BLUE, boss.position + Vector2(20.0, 0.0))
		var selected := world._boss_target(world._boss_enemies())
		check.call(
			(selected == target) == bool(expected.get("target_selected", false)),
			(
				"basic attack target acquisition matches source: %s/%s"
				% [boss_type, String(entry.get("label", ""))]
			)
		)
		world._step_active_boss()
		var primary_hits: Array[Dictionary] = []
		var cleave_hits: Array[Dictionary] = []
		for event in world.recent_events:
			if String(event.get("kind", "")) != "hit":
				continue
			if int(event.get("target_id", -1)) == target.id:
				primary_hits.append(event)
			elif cleave != null and int(event.get("target_id", -1)) == cleave.id:
				cleave_hits.append(event)
		var expected_primary: Array = expected.get("target_calls", [])
		check.call(
			primary_hits.size() == expected_primary.size(),
			(
				"basic attack hit edge matches source: %s/%s"
				% [boss_type, String(entry.get("label", ""))]
			)
		)
		if not primary_hits.is_empty():
			check.call(
				int(primary_hits[0].get("source_id", -1)) == boss.id,
				"basic attack preserves boss source ID: %s" % boss_type
			)
		check.call(
			cleave_hits.size() == expected_cleave.size(),
			(
				"basic attack cleave edge matches source: %s/%s"
				% [boss_type, String(entry.get("label", ""))]
			)
		)
		if not cleave_hits.is_empty():
			check.call(
				int(cleave_hits[0].get("source_id", -2)) == -1,
				"source-omitted cleave stays unattributed: %s" % boss_type
			)
		check.call(
			(
				boss.basic_attack_seq == int(expected.get("basic_attack_seq", -1))
				and boss.timer == int(expected.get("timer", -1))
			),
			(
				"basic attack sequence and cooldown match source: %s/%s"
				% [boss_type, String(entry.get("label", ""))]
			)
		)
	check.call(boss_counts.size() == 216, "basic attack source oracle covers all 216 boss types")
	for boss_type in boss_counts:
		check.call(
			int(boss_counts[boss_type]) == 4,
			"basic attack source oracle has exactly four cases for %s" % String(boss_type)
		)


func _basic_attack_reactive_reflect(check: Callable) -> void:
	var world := _world()
	world.units.clear()
	world.recent_events.clear()
	var boss: BossState = world._spawn_boss("gornak")
	check.call(boss != null, "boss attacker registers for reactive hit effects")
	if boss == null:
		return
	boss.team = world.RED
	boss.position = Vector2(700.0, 300.0)
	boss.entrance_timer = 0
	var thorne := world.spawn_hero(THORNE, world.BLUE, boss.position + Vector2(10.0, 0.0))
	check.call(thorne != null, "Thorne defender spawns for boss hit interaction")
	if thorne == null:
		return
	thorne.bristleback_timer = 120
	var hero_hp := thorne.hp
	var boss_hp := boss.hp
	world._boss_basic_attack(thorne, [thorne])
	check.call(thorne.hp < hero_hp, "boss basic hit damages the reactive defender")
	check.call(boss.hp < boss_hp, "boss basic hit preserves attacker for Bristleback reflect")
	var credited_primary := false
	var reflected_to_boss := false
	for event in world.recent_events:
		if String(event.get("kind", "")) != "hit":
			continue
		if int(event.get("target_id", -1)) == thorne.id:
			credited_primary = int(event.get("source_id", -1)) == boss.id
		if int(event.get("target_id", -1)) == boss.id:
			reflected_to_boss = true
	check.call(credited_primary, "boss primary attack event names its live source ID")
	check.call(reflected_to_boss, "Thorne reflect returns through active boss damage path")


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


func _ranged_ai_dispatch_match_step(check: Callable) -> void:
	var outside_world := _world()
	var outside_boss := outside_world._spawn_boss("ancient_apparition")
	check.call(outside_boss != null, "ranged AI gate boss spawns for outside-range case")
	if outside_boss == null:
		return
	var outside_target := _blue_hero_only(outside_world)
	check.call(outside_target != null, "ranged AI gate isolates a live blue hero")
	if outside_target == null:
		return
	_prime_ancient_dispatch_case(outside_boss, outside_target, 151.0)
	outside_world._step_active_boss()
	check.call(
		outside_boss.target_id == outside_target.id,
		"out-of-range ranged boss still selects its target"
	)
	check.call(
		outside_boss.w_timer == 0 and outside_boss.active_skill != "w",
		"out-of-range ranged boss does not dispatch its smart AI"
	)

	var inside_world := _world()
	var inside_boss := inside_world._spawn_boss("ancient_apparition")
	check.call(inside_boss != null, "ranged AI gate boss spawns for inclusive-edge case")
	if inside_boss == null:
		return
	var inside_target := _blue_hero_only(inside_world)
	check.call(inside_target != null, "ranged AI gate has a live target at attack edge")
	if inside_target == null:
		return
	_prime_ancient_dispatch_case(inside_boss, inside_target, inside_boss.attack_range)
	inside_world._step_active_boss()
	check.call(
		inside_boss.active_skill == "w" and inside_boss.w_timer > 0,
		"inclusive attack-range edge still dispatches ranged smart AI"
	)


func _prime_ancient_dispatch_case(boss: BossState, target: HeroState, distance: float) -> void:
	boss.entrance_timer = 0
	boss.position = Vector2(400, 300)
	boss.previous_position = boss.position
	boss.speed_px_per_tick = 3.0
	boss.attack_range = 150.0
	boss.timer = 999
	boss.ability_timer = 999
	boss.ability2_timer = 999
	boss.q_timer = 999
	boss.w_timer = 0
	boss.e_timer = 999
	boss.r_timer = 999
	boss.active_skill_timer = 0
	boss.kite_mode = "hold"
	target.position = boss.position + Vector2(distance, 0)


func _blue_hero_only(world: Prototype) -> HeroState:
	var target: HeroState = null
	for unit in world.units:
		if unit.team == world.BLUE and unit is HeroState:
			target = unit as HeroState
			break
	if target == null:
		return null
	for unit in world.units:
		if unit.team == world.BLUE and unit != target:
			unit.alive = false
	for structure in world.structures:
		if structure.team == world.BLUE:
			structure.alive = false
	for nexus in world.nexuses:
		if nexus != null and nexus.team == world.BLUE:
			nexus.alive = false
	return target


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
