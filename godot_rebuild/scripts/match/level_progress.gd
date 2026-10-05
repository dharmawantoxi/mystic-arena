extends RefCounted
## In-memory transaction for the source Game._grant_meta_reward policy.
## Save I/O, boss hero unlocks, achievements and match wiring are separate.

const Catalog = preload("res://scripts/match/level_catalog.gd")
const REPEAT_REWARD := 200


static func apply_result(
	state: Dictionary, level: int, victory: bool, is_replay: bool, difficulty: String
) -> Dictionary:
	var config := Catalog.get_level_config(level)
	if config.is_empty():
		return {}  # Unknown level: reject without changing the caller's state.
	var updated := state.duplicate(true)
	var completed: Array = updated.get("completed_levels", [])
	var counts: Dictionary = updated.get("replay_reward_counts", {})
	var reward := 0
	if victory:
		var key := str(level)
		if is_replay or level in completed:
			var count := int(counts.get(key, 0))
			reward = int(config.get("meta_gold_reward_replay", 1500)) if count == 0 else int(
				config.get("meta_gold_reward_replay_repeat", REPEAT_REWARD)
			)
			counts[key] = count + 1
		else:
			reward = int(config.get("meta_gold_reward_win", 3000))
		if level not in completed:
			completed.append(level)
		updated["last_played_level"] = level
		if completed.size() >= Catalog.COUNT:
			updated["run_difficulty"] = null
		elif updated.get("run_difficulty") == null:
			updated["run_difficulty"] = difficulty
		updated["completed_levels"] = completed
		updated["replay_reward_counts"] = counts
	updated["meta_gold"] = int(updated.get("meta_gold", 0)) + reward
	return {"state": updated, "reward": reward}
