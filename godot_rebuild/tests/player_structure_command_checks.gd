extends RefCounted
## Source-backed player structure transaction parity at the native domain boundary.

const World = preload("res://scripts/match/prototype_battle.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const Structure = preload("res://scripts/combat/structure_state.gd")
const FIXTURE := "res://tests/fixtures/player_structure_command_source.json"


func run(check: Callable) -> void:
	var fixture: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary, "Player structure source fixture loads")
	if not fixture is Dictionary:
		return
	_constants(fixture.constants, check)
	_routes(fixture.routes, check)
	for row: Dictionary in fixture.builds:
		_build_case(row, check)
	for row: Dictionary in fixture.regen:
		_regen_case(row, check)
	for row: Dictionary in fixture.castle:
		_castle_case(row, check)
	_extra_guards(check)


func _constants(source: Dictionary, check: Callable) -> void:
	check.call(source.build_cost == Economy.BUILD_COST, "Player build cost matches source")
	check.call(
		source.regen_cost == Structure.REGEN_SHIELD_COST, "Player Regen Shield cost matches source"
	)
	check.call(
		source.regen_min_level == Structure.REGEN_SHIELD_MIN_LEVEL,
		"Player Regen Shield level gate matches source"
	)
	check.call(
		source.castle_cost == Structure.CASTLE_SHIELD_COST,
		"Player Castle Shield cost matches source"
	)
	check.call(source.castle_free_waves == 10, "Player Castle Shield free-wave gate matches source")


func _routes(routes: Array, check: Callable) -> void:
	var buttons: Array[String] = []
	var calls: Array[String] = []
	for row: Dictionary in routes:
		buttons.append(String(row.button))
		check.call(row.handled, String(row.button) + ": source click is handled")
		var receipt: Array = row.calls
		check.call(receipt.size() == 1, String(row.button) + ": source click dispatches once")
		if not receipt.is_empty():
			calls.append(String(receipt[0][0]))
	(
		check
		. call(
			(
				buttons
				== [
					"build_archer",
					"build_cannon",
					"build_ice",
					"build_mage",
					"popup_regen_shield",
					"popup_castle_shield",
				]
			),
			"Source exposes four build and two paid-shield controls"
		)
	)
	check.call(
		calls == ["build", "build", "build", "build", "regen_shield", "castle_shield"],
		"Source controls route to exact structure actions"
	)


func _build_case(row: Dictionary, check: Callable) -> void:
	var spec: Dictionary = row.input
	var world := _world()
	var slot = world.get_slot(0)
	var receipt: Variant = row.receipt
	if receipt is Dictionary:
		slot.position = Vector2(receipt.position[0], receipt.position[1])
		slot.lane = 0
	_set_gold(world, int(spec.gold))
	var accepted := world.build_tower(world.BLUE, slot.id, String(spec.path))
	var tower = world.get_unit(slot.structure_id) as Structure
	check.call(
		accepted == (receipt is Dictionary), row.label + ": native acceptance matches source"
	)
	check.call(world.economy.gold[world.BLUE] == int(row.gold), row.label + ": exact source debit")
	check.call((slot.structure_id != -1) == bool(row.taken), row.label + ": slot claim parity")
	check.call(world.economy.is_balanced(), row.label + ": build ledger remains balanced")
	if not receipt is Dictionary:
		check.call(tower == null, row.label + ": failed build spawns nothing")
		return
	var expected: Dictionary = receipt
	check.call(tower != null, row.label + ": successful build spawns one tower")
	if tower == null:
		return
	var data = tower.settings()
	check.call(data.tower_path == expected.path, row.label + ": exact source path identity")
	check.call(
		data.display_name.begins_with(expected.name), row.label + ": source tower name retained"
	)
	check.call(data.level == expected.level, row.label + ": source Lv1 identity")
	check.call(tower.team == world.BLUE and data.structure_kind == "tower", row.label + ": owner")
	check.call(
		tower.position == Vector2(expected.position[0], expected.position[1]),
		row.label + ": slot position"
	)
	check.call(tower.lane == 0, row.label + ": source top-lane mapping")
	check.call(data.max_hp == expected.max_hp and tower.hp == expected.hp, row.label + ": HP stats")
	check.call(
		tower.shield_max == expected.shield_max and tower.shield == expected.shield,
		row.label + ": initial shield stats"
	)
	check.call(
		(
			data.damage == expected.damage
			and data.attack_range_px == expected.range
			and data.attack_cooldown_ticks == expected.cooldown
		),
		row.label + ": attack stats"
	)
	check.call(
		(
			data.armor == expected.armor
			and data.splash_radius_px == expected.splash
			and data.slow_amount == expected.slow
			and data.chain_count == expected.chain
		),
		row.label + ": Lv1 Archer fallback stats"
	)


func _regen_case(row: Dictionary, check: Callable) -> void:
	var spec: Dictionary = row.input
	var world := _world()
	var team := world.BLUE if spec.team == "blue" else world.RED
	var slot_id := 0 if team == world.BLUE else 9
	world.economy.credit_kill(team, 5000)
	check.call(world.build_tower(team, slot_id), row.label + ": tower fixture builds")
	var tower = world.get_unit(world.get_slot(slot_id).structure_id) as Structure
	while tower.settings().level < int(spec.level):
		var level: int = tower.settings().level
		var upgraded := (
			world.upgrade_tower(tower.id, level, "archer")
			if team == world.BLUE
			else world._upgrade_tower_for(team, tower.id, level, "archer")
		)
		check.call(upgraded, row.label + ": tower fixture reaches source level")
	tower.alive = bool(spec.alive)
	tower.shield = 1
	_set_gold(world, int(spec.gold))
	var states: Array = row.states
	for index in range(states.size()):
		world.activate_player_regen_shield(tower.id)
		var expected: Dictionary = states[index]
		check.call(
			world.economy.gold[world.BLUE] == int(expected.gold),
			row.label + ": Regen press %d exact source balance" % (index + 1)
		)
		check.call(
			tower.regen_shield_active == bool(expected.active),
			row.label + ": Regen press %d activation parity" % (index + 1)
		)
		check.call(
			tower.shield == expected.shield and tower.shield_max == expected.shield_max,
			row.label + ": Regen press %d shield fill parity" % (index + 1)
		)
		if team == world.BLUE:
			check.call(
				tower.sale_value() == int(expected.refund),
				row.label + ": Regen press %d refund parity" % (index + 1)
			)
	check.call(world.economy.is_balanced(), row.label + ": Regen ledger remains balanced")


func _castle_case(row: Dictionary, check: Callable) -> void:
	var spec: Dictionary = row.input
	var world := _world()
	var castle = world.nexuses[world.BLUE] as Structure
	castle.set_wave(int(spec.wave))
	castle.shield = 1
	_set_gold(world, int(spec.gold))
	var states: Array = row.states
	for index in range(states.size()):
		world.activate_player_castle_shield(castle.id)
		var expected: Dictionary = states[index]
		check.call(
			world.economy.gold[world.BLUE] == int(expected.gold),
			row.label + ": Castle press %d exact source balance" % (index + 1)
		)
		check.call(
			(
				castle.castle_shield_purchased == bool(expected.purchased)
				and castle.free_shield_active == bool(expected.free)
				and castle.shield_active == bool(expected.active)
			),
			row.label + ": Castle press %d state parity" % (index + 1)
		)
		check.call(
			castle.shield == expected.shield and castle.shield_max == expected.shield_max,
			row.label + ": Castle press %d shield fill parity" % (index + 1)
		)
	check.call(world.economy.is_balanced(), row.label + ": Castle ledger remains balanced")


func _extra_guards(check: Callable) -> void:
	var world := _world()
	var before: int = world.economy.gold[world.BLUE]
	check.call(
		not world.build_tower(world.BLUE, 0, "invalid"), "Player invalid tower type is rejected"
	)
	check.call(world.transaction_error == "path", "Invalid player tower type reports path")
	check.call(world.economy.gold[world.BLUE] == before, "Invalid tower type cannot debit")
	check.call(
		not world.activate_player_regen_shield(world.nexuses[world.BLUE].id),
		"Player Regen command rejects nexus target"
	)
	check.call(world.transaction_error == "owner", "Wrong Regen target reports ownership")
	check.call(
		not world.activate_player_castle_shield(world.nexuses[world.RED].id),
		"Player Castle command rejects enemy nexus"
	)
	check.call(world.transaction_error == "owner", "Enemy Castle target reports ownership")


func _world() -> World:
	var world := World.new()
	world.setup_arena()
	world.set_ai_enabled(false)
	return world


func _set_gold(world: World, amount: int) -> void:
	world.economy = Economy.new()
	world.economy.gold[world.BLUE] = amount
	world.economy.opening[world.BLUE] = amount
