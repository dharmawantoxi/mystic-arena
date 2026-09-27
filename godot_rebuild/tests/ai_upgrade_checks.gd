extends RefCounted
## Real native domain upgrades versus source AIPlayer + entity method results.

const World = preload("res://scripts/match/prototype_battle.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const Upgrades = preload("res://scripts/match/ai_upgrades.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const FIXTURE := "res://tests/fixtures/ai_upgrade_source.json"


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	for row in fixture.towers:
		_test_tower(row, check)
	for row in fixture.nexuses:
		_test_nexus(row, check)
	for row in fixture.heroes:
		_test_hero(row, check)
	_guards(check)
	_live_reserve(check)


func _world() -> World:
	var world := World.new()
	world.defender_enabled = false
	world.setup_arena()
	world.economy.credit_kill(1, 1000000)
	return world


func _draft(reserved: int) -> Draft:
	var draft := Draft.new()
	draft.purchase_target = "kaizen" if reserved > 0 else ""
	draft.purchase_target_cost = reserved
	return draft


func _fund(world: World, gold: int) -> void:
	# Isolate the action from fixture setup expenses; establish a valid opening ledger.
	world.economy = Economy.new()
	world.economy.gold[1] = gold
	world.economy.opening[1] = gold


func _ledger(world: World, draft: Draft, row: Dictionary, count: int, check: Callable) -> void:
	check.call(world.economy.gold[1] == int(row.expected.gold), "AI upgrade exact red debit")
	check.call(world.economy.gold[0] == 1000, "AI upgrade leaves blue wallet untouched")
	check.call(world.economy.is_balanced(), "AI real match upgrade ledger invariant")
	check.call(draft.reserve() == int(row.expected.reserve), "AI upgrade does not consume reserve")
	check.call(count == int(row.expected.count), "AI upgrade success counter source parity")


func _test_tower(row: Dictionary, check: Callable) -> void:
	var world := _world()
	world.build_tower(1, 9)
	var tower := world.get_unit(world.slots[9].structure_id) as World.StructureState
	for previous in range(1, int(row.level)):
		world._upgrade_tower_for(1, tower.id, previous, row.path)
	tower.hp = 1
	tower.shield = 0
	tower.cooldown_ticks = 17
	tower.no_damage_ticks = 9
	_fund(world, int(row.gold))
	var draft := _draft(int(row.reserved))
	var upgrades := Upgrades.new()
	check.call(
		upgrades.try_tower(world, draft, tower.id) == row.expected.success, "AI tower result"
	)
	_ledger(world, draft, row, upgrades.total_upgraded, check)
	var expected: Dictionary = row.expected.state
	for pair in [
		["level", "level"], ["tower_path", "tower_type"], ["max_hp", "max_hp"], ["damage", "damage"]
	]:
		check.call(tower.settings().get(pair[0]) == expected[pair[1]], "AI tower stat " + pair[0])
	for pair in [
		["hp", "hp"],
		["shield", "shield"],
		["shield_max", "shield_max"],
		["cooldown_ticks", "timer"],
		["no_damage_ticks", "no_damage_timer"]
	]:
		check.call(tower.get(pair[0]) == expected[pair[1]], "AI tower state " + pair[0])


func _test_nexus(row: Dictionary, check: Callable) -> void:
	var world := _world()
	var nexus := world.nexuses[1]
	for previous in range(1, int(row.level)):
		world._upgrade_nexus_for(1, nexus.id, previous)
	nexus.hp = 1
	nexus.cooldown_ticks = 17
	nexus.no_damage_ticks = 9
	nexus.castle_shield_purchased = row.paid
	if row.paid:
		nexus.shield_max = nexus.settings().shield_capacity
	nexus.shield = int(nexus.shield_max * 0.3)
	_fund(world, int(row.gold))
	var draft := _draft(int(row.reserved))
	var upgrades := Upgrades.new()
	check.call(
		upgrades.try_nexus(world, draft, nexus.id) == row.expected.success, "AI nexus result"
	)
	_ledger(world, draft, row, upgrades.total_nexus_upgrades, check)
	var expected: Dictionary = row.expected.state
	for key in ["level", "max_hp", "damage"]:
		check.call(nexus.settings().get(key) == expected[key], "AI nexus stat " + key)
	for pair in [
		["hp", "hp"],
		["shield", "shield"],
		["shield_max", "shield_max"],
		["cooldown_ticks", "timer"],
		["no_damage_ticks", "shield_no_damage_timer"]
	]:
		check.call(nexus.get(pair[0]) == expected[pair[1]], "AI nexus state " + pair[0])


func _test_hero(row: Dictionary, check: Callable) -> void:
	var world := _world()
	var hero := world.units[1] as World.HeroState
	for previous in range(1, int(row.level)):
		world.upgrade_hero(hero.id)
	hero.hp = 1 if row.alive else 0
	hero.alive = row.alive
	hero.skill_timer = 29
	hero.respawn_timer = 77
	_fund(world, int(row.gold))
	var draft := _draft(int(row.reserved))
	var upgrades := Upgrades.new()
	check.call(upgrades.try_hero(world, draft, hero.id) == row.expected.success, "AI hero result")
	_ledger(world, draft, row, upgrades.total_hero_upgrades, check)
	for key in row.expected.state:
		check.call(hero.get(key) == row.expected.state[key], "AI hero stat/state " + key)
	check.call(hero.respawn_timer == 77, "AI dead hero upgrade does not advance respawn")


func _guards(check: Callable) -> void:
	var world := _world()
	world.build_tower(1, 9)
	world.build_tower(0, 0)
	var red := world.get_unit(world.slots[9].structure_id) as World.StructureState
	var blue := world.get_unit(world.slots[0].structure_id) as World.StructureState
	var hero := world.units[1] as World.HeroState
	var draft := _draft(400)
	var upgrades := Upgrades.new()
	var before := world.economy.gold.duplicate()
	check.call(not world.upgrade_tower(red.id, 1), "UI cannot upgrade red tower")
	check.call(not world.upgrade_nexus(world.nexuses[1].id, 1), "UI cannot upgrade red nexus")
	check.call(not world._upgrade_blue_hero(hero.id, 1), "UI cannot upgrade red hero")
	check.call(not upgrades.try_tower(world, draft, blue.id), "AI cannot upgrade blue tower")
	check.call(
		not upgrades.try_nexus(world, draft, world.nexuses[0].id), "AI cannot upgrade blue nexus"
	)
	check.call(
		not upgrades.try_hero(world, draft, world.units[0].id), "AI cannot upgrade blue hero"
	)
	for team in [-1, 2]:
		check.call(
			not world._upgrade_tower_for(team, red.id, 1, "cannon"), "Invalid team tower refused"
		)
		check.call(
			not world._upgrade_nexus_for(team, world.nexuses[1].id, 1), "Invalid team nexus refused"
		)
		check.call(not world._upgrade_hero_for(team, hero.id, 1), "Invalid team hero refused")
	for invalid_id in [-1, world.nexuses[1].id, hero.id]:
		check.call(
			not upgrades.try_tower(world, draft, invalid_id), "AI invalid tower identity refused"
		)
	check.call(not upgrades.try_nexus(world, draft, red.id), "AI tower is not nexus")
	check.call(not upgrades.try_hero(world, draft, red.id), "AI tower is not hero")
	check.call(not world._upgrade_tower_for(1, red.id, 0, "cannon"), "AI stale tower level refused")
	check.call(not world._upgrade_tower_for(1, red.id, 1, "invalid"), "AI invalid path refused")
	check.call(not world._upgrade_nexus_for(1, world.nexuses[1].id, 0), "AI stale nexus refused")
	check.call(not world._upgrade_hero_for(1, hero.id, 0), "AI stale hero refused")
	red.alive = false
	check.call(not upgrades.try_tower(world, draft, red.id), "AI dead tower refused")
	red.alive = true
	world.slots[9].structure_id = -1
	check.call(not upgrades.try_tower(world, draft, red.id), "AI unslotted tower refused")
	world.slots[9].structure_id = red.id
	world.nexuses[1].alive = false
	check.call(not upgrades.try_nexus(world, draft, world.nexuses[1].id), "AI dead nexus refused")
	world.nexuses[1].alive = true
	world.units[0].alive = false
	check.call(not world._upgrade_blue_hero(world.units[0].id, 1), "Blue dead hero gate unchanged")
	world.winner = 0
	check.call(not upgrades.try_tower(world, draft, red.id), "AI finished tower refused")
	check.call(
		not upgrades.try_nexus(world, draft, world.nexuses[1].id), "AI finished nexus refused"
	)
	check.call(not upgrades.try_hero(world, draft, hero.id), "AI finished hero refused")
	check.call(
		world.economy.gold == before and world.economy.is_balanced(),
		"Rejected upgrades never debit"
	)
	check.call(
		red.settings().level == 1 and hero.level == 1, "Rejected upgrades never mutate level"
	)
	check.call(
		upgrades.total_upgraded + upgrades.total_nexus_upgrades + upgrades.total_hero_upgrades == 0,
		"Rejected upgrades never increment counters"
	)


func _live_reserve(check: Callable) -> void:
	var world := _world()
	var hero := world.units[1] as World.HeroState
	_fund(world, 700)
	var draft := _draft(401)
	var upgrades := Upgrades.new()
	check.call(
		not upgrades.try_hero(world, draft, hero.id), "AI reads current reserve: one gold short"
	)
	draft.purchase_target_cost = 400
	check.call(
		upgrades.try_hero(world, draft, hero.id), "AI reads changed reserve: exact threshold"
	)
	check.call(world.economy.gold[1] == 400, "AI reserved gold remains intact")
	check.call(
		not world._upgrade_hero_for(1, hero.id, 1, 0), "Expected level prevents stale double debit"
	)
	draft.purchase_target = ""
	check.call(
		not upgrades.try_hero(world, draft, hero.id),
		"AI cannot afford next upgrade without reserve"
	)
	world.economy.credit_kill(1, 100)
	check.call(upgrades.try_hero(world, draft, hero.id), "AI cleared draft releases reserve")
	check.call(
		world.economy.gold[1] == 0 and world.economy.is_balanced(),
		"AI no extra gold or double debit"
	)
	check.call(Upgrades.new().total_hero_upgrades == 0, "New AI adapter resets upgrade counters")
