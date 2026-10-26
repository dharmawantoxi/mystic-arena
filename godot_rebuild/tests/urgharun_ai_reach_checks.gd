extends RefCounted
## Layer 9bq12: pins the reachability of Urgharun's skill FX. `bosses/level40.py` paints the Q/W/E/R
## layers only while `active_skill` names that key, and the source sets that field exclusively
## inside `Boss._smart_ai_*` recipes. `urgharun` is in neither list, so the boss owns skill stats
## but never casts: the rebuild must stay equally quiet instead of inventing a recipe.
##
## The fixture comes from `urgharun_ai_reach_source_oracle.py` (AST harvest of the chain, of the
## `active_skill` writers and of `bosses/boss_data.py`), and the native half runs the real
## `boss_ai.gd` for 900 ticks against a live boss.

const BossAI = preload("res://scripts/match/boss_ai.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const FIXTURE := "res://tests/fixtures/urgharun_ai_reach_source.json"
const BOSS_AI_PATH := "res://scripts/match/boss_ai.gd"
const BOSS := "urgharun"
const TICKS := 900


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Urgharun AI reach fixture parses")
	if not (data is Dictionary):
		return
	_check_source(check, data)
	_check_native_text(check)
	_check_no_cast(check, data)


func _check_source(check: Callable, data: Dictionary) -> void:
	check.call(
		(
			String(data["subject"]) == BOSS
			and int(data["dispatch_count"]) == 79
			and int(data["smart_ai_method_count"]) == 79
		),
		"`Boss.update` dispatches 79 boss types, one `_smart_ai_*` recipe each"
	)
	check.call(
		not bool(data["dispatch_has_subject"]) and not bool(data["smart_ai_has_subject"]),
		"`urgharun` is neither in the dispatch chain nor the owner of a recipe"
	)
	check.call(
		(data["subject_writers"] as Array).is_empty() and int(data["subject_reset_count"]) == 2,
		"No source function writes `active_skill` for urgharun; only the 2 generic resets exist"
	)
	var keys: Array = data["active_skill_keys"]
	check.call(
		keys.has("q") and keys.has("w") and keys.has("e") and keys.has("r"),
		"The recipes that do exist cast q/w/e/r, which is what the FX layers read"
	)
	var stats: Dictionary = data["stats"]
	check.call(
		(
			String(stats["boss_class"]) == "mini"
			and int(stats["skill_count"]) == 8
			and int(stats["skill_q_cooldown"]) == 425
			and int(stats["skill_r_damage"]) == 2275
		),
		"The boss owns eight skill stats, so the gap is the recipe and not the data"
	)
	var head: Array = data["dispatch_head"]
	var tail: Array = data["dispatch_tail"]
	check.call(
		(
			head.size() == 5
			and tail.size() == 5
			and String(head[0]) == "abaddon"
			and String(tail[4]) == "morthraxis"
		),
		"The chain is pinned from its first arm to its last, so a silent append fails here"
	)


func _check_native_text(check: Callable) -> void:
	var text := FileAccess.get_file_as_string(BOSS_AI_PATH)
	check.call(not text.contains(BOSS), "`boss_ai.gd` carries no urgharun arm")
	check.call(
		text.contains("_:\n\t\t\t_generic(world, boss, enemies)"),
		"A boss without an arm falls through to `_generic`, exactly like the source fallback"
	)
	check.call(
		text.contains("static func _set_skill(") and text.count("_set_skill(boss, ") > 20,
		"The native recipes do cast through `_set_skill`, so the silence is urgharun's alone"
	)


func _check_no_cast(check: Callable, data: Dictionary) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var boss := BossState.new()
	check.call(
		boss.setup(BOSS, PackedVector2Array(), world.boss_table),
		"`urgharun` loads from the boss table"
	)
	var stats: Dictionary = data["stats"]
	check.call(
		(
			int(boss.skill_q_cooldown) == int(stats["skill_q_cooldown"])
			and int(boss.skill_r_damage) == int(stats["skill_r_damage"])
		),
		"The live boss carries the source skill stats"
	)
	boss.alive = true
	boss.entrance_timer = 0
	boss.position = Vector2(700, 380)
	var enemy: UnitState = world.spawn_unit(GOBLIN, 0, 1)
	check.call(enemy != null, "The native match spawns a target for the boss")
	if enemy == null:
		return
	enemy.position = boss.position + Vector2(40, 0)
	enemy.hp = 1000000.0
	enemy.max_hp = 1000000
	var enemies: Array[UnitState] = [enemy]
	var casts := 0
	var generic := false
	for tick in range(TICKS):
		if not enemy.alive:
			enemy.alive = true
		BossAI.tick(world, boss, enemies, enemy, 40.0)
		if boss.active_skill != "" or boss.active_skill_timer != 0:
			casts += 1
		if boss.ability_timer != 0:
			generic = true
	check.call(
		casts == 0, "The native AI never sets `active_skill` for urgharun (%d frames)" % TICKS
	)
	check.call(generic, "The generic ability arm still fires, so the boss is not inert")
	check.call(
		int(boss.skill_q_cooldown) == 425 and int(boss.q_timer) == 0,
		"A zero `q_timer` never turns into a cast, because no recipe consumes it"
	)
