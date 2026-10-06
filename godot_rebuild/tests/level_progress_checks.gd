extends RefCounted
## Domain-only checks: no save or scene payout until an adapter owns idempotency.

const Progress = preload("res://scripts/match/level_progress.gd")
const Catalog = preload("res://scripts/match/level_catalog.gd")
const World = preload("res://scripts/match/prototype_battle.gd")


func run(check: Callable) -> void:
	var initial := {"meta_gold": 10}
	check.call(
		Progress.apply_result(initial, 0, true, false, "normal").is_empty(), "Reject level 0"
	)
	check.call(
		Progress.apply_result(initial, 55, true, false, "normal").is_empty(), "Reject level 55"
	)
	check.call(initial == {"meta_gold": 10}, "Rejected results cannot mutate input")
	var loss: Dictionary = Progress.apply_result(initial, 1, false, false, "normal")
	check.call(loss.reward == 0 and loss.state == initial, "Defeat does not complete or pay")
	var first: Dictionary = Progress.apply_result(initial, 1, true, false, "hard")
	check.call(
		first.reward == 3000 and first.state.meta_gold == 3010, "First clear pays win reward"
	)
	check.call(
		(
			first.state.completed_levels == [1]
			and first.state.last_played_level == 1
			and first.state.run_difficulty == "hard"
		),
		"First clear records completion and run difficulty"
	)
	var replay: Dictionary = Progress.apply_result(first.state, 1, true, false, "easy")
	check.call(replay.reward == 1500, "First replay pays replay reward")
	check.call(replay.state.replay_reward_counts["1"] == 1, "First replay recorded once")
	var repeat: Dictionary = Progress.apply_result(replay.state, 1, true, true, "easy")
	check.call(repeat.reward == 200 and repeat.state.meta_gold == 4710, "Further replay pays 200")
	check.call(repeat.state.completed_levels == [1], "Replays cannot duplicate completions")
	check.call(
		first.state.meta_gold == 3010 and initial.meta_gold == 10, "Transaction is copy-on-write"
	)
	var replay_first: Dictionary = Progress.apply_result(initial, 2, true, true, "normal")
	check.call(
		replay_first.reward == 1500 and replay_first.state.completed_levels == [2],
		"Explicit replay before completion uses replay reward and completes level"
	)
	# All 54 levels use their own catalog values, not a hard-coded reward.
	for number in range(1, Catalog.COUNT + 1):
		var config := Catalog.get_level_config(number)
		var award: Dictionary = Progress.apply_result({}, number, true, false, "normal")
		check.call(
			int(award.reward) == int(config.meta_gold_reward_win),
			"Level %d first-clear reward" % number
		)
		var replay_award: Dictionary = Progress.apply_result(
			award.state, number, true, false, "normal"
		)
		check.call(
			int(replay_award.reward) == int(config.meta_gold_reward_replay),
			"Level %d replay reward" % number
		)
	var completed: Array = []
	for number in range(1, Catalog.COUNT + 1):
		completed.append(number)
	var almost: Array = completed.duplicate()
	almost.erase(54)
	var before := {"completed_levels": almost, "run_difficulty": "hard"}
	var final_clear: Dictionary = Progress.apply_result(before, 54, true, false, "easy")
	check.call(final_clear.state.run_difficulty == null, "Completing all 54 unlocks difficulty")
	check.call(before.run_difficulty == "hard", "Difficulty unlock does not mutate input")
	var world := World.new()
	check.call(world.claim_level_result(initial).is_empty(), "Unfinished match cannot pay")
	world.winner = 0
	var claim: Dictionary = world.claim_level_result(initial)
	check.call(claim.reward == 3000, "Blue victory pays once at result boundary")
	check.call(world.claim_level_result(initial).is_empty(), "Repeated result cannot pay twice")
	var defeat := World.new()
	defeat.winner = 1
	var no_reward: Dictionary = defeat.claim_level_result(initial)
	check.call(no_reward.reward == 0, "Red victory has no player reward")
	check.call(defeat.claim_level_result(initial).is_empty(), "Defeat result also claims once")
