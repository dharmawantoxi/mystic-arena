# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8m native suite: the active boss is visible to tower and nexus
## targeting, exactly like the source call sites (`Tower.update` appends any
## living enemy boss inside `self.range` from its `all_units` scan;
## `Castle.update` builds `enemies` from `all_units`, whose last element is the
## live boss). The source oracle executes the real `Tower._find_target` and
## `Castle._find_target` over those lists.
##
## Every case also replays the same world with `active_boss` cleared, which is
## what the native base class does on its own: the recorded
## `expected_without_boss` column proves the boss arm is what changes the
## outcome instead of an accidental ordering.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const FIXTURE := "res://tests/fixtures/boss_structure_targeting_source.json"

const STRUCTURE_POSITION := Vector2(700.0, 300.0)


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(
		(
			fixture is Dictionary
			and fixture.has("source")
			and fixture.has("cases")
			and bool(fixture.source.get("tower_boss_scan", false))
			and bool(fixture.source.get("castle_uses_all_units", false))
			and bool(fixture.source.get("all_units_includes_boss", false))
			and bool(fixture.source.get("grid_includes_boss", false))
		),
		"boss structure targeting fixture parses"
	)
	if not fixture is Dictionary:
		return
	_replay_cases(check, fixture)
	_live_step_tower_and_nexus(check)
	_same_team_and_dead_boss_guards(check)


func _tag(boss: BossState, unit: UnitState, candidate) -> String:
	if candidate == null:
		return "none"
	if candidate == boss:
		return "boss"
	if candidate == unit:
		return "unit"
	return "other"


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(
		cases.size() == 1728,
		"boss structure targeting has eight source cases for all 216 boss types"
	)
	var world := Prototype.new()
	world.setup_arena()
	# One blue tower and the blue nexus are repositioned per row; the structure
	# cap forbids spawning a fresh tower for every one of the 1728 cases.
	var tower: StructureState = world.spawn_structure(ARCHER, world.BLUE, STRUCTURE_POSITION, 0)
	var nexus: StructureState = world.nexuses[world.BLUE]
	check.call(tower != null and nexus != null, "boss structure targeting structures ready")
	if tower == null or nexus == null:
		return
	check.call(
		(
			is_equal_approx(tower.definition.attack_range_px, float(fixture.source.tower_range))
			and is_equal_approx(
				nexus.definition.attack_range_px, float(fixture.source.castle_range)
			)
		),
		"native structure ranges match the source tower/castle level-1 ranges"
	)
	var boss_counts := {}
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		var structure_kind := String(entry.get("structure_kind", "tower"))
		var label := String(entry.get("label", "unknown"))
		boss_counts[boss_type] = int(boss_counts.get(boss_type, 0)) + 1
		var structure := tower if structure_kind == "tower" else nexus
		structure.position = STRUCTURE_POSITION
		check.call(
			is_equal_approx(structure.definition.attack_range_px, float(entry.get("range", -1.0))),
			"boss structure targeting range: %s (%s)" % [label, structure_kind]
		)
		world.units.clear()
		world.active_boss = null
		var boss: BossState = world._spawn_boss(boss_type)
		check.call(boss != null, "boss structure targeting boss loads: %s" % boss_type)
		if boss == null:
			continue
		boss.position = STRUCTURE_POSITION + Vector2(float(entry.get("boss_distance", 0.0)), 0.0)
		boss.previous_position = boss.position
		var unit: UnitState = world.spawn_unit(GOBLIN, world.RED, 0)
		check.call(unit != null, "boss structure targeting unit spawns: %s" % boss_type)
		if unit == null:
			continue
		unit.position = STRUCTURE_POSITION + Vector2(float(entry.get("unit_distance", 0.0)), 0.0)
		var chosen := world._structure_target(structure)
		check.call(
			_tag(boss, unit, chosen) == String(entry.get("expected", "")),
			(
				"boss structure targeting matches source: %s (%s, %s)"
				% [label, structure_kind, boss_type]
			)
		)
		# Same world without the boss: the native base class result.
		world.active_boss = null
		var without := world._structure_target(structure)
		check.call(
			_tag(boss, unit, without) == String(entry.get("expected_without_boss", "")),
			"boss omission keeps the base target: %s (%s, %s)" % [label, structure_kind, boss_type]
		)
	for boss_type in boss_counts:
		check.call(
			int(boss_counts[boss_type]) == 8,
			"boss structure targeting has exactly eight cases for %s" % boss_type
		)


func _live_step_tower_and_nexus(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var tower: StructureState = world.spawn_structure(ARCHER, world.BLUE, STRUCTURE_POSITION, 0)
	var nexus: StructureState = world.nexuses[world.BLUE]
	check.call(tower != null and nexus != null, "live structure step world is ready")
	if tower == null or nexus == null:
		return
	world.units.clear()
	var boss: BossState = world._spawn_boss("gornak")
	check.call(boss != null, "live structure step boss spawns")
	if boss == null:
		return
	# 100 px: inside the 180 px tower range and the 150 px nexus range.
	boss.position = STRUCTURE_POSITION + Vector2(100.0, 0.0)
	boss.previous_position = boss.position
	var boss_hp := boss.hp
	world.step_tick()
	check.call(
		tower.target_id == boss.id and nexus.target_id == boss.id,
		"live tower and nexus acquire the boss through the source boss scan"
	)
	var aimed := 0
	for shot in world.projectiles:
		if shot.target_id == boss.id:
			aimed += 1
	check.call(aimed >= 2, "live tower and nexus fire at the acquired boss")
	var ticks := 0
	while boss.hp >= boss_hp and ticks < 60:
		world.step_tick()
		ticks += 1
	check.call(
		boss.hp < boss_hp and boss.last_hit_source_id == tower.id,
		"tower projectile damages the boss and preserves the source id"
	)


func _same_team_and_dead_boss_guards(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var red_tower: StructureState = world.spawn_structure(ARCHER, world.RED, STRUCTURE_POSITION, 0)
	var blue_tower: StructureState = world.spawn_structure(
		ARCHER, world.BLUE, STRUCTURE_POSITION, 0
	)
	check.call(red_tower != null and blue_tower != null, "guard structures spawn")
	if red_tower == null or blue_tower == null:
		return
	world.units.clear()
	var boss: BossState = world._spawn_boss("gornak")
	if boss == null:
		return
	boss.position = STRUCTURE_POSITION + Vector2(50.0, 0.0)
	boss.previous_position = boss.position
	check.call(
		world._structure_target(red_tower) == null,
		"same-team structure never targets the boss even at close range"
	)
	# Dead boss: the source scan requires `u.alive`, so a nearer dead boss must
	# not hide a living unit inside range.
	var unit: UnitState = world.spawn_unit(GOBLIN, world.RED, 0)
	if unit == null:
		return
	unit.position = STRUCTURE_POSITION + Vector2(120.0, 0.0)
	boss.alive = false
	boss.position = STRUCTURE_POSITION + Vector2(10.0, 0.0)
	check.call(
		world._structure_target(blue_tower) == unit,
		"dead boss is skipped while the living unit is still picked"
	)
