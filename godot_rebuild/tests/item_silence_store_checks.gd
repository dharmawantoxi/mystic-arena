# gdlint:disable=max-file-lines
extends RefCounted
## Layer 9af native suite: the unit arm of item silence runs the source store.

const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const FIXTURE := "res://tests/fixtures/item_silence_store_source.json"

const HERO_SPOT := Vector2(700, 380)
const SILENCE := 1.0


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("rows"), "silence store fixture parses")
	if not fixture is Dictionary:
		return
	var world := Prototype.new()
	world.setup_arena()
	_shape_check(check, fixture)
	for row in fixture.rows:
		_hero_row(check, world, row)
	_minion_row(check, world, fixture)
	_dead_row(check, world, fixture)
	_structure_control(check, world)
	_boss_control(check, world)


func _shape_check(check: Callable, fixture: Dictionary) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	check.call(
		(
			bool(shape.get("silence_calls_atk_slow", false))
			and bool(shape.get("silence_calls_skill_down", false))
			and bool(shape.get("silence_swallows_lookup", false))
		),
		"source silence helper calls the two debuff stores behind a lookup guard"
	)
	check.call(
		(
			bool(shape.get("store_alive_guard", false))
			and bool(shape.get("store_atk_slow_merge", false))
			and bool(shape.get("store_skill_down_merge", false))
		),
		"source store is the pinned mixin body"
	)
	var owners: Array = shape.get("mixin_owners", [])
	check.call(
		owners == ["Hero", "Minion"],
		"only heroes and minions own the mixin in _entity.py (a tower does not)"
	)
	check.call(
		is_equal_approx(float(fixture.live_stats.get("silence_amount", 0.0)), SILENCE),
		"the silence payload is the pinned 1.0"
	)


func _apply_silence(world: Prototype, target_id: int, duration: int) -> void:
	var bus: BattleItemEffects = world._aura_item_effects()
	bus.apply_silence(target_id, duration)


func _hero_row(check: Callable, world: Prototype, row: Dictionary) -> void:
	var label := String(row.get("name", "unknown"))
	var payload: Dictionary = row.get("input", {})
	var expected: Dictionary = row.get("expected", {})
	var hero = world.spawn_hero(Prototype.KAIZEN, world.BLUE, HERO_SPOT)
	if hero == null:
		check.call(false, "silence hero probe spawns: %s" % label)
		return
	hero.alive = bool(payload.get("alive", true))
	hero.atk_slow_amount = float(payload.get("atk_amount", 0.0))
	hero.atk_slow_timer = int(payload.get("atk_timer", 0))
	hero.skill_down_amount = float(payload.get("skill_amount", 0.0))
	hero.skill_down_timer = int(payload.get("skill_timer", 0))
	_apply_silence(world, hero.id, int(payload.get("duration", 0)))
	check.call(
		(
			is_equal_approx(
				snappedf(hero.atk_slow_amount, 0.0001), float(expected.get("atk_amount", -1.0))
			)
			and hero.atk_slow_timer == int(expected.get("atk_timer", -1))
		),
		"silence attack clock matches the source store: %s" % label
	)
	check.call(
		(
			is_equal_approx(
				snappedf(hero.skill_down_amount, 0.0001), float(expected.get("skill_amount", -1.0))
			)
			and hero.skill_down_timer == int(expected.get("skill_timer", -1))
		),
		"silence skill clock matches the source store: %s" % label
	)


func _minion_row(check: Callable, world: Prototype, fixture: Dictionary) -> void:
	var row: Dictionary = {}
	for entry in fixture.rows:
		if String(entry.get("name", "")) == "weaker_longer_atk_clock":
			row = entry
	var payload: Dictionary = row.get("input", {})
	var expected: Dictionary = row.get("expected", {})
	var minion = world.spawn_unit(GOBLIN, world.RED, 0)
	if minion == null:
		check.call(false, "silence minion probe spawns")
		return
	minion.atk_slow_amount = float(payload.get("atk_amount", 0.0))
	minion.atk_slow_timer = int(payload.get("atk_timer", 0))
	_apply_silence(world, minion.id, int(payload.get("duration", 0)))
	check.call(
		(
			is_equal_approx(
				snappedf(minion.atk_slow_amount, 0.0001), float(expected.get("atk_amount", -1.0))
			)
			and minion.atk_slow_timer == int(expected.get("atk_timer", -1))
			and is_equal_approx(
				snappedf(minion.skill_down_amount, 0.0001),
				float(expected.get("skill_amount", -1.0))
			)
			and minion.skill_down_timer == int(expected.get("skill_timer", -1))
		),
		"a minion takes the same store: the weaker 0.9/200 clock becomes 1.0/60"
	)


func _dead_row(check: Callable, world: Prototype, fixture: Dictionary) -> void:
	var row: Dictionary = {}
	for entry in fixture.rows:
		if String(entry.get("name", "")) == "dead_victim_ignored":
			row = entry
	var payload: Dictionary = row.get("input", {})
	var minion = world.spawn_unit(GOBLIN, world.RED, 0)
	if minion == null:
		check.call(false, "silence dead probe spawns")
		return
	minion.alive = false
	minion.atk_slow_amount = float(payload.get("atk_amount", 0.0))
	minion.atk_slow_timer = int(payload.get("atk_timer", 0))
	_apply_silence(world, minion.id, int(payload.get("duration", 0)))
	check.call(
		(
			is_equal_approx(minion.atk_slow_amount, 0.5)
			and minion.atk_slow_timer == 5
			and is_equal_approx(minion.skill_down_amount, 0.5)
			and minion.skill_down_timer == 5
		),
		"a dead victim keeps its own store (pre-9af forced 1.0/60)"
	)


func _structure_control(check: Callable, world: Prototype) -> void:
	var tower: StructureState = world.structures[0] if not world.structures.is_empty() else null
	check.call(tower != null, "a tower exists for the silence control")
	if tower == null:
		return
	var before_atk := tower.atk_slow_timer
	var before_skill := tower.skill_down_timer
	_apply_silence(world, tower.id, 60)
	check.call(
		(
			tower.atk_slow_timer == before_atk
			and tower.skill_down_timer == before_skill
			and is_equal_approx(tower.atk_slow_amount, 0.0)
			and is_equal_approx(tower.skill_down_amount, 0.0)
		),
		"a tower has no mixin, so silence leaves it untouched"
	)
	check.call(not tower.has_method("apply_debuff"), "towers still carry no debuff store")


func _boss_control(check: Callable, world: Prototype) -> void:
	world.active_boss = null
	var boss: BossState = world._spawn_boss("gornak")
	check.call(boss != null, "boss silence control spawns")
	if boss == null:
		return
	boss.entrance_timer = 0
	_apply_silence(world, boss.id, 60)
	check.call(
		(
			is_equal_approx(snappedf(boss.atk_slow_amount, 0.0001), 0.35)
			and boss.atk_slow_timer == 30
			and is_equal_approx(snappedf(boss.skill_down_amount, 0.0001), 1.0)
			and boss.skill_down_timer == 60
		),
		"the boss arm keeps the 8w tenacity cut (0.35/30) and the raw skill-down (1.0/60)"
	)
