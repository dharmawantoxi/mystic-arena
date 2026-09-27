extends RefCounted
## Differential tests against executed Python policy, not a simulated AI economy.

const Policy = preload("res://scripts/match/ai_policy.gd")
const FIXTURE := "res://tests/fixtures/ai_policy_source.json"

var controls := 0
var attempts := 0
var draws := 0
var step_success := false
var successful_action := ""
var random_value := 0.0
var visited: Array[String] = []


func run(check: Callable) -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	for row in data.schedules:
		var policy := Policy.new()
		policy.level_number = int(row.level)
		policy.level_count = int(row.level_count)
		controls = 0
		attempts = 0
		step_success = row.succeeds
		var recorded: Array = []
		for tick in range(1, 201):
			var before := attempts
			var completed := policy.advance(_control, _step)
			check.call(completed == (attempts - before if step_success else 0), "AI action count")
			if attempts != before:
				recorded.append([tick, attempts - before, policy.think_timer])
		check.call(controls == int(row.controls), "AI controls heroes each tick")
		check.call(is_equal_approx(policy.brain(), row.brain), "AI brain source parity")
		check.call(is_equal_approx(policy.elite(), row.elite), "AI elite source parity")
		check.call(recorded.size() == row.ticks.size(), "AI think count source parity")
		for index in range(mini(recorded.size(), row.ticks.size())):
			for column in range(3):
				check.call(
					recorded[index][column] == int(row.ticks[index][column]), "AI tick parity"
				)
	for row in data.priorities:
		var policy := Policy.new()
		policy.level_number = int(row.level)
		successful_action = row.success
		random_value = row.draw
		visited.clear()
		draws = 0
		var outcome := policy.choose_step(row, _attempt, _draw)
		check.call(outcome == row.outcome, "AI priority result")
		check.call(draws == int(row.draws), "AI RNG consumption")
		check.call(visited.size() == row.visited.size(), "AI attempted action count")
		for index in range(mini(visited.size(), row.visited.size())):
			check.call(visited[index] == row.visited[index], "AI short-circuit action order")


func _control() -> void:
	controls += 1


func _step() -> bool:
	attempts += 1
	return step_success


func _attempt(action: String) -> bool:
	visited.append(action)
	return action == successful_action


func _draw() -> float:
	draws += 1
	return random_value
