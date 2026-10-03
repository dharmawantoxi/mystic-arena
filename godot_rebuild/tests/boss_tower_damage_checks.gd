# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8q native suite: a structure projectile that lands on the boss carries
## no damage school, exactly like the source. `Bullet._on_hit` damages its
## target with `take_damage(damage, team, damage_type='projectile')` - no
## `school=` and no `source=` - and `_entity.resolve_damage_school` returns None
## for that combination, so `Boss.take_damage` skips both the armor and the
## magic-resist branch: only resilience and the anti-burst cap apply.
##
## Every fixture row therefore records two source-executed columns: the
## school-free hit the source produces (`expected_hp_after`) and the same raw
## damage delivered under a declared physical school
## (`expected_physical_hp_after`), which is what the native structure path used
## to hand the boss. The replay asserts the first through the real
## `_update_projectiles` path and the second through a direct physical hit, so
## the recorded gap is what this layer changes.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Projectile = preload("res://scripts/combat/projectile_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const FIXTURE := "res://tests/fixtures/boss_tower_damage_source.json"

const BOSS_AT := Vector2(560.0, 340.0)
const TOWER_AT := Vector2(400.0, 340.0)
# The live scenario stays far from the arena structures `setup_arena()` spawns,
# so only the tower under test can put a bolt on the boss.
const LIVE_BOSS_AT := Vector2(2000.0, 1500.0)
const LIVE_TOWER_AT := Vector2(1840.0, 1500.0)
const LIVE_BOSS := "gornak"
const SOURCE_FLAGS := [
	"main_hit_is_projectile",
	"hit_passes_no_school",
	"resolver_none_for_projectile",
	"resolver_rejects_unknown_school",
	"resolver_reads_source_school",
	"boss_mitigation_gated_by_school",
	"resolver_documented_none"
]


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var parsed: bool = fixture is Dictionary and fixture.has("source") and fixture.has("cases")
	if parsed:
		for flag in SOURCE_FLAGS:
			parsed = parsed and bool(fixture.source.get(flag, false))
	check.call(parsed, "boss tower damage fixture parses with every source flag")
	if not fixture is Dictionary:
		return
	_replay_cases(check, fixture)
	_live_archer_hit(check, fixture)
	_school_guards(check)


func _tower_for(world: Prototype, at: Vector2) -> StructureState:
	return world.spawn_structure(ARCHER, world.BLUE, at, 1)


func _shot(tower: StructureState, boss: BossState, label: String, raw: int) -> Projectile:
	var shot := Projectile.new()
	shot.id = 1
	shot.source_id = tower.id
	shot.target_id = boss.id
	shot.team = tower.team
	shot.damage = raw
	shot.speed = 8.0
	shot.hit_radius = 4.0
	shot.ttl_ticks = 180
	# Impact this tick: the source delivers on `dist < speed + BULLET_RADIUS`.
	shot.position = boss.position - Vector2(1.0, 0.0)
	match label:
		"cannon_level_six":
			shot.kind = "cannon"
			shot.splash_radius = 100.0
			shot.burn_dps = 30.0
			shot.burn_duration = 180
		"ice_level_six":
			shot.kind = "ice"
			shot.slow_amount = 0.65
			shot.slow_duration = 150
			shot.atk_slow_amount = 0.4
			shot.slow_aoe = 80.0
		"mage_level_six":
			shot.kind = "mage"
			shot.skill_down_amount = 0.45
			shot.anti_heal_amount = 0.7
			shot.debuff_duration = 150
	return shot


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(
		cases.size() == 864, "boss tower damage has four source cases for all 216 boss types"
	)
	var world := Prototype.new()
	world.setup_arena()
	var tower := _tower_for(world, TOWER_AT)
	check.call(tower != null, "boss tower damage tower spawns")
	if tower == null:
		return
	var counts := {}
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		var label := String(entry.get("label", "unknown"))
		counts[boss_type] = int(counts.get(boss_type, 0)) + 1
		var raw := int(entry.get("raw_damage", 0))
		world.units.clear()
		world.projectiles.clear()
		world.active_boss = null
		var boss: BossState = world._spawn_boss(boss_type)
		check.call(boss != null, "boss tower damage boss loads: %s" % boss_type)
		if boss == null:
			continue
		boss.position = BOSS_AT
		boss.previous_position = BOSS_AT
		check.call(
			is_equal_approx(boss.hp, float(entry.get("hp_before", -1.0))),
			"boss tower damage starts from the source hp: %s (%s)" % [label, boss_type]
		)
		world.projectiles.append(_shot(tower, boss, label, raw))
		world._update_projectiles(tower)
		check.call(
			(
				is_equal_approx(boss.hp, float(entry.get("expected_hp_after", -1.0)))
				and boss.last_hit_source_id == tower.id
			),
			(
				"structure hit on the boss keeps the source school-free damage: %s (%s)"
				% [label, boss_type]
			)
		)
		# The pre-layer path: the same raw damage under a declared school.
		world.active_boss = null
		var contrast: BossState = world._spawn_boss(boss_type)
		if contrast == null:
			continue
		contrast.position = BOSS_AT
		world._deliver_hit(tower.id, tower.team, contrast, raw, "physical", BOSS_AT)
		check.call(
			is_equal_approx(contrast.hp, float(entry.get("expected_physical_hp_after", -1.0))),
			(
				"declared-school hit reproduces the recorded pre-layer damage: %s (%s)"
				% [label, boss_type]
			)
		)
	for boss_type in counts:
		check.call(
			int(counts[boss_type]) == 4,
			"boss tower damage has exactly four cases for %s" % boss_type
		)


func _live_archer_hit(check: Callable, fixture: Dictionary) -> void:
	var row: Dictionary = {}
	for entry in fixture.get("cases", []):
		if (
			String(entry.get("boss_type", "")) == LIVE_BOSS
			and String(entry.get("label", "")) == "archer_level_one"
		):
			row = entry
			break
	check.call(not row.is_empty(), "live archer case exists for %s" % LIVE_BOSS)
	if row.is_empty():
		return
	var world := Prototype.new()
	world.setup_arena()
	var tower := _tower_for(world, LIVE_TOWER_AT)
	if tower == null:
		return
	world.units.clear()
	var boss: BossState = world._spawn_boss(LIVE_BOSS)
	check.call(boss != null, "live tower damage boss spawns")
	if boss == null:
		return
	boss.position = LIVE_BOSS_AT
	boss.previous_position = LIVE_BOSS_AT
	check.call(
		is_equal_approx(boss.hp, float(row.get("hp_before", -1.0))),
		"live boss starts at the source hp"
	)
	var hp_before := boss.hp
	var ticks := 0
	while is_equal_approx(boss.hp, hp_before) and ticks < 240:
		world.step_tick()
		ticks += 1
	var expected_drop := hp_before - float(row.get("expected_hp_after", hp_before))
	check.call(
		(
			not is_equal_approx(boss.hp, hp_before)
			and is_equal_approx(hp_before - boss.hp, expected_drop)
			and boss.last_hit_source_id == tower.id
		),
		"live level-1 archer hit takes the source school-free amount off the boss"
	)


func _school_guards(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	world.units.clear()
	var boss: BossState = world._spawn_boss(LIVE_BOSS)
	var minion: UnitState = world.spawn_unit(GOBLIN, world.RED, 0)
	check.call(boss != null and minion != null, "school guard units spawn")
	if boss == null or minion == null:
		return
	check.call(
		world._projectile_school(boss, "physical") == "neutral",
		"boss target resolves a structure shot to no school"
	)
	check.call(
		world._projectile_school(boss, "magic") == "neutral",
		"mage bolt on the boss resolves to no school either"
	)
	check.call(
		world._projectile_school(minion, "physical") == "physical",
		"minion target keeps the declared school"
	)
	check.call(
		world._projectile_school(minion, "magic") == "magic",
		"non-boss targets keep the declared magic school"
	)
