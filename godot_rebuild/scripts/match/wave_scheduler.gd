extends RefCounted
## Source timing/queue semantics with per-team nexus tiers. No simulation imports.

const INITIAL_DELAY := 300
const WAVE_INTERVAL := 1500
const SPAWN_DELAY := 20
var wave := 0
var remaining_ticks := INITIAL_DELAY
var spawn_timers: Array[int] = [0, 0]
var queues: Array[Array] = [[], []]


static func base_composition(castle_level: int) -> Array[String]:
	match castle_level:
		2:
			return ["goblin", "goblin", "goblin", "orc"]
		3:
			return ["goblin", "orc", "goblin", "orc", "undead"]
		4:
			return ["orc", "goblin", "orc", "undead", "goblin", "goblin"]
		5:
			return ["orc", "orc", "undead", "troll", "goblin", "goblin"]
		_:
			return ["goblin", "goblin", "goblin"]


static func composition(number: int, castle_level: int = 1) -> Array[String]:
	var result := base_composition(castle_level)
	if number <= 3:
		return result
	if number <= 6:
		result.append("orc")
	elif number <= 9:
		result.append_array(["orc", "undead"])
	elif number <= 12:
		result.append_array(["troll", "dark_rider", "undead"])
	else:
		var elites: Array[String] = ["troll", "troll", "dark_rider", "dark_rider", "undead"]
		result.append_array(elites)
	return result


func step_tick(
	field_clear: bool, capacity: int, blue_level: int = 1, red_level: int = 1
) -> Dictionary:
	var started := false
	var spawns: Array[Dictionary] = []
	if remaining_ticks > 0:
		remaining_ticks -= 1
	elif pending_count() == 0 and field_clear:
		wave += 1
		started = true
		var blue_comp := composition(wave, blue_level)
		var red_comp := composition(wave, red_level)
		for lane in range(3):
			for kind in blue_comp:
				queues[0].append({"kind": kind, "team": 0, "lane": lane})
			for kind in red_comp:
				queues[1].append({"kind": kind, "team": 1, "lane": lane})
		remaining_ticks = WAVE_INTERVAL
	# Timers advance even while idle. Wave 1 therefore emits its first pair at tick 301.
	for team in range(2):
		spawn_timers[team] += 1
		if spawn_timers[team] >= SPAWN_DELAY and not queues[team].is_empty() and capacity > 0:
			spawns.append(queues[team].pop_front())
			spawn_timers[team] = 0
			capacity -= 1
	return {"started": started, "spawns": spawns}


func pending_count() -> int:
	return queues[0].size() + queues[1].size()


func cancel() -> void:
	queues[0].clear()
	queues[1].clear()
