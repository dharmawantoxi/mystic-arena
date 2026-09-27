extends RefCounted
const World = preload("res://scripts/match/prototype_battle.gd")
const Battle = preload("res://scripts/combat/minion_battle.gd")
const Helpers = preload("res://tests/sylara_checks.gd")
const FIXTURE := "res://tests/fixtures/hero_status_source.json"


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var helpers := Helpers.new()
	for row in fixture.heals:
		var world := Battle.new()
		var hero := world.spawn_hero(World.PLAYABLE_AI_HEROES[row.hero], 1, Vector2(500, 340))
		hero.hp = hero.max_hp - row.missing
		hero.anti_heal_amount = row.reduction
		hero.anti_heal_timer = 900
		helpers._dummy(world, Vector2(550, 340))
		check.call(helpers._skill(world, hero.id, row.key), "Status interaction cast")
		check.call(hero.hp == row.cast_hp, "Source cap BEFORE anti-heal gain reduction")
		world._tick_hero(hero)
		check.call(hero.hp == row.tick_hp, "Source recurring heal anti-heal")
	var world := Battle.new()
	var hero := world.spawn_hero(World.PLAYABLE_AI_HEROES.zephyr, 1, Vector2(500, 340))
	hero.hp = 300
	world.cast_hero_w(hero.id)
	world.apply_burn(hero.id, 60, 210, world.BLUE)
	var moment := 0
	for tick in range(1, 211):
		world.step_tick()
		if moment < fixture.burn.size() and tick == fixture.burn[moment].tick:
			var row: Dictionary = fixture.burn[moment]
			check.call(hero.hp == row.hp, "Source realm blocks burn including final active tick")
			check.call(hero.burn_timer == row.burn_timer, "Blocked burn still consumes duration")
			check.call(hero.burn_accum == row.burn_accum, "Blocked burn still consumes accumulator")
			check.call(hero.shadow_realm_timer == row.realm, "Realm expires after debuff damage")
			moment += 1
	check.call(moment == fixture.burn.size(), "All source burn/realm boundaries checked")
