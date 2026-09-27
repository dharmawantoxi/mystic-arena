extends "res://tests/starter_finish_checks.gd"
## Shared native replay harness for the level 5+ boss suites.
##
## This file is a COMPARISON HARNESS, not a hero kit: it replays one captured
## source fixture against real native combat for the IDs a level suite names.
## Every number it asserts comes from that fixture; the kits themselves live in
## scripts/combat/boss_level_*_skills.gd and stay one file per source level.
# `helpers`, `Battle` and `World` are inherited from starter_finish_checks.gd;
# redeclaring a parent member is an error in Godot 4, so none are repeated here.
var _bosses: Dictionary = {}
var _length := 601
var _label := "boss level"


func run_level(check: Callable, fixture_path: String, bosses: Dictionary, length: int) -> void:
	_bosses = bosses
	_length = length
	_label = (
		"boss "
		+ fixture_path.get_file().trim_suffix("_source.json").trim_prefix("boss_").replace("_", " ")
	)
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(fixture_path))
	for kind in bosses:
		check.call(
			bosses[kind].catalog_damage == fixture.catalog[kind].damage,
			_label + " boss raw catalog damage oracle"
		)
	for kind in bosses:
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


func _hero(world: Battle, kind: String) -> Battle.HeroState:
	return world.spawn_hero(_bosses[kind], world.RED, Vector2(500, 340))


func _enemies(world: Battle, positions: Array) -> Array:
	var result := []
	for pos in positions:
		result.append(helpers._dummy(world, Vector2(pos[0], pos[1])))
	return result


func _cast(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	hero.hp = 500
	var enemies := _enemies(world, row.positions)
	if row.target >= 0:
		hero.target_id = enemies[int(row.target)].id
	check.call(helpers._skill(world, hero.id, row.key) == row.ok, row.hero + " cast " + row.key)
	check.call(
		helpers._skill(world, hero.id, row.key) == row.repeat,
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
	check.call(helpers._skill(world, hero.id, row.key), _label + " timer cast " + row.key)
	var moment := 0
	for tick in range(1, int(row.get("length", _length)) + 1):
		if tick == 2 and row.mode == "move_upgrade":
			hero.position.x += 100
			enemies[0].position.x += 200
			check.call(hero.upgrade(), "Upgrade during " + _label + " effect")
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
	check.call(moment == row.rows.size(), "All " + _label + " trace moments compared " + row.hero)


func _attack(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	var target_point: Array = row.get("target_position", [560, 340])
	var enemy = helpers._dummy(world, Vector2(target_point[0], target_point[1]))
	check.call(world.hero_basic_attack(hero.id, enemy.id), _label + " basic attack " + row.hero)
	for moment in row.rows:
		if moment.tick > 0:
			world._tick_hero(hero)
		check.call(enemy.hp == moment.hp, _label + " projectile impact " + row.hero)
		check.call(
			hero.attack_timer == moment.attack_timer, _label + " attack cooldown " + row.hero
		)
		check.call(
			world.hero_projectiles.size() == moment.positions.size(),
			_label + " arrow lifecycle " + row.hero
		)
		for index in range(mini(world.hero_projectiles.size(), moment.positions.size())):
			var point: Array = moment.positions[index]
			check.call(
				(
					world.hero_projectiles[index].position.distance_to(Vector2(point[0], point[1]))
					< 0.002
				),
				_label + " homing trajectory " + row.hero
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
	var total := 0
	for kind in _bosses:
		total += int(_bosses[kind].cost)
	world.economy.credit_kill(world.RED, total + 1000)
	var index := 0
	for kind in _bosses:
		var definition = _bosses[kind]
		check.call(
			world._buy_ai_hero(kind, definition.cost, Vector2(1120, 90 + index * 40)),
			_label + " real kits purchased " + kind
		)
		index += 1
	check.call(world.economy.is_balanced(), _label + " roster ledger balanced")
	check.call(world.units.size() == _bosses.size(), _label + " heroes registered")
	for unit in world.units:
		check.call(
			_bosses.has(unit.definition.id),
			"Distinct " + _label + " identity " + unit.definition.id
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
