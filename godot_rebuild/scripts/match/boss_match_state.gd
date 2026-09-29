extends RefCounted
## Layer 8b: source match-level boss schedule, queue, rewards and unlock ledger.
## Boss combat behavior and presentation intentionally belong to later layers.

const EASY_LOW := 20
const EASY_HIGH := 40
const NORMAL_LOW := 11
const NORMAL_HIGH := 30
const TRUE_BOSS_TOWER_KILLS := 6
const REPEAT_REWARD := 200

var pending: Array[Dictionary] = []
var schedule: Dictionary = {}
var red_towers_destroyed := 0
var true_boss_spawned := false
var defeated_this_run := 0
var defeated_this_match: Array[String] = []
var unlocked_bosses: Array[String] = []
var heroes_unlocked_this_match: Array[String] = []
var purchased_heroes: Array[String] = []
var completed_levels: Array[int] = []
var replay_reward_counts: Dictionary = {}
var meta_gold := 0
var meta_reward_earned := 0
var reward_granted := false
var rng := RandomNumberGenerator.new()


func roll_schedule(configured: Dictionary, difficulty: String) -> Dictionary:
	var bosses: Array = configured.values()
	if bosses.is_empty():
		schedule = {}
		return schedule
	var low := EASY_LOW if difficulty == "easy" else NORMAL_LOW
	var high := EASY_HIGH if difficulty == "easy" else NORMAL_HIGH
	if high - low + 1 < bosses.size():
		high = low + bosses.size() * 5
	var candidates: Array[int] = []
	for wave in range(low, high + 1):
		candidates.append(wave)
	# Equivalent policy to random.sample: unique waves without replacement.
	for index in range(candidates.size() - 1, 0, -1):
		var swap_index := rng.randi_range(0, index)
		var held := candidates[index]
		candidates[index] = candidates[swap_index]
		candidates[swap_index] = held
	candidates.resize(bosses.size())
	candidates.sort()
	schedule = {}
	for index in range(bosses.size()):
		schedule[candidates[index]] = String(bosses[index])
	return schedule


func queue_wave(wave: int) -> void:
	if schedule.has(wave):
		pending.append({"wave": wave, "boss_type": String(schedule[wave])})


func pop_pending(active_alive: bool) -> String:
	if active_alive or pending.is_empty():
		return ""
	return String(pending.pop_front().boss_type)


func note_red_tower_destroyed() -> void:
	red_towers_destroyed += 1


func true_boss_ready(has_active_boss: bool, true_boss_type: String) -> bool:
	return (
		not true_boss_spawned
		and red_towers_destroyed >= TRUE_BOSS_TOWER_KILLS
		and not has_active_boss
		and not true_boss_type.is_empty()
	)


func note_spawned_true_boss() -> void:
	true_boss_spawned = true


func note_boss_defeated(boss_type: String) -> void:
	defeated_this_run += 1
	if boss_type not in defeated_this_match:
		defeated_this_match.append(boss_type)
	if boss_type not in unlocked_bosses:
		unlocked_bosses.append(boss_type)


func unlock_defeated_boss_heroes() -> Array[String]:
	var newly: Array[String] = []
	for boss_type in defeated_this_match:
		if boss_type not in unlocked_bosses:
			unlocked_bosses.append(boss_type)
		if boss_type in purchased_heroes:
			continue
		purchased_heroes.append(boss_type)
		newly.append(boss_type)
	heroes_unlocked_this_match = newly
	return newly


func grant_meta_reward(victory: bool, level_number: int, config: Dictionary, replay: bool) -> int:
	if reward_granted:
		return meta_reward_earned
	reward_granted = true
	var reward := 0
	if victory:
		var first_win := not replay and level_number not in completed_levels
		if first_win:
			reward = int(config.get("meta_gold_reward_win", 3000))
		else:
			var key := str(level_number)
			var count := int(replay_reward_counts.get(key, 0))
			reward = (
				int(config.get("meta_gold_reward_replay", 1500))
				if count == 0
				else int(config.get("meta_gold_reward_replay_repeat", REPEAT_REWARD))
			)
			replay_reward_counts[key] = count + 1
		unlock_defeated_boss_heroes()
		if level_number not in completed_levels:
			completed_levels.append(level_number)
	meta_reward_earned = reward
	meta_gold += reward
	return reward
