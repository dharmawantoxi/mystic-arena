# gdlint:disable=max-file-lines
extends RefCounted
## Layer 9ad native suite: boss tenacity on tower item debuffs (slow/ice/mage/anti-heal).

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const Projectile = preload("res://scripts/combat/projectile_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const MAGE_TWO = preload("res://data/structures/mage_level_2.tres")
const MAGE_SIX = preload("res://data/structures/mage_level_6.tres")
const ICE_TWO = preload("res://data/structures/ice_level_2.tres")
const ICE_SIX = preload("res://data/structures/ice_level_6.tres")
const FIXTURE := "res://tests/fixtures/boss_debuff_tenacity_source.json"

const AURA_TICKS := 30


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("rows"), "boss debuff tenacity fixture parses")
	if not fixture is Dictionary:
		return
	_shape_check(check, fixture)
	var world := Prototype.new()
	world.setup_arena()
	_live_data_check(check, fixture)
	for row in fixture.rows:
		_replay_row(check, world, row)
	_aura_check(check, world, fixture)


func _shape_check(check: Callable, fixture: Dictionary) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	check.call(
		(
			bool(shape.get("has_apply_slow_override", false))
			and bool(shape.get("has_apply_debuff_override", false))
			and bool(shape.get("slow_tenacity_default", false))
			and bool(shape.get("slow_cap", false))
			and bool(shape.get("slow_duration_cut", false))
			and bool(shape.get("atk_slow_cut", false))
			and bool(shape.get("slow_kind_routes_to_apply_slow", false))
		),
		"source boss tenacity overrides are pinned"
	)
	check.call(
		(
			bool(shape.get("skill_down_not_cut", false))
			and bool(shape.get("anti_heal_not_cut", false))
			and bool(shape.get("unit_store_has_no_tenacity", false))
			and bool(shape.get("unit_store_skill_down", false))
			and bool(shape.get("unit_store_anti_heal", false))
		),
		"only slow/atk_slow are cut, the unit store stays raw"
	)


func _live_data_check(check: Callable, fixture: Dictionary) -> void:
	var stats: Dictionary = fixture.live_stats
	var mage: Dictionary = stats.get("mage_levels", {})
	var ice: Dictionary = stats.get("ice_levels", {})
	check.call(
		mage.size() == 5 and ice.size() == 5, "fixture carries all five mage and ice tower levels"
	)
	var level_two: Dictionary = mage.get("2", {})
	var level_six: Dictionary = mage.get("6", {})
	check.call(
		(
			is_equal_approx(MAGE_TWO.skill_down_amount, float(level_two.get("skill_down", -1.0)))
			and is_equal_approx(MAGE_TWO.anti_heal_amount, float(level_two.get("anti_heal", -1.0)))
			and MAGE_TWO.debuff_duration_ticks == int(level_two.get("debuff_duration", -1))
			and is_equal_approx(
				MAGE_SIX.skill_down_amount, float(level_six.get("skill_down", -1.0))
			)
			and is_equal_approx(MAGE_SIX.anti_heal_amount, float(level_six.get("anti_heal", -1.0)))
			and MAGE_SIX.debuff_duration_ticks == int(level_six.get("debuff_duration", -1))
		),
		"native mage towers carry the source skill-down/anti-heal payloads"
	)
	var ice_two: Dictionary = ice.get("2", {})
	var ice_six: Dictionary = ice.get("6", {})
	check.call(
		(
			is_equal_approx(ICE_TWO.slow_amount, float(ice_two.get("slow", -1.0)))
			and ICE_TWO.slow_duration_ticks == int(ice_two.get("slow_duration", -1))
			and is_equal_approx(ICE_SIX.slow_amount, float(ice_six.get("slow", -1.0)))
			and is_equal_approx(ICE_SIX.atk_slow_amount, float(ice_six.get("atk_slow", -1.0)))
		),
		"native ice towers carry the source slow/atk-slow payloads"
	)


func _replay_row(check: Callable, world: Prototype, row: Dictionary) -> void:
	var label := String(row.get("name", "unknown"))
	var payload: Dictionary = row.get("payload", {})
	var expected_boss: Dictionary = row.get("boss", {})
	var expected_unit: Dictionary = row.get("unit", {})
	var kind := String(payload.get("kind", ""))
	if label.begins_with("mage_level_"):
		_mage_row(check, world, row, kind, payload, expected_boss)
	elif label.begins_with("ice_level_"):
		_ice_row(check, world, row, kind, payload, expected_boss)
	else:
		_item_row(check, world, row, kind, payload, expected_boss)
	_unit_row(check, world, row, kind, payload, expected_unit)


func _mage_row(
	check: Callable,
	world: Prototype,
	row: Dictionary,
	kind: String,
	payload: Dictionary,
	expected: Dictionary
) -> void:
	var boss := _spawn(world, "gornak")
	if boss == null:
		check.call(false, "mage tenacity probe spawns")
		return
	var shot := Projectile.new()
	shot.id = 0
	shot.source_id = -1
	shot.target_id = boss.id
	shot.team = world.BLUE
	shot.kind = "mage"
	shot.damage = 0
	shot.skill_down_amount = float(payload.get("amount", 0.0)) if kind == "skill_down" else 0.0
	shot.anti_heal_amount = float(payload.get("amount", 0.0)) if kind == "anti_heal" else 0.0
	shot.debuff_duration = int(payload.get("duration", 0))
	world._mage_impact(shot, boss)
	var stored := boss.skill_down_amount if kind == "skill_down" else boss.anti_heal_amount
	var timer := boss.skill_down_timer if kind == "skill_down" else boss.anti_heal_timer
	check.call(
		(
			is_equal_approx(stored, float(expected.get("amount", -1.0)))
			and timer == int(expected.get("timer", -1))
		),
		"mage bolt boss column matches source: %s" % String(row.get("name", ""))
	)


func _ice_row(
	check: Callable,
	world: Prototype,
	row: Dictionary,
	kind: String,
	payload: Dictionary,
	expected: Dictionary
) -> void:
	var boss := _spawn(world, "gornak")
	if boss == null:
		check.call(false, "ice tenacity probe spawns")
		return
	var shot := Projectile.new()
	shot.id = 0
	shot.source_id = -1
	shot.target_id = boss.id
	shot.team = world.BLUE
	shot.kind = "ice"
	shot.damage = 0
	shot.slow_amount = float(payload.get("amount", 0.0)) if kind == "slow" else 0.0
	shot.slow_duration = int(payload.get("duration", 0))
	shot.atk_slow_amount = float(payload.get("amount", 0.0)) if kind == "atk_slow" else 0.0
	world._ice_main(shot, boss)
	var stored := boss.slow_amount if kind == "slow" else boss.atk_slow_amount
	var timer := boss.slow_timer if kind == "slow" else boss.atk_slow_timer
	check.call(
		(
			is_equal_approx(stored, float(expected.get("amount", -1.0)))
			and timer == int(expected.get("timer", -1))
		),
		"ice bolt boss column matches source: %s" % String(row.get("name", ""))
	)
	if kind == "slow":
		check.call(
			bool(expected.get("capped", false)) == false or is_equal_approx(stored, 0.35),
			"ice slow cap matches the source tenacity cap"
		)


func _item_row(
	check: Callable,
	world: Prototype,
	row: Dictionary,
	kind: String,
	payload: Dictionary,
	expected: Dictionary
) -> void:
	var boss := _spawn(world, "gornak")
	if boss == null:
		check.call(false, "item tenacity probe spawns")
		return
	var bus: BattleItemEffects = world._aura_item_effects()
	var amount := float(payload.get("amount", 0.0))
	var duration := int(payload.get("duration", 0))
	match kind:
		"slow":
			bus.apply_slow(boss.id, amount, duration)
		"atk_slow":
			bus.apply_atk_slow(boss.id, amount, duration)
		"anti_heal":
			bus.apply_anti_heal(boss.id, amount, duration)
		"burn":
			bus.apply_burn(boss.id, amount, duration, world.BLUE)
	var stored := 0.0
	var timer := 0
	match kind:
		"slow":
			stored = boss.slow_amount
			timer = boss.slow_timer
		"atk_slow":
			stored = boss.atk_slow_amount
			timer = boss.atk_slow_timer
		"anti_heal":
			stored = boss.anti_heal_amount
			timer = boss.anti_heal_timer
		"burn":
			stored = boss.burn_dps
			timer = boss.burn_timer
	check.call(
		(
			is_equal_approx(stored, float(expected.get("amount", -1.0)))
			and timer == int(expected.get("timer", -1))
		),
		"item bus boss column matches source: %s" % String(row.get("name", ""))
	)


func _unit_row(
	check: Callable,
	world: Prototype,
	row: Dictionary,
	kind: String,
	payload: Dictionary,
	expected: Dictionary
) -> void:
	var unit = world.spawn_unit(GOBLIN, world.RED, 0)
	if unit == null:
		check.call(false, "unit control probe spawns")
		return
	var amount := float(payload.get("amount", 0.0))
	var duration := int(payload.get("duration", 0))
	match kind:
		"slow":
			world.apply_slow(unit.id, amount, duration)
		"atk_slow":
			world.apply_atk_slow(unit.id, amount, duration)
		"skill_down":
			world.apply_skill_down(unit.id, amount, duration)
		"anti_heal":
			world.apply_anti_heal(unit.id, amount, duration)
	var stored := 0.0
	var timer := 0
	match kind:
		"slow":
			stored = unit.slow_amount
			timer = unit.slow_timer
		"atk_slow":
			stored = unit.atk_slow_amount
			timer = unit.atk_slow_timer
		"skill_down":
			stored = unit.skill_down_amount
			timer = unit.skill_down_timer
		"anti_heal":
			stored = unit.anti_heal_amount
			timer = unit.anti_heal_timer
	check.call(
		(
			is_equal_approx(stored, float(expected.get("amount", -1.0)))
			and timer == int(expected.get("timer", -1))
		),
		"unit column keeps the raw payload: %s" % String(row.get("name", ""))
	)


func _aura_check(check: Callable, world: Prototype, fixture: Dictionary) -> void:
	var row: Dictionary = {}
	for entry in fixture.rows:
		if String(entry.get("name", "")) == "everfrost_aura_atk_slow":
			row = entry
	var expected: Dictionary = row.get("boss", {})
	var boss := _spawn(world, "gornak")
	if boss == null:
		check.call(false, "aura tenacity probe spawns")
		return
	var hero = world.spawn_hero(Prototype.KAIZEN, world.BLUE, boss.position + Vector2(40, 0))
	check.call(hero != null, "aura probe hero spawns")
	if hero == null:
		return
	check.call(hero.items.add("everfrost_guard"), "probe hero equips the aura item")
	boss.atk_slow_amount = 0.0
	boss.atk_slow_timer = 0
	boss.anti_heal_amount = 0.0
	boss.anti_heal_timer = 0
	world._update_auras()
	check.call(
		(
			is_equal_approx(boss.atk_slow_amount, float(expected.get("amount", -1.0)))
			and boss.atk_slow_timer == int(expected.get("timer", -1))
		),
		"Freezing Aura attack slow runs the boss store (0.30/30 -> 0.15/15)"
	)
	var anti: Dictionary = {}
	for entry in fixture.rows:
		if String(entry.get("name", "")) == "everfrost_aura_anti_heal":
			anti = entry.get("boss", {})
	check.call(
		(
			is_equal_approx(boss.anti_heal_amount, float(anti.get("amount", -1.0)))
			and boss.anti_heal_timer == int(anti.get("timer", -1))
		),
		"Freezing Aura anti-heal stays raw on the boss, like the source store rules"
	)
	check.call(
		is_equal_approx(hero.atk_slow_amount, 0.0) and hero.anti_heal_timer == 0,
		"the aura owner is untouched by its own enemy aura"
	)


func _spawn(world: Prototype, kind: String) -> BossState:
	# Each probe needs its own live boss: `_spawn_boss` refuses to spawn while
	# one is active, so the registry slot is released first (the fixture rows
	# compare two or three bosses side by side).
	world.active_boss = null
	var boss: BossState = world._spawn_boss(kind)
	if boss == null:
		return null
	boss.entrance_timer = 0
	return boss
