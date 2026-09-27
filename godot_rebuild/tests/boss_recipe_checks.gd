extends "res://tests/starter_finish_checks.gd"
## Own-recipe boss batch (boss_recipe_skills.gd) against real native combat.
## The ID set is read from the handoff manifest, so a hero can only be claimed
## playable once its source recipe, oracle and this suite all exist.
const MANIFEST := "res://data/ai/hero_migration_status.json"
const HANDLER := "boss_recipe_skills.gd"
const IGNIS := preload("res://data/heroes/ignis_drachorn.tres")
const RECIPE_FIXTURE := "res://tests/fixtures/boss_recipe_source.json"
const HEROES := {"ignis_drachorn": IGNIS}
# fixture field name -> native HeroState property
const DRAGON_FIELDS := {
	"damage": "damage",
	"hp": "hp",
	"level": "level",
	"form": "dragon_form_active",
	"form_timer": "dragon_form_timer",
	"blood": "dragon_blood_active",
	"blood_timer": "dragon_blood_timer"
}
var _kinds: Array = []


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RECIPE_FIXTURE))
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	_kinds = hero_ids(manifest)
	check.call(not _kinds.is_empty(), "Own-recipe boss batch is not empty")
	check.call(_kinds == sorted_ids(), "Native batch and manifest handler list agree")
	for kind in _kinds:
		check.call(
			HEROES[kind].catalog_damage == fixture.catalog[kind].damage,
			"Own-recipe raw catalog damage oracle"
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
	for row in fixture.dragon:
		_dragon(row, check)
	_guards(check)
	_roster(check)


func hero_ids(manifest: Dictionary) -> Array:
	var result: Array = []
	for kind in manifest.heroes:
		if manifest.heroes[kind].native_handler == HANDLER:
			result.append(kind)
	result.sort()
	return result


func sorted_ids() -> Array:
	var result: Array = HEROES.keys()
	result.sort()
	return result


func _hero(world: Battle, kind: String) -> Battle.HeroState:
	return world.spawn_hero(HEROES[kind], world.RED, Vector2(500, 340))


func _flag_defense(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	helpers._dummy(world, Vector2(550, 340))
	check.call(world.cast_hero_e(hero.id), "Own-recipe E activation")
	check.call(hero.hp == row.before, "Own-recipe E does not heal the caster")
	world._deliver_hit(-1, world.BLUE, hero, 100, row.school, Vector2.ZERO)
	check.call(hero.hp == row.hp, "No invented mitigation from the own-recipe kits")


func _dragon(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, "ignis_drachorn")
	hero.hp = 500
	var enemies := _enemies(world, row.positions)
	hero.target_id = enemies[0].id
	check.call(helpers._skill(world, hero.id, row.key), "Ignis " + row.key)
	var moment := 0
	for tick in range(1, int(row.length) + 1):
		if tick == int(row.later_at):
			check.call(helpers._skill(world, hero.id, row.later), "Ignis " + row.later)
		if tick == int(row.upgrade_at):
			check.call(hero.upgrade(), "Ignis upgraded under the dragon buffs")
		world._tick_hero(hero)
		if moment < row.rows.size() and tick == row.rows[moment].tick:
			var expected: Dictionary = row.rows[moment]
			for key in DRAGON_FIELDS:
				check.call(
					hero.get(DRAGON_FIELDS[key]) == expected[key],
					row.mode + " dragon " + key + " tick " + str(tick)
				)
			for index in range(enemies.size()):
				check.call(
					enemies[index].hp == expected.enemies[index].hp,
					row.mode + " dragon nova hit " + str(index) + " tick " + str(tick)
				)
				check.call(
					enemies[index].cooldown_ticks == expected.enemies[index].stun,
					row.mode + " dragon stun " + str(index) + " tick " + str(tick)
				)
			moment += 1
	check.call(moment == row.rows.size(), "All dragon source moments compared")


func _guards(check: Callable) -> void:
	for kind in _kinds:
		var world := Battle.new()
		var hero := _hero(world, kind)
		var other := _hero(world, kind)
		helpers._dummy(world, Vector2(550, 340))
		check.call(world.cast_hero_q(hero.id), "Own-recipe Q activation")
		check.call(
			not other.dragon_form_active and not other.dragon_blood_active,
			"Own-recipe buff state stays per instance"
		)
		hero.alive = false
		for key in ["q", "w", "e", "r"]:
			check.call(not helpers._skill(world, hero.id, key), "Dead own-recipe hero cannot cast")


func _roster(check: Callable) -> void:
	var world := World.new()
	world.economy.credit_kill(world.RED, 4000)
	var index := 0
	for kind in _kinds:
		var definition = HEROES[kind]
		check.call(
			world._buy_ai_hero(kind, definition.cost, Vector2(1120, 90 + index * 40)),
			"Own-recipe boss kits purchased"
		)
		index += 1
	check.call(world.economy.is_balanced(), "Own-recipe roster ledger balanced")
	check.call(world.units.size() == _kinds.size(), "Every own-recipe hero registered")
	for unit in world.units:
		check.call(HEROES.has(unit.definition.id), "Distinct own-recipe identity")
