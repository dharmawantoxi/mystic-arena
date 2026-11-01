class_name WaveDirector
extends RefCounted

## Native port of _core wave scheduling/composition rules.
var schedule: Dictionary = {}
var pending: Array = []
var queue_blue: Array = []
var queue_red: Array = []
var timer_blue := 0
var timer_red := 0


func roll_schedule(
	level_config: Dictionary, difficulty: String, rng: RandomNumberGenerator
) -> Dictionary:
	var src: Dictionary = level_config.get("mini_bosses", {})
	schedule = {}
	pending.clear()
	if src.is_empty():
		return schedule
	var bosses: Array = src.values()
	var low := 20 if difficulty == "easy" else 11
	var high := 40 if difficulty == "easy" else 30
	if high - low + 1 < bosses.size():
		high = low + bosses.size() * 5
	var candidates: Array[int] = []
	for wave in range(low, high + 1):
		candidates.append(wave)
	for i in range(candidates.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp := candidates[i]
		candidates[i] = candidates[j]
		candidates[j] = tmp
	var chosen := candidates.slice(0, bosses.size())
	chosen.sort()
	for index in range(bosses.size()):
		schedule[chosen[index]] = str(bosses[index])
	return schedule


func composition(castle_level: int, wave: int, rules: Dictionary) -> Array[String]:
	var base: Array = rules.get("NEXUS_WAVE_COMPOSITION", {}).get(
		str(clampi(castle_level, 1, 5)), ["goblin"]
	)
	var result: Array[String] = []
	for item: Variant in base:
		result.append(str(item))
	if wave <= 3:
		return result
	if wave <= 6:
		result.append("orc")
		return result
	if wave <= 9:
		result.append("orc")
		result.append("undead")
		return result
	if wave <= 12:
		result.append("troll")
		result.append("dark_rider")
		result.append("undead")
		return result
	result.append("troll")
	result.append("troll")
	result.append("dark_rider")
	result.append("dark_rider")
	result.append("undead")
	return result


func enqueue_wave(
	castle_level_blue: int, castle_level_red: int, wave: int, rules: Dictionary
) -> void:
	var blue := composition(castle_level_blue, wave, rules)
	var red := composition(castle_level_red, wave, rules)
	for lane: String in ["top", "mid", "bot"]:
		for minion: String in blue:
			queue_blue.append({"type": minion, "lane": lane})
		for minion: String in red:
			queue_red.append({"type": minion, "lane": lane})


func queue_mini(wave: int) -> void:
	if schedule.has(wave):
		pending.append({"wave": wave, "type": str(schedule[wave])})


func pop_mini() -> Dictionary:
	if pending.is_empty():
		return {}
	return pending.pop_front()


func pop_spawn(team: String, interval: int) -> Dictionary:
	if team == "blue":
		timer_blue += 1
		if timer_blue >= interval and not queue_blue.is_empty():
			timer_blue = 0
			return queue_blue.pop_front()
	else:
		timer_red += 1
		if timer_red >= interval and not queue_red.is_empty():
			timer_red = 0
			return queue_red.pop_front()
	return {}


static func ai_castle_target(wave: int) -> int:
	if wave >= 13:
		return 5
	if wave >= 10:
		return 4
	if wave >= 7:
		return 3
	if wave >= 4:
		return 2
	return 1
