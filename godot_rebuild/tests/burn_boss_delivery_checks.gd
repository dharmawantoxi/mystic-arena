# gdlint:disable=max-file-lines
extends RefCounted
## Layer 9ab native suite: boss burn tick delivery and the boss damage number.

const BossState = preload("res://scripts/match/boss_state.gd")
const MinionBattle = preload("res://scripts/combat/minion_battle.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const FIXTURE := "res://tests/fixtures/burn_boss_delivery_source.json"

const SOURCE_CRIT_PCT := 0.03
const OLD_CRIT_THRESHOLD := 100


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("cases"), "burn boss fixture parses")
	if not fixture is Dictionary:
		return
	_shape_check(check, fixture)
	var world := Prototype.new()
	world.setup_arena()
	for entry in fixture.cases:
		_replay_case(check, world, entry)
	for entry in fixture.refreshes:
		_replay_refresh(check, world, entry)
	_store_check(check, world, fixture)
	_fire_ignores_attacker(check, world)
	_burn_kill_credit(check, world)
	_sourced_control(check, world)


func _shape_check(check: Callable, fixture: Dictionary) -> void:
	var stats: Dictionary = fixture.get("live_stats", {})
	check.call(
		(
			is_equal_approx(float(stats.get("crit_pct", 0.0)), SOURCE_CRIT_PCT)
			and int(stats.get("old_crit_threshold", 0)) == OLD_CRIT_THRESHOLD
		),
		"burn boss fixture records the source 3% rule and the pre-9ab 100 threshold"
	)
	var burn_shape: Dictionary = fixture.get("burn_shape", {})
	check.call(
		(
			int(burn_shape.get("take_damage_calls", 0)) == 1
			and bool(burn_shape.get("three_positional_args", false))
			and bool(burn_shape.get("third_arg_is_fire", false))
			and bool(burn_shape.get("no_source_keyword", false))
			and bool(burn_shape.get("no_school_keyword", false))
			and int(burn_shape.get("burn_tick_interval", 0)) == int(stats.get("tick_frames", 0))
		),
		"source burn tick call shape is the pinned three-argument fire hit"
	)
	var number_shape: Dictionary = fixture.get("boss_number_shape", {})
	check.call(
		(
			int(number_shape.get("damage_numbers_calls", 0)) == 1
			and bool(number_shape.get("y_is_self_y_radius_minus_10", false))
			and bool(number_shape.get("crit_is_hp_pct", false))
			and int(number_shape.get("particles_count", 0)) == 6
			and bool(number_shape.get("killed_by_is_source", false))
			and bool(number_shape.get("clears_debuffs_on_death", false))
		),
		"source boss damage number shape is the pinned presentation tail"
	)


func _replay_case(check: Callable, world: Prototype, entry: Dictionary) -> void:
	var label := String(entry.get("name", "unknown"))
	var boss := _spawn(world, String(entry.get("kind", "gornak")))
	if boss == null:
		check.call(false, "burn boss probe spawns: %s" % label)
		return
	var input: Dictionary = entry.get("input", {})
	boss.hp = float(input.get("hp", 100000.0))
	boss.burn_dps = float(input.get("burn_dps", 0.0))
	boss.burn_timer = int(input.get("burn_timer", 0))
	boss.burn_accum = float(input.get("burn_accum", 0.0))
	boss.burn_tick_cd = int(input.get("burn_tick_cd", 30))
	boss.burn_team = _team_code(input.get("burn_team"))
	if input.has("dmg_amp_amount"):
		boss.dmg_amp_amount = float(input["dmg_amp_amount"])
		boss.dmg_amp_timer = int(input["dmg_amp_timer"])
	if input.has("armor_shred_amount"):
		boss.armor_shred_amount = float(input["armor_shred_amount"])
		boss.armor_shred_timer = int(input["armor_shred_timer"])
	if input.has("defense_boost"):
		boss.defense_boost = bool(input["defense_boost"])
	var origin := boss.position
	var before_hp := boss.hp
	world.effects.floating_texts.clear()
	world._step_active_boss()
	var expected: Dictionary = entry.get("expected", {})
	var old: Dictionary = entry.get("native_old", {})
	var dealt := int(before_hp - boss.hp)
	check.call(
		dealt == int(expected.get("hp_loss", -1)),
		"boss burn tick payload matches source: %s" % label
	)
	check.call(
		boss.last_hit_source_id == -1,
		"source-free burn tick keeps the attribution sentinel: %s" % label
	)
	check.call(
		(
			is_equal_approx(boss.burn_accum, float(expected.get("burn_accum", 0.0)))
			and boss.burn_tick_cd == int(expected.get("burn_tick_cd", 0))
		),
		"boss burn accumulator and clock match source: %s" % label
	)
	check.call(
		int(expected.get("credits", -1)) == 0 and expected.get("killed_by", "missing") == null,
		"source fixture row stays unattributed: %s" % label
	)
	_damage_number(check, world, boss, origin, label, dealt, expected, old)


func _damage_number(
	check: Callable,
	world: Prototype,
	boss: BossState,
	origin: Vector2,
	label: String,
	dealt: int,
	expected: Dictionary,
	old: Dictionary
) -> void:
	var texts: Array = world.effects.floating_texts
	check.call(not texts.is_empty(), "boss burn tick draws one damage number: %s" % label)
	if texts.is_empty():
		return
	var number = texts[texts.size() - 1]
	var source_crit: bool = float(dealt) > float(boss.max_hp) * SOURCE_CRIT_PCT
	check.call(
		bool(number.critical) == source_crit,
		"boss damage number follows the source 3%% hp crit rule: %s" % label
	)
	check.call(
		bool(number.critical) == bool(expected.get("is_critical", not source_crit)),
		"boss damage number matches the fixture crit column: %s" % label
	)
	check.call(
		is_equal_approx(float(number.y), origin.y - boss.radius - 10.0),
		"boss damage number anchor is source y - radius - 10: %s" % label
	)
	if int(old.get("hp_loss", 0)) != dealt:
		return
	if bool(old.get("is_critical", false)) == bool(expected.get("is_critical", false)):
		return
	check.call(
		bool(number.critical) != bool(old.get("is_critical", false)),
		"pre-9ab flat 100 crit threshold is gone: %s" % label
	)


func _replay_refresh(check: Callable, world: Prototype, entry: Dictionary) -> void:
	var label := String(entry.get("name", "unknown"))
	var boss := _spawn(world, String(entry.get("kind", "gornak")))
	if boss == null:
		check.call(false, "burn refresh probe spawns: %s" % label)
		return
	var input: Dictionary = entry.get("input", {})
	boss.burn_dps = float(input.get("burn_dps", 0.0))
	boss.burn_timer = int(input.get("burn_timer", 0))
	boss.burn_accum = float(input.get("burn_accum", 0.0))
	boss.burn_tick_cd = int(input.get("burn_tick_cd", 30))
	boss.burn_team = -1
	boss.apply_debuff(
		"burn",
		float(input.get("refresh_dps", 60.0)),
		int(input.get("refresh_duration", 120)),
		_team_code(input.get("refresh_team"))
	)
	var result: Dictionary = entry.get("result", {})
	check.call(
		(
			is_equal_approx(boss.burn_dps, float(result.get("burn_dps", -1.0)))
			and boss.burn_timer == int(result.get("burn_timer", -1))
			and is_equal_approx(boss.burn_accum, float(result.get("burn_accum", -1.0)))
			and boss.burn_tick_cd == int(result.get("burn_tick_cd", -1))
		),
		"boss burn store refresh matches source: %s" % label
	)
	check.call(
		boss.burn_team == _team_code(result.get("burn_team")),
		"boss burn store follows the source team: %s" % label
	)


func _store_check(check: Callable, world: Prototype, fixture: Dictionary) -> void:
	var bus_boss := _spawn(world, "gornak")
	var store_boss := _spawn(world, "gornak")
	if bus_boss == null or store_boss == null:
		check.call(false, "burn store probes spawn")
		return
	for boss in [bus_boss, store_boss]:
		boss.burn_dps = 0.0
		boss.burn_timer = 0
		boss.burn_accum = 9.9
		boss.burn_tick_cd = 3
		boss.burn_team = -1
	world.apply_burn(bus_boss.id, 60.0, 120, world.BLUE)
	store_boss.apply_debuff("burn", 60.0, 120, world.BLUE)
	var fields := ["burn_dps", "burn_timer", "burn_accum", "burn_tick_cd", "burn_team"]
	var equal := true
	for field in fields:
		equal = equal and bus_boss.get(field) == store_boss.get(field)
	check.call(equal, "world apply_burn and the boss store agree for a boss victim")
	var expected: Dictionary = fixture.refreshes[0].result
	check.call(
		(
			is_equal_approx(store_boss.burn_dps, float(expected.burn_dps))
			and store_boss.burn_timer == int(expected.burn_timer)
			and is_equal_approx(store_boss.burn_accum, float(expected.burn_accum))
			and store_boss.burn_tick_cd == int(expected.burn_tick_cd)
			and store_boss.burn_team == _team_code(expected.burn_team)
		),
		"native boss burn store equals the executed source refresh row"
	)
	var stats: Dictionary = fixture.live_stats
	check.call(
		(
			int(store_boss.rules.get("burn_tick", 0)) == int(stats.tick_frames)
			and is_equal_approx(BossState.DEBUFF_FPS, float(stats.get("burn_fps", 0.0)))
			and MinionBattle.BURN_TICK_INTERVAL == int(stats.tick_frames)
		),
		"native burn tick interval equals the source constants"
	)
	var mini: Dictionary = stats.mini
	check.call(
		(
			int(bus_boss.max_damage_per_hit) == int(mini.max_damage_per_hit)
			and is_equal_approx(bus_boss.damage_reduction, float(mini.damage_reduction))
		),
		"live mini-boss resilience and anti-burst cap match the fixture"
	)
	var true_boss: Dictionary = stats.true_boss
	var big := _spawn(world, String(true_boss.kind))
	check.call(
		(
			big != null
			and int(big.max_damage_per_hit) == int(true_boss.max_damage_per_hit)
			and is_equal_approx(big.damage_reduction, float(true_boss.damage_reduction))
		),
		"live true-boss resilience and anti-burst cap match the fixture"
	)


func _fire_ignores_attacker(check: Callable, world: Prototype) -> void:
	var free_boss := _spawn(world, "gornak")
	var sourced_boss := _spawn(world, "gornak")
	if free_boss == null or sourced_boss == null:
		check.call(false, "fire ladder probes spawn")
		return
	var hero = world.spawn_hero(Prototype.KAIZEN, world.BLUE, free_boss.position + Vector2(40, 0))
	for boss in [free_boss, sourced_boss]:
		boss.hp = float(boss.max_hp)
	var free_before := free_boss.hp
	world._deliver_hit(-1, world.RED, free_boss, 30, "neutral", free_boss.position, "fire")
	var sourced_before := sourced_boss.hp
	world._deliver_hit(
		hero.id, world.BLUE, sourced_boss, 30, "neutral", sourced_boss.position, "fire"
	)
	check.call(
		int(free_before - free_boss.hp) == int(sourced_before - sourced_boss.hp),
		"fire damage ignores the attacker, so a sourced fire hit lands the tick payload"
	)
	check.call(
		int(free_before - free_boss.hp) == 24,
		"fire payload keeps the 0.20 mini-boss resilience: 30 -> 24"
	)


func _burn_kill_credit(check: Callable, world: Prototype) -> void:
	var boss := _spawn(world, "gornak")
	if boss == null:
		check.call(false, "burn kill-credit probe spawns")
		return
	boss.hp = 20.0
	boss.burn_dps = 60.0
	boss.burn_timer = 2
	boss.burn_accum = 29.5
	boss.burn_tick_cd = 1
	boss.burn_team = world.BLUE
	boss.last_hit_is_miasma_tick = true
	var unlocks_before := world.achievements_unlocked.size()
	world._step_active_boss()
	check.call(not boss.alive and boss.defeated, "lethal boss burn defeats the boss")
	check.call(boss.last_hit_source_id == -1, "lethal boss burn keeps the attribution sentinel")
	check.call(
		is_equal_approx(boss.burn_dps, 0.0) and boss.burn_timer == 0,
		"lethal boss burn clears the debuff store like the source death tail"
	)
	world._process_boss_kill(boss)
	check.call(
		world.kills[world.BLUE] == 0 and world.kills[world.RED] == 0,
		"lethal boss burn credits nobody, stale miasma flag or not"
	)
	check.call(
		(
			int(world.miniboss_kill_count) == 0
			and int(world.trueboss_kill_count) == 0
			and world.achievements_unlocked.size() == unlocks_before
		),
		"lethal boss burn unlocks no slayer achievement"
	)


func _sourced_control(check: Callable, world: Prototype) -> void:
	var boss := _spawn(world, "gornak")
	if boss == null:
		check.call(false, "sourced control probe spawns")
		return
	var hero = world.spawn_hero(Prototype.KAIZEN, world.BLUE, boss.position + Vector2(40, 0))
	boss.hp = 10.0
	check.call(
		world._deliver_hit(hero.id, world.BLUE, boss, 40, "neutral", boss.position),
		"control: a sourced hit on a boss still lands"
	)
	world._process_boss_kill(boss)
	check.call(
		world.kills[world.BLUE] == 1 and int(world.miniboss_kill_count) == 1,
		"control: a blue hero lethal hit still credits the kill"
	)


func _spawn(world: Prototype, kind: String) -> BossState:
	# Each probe needs its own live boss: `_spawn_boss` refuses to spawn while
	# one is active, so the registry slot is released first (the fixture rows
	# compare two or three bosses side by side).
	world.active_boss = null
	var boss: BossState = world._spawn_boss(kind)
	if boss == null:
		return null
	boss.entrance_timer = 0
	return boss


func _team_code(value: Variant) -> int:
	if value == null:
		return -1
	if value is int or value is float:
		return int(value)
	if String(value) == "blue":
		return 0
	if String(value) == "red":
		return 1
	return -1
