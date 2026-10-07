extends RefCounted
## 9f: the Abyss Breaker Bash bonus damage must reach the active boss with the
## source call shape `target.take_damage(bash["damage"], h.team)`
## (`hero_items.py:2542`) - two positional arguments, so `Boss.take_damage`
## (`bosses/base_boss.py:5978`) runs with `source=None` and `school=None`.
## Before this layer the arm went out as
## `effects.deal_damage(target_id, hero_team, damage, "physical")`, which armed
## the Solar Brand blind gate against the basher, let boss armor cut the bonus
## damage, and credited the basher with the boss kill on a lethal proc. The
## replay drives the real inventory arm through the production bus into
## `_deliver_hit` -> `BossState.take_damage` -> `_process_boss_result`; a legacy
## bus reproduces the pre-9f arguments for the counterfactual column.

const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Prior = preload("res://tests/boss_item_cleave_chain_checks.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const FIXTURE := "res://tests/fixtures/boss_item_bash_damage_source.json"

const BASIC_DAMAGE := 50
const BASH_ITEM := "abyss_breaker"
const BOSS_X := 40.0
const BYSTANDER_X := 500.0
const CONTROL_SCENARIO := "bash_internal_cooldown_control"
const BLIND_SCENARIO := "bash_blind_owner_still_lands"
const ARMOR_SCENARIO := "bash_school_vs_boss_armor"
const LETHAL_SCENARIO := "bash_lethal_without_kill_credit"
const RESULT_FIELDS := [
	"boss_hp_loss",
	"boss_alive",
	"bash_cd_after",
	"owner_kills",
	"miniboss_kill_count",
	"trueboss_kill_count",
]
const SOURCE_FLAGS := [
	"bash_requires_internal_cooldown",
	"bash_sets_internal_cooldown",
	"boss_blind_block_requires_source",
	"boss_school_comes_from_resolver",
	"boss_lethal_branch_stores_source",
]


class BashDamageBus:
	extends BattleItemEffects
	var legacy := false

	func deal_damage_sourceless(
		target_id: int, source_team: int, amount: int, school: String = "physical"
	) -> int:
		if legacy:
			# Pre-9f body: the bash arm called the plain bus entry, so the boss
			# took a physical hit that carried the dealing hero as source.
			return deal_damage(target_id, source_team, amount, school)
		return super.deal_damage_sourceless(target_id, source_team, amount, school)


class BashDamageWorld:
	extends Prototype
	var legacy_bash := false

	func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
		var bus := BashDamageBus.new()
		bus.world = self
		bus.legacy = legacy_bash
		bus.dealer_id = source_hero.id
		bus.dealer_team = source_hero.team
		bus.dealer_pos = source_hero.position
		return bus


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "9f bash damage fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == 864, "9f has four bash damage cases for all 216 boss types")
	if cases.size() != 864:
		return
	_check_source_shape(check, fixture)
	var helper := Prior.new()
	var world := BashDamageWorld.new()
	world.setup_arena()
	for row: Dictionary in cases:
		_check_row(check, helper, world, fixture, row)
	helper._reset_world(world, false)


func _check_row(
	check: Callable, helper: Prior, world: BashDamageWorld, fixture: Dictionary, row: Dictionary
) -> void:
	var scenario: String = String(row.get("scenario", ""))
	var expected: Dictionary = _replay(check, helper, world, fixture, row, false)
	var native_old: Dictionary = _replay(check, helper, world, fixture, row, true)
	if expected.is_empty() or native_old.is_empty():
		return
	check.call(
		_matches(expected, row.get("expected", {})),
		"9f source bash outcome on the boss " + _label(row)
	)
	check.call(
		_matches(native_old, row.get("native_old", {})),
		"9f pre-slice native bash counterfactual " + _label(row)
	)
	check.call(
		(not _same_result(expected, native_old)) == (scenario != CONTROL_SCENARIO),
		"9f divergence is limited to the proccing bash scenarios " + _label(row)
	)
	check.call(
		int(expected.get("bystander_hit_count", -1)) == 0,
		"9f the bash arm only touches the main target " + _label(row)
	)
	if scenario == BLIND_SCENARIO:
		check.call(
			(
				int(expected.get("boss_hp_loss", 0)) > 0
				and int(native_old.get("boss_hp_loss", -1)) == 0
			),
			"9f a blinded basher still damages the boss " + _label(row)
		)
	elif scenario == ARMOR_SCENARIO:
		check.call(
			(
				int(expected.get("boss_hp_loss", 0)) > int(native_old.get("boss_hp_loss", 0))
				and String(expected.get("boss_school", "")) == "neutral"
				and String(native_old.get("boss_school", "")) == "physical"
			),
			"9f boss armor no longer cuts the school-less bash " + _label(row)
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
			"9f a lethal bash credits nobody " + _label(row)
		)
	else:
		check.call(
			(
				int(expected.get("boss_hp_loss", -1)) == 0
				and int(expected.get("boss_hit_count", -1)) == 0
				and expected.get("boss_alive", false)
			),
			"9f the internal cooldown blocks the bash in both columns " + _label(row)
		)


func _replay(
	check: Callable,
	helper: Prior,
	world: BashDamageWorld,
	fixture: Dictionary,
	row: Dictionary,
	legacy: bool
) -> Dictionary:
	helper._reset_world(world, false)
	world.legacy_bash = legacy
	world.miniboss_kill_count = 0
	world.trueboss_kill_count = 0
	var layout := {"item": BASH_ITEM, "boss_offset": BOSS_X, "minion_offsets": [[11, BYSTANDER_X]]}
	var spawned: Array = helper._spawn_case_units(world, String(row.get("boss_type", "")), layout)
	if spawned.is_empty():
		check.call(false, "9f case world spawns " + _label(row))
		return {}
	var boss: BossState = spawned[0]
	var hero: HeroState = spawned[1]
	var minions: Array = spawned[3]
	if minions.is_empty():
		check.call(false, "9f case needs a bystander " + _label(row))
		return {}
	var bystander: UnitState = minions[0]
	boss.team = world.RED
	if not hero.items.add(BASH_ITEM):
		check.call(false, "9f equip Abyss Breaker " + _label(row))
		return {}
	hero.items.bash_cd = int(row.get("bash_cd_before", 0))
	if bool(row.get("owner_blind", false)):
		hero.blind_timer = int(fixture.get("source", {}).get("blind_ticks", 90))
		hero.blind_amount = 1.0
	boss.hp = float(row.get("boss_hp_before", boss.hp))
	world.deliveries = {}
	var hp_before := boss.hp
	var rng := RandomNumberGenerator.new()
	rng.seed = helper._seed_below(float(fixture.get("source", {}).get("bash_chance", 0.22)))
	var bus: BashDamageBus = world._battle_item_effects(hero) as BashDamageBus
	# The bash arm hits the hero's main target, so the boss is the victim here.
	hero.items.on_basic_attack_hit(int(boss.id), BASIC_DAMAGE, [], rng, bus)
	var boss_hits: Array = world.deliveries.get(int(boss.id), [])
	if boss.defeated:
		world._process_boss_result()
	return {
		"boss_hp_loss": int(roundf(hp_before - boss.hp)),
		"boss_alive": boss.alive,
		"bash_cd_after": hero.items.bash_cd,
		"owner_kills": hero.kills,
		"miniboss_kill_count": world.miniboss_kill_count,
		"trueboss_kill_count": world.trueboss_kill_count,
		"boss_school": _school_of(boss_hits),
		"boss_hit_count": boss_hits.size(),
		"bystander_hit_count": (world.deliveries.get(int(bystander.id), []) as Array).size(),
		"last_hit_source_id": boss.last_hit_source_id,
		"owner_id": hero.id,
	}


func _school_of(hits: Array) -> String:
	if hits.is_empty():
		return ""
	var entry: Array = hits[0]
	return String(entry[1]) if entry.size() > 1 else ""


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
	var valid := int(shape.get("bash_take_damage_positional_args", 0)) == 2
	valid = valid and (shape.get("bash_take_damage_keywords", [1]) as Array).is_empty()
	for flag: String in SOURCE_FLAGS:
		valid = valid and bool(shape.get(flag, false))
	check.call(
		(
			valid
			and int(source.get("bash_damage", 0)) == 55
			and int(source.get("bash_cooldown", 0)) == 140
			and is_equal_approx(float(source.get("bash_chance", 0.0)), 0.22)
		),
		"9f Python AST proves the bash bonus omits source and school"
	)
	check.call(
		int(fixture.get("boss_type_count", 0)) == 216 and int(fixture.get("case_count", 0)) == 864,
		"9f fixture carries four counterfactual cases for every boss type"
	)


func _label(row: Dictionary) -> String:
	return String(row.get("boss_type", "")) + "/" + String(row.get("scenario", ""))
