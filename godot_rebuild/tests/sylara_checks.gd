extends RefCounted
## Source Hero/SylaraSkills executed fixtures against native combat, not receipts.

const Battle = preload("res://scripts/combat/minion_battle.gd")
const Definition = preload("res://scripts/data/minion_definition.gd")
const SYLARA = preload("res://data/heroes/sylara.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const GOBLIN = preload("res://data/minions/goblin.tres")
const FIXTURE := "res://tests/fixtures/sylara_source.json"


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	for row in fixture.casts:
		_cast(row, check)
	for key in ["q", "w", "e", "r"]:
		_ticks(key, fixture.ticks[key], check)
	for row in fixture.windrun:
		_windrun(row, check)
	_projectiles(fixture.projectiles, check)
	_guards(check)


func _world() -> Battle:
	return Battle.new()


func _hero(world: Battle) -> Battle.HeroState:
	return world.spawn_hero(SYLARA, world.RED, Vector2(500, 340))


func _dummy(world: Battle, pos: Vector2, team: int = Battle.BLUE) -> Battle.UnitState:
	var copy := GOBLIN.duplicate() as Definition
	copy.max_hp = 10000
	var unit := world.spawn_unit(copy, team, 1)
	unit.position = pos
	unit.hp = 10000
	return unit


func _skill(world: Battle, id: int, key: String) -> bool:
	match key:
		"q":
			return world.cast_hero_q(id)
		"w":
			return world.cast_hero_w(id)
		"e":
			return world.cast_hero_e(id)
		"r":
			return world._cast_hero_r(id)
	return false


func _compare(
	hero: Battle.HeroState,
	enemies: Array,
	state: Dictionary,
	check: Callable,
	label: String,
	timed := false
) -> void:
	for pair in [
		["hp", "hp"],
		["speed", "speed"],
		["attack_cd_base", "attack_cd"],
		["focus_fire_timer", "focus"],
		["windrun_timer", "windrun"],
		["shackle_timer", "shackle"],
		["powershot_timer", "powershot"]
	]:
		check.call(hero.get(pair[0]) == state[pair[1]], label + " " + pair[0])
	check.call((hero.shackle_target_id >= 0) == state.bound, label + " bound target")
	for index in range(enemies.size()):
		check.call(enemies[index].hp == state.enemies[index].hp, label + " hit HP")
		check.call(
			enemies[index].cooldown_ticks == state.enemies[index].attack_timer,
			label + " stun clock"
		)
	if timed:
		return
	for pair in [
		["skill_timer", "q"],
		["w_cooldown", "w"],
		["e_cooldown", "e"],
		["r_cooldown", "r"],
		["active_skill", "active"],
		["active_skill_timer", "visual"]
	]:
		check.call(hero.get(pair[0]) == state[pair[1]], label + " " + pair[0])


func _cast(row: Dictionary, check: Callable) -> void:
	var world := _world()
	var hero := _hero(world)
	var enemies: Array = []
	if row.key != "e_boundary":
		hero.hp = 500
		if row.populated:
			for position in row.positions:
				enemies.append(_dummy(world, Vector2(position[0], position[1])))
			hero.target_id = enemies[0].id
		check.call(
			_skill(world, hero.id, row.key) == row.success, "Sylara cast target/cooldown gate"
		)
		check.call(_skill(world, hero.id, row.key) == row.repeat, "Sylara duplicate cast gate")
	else:
		enemies.append(_dummy(world, Vector2(500 + int(row.radius), 340)))
		check.call(_skill(world, hero.id, "e") == row.success, "Sylara Shackle 200px source gate")
	_compare(hero, enemies, row.state, check, "Sylara " + row.key)


func _ticks(key: String, rows: Array, check: Callable) -> void:
	var world := _world()
	var hero := _hero(world)
	var enemies := [
		_dummy(world, Vector2(620, 340)),
		_dummy(world, Vector2(760, 340)),
		_dummy(world, Vector2(650, 365))
	]
	hero.target_id = enemies[0].id
	check.call(_skill(world, hero.id, key), "Sylara buff/channel starts")
	var length := 150 if key == "e" else (60 if key == "r" else 180)
	var moment := 0
	for tick in range(1, length + 1):
		world._tick_hero(hero)
		if moment < rows.size() and tick == rows[moment].tick:
			_compare(
				hero,
				enemies,
				rows[moment].state,
				check,
				"Sylara " + key + " tick " + str(tick),
				true
			)
			moment += 1
	check.call(moment == rows.size(), "All Sylara source tick boundaries checked")


func _windrun(row: Dictionary, check: Callable) -> void:
	var world := _world()
	var hero := _hero(world)
	var attacker := _dummy(world, Vector2(560, 340))
	hero.hp = 500
	check.call(world.cast_hero_w(hero.id), "Windrun without target")
	var roll := float(row.roll)
	world.windrun_roll_override = func() -> float: return roll
	world._deliver_hit(attacker.id, attacker.team, hero, 80, row.school, attacker.position)
	check.call(hero.hp == row.hp, "Sylara physical 75% dodge boundary / magic bypass")


func _projectiles(rows: Array, check: Callable) -> void:
	var world := _world()
	var hero := _hero(world)
	var enemy := _dummy(world, Vector2(620, 340))
	check.call(world.hero_basic_attack(hero.id, enemy.id), "Sylara ranged basic fires")
	var moment := 0
	for tick in range(0, 17):
		if tick == 2:
			enemy.position.y = 360
		if tick > 0:
			world._tick_hero(hero)
		if moment < rows.size() and tick == rows[moment].tick:
			var state: Dictionary = rows[moment]
			check.call(enemy.hp == state.hp, "Arrow damages only on impact")
			check.call(world.hero_projectiles.size() == state.count, "Arrow flight/cleanup")
			if state.count > 0 and not world.hero_projectiles.is_empty():
				var pos: Vector2 = world.hero_projectiles[0].position
				check.call(
					pos.distance_to(Vector2(state.positions[0][0], state.positions[0][1])) < 0.002,
					"Original Hero.update homing trajectory"
				)
			moment += 1
	check.call(moment == rows.size(), "All real projectile source frames checked")


func _guards(check: Callable) -> void:
	var world := _world()
	var hero := _hero(world)
	check.call(
		not world.cast_hero_q(hero.id) and not world.cast_hero_e(hero.id), "Offense needs enemy"
	)
	check.call(not world._cast_hero_r(hero.id), "Powershot needs target to charge")
	var blue := world.spawn_hero(KAIZEN, world.BLUE, Vector2(610, 340))
	check.call(world.cast_hero_w(blue.id), "Kaizen wind wall cast for arrow test")
	check.call(world.hero_basic_attack(hero.id, blue.id), "Arrow can target Kaizen")
	for tick in range(15):
		world._tick_hero(hero)
	check.call(blue.hp == blue.max_hp, "Kaizen wind wall blocks physical Sylara projectile")
	check.call(SYLARA.cost == 380 and SYLARA.damage == 57, "Sylara shared definition untouched")
