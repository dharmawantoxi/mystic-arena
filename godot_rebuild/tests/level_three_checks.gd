extends "res://tests/starter_finish_checks.gd"
## Ancient Apparition and Nyzrak source fixtures against real native combat.
const NYZRAK = preload("res://data/heroes/nyzrak.tres")
const APPARITION = preload("res://data/heroes/ancient_apparition.tres")
const LEVEL_THREE_FIXTURE := "res://tests/fixtures/level_three_source.json"
const HEROES := {"nyzrak": NYZRAK, "ancient_apparition": APPARITION}


func _hero(world: Battle, kind: String) -> Battle.HeroState:
	return world.spawn_hero(HEROES[kind], world.RED, Vector2(500, 340))


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(LEVEL_THREE_FIXTURE))
	for kind in HEROES:
		check.call(
			HEROES[kind].catalog_damage == fixture.catalog[kind].damage,
			"Level-three raw catalog damage oracle"
		)
		_levels(kind, fixture.levels[kind], check)
	for row in fixture.casts:
		_cast(row, check)
	for row in fixture.traces:
		_trace(row, check)
	for row in fixture.attacks:
		_attack(row, check)
	for row in fixture.respawn:
		_respawn(row, check)
	for row in fixture.defense:
		_flag_defense(row, check)
	for row in fixture.dot:
		_vortex_dot(row, check)
	for row in fixture.shield:
		_shield_flag(row, check)
	_guards(check)
	_roster(check)


func _flag_defense(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	helpers._dummy(world, Vector2(550, 340))
	check.call(world.cast_hero_e(hero.id), "Level-three E activation")
	check.call(hero.hp == row.before, "Level-three E does not heal the caster")
	world._deliver_hit(-1, world.BLUE, hero, 100, row.school, Vector2.ZERO)
	check.call(hero.hp == row.hp, "No invented mitigation from the level-three kits")


func _vortex_dot(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, "ancient_apparition")
	hero.hp = 500
	var enemies := _enemies(world, row.positions)
	hero.target_id = enemies[0].id
	check.call(helpers._skill(world, hero.id, row.key), "Apparition DOT " + row.mode)
	var moment := 0
	for tick in range(1, int(row.length) + 1):
		world._tick_hero(hero)
		if tick == 100 and row.mode == "recast":
			hero.skill_timer = 0
			check.call(world.cast_hero_q(hero.id), "Apparition Q recast re-arms the DOT")
		if moment < row.rows.size() and tick == row.rows[moment].tick:
			var expected: Dictionary = row.rows[moment]
			check.call(
				hero.vortex_active_timer == expected.timer,
				row.mode + " vortex clock tick " + str(tick)
			)
			for index in range(enemies.size()):
				check.call(
					enemies[index].hp == expected.enemies[index].hp,
					row.mode + " vortex DOT hit " + str(index) + " tick " + str(tick)
				)
				check.call(
					enemies[index].slow_amount == expected.enemies[index].slow,
					row.mode + " vortex slow " + str(index) + " tick " + str(tick)
				)
				check.call(
					enemies[index].slow_timer == expected.enemies[index].slow_timer,
					row.mode + " vortex slow clock " + str(index) + " tick " + str(tick)
				)
			moment += 1
	check.call(moment == row.rows.size(), "All vortex DOT source moments compared")


func _shield_flag(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, "nyzrak")
	hero.hp = 400
	hero.anti_heal_amount = row.reduction
	hero.anti_heal_timer = 900
	var enemy = helpers._dummy(world, Vector2(550, 340))
	hero.target_id = enemy.id
	check.call(not hero.shield_active and hero.shield_timer == 0, "Source defines no shield yet")
	check.call(world._cast_hero_r(hero.id), "Cold Embrace")
	check.call(hero.shield_active == row.shield_active, "Source shield flag recorded")
	check.call(hero.shield_timer == row.shield_timer, "Source shield clock recorded")
	check.call(enemy.hp == row.enemy_hp, "Cold Embrace nova damage")
	check.call(enemy.slow_amount == row.enemy_slow, "Cold Embrace slow amount")
	check.call(enemy.slow_timer == row.enemy_slow_timer, "Cold Embrace slow clock")
	check.call(hero.hp == row.before, "Cold Embrace 15% max hp heal with anti-heal")
	world._deliver_hit(-1, world.BLUE, hero, 100, row.school, Vector2.ZERO)
	check.call(hero.hp == row.hp, "The source shield flag grants NO mitigation")


func _guards(check: Callable) -> void:
	for kind in HEROES:
		var world := Battle.new()
		var hero := _hero(world, kind)
		var other := _hero(world, kind)
		helpers._dummy(world, Vector2(550, 340))
		check.call(world.cast_hero_q(hero.id), "Level-three Q activation")
		check.call(
			other.vortex_active_timer == 0 and not other.shield_active,
			"Level-three kit state stays per instance"
		)
		hero.alive = false
		for key in ["q", "w", "e", "r"]:
			check.call(not helpers._skill(world, hero.id, key), "Dead level-three hero cannot cast")


func _roster(check: Callable) -> void:
	var world := World.new()
	world.economy.credit_kill(world.RED, 4000)
	var index := 0
	for kind in HEROES:
		var definition = HEROES[kind]
		check.call(
			world._buy_ai_hero(kind, definition.cost, Vector2(1120, 90 + index * 40)),
			"Two different real level-three kits purchased"
		)
		index += 1
	check.call(world.economy.is_balanced(), "Level-three roster ledger balanced")
	check.call(world.units.size() == 2, "Both level-three heroes registered without substitution")
	for unit in world.units:
		check.call(HEROES.has(unit.definition.id), "Distinct level-three identity")
