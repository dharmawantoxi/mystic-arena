extends RefCounted

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const Scheduler = preload("res://scripts/match/wave_scheduler.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")


func run(check: Callable) -> void:
	_fixtures(check)
	_capacity(check)
	_transactions(check)
	_death_and_stale_ids(check)
	_progress_and_result(check)
	_hero_melee(check)
	_hero_wall(check)
	_hero_respawn(check)
	_hero_loop(check)
	_hero_foe(check)
	_hero_red_retreat(check)
	_hero_out_of_lane(check)
	_hero_auto(check)
	_castle_auto_scale(check)
	_spawn_jitter(check)
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
			and _foe_hero(world) != null
			and _foe_hero(world).position == world.RED_HERO_SPAWN
			and world.living_minion_count() == 0
		),
		"match starts with a Kaizen pair and no minions"
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
		first.ai_build.total_built == 0 and first.economy.spent[1] == 0,
		"manual red side never spends without the AI switch"
	)
	check.call(
		first.wave_count > 0 and first._next_projectile_id > 1, "scheduled waves lead to combat"
	)


func _hero_melee(check: Callable) -> void:
	var world := _world()
	var hero: HeroState = world.blue_hero()
	var planted: Vector2 = hero.position
	var foe = world.spawn_unit(GOBLIN, 1, 1)
	foe.position = hero.position + Vector2(20, 0)
	# Unkillable dummy: the auto-cast R (140) would otherwise drop the 45 hp
	# goblin before the melee swing this assertion exists to verify.
	_beef(foe)
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
	var hunter: HeroState = hunt.blue_hero()
	var hunt_from: Vector2 = hunter.position
	var quarry = hunt.spawn_unit(GOBLIN, 1, 1)
	quarry.position = hunt_from + Vector2(200, 0)
	var quarry_hp: float = quarry.hp
	hunt.step_tick()
	check.call(
		hunter.position.x > hunt_from.x and quarry.hp == quarry_hp,
		"hero hunts inside 900 without swinging"
	)
	var beyond := _world()
	var idle: HeroState = beyond.blue_hero()
	var parked: Vector2 = idle.position
	var ghost = beyond.spawn_unit(GOBLIN, 1, 1)
	ghost.position = parked + Vector2(950, 0)
	beyond.step_tick()
	check.call(idle.position.x > parked.x, "beyond hunt range the hero pushes")
	var walk := _world()
	var mover: HeroState = walk.blue_hero()
	var from: Vector2 = mover.position
	var dest: Vector2 = from + Vector2(80, 0)
	check.call(walk.set_hero_destination(mover.id, dest), "manual destination accepted")
	walk.step_tick()
	check.call(mover.position.x > from.x and mover.has_destination, "click-move walks toward point")
	check.call(not walk.set_hero_destination(999, dest), "bad id cannot set destination")
	var snapped := false
	for tick in range(50):
		walk.step_tick()
		if not mover.has_destination:
			snapped = mover.position == dest
			break
	check.call(snapped, "hero snaps and clears on arrival")
	var hold := _world()
	var escort: HeroState = hold.blue_hero()
	var origin: Vector2 = escort.position
	hold.set_hero_destination(escort.id, origin + Vector2(80, 0))
	var blocker = hold.spawn_unit(GOBLIN, 1, 1)
	blocker.position = escort.position + Vector2(20, 0)
	_beef(blocker)
	var blocker_hp: float = blocker.hp
	hold.step_tick()
	check.call(
		escort.position.x > origin.x and blocker.hp < blocker_hp,
		"destination still allows an in-range swing"
	)
	var chase := _world()
	var stalker: HeroState = chase.blue_hero()
	var chase_from: Vector2 = stalker.position
	var mark = chase.spawn_unit(GOBLIN, 1, 1)
	mark.position = chase_from + Vector2(180, 0)
	var mark_hp: float = mark.hp
	check.call(chase._set_hero_follow(stalker.id, mark.id), "follow accepted")
	chase.step_tick()
	check.call(
		stalker.follow_id == mark.id and stalker.position.x > chase_from.x and mark.hp == mark_hp,
		"follow walks without swinging out of melee"
	)
	check.call(not chase._set_hero_follow(stalker.id, stalker.id), "cannot follow self")
	chase.set_hero_destination(stalker.id, chase_from)
	check.call(stalker.follow_id == -1 and stalker.has_destination, "destination clears follow")
	mark.alive = false
	var again := _world()
	var chaser: HeroState = again.blue_hero()
	var corpse = again.spawn_unit(GOBLIN, 1, 1)
	corpse.position = chaser.position + Vector2(180, 0)
	again._set_hero_follow(chaser.id, corpse.id)
	corpse.alive = false
	again.step_tick()
	check.call(chaser.follow_id == -1, "dead follow drops")


func _hero_wall(check: Callable) -> void:
	var cover := _world()
	var shielded: HeroState = cover.blue_hero()
	check.call(cover.cast_hero_w(shielded.id), "prototype W casts")
	cover.build_tower(1, 9)
	var tower = cover.get_unit(cover.slots[9].structure_id)
	tower.position = shielded.position + Vector2(40, 0)
	var shielded_hp: float = shielded.hp
	check.call(cover.fire_projectile(tower.id, shielded.id), "red archer looses a shot")
	cover.projectiles[0].position = shielded.position
	cover.step_tick()
	check.call(
		shielded.hp == shielded_hp and shielded.wind_wall_timer > 0,
		"wind wall blocks physical shot"
	)


func _hero_respawn(check: Callable) -> void:
	var world := _world()
	var hero: HeroState = world.blue_hero()
	hero.alive = false
	hero.hp = 0.0
	hero.position = Vector2(800, 200)
	hero.has_destination = true
	var waited := 0
	while waited < 599:
		world.step_tick()
		waited += 1
	check.call(not hero.alive and hero.respawn_timer == 1, "still dead on tick 599")
	world.step_tick()
	check.call(
		(
			hero.alive
			and hero.hp == hero.max_hp
			and hero.position == world.HERO_SPAWN
			and not hero.has_destination
			and hero.respawn_timer == 0
		),
		"hero respawns at spawn after 600 ticks"
	)


func _hero_loop(check: Callable) -> void:
	var flee := _world()
	var runner: HeroState = flee.blue_hero()
	var flee_from: Vector2 = runner.position
	runner.hp = runner.max_hp * 0.1
	flee.step_tick()
	check.call(
		(
			runner.is_retreating
			and (
				runner.position.distance_to(flee.LaneLayout.BLUE_BASE)
				< flee_from.distance_to(flee.LaneLayout.BLUE_BASE)
			)
		),
		"low HP retreats toward own nexus"
	)
	var shop := _world()
	var pupil: HeroState = shop.blue_hero()
	var gold_before: int = shop.economy.gold[0]
	var cost: int = pupil.upgrade_cost()
	check.call(shop._upgrade_blue_hero(pupil.id, 1), "hero upgrade spends")
	check.call(
		pupil.level == 2 and shop.economy.gold[0] == gold_before - cost,
		"level 2 costs source 300 G"
	)
	check.call(not shop._upgrade_blue_hero(pupil.id, 1), "stale hero level rejected")
	shop.economy.gold[0] = 0
	check.call(not shop._upgrade_blue_hero(pupil.id, 2), "poor hero upgrade rejected")


func _hero_foe(check: Callable) -> void:
	var world := _world()
	var stalker: HeroState = _foe_hero(world)
	check.call(
		not world.set_hero_destination(stalker.id, stalker.position), "player cannot order red"
	)
	var from: Vector2 = stalker.position
	world.step_tick()
	check.call(
		(
			stalker.position.distance_to(world.LaneLayout.BLUE_BASE)
			< from.distance_to(world.LaneLayout.BLUE_BASE)
		),
		"red Kaizen pushes toward the blue nexus"
	)
	var flee := _world()
	var runner: HeroState = _foe_hero(flee)
	runner.position = Vector2(640, 360)
	var flee_from: Vector2 = runner.position
	runner.hp = runner.max_hp * 0.1
	flee.step_tick()
	check.call(
		(
			runner.is_retreating
			and (
				runner.position.distance_to(flee.LaneLayout.RED_BASE)
				< flee_from.distance_to(flee.LaneLayout.RED_BASE)
			)
		),
		"low HP red retreats toward own nexus"
	)
	var rest := _world()
	var fallen: HeroState = _foe_hero(rest)
	fallen.alive = false
	fallen.hp = 0.0
	fallen.position = Vector2(400, 400)
	var waited := 0
	while waited < 599:
		rest.step_tick()
		waited += 1
	check.call(not fallen.alive and fallen.respawn_timer == 1, "red still dead on tick 599")
	rest.step_tick()
	check.call(
		fallen.alive and fallen.position == rest.RED_HERO_SPAWN,
		"red respawns at red spawn after 600 ticks"
	)


func _hero_red_retreat(check: Callable) -> void:
	# Source Hero.update state 1 for the red team: retreat walks to the red
	# nexus, heals 3.0/tick inside the 100 px base radius (on top of the 0.15
	# passive trickle), still swings at anything in melee, and only leaves
	# retreat once the HP ratio is back at 0.80.
	var resting := _world()
	var patient: HeroState = _foe_hero(resting)
	patient.hp = patient.max_hp * 0.5
	patient.is_retreating = true
	var hp_before: float = patient.hp
	resting.step_tick()
	check.call(
		(
			patient.is_retreating
			and resting._hero_near_own_base(patient)
			and patient.hp - hp_before >= resting.HERO_BASE_HEAL
		),
		"a retreating red hero heals at its own nexus"
	)
	var march := _world()
	var wanderer: HeroState = _foe_hero(march)
	wanderer.position = Vector2(600, 380)
	wanderer.hp = wanderer.max_hp * 0.5
	wanderer.is_retreating = true
	var foe: UnitState = march.spawn_unit(GOBLIN, march.BLUE, 1)
	foe.position = Vector2(660, 380)
	var foe_hp: float = foe.hp
	var marched: float = wanderer.hp
	march.step_tick()
	check.call(
		(
			wanderer.is_retreating
			and not march._hero_near_own_base(wanderer)
			and wanderer.hp - marched < march.HERO_BASE_HEAL
			and foe.hp < foe_hp
		),
		"away from base a retreating hero only trickles HP, yet still swings"
	)
	var healed := _world()
	var runner: HeroState = _foe_hero(healed)
	runner.hp = runner.max_hp * 0.1
	healed.step_tick()
	check.call(runner.is_retreating, "low HP starts the red retreat")
	runner.hp = runner.max_hp * 0.79
	var guard := 0
	while runner.is_retreating and guard < 200:
		healed.step_tick()
		guard += 1
	check.call(
		(
			not runner.is_retreating
			and runner.hp / runner.max_hp >= healed.HERO_HEAL_RATIO
			and guard < 200
		),
		"the red retreat ends once the HP ratio is back at 0.80"
	)
	var ordered := _world()
	var commanded: HeroState = _foe_hero(ordered)
	# The lane threat stays outside the hero's 100 px skill range: an enemy
	# inside it would be targeted by the shared auto-cast path (source
	# _try_auto_cast sets hero.target), which keeps the AI from reassigning.
	commanded.position = Vector2(700, 380)
	var threat: UnitState = ordered.spawn_unit(GOBLIN, ordered.BLUE, 1)
	threat.position = Vector2(1100, 380)
	commanded.hp = commanded.max_hp * 0.1
	ordered.step_tick()
	check.call(commanded.is_retreating, "the red hero retreats on its own first")
	ordered.ai_hero_control_enabled = true
	ordered.step_tick()
	check.call(
		not commanded.is_retreating and commanded.has_destination and commanded.destination_auto,
		"the AI lane order overrides the retreat (source move_to clears it)"
	)


func _hero_out_of_lane(check: Callable) -> void:
	# Source Hero.update state 5: the hunt search is map-wide, so an enemy in
	# another lane (inside aggro range) pulls the hero off its lane order, and
	# the hunt then takes the nearest enemy by distance, lane or not.
	var hunting := _world()
	var chaser: HeroState = _foe_hero(hunting)
	chaser.position = Vector2(600, 380)
	hunting.move_to(chaser, Vector2(900, 380), true)
	var prey: UnitState = hunting.spawn_unit(GOBLIN, hunting.BLUE, 0)
	prey.position = Vector2(620, 200)
	var y_before: float = chaser.position.y
	hunting.step_tick()
	check.call(
		not chaser.has_destination and chaser.position.y < y_before,
		"an enemy in another lane inside aggro range pulls the hero off its lane order"
	)
	var blind := _world()
	var chooser: HeroState = _foe_hero(blind)
	chooser.position = Vector2(600, 380)
	var lane_foe: UnitState = blind.spawn_unit(GOBLIN, blind.BLUE, 1)
	lane_foe.position = Vector2(1000, 380)
	var side_foe: UnitState = blind.spawn_unit(GOBLIN, blind.BLUE, 0)
	side_foe.position = Vector2(620, 200)
	var lane_gap: float = chooser.position.distance_to(lane_foe.position)
	var side_gap: float = chooser.position.distance_to(side_foe.position)
	var chase_from: float = chooser.position.y
	blind.step_tick()
	check.call(
		(
			side_gap < lane_gap
			and side_gap < blind.HERO_HUNT_RANGE
			and chooser.position.y < chase_from
		),
		"the hunt takes the nearest enemy by distance, lane or not"
	)


func _castle_auto_scale(check: Callable) -> void:
	# Layer 7a: the AI castle auto-levels with the wave number
	# (source Game._auto_scale_ai_castle, thresholds 4/7/10/13). The upgrade is
	# free — Castle.upgrade() never touches gold — and the player castle is
	# never scaled.
	var data = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/match_source.json")
	)
	check.call(data is Dictionary, "match fixture parses for the castle schedule")
	var rows: Array = data.castle_auto_scale
	for row in rows:
		if row.has("shield"):
			continue
		var world := _world()
		world.wave_count = int(row.wave)
		world._auto_scale_ai_castle()
		var red = world.nexuses[Prototype.RED]
		check.call(
			red.settings().level == int(row.level), "castle auto level at wave %d" % int(row.wave)
		)
		check.call(
			(
				red.definition.max_hp == int(row.max_hp)
				and red.definition.damage == int(row.damage)
				and is_equal_approx(red.definition.attack_range_px, float(row.range))
			),
			"castle auto stats at wave %d" % int(row.wave)
		)
		check.call(
			world.nexuses[Prototype.BLUE].settings().level == 1,
			"the player castle is never auto-scaled (wave %d)" % int(row.wave)
		)
		check.call(
			(
				world.economy.spent[Prototype.RED] == 0
				and world.economy.is_balanced()
				and red.hp > 0.0
			),
			"the AI castle levels for free with HP kept (wave %d)" % int(row.wave)
		)
	# A castle that already bought its shield keeps the remaining percentage.
	var shield_row: Dictionary = rows[rows.size() - 1]
	var shielded := _world()
	var nexus = shielded.nexuses[Prototype.RED]
	shielded.wave_count = 4
	shielded._auto_scale_ai_castle()
	nexus.castle_shield_purchased = true
	nexus.shield_max = float(nexus.definition.shield_capacity)
	nexus.shield = nexus.shield_max * 0.5
	shielded.wave_count = int(shield_row.wave)
	shielded._auto_scale_ai_castle()
	check.call(
		(
			nexus.settings().level == int(shield_row.level)
			and is_equal_approx(nexus.shield_max, float(shield_row.shield_max))
			and int(nexus.shield) == int(shield_row.shield)
		),
		"castle auto-scale keeps the purchased shield percentage"
	)
	# Wiring: the level-up happens when a wave actually starts.
	var wired := _world()
	wired.scheduler.wave = 3
	wired.scheduler.remaining_ticks = 1
	wired.step_tick()
	check.call(wired.wave_count == 3, "wave 3 still running before the forced start")
	wired.step_tick()
	check.call(
		wired.wave_count == 4 and wired.nexuses[Prototype.RED].settings().level == 2,
		"starting a wave triggers the AI castle auto-scale"
	)


func _spawn_jitter(check: Callable) -> void:
	# Layer 7b: the source Minion.__init__ spread is ported for wave spawns:
	# uniform(-8, 8) on both axes, then the per-lane Y offset (already applied
	# by spawn_unit). The match seeds the draws, so a restarted run replays even
	# though the Python stream itself is not reproduced.
	var data = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/match_source.json")
	)
	check.call(data is Dictionary and data.has("minion_spawn_offsets"), "spawn offset fixture")
	if not data is Dictionary:
		return
	var contract: Dictionary = data.minion_spawn_offsets
	var jitter := float(contract.jitter)
	var lane_offsets: Array = contract.lane_offsets
	check.call(is_equal_approx(jitter, 8.0), "source spawn jitter radius")
	# JSON numbers are floats; nested Array equality compares types strictly.
	check.call(
		(
			lane_offsets.size() == 3
			and float(lane_offsets[0]) == -20.0
			and float(lane_offsets[1]) == 0.0
			and float(lane_offsets[2]) == 20.0
		),
		"source lane spread offsets"
	)
	for row in contract.rows:
		check.call(
			(
				absf(float(row.offset_x)) <= jitter + 0.0001
				and absf(float(row.offset_y)) <= jitter + 0.0001
			),
			"recorded source offsets stay inside the jitter radius"
		)
		check.call(
			(
				is_equal_approx(
					float(row.final_y),
					float(row.base[1]) + float(row.offset_y) + float(row.lane_offset)
				)
				and is_equal_approx(float(row.lane_offset), float(lane_offsets[int(row.lane)]))
			),
			"source lane offset applies after the jitter"
		)
	var world := _world()
	var hero_position: Vector2 = world.blue_hero().position
	var xs: Array[float] = []
	for lane in range(3):
		for team in range(2):
			for index in range(10):
				var unit := world._spawn_match_minion(GOBLIN, team, lane)
				check.call(unit != null, "jitter spawn succeeds")
				if unit == null:
					continue
				var base: Vector2 = world.paths[lane][
					0 if team == world.BLUE else world.paths[lane].size() - 1
				]
				var offset := float(lane_offsets[lane])
				var dx: float = unit.position.x - base.x
				var dy: float = unit.position.y - base.y - offset
				check.call(
					absf(dx) <= jitter and absf(dy) <= jitter, "native wave minion spawn bounds"
				)
				check.call(
					(
						unit.position.y - base.y >= offset - jitter
						and unit.position.y - base.y <= offset + jitter
					),
					"native lane spread offset"
				)
				xs.append(dx)
	check.call(xs.size() == 60, "jitter sample size")
	check.call(world.blue_hero().position == hero_position, "heroes skip the minion jitter")
	var varies := false
	for value in xs:
		if absf(value - xs[0]) > 0.000001:
			varies = true
			break
	check.call(varies, "jitter draws actually vary")
	# Two fresh worlds consume the same seeded sequence.
	var first := _world()
	var second := _world()
	var same := true
	for lane in range(3):
		for index in range(4):
			var a := first._spawn_match_minion(GOBLIN, world.BLUE, lane)
			var b := second._spawn_match_minion(GOBLIN, world.BLUE, lane)
			if a == null or b == null or a.position != b.position:
				same = false
	check.call(same, "seeded spawn jitter replays")


func _hero_auto(check: Callable) -> void:
	var idle := _world()
	var quiet: HeroState = _foe_hero(idle)
	for tick in range(25):
		idle.step_tick()
	check.call(quiet.r_cooldown == 0 and quiet.skill_timer == 0, "auto-cast idles without a target")
	var storm := _world()
	var caster: HeroState = _foe_hero(storm)
	var bait = storm.spawn_unit(GOBLIN, 0, 1)
	bait.position = caster.position + Vector2(40, 0)
	bait.hp = 100000.0
	storm.step_tick()
	check.call(
		caster.ulti_active and caster.r_cooldown > 0, "auto-cast R when any foe is in skill range"
	)
	var sweep := _world()
	var blade: HeroState = _foe_hero(sweep)
	blade.r_cooldown = 900
	var one = sweep.spawn_unit(GOBLIN, 0, 1)
	var two = sweep.spawn_unit(GOBLIN, 0, 1)
	one.position = blade.position + Vector2(30, 0)
	two.position = blade.position + Vector2(0, 30)
	one.hp = 100000.0
	two.hp = 100000.0
	sweep.step_tick()
	check.call(blade.e_cooldown > 0 and not blade.ulti_active, "auto-cast E when two foes are near")
	var wall := _world()
	var guard: HeroState = _foe_hero(wall)
	guard.r_cooldown = 900
	guard.e_cooldown = 420
	guard.hp = guard.max_hp * 0.3
	var poke = wall.spawn_unit(GOBLIN, 0, 1)
	poke.position = guard.position + Vector2(40, 0)
	poke.hp = 100000.0
	wall.step_tick()
	check.call(guard.wind_wall_timer > 0, "auto-cast W under 40% HP")
	var steel := _world()
	var cutter: HeroState = _foe_hero(steel)
	cutter.r_cooldown = 900
	cutter.e_cooldown = 420
	cutter.w_cooldown = 240
	var mark = steel.spawn_unit(GOBLIN, 0, 1)
	mark.position = cutter.position + Vector2(40, 0)
	mark.hp = 100000.0
	steel.step_tick()
	check.call(cutter.skill_timer > 0 and cutter.q_stack == 1, "auto-cast Q last")
	var off := _world()
	var mute: HeroState = _foe_hero(off)
	mute.auto_cast_enabled = false
	var dummy = off.spawn_unit(GOBLIN, 0, 1)
	dummy.position = mute.position + Vector2(40, 0)
	dummy.hp = 100000.0
	off.step_tick()
	check.call(mute.r_cooldown == 0 and mute.skill_timer == 0, "disabled auto-cast does not fire")
	# Source v27: the player's Kaizen auto-casts exactly like the red copy.
	var parity := _world()
	var player: HeroState = parity.blue_hero()
	check.call(
		player.auto_cast_enabled and player.auto_cast_check_timer == 0,
		"blue spawns with auto-cast on"
	)
	var hook = parity.spawn_unit(GOBLIN, 1, 1)
	hook.position = player.position + Vector2(40, 0)
	_beef(hook)
	parity.step_tick()
	check.call(
		player.ulti_active and player.r_cooldown > 0 and player.skill_timer == 0,
		"blue auto-cast R when a foe is in skill range"
	)
	var calm := _world()
	var still: HeroState = calm.blue_hero()
	for tick in range(25):
		calm.step_tick()
	check.call(
		still.r_cooldown == 0 and still.skill_timer == 0, "blue auto-cast idles without a target"
	)
	var duo := _world()
	var pair: HeroState = duo.blue_hero()
	pair.r_cooldown = 900
	var left = duo.spawn_unit(GOBLIN, 1, 1)
	var right = duo.spawn_unit(GOBLIN, 1, 1)
	left.position = pair.position + Vector2(30, 0)
	right.position = pair.position + Vector2(0, 30)
	_beef(left)
	_beef(right)
	duo.step_tick()
	check.call(pair.e_cooldown > 0 and not pair.ulti_active, "blue auto-cast E with two foes")
	var tired := _world()
	var saver: HeroState = tired.blue_hero()
	saver.r_cooldown = 900
	saver.e_cooldown = 420
	saver.w_cooldown = 240
	var lone = tired.spawn_unit(GOBLIN, 1, 1)
	lone.position = saver.position + Vector2(40, 0)
	_beef(lone)
	tired.step_tick()
	check.call(saver.skill_timer > 0 and saver.q_stack == 1, "blue auto-cast Q last")
	var muted := _world()
	var quiet2: HeroState = muted.blue_hero()
	quiet2.auto_cast_enabled = false
	var dummy2 = muted.spawn_unit(GOBLIN, 1, 1)
	dummy2.position = quiet2.position + Vector2(40, 0)
	_beef(dummy2)
	muted.step_tick()
	check.call(
		quiet2.r_cooldown == 0 and quiet2.skill_timer == 0, "muted blue auto-cast does not fire"
	)
	check.call(muted._set_hero_autocast(quiet2.id), "status command re-enables blue auto-cast")
	muted.step_tick()
	check.call(
		quiet2.auto_cast_enabled and quiet2.ulti_active and quiet2.r_cooldown > 0,
		"re-enabled blue auto-cast fires"
	)
	check.call(not muted._set_hero_autocast(9999), "autocast rejects unknown id")
	var rival = _foe_hero(muted)
	check.call(not muted._set_hero_autocast(rival.id), "autocast refuses the red hero")
	quiet2.alive = false
	check.call(not muted._set_hero_autocast(quiet2.id), "autocast refuses a dead hero")
	muted.winner = 1
	check.call(not muted._set_hero_autocast(rival.id), "autocast refuses a finished match")


func _foe_hero(world: Prototype) -> HeroState:
	for unit in world.units:
		if unit.is_hero and unit.team == 1:
			return unit as HeroState
	return null


func _world() -> Prototype:
	var world := Prototype.new()
	world.setup_arena()
	return world


func _beef(unit: UnitState, hp: int = 100000) -> void:
	# A bare hp bump snaps back: the minion loop clamps unit hp to
	# definition.max_hp every tick (45 for the goblin). Duplicate the
	# definition so the shared GOBLIN fixture stays read-only, raise the
	# cap, then set the hp.
	var beef = GOBLIN.duplicate()
	beef.max_hp = hp
	unit.definition = beef
	unit.hp = float(hp)


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
