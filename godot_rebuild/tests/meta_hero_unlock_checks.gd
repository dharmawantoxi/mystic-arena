extends RefCounted
## Source-backed permanent Hero Shop catalog and transaction checks.

const Store = preload("res://scripts/match/hero_unlock_store.gd")
const HERO_ROSTER = preload("res://scripts/data/hero_roster.gd").DEFINITIONS
const FIXTURE := "res://tests/fixtures/meta_hero_unlock_source.json"


func run(check: Callable) -> void:
	var fixture: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary, "Meta Hero Shop source fixture loads")
	if not (fixture is Dictionary):
		return
	check.call(Store.is_catalog_valid(), "Meta Hero Shop boss catalog loads")
	var policy: Dictionary = fixture.policy
	check.call(
		int(policy.starter_cost) == Store.STARTER_UNLOCK_COST,
		"Meta Hero Shop starter price matches source"
	)
	check.call(
		int(policy.mini_boss_cost) == Store.MINI_BOSS_UNLOCK_COST,
		"Meta Hero Shop mini-boss price matches source"
	)
	check.call(
		int(policy.true_boss_cost) == Store.TRUE_BOSS_UNLOCK_COST,
		"Meta Hero Shop true-boss price matches source"
	)
	check.call(
		String(policy.starter_auto_grant) == Store.DEFAULT_HERO,
		"Meta Hero Shop auto-granted starter matches source"
	)
	_catalog(check)
	for row in fixture.cases:
		_source_case(row, check)
	var invalid := {"meta_gold": -1, "purchased_heroes": [], "unlocked_bosses": []}
	var invalid_before := invalid.duplicate(true)
	var refused := Store.try_unlock(invalid, "thorne")
	check.call(refused.error == "profile", "Invalid permanent profile is rejected")
	check.call(invalid == invalid_before, "Rejected permanent profile is never mutated")


func _catalog(check: Callable) -> void:
	var starters: Array[String] = Store.ids_for_tab("starter")
	var mini: Array[String] = Store.ids_for_tab("mini")
	var true_bosses: Array[String] = Store.ids_for_tab("true")
	check.call(starters == Store.STARTERS, "Meta Hero Shop preserves source starter order")
	check.call(
		mini.size() + true_bosses.size() == HERO_ROSTER.size() - starters.size(),
		"Every native boss kit appears in exactly one meta shop tab"
	)
	var seen := {}
	for hero_type in starters + mini + true_bosses:
		check.call(not seen.has(hero_type), "Meta Hero Shop catalog ID is unique: " + hero_type)
		seen[hero_type] = true
		var item: Dictionary = Store.entry(hero_type)
		check.call(not item.is_empty(), "Meta Hero Shop entry resolves: " + hero_type)
		if hero_type in starters:
			check.call(
				not item.is_boss_hero and item.unlock_cost == 0,
				"Starter unlock is free: " + hero_type
			)
		else:
			check.call(
				(
					item.is_boss_hero
					and item.unlock_require_boss == hero_type
					and item.unlock_cost == 4500
				),
				"Boss unlock requires its defeat and 4500 Hero Gold: " + hero_type
			)
	check.call(seen.size() == HERO_ROSTER.size(), "Meta Hero Shop covers the native roster")
	check.call(Store.entry("missing").is_empty(), "Unknown meta hero has no substitute entry")


func _source_case(row: Dictionary, check: Callable) -> void:
	var spec: Dictionary = row.input
	var state := {
		"meta_gold": int(spec.gold),
		"completed_levels": [],
		"replay_reward_counts": {},
		"purchased_heroes": _strings(spec.purchased),
		"unlocked_bosses": _strings(spec.defeated),
	}
	var before := state.duplicate(true)
	var result: Dictionary = Store.try_unlock(state, String(spec.hero))
	var accepted := int(row.save_count) == 1
	check.call(
		String(result.error).is_empty() == accepted,
		row.label + ": native acceptance matches source save boundary"
	)
	check.call(int(result.state.meta_gold) == int(row.gold), row.label + ": exact Hero Gold debit")
	check.call(
		result.state.purchased_heroes == _strings(row.purchased),
		row.label + ": permanent ownership matches source"
	)
	check.call(
		result.state.unlocked_bosses == _strings(row.defeated),
		row.label + ": boss defeat gate remains unchanged"
	)
	check.call(state == before, row.label + ": pure transaction never mutates caller state")
	var expected_error := String(
		(
			{
				"unknown": "hero",
				"duplicate_starter": "owned",
				"locked_mini_boss": "locked",
				"mini_boss_one_short": "gold",
			}
			. get(String(row.label), "")
		)
	)
	check.call(result.error == expected_error, row.label + ": explicit refusal reason")


func _strings(values: Array) -> Array[String]:
	var result: Array[String] = []
	for value in values:
		result.append(String(value))
	return result
