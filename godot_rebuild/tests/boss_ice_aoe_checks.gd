# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8p native suite: the ice level-6 freeze AOE reaches the active boss,
## exactly like the source. `Bullet._on_hit` runs its `'slow_aoe' in
## self.special_data and all_units` arm over the `all_units` list that
## `Tower.update` passes down from `Game.update`, and that list ends with the
## live boss (`all_units = all_units + [self.active_boss]`). Every enemy inside
## `d <= aoe` of the impact point - inclusive - is slowed polymorphically, so a
## boss runs `Boss.apply_slow` / `Boss.apply_debuff('atk_slow')`: tenacity (0.50)
## halves magnitude and duration and the magnitude is capped at 0.35.
##
## Every fixture row also replays the same world with `active_boss` cleared, the
## native base behaviour before this layer: the recorded
## `expected_without_boss` column proves the boss arm is what changes the
## outcome instead of an accidental candidate.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Projectile = preload("res://scripts/combat/projectile_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const ICE_SIX = preload("res://data/structures/ice_level_6.tres")
const ICE_FIVE = preload("res://data/structures/ice_level_5.tres")
const FIXTURE := "res://tests/fixtures/boss_ice_aoe_source.json"

# Source `Bullet` impact point: the fixture measures the boss from the primary
# target, so both stay at the source offsets.
const MAIN := Vector2(560.0, 340.0)
const TOWER := Vector2(400.0, 340.0)
const SOURCE_FLAGS := [
	"tower_passes_all_units",
	"castle_omits_all_units",
	"all_units_includes_boss",
	"ice_aoe_gated",
	"ice_aoe_radius_inclusive",
	"ice_aoe_skips_main_allies_dead",
	"ice_aoe_slow_is_polymorphic",
	"ice_aoe_atk_slow_is_polymorphic",
	"shoot_ice_gates_aoe",
	"boss_slow_uses_tenacity"
]


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var parsed: bool = fixture is Dictionary and fixture.has("source") and fixture.has("cases")
	if parsed:
		for flag in SOURCE_FLAGS:
			parsed = parsed and bool(fixture.source.get(flag, false))
	check.call(parsed, "boss ice AOE fixture parses with every source flag")
	if not fixture is Dictionary:
		return
	_check_native_definitions(check, fixture)
	_replay_cases(check, fixture)
	_live_freeze(check)
	_guard_cases(check)


func _check_native_definitions(check: Callable, fixture: Dictionary) -> void:
	var six: Dictionary = fixture.source.get("levels", {}).get("6", {})
	var five: Dictionary = fixture.source.get("levels", {}).get("5", {})
	check.call(
		(
			is_equal_approx(ICE_SIX.slow_amount, float(six.get("slow", -1.0)))
			and ICE_SIX.slow_duration_ticks == int(six.get("slow_duration", -1))
			and is_equal_approx(ICE_SIX.atk_slow_amount, float(six.get("atk_slow", -1.0)))
			and is_equal_approx(ICE_SIX.slow_aoe_px, float(six.get("slow_aoe", -1.0)))
		),
		"native ice level-6 tower matches the source slow/atk-slow/AOE values"
	)
	check.call(
		(
			is_equal_approx(ICE_FIVE.slow_amount, float(five.get("slow", -1.0)))
			and ICE_FIVE.slow_duration_ticks == int(five.get("slow_duration", -1))
			and is_equal_approx(ICE_FIVE.slow_aoe_px, float(five.get("slow_aoe", -1.0)))
		),
		"native ice level-5 tower has the source slows and no AOE"
	)


func _shot(level: Dictionary, main: UnitState) -> Projectile:
	var shot := Projectile.new()
	shot.id = 0
	shot.source_id = -1
	shot.target_id = main.id
	shot.team = world.BLUE
	shot.damage = int(level.get("damage", 0))
	shot.kind = "ice"
	shot.slow_amount = float(level.get("slow", 0.0))
	shot.slow_duration = int(level.get("slow_duration", 0))
	shot.atk_slow_amount = float(level.get("atk_slow", 0.0))
	shot.slow_aoe = float(level.get("slow_aoe", 0.0))
	return shot


func _matches(boss: BossState, expected: Dictionary) -> bool:
	return (
		is_equal_approx(boss.slow_amount, float(expected.get("slow_amount", -1.0)))
		and boss.slow_timer == int(expected.get("slow_timer", -1))
		and is_equal_approx(boss.atk_slow_amount, float(expected.get("atk_slow_amount", -1.0)))
		and boss.atk_slow_timer == int(expected.get("atk_slow_timer", -1))
	)


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == 864, "boss ice AOE has four source cases for all 216 boss types")
	var world := Prototype.new()
	world.setup_arena()
	var levels: Dictionary = fixture.source.get("levels", {})
	var counts := {}
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		var label := String(entry.get("label", "unknown"))
		counts[boss_type] = int(counts.get(boss_type, 0)) + 1
		var level: Dictionary = levels.get(str(int(entry.get("level", 6))), {})
		world.units.clear()
		world.active_boss = null
		var boss: BossState = world._spawn_boss(boss_type)
		check.call(boss != null, "boss ice AOE boss loads: %s" % boss_type)
		if boss == null:
			continue
		boss.position = MAIN + Vector2(float(entry.get("distance", 0.0)), 0.0)
		boss.previous_position = boss.position
		var main: UnitState = world.spawn_unit(GOBLIN, world.RED, 0)
		check.call(main != null, "boss ice AOE primary target spawns: %s" % boss_type)
		if main == null:
			continue
		main.position = MAIN
		world._ice_impact(_shot(level, main), main)
		check.call(
			_matches(boss, entry.get("expected", {})),
			"boss ice AOE matches the source stores: %s (%s)" % [label, boss_type]
		)
		check.call(
			main.slow_timer > 0,
			"primary target keeps the source main-target slow: %s (%s)" % [label, boss_type]
		)
		# Same world with the boss out of the candidate list: the native base.
		boss.clear_tower_debuffs()
		world.active_boss = null
		world._ice_impact(_shot(level, main), main)
		check.call(
			_matches(boss, entry.get("expected_without_boss", {})),
			"boss omission leaves the boss unslowed: %s (%s)" % [label, boss_type]
		)
	for boss_type in counts:
		check.call(
			int(counts[boss_type]) == 4, "boss ice AOE has exactly four cases for %s" % boss_type
		)


func _live_freeze(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var tower: StructureState = world.spawn_structure(ICE_SIX, world.BLUE, TOWER, 1)
	check.call(tower != null, "live ice tower spawns")
	if tower == null:
		return
	check.call(
		is_equal_approx(tower.definition.slow_aoe_px, 80.0),
		"live ice tower carries the source level-6 AOE radius"
	)
	world.units.clear()
	var boss: BossState = world._spawn_boss("gornak")
	check.call(boss != null, "live ice AOE boss spawns")
	if boss == null:
		return
	# The goblin is the nearer enemy, so it stays the primary target while the
	# boss stands 40 px away - inside the 80 px AOE, outside the main-target arm.
	var main: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
	if main == null:
		return
	main.position = MAIN
	boss.position = MAIN + Vector2(40.0, 0.0)
	boss.previous_position = boss.position
	check.call(boss.slow_timer == 0, "boss starts unslowed before the first impact")
	var ticks := 0
	while boss.slow_timer <= 0 and ticks < 240:
		world.step_tick()
		ticks += 1
	check.call(
		(
			boss.slow_timer > 0
			and is_equal_approx(boss.slow_amount, 0.325)
			and is_equal_approx(boss.atk_slow_amount, 0.2)
		),
		"live level-6 ice AOE slows the boss through the source tenacity rule"
	)


func _guard_cases(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	world.units.clear()
	var boss: BossState = world._spawn_boss("gornak")
	check.call(boss != null, "ice AOE guard boss spawns")
	if boss == null:
		return
	var main: UnitState = world.spawn_unit(GOBLIN, world.RED, 0)
	if main == null:
		return
	main.position = MAIN
	boss.position = MAIN + Vector2(10.0, 0.0)
	boss.previous_position = boss.position
	var levels: Dictionary = {
		"slow": 0.65, "slow_duration": 150, "atk_slow": 0.4, "slow_aoe": 80.0, "damage": 78
	}
	var five: Dictionary = {
		"slow": 0.55, "slow_duration": 120, "atk_slow": 0.3, "slow_aoe": 0.0, "damage": 60
	}
	# Control: a living enemy boss 10 px from the impact point is slowed, so each
	# guard below fails for the right reason instead of an already clean boss.
	world._ice_impact(_shot(levels, main), main)
	check.call(boss.slow_timer == 75, "control boss is slowed by the level-6 AOE")
	# Same team as the shooter: the source loop drops allies.
	boss.clear_tower_debuffs()
	boss.team = world.BLUE
	world._ice_impact(_shot(levels, main), main)
	check.call(boss.slow_timer == 0, "same-team boss is never slowed by the AOE")
	# Dead boss: the source loop requires `u.alive`.
	boss.team = world.RED
	boss.alive = false
	world._ice_impact(_shot(levels, main), main)
	check.call(boss.slow_timer == 0, "dead boss is never slowed by the AOE")
	# Living boss, level-5 ice: `'slow_aoe' in special_data` is false, so an
	# adjacent boss stays untouched even at 10 px.
	boss.alive = true
	boss.clear_tower_debuffs()
	world._ice_impact(_shot(five, main), main)
	check.call(boss.slow_timer == 0, "level-5 ice has no AOE arm to reach the boss")
