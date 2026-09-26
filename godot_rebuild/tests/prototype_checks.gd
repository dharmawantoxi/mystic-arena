extends RefCounted

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const Scheduler = preload("res://scripts/match/wave_scheduler.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")


func run(check: Callable) -> void:
	_fixtures(check)
	_capacity(check)
	_transactions(check)
	_death_and_stale_ids(check)
	_progress_and_result(check)
	_hero_melee(check)
	_replay(check)


func _fixtures(check: Callable) -> void:
	var data = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/match_source.json")
	)
	check.call(data is Dictionary, "match fixtures parse")
	if not data is Dictionary:
		return
	var world := Prototype.new()
	check.call(
		world.setup_arena() and world.structures.size() == 2, "match starts with only two nexuses"
	)
	check.call(
		(
			world.blue_hero() != null
			and world.blue_hero().settings().id == "kaizen"
			and world.blue_hero().position == world.HERO_SPAWN
			and world.living_minion_count() == 0
		),
		"match starts with Kaizen and no minions"
	)
	check.call(not world.setup_arena(), "match setup is idempotent")
	check.call(
		world.economy.gold == [int(data.normal_start), int(data.ai_start)],
		"starting budgets match source"
	)
	check.call(
		Economy.BUILD_COST == data.build_cost and Economy.SELL_REFUND == data.sell_refund,
		"full source build and UI sale path prices"
	)
	check.call(world.slots.size() == 18, "nine slots per team")
	for index in range(data.slots.size()):
		var slot = world.slots[index]
		var expected = data.slots[index]
		check.call(
			(
				slot.team == int(expected.team)
				and slot.lane == int(expected.lane)
				and slot.position == Vector2(expected.position[0], expected.position[1])
			),
			"source build slot %d" % index
		)
	for number in data.composition:
		check.call(
			Scheduler.composition(int(number)) == data.composition[number],
			"source tier-1 composition wave " + number
		)
	for sample in data.economy:
		check.call(
			Economy.starting_gold(1000, sample.level, sample.difficulty) == sample.starting,
			"source starting gold formula"
		)
		check.call(
			is_equal_approx(Economy.passive_rate(sample.level, sample.difficulty), sample.rate),
			"source income rate formula"
		)
		var wallet := Economy.new()
		wallet.gold[0] = int(sample.starting)
		wallet.opening[0] = wallet.gold[0]
		wallet.income_per_second = sample.rate
		for tick in range(1, 481):
			wallet.step_tick(int((tick - 1) / 180.0))
			if tick % 60 == 0:
				var expected: Array = sample.pulses[int(tick / 60.0) - 1]
				check.call(
					(
						wallet.gold[0] == int(expected[0])
						and wallet.gold[1] == int(expected[1])
						and wallet.income_milli == int(expected[2])
					),
					"source integer income pulse"
				)
		check.call(wallet.is_balanced(), "income ledger reconciles")
	for trace in data.traces:
		var scheduler := Scheduler.new()
		var starts: Array = []
		var spawns: Array = []
		var snapshots: Array = []
		for tick in range(1, 3801):
			var clear := not (301 < tick and tick < int(trace.blocked_until))
			var batch := scheduler.step_tick(clear, 120)
			if batch.started:
				starts.append([tick, scheduler.wave])
			for spawn in batch.spawns:
				spawns.append([tick, spawn.team, spawn.kind, spawn.lane])
			if tick in [300, 301, 320, 321, 461, 1801, 1802, 2049, 2050, 3303, 3800]:
				snapshots.append(
					[
						tick,
						scheduler.wave,
						scheduler.remaining_ticks,
						scheduler.queues[0].size(),
						scheduler.queues[1].size()
					]
				)
		check.call(_same_trace(starts, trace.starts), "source wave boundary/field-clear trace")
		check.call(_same_trace(spawns, trace.spawns), "source continuous spawn queue trace")
		check.call(_same_trace(snapshots, trace.snapshots), "source wave clocks and queue lengths")


func _capacity(check: Callable) -> void:
	var scheduler := Scheduler.new()
	for tick in range(301):
		scheduler.step_tick(true, 0)
	check.call(
		scheduler.wave == 1 and scheduler.pending_count() == 18,
		"capacity block retains all queued units"
	)
	var next := scheduler.step_tick(true, 1)
	check.call(
		next.spawns.size() == 1 and scheduler.pending_count() == 17,
		"partial capacity emits only one unit"
	)
	var pending := scheduler.pending_count()
	for tick in range(1600):
		scheduler.step_tick(true, 0)
	check.call(
		scheduler.wave == 1 and scheduler.pending_count() == pending,
		"pending queues block next wave"
	)
	scheduler.step_tick(true, 120)
	check.call(
		scheduler.pending_count() == pending - 2,
		"capacity recovery resumes both queues without drops"
	)
	var world := _world()
	for slot in world.slots:
		world.economy.credit_kill(slot.team, 100)
		check.call(world.build_tower(slot.team, slot.id), "all eighteen source slots can build")
	check.call(
		world.structures.size() == 20 and world.economy.is_balanced(),
		"match structure cap includes both nexuses"
	)
	check.call(
		not world.spawn_wave(GOBLIN) and not world.spawn_assault_wave(GOBLIN, 0),
		"manual lab wave bypass disabled"
	)


func _transactions(check: Callable) -> void:
	var world := _world()
	check.call(
		not world.build_tower(0, -1) and not world.build_tower(0, 9),
		"invalid or enemy slots rejected"
	)
	check.call(world.economy.gold == [1000, 350], "rejected builds do not charge")
	check.call(world.build_tower(0, 0), "first build succeeds")
	var tower_id: int = world.slots[0].structure_id
	check.call(world.economy.gold[0] == 900 and world.structures.size() == 3, "build debits once")
	check.call(
		not world.build_tower(0, 0) and world.economy.gold[0] == 900,
		"duplicate build does not debit again"
	)
	check.call(not world.sell_tower(0, world.nexuses[0].id), "nexus cannot be sold")
	check.call(world.sell_tower(0, tower_id), "own living tower can be sold")
	check.call(
		world.economy.gold[0] == 950 and world.slots[0].structure_id == -1,
		"sale refunds 50 and frees slot"
	)
	check.call(
		not world.sell_tower(0, tower_id) and world.economy.gold[0] == 950,
		"repeat sale cannot mint gold"
	)
	check.call(
		world.kills == [0, 0] and world.tower_kills == [0, 0] and world.credited_gold == [0, 0],
		"sale does not trigger a death or kill reward"
	)
	check.call(world.build_tower(0, 0), "released slot rebuilds")
	check.call(
		world.slots[0].structure_id != tower_id and not world.sell_tower(0, tower_id),
		"stale entity ID cannot sell replacement tower"
	)
	check.call(world.build_tower(1, 9), "enemy builder uses same priced build path")
	check.call(not world.sell_tower(0, world.slots[9].structure_id), "enemy tower sale rejected")
	check.call(world.economy.is_balanced(), "transaction ledger reconciles")
	var poor := _world()
	poor.economy.gold[0] = 99
	poor.economy.opening[0] = 99
	check.call(
		(
			not poor.build_tower(0, 0)
			and poor.slots[0].structure_id == -1
			and poor.economy.gold[0] == 99
		),
		"insufficient funds reject atomically"
	)
	check.call(poor.economy.is_balanced(), "failed debit leaves ledger intact")


func _death_and_stale_ids(check: Callable) -> void:
	var world := _world()
	world.build_tower(0, 0)
	var tower = world.get_unit(world.slots[0].structure_id)
	var victim = world.spawn_unit(GOBLIN, 1, 1)
	victim.position = tower.position + Vector2(80, 0)
	world.fire_projectile(tower.id, victim.id)
	var shot = world.projectiles[0]
	world.sell_tower(0, tower.id)
	check.call(
		not shot.active and world.projectiles.is_empty(),
		"sale cancels owned projectiles immediately"
	)
	check.call(victim.hp == 45, "sale cannot deliver cancelled projectile damage")
	world.build_tower(0, 0)
	tower = world.get_unit(world.slots[0].structure_id)
	tower.hp = 1
	tower.shield = 0
	victim.position = tower.position + Vector2(10, 0)
	var before: int = world.economy.gold[1]
	world.apply_hit(victim.id, tower.id)
	check.call(world.economy.gold[1] == before + 100, "tower death credits opposing wallet once")
	check.call(not world.sell_tower(0, tower.id), "dead tower cannot be sold even before cleanup")
	world.step_tick()
	check.call(
		world.slots[0].structure_id == -1, "destroyed slot is reusable (intentional source bug fix)"
	)
	check.call(world.economy.gold[1] == before + 100, "cleanup does not pay twice")
	var red = world.spawn_unit(GOBLIN, 1, 1)
	var blue = world.spawn_unit(GOBLIN, 0, 1)
	blue.position = Vector2(500, 500)
	red.position = Vector2(510, 500)
	red.hp = 1
	before = world.economy.gold[0]
	world.apply_hit(blue.id, red.id)
	check.call(world.economy.gold[0] == before + 8, "minion kill credits real match wallet")
	check.call(
		not world.apply_hit(blue.id, red.id) and world.economy.gold[0] == before + 8,
		"duplicate minion hit cannot duplicate gold"
	)
	check.call(world.economy.is_balanced(), "kill/sale/build ledger reconciles")


func _progress_and_result(check: Callable) -> void:
	var world := _world()
	for tick in range(300):
		world.step_tick()
	check.call(
		world.wave_count == 0 and world.living_minion_count() == 0,
		"initial 300-tick preparation window"
	)
	check.call(world.economy.gold == [1015, 365], "passive gold is active during preparation")
	world.step_tick()
	check.call(
		world.wave_count == 1 and world.living_minion_count() == 2,
		"tick 301 starts and immediately spawns first pair"
	)
	for tick in range(19):
		world.step_tick()
	check.call(world.living_minion_count() == 2, "no early second spawn")
	world.step_tick()
	check.call(world.living_minion_count() == 4, "tick 321 spawns next pair during wave timer")
	var nexus = world.nexuses[1]
	nexus.shield_active = false
	nexus.shield = 0
	nexus.hp = 1
	var attacker = world.spawn_unit(GOBLIN, 0, 1)
	attacker.position = nexus.position - Vector2(20, 0)
	world.apply_hit(attacker.id, nexus.id)
	var balances := world.economy.gold.duplicate()
	var ticks := world.tick_count
	check.call(
		world.winner == 0 and world.scheduler.pending_count() == 0,
		"result cancels queued wave units"
	)
	check.call(
		not world.build_tower(0, 0) and not world.sell_tower(0, nexus.id),
		"result blocks transactions"
	)
	for tick in range(120):
		world.step_tick()
	check.call(
		world.economy.gold == balances and world.tick_count == ticks,
		"result freezes economy and clocks"
	)


func _replay(check: Callable) -> void:
	var first := Prototype.new()
	var second := Prototype.new()
	first.setup_arena()
	second.setup_arena()
	for tick in range(4200):
		if tick in [1, 80, 200]:
			var slot: int = {1: 2, 80: 5, 200: 8}[tick]
			first.build_tower(0, slot)
			second.build_tower(0, slot)
		first.step_tick()
		second.step_tick()
		if tick % 300 == 0:
			check.call(_snapshot(first) == _snapshot(second), "match replay deterministic")
			check.call(first.economy.is_balanced(), "replay budget reconciles")
	check.call(
		first._defender_built == 3 and first.economy.spent[1] == 300,
		"temporary defender pays for exactly three towers"
	)
	check.call(
		first.wave_count > 0 and first._next_projectile_id > 1, "scheduled waves lead to combat"
	)


func _hero_melee(check: Callable) -> void:
	var world := _world()
	var hero = world.blue_hero()
	var planted := hero.position
	var foe = world.spawn_unit(GOBLIN, 1, 1)
	foe.position = hero.position + Vector2(20, 0)
	var hp: float = foe.hp
	world.step_tick()
	check.call(foe.hp < hp and hero.attack_timer > 0, "in-range hero autoswings once")
	check.call(hero.position == planted, "in-range hero does not chase")
	var far = world.spawn_unit(GOBLIN, 1, 1)
	far.position = hero.position + Vector2(400, 0)
	var far_hp: float = far.hp
	world.step_tick()
	check.call(far.hp == far_hp and foe.hp < hp, "out-of-range minion is not swung")
	hero.alive = false
	var bait = world.spawn_unit(GOBLIN, 1, 1)
	bait.position = hero.position + Vector2(10, 0)
	var bait_hp: float = bait.hp
	world.step_tick()
	check.call(bait.hp == bait_hp, "dead hero does not swing")
	var hunt := _world()
	var hunter = hunt.blue_hero()
	var start := hunter.position
	var quarry = hunt.spawn_unit(GOBLIN, 1, 1)
	quarry.position = start + Vector2(200, 0)
	var quarry_hp: float = quarry.hp
	hunt.step_tick()
	check.call(
		hunter.position.x > start.x and quarry.hp == quarry_hp,
		"hero hunts inside 900 without swinging"
	)
	var beyond := _world()
	var idle = beyond.blue_hero()
	var parked := idle.position
	var ghost = beyond.spawn_unit(GOBLIN, 1, 1)
	ghost.position = parked + Vector2(950, 0)
	beyond.step_tick()
	check.call(idle.position == parked, "beyond hunt range the hero stays")
	var walk := _world()
	var mover = walk.blue_hero()
	var from := mover.position
	var dest := from + Vector2(80, 0)
	check.call(walk.set_hero_destination(mover.id, dest), "manual destination accepted")
	walk.step_tick()
	check.call(mover.position.x > from.x and mover.has_destination, "click-move walks toward point")
	check.call(not walk.set_hero_destination(999, dest), "bad id cannot set destination")
	for tick in range(40):
		walk.step_tick()
	check.call(
		mover.position == dest and not mover.has_destination, "hero snaps and clears on arrival"
	)
	var hold := _world()
	var escort = hold.blue_hero()
	var origin := escort.position
	hold.set_hero_destination(escort.id, origin + Vector2(80, 0))
	var blocker = hold.spawn_unit(GOBLIN, 1, 1)
	blocker.position = escort.position + Vector2(20, 0)
	var blocker_hp: float = blocker.hp
	hold.step_tick()
	check.call(
		escort.position.x > origin.x and blocker.hp < blocker_hp,
		"destination still allows an in-range swing"
	)
	var chase := _world()
	var stalker = chase.blue_hero()
	var start := stalker.position
	var mark = chase.spawn_unit(GOBLIN, 1, 1)
	mark.position = start + Vector2(180, 0)
	var mark_hp: float = mark.hp
	check.call(chase._set_hero_follow(stalker.id, mark.id), "follow accepted")
	chase.step_tick()
	check.call(
		stalker.follow_id == mark.id and stalker.position.x > start.x and mark.hp == mark_hp,
		"follow walks without swinging out of melee"
	)
	check.call(not chase._set_hero_follow(stalker.id, stalker.id), "cannot follow self")
	chase.set_hero_destination(stalker.id, start)
	check.call(stalker.follow_id == -1 and stalker.has_destination, "destination clears follow")
	mark.alive = false
	var again := _world()
	var chaser = again.blue_hero()
	var corpse = again.spawn_unit(GOBLIN, 1, 1)
	corpse.position = chaser.position + Vector2(180, 0)
	again._set_hero_follow(chaser.id, corpse.id)
	corpse.alive = false
	var parked_follow := chaser.position
	again.step_tick()
	check.call(chaser.follow_id == -1 and chaser.position == parked_follow, "dead follow drops")


func _world() -> Prototype:
	var world := Prototype.new()
	world.defender_enabled = false
	world.setup_arena()
	return world


func _snapshot(world: Prototype) -> Array:
	var result: Array = [
		world.tick_count,
		world.winner,
		world.wave_count,
		world.economy.gold.duplicate(),
		world.scheduler.remaining_ticks,
		world.scheduler.pending_count(),
		world._next_projectile_id
	]
	for unit in world.units:
		result.append([unit.id, unit.position, unit.hp, unit.cooldown_ticks])
	for tower in world.structures:
		result.append([tower.id, tower.hp, tower.shield, tower.cooldown_ticks])
	return result


func _same_trace(actual: Array, expected: Array) -> bool:
	# JSON numbers are floats; nested Array equality compares Variant types strictly.
	# Compare scalar values, retaining fractional mismatches rather than truncating them.
	if actual.size() != expected.size():
		return false
	for row in range(actual.size()):
		if actual[row].size() != expected[row].size():
			return false
		for column in range(actual[row].size()):
			if actual[row][column] != expected[row][column]:
				printerr("TRACE mismatch: actual=%s expected=%s" % [actual[row], expected[row]])
				return false
	return true
