extends RefCounted

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const NexusUpgrades = preload("res://scripts/match/nexus_upgrades.gd")
const Scheduler = preload("res://scripts/match/wave_scheduler.gd")
const Siege = preload("res://scripts/combat/siege_battle.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const ORC = preload("res://data/minions/orc.tres")
const TROLL = preload("res://data/minions/troll.tres")
const UNDEAD = preload("res://data/minions/undead.tres")
const DARK = preload("res://data/minions/dark_rider.tres")


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/nexus_source.json")
	)
	check.call(fixture is Dictionary, "nexus fixtures parse")
	if not fixture is Dictionary:
		return
	_tiers(check, fixture)
	_hp_cases(check, fixture)
	_shield_waves(check, fixture)
	_scaling(check, fixture)
	_composition(check, fixture)
	_scheduler_teams(check, fixture)
	_ai(check, fixture)
	_guards(check)


func _tiers(check: Callable, fixture: Dictionary) -> void:
	check.call(NexusUpgrades.LEVELS.size() == 5, "five nexus tiers")
	for row in fixture.nexus_levels:
		var level := int(row.level)
		var data = NexusUpgrades.LEVELS[level - 1]
		check.call(data.is_valid(), "nexus definition valid")
		check.call(data.level == level, "nexus level field")
		check.call(data.max_hp == int(row.hp), "source nexus hp")
		check.call(data.damage == int(row.damage), "source nexus damage")
		check.call(data.attack_range_px == float(row.range), "source nexus range")
		check.call(data.attack_cooldown_ticks == int(row.cooldown), "source nexus cooldown")
		check.call(data.shield_capacity == float(row.shield_capacity), "source shield cap")
		check.call(data.upgrade_price == int(row.price), "source nexus price")
		check.call(data.sale_refund == 0, "nexus cannot be sold")
		check.call(
			NexusUpgrades.MINION_SCALES[level - 1] == float(row.scale), "source minion scale"
		)
		check.call(NexusUpgrades.MINION_AI[level - 1] == int(row.ai), "source minion AI")
		var world := _rich_world()
		var nexus = world.nexuses[0]
		for previous in range(1, level):
			world.upgrade_nexus(nexus.id, previous)
		check.call(
			world.nexus_upgrade_price(nexus.id) == int(row.next_price),
			"source nexus next/max quote"
		)
		check.call(world.economy.is_balanced(), "nexus tier ledger balanced")


func _hp_cases(check: Callable, fixture: Dictionary) -> void:
	for sample in fixture.hp_cases:
		var world := _rich_world()
		var nexus = world.nexuses[0]
		for previous in range(1, int(sample.from)):
			world.upgrade_nexus(nexus.id, previous)
		nexus.hp = float(sample.old_hp)
		nexus.castle_shield_purchased = bool(sample.purchased)
		if bool(sample.purchased):
			nexus.shield_max = NexusUpgrades.LEVELS[int(sample.from) - 1].shield_capacity
		else:
			nexus.shield_max = NexusUpgrades.LEVELS[0].shield_capacity
		nexus.shield = int(nexus.shield_max * float(sample.shield_ratio))
		nexus.cooldown_ticks = 7
		nexus.no_damage_ticks = 11
		var before: int = world.economy.gold[0]
		check.call(
			world.nexus_upgrade_price(nexus.id) == int(sample.cost), "source nexus upgrade cost"
		)
		check.call(world.upgrade_nexus(nexus.id, int(sample.from)), "nexus upgrade accepted")
		check.call(world.economy.gold[0] == before - int(sample.cost), "nexus upgrade debits once")
		check.call(nexus.hp == float(sample.new_hp), "source nexus HP formula")
		check.call(nexus.shield == float(sample.new_shield), "source shield preserve/resize")
		check.call(nexus.shield_max == float(sample.new_shield_max), "source shield capacity")
		check.call(
			nexus.cooldown_ticks == 7 and nexus.no_damage_ticks == 11,
			"nexus keeps cooldown and regen clock"
		)
		check.call(world.economy.is_balanced(), "nexus HP ledger balanced")


func _shield_waves(check: Callable, fixture: Dictionary) -> void:
	for sample in fixture.shield_waves:
		var world := _rich_world()
		var nexus = world.nexuses[0]
		nexus.castle_shield_purchased = bool(sample.purchased)
		nexus.shield_max = NexusUpgrades.LEVELS[0].shield_capacity
		nexus.shield = float(sample.before)
		nexus.shield_active = true
		nexus.free_shield_active = true
		nexus.set_wave(int(sample.wave))
		check.call(nexus.shield == float(sample.after), "source set_wave shield")
		check.call(nexus.shield_active == bool(sample.active), "source shield active")
		check.call(nexus.free_shield_active == bool(sample.free), "source free flag")


func _scaling(check: Callable, fixture: Dictionary) -> void:
	var bases := {
		"goblin": GOBLIN, "orc": ORC, "troll": TROLL, "undead": UNDEAD, "dark_rider": DARK
	}
	for row in fixture.minion_scaling:
		var base = bases[row.kind]
		var world := _rich_world()
		var scaled = world.scaled_minion_definition(base, int(row.nexus))
		check.call(scaled.max_hp == int(row.max_hp), "source scaled hp")
		check.call(scaled.damage == int(row.damage), "source scaled damage")
		check.call(is_equal_approx(scaled.speed_px_per_tick, float(row.speed)), "scaled speed")
		check.call(scaled.attack_range_px == float(row.range), "range never scales")
		check.call(scaled.attack_cooldown_ticks == int(row.cooldown), "scaled cooldown")
		check.call(scaled.gold_reward == int(row.gold), "scaled reward")
		check.call(is_equal_approx(scaled.regen_per_tick, float(row.regen)), "scaled regen")
		check.call(scaled.armor == float(row.armor), "armor never scales")
		check.call(scaled.magic_resist == float(row.magic_resist), "resist never scales")
		check.call(scaled.is_valid(), "scaled definition valid")
	# Spawned stats are snapshots; old units never change retroactively.
	var world := _rich_world()
	var veteran = world.spawn_unit(GOBLIN, 0, 1)
	check.call(veteran.ai_level == 1 and veteran.hp == 45, "tier-one spawn")
	world.upgrade_nexus(world.nexuses[0].id, 1)
	var recruit = world.spawn_unit(GOBLIN, 0, 1)
	check.call(recruit.ai_level == 2 and recruit.hp == 54, "spawn reads live tier")
	check.call(veteran.hp == 45 and veteran.ai_level == 1, "veteran untouched")
	check.call(veteran.definition != recruit.definition, "scaled copy not shared")
	check.call(GOBLIN.max_hp == 45 and GOBLIN.damage == 5, "base resource immutable")
	var red = world.spawn_unit(GOBLIN, 1, 1)
	check.call(red.ai_level == 1 and red.hp == 45, "per-team tier respected")


func _composition(check: Callable, fixture: Dictionary) -> void:
	for castle_level in fixture.composition:
		for wave in fixture.composition[castle_level]:
			var expected: Array = fixture.composition[castle_level][wave]
			check.call(
				Scheduler.composition(int(wave), int(castle_level)) == expected,
				"source composition tier %s wave %s" % [castle_level, wave]
			)
	check.call(
		Scheduler.composition(2) == ["goblin", "goblin", "goblin"],
		"legacy single-arg composition stays tier one"
	)


func _scheduler_teams(check: Callable, fixture: Dictionary) -> void:
	var scheduler := Scheduler.new()
	for tick in range(301):
		scheduler.step_tick(true, 0, 2, 5)
	check.call(scheduler.wave == 1, "per-team wave starts")
	var blue_kinds: Array = []
	var red_kinds: Array = []
	for entry in scheduler.queues[0]:
		blue_kinds.append(entry.kind)
	for entry in scheduler.queues[1]:
		red_kinds.append(entry.kind)
	var blue_expected: Array = fixture.composition["2"]["1"]
	var red_expected: Array = fixture.composition["5"]["1"]
	check.call(blue_kinds.size() == blue_expected.size() * 3, "blue queue length")
	check.call(red_kinds.size() == red_expected.size() * 3, "red queue length")
	check.call(blue_kinds[0] == blue_expected[0], "blue keeps own tier order")
	check.call(red_kinds[0] == red_expected[0], "red keeps own tier order")
	# Composition is fixed at wave start; scaling follows live tier at spawn.
	var world := _rich_world()
	for tick in range(301):
		world.step_tick()
	check.call(world.wave_count == 1 and world.units.size() == 2, "wave one pair")
	var pending: int = world.scheduler.pending_count()
	check.call(pending == 16, "tier-one wave one queue holds remainder")
	world.upgrade_nexus(world.nexuses[0].id, 1)
	check.call(world.scheduler.pending_count() == pending, "upgrade keeps queued kinds")
	for tick in range(20):
		world.step_tick()
	var upgraded := 0
	for unit in world.units:
		if unit.team == 0 and unit.ai_level == 2:
			upgraded += 1
	check.call(upgraded > 0, "late queue spawns use new tier")
	for unit in world.units:
		if unit.team == 1:
			check.call(unit.ai_level == 1, "enemy tier unaffected")


func _ai(check: Callable, fixture: Dictionary) -> void:
	var scenarios := {
		"mixed":
		[
			[11, 120, 100, 40, 1, 45, true],
			[12, 110, 100, 10, 0, 45, true],
			[13, 125, 100, 5, 1, 45, true],
			[21, 115, 100, 2000, 1, 2000, false],
			[22, 118, 100, 4000, 1, 2000, false],
			[31, 200, 100, 45, 1, 45, true],
			[32, 125, 100, 45, 1, 45, true],
			[33, 150, 100, 45, 1, 45, true]
		],
		"structures_only":
		[[21, 115, 100, 2000, 1, 2000, false], [22, 110, 100, 4000, 1, 2000, false]],
		"fallback": [[41, 140, 100, 45, 1, 45, true], [42, 150, 100, 5, 0, 45, true]],
		"tie": [[51, 110, 100, 40, 1, 45, true], [52, 90, 100, 10, 1, 45, true]]
	}
	for name in scenarios:
		var world := Siege.new()
		var mapping: Dictionary = {}
		for spec in scenarios[name]:
			var eid: int = spec[0]
			if bool(spec[6]):
				var unit = world.spawn_unit(GOBLIN, 1, int(spec[4]))
				unit.position = Vector2(spec[1], spec[2])
				unit.hp = float(spec[3])
				mapping[unit.id] = eid
			else:
				var tower = world.spawn_structure(Siege.ARCHER, 1, Vector2(spec[1], spec[2]), 1)
				tower.position = Vector2(spec[1], spec[2])
				tower.hp = float(spec[3])
				mapping[tower.id] = eid
		var seeker = world.spawn_unit(GOBLIN, 0, 1)
		seeker.position = Vector2(100, 100)
		seeker.definition = GOBLIN.duplicate()
		seeker.definition.attack_range_px = 30.0
		for sample in fixture.ai_cases:
			if sample.scenario != name:
				continue
			seeker.ai_level = int(sample.ai)
			var target = world._find_target(seeker)
			var actual = mapping.get(target.id, -1) if target != null else null
			check.call(actual == sample.target, "source AI tier %s %s" % [name, sample.ai])


func _guards(check: Callable) -> void:
	var world := _rich_world()
	var nexus = world.nexuses[0]
	check.call(world.nexus_upgrade_price(-1) == 0, "invalid nexus quote zero")
	check.call(not world.upgrade_nexus(-1, 1), "invalid nexus rejected")
	check.call(not world.upgrade_nexus(world.nexuses[1].id, 1), "enemy nexus rejected")
	world.build_tower(0, 0)
	check.call(not world.upgrade_nexus(world.slots[0].structure_id, 1), "tower is not a nexus")
	var enemy = world.spawn_unit(GOBLIN, 1, 0)
	check.call(not world.upgrade_nexus(enemy.id, 1), "minion is not a nexus")
	check.call(world.upgrade_nexus(nexus.id, 1), "first nexus upgrade")
	check.call(not world.upgrade_nexus(nexus.id, 1), "stale nexus level rejected")
	check.call(world.economy.is_balanced(), "stale keeps ledger")
	nexus.alive = false
	check.call(not world.upgrade_nexus(nexus.id, 2), "dead nexus rejected")
	var poor := Prototype.new()
	poor.defender_enabled = false
	poor.setup_arena()
	poor.economy.gold[0] = 100
	poor.economy.opening[0] = 100
	var poor_nexus = poor.nexuses[0]
	check.call(not poor.upgrade_nexus(poor_nexus.id, 1), "poor nexus rejected")
	check.call(poor_nexus.settings().level == 1 and poor.economy.is_balanced(), "poor untouched")
	var capped := _rich_world()
	var top = capped.nexuses[0]
	for level in range(1, 5):
		capped.upgrade_nexus(top.id, level)
	check.call(top.settings().level == 5, "nexus reaches max")
	check.call(
		not capped.upgrade_nexus(top.id, 5) and capped.nexus_upgrade_price(top.id) == 0,
		"max nexus rejected"
	)
	check.call(not capped.upgrade_tower(top.id, 5), "archer path still rejects nexus")
	var finished := _rich_world()
	finished.winner = 1
	check.call(not finished.upgrade_nexus(finished.nexuses[0].id, 1), "result blocks nexus")
	# In-flight arrows and cooldown survive a nexus upgrade.
	var battle := _rich_world()
	battle.build_tower(0, 0)
	var archer = battle.get_unit(battle.slots[0].structure_id)
	var victim = battle.spawn_unit(GOBLIN, 1, 0)
	victim.position = archer.position + Vector2(60, 0)
	battle.fire_projectile(archer.id, victim.id)
	var shot = battle.projectiles[0]
	archer.cooldown_ticks = 12
	var fort = battle.nexuses[0]
	fort.cooldown_ticks = 9
	fort.target_id = victim.id
	battle.upgrade_nexus(fort.id, 1)
	check.call(shot.active and shot.damage == 20, "nexus keeps foreign arrows")
	check.call(archer.cooldown_ticks == 12, "archer clock untouched")
	check.call(fort.cooldown_ticks == 9 and fort.target_id == victim.id, "nexus keeps own clock")


func _rich_world() -> Prototype:
	var world := Prototype.new()
	world.defender_enabled = false
	world.economy.gold[0] = 20000
	world.economy.opening[0] = 20000
	world.setup_arena()
	return world
