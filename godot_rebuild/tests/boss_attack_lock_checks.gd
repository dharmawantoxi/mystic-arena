# gdlint:disable=max-file-lines
extends RefCounted
## Layer 9ah native suite: the boss attack lock is hero-only like the source gate.

const BossAI = preload("res://scripts/match/boss_ai.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const FIXTURE := "res://tests/fixtures/boss_attack_lock_source.json"

const HERO_SPOT := Vector2(700, 380)


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("rows"), "attack lock fixture parses")
	if not fixture is Dictionary:
		return
	var world := Prototype.new()
	world.setup_arena()
	_shape_check(check, fixture)
	for row in fixture.rows:
		_replay_row(check, world, row)
	_recipe_control(check, world)


func _shape_check(check: Callable, fixture: Dictionary) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	check.call(
		(
			int(shape.get("source_writes", 0)) == 46
			and int(shape.get("resolved_payloads", 0)) == 46
			and int(shape.get("hasattr_guarded", 0)) == 46
		),
		"all 46 source attack locks sit behind the hasattr gate"
	)
	var owners: Array = shape.get("owner_classes", [])
	check.call(owners == ["Hero"], "attack_timer is created by Hero alone")
	check.call(
		shape.get("payload_multiset", {}) == shape.get("native_payload_multiset", {}),
		"the native payload multiset equals the source"
	)
	check.call(
		(
			int(shape.get("native_writes", -1)) == 46
			and Array(shape.get("native_unparsed", [])).is_empty()
		),
		"every native lock parsed and the count matches"
	)


func _replay_row(check: Callable, world: Prototype, row: Dictionary) -> void:
	var label := String(row.get("name", "unknown"))
	var payload: Dictionary = row.get("input", {})
	var expected: Dictionary = row.get("expected", {})
	var kind := String(payload.get("kind", "hero"))
	var target: UnitState = null
	if kind == "hero":
		target = world.spawn_hero(Prototype.KAIZEN, world.BLUE, HERO_SPOT)
	elif kind == "minion":
		target = world.spawn_unit(GOBLIN, world.RED, 0)
	elif kind == "structure":
		target = world.structures[0] if not world.structures.is_empty() else null
	if target == null:
		check.call(false, "attack lock probe spawns: %s" % label)
		return
	target.alive = bool(payload.get("alive", true))
	var hero_clock_before := 0
	if target is HeroState:
		(target as HeroState).attack_timer = int(payload.get("pre_clock", 0))
		hero_clock_before = (target as HeroState).attack_timer
	else:
		target.cooldown_ticks = int(payload.get("pre_clock", 0))
	BossAI._attack_lock(target, int(payload.get("duration", 0)))
	if target is HeroState:
		check.call(
			(target as HeroState).attack_timer == int(expected.get("clock", -1)),
			"hero attack clock follows the source max rule: %s" % label
		)
		check.call(
			target.cooldown_ticks == 0 and hero_clock_before == int(payload.get("pre_clock", 0)),
			"the hero lock never touches the cooldown slot: %s" % label
		)
	else:
		check.call(
			target.cooldown_ticks == int(expected.get("clock", -1)),
			"a non-hero victim keeps its own clock untouched: %s" % label
		)


func _recipe_control(check: Callable, world: Prototype) -> void:
	# Ancient Apparition E (Cold Feet burst) is `_attack_lock(target, 90)` when the
	# target is farther than 250 px: drive the live recipe with a hero and with a
	# minion and pin both columns.
	for kind in ["hero", "minion"]:
		world.active_boss = null
		var boss: BossState = world._spawn_boss("ancient_apparition")
		if boss == null:
			check.call(false, "recipe probe spawns")
			return
		boss.entrance_timer = 0
		boss.hp = float(boss.max_hp)
		boss.q_timer = 1000
		boss.w_timer = 1000
		boss.r_timer = 1000
		boss.e_timer = 0
		var target: UnitState = null
		if kind == "hero":
			target = world.spawn_hero(Prototype.KAIZEN, world.BLUE, HERO_SPOT)
			(target as HeroState).max_hp = 100000
			(target as HeroState).hp = 100000.0
		else:
			target = world.spawn_unit(GOBLIN, world.RED, 0)
			target.hp = 100000.0
		if target == null:
			check.call(false, "recipe probe target spawns")
			return
		target.position = boss.position + Vector2(320, 0)
		var enemies: Array[UnitState] = [target]
		BossAI.tick(world, boss, enemies, target, 320.0)
		if kind == "hero":
			check.call(
				(target as HeroState).attack_timer == 90,
				"the live E recipe locks a hero for 90 ticks"
			)
		else:
			check.call(
				target.cooldown_ticks == 0,
				"the live E recipe leaves a minion alone (source hasattr fails)"
			)
			check.call(boss.e_timer > 0, "the E recipe still fired and armed its own cooldown")
