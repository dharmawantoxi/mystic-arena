extends RefCounted
## Exact original Grimjaw skill receipts, modulo clocks, ward and repeatable crit.

const Battle = preload("res://scripts/combat/minion_battle.gd")
const World = preload("res://scripts/match/prototype_battle.gd")
const Definition = preload("res://scripts/data/minion_definition.gd")
const HeroMarker = preload("res://scripts/ui/hero_marker.gd")
const GRIMJAW = preload("res://data/heroes/grimjaw.tres")
const GOBLIN = preload("res://data/minions/goblin.tres")
const FIXTURE := "res://tests/fixtures/grimjaw_source.json"
const STATS := "res://data/ai/hero_combat_stats.json"


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	for row in fixture.casts:
		_cast(row, check)
	for key in ["q", "r"]:
		_trace(key, fixture.traces[key], check)
	_ward(fixture.traces.w, check)
	_crit(fixture.crit_attacks, check)
	_markers(check)
	_guards(check)


func _world() -> Battle:
	return Battle.new()


func _hero(world: Battle) -> Battle.HeroState:
	return world.spawn_hero(GRIMJAW, world.RED, Vector2(500, 340))


func _dummy(world: Battle, team: int, x: int, y: int) -> Battle.UnitState:
	# Real minion tick clamps HP to max_hp: duplicate the shared definition.
	var copy := GOBLIN.duplicate() as Definition
	copy.max_hp = 10000
	var unit := world.spawn_unit(copy, team, 1)
	unit.position = Vector2(x, y)
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


func _state(
	hero: Battle.HeroState,
	enemies: Array,
	state: Dictionary,
	check: Callable,
	label: String,
	only_effects := false
) -> void:
	check.call(hero.hp == state.hp, label + " HP")
	check.call(hero.blade_fury_timer == state.spin, label + " spin")
	check.call(hero.heal_ward_timer == state.ward, label + " ward")
	check.call(hero.grimjaw_crit_timer == state.crit, label + " crit")
	check.call(hero.omnislash_timer == state.slash, label + " slash")
	check.call((hero.omnislash_target_id >= 0) == state.locked, label + " locked target")
	for index in range(enemies.size()):
		check.call(enemies[index].hp == state.enemies[index], label + " enemy HP")
	if only_effects:
		return
	for pair in [
		["damage", "damage"],
		["attack_timer", "attack_timer"],
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
	hero.hp = 900
	var enemies: Array = []
	if row.with_enemies:
		for pos in row.positions:
			enemies.append(_dummy(world, world.BLUE, int(pos[0]), int(pos[1])))
	check.call(_skill(world, hero.id, row.key) == row.success, "Grimjaw cast target gate")
	check.call(_skill(world, hero.id, row.key) == row.repeat, "Grimjaw cooldown gate")
	_state(hero, enemies, row.state, check, "Grimjaw " + row.key)


func _trace(key: String, rows: Array, check: Callable) -> void:
	var world := _world()
	var hero := _hero(world)
	var enemies := [_dummy(world, world.BLUE, 450, 340), _dummy(world, world.BLUE, 600, 340)]
	check.call(_skill(world, hero.id, key), "Grimjaw timed skill cast")
	var moment := 0
	var final_tick := 180 if key == "q" else 90
	for tick in range(1, final_tick + 1):
		world._tick_hero(hero)
		if moment < rows.size() and tick == rows[moment].tick:
			_state(
				hero,
				enemies,
				rows[moment].state,
				check,
				"Grimjaw " + key + " tick " + str(tick),
				true
			)
			moment += 1
	check.call(moment == rows.size(), "All Grimjaw source modulo boundaries compared")


func _ward(rows: Array, check: Callable) -> void:
	var world := _world()
	var hero := _hero(world)
	hero.hp = 900
	var near := _dummy(world, world.RED, 540, 340)
	var far := _dummy(world, world.RED, 620, 340)
	near.hp = 9990
	far.hp = 9990
	check.call(world.cast_hero_w(hero.id), "Grimjaw W works without enemies")
	var moment := 0
	for tick in range(1, 361):
		if tick == 2:
			hero.position.x = 610
		world._tick_hero(hero)
		if moment < rows.size() and tick == rows[moment].tick:
			var state: Dictionary = rows[moment]
			check.call(hero.hp == state.hp, "Grimjaw ward heals hero only within 100px")
			check.call(near.hp == state.near and far.hp == state.far, "Ward heals nearby ally only")
			check.call(hero.heal_ward_timer == state.ward, "Ward 360 tick lifetime")
			check.call(
				hero.heal_ward_position == Vector2(state.ward_pos[0], state.ward_pos[1]),
				"Ward fixed at cast location"
			)
			moment += 1
	check.call(moment == rows.size(), "All Grimjaw source ward boundaries compared")


func _crit(states: Dictionary, check: Callable) -> void:
	var world := _world()
	var hero := _hero(world)
	var enemy := _dummy(world, world.BLUE, 450, 340)
	check.call(world.cast_hero_e(hero.id), "Grimjaw E grants crit and radial damage")
	_state(hero, [enemy], states.before, check, "Grimjaw crit before")
	check.call(world.hero_basic_attack(hero.id, enemy.id), "Grimjaw first crit")
	_state(hero, [enemy], states.first, check, "Grimjaw first crit")
	hero.attack_timer = 0
	check.call(world.hero_basic_attack(hero.id, enemy.id), "Grimjaw second crit")
	_state(hero, [enemy], states.second, check, "Grimjaw buff persists after hit")
	for index in range(300):
		world._tick_hero(hero)
	hero.attack_timer = 0
	check.call(world.hero_basic_attack(hero.id, enemy.id), "Grimjaw normal attack after expiry")
	_state(hero, [enemy], states.after, check, "Grimjaw crit expiry", true)


func _markers(check: Callable) -> void:
	var stats: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(STATS))
	check.call(stats.size() == 222, "All hero IDs get temporary procedural markers")
	for kind in stats:
		var points := HeroMarker.body(Vector2(10, 20), 16, kind)
		check.call(points.size() >= 4 and points.size() <= 6, "Hero marker geometry without assets")
		check.call(points == HeroMarker.body(Vector2(10, 20), 16, kind), "Hero marker is stable")
		var fill := HeroMarker.fill(kind)
		check.call(fill == HeroMarker.fill(kind), "Hero color is stable")
		check.call(fill.a == 1.0, "Temporary hero marker is opaque")
	check.call(
		HeroMarker.fill("kaizen") != HeroMarker.fill("thorne"),
		"Starter silhouettes have distinct fill"
	)
	check.call(
		HeroMarker.fill("thorne") != HeroMarker.fill("grimjaw"), "Next starter has distinct fill"
	)


func _guards(check: Callable) -> void:
	var world := _world()
	var hero := _hero(world)
	check.call(
		(
			not world.cast_hero_q(hero.id)
			and not world.cast_hero_e(hero.id)
			and not world._cast_hero_r(hero.id)
		),
		"Offense needs living enemy"
	)
	hero.alive = false
	check.call(not world.cast_hero_w(hero.id), "Dead Grimjaw cannot place a ward")
	check.call(GRIMJAW.damage == 42 and GRIMJAW.cost == 450, "No shared definition mutation")
