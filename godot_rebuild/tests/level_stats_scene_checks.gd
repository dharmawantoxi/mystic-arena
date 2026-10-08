extends RefCounted
## Playable match -> atomic slot -> retry -> menu statistics lifecycle.

const Slots = preload("res://scripts/match/save_slot_store.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const TEST_TEMPLATE := "user://level_stats_scene_%d.json"


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	_cleanup()
	app.slot_path_template = TEST_TEMPLATE
	app.active_slot = 1
	var menu = app.current_screen
	check.call(menu.configure_slot_paths(TEST_TEMPLATE, 1), "Stats scene accepts isolated slot")
	var initial := {
		"meta_gold": 0,
		"completed_levels": [],
		"replay_reward_counts": {},
		"last_played_level": 1,
		"purchased_heroes": ["kaizen"],
		"unlocked_bosses": [],
		"run_difficulty": "normal",
		"level_stats": {},
	}
	check.call(
		Slots.save_state(initial, 1, 1_700_001_000.0, TEST_TEMPLATE),
		"Stats scene seeds an isolated profile"
	)
	menu.refresh_levels()
	check.call(
		menu.get_node("%LevelStatsLabel").text == "NO STATS YET",
		"Unplayed selected level exposes the source empty state"
	)

	menu.get_node("%PrototypeButton").pressed.emit()
	await _settle(tree)
	var screen = app.current_screen
	var world = screen.simulation.world
	for index in range(3):
		check.call(_kill_red_minion(world), "Playable score records minion %d" % (index + 1))
		world._step_combo_clock()
	world.match_time_override_seconds = 125
	world.winner = world.BLUE
	screen._save_result()
	var first := Slots.load_state(1, TEST_TEMPLATE)
	var first_stats: Dictionary = first.level_stats["1"]
	check.call(
		(
			first_stats.best_score == 24
			and first_stats.best_time_seconds == 125
			and first_stats.total_attempts == 1
			and first_stats.wins == 1
			and first_stats.total_kills == 3
			and first_stats.max_combo == 2
			and first_stats.total_playtime_seconds == 125
		),
		"Victory atomically persists the source score, time, kills and combo"
	)
	check.call(
		(
			screen.get_node("%Hint").text.contains("Score: 24")
			and screen.get_node("%Hint").text.contains("+3000 Meta Gold")
		),
		"Playable result exposes source score and permanent reward"
	)

	screen.get_node("%RestartButton").pressed.emit()
	await _settle(tree)
	screen = app.current_screen
	world = screen.simulation.world
	check.call(_kill_red_minion(world), "Retry records its independent minion kill")
	world._step_combo_clock()
	world.match_time_override_seconds = 60
	world.winner = world.RED
	screen._save_result()
	var second := Slots.load_state(1, TEST_TEMPLATE)
	var second_stats: Dictionary = second.level_stats["1"]
	check.call(
		(
			second_stats.best_score == 24
			and second_stats.best_time_seconds == 125
			and second_stats.total_attempts == 2
			and second_stats.wins == 1
			and second_stats.total_kills == 4
			and second_stats.max_combo == 2
			and second_stats.total_playtime_seconds == 185
		),
		"Defeat retry accumulates totals without replacing victory bests"
	)

	screen.get_node("%BackButton").pressed.emit()
	await _settle(tree)
	menu = app.current_screen
	var summary := String(menu.get_node("%LevelStatsLabel").text)
	check.call(
		(
			summary.contains("BEST 24")
			and summary.contains("TIME 2:05")
			and summary.contains("1W/2")
			and summary.contains("50%")
		),
		"Reloaded menu exposes selected-level bests, attempts and win rate"
	)
	app.slot_path_template = Slots.PATH_TEMPLATE
	check.call(menu.configure_slot_paths(Slots.PATH_TEMPLATE, 1), "Restore production slot paths")
	_cleanup()
	await _settle(tree)
	check.call(
		tree.get_node_count() == baseline, "Level-stat scene lifecycle leaves no orphan nodes"
	)


func _kill_red_minion(world) -> bool:
	if world.player_hero_ids.is_empty():
		return false
	var hero = world.get_unit(world.player_hero_ids[0])
	var target = world.spawn_unit(GOBLIN, world.RED, 1)
	if hero == null or target == null:
		return false
	target.position = hero.position
	target.hp = 1.0
	hero.cooldown_ticks = 0
	return world.apply_hit(hero.id, target.id)


func _cleanup() -> void:
	for slot in range(1, Slots.SLOT_COUNT + 1):
		Slots.delete_slot(slot, TEST_TEMPLATE)


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
