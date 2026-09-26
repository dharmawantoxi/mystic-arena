extends RefCounted

const World = preload("res://scripts/match/prototype_battle.gd")
const Mage = preload("res://scripts/match/mage_upgrades.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/mage_source.json")
	)
	_path_selection(check, fixture.path_selection)
	for row in fixture.levels:
		_level(check, row)
	_muzzle(check, fixture.muzzle)
	for volley in fixture.volleys:
		_volley(check, volley)
	for case in fixture.on_hit:
		_on_hit(check, case)
	_debuff(check, fixture.debuff)
	_guards(check)


func _path_selection(check: Callable, expected: Dictionary) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	check.call(
		world.upgrade_price(tower.id, "mage") == int(expected.mage_price),
		"source level-1 mage quote"
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
	check.call(world.upgrade_tower(tower.id, 1, "mage"), "mage path upgrade accepted")
	check.call(
		(
			tower.settings().level == int(expected.mage_level)
			and tower.settings().tower_path == str(expected.mage_type)
		),
		"mage path switches type at level 2"
	)
	check.call(
		world.upgrade_price(tower.id) == int(expected.mage_next_default),
		"source mage level-3 quote ignores path argument"
	)
	check.call(world.upgrade_tower(tower.id, 2, "archer"), "later upgrade ignores path argument")
	check.call(
		(
			tower.settings().tower_path == str(expected.kept_type)
			and tower.settings().level == int(expected.kept_level)
		),
		"source keeps mage path past level 1"
	)
	for previous in range(3, 6):
		world.upgrade_tower(tower.id, previous)
	check.call(
		(
			world.upgrade_price(tower.id) == int(expected.mage_max_price)
			and not world.upgrade_tower(tower.id, 6)
		),
		"source mage level six is maxed with a zero quote"
	)
	check.call(world.economy.is_balanced(), "path ledger stays balanced")


func _level(check: Callable, row: Dictionary) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	for previous in range(1, int(row.level)):
		if previous == 1:
			tower.hp = 1
			tower.shield = 0
			world.upgrade_tower(tower.id, previous, "mage")
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
				"source mage upgrade price"
			)
			check.call(world.upgrade_tower(tower.id, previous), "mage upgrade accepted")
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
		["skill_down_amount", "skill_down"],
		["anti_heal_amount", "anti_heal"],
		["debuff_duration_ticks", "debuff_duration"],
		["chain_count", "chain"]
	]:
		check.call(data.get(pair[0]) == row[pair[1]], "source mage property " + pair[0])
	check.call(
		data.tower_path == "mage" and data.level == int(row.level) and data.volley_count == 1,
		"mage path, level and chain-driven volley"
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
		seller.upgrade_tower(sale_tower.id, previous, "mage" if previous == 1 else "archer")
	var refund_before: int = seller.economy.gold[0]
	check.call(seller.sell_tower(0, sale_tower.id), "mage sale succeeds")
	check.call(
		seller.economy.gold[0] == refund_before + int(row.refund),
		"source mage tier-specific refund"
	)
	check.call(
		not seller.sell_tower(0, sale_tower.id) and seller.economy.is_balanced(),
		"mage refund is exactly once"
	)
	if int(row.level) == 6:
		check.call(not world.upgrade_tower(tower.id, 6), "level six maximum rejects upgrade")
		check.call(world.transaction_error == "max_level", "maximum reports max_level")


func _muzzle(check: Callable, rows: Array) -> void:
	for row in rows:
		var world := _world()
		var tower = world.spawn_structure(Mage.LEVELS[int(row.level)], 0, Vector2(500, 340))
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
				"source mage muzzle level %d aim %s" % [int(row.level), str(spec[0])]
			)


func _volley(check: Callable, expected: Dictionary) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	for previous in range(1, int(expected.level)):
		world.upgrade_tower(tower.id, previous, "mage" if previous == 1 else "archer")
	tower.position = Vector2(500, 340)
	tower.cooldown_ticks = 0
	var primary = world.spawn_unit(GOBLIN, 1, 0)
	primary.position = Vector2(500 + int(expected.side) * 60, 340)
	var by_source_id := {7: primary.id}
	if str(expected.mode) == "full":
		var tower_range: float = tower.settings().attack_range_px
		for slot in range(int(tower.settings().chain_count) - 2):
			var extra = world.spawn_unit(GOBLIN, 1, 0)
			extra.position = Vector2(560 + slot * 12, 340)
			by_source_id[20 + slot] = extra.id
		var edge = world.spawn_unit(GOBLIN, 1, 0)
		edge.position = Vector2(500 + tower_range, 340)
		by_source_id[30] = edge.id
		var outside = world.spawn_unit(GOBLIN, 1, 0)
		outside.position = Vector2(500 + tower_range + 1.0, 340)
		var dead = world.spawn_unit(GOBLIN, 1, 0)
		dead.position = Vector2(570, 340)
		dead.alive = false
		var overflow = world.spawn_unit(GOBLIN, 1, 0)
		overflow.position = Vector2(575, 340)
	check.call(world.fire_projectile(tower.id, primary.id), "mage launch succeeds")
	var shots: Array = expected.shots
	check.call(
		world.projectiles.size() == shots.size(),
		(
			"source chain length without refill"
			if str(expected.mode) == "solo"
			else "source chain order and cap"
		)
	)
	for index in range(shots.size()):
		var shot = world.projectiles[index]
		var source = shots[index]
		check.call(
			shot.position == Vector2(source.position[0], source.position[1]),
			"source shared chain muzzle"
		)
		check.call(
			(
				shot.target_id == by_source_id[int(source.target)]
				and shot.damage == int(source.damage)
				and shot.kind == "mage"
			),
			"source chain bolt target and damage"
		)
		check.call(
			(
				shot.skill_down_amount == float(source.special.skill_down)
				and shot.anti_heal_amount == float(source.special.anti_heal)
				and shot.debuff_duration == int(source.special.debuff_duration)
			),
			"source chain bolt debuff payload"
		)
	check.call(
		primary.hp == 45 and tower.cooldown_ticks == tower.definition.attack_cooldown_ticks,
		"chain has no instant damage and sets cooldown once"
	)
	check.call(
		not world.fire_projectile(tower.id, primary.id), "mage cannot fire twice in one cooldown"
	)


func _on_hit(check: Callable, case: Dictionary) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	for previous in range(1, int(case.level)):
		world.upgrade_tower(tower.id, previous, "mage" if previous == 1 else "archer")
	tower.position = Vector2(500, 340)
	tower.cooldown_ticks = 0
	var main = world.spawn_unit(GOBLIN, 1, 0)
	main.hp = 10000
	main.position = Vector2(560, 340)
	check.call(world.fire_projectile(tower.id, main.id), "mage volley launches")
	check.call(world.projectiles.size() == 1, "lone target takes a single bolt")
	_fly_to_impact(world, tower)
	var main_call = case.main_calls[0]
	check.call(
		main.hp == 10000 - int(main_call.damage) and main.alive,
		"source mage direct damage without mitigation"
	)
	check.call(
		(
			main.skill_down_amount == float(case.main_skill.amount)
			and main.skill_down_timer == int(case.main_skill.timer)
		),
		"source applies skill-down to the main target"
	)
	check.call(
		(
			main.anti_heal_amount == float(case.main_anti.amount)
			and main.anti_heal_timer == int(case.main_anti.timer)
		),
		"source applies anti-heal to the main target"
	)
	var frail = world.spawn_unit(GOBLIN, 1, 0)
	frail.hp = 5
	frail.position = Vector2(560, 340)
	tower.cooldown_ticks = 0
	check.call(world.fire_projectile(tower.id, frail.id), "mage frail volley launches")
	_fly_to_impact(world, tower)
	var frail_call = case.frail_calls[0]
	check.call(
		not frail.alive and frail.hp == maxf(0.0, 5.0 - float(frail_call.damage)),
		"source mage bolt kills the frail victim"
	)
	check.call(
		(
			frail.skill_down_amount == float(case.frail_skill.amount)
			and frail.skill_down_timer == int(case.frail_skill.timer)
			and frail.anti_heal_amount == float(case.frail_anti.amount)
			and frail.anti_heal_timer == int(case.frail_anti.timer)
		),
		"dead victims keep no debuffs, like source clear on death"
	)
	check.call(world.economy.is_balanced(), "mage impact ledger stays balanced")


func _debuff(check: Callable, cases: Array) -> void:
	_stacking(check, cases[0], "skill_down")
	_stacking(check, cases[1], "anti_heal")
	_debuff_ticks(check, cases[2])
	_regen(check, cases[3])


func _stacking(check: Callable, stacking: Dictionary, kind: String) -> void:
	var world := _world()
	var unit = world.spawn_unit(GOBLIN, 1, 0)
	var apply := Callable(world, "apply_skill_down" if kind == "skill_down" else "apply_anti_heal")
	var amount := "skill_down_amount" if kind == "skill_down" else "anti_heal_amount"
	var timer := "skill_down_timer" if kind == "skill_down" else "anti_heal_timer"
	check.call(
		apply.call(unit.id, float(stacking.first.amount), int(stacking.first.timer)),
		"fresh %s applies" % kind
	)
	check.call(
		(
			unit.get(amount) == float(stacking.first.amount)
			and unit.get(timer) == int(stacking.first.timer)
		),
		"source fresh %s state" % kind
	)
	check.call(apply.call(unit.id, 0.10, 10), "weaker shorter %s lands" % kind)
	check.call(
		(
			unit.get(amount) == float(stacking.weaker_shorter.amount)
			and unit.get(timer) == int(stacking.weaker_shorter.timer)
		),
		"source ignores weaker shorter %s" % kind
	)
	check.call(apply.call(unit.id, 0.10, 200), "weaker longer %s lands" % kind)
	check.call(
		(
			unit.get(amount) == float(stacking.weaker_longer.amount)
			and unit.get(timer) == int(stacking.weaker_longer.timer)
		),
		"source longer duration refreshes even when weaker"
	)
	var strong := 0.50 if kind == "skill_down" else 0.75
	check.call(apply.call(unit.id, strong, 50), "stronger %s lands" % kind)
	check.call(
		(
			unit.get(amount) == float(stacking.stronger.amount)
			and unit.get(timer) == int(stacking.stronger.timer)
		),
		"source stronger %s wins" % kind
	)


func _debuff_ticks(check: Callable, ticks_case: Dictionary) -> void:
	var world := _world()
	var unit = world.spawn_unit(GOBLIN, 1, 0)
	unit.position = Vector2(600, 600)
	check.call(world.apply_skill_down(unit.id, 0.5, 3), "tick skill-down applies")
	check.call(world.apply_anti_heal(unit.id, 0.75, 2), "tick anti-heal applies")
	for event in ticks_case.ticks:
		world.step_tick()
		check.call(
			(
				unit.skill_down_amount == float(event.skill_amount)
				and unit.skill_down_timer == int(event.skill_timer)
				and unit.anti_heal_amount == float(event.anti_amount)
				and unit.anti_heal_timer == int(event.anti_timer)
			),
			"source debuff state after tick"
		)


func _regen(check: Callable, regen_case: Dictionary) -> void:
	for row in regen_case.rows:
		var world := _world()
		var definition = GOBLIN.duplicate()
		definition.max_hp = int(row.max_hp)
		definition.regen_per_tick = float(row.regen)
		var unit = world.spawn_unit(definition, 1, 0)
		unit.position = Vector2(600, 600)
		unit.hp = float(row.hp_before)
		if int(row.timer) > 0:
			world.apply_anti_heal(unit.id, float(row.amount), int(row.timer))
		world.step_tick()
		check.call(unit.hp == float(row.hp_after), "source anti-heal regen at %s" % str(row.amount))


func _guards(check: Callable) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	check.call(
		(
			not world.apply_skill_down(tower.id, 0.5, 180)
			and not world.apply_anti_heal(tower.id, 0.75, 180)
		),
		"structures cannot be debuffed"
	)
	var ally = world.spawn_unit(GOBLIN, 0, 0)
	check.call(
		world.apply_skill_down(ally.id, 0.5, 180) and world.apply_anti_heal(ally.id, 0.75, 180),
		"source debuff has no team check; chain callers pass enemies"
	)
	var enemy = world.spawn_unit(GOBLIN, 1, 0)
	check.call(
		(
			not world.apply_skill_down(enemy.id, 0.0, 180)
			and not world.apply_skill_down(enemy.id, 0.5, 0)
			and not world.apply_skill_down(-1, 0.5, 180)
			and not world.apply_anti_heal(enemy.id, 0.0, 180)
			and not world.apply_anti_heal(enemy.id, 0.75, 0)
			and not world.apply_anti_heal(-1, 0.75, 180)
		),
		"debuff rejects empty payloads and stale IDs"
	)
	check.call(world.defender_enabled == false, "mage domain tests keep the defender parked")


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
