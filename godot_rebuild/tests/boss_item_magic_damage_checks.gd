extends RefCounted
## 9g: the on-hit magic arms must reach the active boss with the source call
## shape `take_damage(damage, h.team, "magic")` - three positional arguments, so
## `Boss.take_damage` (`bosses/base_boss.py:5978`) runs with
## `damage_type="magic"`, `source=None`, `school=None`:
## arc chain (`hero_items.py:2568`), Sundering Cudgel Piercing Bash (`:2589`),
## Basilisk Breath Polycephaly multishot (`:2633`) and Runic Gavel Empower
## Strike (`:2648`). Before this layer all four went out as
## `effects.deal_damage(id, hero_team, amount, "magic")`, which armed the Solar
## Brand blind gate against the owner, cut the payload by boss magic resist while
## the source resolves no school at all, and credited the owner with the boss
## kill. The replay drives the real inventory arms through the production bus
## into `_deliver_hit` -> `BossState.take_damage` -> `_process_boss_result`; a
## legacy bus reproduces the pre-9g arguments for the counterfactual column.

const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Prior = preload("res://tests/boss_item_cleave_chain_checks.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const SYLARA = preload("res://data/heroes/sylara.tres")
const FIXTURE := "res://tests/fixtures/boss_item_magic_damage_source.json"

const BASIC_DAMAGE := 50
const BOSS_ID := 500
const CONTROL_ARM_FIELDS := {
	"chain": "chains_cd",
	"pierce_bash": "pierce_bash_cd",
	"polycephaly": "none",
	"empower": "empower_charge",
}
const RESULT_FIELDS := [
	"boss_hp_loss",
	"boss_alive",
	"owner_kills",
	"boss_counter",
	"regular_hits",
	"gate_after",
	"boss_schools",
	"boss_damage_types",
]
const NUMBER_FIELDS := ["boss_hp_loss", "owner_kills", "boss_counter", "gate_after"]
const NUMBER_LIST_FIELDS := ["regular_hits"]
const TEXT_LIST_FIELDS := ["boss_schools", "boss_damage_types"]
# Source AST/behaviour flags the Python oracle executes.
const SOURCE_FLAGS := [
	"boss_blind_block_requires_source",
	"boss_school_comes_from_resolver",
	"resolver_returns_none_without_school_or_source",
	"boss_lethal_branch_stores_source",
	"arms_are_reached_from_basic_attack",
	"chain_uses_the_chain_getter",
	"pierce_uses_the_cudgel_bash_block",
]
const ARMS := ["chain", "pierce_bash", "polycephaly", "empower"]
const BOSS_TYPES := 216
const CASE_COUNT := 3456


class MagicDamageBus:
	extends BattleItemEffects
	var legacy := false

	func deal_damage_magic_sourceless(
		target_id: int, source_team: int, amount: int, school: String = "magic"
	) -> int:
		if legacy:
			# Pre-9g body: every magic arm called the plain bus entry, so the
			# boss took a "normal" hit that carried the dealing hero as source
			# and the declared magic school.
			return deal_damage(target_id, source_team, amount, school)
		return super.deal_damage_magic_sourceless(target_id, source_team, amount, school)


class MagicDamageWorld:
	extends Prototype
	var pre_fix_mode := false
	var deliveries: Dictionary = {}
	var roles: Dictionary = {}
	var hit_order: Array = []
	var types: Dictionary = {}
	var legacy_magic := false

	func _deliver_hit(
		source_id: int,
		source_team: int,
		target: UnitState,
		raw_damage: int,
		school: String,
		origin: Vector2,
		damage_type: String = "normal"
	) -> bool:
		var landed: bool = super._deliver_hit(
			source_id, source_team, target, raw_damage, school, origin, damage_type
		)
		if landed:
			var unit_id := int(target.id)
			var log: Array = deliveries.get(unit_id, [])
			log.append([int(raw_damage), school])
			deliveries[unit_id] = log
			hit_order.append(unit_id)
		return landed

	func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
		var bus := MagicDamageBus.new()
		bus.world = self
		bus.legacy = legacy_magic
		bus.dealer_id = source_hero.id
		bus.dealer_team = source_hero.team
		bus.dealer_pos = source_hero.position
		return bus


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "9g magic damage fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == CASE_COUNT, "9g has sixteen magic arm cases per boss type")
	if cases.size() != CASE_COUNT:
		return
	_check_source_shape(check, fixture)
	var helper := Prior.new()
	var world := MagicDamageWorld.new()
	world.setup_arena()
	for row: Dictionary in cases:
		_check_row(check, helper, world, fixture, row)
	helper._reset_world(world, false)


func _check_row(
	check: Callable, helper: Prior, world: MagicDamageWorld, fixture: Dictionary, row: Dictionary
) -> void:
	var scenario: String = String(row.get("scenario", ""))
	var expected: Dictionary = _replay(helper, world, fixture, row, false)
	var native_old: Dictionary = _replay(helper, world, fixture, row, true)
	if expected.is_empty() or native_old.is_empty():
		return
	check.call(
		_matches(expected, row.get("expected", {})),
		"9g source magic arm outcome on the boss " + _label(row)
	)
	check.call(
		_matches(native_old, row.get("native_old", {})),
		"9g pre-slice native magic arm counterfactual " + _label(row)
	)
	check.call(
		_same_result(expected, native_old) == _is_control(fixture, row),
		"9g divergence is limited to the proccing magic arm scenarios " + _label(row)
	)
	check.call(
		_same_numbers(expected.get("regular_hits", []), native_old.get("regular_hits", [])),
		"9g the regular-unit arm of every magic effect is unchanged " + _label(row)
	)
	if _is_control(fixture, row):
		check.call(
			int(expected.get("boss_hp_loss", -1)) == 0 and bool(expected.get("boss_alive", false)),
			"9g the internal gate blocks the arm in both columns " + _label(row)
		)
		return
	check.call(
		int(expected.get("boss_hp_loss", 0)) > 0,
		"9g the source magic arm lands on the boss " + _label(row)
	)
	var schools: Array = expected.get("boss_schools", [])
	var types: Array = expected.get("boss_damage_types", [])
	var legacy_schools: Array = native_old.get("boss_schools", [])
	var legacy_types: Array = native_old.get("boss_damage_types", [])
	# The pre-9g arm delivered "normal" with the declared magic school, unless the
	# Solar Brand gate dropped the hit (empty record) for a blinded owner.
	var legacy_shape := (
		(legacy_schools.is_empty() and legacy_types.is_empty())
		or (legacy_schools == ["magic"] and legacy_types == ["normal"])
	)
	check.call(
		schools == ["neutral"] and types == ["magic"] and legacy_shape,
		"9g the boss arm keeps the source-less neutral school and the magic type " + _label(row)
	)
	if scenario.ends_with("magic_arm_vs_boss_resist"):
		# Small magic resist can round away on the smallest payload, so the
		# per-row bound is `>=`; the oracle asserts at least one gap per arm.
		check.call(
			int(expected.get("boss_hp_loss", 0)) >= int(native_old.get("boss_hp_loss", -1)),
			"9g boss magic resist no longer cuts the source-less payload " + _label(row)
		)
	elif scenario.ends_with("blind_owner_still_lands"):
		if bool(
			(fixture.get("source", {}).get("owner_true_strike", {}) as Dictionary).get(
				String(row.get("arm", "")), false
			)
		):
			check.call(
				int(native_old.get("boss_hp_loss", 0)) > 0,
				"9g the true-strike item pierces blind in both columns " + _label(row)
			)
		else:
			check.call(
				(
					int(expected.get("boss_hp_loss", 0)) > 0
					and int(native_old.get("boss_hp_loss", -1)) == 0
				),
				"9g a blinded owner still lands the magic proc " + _label(row)
			)
	elif scenario.ends_with("lethal_without_kill_credit"):
		check.call(
			(
				int(expected.get("owner_kills", -1)) == 0
				and int(expected.get("boss_counter", -1)) == 0
				and int(native_old.get("owner_kills", -1)) == 1
				and int(native_old.get("boss_counter", -1)) == 1
			),
			"9g a lethal magic proc credits nobody " + _label(row)
		)
		check.call(
			(
				int(expected.get("last_hit_source_id", 0)) == -1
				and (
					int(native_old.get("last_hit_source_id", -1))
					== int(native_old.get("owner_id", -2))
				)
			),
			"9g the lethal hit keeps the source id the bus sent " + _label(row)
		)


func _replay(
	helper: Prior, world: MagicDamageWorld, fixture: Dictionary, row: Dictionary, legacy: bool
) -> Dictionary:
	helper._reset_world(world, false)
	world.legacy_magic = legacy
	world.miniboss_kill_count = 0
	world.trueboss_kill_count = 0
	var arm: String = String(row.get("arm", ""))
	var arms: Dictionary = fixture.get("source", {}).get("arms", {})
	if not arms.has(arm):
		return {}
	var arm_meta: Dictionary = arms[arm]
	var layout: Dictionary = (fixture.get("source", {}).get("layout", {}) as Dictionary).get(
		arm, {}
	)
	var control := _is_control(fixture, row)
	var boss_offset := float(layout.get("boss_x", 0.0))
	if control and layout.has("control_boss_x"):
		boss_offset = float(layout["control_boss_x"])
	var spawned: Array = _spawn_units(
		world, String(row.get("boss_type", "")), arm, boss_offset, layout
	)
	if spawned.is_empty():
		return {}
	var boss: BossState = spawned[0]
	var hero: HeroState = spawned[1]
	var target: UnitState = spawned[2]
	var regular: UnitState = spawned[3]
	if not hero.items.add(String(arm_meta.get("item", ""))):
		return {}
	var gate: String = String(arm_meta.get("gate_field", "none"))
	var gate_start := int(layout.get("control_gate", 0)) if control else 0
	if gate == "pierce_bash_cd":
		hero.items.pierce_bash_cd = gate_start
	elif gate == "empower_charge":
		hero.items.empower_charge = gate_start
	boss.hp = float(row.get("boss_hp_before", boss.hp))
	if bool(row.get("owner_blind", false)):
		hero.blind_timer = int(fixture.get("source", {}).get("blind_ticks", 90))
		hero.blind_amount = 1.0
	var victim_id := int(boss.id) if String(arm_meta.get("role", "")) == "main" else int(target.id)
	var rng := RandomNumberGenerator.new()
	rng.seed = helper._seed_below(float(_chance_of(arm_meta)))
	var bus: MagicDamageBus = world._battle_item_effects(hero) as MagicDamageBus
	world.deliveries = {}
	world.types = {}
	var hp_before := boss.hp
	# Production enemy list: units in spawn order with the living boss appended
	# last (`_hero_enemy_list`), matching the source
	# `_all_units = minions + heroes + [active_boss]`. `UnitState` has no
	# `max_hp`, so the hand-built entries would drop the minion definition hp.
	hero.items.on_basic_attack_hit(victim_id, BASIC_DAMAGE, world._hero_enemy_list(), rng, bus)
	if boss.defeated:
		world._process_boss_result()
	return {
		"boss_hp_loss": int(roundf(hp_before - boss.hp)),
		"boss_alive": boss.alive,
		"owner_kills": hero.kills,
		"boss_counter": world.miniboss_kill_count + world.trueboss_kill_count,
		"regular_hits": _hit_numbers(world, int(regular.id)),
		"gate_after": _gate_after(hero, gate),
		"boss_schools": _schools_of(world.deliveries.get(int(boss.id), [])),
		"boss_damage_types": _damage_types_of(world.types.get(int(boss.id), [])),
		"last_hit_source_id": boss.last_hit_source_id,
		"owner_id": hero.id,
	}


func _spawn_units(
	world: MagicDamageWorld, boss_type: String, arm: String, boss_offset: float, layout: Dictionary
) -> Array:
	var boss: BossState = world._spawn_boss(boss_type)
	if boss == null:
		return []
	boss.position = Vector2(boss_offset, 0.0)
	boss.previous_position = boss.position
	boss.entrance_timer = 0
	boss.timer = 0
	boss.team = world.RED
	var target: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
	if target == null:
		return []
	target.position = Vector2.ZERO
	var regular: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
	if regular == null:
		return []
	regular.position = Vector2(float(layout.get("regular_x", 0.0)), 0.0)
	# Polycephaly is ranged-only in the source (`is_melee_hero` False), and
	# `HeroState.apply_level_stats` derives the flag from `attack_range`.
	var hero_def = SYLARA if arm == "polycephaly" else KAIZEN
	var hero: HeroState = world.spawn_hero(hero_def, world.BLUE, Vector2(-40.0, 0.0))
	if hero == null:
		return []
	hero.max_hp = 10000.0
	hero.hp = 10000.0
	hero.alive = true
	hero.target_id = int(target.id)
	hero.items.set_hero_runtime(
		hero.id,
		hero.alive,
		hero.hp,
		int(hero.max_hp),
		hero.team,
		hero.facing,
		hero.position,
		hero.target_id
	)
	# The oracle seeds `owner.is_melee_hero = arm != "polycephaly"` with
	# `range` 70/130 (`is_melee_hero` is the `< 110` rule in the source), and
	# Polycephaly only fires for a ranged owner.
	hero.items.hero_melee_flag = 0 if arm == "polycephaly" else 1
	hero.items.hero_range = 130.0 if arm == "polycephaly" else 70.0
	return [boss, hero, target, regular]


func _chance_of(arm_meta: Dictionary) -> float:
	var payload: Dictionary = arm_meta.get("payload", {})
	return float(payload.get("chance", 1.0))


func _gate_after(hero: HeroState, gate: String) -> int:
	if gate == "chains_cd":
		return hero.items.chains_cd
	if gate == "pierce_bash_cd":
		return hero.items.pierce_bash_cd
	if gate == "empower_charge":
		return hero.items.empower_charge
	return 0


func _is_control(fixture: Dictionary, row: Dictionary) -> bool:
	var arms: Dictionary = fixture.get("source", {}).get("arms", {})
	var arm: String = String(row.get("arm", ""))
	if not arms.has(arm):
		return false
	return (
		String(row.get("scenario", ""))
		== String((arms[arm] as Dictionary).get("control_scenario", ""))
	)


func _hit_numbers(world: MagicDamageWorld, unit_id: int) -> Array:
	var out: Array = []
	var log: Array = world.deliveries.get(unit_id, [])
	for entry: Array in log:
		if not entry.is_empty():
			out.append(int(entry[0]))
	return out


func _schools_of(hits: Variant) -> Array:
	var out: Array = []
	var entries: Array = hits if hits is Array else []
	for entry: Array in entries:
		if entry.size() > 1:
			out.append(String(entry[1]))
	return out


func _damage_types_of(log: Variant) -> Array:
	var out: Array = []
	var entries: Array = log if log is Array else []
	for value in entries:
		out.append(String(value))
	return out


func _same_numbers(left: Variant, right: Variant) -> bool:
	var a: Array = left if left is Array else []
	var b: Array = right if right is Array else []
	if a.size() != b.size():
		return false
	for index in range(a.size()):
		if int(a[index]) != int(b[index]):
			return false
	return true


func _field_matches(actual: Variant, expected: Variant, field: String) -> bool:
	# JSON numbers arrive as floats and the string-array fields (`boss_schools`,
	# `boss_damage_types`) must never go through `int()`: compare per field type.
	if field in NUMBER_FIELDS:
		return int(actual) == int(expected)
	if field in NUMBER_LIST_FIELDS:
		return _same_numbers(actual, expected)
	if field in TEXT_LIST_FIELDS:
		return _same_text(actual, expected)
	return bool(actual) == bool(expected)


func _matches(actual: Dictionary, expected: Dictionary) -> bool:
	for field: String in RESULT_FIELDS:
		if not actual.has(field) or not expected.has(field):
			return false
		if not _field_matches(actual[field], expected[field], field):
			return false
	return true


func _same_result(left: Dictionary, right: Dictionary) -> bool:
	for field: String in RESULT_FIELDS:
		if not left.has(field) or not right.has(field):
			return false
		if not _field_matches(left[field], right[field], field):
			return false
	return true


func _same_text(left: Variant, right: Variant) -> bool:
	var a: Array = left if left is Array else []
	var b: Array = right if right is Array else []
	if a.size() != b.size():
		return false
	for index in range(a.size()):
		if String(a[index]) != String(b[index]):
			return false
	return true


func _check_source_shape(check: Callable, fixture: Dictionary) -> void:
	var source: Dictionary = fixture.get("source", {})
	var shape: Dictionary = source.get("ast_shape", {})
	var valid := true
	for arm: String in ARMS:
		valid = valid and int(shape.get(arm + "_take_damage_positional_args", 0)) == 3
		valid = valid and (shape.get(arm + "_take_damage_keywords", [1]) as Array).is_empty()
		valid = valid and String(shape.get(arm + "_take_damage_third_arg", "")) == "'magic'"
	for flag: String in SOURCE_FLAGS:
		valid = valid and bool(shape.get(flag, false))
	check.call(valid, "9g Python AST proves all four magic arms omit source and school")
	var payloads: Dictionary = source.get("arms", {})
	check.call(
		(
			int((payloads.get("chain", {}) as Dictionary).get("payload", {}).get("damage", 0)) == 45
			and (
				int(
					(payloads.get("pierce_bash", {}) as Dictionary).get("payload", {}).get(
						"damage", 0
					)
				)
				== 55
			)
			and (
				int(
					(payloads.get("polycephaly", {}) as Dictionary).get("payload", {}).get(
						"damage", 0
					)
				)
				== 35
			)
			and (
				int((payloads.get("empower", {}) as Dictionary).get("payload", {}).get("damage", 0))
				== 130
			)
			and int(source.get("basic_damage", 0)) == BASIC_DAMAGE
		),
		"9g fixture records the four source payloads"
	)
	var true_strike: Dictionary = source.get("owner_true_strike", {})
	check.call(
		(
			bool(true_strike.get("pierce_bash", false))
			and not bool(true_strike.get("chain", true))
			and not bool(true_strike.get("polycephaly", true))
			and not bool(true_strike.get("empower", true))
		),
		"9g only Sundering Cudgel carries true strike against the blind gate"
	)
	check.call(
		(
			int(fixture.get("boss_type_count", 0)) == BOSS_TYPES
			and int(fixture.get("case_count", 0)) == CASE_COUNT
		),
		"9g fixture carries sixteen counterfactual cases for every boss type"
	)
	var gate_fields: Dictionary = {}
	for arm: String in ARMS:
		gate_fields[arm] = String((payloads.get(arm, {}) as Dictionary).get("gate_field", ""))
	check.call(
		gate_fields == CONTROL_ARM_FIELDS, "9g the arm gates match the native inventory fields"
	)


func _label(row: Dictionary) -> String:
	return (
		String(row.get("boss_type", ""))
		+ "/"
		+ String(row.get("arm", ""))
		+ "/"
		+ String(row.get("scenario", ""))
	)
