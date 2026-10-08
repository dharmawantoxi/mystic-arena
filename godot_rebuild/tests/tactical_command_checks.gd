extends RefCounted
## Domain parity for tactical_commands.py. Every command/lifecycle case is
## driven by the checked-in fixture produced from the read-only Python manager.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const GOBLIN = preload("res://data/minions/goblin.tres")
const FIXTURE := "res://tests/fixtures/tactical_command_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary, "Tactical source fixture parses")
	if not fixture is Dictionary:
		return
	_check_policy(check, fixture.policy)
	_gather_explicit(check, fixture)
	_protect_most_threatened(check, fixture)
	_protect_castle(check, fixture)
	_attack_boss(check, fixture)
	_attack_damage_dealer(check, fixture)
	_quick_tap(check, fixture)
	_long_hold_release(check, fixture)
	_armed_boss_hold(check, fixture)
	_held_gather_push(check, fixture)
	_auto_protect_castle(check, fixture)
	_damage_attribution(check)


func _check_policy(check: Callable, expected: Dictionary) -> void:
	var tactical = Prototype.new().tactical
	check.call(tactical.COMMAND_TICKS == int(expected.duration), "Tactical duration matches source")
	check.call(
		tactical.COOLDOWN_TICKS == int(expected.cooldown), "Tactical cooldown matches source"
	)
	check.call(
		tactical.HOLD_TAP_MAX_TICKS == int(expected.hold_tap_max),
		"Tactical tap threshold matches source"
	)
	check.call(
		tactical.HOLD_RELEASE_TAIL == int(expected.hold_release_tail),
		"Tactical hold release tail matches source"
	)
	check.call(
		tactical.GATHER_PUSH_DELAY_TICKS == int(expected.gather_push_delay),
		"Tactical gather push delay matches source"
	)
	check.call(tactical.COMMANDS == expected.commands, "All five source tactical commands exist")


func _gather_explicit(check: Callable, fixture: Dictionary) -> void:
	var world := _world_with_heroes(4)
	var heroes := _prepare_heroes(world, [[100, 200], [200, 220], [300, 240], [400, 260]])
	var labels := _hero_labels(heroes)
	var accepted := world.tactical.issue(world, "gather", Vector2(640, 360), true, -1, -1, true)
	_assert_case(check, "gather_explicit", fixture, world, heroes, labels, accepted)


func _protect_most_threatened(check: Callable, fixture: Dictionary) -> void:
	var world := _world_with_heroes(5)
	var heroes := _prepare_heroes(
		world, [[250, 300], [280, 300], [500, 500], [800, 600], [1000, 100]]
	)
	var labels := _hero_labels(heroes)
	var threatened = world.spawn_structure(ARCHER, world.BLUE, Vector2(300, 300), 1)
	threatened.hp = threatened.definition.max_hp * 0.5
	labels[threatened.id] = "outer_tower"
	var safe = world.spawn_structure(ARCHER, world.BLUE, Vector2(800, 500), 1)
	labels[safe.id] = "inner_tower"
	for point in [Vector2(320, 300), Vector2(330, 310)]:
		var minion = world.spawn_unit(GOBLIN, world.RED, 1)
		minion.position = point
	var boss = world._spawn_boss("gornak")
	boss.position = Vector2(350, 300)
	boss.entrance_timer = 0
	labels[boss.id] = "boss"
	var accepted := world.tactical.issue(world, "protect_tower", Vector2.ZERO, false, -1, -1, true)
	_assert_case(check, "protect_most_threatened", fixture, world, heroes, labels, accepted)


func _protect_castle(check: Callable, fixture: Dictionary) -> void:
	var world := _world_with_heroes(4)
	var heroes := _prepare_heroes(world, [[100, 200], [200, 220], [300, 240], [400, 260]])
	world.nexuses[world.BLUE].position = Vector2(100, 620)
	var labels := _hero_labels(heroes)
	labels[world.nexuses[world.BLUE].id] = "blue_castle"
	var accepted := world.tactical.issue(world, "protect_castle", Vector2.ZERO, false, -1, -1, true)
	_assert_case(check, "protect_castle", fixture, world, heroes, labels, accepted)


func _attack_boss(check: Callable, fixture: Dictionary) -> void:
	var world := _world_with_heroes(3)
	var heroes := _prepare_heroes(world, [[100, 200], [200, 220], [300, 240]])
	var boss = world._spawn_boss("gornak")
	boss.position = Vector2(700, 300)
	boss.entrance_timer = 0
	var labels := _hero_labels(heroes)
	labels[boss.id] = "boss"
	var accepted := world.tactical.issue(world, "attack_boss", Vector2.ZERO, false, -1, -1, true)
	_assert_case(check, "attack_boss", fixture, world, heroes, labels, accepted)


func _attack_damage_dealer(check: Callable, fixture: Dictionary) -> void:
	var world := _world_with_heroes(3)
	var heroes := _prepare_heroes(world, [[100, 200], [200, 220], [300, 240]])
	var red := _free_red_hero(world)
	red.position = Vector2(750, 250)
	red.damage_dealt = 125
	world.ai_hero_ids.append(red.id)
	var high: HeroState = world.spawn_hero(KAIZEN, world.RED, Vector2(800, 300))
	high.damage_dealt = 900
	world.ai_hero_ids.append(high.id)
	var dead: HeroState = world.spawn_hero(KAIZEN, world.RED, Vector2(810, 320))
	dead.damage_dealt = 5000
	dead.alive = false
	world.ai_hero_ids.append(dead.id)
	var labels := _hero_labels(heroes)
	labels[red.id] = "dealer_low"
	labels[high.id] = "dealer_high"
	labels[dead.id] = "dealer_dead"
	var accepted := world.tactical.issue(
		world, "attack_damage_dealer", Vector2.ZERO, false, -1, -1, true
	)
	_assert_case(check, "attack_damage_dealer", fixture, world, heroes, labels, accepted)


func _quick_tap(check: Callable, fixture: Dictionary) -> void:
	var world := _world_with_heroes(2)
	var heroes := _prepare_heroes(world, [[100, 200], [200, 220]])
	var labels := _hero_labels(heroes)
	var accepted := world.tactical.hold_start(world, "gather", Vector2(600, 350), true)
	for tick in range(5):
		world.tactical.step_tick(world)
	world.tactical.hold_end("gather")
	_assert_case(check, "quick_tap_keeps_duration", fixture, world, heroes, labels, accepted)


func _long_hold_release(check: Callable, fixture: Dictionary) -> void:
	var world := _world_with_heroes(2)
	var heroes := _prepare_heroes(world, [[100, 200], [200, 220]])
	world.nexuses[world.BLUE].position = Vector2(100, 620)
	var labels := _hero_labels(heroes)
	labels[world.nexuses[world.BLUE].id] = "blue_castle"
	var accepted := world.tactical.hold_start(world, "protect_castle")
	for tick in range(35):
		world.tactical.step_tick(world)
	world.tactical.hold_end("protect_castle")
	_assert_case(check, "long_hold_release_tail", fixture, world, heroes, labels, accepted)


func _armed_boss_hold(check: Callable, fixture: Dictionary) -> void:
	var world := _world_with_heroes(2)
	var heroes := _prepare_heroes(world, [[100, 200], [200, 220]])
	var labels := _hero_labels(heroes)
	var accepted := world.tactical.hold_start(world, "attack_boss")
	for tick in range(10):
		world.tactical.step_tick(world)
	var boss = world._spawn_boss("gornak")
	boss.position = Vector2(700, 300)
	boss.entrance_timer = 0
	boss.display_name = "late_boss"
	labels[boss.id] = "late_boss"
	for tick in range(5):
		world.tactical.step_tick(world)
	_assert_case(check, "armed_hold_waits_for_boss", fixture, world, heroes, labels, accepted)


func _held_gather_push(check: Callable, fixture: Dictionary) -> void:
	var world := _world_with_heroes(3)
	var heroes := _prepare_heroes(world, [[640, 360], [650, 360], [630, 360]])
	var labels := _hero_labels(heroes)
	var boss = world._spawn_boss("gornak")
	boss.position = Vector2(700, 360)
	boss.entrance_timer = 0
	labels[boss.id] = "far_boss"
	var tower = world.spawn_structure(ARCHER, world.RED, Vector2(665, 360), 1)
	labels[tower.id] = "near_tower"
	var enemy := _free_red_hero(world)
	enemy.position = Vector2(680, 360)
	enemy.damage_dealt = 20
	world.ai_hero_ids.append(enemy.id)
	labels[enemy.id] = "enemy_hero"
	var accepted := world.tactical.hold_start(world, "gather", Vector2(640, 360), true)
	for tick in range(240):
		world.tactical.step_tick(world)
	_assert_case(check, "held_gather_push", fixture, world, heroes, labels, accepted)


func _auto_protect_castle(check: Callable, fixture: Dictionary) -> void:
	var world := _world_with_heroes(3)
	var heroes := _prepare_heroes(world, [[100, 200], [200, 220], [300, 240]])
	var castle = world.nexuses[world.BLUE]
	castle.position = Vector2(100, 620)
	castle.hp = castle.definition.max_hp * 0.3
	var labels := _hero_labels(heroes)
	labels[castle.id] = "blue_castle"
	for point in [Vector2(120, 600), Vector2(140, 610)]:
		var minion = world.spawn_unit(GOBLIN, world.RED, 1)
		minion.position = point
	world.tactical.auto_check_timer = 89
	world.tactical.step_tick(world)
	_assert_case(check, "auto_protect_castle", fixture, world, heroes, labels, true)


func _damage_attribution(check: Callable) -> void:
	var world := _world_with_heroes(1)
	var hero: HeroState = world.player_roster()[0]
	var victim = world.spawn_unit(GOBLIN, world.RED, 1)
	victim.position = hero.position + Vector2(5, 0)
	check.call(
		world._deliver_hit(hero.id, hero.team, victim, 17, "neutral", hero.position),
		"Tactical dealer accounting uses the authoritative non-boss hit path"
	)
	check.call(hero.damage_dealt == 17, "Hero receives post-mitigation non-boss damage credit")
	check.call(
		world._deliver_hit(hero.id, hero.team, victim, 100, "neutral", hero.position),
		"Overkill hit is delivered"
	)
	check.call(
		hero.damage_dealt == 117, "Damage credit is post-mitigation amount, not remaining-HP loss"
	)
	var boss = world._spawn_boss("gornak")
	boss.position = hero.position + Vector2(5, 0)
	boss.entrance_timer = 0
	var before_hp: float = boss.hp
	var before_credit := hero.damage_dealt
	check.call(
		world._deliver_hit(hero.id, hero.team, boss, 50, "neutral", hero.position),
		"Tactical dealer accounting uses the boss hit branch"
	)
	check.call(
		hero.damage_dealt - before_credit == int(before_hp - boss.hp),
		"Boss damage credits the known attacking hero after mitigation"
	)


func _assert_case(
	check: Callable,
	label: String,
	fixture: Dictionary,
	world: Prototype,
	heroes: Array,
	labels: Dictionary,
	accepted: bool
) -> void:
	var expected := _case(fixture, label)
	check.call(not expected.is_empty(), "Tactical fixture contains %s" % label)
	if expected.is_empty():
		return
	var state: Dictionary = expected.state
	check.call(accepted == bool(expected.accepted), "%s acceptance matches source" % label)
	check.call(
		world.tactical.active_command == state.active, "%s active command matches source" % label
	)
	check.call(world.tactical.command_timer == int(state.timer), "%s timer matches source" % label)
	check.call(world.tactical.cooldown == int(state.cooldown), "%s cooldown matches source" % label)
	check.call(
		_label_for(world.tactical.command_target_id, labels) == state.target,
		"%s target selection matches source" % label
	)
	check.call(
		_same_optional_point(
			world.tactical.gather_point, world.tactical.gather_point_active, state.point
		),
		"%s command point matches source" % label
	)
	check.call(
		world.tactical.gather_point_timer == int(state.point_timer),
		"%s point timer matches source" % label
	)
	var native_held: Variant = (
		null if world.tactical.held_command.is_empty() else world.tactical.held_command
	)
	check.call(native_held == state.held, "%s held command matches source" % label)
	check.call(
		world.tactical.hold_elapsed == int(state.hold_elapsed), "%s hold age matches source" % label
	)
	check.call(
		world.tactical.hold_has_fired == bool(state.hold_fired),
		"%s first-fire latch matches source" % label
	)
	check.call(
		world.tactical.gather_push_fired == bool(state.gather_push),
		"%s gather push latch matches source" % label
	)
	check.call(world.tactical.feedback_text == state.feedback, "%s feedback matches source" % label)
	for index in range(heroes.size()):
		var hero: HeroState = heroes[index]
		var expected_hero: Dictionary = state.heroes[index]
		check.call(
			_same_optional_point(hero.destination, hero.has_destination, expected_hero.destination),
			"%s %s formation destination" % [label, expected_hero.id]
		)
		check.call(
			_label_for(hero.follow_id, labels) == expected_hero.follow,
			"%s %s follow target" % [label, expected_hero.id]
		)
		check.call(
			_label_for(hero.target_id, labels) == expected_hero.target,
			"%s %s combat target" % [label, expected_hero.id]
		)
		check.call(
			hero.is_retreating == bool(expected_hero.retreating),
			"%s %s retreat state" % [label, expected_hero.id]
		)


func _world_with_heroes(count: int) -> Prototype:
	var world := Prototype.new()
	world.setup_arena()
	while world.player_roster().size() < count:
		var hero: HeroState = world.spawn_hero(KAIZEN, world.BLUE, Vector2.ZERO)
		world.player_hero_ids.append(hero.id)
	return world


func _prepare_heroes(world: Prototype, points: Array) -> Array:
	var heroes := world.player_roster()
	for index in range(heroes.size()):
		var hero: HeroState = heroes[index]
		hero.position = Vector2(float(points[index][0]), float(points[index][1]))
		hero.attack_range = 100.0
		hero.has_destination = false
		hero.destination_auto = false
		hero.follow_id = -1
		hero.target_id = -1
		hero.is_retreating = true
	return heroes


func _free_red_hero(world: Prototype) -> HeroState:
	for unit in world.units:
		var hero := unit as HeroState
		if hero != null and hero.team == world.RED:
			return hero
	return null


func _hero_labels(heroes: Array) -> Dictionary:
	var labels := {}
	for index in range(heroes.size()):
		labels[heroes[index].id] = "blue_%d" % index
	return labels


func _label_for(id: int, labels: Dictionary) -> Variant:
	return null if id < 0 else labels.get(id, "unmapped:%d" % id)


func _same_optional_point(actual: Vector2, active: bool, expected: Variant) -> bool:
	if expected == null:
		return not active
	if not active or not expected is Array or expected.size() != 2:
		return false
	return actual.is_equal_approx(Vector2(float(expected[0]), float(expected[1])))


func _case(fixture: Dictionary, label: String) -> Dictionary:
	for value in fixture.cases:
		if value.label == label:
			return value
	return {}
