extends RefCounted

const World = preload("res://scripts/match/prototype_battle.gd")
const Cannon = preload("res://scripts/match/cannon_upgrades.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/cannon_source.json")
	)
	_path_selection(check, fixture.path_selection)
	for row in fixture.levels:
		_level(check, row)
	_muzzle(check, fixture.muzzle)
	for volley in fixture.volleys:
		_volley(check, volley)
	for case in fixture.splash:
		_splash(check, case)
	_burn(check, fixture.burn)
	_guards(check)


func _path_selection(check: Callable, expected: Dictionary) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	check.call(
		world.upgrade_price(tower.id, "archer") == int(expected.archer_price),
		"source level-1 archer quote"
	)
	check.call(
		world.upgrade_price(tower.id, "cannon") == int(expected.cannon_price),
		"source level-1 cannon quote"
	)
	check.call(
		world.upgrade_price(tower.id) == int(expected.default_price),
		"upgrade keeps archer default path"
	)
	check.call(
		world.upgrade_price(tower.id, "ice") == 0 and world.upgrade_price(tower.id, "mage") == 0,
		"unported paths quote zero"
	)
	var before: int = world.economy.gold[0]
	check.call(
		not world.upgrade_tower(tower.id, 1, "") and world.transaction_error == "path",
		"source rejects missing path choice"
	)
	check.call(
		not world.upgrade_tower(tower.id, 1, "bogus") and world.transaction_error == "path",
		"source rejects unknown path choice"
	)
	check.call(
		tower.settings().level == 1 and tower.settings().tower_path == "archer",
		"rejected path keeps level and type"
	)
	check.call(world.economy.gold[0] == before, "rejected path spends nothing")
	check.call(world.upgrade_tower(tower.id, 1, "cannon"), "cannon path upgrade accepted")
	check.call(
		tower.settings().level == 2 and tower.settings().tower_path == "cannon",
		"cannon path switches type at level 2"
	)
	check.call(
		world.upgrade_price(tower.id) == int(expected.cannon_next_default),
		"source cannon level-3 quote ignores path argument"
	)
	check.call(world.upgrade_tower(tower.id, 2, "archer"), "later upgrade ignores path argument")
	check.call(
		tower.settings().tower_path == "cannon" and tower.settings().level == 3,
		"source keeps cannon path past level 1"
	)
	check.call(world.economy.is_balanced(), "path ledger stays balanced")


func _level(check: Callable, row: Dictionary) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	for previous in range(1, int(row.level)):
		if previous == 1:
			tower.hp = 1
			tower.shield = 0
			world.upgrade_tower(tower.id, previous, "cannon")
		else:
			tower.hp = 1
			tower.shield = 0
			tower.cooldown_ticks = 17
			tower.no_damage_ticks = 9
			var before: int = world.economy.gold[0]
			check.call(
				(
					world.upgrade_price(tower.id) == int(row.price)
					if previous == int(row.level) - 1
					else true
				),
				"source cannon upgrade price"
			)
			check.call(world.upgrade_tower(tower.id, previous), "cannon upgrade accepted")
			if previous == int(row.level) - 1:
				check.call(
					world.economy.gold[0] == before - int(row.price),
					"upgrade debits exact price once"
				)
				check.call(
					not world.upgrade_tower(tower.id, previous),
					"stale expected level rejects duplicate upgrade"
				)
	var data = tower.settings()
	for pair in [
		["max_hp", "max_hp"],
		["damage", "damage"],
		["attack_range_px", "range"],
		["attack_cooldown_ticks", "cooldown"],
		["armor", "armor"],
		["sale_refund", "refund"],
		["splash_radius_px", "splash"],
		["burn_dps", "burn_dps"],
		["burn_duration_ticks", "burn_duration"]
	]:
		check.call(data.get(pair[0]) == row[pair[1]], "source cannon property " + pair[0])
	check.call(
		data.tower_path == "cannon" and data.level == int(row.level) and data.volley_count == 1,
		"cannon path, level and single-shot volley"
	)
	check.call(
		tower.hp == row.hp and tower.shield == row.shield, "source full HP and shield restore"
	)
	check.call(
		(
			tower.cooldown_ticks == int(row.timer)
			and tower.no_damage_ticks == int(row.no_damage_timer)
		),
		"upgrade retains cooldown and regen clock"
	)
	check.call(world.upgrade_price(tower.id) == int(row.next_price), "source next/max level quote")
	check.call(
		data.is_valid() and world.economy.is_balanced(), "upgraded definition and ledger valid"
	)
	var seller := _world()
	var sale_tower = seller.get_unit(seller.slots[0].structure_id)
	for previous in range(1, int(row.level)):
		seller.upgrade_tower(sale_tower.id, previous, "cannon" if previous == 1 else "archer")
	var refund_before: int = seller.economy.gold[0]
	check.call(seller.sell_tower(0, sale_tower.id), "cannon sale succeeds")
	check.call(
		seller.economy.gold[0] == refund_before + int(row.refund),
		"source cannon tier-specific refund"
	)
	check.call(
		not seller.sell_tower(0, sale_tower.id) and seller.economy.is_balanced(),
		"cannon refund is exactly once"
	)
	if int(row.level) == 6:
		check.call(not world.upgrade_tower(tower.id, 6), "level six maximum rejects upgrade")
		check.call(world.transaction_error == "max_level", "maximum reports max_level")


func _muzzle(check: Callable, rows: Array) -> void:
	for row in rows:
		var world := _world()
		var tower = world.spawn_structure(Cannon.LEVELS[int(row.level)], 0, Vector2(500, 340))
		for face in [-1, 1]:
			var aim := Vector2(500 + face * 60, 340)
			var expected = row.faces[str(face)]
			check.call(
				world.muzzle_position(tower, aim) == Vector2(expected[0], expected[1]),
				"source cannon muzzle level %d face %d" % [int(row.level), face]
			)


func _volley(check: Callable, expected: Dictionary) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	for previous in range(1, int(expected.level)):
		world.upgrade_tower(tower.id, previous, "cannon" if previous == 1 else "archer")
	tower.position = Vector2(500, 340)
	var primary = world.spawn_unit(GOBLIN, 1, 0)
	primary.position = Vector2(500 + int(expected.side) * 60, 340)
	check.call(world.fire_projectile(tower.id, primary.id), "cannon launch succeeds")
	check.call(world.projectiles.size() == 1, "cannon fires a single shell")
	var shot = world.projectiles[0]
	var source = expected.shots[0]
	check.call(
		shot.position == Vector2(source.position[0], source.position[1]),
		"source cannon muzzle position"
	)
	check.call(
		shot.target_id == primary.id and shot.damage == int(source.damage),
		"source cannon shell damage and target"
	)
	check.call(
		(
			shot.kind == "cannon"
			and shot.splash_radius == float(source.special.splash)
			and shot.burn_dps == float(source.special.burn_dps)
			and shot.burn_duration == int(source.special.burn_duration)
		),
		"source cannon shell splash and burn payload"
	)
	check.call(
		primary.hp == 45 and tower.cooldown_ticks == tower.definition.attack_cooldown_ticks,
		"cannon shell has no instant damage and sets cooldown once"
	)
	check.call(
		not world.fire_projectile(tower.id, primary.id), "cannon cannot fire twice in one cooldown"
	)


func _splash(check: Callable, case: Dictionary) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	for previous in range(1, int(case.level)):
		world.upgrade_tower(tower.id, previous, "cannon" if previous == 1 else "archer")
	tower.position = Vector2(500, 340)
	tower.cooldown_ticks = 0
	var main = world.spawn_unit(GOBLIN, 1, 0)
	main.hp = 10000
	main.position = Vector2(560, 340)
	var radius := float(case.splash)
	var victims: Array = []
	var edge = world.spawn_unit(GOBLIN, 1, 0)
	edge.hp = 10000
	edge.position = Vector2(560 + radius, 340)
	victims.append(edge)
	var outside = world.spawn_unit(GOBLIN, 1, 0)
	outside.hp = 10000
	outside.position = Vector2(560 + radius + 1.0, 340)
	victims.append(outside)
	var frail = world.spawn_unit(GOBLIN, 1, 0)
	frail.hp = 5
	frail.position = Vector2(570, 340)
	victims.append(frail)
	var ally = world.spawn_unit(GOBLIN, 0, 0)
	ally.position = Vector2(570, 340)
	victims.append(ally)
	var dead = world.spawn_unit(GOBLIN, 1, 0)
	dead.position = Vector2(570, 340)
	dead.alive = false
	victims.append(dead)
	# Source all_units never contains structures: towers take no splash.
	var enemy_tower = world.spawn_structure(world.ARCHER, 1, Vector2(570, 340))
	var tower_hp: float = enemy_tower.hp
	var tower_shield: float = enemy_tower.shield
	check.call(world.fire_projectile(tower.id, main.id), "splash volley launches")
	_fly_to_impact(world, tower)
	var main_call = case.main_calls[0]
	check.call(
		main.hp == 10000 - int(main_call.damage) and main.alive,
		"source cannon direct damage without mitigation"
	)
	check.call(
		(
			main.burn_dps == float(case.main_burn.dps)
			and main.burn_timer == int(case.main_burn.timer)
			and main.burn_team == 0
		),
		"source burns the main target"
	)
	var expectations: Array = case.victims.slice(0, 5)
	for index in range(expectations.size()):
		var victim = victims[index]
		var expected = expectations[index]
		var calls: Array = expected.calls
		if calls.is_empty():
			check.call(victim.burn_timer == 0, "source skips splash victim %d" % int(expected.id))
			continue
		var call = calls[0]
		var unit_max := 10000.0 if index != 2 else 5.0
		check.call(
			(
				victim.hp == maxf(0.0, unit_max - float(call.damage))
				and victim.alive == bool(call.alive_after)
			),
			"source splash damage victim %d" % int(expected.id)
		)
		check.call(
			(
				victim.burn_dps == float(expected.burn.dps)
				and victim.burn_timer == int(expected.burn.timer)
			),
			"source splash burn victim %d" % int(expected.id)
		)
	check.call(
		enemy_tower.hp == tower_hp and enemy_tower.shield == tower_shield,
		"structures take no cannon splash"
	)
	check.call(world.economy.is_balanced(), "splash ledger stays balanced")


func _burn(check: Callable, cases: Array) -> void:
	var stacking = cases[0]
	var world := _world()
	var unit = world.spawn_unit(GOBLIN, 1, 0)
	check.call(world.apply_burn(unit.id, 8, 120, 0), "fresh burn applies")
	check.call(
		(
			unit.burn_dps == float(stacking.first.dps)
			and unit.burn_timer == int(stacking.first.timer)
			and unit.burn_accum == float(stacking.first.accum)
			and unit.burn_tick_cd == int(stacking.first.tick_cd)
			and unit.burn_team == 0
		),
		"source fresh burn state"
	)
	check.call(world.apply_burn(unit.id, 5, 200, 1), "weaker burn refreshes")
	check.call(
		(
			unit.burn_dps == float(stacking.weaker.dps)
			and unit.burn_timer == int(stacking.weaker.timer)
			and unit.burn_team == 1
		),
		"source keeps stronger dps, longest timer, newest team"
	)
	check.call(world.apply_burn(unit.id, 30, 60, 1), "stronger burn raises dps")
	check.call(
		(
			unit.burn_dps == float(stacking.stronger.dps)
			and unit.burn_timer == int(stacking.stronger.timer)
		),
		"source stronger burn wins without shortening timer"
	)
	for burn_case in cases.slice(1, 2):
		_burn_ticks(check, burn_case)
	_falloff_and_death(check)


func _burn_ticks(check: Callable, burn_case: Dictionary) -> void:
	var world := _world()
	var definition = GOBLIN.duplicate()
	definition.max_hp = 10000
	definition.regen_per_tick = 0.0
	var unit = world.spawn_unit(definition, 1, 0)
	unit.position = Vector2(600, 600)
	check.call(
		world.apply_burn(unit.id, float(burn_case.dps), int(burn_case.duration), 0),
		"burn tick case applies"
	)
	var last_hp := 10000.0
	var last_tick := 0
	for event in burn_case.events:
		for _index in range(int(event.tick) - last_tick):
			world.step_tick()
		last_tick = int(event.tick)
		check.call(
			unit.hp == last_hp - float(event.damage),
			"source burn damage at tick %d" % int(event.tick)
		)
		last_hp = unit.hp
	for _index in range(int(burn_case.duration) + 4 - last_tick):
		world.step_tick()
	check.call(
		unit.hp == float(burn_case.hp) and unit.burn_timer == 0 and unit.burn_dps == 0.0,
		"source burn ends cleanly after duration"
	)
	check.call(world.economy.is_balanced() and unit.alive, "burn survivor keeps ledger balanced")


func _falloff_and_death(check: Callable) -> void:
	var world := _world()
	var dying = world.spawn_unit(GOBLIN, 1, 0)
	dying.position = Vector2(600, 600)
	dying.hp = 3
	world.apply_burn(dying.id, 60, 180, 0)
	var kills_before: int = world.kills[0]
	var earned_before: int = world.economy.earned[0]
	for _index in range(60):
		world.step_tick()
	check.call(not dying.alive, "burn damage kills")
	check.call(
		world.kills[0] == kills_before + 1 and world.get_unit(dying.id) == null,
		"burn death credits the victim's enemy exactly once"
	)
	check.call(
		world.economy.earned[0] == earned_before + GOBLIN.gold_reward,
		"burn kill pays the victim reward once"
	)
	check.call(world.economy.is_balanced(), "burn kill keeps ledger balanced")
	var frozen := _world()
	var doomed = frozen.spawn_unit(GOBLIN, 1, 0)
	doomed.position = Vector2(600, 600)
	frozen.apply_burn(doomed.id, 60, 180, 0)
	for _index in range(10):
		frozen.step_tick()
	var held_timer: int = doomed.burn_timer
	var killer = frozen.spawn_unit(GOBLIN, 0, 0)
	killer.position = doomed.position
	killer.cooldown_ticks = 0
	doomed.hp = 1
	check.call(frozen.apply_hit(killer.id, doomed.id), "overkill interrupts burn")
	for _index in range(40):
		frozen.step_tick()
	check.call(
		doomed.burn_timer == held_timer, "dead units never tick burn, like source Minion.update"
	)


func _guards(check: Callable) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	check.call(not world.apply_burn(tower.id, 8, 120, 1), "structures cannot burn")
	var ally = world.spawn_unit(GOBLIN, 0, 0)
	check.call(
		world.apply_burn(ally.id, 8, 120, 0),
		"source burn has no team check; credit stays victim-based"
	)
	var enemy = world.spawn_unit(GOBLIN, 1, 0)
	check.call(
		(
			not world.apply_burn(enemy.id, 0, 120, 0)
			and not world.apply_burn(enemy.id, 8, 0, 0)
			and not world.apply_burn(-1, 8, 120, 0)
		),
		"burn rejects empty payloads and stale IDs"
	)
	check.call(world.defender_enabled == false, "cannon domain tests keep the defender parked")
	var skirmish := _world()
	skirmish.defender_enabled = true
	for _index in range(301):
		skirmish.step_tick()
	var built = skirmish.get_unit(skirmish.slots[11].structure_id)
	check.call(
		built != null and built.settings().tower_path == "archer",
		"scheduled defender still builds archers"
	)
	check.call(skirmish.economy.is_balanced(), "defender ledger stays balanced")


func _fly_to_impact(world: World, tower) -> void:
	for _index in range(60):
		var flying := false
		for shot in world.projectiles:
			if shot.active:
				flying = true
		if not flying:
			return
		world._update_projectiles(tower)


func _world() -> World:
	var world := World.new()
	world.defender_enabled = false
	world.economy.gold[0] = 10000
	world.economy.opening[0] = 10000
	world.setup_arena()
	world.build_tower(0, 0)
	return world
