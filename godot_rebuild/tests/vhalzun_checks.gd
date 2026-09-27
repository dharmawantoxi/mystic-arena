extends "res://tests/boss_level_four_checks.gd"
## Reuse fixture comparison only, never another hero's implementation.
const VHALZUN = preload("res://data/heroes/vhalzun.tres")
const Lifecycle = preload("res://tests/source_shared_boss_checks.gd")


func _hero(world: Battle, _kind: String) -> Battle.HeroState:
	return world.spawn_hero(VHALZUN, world.RED, Vector2(500, 340))


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/vhalzun_source.json")
	)
	check.call(VHALZUN.catalog_damage == fixture.catalog.vhalzun.damage, "Vhalzun catalog")
	_levels("vhalzun", fixture.levels.vhalzun, check)
	for row in fixture.casts:
		_cast(row, check)
	for row in fixture.traces:
		_trace(row, check)
	for row in fixture.attacks:
		_attack(row, check)
	for row in fixture.respawn:
		_respawn(row, check)
	for row in fixture.clocks:
		_clocks(row, check)
	for row in fixture.healing:
		_healing(row, check)
	for row in fixture.selection:
		_selection(row, check)
	for row in fixture.defense:
		_no_defense(row, check)
	Lifecycle.new()._lifecycle("vhalzun", check)
	_roster(check)


func _clocks(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, "vhalzun")
	var enemies := _enemies(world, [[550, 340]])
	check.call(helpers._skill(world, hero.id, row.key), "Vhalzun clock start")
	var moment := 0
	for tick in range(1, int(row.duration) + 1):
		world._tick_hero(hero)
		if moment < row.rows.size() and tick == row.rows[moment].tick:
			_compare(hero, enemies, row.rows[moment].state, check, "Vhalzun clock " + row.key)
			if tick < row.duration:
				check.call(not helpers._skill(world, hero.id, row.key), "Vhalzun cooldown holds")
			moment += 1
	check.call(moment == row.rows.size(), "Vhalzun all clock boundaries")
	check.call(helpers._skill(world, hero.id, row.key), "Vhalzun exact cooldown recast")
	_compare(hero, enemies, row.recast, check, "Vhalzun recast " + row.key)


func _healing(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, "vhalzun")
	while hero.level < row.level:
		check.call(hero.upgrade(), "Vhalzun healing level")
	hero.hp = row.initial
	hero.anti_heal_amount = row.reduction
	hero.anti_heal_timer = 900
	var enemy = _enemies(world, [[550, 340]])[0]
	enemy.definition.max_hp = 100000
	enemy.hp = 100000
	check.call(helpers._skill(world, hero.id, row.key), "Vhalzun heal activation")
	check.call(hero.hp == row.hp, "Vhalzun cap then anti-heal " + row.key)
	check.call(enemy.hp == row.enemy_hp, "Vhalzun leveled damage " + row.key)


func _selection(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, "vhalzun")
	var enemies := _enemies(world, [[550, 340], [600, 340], [540, 340]])
	hero.target_id = enemies[0].id
	if row.mode == "dead_selected":
		enemies[0].alive = false
	if row.mode == "friendly_unselected":
		enemies[1].team = world.RED
	if row.mode == "stun_max":
		enemies[0].cooldown_ticks = 200
	check.call(helpers._skill(world, hero.id, row.key), "Vhalzun target/stun cast")
	_compare(hero, enemies, row.state, check, "Vhalzun " + row.mode + " " + row.key)


func _no_defense(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, "vhalzun")
	_enemies(world, [[550, 340]])
	check.call(world.cast_hero_e(hero.id), "Vhalzun siphon")
	check.call(hero.hp == row.before, "Vhalzun siphon HP before hit")
	world._deliver_hit(-1, world.BLUE, hero, 100, row.school, Vector2.ZERO)
	check.call(hero.hp == row.hp, "No invented Vhalzun defense")


func _roster(check: Callable) -> void:
	var world := World.new()
	world.economy.credit_kill(world.RED, 4000)
	check.call(world._buy_ai_hero("vhalzun", 1200, Vector2(1120, 90)), "Vhalzun summon")
	check.call(world.units.size() == 1, "Vhalzun one registered hero")
	check.call(world.units[0].definition.id == "vhalzun", "Vhalzun not substituted")
	check.call(world.economy.is_balanced(), "Vhalzun balanced ledger")
