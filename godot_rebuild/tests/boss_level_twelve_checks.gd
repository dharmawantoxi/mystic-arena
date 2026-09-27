extends "res://tests/starter_finish_checks.gd"
## Level-12 bosses (Aurelix, Aurelyssa, Vargrath, Nazulmor) real recipes, gates,
## timers, attacks, respawn.
const BOSS_FIXTURE := "res://tests/fixtures/boss_level_twelve_source.json"
const BOSSES := {
	"nazulmor": preload("res://data/heroes/nazulmor.tres"),
	"vargrath": preload("res://data/heroes/vargrath.tres"),
	"aurelyssa": preload("res://data/heroes/aurelyssa.tres"),
	"aurelix": preload("res://data/heroes/aurelix.tres"),
}


func _hero(world: Battle, kind: String) -> Battle.HeroState:
	return world.spawn_hero(BOSSES[kind], world.RED, Vector2(500, 340))


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(BOSS_FIXTURE))
	for kind in BOSSES:
		check.call(
			BOSSES[kind].catalog_damage == fixture.catalog[kind].damage,
			"Level12 boss raw catalog damage oracle"
		)
	for kind in BOSSES:
		_levels(kind, fixture.levels[kind], check)
	for row in fixture.casts:
		_cast(row, check)
	for row in fixture.traces:
		_trace(row, check)
	for row in fixture.attacks:
		_attack(row, check)
	for row in fixture.respawn:
		_respawn(row, check)
	_roster(check)


func _cast(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	hero.hp = 500
	var enemies := _enemies(world, row.positions)
	if row.target >= 0:
		hero.target_id = enemies[int(row.target)].id
	var skill_key: String = row.key
	check.call(helpers._skill(world, hero.id, skill_key) == row.ok, row.hero + " cast " + row.key)
	if row.repeat != null:
		check.call(
			helpers._skill(world, hero.id, skill_key) == row.repeat,
			row.hero + " duplicate cast " + row.key
		)
	_compare(hero, enemies, row.state, check, row.hero + " " + row.key)


func _trace(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	hero.hp = 500
	var enemies := _enemies(world, row.positions)
	hero.target_id = enemies[0].id
	enemies[0].cooldown_ticks = 90
	check.call(
		helpers._skill(world, hero.id, row.key), "Level12 timer cast " + row.hero + " " + row.key
	)
	var moment := 0
	for tick in range(1, int(row.get("length", 601)) + 1):
		if tick == 2 and row.mode == "move_upgrade":
			hero.position.x += 100
			enemies[0].position.x += 200
			check.call(hero.upgrade(), "Upgrade during level12 effect")
		if tick == 2 and row.mode == "retarget":
			hero.target_id = enemies[1].id
		if tick == 2 and row.mode == "target_dies":
			enemies[0].alive = false
		world._tick_hero(hero)
		if moment < row.rows.size() and tick == row.rows[moment].tick:
			_compare(
				hero,
				enemies,
				row.rows[moment].state,
				check,
				row.hero + " " + row.key + " " + row.mode + " tick " + str(tick)
			)
			moment += 1
	check.call(
		moment == row.rows.size(), "All level12 trace moments compared " + row.hero + " " + row.key
	)


func _attack(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	var target_point: Array = row.get("target_position", [560, 340])
	var enemy = helpers._dummy(world, Vector2(target_point[0], target_point[1]))
	check.call(world.hero_basic_attack(hero.id, enemy.id), "Level12 basic attack " + row.hero)
	for moment in row.rows:
		if moment.tick > 0:
			world._tick_hero(hero)
		check.call(enemy.hp == moment.hp, "Level12 projectile impact " + row.hero)
		check.call(hero.attack_timer == moment.attack_timer, "Level12 attack cooldown " + row.hero)
		check.call(
			world.hero_projectiles.size() == moment.positions.size(),
			"Level12 arrow lifecycle " + row.hero
		)
		for index in range(mini(world.hero_projectiles.size(), moment.positions.size())):
			var point: Array = moment.positions[index]
			check.call(
				(
					world.hero_projectiles[index].position.distance_to(Vector2(point[0], point[1]))
					< 0.002
				),
				"Level12 homing trajectory " + row.hero
			)


func _respawn(row: Dictionary, check: Callable) -> void:
	var world := World.new()
	var hero := _hero(world, row.hero)
	var enemies := _enemies(world, [[550, 340]])
	for key in ["q", "w", "e", "r"]:
		check.call(helpers._skill(world, hero.id, key), "Pre-death activation " + row.hero)
	hero.attack_timer = 17
	hero.hp = 0
	hero.alive = false
	hero.respawn_timer = 1
	world._step_hero_respawn(hero)
	_compare(hero, enemies, row.state, check, row.hero + " respawn")


func _roster(check: Callable) -> void:
	var world := World.new()
	world.economy.credit_kill(world.RED, 8000)
	var index := 0
	for kind in BOSSES:
		var definition = BOSSES[kind]
		check.call(
			world._buy_ai_hero(kind, definition.cost, Vector2(1120, 90 + index * 40)),
			"Level12 real kits purchased " + kind
		)
		index += 1
	check.call(world.economy.is_balanced(), "Level12 roster ledger balanced")
	check.call(world.units.size() == BOSSES.size(), "Level12 heroes registered")
	for unit in world.units:
		check.call(
			BOSSES.has(unit.definition.id), "Distinct level12 identity " + unit.definition.id
		)


func _compare(hero, enemies: Array, expected: Dictionary, check: Callable, label: String) -> void:
	for key in expected:
		if key == "enemies":
			for idx in range(enemies.size()):
				for field in expected.enemies[idx]:
					check.call(
						enemies[idx].get(field) == expected.enemies[idx][field],
						label + " enemy " + str(idx) + " " + field
					)
		elif (
			key
			in [
				"position",
				"vortex_origin",
				"blink_from",
				"mana_void_origin",
				"alchemy_target",
				"w_dir",
				"r_dir"
			]
		):
			if expected[key] is Array:
				check.call(
					hero.get(key) == Vector2(expected[key][0], expected[key][1]), label + " " + key
				)
			else:
				check.call(hero.get(key) == expected[key], label + " " + key)
		elif key in ["target_id", "flux_target_id"]:
			var target := int(expected[key])
			check.call(
				hero.get(key) == (-1 if target < 0 else enemies[target].id), label + " " + key
			)
		else:
			check.call(hero.get(key) == expected[key], label + " " + key)


func _enemies(world: Battle, positions: Array) -> Array:
	var result := []
	for pos in positions:
		result.append(helpers._dummy(world, Vector2(pos[0], pos[1])))
	return result
