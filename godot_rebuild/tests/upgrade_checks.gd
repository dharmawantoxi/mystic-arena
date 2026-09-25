extends RefCounted

const World = preload("res://scripts/match/prototype_battle.gd")
const Upgrades = preload("res://scripts/match/archer_upgrades.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const Shot = preload("res://scripts/combat/projectile_state.gd")


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/archer_upgrade_source.json")
	)
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	for row in fixture:
		var level := int(row.level)
		if level > 1:
			tower.hp = 1
			tower.shield = 0
			tower.cooldown_ticks = 17
			tower.no_damage_ticks = 9
			var before: int = world.economy.gold[0]
			check.call(world.upgrade_price(tower.id) == int(row.price), "source upgrade price")
			check.call(world.upgrade_tower(tower.id, level - 1), "Archer upgrade accepted")
			check.call(
				world.economy.gold[0] == before - int(row.price), "upgrade debits exact price once"
			)
			check.call(
				not world.upgrade_tower(tower.id, level - 1),
				"stale expected level rejects duplicate upgrade"
			)
		var data = tower.settings()
		for pair in [
			["max_hp", "max_hp"],
			["damage", "damage"],
			["attack_range_px", "range"],
			["attack_cooldown_ticks", "cooldown"],
			["armor", "armor"],
			["sale_refund", "refund"]
		]:
			check.call(data.get(pair[0]) == row[pair[1]], "source upgraded property " + pair[0])
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
		check.call(
			world.upgrade_price(tower.id) == int(row.next_price), "source next/max level quote"
		)
		check.call(
			data.is_valid() and world.economy.is_balanced(), "upgraded definition and ledger valid"
		)
		for volley in row.volleys:
			_volley(check, level, volley)
		var seller := _world()
		var sale_tower = seller.get_unit(seller.slots[0].structure_id)
		for previous in range(1, level):
			seller.upgrade_tower(sale_tower.id, previous)
		var before: int = seller.economy.gold[0]
		check.call(seller.sell_tower(0, sale_tower.id), "upgraded tower sale succeeds")
		check.call(
			seller.economy.gold[0] == before + int(row.refund), "source tier-specific refund"
		)
		check.call(
			not seller.sell_tower(0, sale_tower.id) and seller.economy.is_balanced(),
			"upgraded refund is exactly once"
		)
	check.call(not world.upgrade_tower(tower.id, 6), "level six maximum rejects upgrade")
	_guards(check)


func _volley(check: Callable, level: int, expected: Dictionary) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	for previous in range(1, level):
		world.upgrade_tower(tower.id, previous)
	tower.position = Vector2(500, 340)
	var mapping: Dictionary = {}
	var dead = world.spawn_unit(GOBLIN, 1, 0)
	dead.position = Vector2(501, 340)
	dead.alive = false
	mapping[dead.id] = 90
	var far = world.spawn_unit(GOBLIN, 1, 0)
	far.position = Vector2(1500, 340)
	mapping[far.id] = 91
	# Friendly units are also excluded even though they are present in the world registry.
	var friendly = world.spawn_unit(GOBLIN, 0, 0)
	friendly.position = Vector2(502, 340)
	for index in range(int(expected.count) - 1):
		var extra = world.spawn_unit(GOBLIN, 1, 0)
		extra.position = Vector2(500 + int(expected.side) * (70 + index * 10), 340)
		mapping[extra.id] = index + 2
	var primary = world.spawn_unit(GOBLIN, 1, 0)
	primary.position = Vector2(500 + int(expected.side) * 60, 340)
	mapping[primary.id] = 1
	check.call(world.fire_projectile(tower.id, primary.id), "source volley launch succeeds")
	check.call(
		world.projectiles.size() == expected.shots.size(),
		"source two/three arrow count, not table label"
	)
	for index in range(mini(world.projectiles.size(), expected.shots.size())):
		var shot = world.projectiles[index]
		var source = expected.shots[index]
		check.call(
			shot.position == Vector2(source.position[0], source.position[1]),
			"source level muzzle and offset"
		)
		check.call(
			mapping[shot.target_id] == int(source.target) and shot.damage == int(source.damage),
			"source ordered secondary targets / primary fallback"
		)
	check.call(
		primary.hp == 45 and tower.cooldown_ticks == tower.definition.attack_cooldown_ticks,
		"volley has no instant damage and sets cooldown once"
	)
	check.call(
		not world.fire_projectile(tower.id, primary.id), "volley cannot fire twice in one cooldown"
	)


func _guards(check: Callable) -> void:
	var world := _world()
	var tower = world.get_unit(world.slots[0].structure_id)
	var enemy = world.spawn_unit(GOBLIN, 1, 0)
	enemy.position = tower.position + Vector2(80, 0)
	world.fire_projectile(tower.id, enemy.id)
	var old_shot = world.projectiles[0]
	world.upgrade_tower(tower.id, 1)
	check.call(
		old_shot.damage == 20 and world.projectiles.size() == 1 and old_shot.active,
		"in-flight shot keeps old damage after upgrade"
	)
	check.call(tower.cooldown_ticks == 35, "upgrade cannot reset firing cooldown")
	var other := _world()
	check.call(
		(
			other.get_unit(other.slots[0].structure_id).definition == Upgrades.LEVELS[0]
			and Upgrades.LEVELS[0].max_hp == 2000
		),
		"upgrade never mutates shared resource or other match"
	)
	world.build_tower(0, 1)
	check.call(
		world.get_unit(world.slots[1].structure_id).settings().level == 1,
		"new builds remain level one"
	)
	world.build_tower(1, 9)
	check.call(
		not world.upgrade_tower(world.slots[9].structure_id, 1), "enemy tower upgrade rejected"
	)
	check.call(
		not world.upgrade_tower(world.nexuses[0].id, 1),
		"nexus upgrade unavailable until minion scaling port"
	)
	check.call(
		not world.upgrade_tower(enemy.id, 1) and not world.upgrade_tower(-1, 1),
		"invalid targets rejected"
	)
	var sold_id: int = tower.id
	world.sell_tower(0, sold_id)
	world.build_tower(0, 0)
	check.call(not world.upgrade_tower(sold_id, 1), "stale ID cannot upgrade replacement")
	tower = world.get_unit(world.slots[0].structure_id)
	tower.alive = false
	check.call(not world.upgrade_tower(tower.id, 1), "dead tower cannot be healed by upgrade")
	var poor := World.new()
	poor.setup_arena()
	poor.build_tower(0, 0)
	var poor_tower = poor.get_unit(poor.slots[0].structure_id)
	poor.economy.spend(0, 800)
	check.call(
		(
			not poor.upgrade_tower(poor_tower.id, 1)
			and poor.economy.gold[0] == 100
			and poor_tower.settings().level == 1
			and poor.economy.is_balanced()
		),
		"poor upgrade rejects without mutation"
	)
	var capped := _world()
	var shooter = capped.get_unit(capped.slots[0].structure_id)
	for level in range(1, 6):
		capped.upgrade_tower(shooter.id, level)
	var target = capped.spawn_unit(GOBLIN, 1, 0)
	target.position = shooter.position + Vector2(60, 0)
	for index in range(capped.MAX_PROJECTILES - 2):
		capped.projectiles.append(Shot.new())
	var next_id: int = capped._next_projectile_id
	check.call(
		(
			not capped.fire_projectile(shooter.id, target.id)
			and shooter.cooldown_ticks == 0
			and capped._next_projectile_id == next_id
		),
		"whole volley cap rejection is atomic"
	)
	capped.projectiles.clear()
	check.call(
		capped.fire_projectile(shooter.id, target.id), "volley resumes when capacity recovers"
	)
	var shots: Array = capped.projectiles.duplicate()
	capped.sell_tower(0, shooter.id)
	check.call(capped.projectiles.is_empty(), "sale cancels entire upgraded volley")
	for shot in shots:
		check.call(not shot.active, "sold volley cannot deliver later")
	var finished := _world()
	finished.winner = 1
	check.call(
		not finished.upgrade_tower(finished.slots[0].structure_id, 1), "result blocks upgrade"
	)

	var impact_world := _world()
	var archer = impact_world.get_unit(impact_world.slots[0].structure_id)
	for level in range(1, 6):
		impact_world.upgrade_tower(archer.id, level)
	var victim = impact_world.spawn_unit(GOBLIN, 1, 0)
	victim.position = archer.position + Vector2(40, 0)
	victim.hp = 500
	impact_world.fire_projectile(archer.id, victim.id)
	for arrow in impact_world.projectiles:
		arrow.position = victim.position
	impact_world._update_projectiles(archer)
	check.call(victim.hp == 110, "three arrows deliver three independent source damage hits")
	impact_world._update_projectiles(archer)
	check.call(victim.hp == 110, "processed volley cannot hit twice")
	archer.cooldown_ticks = 0
	impact_world.projectiles.clear()
	impact_world.fire_projectile(archer.id, victim.id)
	for arrow in impact_world.projectiles:
		arrow.position = victim.position
	impact_world._update_projectiles(archer)
	check.call(
		not victim.alive and impact_world.kills[0] == 1 and impact_world.credited_gold[0] == 8,
		"fallback volley overkill rewards victim once, not once per arrow"
	)


func _world() -> World:
	var world := World.new()
	world.defender_enabled = false
	world.economy.gold[0] = 10000
	world.economy.opening[0] = 10000
	world.setup_arena()
	world.build_tower(0, 0)
	return world
