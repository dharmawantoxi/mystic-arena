extends "res://tests/boss_level_one_checks.gd"
const ALCHEMIST = preload("res://data/heroes/alchemist.tres")
const ALCHEMIST_FIXTURE := "res://tests/fixtures/alchemist_source.json"


func _hero(world: Battle, _kind: String) -> Battle.HeroState:
	return world.spawn_hero(ALCHEMIST, world.RED, Vector2(500, 340))


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(ALCHEMIST_FIXTURE))
	check.call(
		ALCHEMIST.catalog_damage == fixture.catalog.alchemist.damage, "Alchemist buff catalog"
	)
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
	_levels("alchemist", fixture.levels.alchemist, check)
	for row in fixture.kills:
		_kill_heal(row, check)


func _kill_heal(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, "alchemist")
	hero.hp = 500
	hero.anti_heal_amount = row.reduction
	hero.anti_heal_timer = 900
	var enemies := _enemies(world, [[550, 340], [650, 340], [700, 340], [701, 340]])
	for index in [0, 2, 3]:
		enemies[index].hp = 1
	check.call(world._cast_hero_r(hero.id), "Greevil's Greed actual kills")
	check.call(hero.hp == row.hp, "100 HP per kill, capped and anti-heal adjusted")
	for index in range(enemies.size()):
		check.call(enemies[index].hp == row.enemies[index].hp, "Alchemist R radius 200 boundary")
		check.call(enemies[index].alive == row.enemies[index].alive, "Alchemist R death once")
	check.call(world.kills[world.RED] == 2, "Only killed live targets counted")
