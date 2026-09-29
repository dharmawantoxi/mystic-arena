extends RefCounted

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossMatchState = preload("res://scripts/match/boss_match_state.gd")


func run(check: Callable) -> void:
	var fixture = (
		JSON
		. parse_string(FileAccess.get_file_as_string("res://tests/fixtures/match_source.json"))
		. boss_conditions
	)
	_source_policy(check, fixture)
	_queue_and_trigger(check, fixture)
	_reward_and_unlock(check, fixture)
	_world_wiring(check)


func _source_policy(check: Callable, fixture: Dictionary) -> void:
	for sample in fixture.schedules:
		var entries: Array = sample.entries
		var low := 20 if sample.difficulty == "easy" else 11
		var high := 40 if sample.difficulty == "easy" else 30
		check.call(entries.size() == 3, "source schedules every configured mini boss")
		(
			check
			. call(
				(
					entries[0][1] == "gornak"
					and entries[1][1] == "morgath"
					and entries[2][1] == "drakar"
				),
				"source schedule preserves configured boss order",
			)
		)
		var waves: Array[int] = []
		for entry in entries:
			waves.append(int(entry[0]))
		(
			check
			. call(
				waves[0] >= low and waves[-1] <= high,
				"source schedule waves stay in the difficulty range",
			)
		)
		check.call(waves[0] < waves[1] and waves[1] < waves[2], "source schedule waves are unique")


func _queue_and_trigger(check: Callable, fixture: Dictionary) -> void:
	var state := BossMatchState.new()
	state.schedule = {11: "gornak", 12: "morgath"}
	state.queue_wave(11)
	state.queue_wave(12)
	check.call(state.pop_pending(true).is_empty(), "living boss preserves pending queue")
	check.call(
		state.pending.size() == int(fixture.pending.blocked), "source pending queue remains blocked"
	)
	check.call(
		state.pop_pending(false) == fixture.pending.first[0],
		"oldest pending mini boss spawns first"
	)
	for index in range(6):
		state.note_red_tower_destroyed()
	(
		check
		. call(
			state.true_boss_ready(false, "abaddon") == bool(fixture.true_spawn[0]),
			"six destroyed red towers trigger the source true boss condition",
		)
	)
	state.note_spawned_true_boss()
	check.call(not state.true_boss_ready(false, "abaddon"), "true boss only spawns once")


func _reward_and_unlock(check: Callable, fixture: Dictionary) -> void:
	var state := BossMatchState.new()
	state.purchased_heroes = ["gornak"]
	for boss_type in ["gornak", "morgath", "morgath", "drakar"]:
		state.note_boss_defeated(boss_type)
	var config := {
		"meta_gold_reward_win": int(fixture.rewards.win),
		"meta_gold_reward_replay": int(fixture.rewards.replay),
	}
	check.call(state.grant_meta_reward(true, 1, config, false) == 3000, "first victory reward")
	(
		check
		. call(
			state.heroes_unlocked_this_match == fixture.newly_purchased,
			"victory purchases each defeated unowned boss hero for free",
		)
	)
	check.call(state.purchased_heroes == fixture.purchased, "source purchased boss list order")
	check.call(state.grant_meta_reward(true, 1, config, false) == 3000, "reward is idempotent")
	var replay := BossMatchState.new()
	replay.completed_levels = [1]
	check.call(replay.grant_meta_reward(true, 1, config, true) == 1500, "first replay reward")
	var repeated := BossMatchState.new()
	repeated.completed_levels = [1]
	repeated.replay_reward_counts = {"1": 1}
	check.call(repeated.grant_meta_reward(true, 1, config, true) == 200, "repeat replay reward")
	var loss := BossMatchState.new()
	check.call(loss.grant_meta_reward(false, 1, config, false) == 0, "loss reward")


func _world_wiring(check: Callable) -> void:
	var world := Prototype.new()
	check.call(world.setup_arena(), "boss match world setup")
	world.boss_match.schedule = {1: "gornak"}
	world.boss_match.queue_wave(1)
	check.call(world._try_spawn_pending_mini_boss(), "pending mini boss enters the match")
	check.call(
		world.active_boss != null and world.active_boss.boss_type == "gornak", "mini boss identity"
	)
	var reward := world.active_boss.gold_reward
	world.active_boss.alive = false
	world.active_boss.defeated = true
	world._process_defeated_boss()
	(
		check
		. call(
			(
				world.active_boss == null
				and world.economy.earned[0] == reward
				and world.boss_match.defeated_this_match == ["gornak"]
			),
			"boss defeat credits reward and records unlock candidate",
		)
	)
	world.boss_match.red_towers_destroyed = 6
	check.call(world._try_spawn_true_boss(), "true boss enters after six red towers")
	(
		check
		. call(
			world.active_boss.boss_type == "abaddon" and world.boss_match.true_boss_spawned,
			"configured true boss owns the active slot",
		)
	)
