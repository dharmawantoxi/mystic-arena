# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8t native suite: archer multi-shot volleys (levels 5/6) and mage chain
## bolts (levels 2..6) include the living in-range enemy boss as a secondary
## target when a closer unit is the primary target, matching `Tower.update` ->
## `Tower._shoot(enemies)` -> `_shoot_archer` / `_shoot_mage`.
##
## Every fixture row carries both source-executed columns: `expected` (with the
## live boss in `all_units`) and `expected_without_boss` (the pre-layer
## `units`-only scan). The replay verifies both columns through
## `PrototypeBattle.fire_projectile`, plus live ticks for archer L5 and mage L2
## and guard checks for dead, same-team, primary-target and full-capacity cases.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const ARCHER_FIVE = preload("res://data/structures/archer_level_5.tres")
const ARCHER_SIX = preload("res://data/structures/archer_level_6.tres")
const MAGE_TWO = preload("res://data/structures/mage_level_2.tres")
const MAGE_SIX = preload("res://data/structures/mage_level_6.tres")
const FIXTURE := "res://tests/fixtures/boss_tower_volley_source.json"

const TOWER_POS := Vector2(500.0, 340.0)
# Keep live-tick structures far from the default arena nexuses/heroes so only
# the tower under test interacts with the minion and the boss.
const LIVE_TOWER := Vector2(1840.0, 1500.0)
const LIVE_BOSS := "gornak"
const SOURCE_FLAGS := [
	"tower_boss_scan_in_update",
	"tower_update_passes_enemies_to_shoot",
	"shoot_dispatches_archer_and_mage",
	"archer_volley_scans_enemies_inclusive",
	"archer_volley_refills_primary",
	"mage_chain_scans_enemies_inclusive",
	"mage_chain_has_no_refill",
	"all_units_includes_boss"
]


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var parsed: bool = fixture is Dictionary and fixture.has("source") and fixture.has("cases")
	if parsed:
		for flag in SOURCE_FLAGS:
			parsed = parsed and bool(fixture.source.get(flag, false))
	check.call(parsed, "boss tower volley fixture parses with every source flag")
	if not fixture is Dictionary:
		return
	_check_towers(check, fixture)
	_replay_cases(check, fixture)
	_live_volleys(check)
	_guard_cases(check)


func _check_towers(check: Callable, fixture: Dictionary) -> void:
	var src: Dictionary = fixture.get("source", {})
	var a5: Dictionary = src.get("archer_l5", {})
	var a6: Dictionary = src.get("archer_l6", {})
	var m2: Dictionary = src.get("mage_l2", {})
	var m6: Dictionary = src.get("mage_l6", {})
	(
		check
		. call(
			(
				is_equal_approx(ARCHER_FIVE.attack_range_px, float(a5.get("range", -1.0)))
				and ARCHER_FIVE.volley_count == int(a5.get("volley_count", -1))
				and is_equal_approx(ARCHER_SIX.attack_range_px, float(a6.get("range", -1.0)))
				and ARCHER_SIX.volley_count == int(a6.get("volley_count", -1))
				and is_equal_approx(MAGE_TWO.attack_range_px, float(m2.get("range", -1.0)))
				and MAGE_TWO.chain_count == int(m2.get("chain", -1))
				and is_equal_approx(MAGE_SIX.attack_range_px, float(m6.get("range", -1.0)))
				and MAGE_SIX.chain_count == int(m6.get("chain", -1))
			),
			"native archer L5/L6 and mage L2/L6 resources match the source range and volley/chain counts"
		)
	)


func _tower_def(path: String, level: int):
	if path == "archer":
		return ARCHER_FIVE if level == 5 else ARCHER_SIX
	return MAGE_TWO if level == 2 else MAGE_SIX


func _shot_tags(
	projectiles: Array, spawned_units: Array[UnitState], boss: BossState
) -> Array[String]:
	var tags: Array[String] = []
	for shot in projectiles:
		if boss != null and shot.target_id == boss.id:
			tags.append("boss")
			continue
		var matched := false
		for index in range(spawned_units.size()):
			if shot.target_id == spawned_units[index].id:
				tags.append("unit_%d" % (index + 1))
				matched = true
				break
		if not matched:
			tags.append("unknown")
	return tags


func _matches_expected(
	projectiles: Array, spawned_units: Array[UnitState], boss: BossState, expected: Dictionary
) -> bool:
	var tags := _shot_tags(projectiles, spawned_units, boss)
	var expected_targets: Array = expected.get("shot_targets", [])
	if tags.size() != expected_targets.size():
		return false
	if tags.size() != int(expected.get("shot_count", -1)):
		return false
	var boss_hits := 0
	for index in range(tags.size()):
		if tags[index] != String(expected_targets[index]):
			return false
		if tags[index] == "boss":
			boss_hits += 1
	return boss_hits == int(expected.get("boss_shots", -1))


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(
		cases.size() == 864, "boss tower volley has four source cases for all 216 boss types"
	)
	var world := Prototype.new()
	world.setup_arena()
	var counts := {}
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		var label := String(entry.get("label", "unknown"))
		var path := String(entry.get("tower_path", "archer"))
		var level := int(entry.get("level", 5))
		var unit_distances: Array = entry.get("unit_distances", [])
		var boss_distance := float(entry.get("boss_distance", 0.0))
		counts[boss_type] = int(counts.get(boss_type, 0)) + 1
		world.units.clear()
		world.projectiles.clear()
		world.active_boss = null
		while world.structures.size() > 2:
			var old: StructureState = world.structures.pop_back()
			world._by_id.erase(old.id)
		var tower: StructureState = world.spawn_structure(
			_tower_def(path, level), world.BLUE, TOWER_POS, 1
		)
		check.call(tower != null, "volley tower spawns: %s (%s)" % [label, boss_type])
		if tower == null:
			continue
		var spawned_units: Array[UnitState] = []
		for offset in unit_distances:
			var minion: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
			if minion != null:
				minion.position = TOWER_POS + Vector2(float(offset), 0.0)
				spawned_units.append(minion)
		var boss: BossState = world._spawn_boss(boss_type)
		check.call(boss != null, "boss tower volley boss loads: %s" % boss_type)
		if boss == null or spawned_units.is_empty():
			continue
		boss.position = TOWER_POS + Vector2(boss_distance, 0.0)
		boss.previous_position = boss.position
		var chosen: UnitState = world._structure_target(tower)
		check.call(
			chosen == spawned_units[0],
			"nearest unit stays primary target before volley: %s (%s)" % [label, boss_type]
		)
		check.call(
			world.fire_projectile(tower.id, spawned_units[0].id),
			"tower volley fires with boss present: %s (%s)" % [label, boss_type]
		)
		check.call(
			_matches_expected(world.projectiles, spawned_units, boss, entry.get("expected", {})),
			"tower volley matches source with boss: %s (%s)" % [label, boss_type]
		)
		world.projectiles.clear()
		tower.cooldown_ticks = 0
		world.active_boss = null
		check.call(
			world.fire_projectile(tower.id, spawned_units[0].id),
			"tower volley fires without boss: %s (%s)" % [label, boss_type]
		)
		check.call(
			_matches_expected(
				world.projectiles, spawned_units, null, entry.get("expected_without_boss", {})
			),
			"tower volley matches pre-layer baseline without boss: %s (%s)" % [label, boss_type]
		)
	for boss_type in counts:
		check.call(
			int(counts[boss_type]) == 4,
			"boss tower volley has exactly four cases for %s" % boss_type
		)


func _live_volleys(check: Callable) -> void:
	# Live archer L5: minion at 80 px is primary target; boss at 160 px takes the second arrow.
	var archer_world := Prototype.new()
	archer_world.setup_arena()
	archer_world.units.clear()
	var archer_tower: StructureState = archer_world.spawn_structure(
		ARCHER_FIVE, archer_world.BLUE, LIVE_TOWER, 1
	)
	var archer_minion: UnitState = archer_world.spawn_unit(GOBLIN, archer_world.RED, 1)
	var archer_boss: BossState = archer_world._spawn_boss(LIVE_BOSS)
	check.call(
		archer_tower != null and archer_minion != null and archer_boss != null,
		"live archer L5 volley entities spawn"
	)
	if archer_tower == null or archer_minion == null or archer_boss == null:
		return
	archer_minion.hp = 10000.0
	var boss_hp_before := archer_boss.hp
	var ticks := 0
	while archer_boss.hp == boss_hp_before and ticks < 240:
		archer_minion.position = LIVE_TOWER + Vector2(80.0, 0.0)
		archer_boss.position = LIVE_TOWER + Vector2(160.0, 0.0)
		archer_boss.previous_position = archer_boss.position
		archer_world.step_tick()
		ticks += 1
	check.call(
		archer_boss.hp < boss_hp_before,
		"live archer L5 secondary arrow lands on the boss while the closer minion is primary"
	)

	# Live mage L2: minion at 60 px is primary target; boss at 140 px takes the chain bolt.
	var mage_world := Prototype.new()
	mage_world.setup_arena()
	mage_world.units.clear()
	var mage_tower: StructureState = mage_world.spawn_structure(
		MAGE_TWO, mage_world.BLUE, LIVE_TOWER, 1
	)
	var mage_minion: UnitState = mage_world.spawn_unit(GOBLIN, mage_world.RED, 1)
	var mage_boss: BossState = mage_world._spawn_boss(LIVE_BOSS)
	check.call(
		mage_tower != null and mage_minion != null and mage_boss != null,
		"live mage L2 chain entities spawn"
	)
	if mage_tower == null or mage_minion == null or mage_boss == null:
		return
	mage_minion.hp = 10000.0
	var mage_hp_before := mage_boss.hp
	var mage_ticks := 0
	while mage_boss.skill_down_timer <= 0 and mage_ticks < 240:
		mage_minion.position = LIVE_TOWER + Vector2(60.0, 0.0)
		mage_boss.position = LIVE_TOWER + Vector2(140.0, 0.0)
		mage_boss.previous_position = mage_boss.position
		mage_world.step_tick()
		mage_ticks += 1
	check.call(
		(
			mage_boss.hp < mage_hp_before
			and mage_boss.skill_down_timer > 0
			and is_equal_approx(mage_boss.skill_down_amount, 0.2)
			and is_equal_approx(mage_boss.anti_heal_amount, 0.4)
		),
		"live mage L2 chain bolt damages and debuffs the secondary boss target"
	)


func _guard_cases(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	world.units.clear()
	var archer_tower: StructureState = world.spawn_structure(ARCHER_FIVE, world.BLUE, TOWER_POS, 1)
	var mage_tower: StructureState = world.spawn_structure(MAGE_TWO, world.BLUE, TOWER_POS, 1)
	var minion_one: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
	var boss: BossState = world._spawn_boss(LIVE_BOSS)
	check.call(
		archer_tower != null and mage_tower != null and minion_one != null and boss != null,
		"volley guard entities spawn"
	)
	if archer_tower == null or mage_tower == null or minion_one == null or boss == null:
		return
	minion_one.position = TOWER_POS + Vector2(60.0, 0.0)
	boss.position = TOWER_POS + Vector2(120.0, 0.0)

	# Dead boss: ignored by both archer volley and mage chain.
	boss.alive = false
	world.projectiles.clear()
	archer_tower.cooldown_ticks = 0
	world.fire_projectile(archer_tower.id, minion_one.id)
	check.call(
		(
			world.projectiles.size() == 2
			and world.projectiles[0].target_id == minion_one.id
			and world.projectiles[1].target_id == minion_one.id
		),
		"dead boss is skipped by archer volley and refilled with primary target"
	)
	world.projectiles.clear()
	mage_tower.cooldown_ticks = 0
	world.fire_projectile(mage_tower.id, minion_one.id)
	check.call(
		world.projectiles.size() == 1 and world.projectiles[0].target_id == minion_one.id,
		"dead boss is skipped by mage chain without refill"
	)

	# Same-team boss: ignored by both archer volley and mage chain.
	boss.alive = true
	boss.team = world.BLUE
	world.projectiles.clear()
	archer_tower.cooldown_ticks = 0
	world.fire_projectile(archer_tower.id, minion_one.id)
	check.call(
		(
			world.projectiles.size() == 2
			and world.projectiles[0].target_id == minion_one.id
			and world.projectiles[1].target_id == minion_one.id
		),
		"same-team boss is never targeted by archer volley"
	)
	world.projectiles.clear()
	mage_tower.cooldown_ticks = 0
	world.fire_projectile(mage_tower.id, minion_one.id)
	check.call(
		world.projectiles.size() == 1 and world.projectiles[0].target_id == minion_one.id,
		"same-team boss is never targeted by mage chain"
	)

	# Boss is already the solo primary target: mage fires 1 bolt (not 2), archer refills to 2.
	boss.team = world.RED
	minion_one.position = TOWER_POS + Vector2(500.0, 0.0)
	world.projectiles.clear()
	mage_tower.cooldown_ticks = 0
	world.fire_projectile(mage_tower.id, boss.id)
	check.call(
		world.projectiles.size() == 1 and world.projectiles[0].target_id == boss.id,
		"solo primary-target boss is not duplicated as a mage chain target"
	)
	world.projectiles.clear()
	archer_tower.cooldown_ticks = 0
	world.fire_projectile(archer_tower.id, boss.id)
	check.call(
		(
			world.projectiles.size() == 2
			and world.projectiles[0].target_id == boss.id
			and world.projectiles[1].target_id == boss.id
		),
		"solo primary-target boss still receives the archer refill arrow"
	)

	# Full capacity from ordinary units: two minions fill archer L5 before the boss.
	minion_one.position = TOWER_POS + Vector2(60.0, 0.0)
	var minion_two: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
	if minion_two == null:
		return
	minion_two.position = TOWER_POS + Vector2(90.0, 0.0)
	world.projectiles.clear()
	archer_tower.cooldown_ticks = 0
	world.fire_projectile(archer_tower.id, minion_one.id)
	check.call(
		(
			world.projectiles.size() == 2
			and world.projectiles[0].target_id == minion_one.id
			and world.projectiles[1].target_id == minion_two.id
		),
		"ordinary units fill the volley cap before the trailing boss entry"
	)
