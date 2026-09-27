extends RefCounted
## Vex and Zephyr behavioral fixtures, executed against real native combat.
const Battle = preload("res://scripts/combat/minion_battle.gd")
const World = preload("res://scripts/match/prototype_battle.gd")
const Helpers = preload("res://tests/sylara_checks.gd")
const VEX = preload("res://data/heroes/vex.tres")
const ZEPHYR = preload("res://data/heroes/zephyr.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const FIXTURE := "res://tests/fixtures/starter_finish_source.json"
var helpers := Helpers.new()


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	for row in fixture.casts:
		_cast(row, check)
	for row in fixture.traces:
		_trace(row, check)
	for row in fixture.defense:
		_defense(row, check)
	for row in fixture.attacks:
		_attack(row, check)
	for row in fixture.respawn:
		_respawn(row, check)
	_guards(check)


func _hero(world: Battle, kind: String) -> Battle.HeroState:
	return world.spawn_hero(VEX if kind == "vex" else ZEPHYR, world.RED, Vector2(500, 340))


func _enemies(world: Battle, positions: Array) -> Array:
	var result := []
	for pos in positions:
		result.append(helpers._dummy(world, Vector2(pos[0], pos[1])))
	return result


func _compare(hero, enemies: Array, expected: Dictionary, check: Callable, label: String) -> void:
	for key in expected:
		if key == "enemies":
			for index in range(enemies.size()):
				for field in expected.enemies[index]:
					check.call(
						enemies[index].get(field) == expected.enemies[index][field],
						label + " target " + str(index) + " " + field
					)
		elif (
			key
			in [
				"position",
				"bramble_origin",
				"blink_from",
				"mana_void_origin",
				"alchemy_target",
				"vortex",
				"w_dir",
				"r_dir"
			]
		):
			check.call(
				hero.get(key) == Vector2(expected[key][0], expected[key][1]), label + " " + key
			)
		elif key in ["prison_target_id", "curse_target_id", "flux_target_id", "target_id"]:
			var target := int(expected[key])
			check.call(
				hero.get(key) == (-1 if target < 0 else enemies[target].id), label + " " + key
			)
		else:
			check.call(hero.get(key) == expected[key], label + " " + key)


func _cast(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	hero.hp = 500
	var enemies := _enemies(world, row.positions)
	if row.target >= 0:
		hero.target_id = enemies[int(row.target)].id
	check.call(helpers._skill(world, hero.id, row.key) == row.ok, row.hero + " cast " + row.key)
	check.call(helpers._skill(world, hero.id, row.key) == row.repeat, row.hero + " duplicate cast")
	_compare(hero, enemies, row.state, check, row.hero + " " + row.key)


func _trace(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	hero.hp = 500
	var enemies := _enemies(world, row.positions)
	hero.target_id = enemies[0].id
	enemies[0].cooldown_ticks = 90
	check.call(helpers._skill(world, hero.id, row.key), "Starter timer cast")
	var moment := 0
	for tick in range(1, int(row.get("length", 241)) + 1):
		if tick == 2 and row.mode == "move_upgrade":
			hero.position.x += 100
			enemies[0].position.x += 200
			check.call(hero.upgrade(), "Upgrade during starter effect")
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
	check.call(moment == row.rows.size(), "All starter source trace moments compared")


func _defense(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, "zephyr")
	hero.hp = 300
	check.call(world.cast_hero_w(hero.id), "Shadow Realm has no target gate")
	for tick in range(int(row.tick)):
		world._tick_hero(hero)
	check.call(hero.hp == row.before, "Shadow Realm heal/cap/end tick")
	world._deliver_hit(-1, world.BLUE, hero, 100, row.school, Vector2.ZERO)
	check.call(hero.hp == row.hp, "Shadow Realm physical AND magic immunity/end")


func _attack(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	var target_point: Array = row.get("target_position", [620, 340])
	var enemy = helpers._dummy(world, Vector2(target_point[0], target_point[1]))
	check.call(world.hero_basic_attack(hero.id, enemy.id), "Starter magic homing attack")
	for moment in row.rows:
		if moment.tick > 0:
			world._tick_hero(hero)
		check.call(enemy.hp == moment.hp, "Starter projectile source impact")
		check.call(hero.attack_timer == moment.attack_timer, "Starter source attack cooldown")
		check.call(
			world.hero_projectiles.size() == moment.positions.size(), "Source arrow lifecycle"
		)
		for index in range(mini(world.hero_projectiles.size(), moment.positions.size())):
			var point: Array = moment.positions[index]
			check.call(
				(
					world.hero_projectiles[index].position.distance_to(Vector2(point[0], point[1]))
					< 0.002
				),
				"Source magic homing trajectory"
			)


func _respawn(row: Dictionary, check: Callable) -> void:
	var world := World.new()
	var hero := _hero(world, row.hero)
	var enemies := _enemies(world, [[550, 340]])
	for key in ["q", "w", "e", "r"]:
		check.call(helpers._skill(world, hero.id, key), "Pre-death kit activation")
	hero.attack_timer = 17
	hero.hp = 0
	hero.alive = false
	hero.respawn_timer = 1
	world._step_hero_respawn(hero)
	_compare(hero, enemies, row.state, check, row.hero + " source respawn")


func _guards(check: Callable) -> void:
	for kind in ["vex", "zephyr"]:
		var world := Battle.new()
		var hero := _hero(world, kind)
		var other := _hero(world, kind)
		var blue := world.spawn_hero(KAIZEN, world.BLUE, Vector2(610, 340))
		check.call(world.cast_hero_w(blue.id), "Existing Kaizen wall")
		check.call(world.hero_basic_attack(hero.id, blue.id), "Magic arrow launch")
		for tick in range(15):
			world._tick_hero(hero)
		check.call(blue.hp < blue.max_hp, "Magic arrows bypass physical wall")
		check.call(other.attack_timer == 0, "Starter instance isolation")
		hero.alive = false
		for key in ["q", "w", "e", "r"]:
			check.call(not helpers._skill(world, hero.id, key), "Dead starter cannot cast")


func _levels(kind: String, rows: Array, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, kind)
	hero.hp = 1
	if hero.settings().is_boss_hero:
		_paid_upgrade(kind, int(rows[0].price), check)
	for row in rows:
		for key in ["hp", "level", "damage", "max_hp", "skill_value"]:
			check.call(hero.get(key) == row[key], kind + " source level " + str(row.level) + key)
		check.call(hero.upgrade_cost() == row.price, kind + " source upgrade price")
		check.call(hero.upgrade() == (row.level < 15), kind + " source upgrade cap")


func _paid_upgrade(kind: String, price: int, check: Callable) -> void:
	for delta in [-1, 0, 1]:
		for alive in [false, true]:
			var world := World.new()
			var hero := _hero(world, kind)
			hero.hp = 1 if alive else 0
			hero.alive = alive
			hero.skill_timer = 29
			hero.respawn_timer = 17
			var gold: int = price + 400 + delta
			world.economy.opening[1] = gold
			world.economy.gold[1] = gold
			var success := world._upgrade_hero_for(world.RED, hero.id, 1, 400)
			check.call(success == (delta >= 0), kind + " source upgrade price + reserve boundary")
			check.call(
				world.economy.gold[1] == gold - (price if success else 0),
				kind + " exact boss upgrade debit"
			)
			check.call(world.economy.is_balanced(), kind + " boss upgrade ledger")
			check.call(hero.level == (2 if success else 1), kind + " boss upgrade level")
			check.call(
				hero.hp == (1 if alive else 0) and hero.alive == alive, "Upgrade never revives"
			)
			check.call(
				hero.skill_timer == 29 and hero.respawn_timer == 17, "Upgrade retains clocks"
			)
