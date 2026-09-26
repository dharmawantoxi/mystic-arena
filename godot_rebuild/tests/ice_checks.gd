extends RefCounted

const World = preload("res://scripts/match/prototype_battle.gd")
const Ice = preload("res://scripts/match/ice_upgrades.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/ice_source.json")
	)
	_path_selection(check, fixture.path_selection)
	for row in fixture.levels:
		_level(check, row)
	_muzzle(check, fixture.muzzle)
	for volley in fixture.volleys:
		_volley(check, volley)
	for case in fixture.on_hit:
		_on_hit(check, case)
	_slow(check, fixture.slow)
	_guards(check)


func _path_selection(check: Callable, expected: Dictionary) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	check.call(
		world.upgrade_price(tower.id, "ice") == int(expected.ice_price), "source level-1 ice quote"
	)
	check.call(
		not world.upgrade_tower(tower.id, 1, "") and world.transaction_error == "path",
		"source rejects missing path choice"
	)
	check.call(
		not world.upgrade_tower(tower.id, 1, "bogus") and world.transaction_error == "path",
		"source rejects unknown path choice"
	)
	check.call(
		(
			tower.settings().level == int(expected.still_level)
			and tower.settings().tower_path == str(expected.still_type)
		),
		"rejected path keeps level and type"
	)
	check.call(world.upgrade_tower(tower.id, 1, "ice"), "ice path upgrade accepted")
	check.call(
		(
			tower.settings().level == int(expected.ice_level)
			and tower.settings().tower_path == str(expected.ice_type)
		),
		"ice path switches type at level 2"
	)
	check.call(
		world.upgrade_price(tower.id) == int(expected.ice_next_default),
		"source ice level-3 quote ignores path argument"
	)
	check.call(world.upgrade_tower(tower.id, 2, "archer"), "later upgrade ignores path argument")
	check.call(
		(
			tower.settings().tower_path == str(expected.kept_type)
			and tower.settings().level == int(expected.kept_level)
		),
		"source keeps ice path past level 1"
	)
	for previous in range(3, 6):
		world.upgrade_tower(tower.id, previous)
	check.call(
		(
			world.upgrade_price(tower.id) == int(expected.ice_max_price)
			and not world.upgrade_tower(tower.id, 6)
		),
		"source ice level six is maxed with a zero quote"
	)
	check.call(world.economy.is_balanced(), "path ledger stays balanced")


func _level(check: Callable, row: Dictionary) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	for previous in range(1, int(row.level)):
		if previous == 1:
			tower.hp = 1
			tower.shield = 0
			world.upgrade_tower(tower.id, previous, "ice")
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
				"source ice upgrade price"
			)
			check.call(world.upgrade_tower(tower.id, previous), "ice upgrade accepted")
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
		["slow_amount", "slow"],
		["slow_duration_ticks", "slow_duration"],
		["atk_slow_amount", "atk_slow"],
		["slow_aoe_px", "slow_aoe"]
	]:
		check.call(data.get(pair[0]) == row[pair[1]], "source ice property " + pair[0])
	check.call(
		data.tower_path == "ice" and data.level == int(row.level) and data.volley_count == 1,
		"ice path, level and single-shot volley"
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
		seller.upgrade_tower(sale_tower.id, previous, "ice" if previous == 1 else "archer")
	var refund_before: int = seller.economy.gold[0]
	check.call(seller.sell_tower(0, sale_tower.id), "ice sale succeeds")
	check.call(
		seller.economy.gold[0] == refund_before + int(row.refund), "source ice tier-specific refund"
	)
	check.call(
		not seller.sell_tower(0, sale_tower.id) and seller.economy.is_balanced(),
		"ice refund is exactly once"
	)
	if int(row.level) == 6:
		check.call(not world.upgrade_tower(tower.id, 6), "level six maximum rejects upgrade")
		check.call(world.transaction_error == "max_level", "maximum reports max_level")


func _muzzle(check: Callable, rows: Array) -> void:
	for row in rows:
		var world := _world()
		var tower = world.spawn_structure(Ice.LEVELS[int(row.level)], 0, Vector2(500, 340))
		for spec in [
			["E", 60, 0],
			["W", -60, 0],
			["N", 0, -60],
			["S", 0, 60],
			["NE", 60, -60],
			["SE", 60, 60],
			["SW", -60, 60],
			["NW", -60, -60]
		]:
			var aim := Vector2(500 + int(spec[1]), 340 + int(spec[2]))
			var expected = row.aims[str(spec[0])]
			check.call(
				(
					world.muzzle_position(tower, aim)
					== Vector2(expected.position[0], expected.position[1])
				),
				"source ice muzzle level %d aim %s" % [int(row.level), str(spec[0])]
			)


func _volley(check: Callable, expected: Dictionary) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	for previous in range(1, int(expected.level)):
		world.upgrade_tower(tower.id, previous, "ice" if previous == 1 else "archer")
	tower.position = Vector2(500, 340)
	var primary = world.spawn_unit(GOBLIN, 1, 0)
	primary.position = Vector2(500 + int(expected.side) * 60, 340)
	check.call(world.fire_projectile(tower.id, primary.id), "ice launch succeeds")
	check.call(world.projectiles.size() == 1, "ice fires a single shard")
	var shot = world.projectiles[0]
	var source = expected.shots[0]
	check.call(
		shot.position == Vector2(source.position[0], source.position[1]),
		"source ice muzzle position"
	)
	check.call(
		shot.target_id == primary.id and shot.damage == int(source.damage),
		"source ice shard damage and target"
	)
	check.call(
		(
			shot.kind == "ice"
			and shot.slow_amount == float(source.special.slow)
			and shot.slow_duration == int(source.special.slow_duration)
			and shot.atk_slow_amount == float(source.special.get("atk_slow", 0.0))
			and shot.slow_aoe == float(source.special.get("slow_aoe", 0.0))
		),
		"source ice shard slow payload"
	)
	check.call(
		primary.hp == 45 and tower.cooldown_ticks == tower.definition.attack_cooldown_ticks,
		"ice shard has no instant damage and sets cooldown once"
	)
	check.call(
		not world.fire_projectile(tower.id, primary.id), "ice cannot fire twice in one cooldown"
	)


func _on_hit(check: Callable, case: Dictionary) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	for previous in range(1, int(case.level)):
		world.upgrade_tower(tower.id, previous, "ice" if previous == 1 else "archer")
	tower.position = Vector2(500, 340)
	tower.cooldown_ticks = 0
	var main = world.spawn_unit(GOBLIN, 1, 0)
	main.hp = 10000
	main.position = Vector2(560, 340)
	check.call(world.fire_projectile(tower.id, main.id), "ice volley launches")
	_fly_to_impact(world, tower)
	check.call(
		main.hp == 10000 - int(case.damage) and main.alive,
		"source ice direct damage without mitigation"
	)
	check.call(
		(
			main.slow_amount == float(case.main_slow.amount)
			and main.slow_timer == int(case.main_slow.timer)
		),
		"source slows the main target"
	)
	check.call(
		(
			main.atk_slow_amount == float(case.main_atk.amount)
			and main.atk_slow_timer == int(case.main_atk.timer)
		),
		"source attack-slows the main target"
	)
	var victims: Array = case.victims
	if victims.is_empty():
		var near = world.spawn_unit(GOBLIN, 1, 0)
		near.hp = 10000
		near.position = Vector2(570, 340)
		_fly_again(world, tower, main)
		check.call(near.slow_timer == 0 and near.atk_slow_timer == 0, "no ice AOE below level 6")
	else:
		var edge = world.spawn_unit(GOBLIN, 1, 0)
		edge.hp = 10000
		edge.position = Vector2(560 + float(case.slow_aoe), 340)
		var outside = world.spawn_unit(GOBLIN, 1, 0)
		outside.hp = 10000
		outside.position = Vector2(560 + float(case.slow_aoe) + 1.0, 340)
		var ally = world.spawn_unit(GOBLIN, 0, 0)
		ally.position = Vector2(570, 340)
		var dead = world.spawn_unit(GOBLIN, 1, 0)
		dead.position = Vector2(570, 340)
		dead.alive = false
		# Victims spawn after the first impact; fire a second volley at
		# the same main target so the level-6 AOE meets the full lineup.
		_fly_again(world, tower, main)
		var lineup := [edge, outside, ally, dead]
		for index in range(victims.size()):
			var victim = lineup[index]
			var expected = victims[index]
			check.call(
				(
					victim.slow_amount == float(expected.slow.amount)
					and victim.slow_timer == int(expected.slow.timer)
				),
				"source ice AOE slow victim %d" % int(expected.id)
			)
			check.call(
				(
					victim.atk_slow_amount == float(expected.atk.amount)
					and victim.atk_slow_timer == int(expected.atk.timer)
				),
				"source ice AOE attack-slow victim %d" % int(expected.id)
			)
	check.call(world.economy.is_balanced(), "ice impact ledger stays balanced")


func _slow(check: Callable, cases: Array) -> void:
	var stacking = cases[0]
	var world := _world()
	var unit = world.spawn_unit(GOBLIN, 1, 0)
	check.call(world.apply_slow(unit.id, 0.25, 90), "fresh slow applies")
	check.call(
		(
			unit.slow_amount == float(stacking.first.amount)
			and unit.slow_timer == int(stacking.first.timer)
		),
		"source fresh slow state"
	)
	check.call(world.apply_slow(unit.id, 0.10, 10), "weaker shorter slow lands")
	check.call(
		(
			unit.slow_amount == float(stacking.weaker_shorter.amount)
			and unit.slow_timer == int(stacking.weaker_shorter.timer)
		),
		"source ignores weaker shorter slow"
	)
	check.call(world.apply_slow(unit.id, 0.10, 200), "weaker longer slow lands")
	check.call(
		(
			unit.slow_amount == float(stacking.weaker_longer.amount)
			and unit.slow_timer == int(stacking.weaker_longer.timer)
		),
		"source longer duration refreshes even when weaker"
	)
	check.call(world.apply_slow(unit.id, 0.65, 50), "stronger slow lands")
	check.call(
		(
			unit.slow_amount == float(stacking.stronger.amount)
			and unit.slow_timer == int(stacking.stronger.timer)
		),
		"source stronger slow wins"
	)
	_slow_ticks(check, cases[1])
	_slow_speed(check, cases[2])
	_attack_cd(check, cases[3])


func _slow_ticks(check: Callable, ticks_case: Dictionary) -> void:
	var world := _world()
	var unit = world.spawn_unit(GOBLIN, 1, 0)
	unit.position = Vector2(600, 600)
	check.call(world.apply_slow(unit.id, 0.5, 3), "tick slow applies")
	check.call(world.apply_atk_slow(unit.id, 0.4, 2), "tick attack-slow applies")
	for event in ticks_case.ticks:
		world.step_tick()
		check.call(
			(
				unit.slow_amount == float(event.slow_amount)
				and unit.slow_timer == int(event.slow_timer)
				and unit.atk_slow_amount == float(event.atk_amount)
				and unit.atk_slow_timer == int(event.atk_timer)
			),
			"source slow state after tick"
		)


func _slow_speed(check: Callable, speed_case: Dictionary) -> void:
	for row in speed_case.rows:
		var world := _world()
		var unit = world.spawn_unit(GOBLIN, 1, 0)
		if int(row.timer) > 0:
			world.apply_slow(unit.id, float(row.amount), int(row.timer))
		check.call(
			world._eff_speed(unit) == float(row.eff),
			"source effective speed at slow %s" % str(row.amount)
		)


func _attack_cd(check: Callable, cd_case: Dictionary) -> void:
	var slow22 = GOBLIN.duplicate()
	slow22.attack_cooldown_ticks = 22
	for row in cd_case.rows:
		var world := _world()
		var base45 = world.spawn_unit(GOBLIN, 1, 0)
		var base22 = world.spawn_unit(slow22, 1, 0)
		if int(row.timer) > 0:
			check.call(
				world.apply_atk_slow(base45.id, float(row.amount), int(row.timer)),
				"attack-slow applies"
			)
			world.apply_atk_slow(base22.id, float(row.amount), int(row.timer))
		check.call(
			(
				world._eff_attack_cd(base45) == int(row.eff45)
				and world._eff_attack_cd(base22) == int(row.eff22)
			),
			"source effective cooldown at attack-slow %s" % str(row.amount)
		)


func _guards(check: Callable) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	check.call(
		not world.apply_slow(tower.id, 0.5, 90) and not world.apply_atk_slow(tower.id, 0.4, 90),
		"structures cannot be slowed"
	)
	var ally = world.spawn_unit(GOBLIN, 0, 0)
	check.call(
		world.apply_slow(ally.id, 0.5, 90) and world.apply_atk_slow(ally.id, 0.4, 90),
		"source slow has no team check; AOE callers filter allies"
	)
	var enemy = world.spawn_unit(GOBLIN, 1, 0)
	check.call(
		(
			not world.apply_slow(enemy.id, 0.0, 90)
			and not world.apply_slow(enemy.id, 0.5, 0)
			and not world.apply_slow(-1, 0.5, 90)
			and not world.apply_atk_slow(enemy.id, 0.0, 90)
			and not world.apply_atk_slow(enemy.id, 0.4, 0)
			and not world.apply_atk_slow(-1, 0.4, 90)
		),
		"slow rejects empty payloads and stale IDs"
	)
	check.call(world.defender_enabled == false, "ice domain tests keep the defender parked")


func _fly_to_impact(world: World, tower) -> void:
	for _index in range(60):
		var flying := false
		for shot in world.projectiles:
			if shot.active:
				flying = true
		if not flying:
			return
		world._update_projectiles(tower)


func _fly_again(world: World, tower, main) -> void:
	tower.cooldown_ticks = 0
	world.fire_projectile(tower.id, main.id)
	_fly_to_impact(world, tower)


func _world() -> World:
	var world := World.new()
	world.defender_enabled = false
	world.economy.gold[0] = 10000
	world.economy.opening[0] = 10000
	world.setup_arena()
	world.build_tower(0, 0)
	return world
