# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8r native suite: the cannon splash/burn arm reaches the active boss,
## exactly like the source. `Bullet._on_hit` runs its splash loop over the
## `all_units` list that `Tower.update` passes down from `Game.update`, and that
## list ends with the live boss (`all_units = all_units + [self.active_boss]`).
## Every enemy inside `d <= splash_radius` of the impact point - inclusive -
## takes `int(damage * 0.6)` with neither school nor source, and burns through
## `u.apply_debuff('burn', ..., source_team=self.team)`.
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
const CANNON = preload("res://data/structures/cannon_level_6.tres")
const FIXTURE := "res://tests/fixtures/boss_cannon_splash_source.json"

const MAIN := Vector2(560.0, 340.0)
# The live scenario stays far from the arena structures `setup_arena()` spawns,
# so only the cannon under test can put a shell on the boss.
const LIVE_MAIN := Vector2(2000.0, 1500.0)
const LIVE_TOWER := Vector2(1840.0, 1500.0)
const LIVE_BOSS := "gornak"
const SOURCE_FLAGS := [
	"tower_passes_all_units",
	"all_units_includes_boss",
	"splash_damage_scale",
	"splash_radius_inclusive",
	"splash_skips_main_allies_dead",
	"splash_hit_has_no_source",
	"splash_burn_uses_source_team",
	"burn_gated_by_dps",
	"kill_credit_written_on_lethal"
]


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var parsed: bool = fixture is Dictionary and fixture.has("source") and fixture.has("cases")
	if parsed:
		for flag in SOURCE_FLAGS:
			parsed = parsed and bool(fixture.source.get(flag, false))
	check.call(parsed, "boss cannon splash fixture parses with every source flag")
	if not fixture is Dictionary:
		return
	_check_cannon(check, fixture)
	_replay_cases(check, fixture)
	_live_splash(check)
	_guard_cases(check)


func _check_cannon(check: Callable, fixture: Dictionary) -> void:
	var cannon: Dictionary = fixture.source.get("cannon", {})
	check.call(
		(
			is_equal_approx(CANNON.damage, float(cannon.get("damage", -1)))
			and is_equal_approx(CANNON.splash_radius_px, float(cannon.get("splash", -1.0)))
			and is_equal_approx(CANNON.burn_dps, float(cannon.get("burn_dps", -1.0)))
			and CANNON.burn_duration_ticks == int(cannon.get("burn_duration", -1))
		),
		"native level-6 cannon matches the source damage/splash/burn values"
	)


func _shot(world: Prototype, main: UnitState, splash_radius: float) -> Projectile:
	var shot := Projectile.new()
	shot.id = 0
	shot.source_id = -1
	shot.target_id = main.id
	shot.team = world.BLUE
	shot.damage = int(CANNON.damage)
	shot.kind = "cannon"
	shot.splash_radius = splash_radius
	shot.burn_dps = CANNON.burn_dps
	shot.burn_duration = CANNON.burn_duration_ticks
	return shot


func _team_of(recorded: String) -> int:
	match recorded:
		"blue":
			return 0
		"red":
			return 1
	return -1


func _matches(boss: BossState, expected: Dictionary) -> bool:
	return (
		is_equal_approx(boss.hp, float(expected.get("hp", -1.0)))
		and boss.alive == bool(expected.get("alive", false))
		and is_equal_approx(boss.burn_dps, float(expected.get("burn_dps", -1.0)))
		and boss.burn_timer == int(expected.get("burn_timer", -1))
		and boss.burn_team == _team_of(String(expected.get("burn_team", "")))
	)


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(
		cases.size() == 864, "boss cannon splash has four source cases for all 216 boss types"
	)
	var world := Prototype.new()
	world.setup_arena()
	var counts := {}
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		var label := String(entry.get("label", "unknown"))
		counts[boss_type] = int(counts.get(boss_type, 0)) + 1
		world.units.clear()
		world.projectiles.clear()
		world.active_boss = null
		var boss: BossState = world._spawn_boss(boss_type)
		check.call(boss != null, "boss cannon splash boss loads: %s" % boss_type)
		if boss == null:
			continue
		boss.position = MAIN + Vector2(float(entry.get("distance", 0.0)), 0.0)
		boss.previous_position = boss.position
		if String(label) == "splash_lethal_no_source":
			boss.hp = float(entry.get("hp_before", 1.0))
		var main: UnitState = world.spawn_unit(GOBLIN, world.RED, 0)
		check.call(main != null, "boss cannon splash primary target spawns: %s" % boss_type)
		if main == null:
			continue
		main.position = MAIN
		world._cannon_impact(_shot(world, main, float(entry.get("splash_radius", 100.0))), main)
		check.call(
			_matches(boss, entry.get("expected", {})),
			"cannon splash matches the source result: %s (%s)" % [label, boss_type]
		)
		var expected: Dictionary = entry.get("expected", {})
		if float(expected.get("hp", 0.0)) < float(entry.get("hp_before", 0.0)):
			check.call(
				boss.last_hit_source_id == -1,
				"splash keeps the source-omitted attribution: %s (%s)" % [label, boss_type]
			)
		# Same world with the boss out of the candidate list: the native base.
		world.active_boss = null
		var fresh: BossState = world._spawn_boss(boss_type)
		world.active_boss = null
		if fresh == null:
			continue
		fresh.position = MAIN + Vector2(float(entry.get("distance", 0.0)), 0.0)
		if String(label) == "splash_lethal_no_source":
			fresh.hp = float(entry.get("hp_before", 1.0))
		world._cannon_impact(_shot(world, main, float(entry.get("splash_radius", 100.0))), main)
		check.call(
			_matches(fresh, entry.get("expected_without_boss", {})),
			"boss omission leaves the boss untouched: %s (%s)" % [label, boss_type]
		)
	for boss_type in counts:
		check.call(
			int(counts[boss_type]) == 4,
			"boss cannon splash has exactly four cases for %s" % boss_type
		)


func _live_splash(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var tower: StructureState = world.spawn_structure(CANNON, world.BLUE, LIVE_TOWER, 1)
	check.call(tower != null, "live cannon spawns")
	if tower == null:
		return
	check.call(
		is_equal_approx(tower.definition.splash_radius_px, 100.0),
		"live cannon carries the source level-6 splash radius"
	)
	world.units.clear()
	var boss: BossState = world._spawn_boss(LIVE_BOSS)
	check.call(boss != null, "live cannon splash boss spawns")
	if boss == null:
		return
	# The goblin is the nearer enemy, so it stays the primary target while the
	# boss stands 50 px away - inside the 100 px splash, outside the main hit.
	var main: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
	if main == null:
		return
	main.position = LIVE_MAIN
	boss.position = LIVE_MAIN + Vector2(50.0, 0.0)
	boss.previous_position = boss.position
	var hp_before := boss.hp
	check.call(boss.burn_timer == 0, "boss starts unburned before the first impact")
	var ticks := 0
	while boss.burn_timer <= 0 and ticks < 240:
		world.step_tick()
		ticks += 1
	check.call(
		boss.burn_timer > 0 and is_equal_approx(boss.burn_dps, 30.0) and boss.hp < hp_before,
		"live level-6 cannon splash damages and burns the boss"
	)


func _guard_cases(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	world.units.clear()
	var boss: BossState = world._spawn_boss(LIVE_BOSS)
	check.call(boss != null, "cannon splash guard boss spawns")
	if boss == null:
		return
	var main: UnitState = world.spawn_unit(GOBLIN, world.RED, 0)
	if main == null:
		return
	main.position = MAIN
	boss.position = MAIN + Vector2(10.0, 0.0)
	boss.previous_position = boss.position
	# Control: a living enemy boss 10 px from the impact point is splashed, so
	# each guard below fails for the right reason instead of an untouched boss.
	world._cannon_impact(_shot(world, main, 100.0), main)
	check.call(boss.hp < float(boss.max_hp) and boss.burn_timer == 180, "control boss is splashed")
	# Same team as the shooter: the source loop drops allies.
	world.active_boss = null
	var ally: BossState = world._spawn_boss(LIVE_BOSS)
	world.active_boss = ally
	if ally == null:
		return
	ally.position = MAIN + Vector2(10.0, 0.0)
	ally.team = world.BLUE
	world._cannon_impact(_shot(world, main, 100.0), main)
	check.call(
		is_equal_approx(ally.hp, float(ally.max_hp)) and ally.burn_timer == 0,
		"same-team boss is never splashed"
	)
	# Dead boss: the source loop requires `u.alive`.
	ally.team = world.RED
	ally.alive = false
	world._cannon_impact(_shot(world, main, 100.0), main)
	check.call(is_equal_approx(ally.hp, float(ally.max_hp)), "dead boss is never splashed")
	# No splash radius: the arm does not exist, so an adjacent boss stays clean.
	ally.alive = true
	world._cannon_impact(_shot(world, main, 0.0), main)
	check.call(
		is_equal_approx(ally.hp, float(ally.max_hp)) and ally.burn_timer == 0,
		"a shell without splash radius never reaches the boss"
	)
