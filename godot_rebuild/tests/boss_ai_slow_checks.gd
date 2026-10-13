# gdlint:disable=max-file-lines
extends RefCounted
## Layer 9ag native suite: boss slow arms deliver through the victim method, and
## the Ice Vortex DOT damaged and slowed enemies every 20 ticks.

const BossAI = preload("res://scripts/match/boss_ai.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const FIXTURE := "res://tests/fixtures/boss_ai_slow_source.json"

const ABYSS_RESIST := 0.3
const HERO_SPOT := Vector2(700, 380)


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("rows"), "boss AI slow fixture parses")
	if not fixture is Dictionary:
		return
	var world := Prototype.new()
	world.setup_arena()
	_shape_check(check, fixture)
	_payload_rows(check, world, fixture)
	_merge_rows(check, world, fixture)
	_guards(check, world)
	_vortex_dot(check, world)


func _shape_check(check: Callable, fixture: Dictionary) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	check.call(
		(
			int(shape.get("source_calls", 0)) == 39
			and int(shape.get("hasattr_guarded", 0)) == 39
			and int(shape.get("native_slow_calls", -1)) == 39
		),
		"every source boss slow arm has a native twin behind the hasattr gate"
	)
	check.call(
		(
			bool(shape.get("vortex_block_found", false))
			and bool(shape.get("vortex_every_20", false))
			and bool(shape.get("vortex_radius", false))
			and bool(shape.get("vortex_damage_trisect", false))
			and bool(shape.get("vortex_slow_hasattr", false))
			and bool(shape.get("vortex_slow_payload", false))
		),
		"the source vortex DOT shape is pinned"
	)
	check.call(not bool(shape.get("tower_has_mixin", true)), "the source Tower carries no mixin")


func _spawn_hero_with_items(world: Prototype, items: Array) -> HeroState:
	var hero = world.spawn_hero(Prototype.KAIZEN, world.BLUE, HERO_SPOT)
	if hero == null:
		return null
	for item_id in items:
		hero.items.add(String(item_id))
	return hero


func _payload_rows(check: Callable, world: Prototype, fixture: Dictionary) -> void:
	for row in fixture.rows:
		var label := String(row.get("name", "unknown"))
		var amount := float(row.input.amount)
		var duration := int(row.input.duration)
		var plain := _spawn_hero_with_items(world, [])
		if plain == null:
			check.call(false, "boss slow probe spawns: %s" % label)
			return
		BossAI._slow(plain, amount, duration)
		check.call(
			(
				is_equal_approx(
					snappedf(plain.slow_amount, 0.0001), float(row.expected_plain.amount)
				)
				and plain.slow_timer == int(row.expected_plain.timer)
			),
			"a plain victim takes the boss slow raw: %s" % label
		)
		var resisted := _spawn_hero_with_items(world, ["abyss_breaker"])
		if resisted == null:
			check.call(false, "resisted probe spawns: %s" % label)
			return
		BossAI._slow(resisted, amount, duration)
		check.call(
			(
				is_equal_approx(
					snappedf(resisted.slow_amount, 0.0001), float(row.expected_resisted.amount)
				)
				and resisted.slow_timer == int(row.expected_resisted.timer)
			),
			"Abyss Breaker cuts the boss slow by 0.30: %s" % label
		)


func _merge_rows(check: Callable, world: Prototype, fixture: Dictionary) -> void:
	for row in fixture.merge_rows:
		var label := String(row.get("name", "unknown"))
		var payload: Dictionary = row.input
		var hero = _spawn_hero_with_items(world, ["abyss_breaker"])
		if hero == null:
			check.call(false, "merge probe spawns: %s" % label)
			return
		hero.slow_amount = float(payload.pre_amount)
		hero.slow_timer = int(payload.pre_timer)
		BossAI._slow(hero, float(payload.amount), int(payload.duration))
		var expected: Dictionary = row.expected_resisted
		check.call(
			(
				is_equal_approx(snappedf(hero.slow_amount, 0.0001), float(expected.amount))
				and hero.slow_timer == int(expected.timer)
			),
			"the resisted payload drives the source store rule: %s" % label
		)


func _guards(check: Callable, world: Prototype) -> void:
	var dead = _spawn_hero_with_items(world, [])
	dead.alive = false
	BossAI._slow(dead, 0.5, 180)
	check.call(
		dead.slow_amount == 0.0 and dead.slow_timer == 0,
		"a dead victim takes no boss slow (source alive guard)"
	)
	var tower = world.structures[0] if not world.structures.is_empty() else null
	check.call(tower != null, "a tower exists for the boss slow guard")
	if tower != null:
		BossAI._slow(tower, 0.5, 180)
		check.call(
			tower.slow_amount == 0.0 and tower.slow_timer == 0,
			"a tower has no mixin, so the boss slow skips it like the source hasattr"
		)
	var minion = world.spawn_unit(GOBLIN, world.RED, 0)
	BossAI._slow(minion, 0.5, 180)
	check.call(
		is_equal_approx(snappedf(minion.slow_amount, 0.0001), 0.5) and minion.slow_timer == 180,
		"a minion carries no inventory, so the boss slow lands raw"
	)


func _vortex_dot(check: Callable, world: Prototype) -> void:
	world.active_boss = null
	var boss: BossState = world._spawn_boss("ancient_apparition")
	check.call(boss != null, "the ancient apparition probe spawns")
	if boss == null:
		return
	boss.entrance_timer = 0
	boss.vortex_origin = boss.position + Vector2(300, 0)
	boss.vortex_active_timer = 20
	var inside = _spawn_hero_with_items(world, [])
	var inside_resisted = _spawn_hero_with_items(world, ["abyss_breaker"])
	var outside = _spawn_hero_with_items(world, [])
	if inside == null or inside_resisted == null or outside == null:
		check.call(false, "vortex probes spawn")
		return
	inside.position = boss.vortex_origin + Vector2(10, 0)
	inside_resisted.position = boss.vortex_origin + Vector2(0, 10)
	outside.position = boss.vortex_origin + Vector2(81, 0)
	for hero in [inside, inside_resisted, outside]:
		hero.max_hp = 100000.0
		hero.hp = 100000.0
	var enemies: Array[UnitState] = []
	for unit in world.units:
		if unit.alive and unit.team != boss.team:
			enemies.append(unit)
	var per_tick := int(BossAI._skill_damage(boss, boss.skill_q_damage) / 3.0)
	check.call(per_tick == 81, "the live skill_q_damage trisects to 81 like the source")
	var inside_before := inside.hp
	var resisted_before := inside_resisted.hp
	var outside_before := outside.hp
	BossAI.tick(world, boss, enemies, null, INF)
	check.call(
		(
			int(inside_before - inside.hp) == per_tick
			and int(resisted_before - inside_resisted.hp) == per_tick
		),
		"the vortex DOT damages every enemy inside the 80 px radius, target or not"
	)
	check.call(
		is_equal_approx(outside_before, outside.hp),
		"an enemy just outside the 80 px radius takes nothing"
	)
	check.call(
		is_equal_approx(snappedf(inside.slow_amount, 0.0001), 0.5) and inside.slow_timer == 60,
		"the vortex slows its victims 0.5/60"
	)
	check.call(
		(
			is_equal_approx(snappedf(inside_resisted.slow_amount, 0.0001), 0.35)
			and inside_resisted.slow_timer == 60
		),
		"the vortex slow respects the victim item resist (0.5 -> 0.35)"
	)
	check.call(boss.vortex_active_timer == 19, "the vortex clock advances once per tick")
	inside.hp = 100000.0
	inside_before = inside.hp
	BossAI.tick(world, boss, enemies, null, INF)
	check.call(
		is_equal_approx(inside_before, inside.hp) and boss.vortex_active_timer == 18,
		"off the 20 tick gate the vortex only counts down"
	)
	boss.vortex_active_timer = 1
	BossAI.tick(world, boss, enemies, null, INF)
	check.call(boss.vortex_active_timer == 0, "the vortex expires at zero")
