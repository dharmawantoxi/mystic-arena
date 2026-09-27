extends "res://tests/starter_finish_checks.gd"
## Same fixture runner, distinct source recipes and oracle for every boss here.
const BOSS_FIXTURE := "res://tests/fixtures/boss_level_one_source.json"
const BOSSES := {
	"gornak": preload("res://data/heroes/gornak.tres"),
	"morgath": preload("res://data/heroes/morgath.tres"),
	"drakar": preload("res://data/heroes/drakar.tres"),
	"abaddon": preload("res://data/heroes/abaddon.tres")
}


func _hero(world: Battle, kind: String) -> Battle.HeroState:
	return world.spawn_hero(BOSSES[kind], world.RED, Vector2(500, 340))


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(BOSS_FIXTURE))
	for kind in BOSSES:
		check.call(
			BOSSES[kind].catalog_damage == fixture.catalog[kind].damage,
			"Boss raw catalog buff damage oracle"
		)
	for row in fixture.casts:
		_cast(row, check)
	for row in fixture.traces:
		_trace(row, check)
	for row in fixture.attacks:
		_attack(row, check)
	for row in fixture.respawn:
		_respawn(row, check)
	for row in fixture.execute:
		_execute(row, check)
	for row in fixture.defense:
		_flag_defense(row, check)
	_roster(check)


func _execute(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, "drakar")
	while hero.level < row.level:
		check.call(hero.upgrade(), "Drakar leveled execute")
	var enemy = helpers._dummy(world, Vector2(550, 340))
	enemy.hp = row.hp
	check.call(world._cast_hero_r(hero.id), "Culling Blade")
	check.call(enemy.hp == row.after, "Strict source execute threshold/int then double")


func _flag_defense(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	helpers._dummy(world, Vector2(550, 340))
	check.call(world.cast_hero_e(hero.id), "Boss E activation")
	check.call(hero.hp == row.before, "Boss E heal before hit")
	world._deliver_hit(-1, world.BLUE, hero, 100, row.school, Vector2.ZERO)
	check.call(hero.hp == row.hp, "No invented mitigation from source defense flag")


func _roster(check: Callable) -> void:
	var world := World.new()
	world.economy.credit_kill(world.RED, 4000)
	var index := 0
	for kind in BOSSES:
		var definition = BOSSES[kind]
		check.call(
			world._buy_ai_hero(kind, definition.cost, Vector2(1120, 90 + index * 40)),
			"Four different real boss kits purchased"
		)
		index += 1
	check.call(world.economy.is_balanced(), "Boss roster ledger balanced")
	check.call(world.units.size() == 4, "Four boss heroes registered without substitution")
	for unit in world.units:
		check.call(BOSSES.has(unit.definition.id), "Distinct boss identity")
