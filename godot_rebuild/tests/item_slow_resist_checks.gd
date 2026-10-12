# gdlint:disable=max-file-lines
extends RefCounted
## Layer 9ae native suite: item slow resist and the source store rule on the bus.

const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const FIXTURE := "res://tests/fixtures/item_slow_resist_source.json"

const RESIST_CAP := 0.6
const ABYSS_RESIST := 0.3
const HERO_SPOT := Vector2(700, 380)


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("rows"), "item slow fixture parses")
	if not fixture is Dictionary:
		return
	var world := Prototype.new()
	world.setup_arena()
	_shape_check(check, fixture)
	_live_catalog_check(check, world, fixture)
	for row in fixture.rows:
		_replay_row(check, world, row)
	_controls(check, world, fixture)


func _shape_check(check: Callable, fixture: Dictionary) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	check.call(
		(
			bool(shape.get("alive_guard", false))
			and bool(shape.get("reads_items", false))
			and bool(shape.get("scales_by_resist", false))
			and bool(shape.get("resist_guarded", false))
			and bool(shape.get("refresh_rule", false))
			and bool(shape.get("catalog_resist_cap", false))
		),
		"source slow shape is the pinned mixin method"
	)


func _live_catalog_check(check: Callable, world: Prototype, fixture: Dictionary) -> void:
	var stats: Dictionary = fixture.live_stats
	var hero = world.spawn_hero(Prototype.KAIZEN, world.BLUE, HERO_SPOT)
	if hero == null:
		check.call(false, "catalog probe hero spawns")
		return
	check.call(hero.items.add("abyss_breaker"), "catalog probe equips Abyss Breaker")
	check.call(
		is_equal_approx(hero.slow_resist(), float(stats.abyss_breaker_slow_resist)),
		"live Abyss Breaker slow resist matches the fixture"
	)
	check.call(
		is_equal_approx(hero.slow_resist(), ABYSS_RESIST) and hero.slow_resist() <= RESIST_CAP,
		"live resist sits under the 0.60 source cap"
	)
	var minion = world.spawn_unit(GOBLIN, world.RED, 0)
	check.call(
		minion != null and is_equal_approx(minion.slow_resist(), 0.0), "a minion resists nothing"
	)


func _replay_row(check: Callable, world: Prototype, row: Dictionary) -> void:
	var label := String(row.get("name", "unknown"))
	var payload: Dictionary = row.get("input", {})
	var expected: Dictionary = row.get("expected", {})
	var target = null
	if label.begins_with("minion"):
		target = world.spawn_unit(GOBLIN, world.RED, 0)
	else:
		target = world.spawn_hero(Prototype.KAIZEN, world.BLUE, HERO_SPOT)
	if target == null:
		check.call(false, "slow probe spawns: %s" % label)
		return
	var resist = payload.get("resist")
	if resist != null and float(resist) > 0.0:
		check.call(target.items.add("abyss_breaker"), "probe equips the resist item: %s" % label)
	target.slow_amount = float(payload.get("pre_amount", 0.0))
	target.slow_timer = int(payload.get("pre_timer", 0))
	target.alive = bool(payload.get("alive", true))
	var bus: BattleItemEffects = world._aura_item_effects()
	bus.apply_slow(target.id, float(payload.get("amount", 0.0)), int(payload.get("duration", 0)))
	check.call(
		(
			is_equal_approx(
				snappedf(target.slow_amount, 0.0001), float(expected.get("amount", -1.0))
			)
			and target.slow_timer == int(expected.get("timer", -1))
		),
		"bus slow column matches the source mixin method: %s" % label
	)


func _controls(check: Callable, world: Prototype, fixture: Dictionary) -> void:
	var stats: Dictionary = fixture.live_stats
	var frost: Dictionary = stats.frostbound
	var hero = world.spawn_hero(Prototype.KAIZEN, world.BLUE, HERO_SPOT)
	if hero == null:
		check.call(false, "control probe hero spawns")
		return
	check.call(hero.items.add("abyss_breaker"), "control probe equips Abyss Breaker")
	hero.slow_amount = 0.0
	hero.slow_timer = 0
	check.call(
		world.apply_slow(hero.id, float(frost.slow), int(frost.duration)),
		"the world slow path still accepts a hero victim"
	)
	check.call(
		is_equal_approx(snappedf(hero.slow_amount, 0.0001), 0.196) and hero.slow_timer == 180,
		"world path keeps its own resist pass (0.28 -> 0.196, no double cut)"
	)
	world.active_boss = null
	var boss: BossState = world._spawn_boss("gornak")
	check.call(boss != null, "boss control probe spawns")
	if boss == null:
		return
	boss.entrance_timer = 0
	var bus: BattleItemEffects = world._aura_item_effects()
	bus.apply_slow(boss.id, float(frost.slow), int(frost.duration))
	check.call(
		is_equal_approx(snappedf(boss.slow_amount, 0.0001), 0.14) and boss.slow_timer == 90,
		"boss victims keep the 9ad tenacity cut through the same bus arm"
	)
	check.call(
		is_equal_approx(hero.slow_resist(), ABYSS_RESIST) and boss.slow_resist() == 0.0,
		"only the hero victim carries the item resist"
	)
