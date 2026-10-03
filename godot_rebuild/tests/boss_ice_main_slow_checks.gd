# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8s native suite: an ice tower that aims AT the boss slows it through
## the boss rule, exactly like the source. `Bullet._on_hit` calls
## `self.target.apply_slow(...)` and
## `self.target.apply_debuff('atk_slow', ...)` polymorphically, so a boss
## primary target runs `Boss.apply_slow` / `Boss.apply_debuff`: tenacity (0.50)
## cuts magnitude AND duration and the magnitude is capped at 0.35 - ice level 6
## (0.65/150, atk 0.40) becomes 0.325/75 and atk 0.20. A minion or hero runs the
## `TowerDebuffMixin` store instead and keeps the raw values.
##
## Every fixture row therefore carries both source-executed columns: `expected`
## (Boss rule) and `expected_mixin` (mixin rule on a real source victim, which
## is what the native world-level stores produced before this layer). The replay
## asserts the boss column on the boss and the mixin column on a goblin hit by
## the very same shots, so the unit path is pinned as unchanged.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Projectile = preload("res://scripts/combat/projectile_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const ICE_SIX = preload("res://data/structures/ice_level_6.tres")
const FIXTURE := "res://tests/fixtures/boss_ice_main_slow_source.json"

const MAIN := Vector2(560.0, 340.0)
# The live scenario stays far from the arena structures `setup_arena()` spawns,
# so only the ice tower under test can put a bolt on the boss.
const LIVE_MAIN := Vector2(2000.0, 1500.0)
const LIVE_TOWER := Vector2(1840.0, 1500.0)
const LIVE_BOSS := "gornak"
const SOURCE_FLAGS := [
	"main_slow_is_polymorphic",
	"main_atk_slow_is_polymorphic",
	"main_atk_slow_gated",
	"boss_slow_requires_alive",
	"boss_slow_uses_tenacity",
	"boss_slow_cuts_duration",
	"boss_atk_slow_uses_tenacity",
	"mixin_slow_has_no_tenacity"
]


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var parsed: bool = fixture is Dictionary and fixture.has("source") and fixture.has("cases")
	if parsed:
		for flag in SOURCE_FLAGS:
			parsed = parsed and bool(fixture.source.get(flag, false))
	check.call(parsed, "boss ice main slow fixture parses with every source flag")
	if not fixture is Dictionary:
		return
	_check_levels(check, fixture)
	_replay_cases(check, fixture)
	_live_freeze(check)
	_guard_cases(check)


func _check_levels(check: Callable, fixture: Dictionary) -> void:
	var six: Dictionary = fixture.source.get("levels", {}).get("6", {})
	check.call(
		(
			is_equal_approx(ICE_SIX.slow_amount, float(six.get("slow", -1.0)))
			and ICE_SIX.slow_duration_ticks == int(six.get("slow_duration", -1))
			and is_equal_approx(ICE_SIX.atk_slow_amount, float(six.get("atk_slow", -1.0)))
		),
		"native ice level-6 tower matches the source slow/atk-slow values"
	)


func _shot(input: Dictionary, main: UnitState) -> Projectile:
	var shot := Projectile.new()
	shot.id = 0
	shot.source_id = -1
	shot.target_id = main.id
	shot.team = 0
	shot.damage = 0
	shot.kind = "ice"
	shot.slow_amount = float(input.get("slow", 0.0))
	shot.slow_duration = int(input.get("slow_duration", 0))
	shot.atk_slow_amount = float(input.get("atk_slow", 0.0))
	return shot


func _matches(unit: UnitState, expected: Dictionary) -> bool:
	return (
		is_equal_approx(unit.slow_amount, float(expected.get("slow_amount", -1.0)))
		and unit.slow_timer == int(expected.get("slow_timer", -1))
		and is_equal_approx(unit.atk_slow_amount, float(expected.get("atk_slow_amount", -1.0)))
		and unit.atk_slow_timer == int(expected.get("atk_slow_timer", -1))
	)


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(
		cases.size() == 864, "boss ice main slow has four source cases for all 216 boss types"
	)
	var world := Prototype.new()
	world.setup_arena()
	var counts := {}
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		var label := String(entry.get("label", "unknown"))
		counts[boss_type] = int(counts.get(boss_type, 0)) + 1
		var inputs: Array = entry.get("inputs", [])
		world.units.clear()
		world.active_boss = null
		var boss: BossState = world._spawn_boss(boss_type)
		check.call(boss != null, "boss ice main slow boss loads: %s" % boss_type)
		if boss == null:
			continue
		boss.position = MAIN
		boss.previous_position = MAIN
		for input in inputs:
			world._ice_impact(_shot(input, boss), boss)
		check.call(
			_matches(boss, entry.get("expected", {})),
			"ice main target keeps the source boss tenacity rule: %s (%s)" % [label, boss_type]
		)
		# The very same shots on a minion: the unchanged mixin store.
		world.active_boss = null
		var minion: UnitState = world.spawn_unit(GOBLIN, world.RED, 0)
		if minion == null:
			continue
		minion.position = MAIN
		for input in inputs:
			world._ice_impact(_shot(input, minion), minion)
		check.call(
			_matches(minion, entry.get("expected_mixin", {})),
			"ice main target keeps the mixin store for minions: %s (%s)" % [label, boss_type]
		)
	for boss_type in counts:
		check.call(
			int(counts[boss_type]) == 4,
			"boss ice main slow has exactly four cases for %s" % boss_type
		)


func _live_freeze(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var tower: StructureState = world.spawn_structure(ICE_SIX, world.BLUE, LIVE_TOWER, 1)
	check.call(tower != null, "live ice tower spawns")
	if tower == null:
		return
	world.units.clear()
	var boss: BossState = world._spawn_boss(LIVE_BOSS)
	check.call(boss != null, "live ice main slow boss spawns")
	if boss == null:
		return
	# The boss is the only enemy, so it is the primary target of every bolt.
	boss.position = LIVE_MAIN
	boss.previous_position = LIVE_MAIN
	check.call(boss.slow_timer == 0, "boss starts unslowed before the first impact")
	var ticks := 0
	while boss.slow_timer <= 0 and ticks < 240:
		world.step_tick()
		ticks += 1
	check.call(
		(
			boss.slow_timer > 0
			and boss.slow_timer <= 75
			and is_equal_approx(boss.slow_amount, 0.325)
			and is_equal_approx(boss.atk_slow_amount, 0.2)
		),
		"live level-6 ice bolt slows the boss through the source tenacity rule"
	)


func _guard_cases(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	world.units.clear()
	var boss: BossState = world._spawn_boss(LIVE_BOSS)
	check.call(boss != null, "ice main slow guard boss spawns")
	if boss == null:
		return
	var level: Dictionary = {"slow": 0.65, "slow_duration": 150, "atk_slow": 0.4}
	var aoe_level: Dictionary = {
		"slow": 0.65, "slow_duration": 150, "atk_slow": 0.4, "slow_aoe": 80.0
	}
	# Control: a living boss as the primary target takes the tenacity slow.
	boss.position = MAIN
	boss.previous_position = MAIN
	world._ice_impact(_shot(level, boss), boss)
	check.call(
		(
			is_equal_approx(boss.slow_amount, 0.325)
			and boss.slow_timer == 75
			and is_equal_approx(boss.atk_slow_amount, 0.2)
		),
		"control boss takes the tenacity slow as the primary target"
	)
	# Dead boss: `Boss.apply_slow` returns on the source alive guard.
	boss.clear_tower_debuffs()
	boss.alive = false
	world._ice_impact(_shot(level, boss), boss)
	check.call(boss.slow_timer == 0 and boss.atk_slow_timer == 0, "dead boss is never slowed")
	# One level-6 impact with the boss as the primary target and a goblin inside
	# the 80 px AOE: the boss keeps the tenacity values while the goblin next to
	# it takes the raw mixin store from the AOE arm.
	boss.alive = true
	boss.clear_tower_debuffs()
	var minion: UnitState = world.spawn_unit(GOBLIN, world.RED, 0)
	if minion == null:
		return
	minion.position = MAIN + Vector2(40.0, 0.0)
	world._ice_impact(_shot(aoe_level, boss), boss)
	check.call(
		(
			is_equal_approx(boss.slow_amount, 0.325)
			and boss.slow_timer == 75
			and is_equal_approx(minion.slow_amount, 0.65)
			and minion.slow_timer == 150
		),
		"one impact gives the boss tenacity values and the minion the raw store"
	)
