extends RefCounted
## Source timing/queue semantics, restricted to nexus level 1. No simulation or rendering imports.

const INITIAL_DELAY := 300
const WAVE_INTERVAL := 1500
const SPAWN_DELAY := 20
var wave := 0
var remaining_ticks := INITIAL_DELAY
var spawn_timers: Array[int] = [0, 0]
var queues: Array[Array] = [[], []]


static func composition(number: int) -> Array[String]:
	var result: Array[String] = ["goblin", "goblin", "goblin"]
	if number <= 3:
		return result
	if number <= 6:
		result.append("orc")
	elif number <= 9:
		result.append_array(["orc", "undead"])
	elif number <= 12:
		result.append_array(["troll", "dark_rider", "undead"])
	else:
		result.append_array(["troll", "troll", "dark_rider", "dark_rider", "undead"])
	return result


func step_tick(field_clear: bool, capacity: int) -> Dictionary:
	var started := false
	var spawns: Array[Dictionary] = []
	if remaining_ticks > 0:
		remaining_ticks -= 1
	elif pending_count() == 0 and field_clear:
		wave += 1
		started = true
		for lane in range(3):
			for kind in composition(wave):
				for team in range(2):
					queues[team].append({"kind": kind, "team": team, "lane": lane})
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
