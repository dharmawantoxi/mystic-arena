# gdlint:disable=max-returns
extends RefCounted
## Deterministic replay of SaveManager stats and Game reward/combo policy.

const LevelStats = preload("res://scripts/match/level_stats.gd")
const World = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const FIXTURE := "res://tests/fixtures/level_stats_source.json"


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Level-stat source fixture parses")
	if not (parsed is Dictionary):
		return
	var fixture: Dictionary = parsed
	check.call(
		_values_match(LevelStats.empty_stats(), fixture.empty),
		"Native empty per-level stats match SaveManager"
	)
	var state := {}
	for row in fixture.updates:
		var before := state.duplicate(true)
		var result := LevelStats.update_level_stats(
			state, int(row.level), _match_payload(row.match)
		)
		check.call(not result.is_empty(), "Level-stat update accepts source case " + row.name)
		if result.is_empty():
			continue
		check.call(state == before, "Level-stat transaction does not mutate input " + row.name)
		check.call(
			bool(result.is_new_best_score) == bool(row.is_new_best_score),
			"Best-score flag matches source " + row.name
		)
		check.call(
			bool(result.is_new_best_time) == bool(row.is_new_best_time),
			"Best-time flag matches source " + row.name
		)
		check.call(
			_values_match(result.new_stats, row.new_stats),
			"Accumulated stats match source " + row.name
		)
		state = result.state
	check.call(
		_values_match(state.level_stats, fixture.final_level_stats),
		"Two levels retain independent source statistics"
	)
	check.call(
		(
			LevelStats.format_time(0) == fixture.format.zero
			and LevelStats.format_time(65) == fixture.format.sixty_five
			and LevelStats.format_time(3605) == fixture.format.hour
		),
		"Level best-time formatting matches source"
	)
	_check_validation(check)
	_check_reward_runtime(fixture.rewards, check)


func _match_payload(source: Dictionary) -> Dictionary:
	return {
		"won": bool(source.won),
		"score": int(source.score),
		"time_seconds": int(source.time_seconds),
		"kills": int(source.kills),
		"combo": int(source.combo),
		"playtime_seconds": int(source.playtime_seconds),
	}


func _check_validation(check: Callable) -> void:
	var valid := LevelStats.empty_stats()
	check.call(LevelStats.valid_entry(valid), "Complete source stat entry validates")
	var missing := valid.duplicate(true)
	missing.erase("wins")
	check.call(not LevelStats.valid_entry(missing), "Missing source stat field is rejected")
	var fractional := valid.duplicate(true)
	fractional["best_score"] = 1.5
	check.call(not LevelStats.valid_entry(fractional), "Fractional stat metadata is rejected")
	var impossible := valid.duplicate(true)
	impossible["total_attempts"] = 1
	impossible["wins"] = 2
	check.call(not LevelStats.valid_entry(impossible), "Wins cannot exceed attempts")
	check.call(
		not LevelStats.valid_map({"55": valid}), "Stats outside the 54 source levels are rejected"
	)
	check.call(
		LevelStats.update_level_stats({}, 1, {"won": true}).is_empty(),
		"Incomplete match statistic payload is rejected"
	)


func _check_reward_runtime(expected: Dictionary, check: Callable) -> void:
	var world := World.new()
	var trace: Array = expected.trace
	for index in range(3):
		world._on_death(world.BLUE, _minion(world.RED, 8))
		world._step_combo_clock()
		check.call(
			_values_match(_reward_state(world), trace[index]),
			"Minion score/combo source frame %d" % (index + 1)
		)
	world._on_death(world.RED, _minion(world.BLUE, 8))
	world._on_death(world.BLUE, _tower(world.RED))
	world._on_death(world.RED, _tower(world.BLUE))
	world._on_death(world.BLUE, _hero(world.RED))
	world._on_death(world.RED, _hero(world.BLUE))
	world._flush_red_tower_deaths()
	world._step_combo_clock()
	check.call(
		_values_match(_reward_state(world), trace[3]),
		"Tower and fixed hero rewards match the source frame"
	)
	for _tick in range(119):
		world._step_combo_clock()
	check.call(
		_values_match(_reward_state(world), expected.expired),
		"Source two-second combo expiry preserves last combo"
	)
	world._on_death(world.BLUE, _minion(world.RED, 8))
	world._step_combo_clock()
	check.call(
		_values_match(_reward_state(world), expected.after_expiry),
		"First kill after expiry starts a fresh combo without replacing the maximum"
	)
	check.call(world.economy.is_balanced(), "Source reward replay keeps native ledger balanced")


func _minion(team: int, reward: int) -> UnitState:
	var unit := UnitState.new()
	var definition = GOBLIN.duplicate()
	definition.gold_reward = reward
	unit.team = team
	unit.definition = definition
	return unit


func _tower(team: int) -> StructureState:
	var tower := StructureState.new()
	tower.team = team
	tower.definition = ARCHER
	return tower


func _hero(team: int) -> HeroState:
	var hero := HeroState.new()
	hero.team = team
	hero.definition = KAIZEN
	return hero


func _reward_state(world) -> Dictionary:
	return {
		"gold": world.economy.earned[world.BLUE],
		"ai_gold": world.economy.earned[world.RED],
		"score": world.score,
		"total_kills": world.total_kills,
		"max_combo": world.max_combo,
		"combo_count": world.combo_count,
		"combo_timer": world.combo_timer,
		"last_combo": world.last_combo,
		"red_towers_destroyed": world.red_towers_destroyed,
	}


func _values_match(actual: Variant, expected: Variant) -> bool:
	if (actual is int or actual is float) and (expected is int or expected is float):
		return is_equal_approx(float(actual), float(expected))
	if actual is Array and expected is Array:
		if actual.size() != expected.size():
			return false
		for index in range(actual.size()):
			if not _values_match(actual[index], expected[index]):
				return false
		return true
	if actual is Dictionary and expected is Dictionary:
		if actual.size() != expected.size():
			return false
		for key in expected:
			if not actual.has(key) or not _values_match(actual[key], expected[key]):
				return false
		return true
	return actual == expected
