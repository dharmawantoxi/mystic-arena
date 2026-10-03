# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8n native suite: the active boss is visible to minion targeting, just
## like the source. `Minion._get_enemies` reads its candidates from the spatial
## grid and `Game.update` indexes the live boss there as the LAST hero entry
## (`spatial_heroes + [active_boss]`), inside `self.range + 30`; towers and
## bases are appended after the grid results. `_find_target_smart` then groups
## with `isinstance(e, Minion)`, so the boss is a target but never a member of
## the lane/lowest-hp minion groups, while the siege group (`max_hp >= 1500`,
## first match wins) sees it ahead of every appended tower.
##
## Every fixture row also replays the same world with `active_boss` cleared, the
## native base behaviour before this layer: the recorded `expected_without_boss`
## column proves the boss arm is what changes the outcome.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const FIXTURE := "res://tests/fixtures/boss_minion_targeting_source.json"

# Cell-aligned origin: every scenario offset stays inside one 60 px grid cell,
# so the source bucket order (minions, heroes, boss) is deterministic.
const QUERIER := Vector2(600.0, 300.0)
const PARKED := Vector2(5000.0, 5000.0)
const SOURCE_FLAGS := [
	"query_radius_source",
	"grid_indexes_boss",
	"grid_inserts_heroes",
	"selection_order",
	"minion_groups_exclude_boss",
	"siege_group_uses_max_hp"
]


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var parsed := fixture is Dictionary and fixture.has("source") and fixture.has("cases")
	if parsed:
		for flag in SOURCE_FLAGS:
			parsed = parsed and bool(fixture.source.get(flag, false))
	check.call(parsed, "boss minion targeting fixture parses with every source flag")
	if not fixture is Dictionary:
		return
	_replay_cases(check, fixture)
	_live_minion_engages_boss(check)
	_guard_cases(check)


func _tag(boss: BossState, unit: UnitState, tower: StructureState, candidate) -> String:
	if candidate == null:
		return "none"
	if candidate == boss:
		return "boss"
	if candidate == unit:
		return "unit"
	if candidate == tower:
		return "tower"
	return "other"


func _park_structures(world: Prototype) -> void:
	# The oracle rows carry at most one tower; everything else must stay out of
	# both the attack range and the source grid radius.
	for structure in world.structures:
		structure.position = PARKED


func _red_tower(world: Prototype) -> StructureState:
	for structure in world.structures:
		if structure.team == world.RED and structure.definition.structure_kind == "tower":
			return structure
	return null


func _placed_minion(world: Prototype, team: int, at: Vector2) -> UnitState:
	var unit := world.spawn_unit(GOBLIN, team, 0)
	if unit == null:
		return null
	# Castle-tier scaling must not move the source goblin numbers this suite pins.
	unit.definition = GOBLIN
	unit.hp = float(GOBLIN.max_hp)
	unit.position = at
	return unit


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(
		cases.size() == 864, "boss minion targeting has four source cases for all 216 boss types"
	)
	var world := Prototype.new()
	world.setup_arena()
	check.call(not world.structures.is_empty(), "boss minion targeting arena is ready")
	check.call(
		(
			is_equal_approx(GOBLIN.attack_range_px, float(fixture.source.get("minion_range", -1.0)))
			and is_equal_approx(GOBLIN.max_hp, float(fixture.source.get("minion_hp", -1.0)))
			and is_equal_approx(ARCHER.max_hp, float(fixture.source.get("tower_max_hp", -1.0)))
		),
		"native goblin range/hp and archer hp match the source tables"
	)
	var boss_counts := {}
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		var label := String(entry.get("label", "unknown"))
		boss_counts[boss_type] = int(boss_counts.get(boss_type, 0)) + 1
		world.units.clear()
		world.active_boss = null
		_park_structures(world)
		var boss: BossState = world._spawn_boss(boss_type)
		check.call(boss != null, "boss minion targeting boss loads: %s" % boss_type)
		if boss == null:
			continue
		boss.position = QUERIER + Vector2(float(entry.get("boss_distance", 0.0)), 0.0)
		boss.previous_position = boss.position
		if entry.get("boss_hp", null) != null:
			boss.hp = float(entry.get("boss_hp"))
		var querier := _placed_minion(world, world.BLUE, QUERIER)
		var unit := _placed_minion(
			world, world.RED, QUERIER + Vector2(float(entry.get("unit_distance", 0.0)), 0.0)
		)
		check.call(querier != null and unit != null, "boss minion targeting minions spawn")
		if querier == null or unit == null:
			continue
		querier.ai_level = int(entry.get("ai_level", 1))
		unit.hp = float(entry.get("unit_hp", querier.hp))
		check.call(
			is_equal_approx(querier.definition.attack_range_px, float(entry.get("range", -1.0))),
			"boss minion targeting range: %s" % label
		)
		var tower: StructureState = null
		if entry.get("tower_distance", null) != null:
			tower = _red_tower(world)
			check.call(tower != null, "boss minion targeting tower ready: %s" % label)
			if tower == null:
				continue
			tower.position = QUERIER + Vector2(float(entry.get("tower_distance")), 0.0)
		var chosen := world._find_target(querier)
		check.call(
			_tag(boss, unit, tower, chosen) == String(entry.get("expected", "")),
			"boss minion targeting matches source: %s (%s)" % [label, boss_type]
		)
		# Same world without the boss: the native base class result.
		world.active_boss = null
		var without := world._find_target(querier)
		check.call(
			_tag(boss, unit, tower, without) == String(entry.get("expected_without_boss", "")),
			"boss omission keeps the base target: %s (%s)" % [label, boss_type]
		)
	for boss_type in boss_counts:
		check.call(
			int(boss_counts[boss_type]) == 4,
			"boss minion targeting has exactly four cases for %s" % boss_type
		)


func _live_minion_engages_boss(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	_park_structures(world)
	world.units.clear()
	var boss: BossState = world._spawn_boss("gornak")
	check.call(boss != null, "live minion step boss spawns")
	if boss == null:
		return
	# 40 px: outside the 25 px attack range, inside the source `range + 30`
	# lookup radius, so the minion must chase and then swing.
	boss.position = QUERIER + Vector2(40.0, 0.0)
	boss.previous_position = boss.position
	var striker := _placed_minion(world, world.BLUE, QUERIER)
	check.call(striker != null, "live minion striker spawns")
	if striker == null:
		return
	var boss_hp := boss.hp
	world.step_tick()
	check.call(
		striker.target_id == boss.id, "live blue minion acquires the boss inside the grid radius"
	)
	check.call(striker.position.x > QUERIER.x, "live blue minion walks toward the acquired boss")
	var ticks := 0
	while boss.hp >= boss_hp and ticks < 120:
		world.step_tick()
		ticks += 1
	check.call(
		boss.hp < boss_hp and boss.last_hit_source_id == striker.id,
		"live minion damage reaches the boss and preserves the source id"
	)


func _guard_cases(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	_park_structures(world)
	world.units.clear()
	var boss: BossState = world._spawn_boss("gornak")
	check.call(boss != null, "guard world boss spawns")
	if boss == null:
		return
	boss.position = QUERIER + Vector2(10.0, 0.0)
	boss.previous_position = boss.position
	var red_minion := _placed_minion(world, world.RED, QUERIER)
	check.call(
		red_minion != null and world._find_target(red_minion) == null,
		"same-team minion never targets the boss even at point blank"
	)
	var blue_minion := _placed_minion(world, world.BLUE, QUERIER)
	var alive_unit := _placed_minion(world, world.RED, QUERIER + Vector2(40.0, 0.0))
	check.call(blue_minion != null and alive_unit != null, "guard world minions spawn")
	if red_minion == null or blue_minion == null or alive_unit == null:
		return
	boss.alive = false
	boss.position = QUERIER + Vector2(5.0, 0.0)
	check.call(
		world._find_target(blue_minion) == alive_unit,
		"dead boss is skipped while the living unit is still picked"
	)
	boss.alive = true
	boss.position = QUERIER + Vector2(56.0, 0.0)
	check.call(
		world._find_target(blue_minion) == alive_unit,
		"boss beyond the source grid radius stays invisible to minions"
	)
	# Source ai_level 2 returns the first in-range Minion on the querier's lane;
	# the boss shares the lane but is not a Minion, so it must not short-circuit
	# the group even though it is the nearest candidate.
	boss.position = QUERIER + Vector2(10.0, 0.0)
	boss.lane = blue_minion.lane
	alive_unit.lane = 1 - blue_minion.lane
	alive_unit.position = QUERIER + Vector2(20.0, 0.0)
	blue_minion.ai_level = 2
	check.call(
		world._find_target(blue_minion) == alive_unit,
		"lane AI keeps the boss out of the source Minion group"
	)
