extends RefCounted
## 9e: the hero item cleave splash must reach the active boss with the source
## call shape `u.take_damage(splash, h.team)` (`hero_items.py:2516`) - two
## positional arguments, so `Boss.take_damage` (`bosses/base_boss.py:5978`) runs
## with `source=None` and `school=None`. Layer 8z made the boss a candidate but
## delivered the hit as `_deliver_hit(dealer_id, ..., "physical", ...)`, which
## armed the Solar Brand blind gate against the cleaving hero, cut the splash by
## boss armor, and credited that hero with the boss kill on a lethal splash.
## The replay drives the real inventory arm through the production bus into
## `_deliver_hit` -> `BossState.take_damage` -> `_process_boss_result`, and a
## legacy bus reproduces the pre-9e arguments for the counterfactual column.

const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Prior = preload("res://tests/boss_item_cleave_chain_checks.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const FIXTURE := "res://tests/fixtures/boss_item_cleave_damage_source.json"

const BASIC_DAMAGE := 50
const CLEAVE_ITEM := "cleave_axe"
const NEAR_MINION_X := 30.0
const CONTROL_SCENARIO := "cleave_outside_radius_control"
const BLIND_SCENARIO := "cleave_blind_owner_still_lands"
const ARMOR_SCENARIO := "cleave_school_vs_boss_armor"
const LETHAL_SCENARIO := "cleave_lethal_without_kill_credit"
const RESULT_FIELDS := [
	"boss_hp_loss",
	"boss_alive",
	"owner_kills",
	"miniboss_kill_count",
	"trueboss_kill_count",
]
const SOURCE_FLAGS := [
	"boss_blind_block_requires_source",
	"boss_school_comes_from_resolver",
	"resolver_returns_none_without_school_or_source",
	"boss_lethal_branch_stores_source",
]


class CleaveDamageBus:
	extends BattleItemEffects
	var legacy := false

	func cleave_splash(
		target_id: int, src_team: int, src_pos: Vector2, splash: int, radius: float
	) -> void:
		if not legacy:
			super.cleave_splash(target_id, src_team, src_pos, splash, radius)
			return
		_legacy_cleave(target_id, src_team, src_pos, splash, radius)

	func _legacy_cleave(
		target_id: int, src_team: int, src_pos: Vector2, splash: int, radius: float
	) -> void:
		# Pre-9e body: regular units and the boss both took a physical hit that
		# carried the dealing hero as `source`.
		var center: Object = world.get_unit(target_id)
		if center == null:
			return
		var center_pos: Vector2 = center.position
		for u in world.units:
			if u == null or not u.alive or u.team == src_team or u.id == target_id:
				continue
			if center_pos.distance_to(u.position) <= radius:
				world._deliver_hit(dealer_id, src_team, u, splash, "physical", src_pos)
		var boss: Object = _onhit_boss(src_team, target_id)
		if boss != null and center_pos.distance_to(boss.position) <= radius:
			world._deliver_hit(dealer_id, src_team, boss, splash, "physical", src_pos)


class CleaveDamageWorld:
	extends Prototype
	var legacy_cleave := false

	func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
		var bus := CleaveDamageBus.new()
		bus.world = self
		bus.legacy = legacy_cleave
		bus.dealer_id = source_hero.id
		bus.dealer_team = source_hero.team
		bus.dealer_pos = source_hero.position
		return bus


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "9e cleave damage fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == 864, "9e has four cleave damage cases for all 216 boss types")
	if cases.size() != 864:
		return
	_check_source_shape(check, fixture)
	var helper := Prior.new()
	var world := CleaveDamageWorld.new()
	world.setup_arena()
	for row: Dictionary in cases:
		_check_row(check, helper, world, fixture, row)
	helper._reset_world(world, false)


func _check_row(
	check: Callable, helper: Prior, world: CleaveDamageWorld, fixture: Dictionary, row: Dictionary
) -> void:
	var scenario: String = String(row.get("scenario", ""))
	var expected: Dictionary = _replay(check, helper, world, fixture, row, false)
	var native_old: Dictionary = _replay(check, helper, world, fixture, row, true)
	if expected.is_empty() or native_old.is_empty():
		return
	check.call(
		_matches(expected, row.get("expected", {})),
		"9e source cleave outcome on the boss " + _label(row)
	)
	check.call(
		_matches(native_old, row.get("native_old", {})),
		"9e pre-slice native cleave counterfactual " + _label(row)
	)
	check.call(
		(not _same_result(expected, native_old)) == (scenario != CONTROL_SCENARIO),
		"9e divergence is limited to the boss arm scenarios " + _label(row)
	)
	check.call(
		_minion_arm_stable(expected, native_old, fixture),
		"9e the regular-unit cleave arm is untouched " + _label(row)
	)
	if scenario == BLIND_SCENARIO:
		check.call(
			(
				int(expected.get("boss_hp_loss", 0)) > 0
				and int(native_old.get("boss_hp_loss", -1)) == 0
			),
			"9e a blinded cleaver still splashes the boss " + _label(row)
		)
	elif scenario == ARMOR_SCENARIO:
		check.call(
			(
				int(expected.get("boss_hp_loss", 0)) > int(native_old.get("boss_hp_loss", 0))
				and String(expected.get("boss_school", "")) == "neutral"
				and String(native_old.get("boss_school", "")) == "physical"
			),
			"9e boss armor no longer cuts the school-less splash " + _label(row)
		)
	elif scenario == LETHAL_SCENARIO:
		check.call(
			(
				int(expected.get("owner_kills", -1)) == 0
				and int(native_old.get("owner_kills", -1)) == 1
				and int(expected.get("last_hit_source_id", 0)) == -1
				and (
					int(native_old.get("last_hit_source_id", -1))
					== int(native_old.get("owner_id", -2))
				)
			),
			"9e a lethal cleave splash credits nobody " + _label(row)
		)
	else:
		check.call(
			int(expected.get("boss_hp_loss", -1)) == 0 and expected.get("boss_alive", false),
			"9e a boss outside the cleave radius takes nothing " + _label(row)
		)


func _replay(
	check: Callable,
	helper: Prior,
	world: CleaveDamageWorld,
	fixture: Dictionary,
	row: Dictionary,
	legacy: bool
) -> Dictionary:
	helper._reset_world(world, false)
	world.legacy_cleave = legacy
	world.miniboss_kill_count = 0
	world.trueboss_kill_count = 0
	var layout := {
		"item": CLEAVE_ITEM,
		"boss_offset": float(row.get("boss_offset", 0.0)),
		"minion_offsets": [[11, NEAR_MINION_X]]
	}
	var spawned: Array = helper._spawn_case_units(world, String(row.get("boss_type", "")), layout)
	if spawned.is_empty():
		check.call(false, "9e case world spawns " + _label(row))
		return {}
	var boss: BossState = spawned[0]
	var hero: HeroState = spawned[1]
	var target: UnitState = spawned[2]
	var minions: Array = spawned[3]
	if minions.is_empty():
		check.call(false, "9e case needs a regular splash victim " + _label(row))
		return {}
	var near: UnitState = minions[0]
	boss.team = world.RED
	if not hero.items.add(CLEAVE_ITEM):
		check.call(false, "9e equip Cleave Axe " + _label(row))
		return {}
	if bool(row.get("owner_blind", false)):
		hero.blind_timer = int(fixture.get("source", {}).get("blind_ticks", 90))
		hero.blind_amount = 1.0
	boss.hp = float(row.get("boss_hp_before", boss.hp))
	world.deliveries = {}
	var hp_before := boss.hp
	var rng := RandomNumberGenerator.new()
	rng.seed = 0
	var bus: CleaveDamageBus = world._battle_item_effects(hero) as CleaveDamageBus
	hero.items.on_basic_attack_hit(int(target.id), BASIC_DAMAGE, [], rng, bus)
	var boss_hits: Array = world.deliveries.get(int(boss.id), [])
	if boss.defeated:
		world._process_boss_result()
	return {
		"boss_hp_loss": int(roundf(hp_before - boss.hp)),
		"boss_alive": boss.alive,
		"owner_kills": hero.kills,
		"miniboss_kill_count": world.miniboss_kill_count,
		"trueboss_kill_count": world.trueboss_kill_count,
		"boss_school": _school_of(boss_hits),
		"boss_hit_count": boss_hits.size(),
		"minion_hit_count": (world.deliveries.get(int(near.id), []) as Array).size(),
		"minion_damage": _damage_of(world.deliveries.get(int(near.id), [])),
		"target_hit_count": (world.deliveries.get(int(target.id), []) as Array).size(),
		"last_hit_source_id": boss.last_hit_source_id,
		"owner_id": hero.id,
	}


func _school_of(hits: Array) -> String:
	if hits.is_empty():
		return ""
	var entry: Array = hits[0]
	return String(entry[1]) if entry.size() > 1 else ""


func _damage_of(hits: Variant) -> int:
	var rows: Array = hits if hits is Array else []
	if rows.is_empty():
		return 0
	var entry: Array = rows[0]
	return int(entry[0])


func _minion_arm_stable(expected: Dictionary, native_old: Dictionary, fixture: Dictionary) -> bool:
	var splash := int(fixture.get("source", {}).get("splash_damage", 0))
	return (
		int(expected.get("minion_hit_count", -1)) == 1
		and int(native_old.get("minion_hit_count", -1)) == 1
		and int(expected.get("minion_damage", 0)) == splash
		and int(native_old.get("minion_damage", 0)) == splash
		and int(expected.get("target_hit_count", -1)) == 0
		and int(native_old.get("target_hit_count", -1)) == 0
	)


func _matches(actual: Dictionary, expected: Dictionary) -> bool:
	for field: String in RESULT_FIELDS:
		if not actual.has(field) or not expected.has(field):
			return false
		var value: Variant = expected[field]
		if value is bool:
			if bool(actual[field]) != bool(value):
				return false
		elif int(actual[field]) != int(value):
			return false
	return true


func _same_result(left: Dictionary, right: Dictionary) -> bool:
	for field: String in RESULT_FIELDS:
		if left.get(field) != right.get(field):
			return false
	return true


func _check_source_shape(check: Callable, fixture: Dictionary) -> void:
	var source: Dictionary = fixture.get("source", {})
	var shape: Dictionary = source.get("ast_shape", {})
	var valid := int(shape.get("cleave_take_damage_positional_args", 0)) == 2
	valid = valid and (shape.get("cleave_take_damage_keywords", [1]) as Array).is_empty()
	for flag: String in SOURCE_FLAGS:
		valid = valid and bool(shape.get(flag, false))
	check.call(
		(
			valid
			and int(source.get("basic_damage", 0)) == BASIC_DAMAGE
			and int(source.get("splash_damage", 0)) == 25
			and is_equal_approx(float(source.get("cleave_radius", 0.0)), 110.0)
		),
		"9e Python AST proves the cleave splash omits source and school"
	)
	check.call(
		int(fixture.get("boss_type_count", 0)) == 216 and int(fixture.get("case_count", 0)) == 864,
		"9e fixture carries four counterfactual cases for every boss type"
	)


func _label(row: Dictionary) -> String:
	return String(row.get("boss_type", "")) + "/" + String(row.get("scenario", ""))
