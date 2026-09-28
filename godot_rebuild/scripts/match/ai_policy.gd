extends RefCounted
## Source AIPlayer scheduling and short-circuit priority policy.
## Not connected to the playable scene until all action adapters are implemented.

const THINK_INTERVAL := 90
const MAX_HEROES := 5

var level_number := 1
var level_count := 54
var think_timer := THINK_INTERVAL
# Diagnostics for the controller: priorities attempted in the last think tick.
var last_attempts := 0


func brain() -> float:
	return minf(1.0, (maxi(1, level_number) - 1) / 19.0)


func elite() -> float:
	if level_number <= 20:
		return 0.0
	return minf(1.0, float(level_number - 20) / maxi(1, maxi(21, level_count) - 20))


func interval() -> int:
	return maxi(8, int(THINK_INTERVAL * (1.0 - 0.65 * brain()) - 22 * elite()))


func action_budget() -> int:
	# Python round() is ties-to-even, unlike Godot roundi().
	var value := 2.0 * elite()
	var lower := int(floor(value))
	var fraction := value - lower
	if fraction > 0.5 or (fraction == 0.5 and lower % 2 != 0):
		lower += 1
	return 1 + lower


func reset() -> void:
	# Source Game.reset() builds a fresh AIPlayer: the think clock and the
	# diagnostics of the last scried tick start over.
	think_timer = THINK_INTERVAL
	last_attempts = 0


func advance(control_heroes: Callable, perform_step: Callable) -> int:
	# The source controls heroes every tick, including the initial 90-tick wait.
	control_heroes.call()
	think_timer -= 1
	if think_timer > 0:
		return 0
	think_timer = interval()
	var completed := 0
	var attempts := 0
	for index in range(action_budget()):
		attempts += 1
		if not perform_step.call():
			break
		completed += 1
	last_attempts = attempts
	return completed


func roll(base: float, draw: Callable) -> bool:
	return float(draw.call()) < minf(0.98, base + 0.45 * elite())


func choose_step(state: Dictionary, attempt: Callable, draw: Callable) -> bool:
	# Callbacks deliberately preserve source evaluation order and RNG consumption.
	# state counts living towers, but hero_count includes dead/respawning heroes.
	var intelligence := brain()
	var priorities := [
		["build", state.empty_slots > 0 and state.gold >= 150, 0.4 + 0.45 * intelligence],
		["buy_hero", state.hero_count < MAX_HEROES, 0.45 * (0.55 + 0.9 * intelligence)],
		["upgrade_hero", state.hero_count > 0, 0.4 * (0.7 + 0.6 * intelligence)],
		["buy_item", state.hero_count > 0, 0.35 + 0.4 * intelligence + 0.2 * elite()],
		["upgrade_tower", state.upgradeable_towers > 0, 0.30 + 0.5 * intelligence],
		["regen_shield", state.living_towers > 0, -1.0],
		["castle_shield", true, -1.0],
		["upgrade_nexus", true, 0.35 * (0.7 + 0.6 * intelligence)]
	]
	for priority in priorities:
		if priority[1] and (priority[2] < 0.0 or roll(priority[2], draw)):
			if attempt.call(priority[0]):
				return true
	return false
