extends RefCounted
## 9c: replay Basilisk Breath Miasma ticks against every active boss while the
## poison owner is blinded (Solar Brand aura). The replay runs the real
## `hero_basic_attack` -> `_tick_auras_and_items` -> item bus -> `_deliver_hit`
## -> `BossState.take_damage` path, not a helper stub.
##
## `MiasmaBlindBus.legacy` restores the pre-9c `deal_damage_from` body, which
## forwarded the hit without a damage_type, so `_deliver_hit` kept its "normal"
## default and `BossState.blind_live` rolled the blinded owner before the
## poison could land.

const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const Prior = preload("res://tests/boss_item_cleave_chain_checks.gd")
const FIXTURE := "res://tests/fixtures/boss_miasma_blind_source.json"

const BLIND_TIMER := 90
const GAP_SCENARIOS := ["blind_owner_tick_blocked", "blind_owner_second_tick"]


class MiasmaBlindBus:
	extends BattleItemEffects
	# Records nothing: the world owns the delivery log, so no RefCounted cycle
	# can survive to engine exit.
	var legacy := false

	func deal_damage_from(
		source_id: int,
		source_team: int,
		source_pos: Vector2,
		target_id: int,
		amount: int,
		school: String = "magic",
		damage_type: String = "magic"
	) -> int:
		if legacy:
			return _legacy_deal_damage_from(
				source_id, source_team, source_pos, target_id, amount, school
			)
		return super.deal_damage_from(
			source_id, source_team, source_pos, target_id, amount, school, damage_type
		)

	func _legacy_deal_damage_from(
		source_id: int,
		source_team: int,
		source_pos: Vector2,
		target_id: int,
		amount: int,
		school: String
	) -> int:
		# Pre-9c body verbatim: no damage_type argument, so the "normal" default
		# of `_deliver_hit` armed the blind gate against the stored owner.
		var tgt: Object = world.get_unit(target_id)
		if tgt == null:
			return 0
		var origin := source_pos
		var source: Object = world.get_unit(source_id)
		if source != null:
			var current_pos: Variant = source.get("position")
			if current_pos is Vector2:
				origin = current_pos
		world._deliver_hit(source_id, source_team, tgt, amount, school, origin)
		return amount


class MiasmaBlindWorld:
	extends Prior.CleaveChainWorld
	var legacy := false

	func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
		_bind_miasma_registry(source_hero)
		var bus := MiasmaBlindBus.new()
		bus.world = self
		bus.legacy = legacy
		bus.dealer_id = source_hero.id
		bus.dealer_team = source_hero.team
		bus.dealer_pos = source_hero.position
		return bus


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var fixture: Dictionary = parsed if parsed is Dictionary else {}
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == 864, "9c four Miasma blind-gate cases for 216 bosses")
	if cases.size() != 864:
		return
	var shape: Dictionary = fixture.get("source", {}).get("ast_shape", {})
	check.call(
		shape.size() == 5 and _all_true(shape),
		"9c Python AST proves the Miasma tick is magic and carries no source"
	)
	var helper := Prior.new()
	var world := MiasmaBlindWorld.new()
	for row: Dictionary in cases:
		world.legacy = false
		var expected: Array = _replay(check, helper, world, row)
		var expected_fixture: Array = (row.get("expected", {}) as Dictionary).get("events", [])
		check.call(
			_events_match(expected, expected_fixture),
			"9c blinded owner still poisons the boss " + _label(row)
		)
		world.legacy = true
		var legacy: Array = _replay(check, helper, world, row)
		var legacy_fixture: Array = (row.get("native_old", {}) as Dictionary).get("events", [])
		check.call(
			_events_match(legacy, legacy_fixture),
			"9c pre-9c bus reproduces the recorded counterfactual " + _label(row)
		)
		var gap: bool = GAP_SCENARIOS.has(String(row.get("scenario", "")))
		check.call(
			(expected != legacy) == gap,
			"9c counterfactual divergence matches the scenario " + _label(row)
		)
	helper._reset_world(world, false)
	world._miasma_registry.clear()


func _replay(check: Callable, helper: Prior, world: MiasmaBlindWorld, row: Dictionary) -> Array:
	helper._reset_world(world, false)
	world._miasma_registry.clear()
	world.deliveries = {}
	world.hit_order = []
	world.recent_events.clear()
	var spawned: Array = helper._spawn_case_units(
		world, String(row.get("boss_type", "")), {"boss_offset": 0.0, "minion_offsets": []}
	)
	if spawned.size() != 4:
		return []
	var boss: BossState = spawned[0]
	var hero: HeroState = spawned[1]
	_prepare_attacker(hero, boss)
	# The oracle pins the blind roll to 0.0: a 100% blind always misses and a
	# 0% blind can never miss, so no RNG is left in the comparison.
	boss.blind_roll_override = func() -> float: return 0.0
	check.call(hero.items.add("basilisk_breath"), "9c equip Basilisk Breath")
	check.call(
		world.hero_basic_attack(hero.id, boss.id), "9c hero hit applies Miasma on the active boss"
	)
	if bool(row.get("true_strike", false)):
		# Equipped after the hit so the Cudgel bash arm cannot add damage.
		check.call(hero.items.add("sundering_cudgel"), "9c equip Sundering Cudgel")
	world.deliveries = {}
	world.hit_order = []
	var blind_frame: int = int(row.get("blind_frame", 0))
	var events: Array = []
	var schools: Array = []
	for frame in range(1, int(row.get("observe_frames", 0)) + 1):
		if frame > blind_frame:
			hero.blind_timer = BLIND_TIMER
			hero.blind_amount = float(row.get("blind_amount", 0.0))
		var before: int = _boss_deliveries(world, boss).size()
		world._tick_auras_and_items()
		var deliveries: Array = _boss_deliveries(world, boss)
		if deliveries.size() > before:
			var delivery: Array = deliveries[deliveries.size() - 1] as Array
			events.append([frame, int(delivery[0])])
			schools.append(String(delivery[1]))
	var magic_only: bool = true
	for school: String in schools:
		if school != "magic":
			magic_only = false
	check.call(
		schools.is_empty() or magic_only,
		"9c every poison tick reaches the boss as magic " + _label(row)
	)
	return events


func _prepare_attacker(hero: HeroState, boss: BossState) -> void:
	hero.position = boss.position + Vector2(-40.0, 0.0)
	hero.target_id = int(boss.id)
	hero.attack_timer = 0
	hero.items.hero_melee_flag = 1
	hero.items.hero_range = 70.0


func _boss_deliveries(world: MiasmaBlindWorld, boss: BossState) -> Array:
	return world.deliveries.get(int(boss.id), [])


func _label(row: Dictionary) -> String:
	return String(row.get("boss_type", "")) + "/" + String(row.get("scenario", ""))


func _all_true(values: Dictionary) -> bool:
	for value: Variant in values.values():
		if not bool(value):
			return false
	return true


func _events_match(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size():
		return false
	for index in range(actual.size()):
		var actual_row: Array = actual[index] as Array
		var expected_row: Array = expected[index] as Array
		if int(actual_row[0]) != int(expected_row[0]) or int(actual_row[1]) != int(expected_row[1]):
			return false
	return true
