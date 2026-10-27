extends RefCounted
## Slice 9bq13: user-authorized R-only recipe for Urgharun. The Python source has no Urgharun AI
## recipe, so this is an explicit native extension rather than a claim of gameplay parity. It reuses
## Gravefang's already-source-backed R trigger/area/timer shape and Urgharun's existing R data;
## damage and cooldown values themselves are unchanged.

const BossAI = preload("res://scripts/match/boss_ai.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const FIXTURE := "res://tests/fixtures/urgharun_ai_skill_source.json"
const BOSS_AI_PATH := "res://scripts/match/boss_ai.gd"
const BOSS := "urgharun"
const CAST_DURATION := 100
const RADIUS := 180.0
const CROWD_THRESHOLD := 3
const HP_THRESHOLD := 0.35


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Urgharun R-AI source fixture parses")
	if not (data is Dictionary):
		return
	_check_source_contract(check, data)
	_check_native_wiring(check)
	_check_no_trigger(check)
	_check_crowd_cast(check)
	_check_low_hp_cast(check)
	_check_cooldown_gate(check)


func _check_source_contract(check: Callable, data: Dictionary) -> void:
	var stats: Dictionary = data["urgharun_r"]
	var reference: Dictionary = data["reference"]
	(
		check
		. call(
			String(data["subject"]) == BOSS and not bool(data["python_recipe_exists"]),
			"The fixture records that the source lacks an Urgharun recipe; 9bq13 is an authorized extension"
		)
	)
	check.call(
		(
			int(stats["damage"]) == 2275
			and int(stats["cooldown"]) == 1020
			and String(stats["boss_class"]) == "mini"
		),
		"The R recipe uses Urgharun's existing normalized damage and cooldown data"
	)
	var radii: Array = reference["r_radii_found"]
	var radius_matches := radii.size() == 1 and int(radii[0]) == int(RADIUS)
	check.call(
		(
			String(reference["boss"]) == "gravefang"
			and bool(reference["crowd_shape_found"])
			and bool(reference["low_hp_shape_found"])
			and int(reference["crowd_threshold"]) == CROWD_THRESHOLD
			and is_equal_approx(float(reference["low_hp_ratio"]), HP_THRESHOLD)
		),
		"The crowd and low-HP triggers come from the source-backed Gravefang R"
	)
	check.call(radius_matches, "The source-backed R radius is 180 px")
	check.call(
		int(reference["active_skill_timer"]) == CAST_DURATION,
		"The source-backed R cast window is 100 ticks"
	)


func _check_native_wiring(check: Callable) -> void:
	var text := FileAccess.get_file_as_string(BOSS_AI_PATH)
	check.call(
		(
			text.contains(
				'"urgharun":\n\t\t\t_urgharun(world, boss, enemies, target, target_distance)'
			)
			and text.contains("static func _urgharun(")
		),
		"BossAI dispatches Urgharun into its dedicated R recipe"
	)
	check.call(
		(
			text.contains("boss.r_timer = boss.skill_r_cooldown")
			and text.contains('_set_skill(boss, "r", 100)')
			and text.contains("_skill_damage(boss, boss.skill_r_damage)")
		),
		"The recipe consumes the catalog cooldown/damage and activates the R presentation key"
	)


func _new_world() -> Prototype:
	var world := Prototype.new()
	world.setup_arena()
	return world


func _new_boss(world, hp_ratio: float = 1.0) -> BossState:
	var boss := BossState.new()
	if not boss.setup(BOSS, PackedVector2Array(), world.boss_table):
		return null
	boss.alive = true
	boss.entrance_timer = 0
	boss.position = Vector2(640, 360)
	boss.hp = float(boss.max_hp) * hp_ratio
	return boss


func _spawn_enemy(world, position: Vector2) -> UnitState:
	var enemy: UnitState = world.spawn_unit(GOBLIN, 0, 1)
	if enemy != null:
		enemy.position = position
		enemy.hp = 1000000.0
	return enemy


func _check_no_trigger(check: Callable) -> void:
	var world := _new_world()
	var boss := _new_boss(world)
	var target := _spawn_enemy(world, boss.position + Vector2(60, 0))
	var enemies: Array[UnitState] = [target]
	BossAI.tick(world, boss, enemies, target, 60.0)
	check.call(
		boss.active_skill == "" and boss.r_timer == 0,
		"One nearby target at full HP does not spend the ultimate"
	)
	check.call(
		boss.ability_timer == boss.ability_cooldown,
		"The previous generic ability still runs when the new R recipe does not cast"
	)


func _check_crowd_cast(check: Callable) -> void:
	var world := _new_world()
	var boss := _new_boss(world)
	var first := _spawn_enemy(world, boss.position + Vector2(60, 0))
	var second := _spawn_enemy(world, boss.position + Vector2(120, 0))
	var third := _spawn_enemy(world, boss.position + Vector2(-180, 0))
	var outside := _spawn_enemy(world, boss.position + Vector2(181, 0))
	var enemies: Array[UnitState] = [first, second, third, outside]
	var outside_hp := outside.hp
	BossAI.tick(world, boss, enemies, first, 60.0)
	check.call(
		boss.active_skill == "r" and boss.active_skill_timer == CAST_DURATION,
		"Three enemies in the 180 px crowd trigger start the R presentation"
	)
	check.call(
		(
			boss.r_timer == boss.skill_r_cooldown
			and boss.skill_r_cooldown == 1020
			and boss.skill_r_damage == 2275
		),
		"The R timer/damage use Urgharun's unchanged catalog values"
	)
	check.call(
		(
			first.hp < 1000000.0
			and second.hp < 1000000.0
			and third.hp < 1000000.0
			and outside.hp == outside_hp
		),
		"R damages every target in its 180 px area and leaves the outside target untouched"
	)


func _check_low_hp_cast(check: Callable) -> void:
	var world := _new_world()
	var boss := _new_boss(world, 0.34)
	var target := _spawn_enemy(world, boss.position + Vector2(80, 0))
	var enemies: Array[UnitState] = [target]
	BossAI.tick(world, boss, enemies, target, 80.0)
	check.call(
		boss.active_skill == "r" and boss.r_timer == boss.skill_r_cooldown,
		"Below 35 percent HP, a single target is enough to trigger R"
	)


func _check_cooldown_gate(check: Callable) -> void:
	var world := _new_world()
	var boss := _new_boss(world)
	boss.r_timer = 2
	var first := _spawn_enemy(world, boss.position + Vector2(40, 0))
	var second := _spawn_enemy(world, boss.position + Vector2(80, 0))
	var third := _spawn_enemy(world, boss.position + Vector2(120, 0))
	var enemies: Array[UnitState] = [first, second, third]
	BossAI.tick(world, boss, enemies, first, 40.0)
	check.call(
		boss.active_skill == "" and boss.r_timer == 1,
		"The R cooldown gate blocks a cast until its source-shaped timer reaches zero"
	)
