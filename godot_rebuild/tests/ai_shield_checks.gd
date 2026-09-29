extends RefCounted
## Paid shield transactions and real native regen/damage against original Python.

const World = preload("res://scripts/match/prototype_battle.gd")
const State = preload("res://scripts/combat/structure_state.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const Shields = preload("res://scripts/match/ai_shields.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const FIXTURE := "res://tests/fixtures/ai_shield_source.json"


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(
		State.REGEN_SHIELD_COST == int(fixture.constants.TOWER_REGEN_SHIELD_COST),
		"Tower shield price"
	)
	check.call(
		State.CASTLE_SHIELD_COST == int(fixture.constants.CASTLE_SHIELD_COST), "Castle shield price"
	)
	check.call(
		State.REGEN_SHIELD_MIN_LEVEL == int(fixture.constants.TOWER_REGEN_SHIELD_MIN_LEVEL),
		"Regen shield level gate"
	)
	for row in fixture.towers:
		_transaction(row, false, check)
	for row in fixture.castles:
		_transaction(row, true, check)
	for row in fixture.traces:
		_trace(row, check)
	for row in fixture.refunds:
		_refund(row, check)
	for row in fixture.castle_upgrades:
		_castle_upgrade(row, check)
	_guards(check)
	_isolation(check)


func _world() -> World:
	var world := World.new()
	world.setup_arena()
	world.economy.credit_kill(0, 1000000)
	world.economy.credit_kill(1, 1000000)
	return world


func _tower(world: World, path: String, level: int, team: int = 1, slot: int = 9) -> State:
	world.build_tower(team, slot)
	var tower := world.get_unit(world.slots[slot].structure_id) as State
	for previous in range(1, level):
		world._upgrade_tower_for(team, tower.id, previous, path)
	return tower


func _castle(world: World, level: int) -> State:
	var castle := world.nexuses[1]
	for previous in range(1, level):
		world._upgrade_nexus_for(1, castle.id, previous)
	return castle


func _draft(reserve: int) -> Draft:
	var draft := Draft.new()
	draft.purchase_target = "kaizen" if reserve > 0 else ""
	draft.purchase_target_cost = reserve
	return draft


func _state(target: State, expected: Dictionary, check: Callable, label: String) -> void:
	for key in expected:
		var actual: Variant = target.settings().level if key == "level" else target.get(key)
		if key in ["shield", "hp", "shield_max"]:
			check.call(is_equal_approx(float(actual), float(expected[key])), label + " " + key)
		else:
			check.call(actual == expected[key], label + " " + key)


func _transaction(row: Dictionary, castle: bool, check: Callable) -> void:
	var world := _world()
	var target := (
		_castle(world, int(row.level)) if castle else _tower(world, row.path, int(row.level))
	)
	if castle:
		target.set_wave(int(row.wave))
	else:
		target.shield = 13
	target.hp = 1
	target.no_damage_ticks = 27
	world.economy = Economy.new()
	world.economy.gold[1] = int(row.gold)
	world.economy.opening[1] = int(row.gold)
	var draft := _draft(int(row.reserve))
	var adapter := Shields.new()
	var result := (
		adapter.try_castle(world, draft, target.id)
		if castle
		else adapter.try_regen(world, draft, target.id)
	)
	check.call(result == row.success, "Source shield transaction result")
	var repeat := (
		adapter.try_castle(world, draft, target.id)
		if castle
		else adapter.try_regen(world, draft, target.id)
	)
	check.call(repeat == row.repeat, "Source duplicate shield result")
	check.call(world.economy.gold[1] == int(row.balance), "Source exact shield debit")
	check.call(
		world.economy.gold[0] == 1000 and world.economy.is_balanced(),
		"Shield leaves blue ledger unchanged"
	)
	check.call(draft.reserve() == int(row.reserve), "Shield never spends hero reserve")
	_state(target, row.state, check, "Paid shield transaction")


func _trace(row: Dictionary, check: Callable) -> void:
	var world := _world()
	var castle: bool = row.kind == "castle"
	var target := (
		_castle(world, int(row.setup.level))
		if castle
		else _tower(world, row.setup.path, int(row.setup.level))
	)
	if castle:
		target.set_wave(10 if row.setup.mode == "free" else 11)
		if row.setup.mode == "paid":
			check.call(world._activate_castle_shield_for(1, target.id), "Trace castle purchase")
	elif row.setup.paid:
		check.call(world._activate_regen_shield_for(1, target.id), "Trace tower purchase")
	target.hp = target.definition.max_hp - 2
	if not castle or target.shield_active:
		target.shield = target.shield_max - 5
	target.no_damage_ticks = int(row.delay) - 2
	for step in row.rows:
		if step.operation == "tick":
			for tick in range(int(step.ticks)):
				target.tick_regen()
		else:
			check.call(
				world._deliver_hit(-1, 0, target, int(step.damage), "magic", target.position),
				"Shield trace hit delivered"
			)
		_state(target, step.state, check, "Source shield regen/hit trace " + row.kind)


func _refund(row: Dictionary, check: Callable) -> void:
	var world := _world()
	var tower := _tower(world, row.path, 4, 0, 0)
	check.call(
		world._activate_regen_shield_for(0, tower.id), "Blue shield uses same paid transaction"
	)
	for previous in range(4, int(row.level)):
		tower.hp = 1
		tower.shield = 0
		tower.no_damage_ticks = 17
		check.call(
			world.upgrade_tower(tower.id, previous, row.path), "Paid tower upgrades normally"
		)
	_state(tower, row.state, check, "Source paid tower upgrade")
	check.call(tower.sale_value() == int(row.refund), "Source paid shield sale quote")
	var before := world.economy.gold[0]
	check.call(world.sell_tower(0, tower.id), "Paid tower sale succeeds")
	check.call(world.economy.gold[0] == before + int(row.refund), "Source paid shield refund exact")
	check.call(
		not world.sell_tower(0, tower.id) and world.economy.is_balanced(),
		"Paid shield sale exactly once"
	)
	check.call(not world._activate_regen_shield_for(0, tower.id), "Sold ID cannot buy shield")
	world.build_tower(0, 0)
	var fresh := world.get_unit(world.slots[0].structure_id) as State
	check.call(
		fresh.id != tower.id and not fresh.regen_shield_active,
		"Rebuilt slot has fresh identity and no paid flag"
	)


func _castle_upgrade(row: Dictionary, check: Callable) -> void:
	var world := _world()
	var castle := _castle(world, int(row.level))
	castle.set_wave(11)
	check.call(world._activate_castle_shield_for(1, castle.id), "Castle before upgrade paid")
	castle.shield = int(castle.shield_max * 0.3)
	castle.hp = 1
	castle.no_damage_ticks = 17
	check.call(
		world._upgrade_nexus_for(1, castle.id, int(row.level)), "Paid castle upgrade succeeds"
	)
	castle.set_wave(20)
	_state(castle, row.state, check, "Source paid castle upgrade/wave")
	check.call(world.economy.is_balanced(), "Paid castle upgrade ledger")


func _guards(check: Callable) -> void:
	var world := _world()
	var tower := _tower(world, "archer", 4)
	var blue := _tower(world, "archer", 4, 0, 0)
	var castle := world.nexuses[1]
	castle.set_wave(11)
	var draft := _draft(400)
	var adapter := Shields.new()
	var before := world.economy.gold.duplicate()
	for team in [-1, 2]:
		check.call(
			not world._activate_regen_shield_for(team, tower.id), "Invalid shield team refused"
		)
		check.call(
			not world._activate_castle_shield_for(team, castle.id), "Invalid castle team refused"
		)
	check.call(not adapter.try_regen(world, draft, blue.id), "AI refuses blue tower shield")
	check.call(
		not adapter.try_castle(world, draft, world.nexuses[0].id), "AI refuses blue castle shield"
	)
	for wrong in [-1, castle.id, world.units[1].id]:
		check.call(
			not adapter.try_regen(world, draft, wrong), "Wrong tower shield identity refused"
		)
	for wrong in [-1, tower.id, world.units[1].id]:
		check.call(
			not adapter.try_castle(world, draft, wrong), "Wrong castle shield identity refused"
		)
	world.slots[9].structure_id = -1
	check.call(not adapter.try_regen(world, draft, tower.id), "Unslotted shield target refused")
	world.slots[9].structure_id = tower.id
	tower.alive = false
	castle.alive = false
	check.call(not adapter.try_regen(world, draft, tower.id), "Dead tower shield refused")
	check.call(not adapter.try_castle(world, draft, castle.id), "Native dead castle shield guard")
	tower.alive = true
	castle.alive = true
	world.winner = 0
	check.call(not adapter.try_regen(world, draft, tower.id), "Finished tower shield refused")
	check.call(not adapter.try_castle(world, draft, castle.id), "Finished castle shield refused")
	check.call(
		world.economy.gold == before and world.economy.is_balanced(),
		"Shield guard failures never debit"
	)
	check.call(
		not tower.regen_shield_active and not castle.castle_shield_purchased,
		"Shield guard failures never activate"
	)


func _isolation(check: Callable) -> void:
	var world := _world()
	var tower := _tower(world, "archer", 4)
	var other := _tower(world, "archer", 4, 1, 10)
	var definition := tower.definition
	world.economy = Economy.new()
	world.economy.credit_kill(1, 899)
	var draft := _draft(400)
	var adapter := Shields.new()
	check.call(not adapter.try_regen(world, draft, tower.id), "Shield reserve one gold short")
	world.economy.credit_kill(1, 1)
	check.call(adapter.try_regen(world, draft, tower.id), "Shield reserve exact threshold")
	check.call(
		world.economy.gold[1] == 400 and world.economy.is_balanced(),
		"Shield preserves reserved wallet"
	)
	check.call(
		tower.definition == definition and other.definition == definition,
		"Shield leaves shared definition intact"
	)
	check.call(
		not other.regen_shield_active and not tower.settings().shield_regen_enabled,
		"Paid flag is per instance, not fixture mutation"
	)
	tower.shield = 0
	tower.no_damage_ticks = 179
	other.shield = 0
	other.no_damage_ticks = 179
	tower.tick_regen()
	other.tick_regen()
	check.call(tower.shield > 0 and other.shield == 0, "Only paid instance regens")
	tower.alive = false
	var shield := tower.shield
	var timer := tower.no_damage_ticks
	tower.tick_regen()
	check.call(
		tower.shield == shield and tower.no_damage_ticks == timer, "Dead paid tower does not regen"
	)
