extends RefCounted

const Siege = preload("res://scripts/combat/siege_battle.gd")
const Definition = preload("res://scripts/data/minion_definition.gd")
const Projectile = preload("res://scripts/combat/projectile_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const ORC = preload("res://data/minions/orc.tres")


func run(check: Callable) -> void:
	_fixtures(check)
	_projectile_delivery(check)
	_projectile_cancellation(check)
	_target_ties_and_cooldown(check)
	_regen_and_shields(check)
	_siege_result(check)
	_capacity(check)


func _fixtures(check: Callable) -> void:
	var data = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/structures_source.json")
	)
	check.call(data is Dictionary, "structure source fixtures parse")
	if not data is Dictionary:
		return
	for kind in ["tower", "nexus"]:
		var definition = Siege.ARCHER if kind == "tower" else Siege.NEXUS
		check.call(definition.is_valid(), "stationary definition validates")
		for key in data.stats[kind]:
			check.call(
				definition.get(key) == data.stats[kind][key], "source structure %s.%s" % [kind, key]
			)
	for sample in data.damage:
		var world := Siege.new()
		var definition = Siege.ARCHER if sample.kind == "tower" else Siege.NEXUS
		var target := world.spawn_structure(definition, 1, Vector2(120, 100))
		target.hp = 1000
		target.shield = sample.shield
		var attacker_data := GOBLIN.duplicate() as Definition
		attacker_data.damage = int(sample.amount)
		var attacker := world.spawn_unit(attacker_data, 0, 1)
		attacker.position = Vector2(100, 100)
		check.call(world.apply_hit(attacker.id, target.id, sample.school), "structure hit accepted")
		check.call(is_equal_approx(target.hp, sample.hp), "source shield/armor/reduction HP")
		check.call(is_equal_approx(target.shield, sample.shield_after), "source shield remaining")
		check.call(target.no_damage_ticks == 0, "absorbed hits reset regen clock")
	for sample in data.muzzle:
		var world := Siege.new()
		var point := Vector2(sample.at[0], sample.at[1])
		var tower := world.spawn_structure(Siege.ARCHER, 0, point)
		check.call(
			(
				world.muzzle_position(tower, point + Vector2(sample.face * 100, 0))
				== Vector2(sample.expected[0], sample.expected[1])
			),
			"original archer muzzle helper"
		)
	for index in range(3):
		check.call(
			(
				Siege.BLUE_POSITIONS[index]
				== Vector2(data.positions.blue[index][0], data.positions.blue[index][1])
			),
			"blue tower uses source position"
		)
		check.call(
			(
				Siege.RED_POSITIONS[index]
				== Vector2(data.positions.red[index][0], data.positions.red[index][1])
			),
			"red tower uses source position"
		)


func _projectile_delivery(check: Callable) -> void:
	var world := Siege.new()
	var tower := world.spawn_structure(Siege.ARCHER, 0, Vector2(100, 100))
	var target := world.spawn_unit(GOBLIN, 1, 1)
	target.position = Vector2(200, 100)
	check.call(
		not world.apply_hit(tower.id, target.id), "tower cannot bypass projectile with melee"
	)
	check.call(world.fire_projectile(tower.id, target.id), "tower fires within range")
	check.call(target.hp == 45, "launch does not apply damage")
	check.call(not world.fire_projectile(tower.id, target.id), "cooldown blocks duplicate launch")
	var shot := world.projectiles[0]
	for tick in range(20):
		world.step_tick()
	check.call(target.hp == 25, "projectile hits once for 20 damage")
	check.call(not shot.active and world.projectiles.is_empty(), "impacted projectile retired")
	world._update_projectiles(tower)
	check.call(target.hp == 25, "duplicate projectile update cannot re-hit")
	check.call(world.credited_gold == [0, 0], "nonlethal projectile gives no credit")


func _projectile_cancellation(check: Callable) -> void:
	var world := Siege.new()
	var a := world.spawn_structure(Siege.ARCHER, 0, Vector2(100, 100))
	var b := world.spawn_structure(Siege.ARCHER, 0, Vector2(105, 100))
	var target := world.spawn_unit(GOBLIN, 1, 1)
	target.position = Vector2(120, 100)
	target.hp = 20
	world.fire_projectile(a.id, target.id)
	world.fire_projectile(b.id, target.id)
	for tick in range(6):
		world.step_tick()
	check.call(
		world.kills == [1, 0] and world.credited_gold == [8, 0], "two shots credit one death"
	)
	check.call(world.projectiles.is_empty(), "second shot cancels when target dies")
	world = Siege.new()
	a = world.spawn_structure(Siege.ARCHER, 0, Vector2(100, 100))
	target = world.spawn_unit(GOBLIN, 1, 1)
	target.position = Vector2(200, 100)
	world.fire_projectile(a.id, target.id)
	var shot := world.projectiles[0]
	var attacker := world.spawn_unit(ORC, 1, 1)
	attacker.position = Vector2(110, 100)
	a.shield = 0
	a.hp = 1
	world.step_tick()
	check.call(not a.alive and not shot.active, "owner death cancels in-flight shots")
	check.call(target.hp == 45, "cancelled shot deals no damage")
	check.call(
		world.tower_kills == [0, 1] and world.credited_gold == [0, 100], "tower kill credits once"
	)
	world.step_tick()
	check.call(world.credited_gold == [0, 100], "tower credit does not repeat")
	world = Siege.new()
	a = world.spawn_structure(Siege.ARCHER, 0, Vector2(100, 100))
	target = world.spawn_unit(GOBLIN, 1, 1)
	target.position = Vector2(200, 100)
	world.fire_projectile(a.id, target.id)
	world.projectiles[0].ttl_ticks = 1
	world.step_tick()
	check.call(world.projectiles.is_empty() and target.hp == 45, "expired projectile cannot hit")


func _target_ties_and_cooldown(check: Callable) -> void:
	var world := Siege.new()
	var tower := world.spawn_structure(Siege.ARCHER, 0, Vector2(100, 100))
	var durable := GOBLIN.duplicate() as Definition
	durable.max_hp = 5000
	var first := world.spawn_unit(durable, 1, 1)
	var second := world.spawn_unit(durable, 1, 1)
	first.position = Vector2(120, 100)
	second.position = Vector2(80, 100)
	check.call(world._structure_target(tower) == second, "tower tie uses later ID like source <=")
	check.call(world.fire_projectile(tower.id, first.id), "first shot starts cooldown")
	for tick in range(34):
		world.step_tick()
	check.call(tower.cooldown_ticks == 1 and world._next_projectile_id == 2, "no early archer shot")
	world.step_tick()
	check.call(
		tower.cooldown_ticks == 35 and world._next_projectile_id == 3, "archer fires at 35 ticks"
	)


func _regen_and_shields(check: Callable) -> void:
	var world := Siege.new()
	var tower := world.spawn_structure(Siege.ARCHER, 0, Vector2.ZERO)
	tower.hp = 1999.9
	tower.shield = 0
	tower.no_damage_ticks = 298
	tower.tick_regen()
	check.call(is_equal_approx(tower.hp, 1999.9), "tower HP regen not before 300 ticks")
	tower.tick_regen()
	check.call(
		tower.hp == 2000 and tower.shield == 0, "HP regen clamps; unpaid shield never regens"
	)
	var nexus := world.spawn_structure(Siege.NEXUS, 1, Vector2(100, 100))
	nexus.shield = 3998
	nexus.no_damage_ticks = 118
	nexus.tick_regen()
	check.call(nexus.shield == 3998, "nexus regen waits 120 ticks")
	nexus.tick_regen()
	check.call(nexus.shield == 4000, "nexus regen clamps at capacity")
	nexus.shield = 0
	nexus.set_wave(10)
	check.call(nexus.shield_active and nexus.shield == 4000, "wave 10 still protected")
	nexus.set_wave(11)
	check.call(not nexus.shield_active and nexus.shield == 0, "wave 11 removes unpurchased shield")
	for tick in range(130):
		nexus.tick_regen()
	check.call(nexus.shield == 0, "disabled nexus shield cannot regrow")
	check.call(nexus.absorb(5, "physical") == 5, "unprotected nexus takes full damage")
	nexus.set_wave(10)
	nexus.shield = 0
	check.call(
		nexus.absorb(5, "physical") == 0, "active depleted shield reduction can truncate to zero"
	)
	check.call(nexus.no_damage_ticks == 0, "zero HP damage still resets regen delay")


func _siege_result(check: Callable) -> void:
	var world := Siege.new()
	var blue := world.spawn_structure(Siege.NEXUS, 0, Vector2(500, 500))
	var red := world.spawn_structure(Siege.NEXUS, 1, Vector2(120, 100))
	red.set_wave(11)
	red.hp = 3
	var attacker := world.spawn_unit(GOBLIN, 0, 1)
	attacker.position = Vector2(100, 100)
	attacker.waypoint_index = world.paths[1].size()
	world.step_tick()
	check.call(
		world.winner == 0 and red.hp == 0 and blue.alive, "nexus death ends siege for correct team"
	)
	check.call(world.escaped == [0, 0], "end-of-route siege is not a lab exit")
	check.call(world.credited_gold == [0, 0], "nexus result does not invent persistent currency")
	var tick := world.tick_count
	var count := world.units.size()
	check.call(not world.spawn_wave(GOBLIN), "finished world rejects waves")
	check.call(world.spawn_unit(GOBLIN, 1, 1) == null, "finished world rejects individual spawns")
	check.call(not world.apply_hit(attacker.id, blue.id), "finished world rejects hits")
	for step in range(10):
		world.step_tick()
	check.call(
		world.tick_count == tick and world.units.size() == count, "result freezes simulation"
	)
	var victories := 0
	for event in world.recent_events:
		if event.kind == "victory":
			victories += 1
	check.call(
		victories == 1 and world.projectiles.is_empty(), "result emitted once; projectiles cleared"
	)
	world = Siege.new()
	red = world.spawn_structure(Siege.NEXUS, 1, Vector2(300, 100))
	attacker = world.spawn_unit(GOBLIN, 0, 1)
	attacker.position = Vector2(200, 100)
	attacker.waypoint_index = world.paths[1].size()
	world.step_tick()
	check.call(
		attacker.position.x > 200 and attacker.alive, "completed lane continues toward nexus"
	)


func _capacity(check: Callable) -> void:
	var world := Siege.new()
	check.call(world.setup_arena(), "initial structure setup succeeds")
	check.call(
		not world.setup_arena() and world.structures.size() == 8,
		"setup cannot duplicate structures"
	)
	check.call(not world.spawn_assault_wave(GOBLIN, 2), "invalid team mode rejected")
	check.call(not world.spawn_assault_wave(Siege.ARCHER, 0), "structures cannot spawn as minions")
	check.call(
		world.spawn_assault_wave(GOBLIN, 0) and world.units.size() == 3,
		"blue-only wave has 3 units"
	)
	check.call(
		world.spawn_assault_wave(GOBLIN, 1) and world.units.size() == 6, "red-only wave has 3 units"
	)
	for index in range(38):
		world.spawn_assault_wave(GOBLIN, 0)
	check.call(
		world.units.size() == 120 and not world.spawn_assault_wave(GOBLIN, 1),
		"one-team wave cap atomic"
	)
	var tower = world.structures[0]
	var target = world.units[3]
	target.position = tower.position + Vector2(30, 0)
	for index in range(Siege.MAX_PROJECTILES):
		world.projectiles.append(Projectile.new())
	check.call(
		not world.fire_projectile(tower.id, target.id) and tower.cooldown_ticks == 0,
		"projectile cap rejects without consuming cooldown"
	)
