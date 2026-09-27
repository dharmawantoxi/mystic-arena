extends "res://tests/starter_finish_checks.gd"
## Per-ID behavioral checks; numeric baseline alone never registers a playable kit.
const Shared = preload("res://scripts/combat/source_shared_boss_skills.gd")
const Roster = preload("res://scripts/data/hero_roster.gd")
const SHARED_FIXTURE := "res://tests/fixtures/source_shared_boss.json"


func _hero(world: Battle, kind: String) -> Battle.HeroState:
	return world.spawn_hero(Roster.DEFINITIONS[kind], world.RED, Vector2(500, 340))


func _enemies(world: Battle, positions: Array) -> Array:
	var result := super._enemies(world, positions)
	for enemy in result:
		enemy.definition.max_hp = 100000
		enemy.hp = 100000
	return result


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(SHARED_FIXTURE))
	check.call(Shared.IDS.size() == fixture.ids.size(), "Closed source shared-kit membership size")
	for kind in fixture.ids:
		check.call(kind in Shared.IDS, "Actual source dispatch membership: " + kind)
		var data: Dictionary = fixture.heroes[kind]
		for row in data.casts:
			_cast(row, check)
		for row in data.clocks:
			_clocks(kind, row, check)
		for row in data.attacks:
			_attack(row, check)
		for row in data.respawn:
			_respawn(row, check)
		_levels(kind, data.levels, check)
		_lifecycle(kind, check)
	_no_fallback(check)
	_schools(check)


func _clocks(kind: String, row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, kind)
	var enemies := _enemies(world, [[550, 340]])
	check.call(helpers._skill(world, hero.id, row.key), kind + " initial skill")
	var moment := 0
	for tick in range(1, int(row.duration) + 1):
		world._tick_hero(hero)
		if moment < row.rows.size() and tick == row.rows[moment].tick:
			_compare(hero, enemies, row.rows[moment].state, check, kind + " clock " + str(tick))
			if tick < row.duration:
				check.call(not helpers._skill(world, hero.id, row.key), kind + " cooldown holds")
			moment += 1
	check.call(moment == row.rows.size(), kind + " all source cooldown boundaries")
	check.call(helpers._skill(world, hero.id, row.key), kind + " exact cooldown recast")
	_compare(hero, enemies, row.recast, check, kind + " recast")


func _lifecycle(kind: String, check: Callable) -> void:
	var world := World.new()
	var hero := _hero(world, kind)
	var enemies := _enemies(world, [[550, 340]])
	hero.hp = 1
	world._deliver_hit(enemies[0].id, world.BLUE, hero, 10000, "magic", enemies[0].position)
	check.call(not hero.alive and hero.deaths == 1, kind + " real combat death once")
	for key in ["q", "w", "e", "r"]:
		check.call(not helpers._skill(world, hero.id, key), kind + " dead cast refused")
	for tick in range(599):
		world._step_hero_respawn(hero)
	check.call(not hero.alive and hero.respawn_timer == 1, kind + " respawn pending 599")
	world._step_hero_respawn(hero)
	check.call(hero.alive and hero.hp == hero.max_hp, kind + " full HP respawn tick 600")
	check.call(hero.position == World.RED_HERO_SPAWN, kind + " respawn team position")
	world.winner = world.BLUE
	check.call(not helpers._skill(world, hero.id, "q"), kind + " finished world no cast")


func _no_fallback(check: Callable) -> void:
	var world := Battle.new()
	var fake = Roster.DEFINITIONS.kaizen.duplicate()
	fake.id = "alchemist"
	var hero := world.spawn_hero(fake, world.RED, Vector2(500, 340))
	_enemies(world, [[550, 340]])
	for key in ["q", "w", "e", "r"]:
		check.call(
			not Shared.cast(world, hero, key, []), "No generic substitution for source recipe"
		)
		check.call(not helpers._skill(world, hero.id, key), "Dispatcher refuses unported recipe")


func _schools(check: Callable) -> void:
	var rows: Array = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/hero_school_source.json")
	)
	for row in rows:
		var world := Battle.new()
		var hero := _hero(world, row.hero)
		var defender := world.spawn_hero(Roster.DEFINITIONS.thorne, world.BLUE, Vector2(550, 340))
		check.call(world.cast_hero_w(defender.id), "Source Thorne mitigation activation")
		check.call(helpers._skill(world, hero.id, row.key), row.hero + " real hero-v-hero cast")
		check.call(
			defender.hp == row.target_hp and defender.alive == row.target_alive,
			row.hero + " source damage school mitigation"
		)
		check.call(hero.hp == row.hp, row.hero + " source attribution/post-mitigation reflect")
