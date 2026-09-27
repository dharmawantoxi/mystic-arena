extends RefCounted
## Native candidate ordering versus the real AIPlayer kills-descending sort.
## Uses the live match domain and ledger, not receipts.

const World = preload("res://scripts/match/prototype_battle.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const Upgrades = preload("res://scripts/match/ai_upgrades.gd")
const Shields = preload("res://scripts/match/ai_shields.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const FIXTURE := "res://tests/fixtures/ai_priority_source.json"
const RED_SLOTS := [9, 10, 11, 12]
const HERO_TYPES := ["thorne", "grimjaw", "sylara", "vex"]


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	for row in fixture.towers:
		_test_tower(row, check)
	for row in fixture.shields:
		_test_shield(row, check)
	for row in fixture.heroes:
		_test_hero(row, check)
	_test_attribution(check)


func _world() -> World:
	var world := World.new()
	world.defender_enabled = false
	world.setup_arena()
	return world


func _fund(world: World, gold: int) -> void:
	world.economy = Economy.new()
	world.economy.gold[1] = gold
	world.economy.opening[1] = gold


func _draft(reserved: int) -> Draft:
	var draft := Draft.new()
	draft.purchase_target = "kaizen" if reserved > 0 else ""
	draft.purchase_target_cost = reserved
	return draft


func _towers(world: World, levels: Array, kills: Array) -> Array[int]:
	# Candidates are created in slot order so the tie-break index is the fixture tag.
	var ids: Array[int] = []
	_fund(world, 1000000)
	for index in range(levels.size()):
		world.build_tower(1, RED_SLOTS[index])
		var tower := (
			world.get_unit(world.slots[RED_SLOTS[index]].structure_id) as World.StructureState
		)
		for previous in range(1, int(levels[index])):
			world._upgrade_tower_for(1, tower.id, previous, "archer")
		tower.kills = int(kills[index])
		ids.append(tower.id)
	return ids


func _ints(values: Array) -> Array:
	var out: Array = []
	for value in values:
		out.append(int(value))
	return out


func _tags(ids: Array[int], order: Array[int]) -> Array:
	var tags: Array = []
	for entity_id in order:
		tags.append(ids.find(entity_id))
	return tags


func _test_tower(row: Dictionary, check: Callable) -> void:
	var world := _world()
	var ids := _towers(world, row.levels, row.kills)
	_fund(world, int(row.gold))
	var draft := _draft(int(row.reserved))
	var upgrades := Upgrades.new()
	var order := upgrades.tower_candidates(world)
	check.call(_tags(ids, order) == _ints(row.order), "AI tower candidates kills descending stable")
	check.call(upgrades.try_tower_priority(world, draft) == row.success, "AI tower priority result")
	check.call(world.economy.gold[1] == int(row.balance), "AI tower priority exact debit")
	check.call(world.economy.is_balanced(), "AI tower priority ledger invariant")
	check.call(upgrades.total_upgraded == int(row.count), "AI tower priority counter")
	check.call(draft.reserve() == int(row.reserved), "AI tower priority keeps reserve")
	for index in range(ids.size()):
		var tower := world.get_unit(ids[index]) as World.StructureState
		check.call(
			tower.settings().level == int(row.end_levels[index]), "AI tower priority winner level"
		)
		check.call(
			tower.settings().tower_path == String(row.paths[index]), "AI tower priority path"
		)


func _test_shield(row: Dictionary, check: Callable) -> void:
	var world := _world()
	var ids := _towers(world, row.levels, row.kills)
	_fund(world, 100000)
	var draft := _draft(0)
	var shields := Shields.new()
	var order: Array = []
	# Each purchase removes its tower from the pool, exposing the full order.
	while shields.try_regen_priority(world, draft):
		for entity_id in ids:
			var tower := world.get_unit(entity_id) as World.StructureState
			var tag := ids.find(entity_id)
			if tower.regen_shield_active and not order.has(tag):
				order.append(tag)
	check.call(order == _ints(row.order), "AI regen shield candidates kills descending stable")
	check.call(world.economy.gold[1] == int(row.balance), "AI regen shield priority spend")
	check.call(world.economy.is_balanced(), "AI regen shield priority ledger invariant")


func _heroes(world: World, kills: Array) -> Array[int]:
	var ids: Array[int] = []
	_fund(world, 1000000)
	for index in range(kills.size()):
		var hero_type: String = HERO_TYPES[index]
		var before := world._next_id
		world._buy_ai_hero(
			hero_type, int(World.PLAYABLE_AI_HEROES[hero_type].cost), Vector2(1120, 90)
		)
		var hero := world.get_unit(before) as World.HeroState
		for previous in range(1, 14):
			world._upgrade_hero_for(1, hero.id, previous)
		hero.kills = int(kills[index])
		ids.append(hero.id)
	return ids


func _test_hero(row: Dictionary, check: Callable) -> void:
	var world := _world()
	var ids := _heroes(world, row.kills)
	# The free red Kaizen of setup_arena must not join the level-14 comparison.
	var free_kaizen := 0
	for unit in world.units:
		if unit.is_hero and unit.team == 1 and not ids.has(unit.id):
			free_kaizen = unit.id
			for previous in range(1, 15):
				world._upgrade_hero_for(1, unit.id, previous)
	var parked := world.get_unit(free_kaizen) as World.HeroState
	check.call(parked.level == 15, "Free red Kaizen parked at max level")
	_fund(world, 100000)
	var draft := _draft(0)
	var upgrades := Upgrades.new()
	var order: Array = []
	while upgrades.try_hero_priority(world, draft):
		for entity_id in ids:
			var tag := ids.find(entity_id)
			var hero := world.get_unit(entity_id) as World.HeroState
			if hero.level >= 15 and not order.has(tag):
				order.append(tag)
	check.call(order == _ints(row.order), "AI hero candidates kills descending stable")
	check.call(upgrades.total_hero_upgrades == int(row.count), "AI hero priority counter")
	check.call(world.economy.gold[1] == 100000 - int(row.spent), "AI hero priority spend")
	check.call(world.economy.is_balanced(), "AI hero priority ledger invariant")


func _test_attribution(check: Callable) -> void:
	# Source Game._process_hero_kill: only an enemy hero last hit scores a kill.
	var world := _world()
	var red: World.HeroState = null
	var blue: World.HeroState = null
	for unit in world.units:
		if unit.is_hero and unit.team == 1:
			red = unit as World.HeroState
		elif unit.is_hero and unit.team == 0:
			blue = unit as World.HeroState
	check.call(red.kills == 0 and blue.kills == 0, "Heroes start with zero source kills")
	world._on_hero_death(blue, red.id)
	check.call(red.kills == 1, "Enemy hero last hit credits one source kill")
	check.call(blue.kills == 0, "Victim never gains a kill")
	world._on_hero_death(red, -1)
	check.call(red.kills == 1 and blue.kills == 0, "Tower/minion/burn deaths credit nobody")
	world._on_hero_death(red, red.id)
	check.call(red.kills == 1, "Self kill is not credited")
	var tower_slot: int = RED_SLOTS[0]
	_fund(world, 1000000)
	world.build_tower(1, tower_slot)
	var tower := world.get_unit(world.slots[tower_slot].structure_id) as World.StructureState
	check.call(tower.kills == 0, "Source Tower.kills is never incremented")
