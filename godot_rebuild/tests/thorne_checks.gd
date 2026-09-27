extends RefCounted
## Real source ThorneSkills vs native hero/world combat. No presentation/item claims.

const Battle = preload("res://scripts/combat/minion_battle.gd")
const World = preload("res://scripts/match/prototype_battle.gd")
const Definition = preload("res://scripts/data/minion_definition.gd")
const ThorneSkills = preload("res://scripts/combat/thorne_skills.gd")
const THORNE = preload("res://data/heroes/thorne.tres")
const GOBLIN = preload("res://data/minions/goblin.tres")
const FIXTURE := "res://tests/fixtures/thorne_source.json"


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	for row in fixture.skills:
		_skill(row, check)
	for row in fixture.reflect:
		_reflect(row, check)
	for row in fixture.timers:
		_timer(row, check)
	_respawn(fixture.respawn, check)
	_guards(check)


func _world() -> Battle:
	return Battle.new()


func _thorne(world: Battle) -> Battle.HeroState:
	return world.spawn_hero(THORNE, world.RED, Vector2(500, 340))


func _beef(world: Battle, x: int, y: int) -> Battle.UnitState:
	# Minion tick clamps to definition.max_hp; hp alone is not sufficient.
	var copy := GOBLIN.duplicate() as Definition
	copy.max_hp = 10000
	var unit := world.spawn_unit(copy, world.BLUE, 1)
	unit.position = Vector2(x, y)
	unit.hp = 10000
	return unit


func _cast(world: Battle, hero_id: int, key: String) -> bool:
	match key:
		"q":
			return world.cast_hero_q(hero_id)
		"w":
			return world.cast_hero_w(hero_id)
		"e":
			return world.cast_hero_e(hero_id)
		"r":
			return world._cast_hero_r(hero_id)
	return false


func _skill(row: Dictionary, check: Callable) -> void:
	var world := _world()
	var hero := _thorne(world)
	hero.hp = 1000
	var enemies: Array = []
	if row.with_enemies:
		for point in row.positions:
			enemies.append(_beef(world, int(point[0]), int(point[1])))
	check.call(_cast(world, hero.id, row.skill) == row.success, "Thorne skill result")
	check.call(_cast(world, hero.id, row.skill) == row.repeat, "Thorne skill cooldown repeat")
	for pair in [
		["hp", "hp"],
		["damage", "damage"],
		["attack_cd_base", "attack_cd"],
		["skill_timer", "skill_timer"],
		["w_cooldown", "w_cooldown"],
		["e_cooldown", "e_cooldown"],
		["r_cooldown", "r_cooldown"],
		["active_skill", "active_skill"],
		["active_skill_timer", "active_timer"],
		["viscous_timer", "viscous"],
		["bristleback_timer", "bristleback"],
		["quill_timer", "quill"],
		["warpath_timer", "warpath"]
	]:
		check.call(hero.get(pair[0]) == row[pair[1]], "Thorne skill state " + pair[0])
	for index in range(enemies.size()):
		var expected: Dictionary = row.enemies[index]
		check.call(enemies[index].hp == expected.hp, "Thorne damage/cone/radius parity")
		check.call(
			(
				enemies[index].slow_amount == expected.slow
				and enemies[index].slow_timer == expected.slow_timer
			),
			"Thorne Q slow only on targets in cone"
		)


func _reflect(row: Dictionary, check: Callable) -> void:
	var world := _world()
	var hero := _thorne(world)
	hero.hp = 1000
	var attacker := _beef(world, 450, 340)
	if row.active:
		check.call(world.cast_hero_w(hero.id), "Thorne W activates before damage")
	check.call(hero.hp == row.before, "Thorne W heal source")
	world._deliver_hit(attacker.id, attacker.team, hero, 100, row.school, attacker.position)
	check.call(hero.hp == row.hp, "Thorne W physical/magic mitigation")
	check.call(attacker.hp == row.attacker_hp, "Thorne W reflects post-mitigation once")
	check.call(hero.bristleback_timer == row.bristleback, "Thorne W clock unchanged by hit")


func _timer(row: Dictionary, check: Callable) -> void:
	var world := _world()
	var hero := _thorne(world)
	_beef(world, 450, 340)
	var key: String = row.mode.substr(0, 1)
	check.call(_cast(world, hero.id, key), "Thorne timed buff activates")
	var total := 240 if key == "w" else 300
	if row.mode == "r_upgrade":
		for index in range(120):
			world._tick_hero(hero)
		check.call(hero.upgrade(), "Thorne upgrades during Warpath")
		total -= 120
	for index in range(total - 1):
		world._tick_hero(hero)
	_compare_timer(hero, row.before, check)
	world._tick_hero(hero)
	_compare_timer(hero, row.after, check)


func _compare_timer(hero: Battle.HeroState, state: Dictionary, check: Callable) -> void:
	check.call(hero.bristleback_timer == state.bristleback, "Thorne W expiry")
	check.call(hero.warpath_timer == state.warpath, "Thorne R expiry")
	check.call(
		hero.damage == state.damage and hero.attack_cd_base == state.attack_cd,
		"Thorne R restores current-level damage and original CD"
	)
	check.call(hero.level == state.level, "Thorne R upgrade remains")


func _guards(check: Callable) -> void:
	var world := _world()
	var hero := _thorne(world)
	check.call(
		not world.cast_hero_q(hero.id) and not world.cast_hero_e(hero.id),
		"Thorne offensive skills need target"
	)
	check.call(not world._cast_hero_r(hero.id), "Thorne ultimate needs target")
	hero.alive = false
	check.call(not world.cast_hero_w(hero.id), "Dead Thorne cannot buff")
	check.call(
		THORNE.damage == 41 and THORNE.attack_cooldown_ticks == 35,
		"Thorne buff never mutates shared resource"
	)


func _respawn(state: Dictionary, check: Callable) -> void:
	var world := World.new()
	var hero := world.spawn_hero(THORNE, world.RED, Vector2(500, 340))
	hero.alive = false
	hero.hp = 0
	hero.respawn_timer = 1
	hero.w_cooldown = 123
	hero.e_cooldown = 77
	hero.r_cooldown = 321
	hero.skill_timer = 88
	hero.active_skill = "r"
	hero.active_skill_timer = 60
	world._step_hero_respawn(hero)
	check.call(hero.position == Vector2(state.x, state.y), "Thorne source respawn point")
	check.call(hero.alive == state.alive and hero.hp == state.hp, "Thorne source respawn HP")
	check.call(
		hero.w_cooldown == state.w and hero.e_cooldown == state.e and hero.r_cooldown == state.r,
		"Thorne source respawn keeps W/E/R cooldown"
	)
	check.call(
		(
			hero.skill_timer == state.q
			and hero.active_skill == state.active
			and hero.active_skill_timer == state.visual
		),
		"Thorne source respawn clears Q/visual"
	)
