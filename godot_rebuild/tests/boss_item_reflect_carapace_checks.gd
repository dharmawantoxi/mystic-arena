extends RefCounted
## 9i: the Razor Carapace Thornmail reflect must reach the attacking boss with
## the source call shape `take_damage(dmg, hero.team, "magic")` - three
## positional arguments, so `Boss.take_damage` (`bosses/base_boss.py:5978`)
## runs with `damage_type="magic"`, `source=None`, `school=None`
## (`hero_items.py:2468`, via `notify_damage_taken`). Before this layer the
## `ReflectItemEffects` bus delivered the `"normal"` damage-type default with
## the declared magic school: the blind gate and the kill credit already
## matched the source (no source on either side), but `school="magic"` cut the
## reflected payload by boss magic resist while the source resolves no school
## at all. The replay drives the real `notify_damage_taken` reflect arm
## through the production bus into `_deliver_hit` -> `BossState.take_damage`
## -> `_process_boss_result`; a legacy bus reproduces the pre-9i arguments for
## the counterfactual column. Non-boss attackers keep the declared school and
## the sourceless delivery, exactly as before.

const ReflectItemEffects = preload("res://scripts/match/reflect_item_effects.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Prior = preload("res://tests/boss_item_cleave_chain_checks.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const FIXTURE := "res://tests/fixtures/boss_item_reflect_carapace_source.json"

const BOSS_ID := 500
const VICTIM_X := -40.0
const RESULT_FIELDS := [
	"boss_hp_loss",
	"boss_alive",
	"owner_kills",
	"boss_counter",
	"regular_hits",
	"reflect_sent",
	"boss_schools",
	"boss_damage_types",
]
const NUMBER_FIELDS := ["boss_hp_loss", "owner_kills", "boss_counter", "reflect_sent"]
const NUMBER_LIST_FIELDS := ["regular_hits"]
const TEXT_LIST_FIELDS := ["boss_schools", "boss_damage_types"]
# Source AST/behaviour flags the Python oracle executes.
const SOURCE_FLAGS := [
	"reflect_pct_needs_thorn_timer",
	"reflect_pct_needs_razor",
	"reflect_guard_requires_alive_attacker",
	"reflect_guard_requires_enemy_team",
	"notify_is_reached_from_hero_take_damage",
	"notify_wraps_reflect_in_try_except",
	"boss_blind_block_requires_source",
	"boss_school_comes_from_resolver",
	"resolver_returns_none_without_school_or_source",
	"boss_lethal_branch_stores_source",
]
const BOSS_TYPES := 216
const CASE_COUNT := 864


class ReflectCarapaceWorld:
	extends Prior.CleaveChainWorld
	var types: Dictionary = {}

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
			var log: Array = types.get(unit_id, [])
			log.append(damage_type)
			types[unit_id] = log
		return landed


class LegacyReflectBus:
	extends ReflectItemEffects

	func deal_damage(target_id: int, src_team: int, amount: int, school: String = "magic") -> int:
		# Pre-9i body: the reflect bus delivered every attacker with the
		# `"normal"` damage-type default and the declared school, so boss
		# magic resist cut the reflected payload.
		var attacker: Object = world.get_unit(target_id)
		if attacker == null:
			return 0
		world._deliver_hit(-1, src_team, attacker, amount, school, attacker.position)
		return amount


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "9i reflect carapace fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == CASE_COUNT, "9i has four reflect cases per boss type")
	if cases.size() != CASE_COUNT:
		return
	_check_source_shape(check, fixture)
	var helper := Prior.new()
	var world := ReflectCarapaceWorld.new()
	world.setup_arena()
	for row: Dictionary in cases:
		_check_row(check, helper, world, fixture, row)
	helper._reset_world(world, false)


func _check_row(
	check: Callable,
	helper: Prior,
	world: ReflectCarapaceWorld,
	fixture: Dictionary,
	row: Dictionary
) -> void:
	var scenario: String = String(row.get("scenario", ""))
	var expected: Dictionary = _replay(helper, world, fixture, row, false)
	var native_old: Dictionary = _replay(helper, world, fixture, row, true)
	if expected.is_empty() or native_old.is_empty():
		return
	check.call(
		_matches(expected, row.get("expected", {})),
		"9i source reflect outcome on the boss " + _label(row)
	)
	check.call(
		_matches(native_old, row.get("native_old", {})),
		"9i pre-slice native reflect counterfactual " + _label(row)
	)
	check.call(
		_same_result(expected, native_old) == _is_control(fixture, row),
		"9i divergence is limited to the proccing reflect scenarios " + _label(row)
	)
	check.call(
		_same_numbers(expected.get("regular_hits", []), native_old.get("regular_hits", [])),
		"9i the regular-unit reflect of every scenario is unchanged " + _label(row)
	)
	check.call(
		int(expected.get("reflect_sent", -1)) == int(native_old.get("reflect_sent", -2)),
		"9i the reflected payload math is unchanged " + _label(row)
	)
	if _is_control(fixture, row):
		check.call(
			int(expected.get("boss_hp_loss", -1)) == 0 and bool(expected.get("boss_alive", false)),
			"9i the control layout keeps the boss untouched " + _label(row)
		)
		if scenario == "reflect_to_minion_unchanged":
			check.call(
				not (expected.get("regular_hits", []) as Array).is_empty(),
				"9i the minion attacker eats the reflected payload " + _label(row)
			)
		else:
			check.call(
				(
					(expected.get("regular_hits", []) as Array).is_empty()
					and int(expected.get("reflect_sent", -1)) == 0
				),
				"9i an inactive thorn reflects nothing " + _label(row)
			)
		return
	check.call(
		int(expected.get("boss_hp_loss", 0)) > 0,
		"9i the source reflect lands on the boss " + _label(row)
	)
	var schools: Array = expected.get("boss_schools", [])
	var types: Array = expected.get("boss_damage_types", [])
	var legacy_schools: Array = native_old.get("boss_schools", [])
	var legacy_types: Array = native_old.get("boss_damage_types", [])
	check.call(
		(
			schools == ["neutral"]
			and types == ["magic"]
			and legacy_schools == ["magic"]
			and legacy_types == ["normal"]
		),
		"9i the boss reflect keeps the source-less neutral school and the magic type " + _label(row)
	)
	if scenario == "reflect_vs_boss_resist":
		# Small magic resist can round away on some boss types, so the
		# per-row bound is `>=`; the oracle asserts the gap exists.
		check.call(
			int(expected.get("boss_hp_loss", 0)) >= int(native_old.get("boss_hp_loss", -1)),
			"9i boss magic resist no longer cuts the reflected payload " + _label(row)
		)
	elif scenario == "reflect_lethal_no_credit":
		check.call(
			(
				int(expected.get("owner_kills", -1)) == 0
				and int(expected.get("boss_counter", -1)) == 0
				and int(native_old.get("owner_kills", -1)) == 0
				and int(native_old.get("boss_counter", -1)) == 0
			),
			"9i a lethal reflect credits nobody on either side " + _label(row)
		)
		check.call(
			(
				int(expected.get("last_hit_source_id", 0)) == -1
				and int(native_old.get("last_hit_source_id", 0)) == -1
			),
			"9i the lethal reflect keeps the sourceless bus id on either side " + _label(row)
		)


func _replay(
	helper: Prior, world: ReflectCarapaceWorld, fixture: Dictionary, row: Dictionary, legacy: bool
) -> Dictionary:
	helper._reset_world(world, false)
	world.miniboss_kill_count = 0
	world.trueboss_kill_count = 0
	var source: Dictionary = fixture.get("source", {})
	var layout: Dictionary = source.get("layout", {})
	var spawned: Array = _spawn_units(world, String(row.get("boss_type", "")), layout)
	if spawned.is_empty():
		return {}
	var boss: BossState = spawned[0]
	var victim: HeroState = spawned[1]
	var extra_one: UnitState = spawned[2]
	var extra_two: UnitState = spawned[3]
	if not victim.items.add("razor_carapace"):
		return {}
	victim.items.set_hero_runtime(
		victim.id,
		victim.alive,
		victim.hp,
		int(victim.max_hp),
		victim.team,
		victim.facing,
		victim.position,
		victim.target_id
	)
	boss.hp = float(row.get("boss_hp_before", boss.hp))
	if bool(row.get("thorn_active", false)):
		victim.items.thorn_timer = int(source.get("thorn_active_ticks", 270))
	else:
		victim.items.thorn_timer = 0
	var attacker: UnitState = extra_one if String(row.get("attacker", "")) == "minion" else boss
	var bus: ReflectItemEffects
	if legacy:
		bus = LegacyReflectBus.new()
	else:
		bus = ReflectItemEffects.new()
	bus.world = world
	bus.defender_team = victim.team
	world.deliveries = {}
	world.types = {}
	var hp_before := boss.hp
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	# Production order in `prototype_battle`: runtime refresh, then the notify
	# with the post-mitigation damage and the reflect bus.
	victim.items.notify_damage_taken(
		int(source.get("incoming_damage", 200)),
		int(attacker.id),
		attacker.team,
		attacker.alive,
		rng,
		bus
	)
	if boss.defeated:
		world._process_boss_result()
	return {
		"boss_hp_loss": int(roundf(hp_before - boss.hp)),
		"boss_alive": boss.alive,
		"owner_kills": victim.kills,
		"boss_counter": world.miniboss_kill_count + world.trueboss_kill_count,
		"regular_hits":
		_hit_numbers(world, int(extra_one.id)) + _hit_numbers(world, int(extra_two.id)),
		"reflect_sent": _reflect_sent(world, int(attacker.id)),
		"boss_schools": _schools_of(world.deliveries.get(int(boss.id), [])),
		"boss_damage_types": _damage_types_of(world.types.get(int(boss.id), [])),
		"last_hit_source_id": boss.last_hit_source_id,
		"owner_id": victim.id,
	}


func _spawn_units(world: ReflectCarapaceWorld, boss_type: String, layout: Dictionary) -> Array:
	var boss: BossState = world._spawn_boss(boss_type)
	if boss == null:
		return []
	boss.position = Vector2(float(layout.get("boss_x", 0.0)), 0.0)
	boss.previous_position = boss.position
	boss.entrance_timer = 0
	boss.timer = 0
	boss.team = world.RED
	var extra_one: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
	if extra_one == null:
		return []
	extra_one.position = Vector2(float(layout.get("extra_one_x", 20.0)), 0.0)
	var extra_two: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
	if extra_two == null:
		return []
	extra_two.position = Vector2(float(layout.get("extra_two_x", 50.0)), 0.0)
	# Razor Carapace carries no role gate, so the default Kaizen victim holds it.
	var victim: HeroState = world.spawn_hero(KAIZEN, world.BLUE, Vector2(VICTIM_X, 0.0))
	if victim == null:
		return []
	victim.max_hp = 10000.0
	victim.hp = 10000.0
	victim.alive = true
	victim.target_id = int(boss.id)
	victim.items.set_hero_runtime(
		victim.id,
		victim.alive,
		victim.hp,
		int(victim.max_hp),
		victim.team,
		victim.facing,
		victim.position,
		victim.target_id
	)
	return [boss, victim, extra_one, extra_two]


func _is_control(fixture: Dictionary, row: Dictionary) -> bool:
	var arm: Dictionary = fixture.get("source", {}).get("arm", {})
	var controls: Array = arm.get("control_scenarios", [])
	return String(row.get("scenario", "")) in controls


func _hit_numbers(world: ReflectCarapaceWorld, unit_id: int) -> Array:
	var out: Array = []
	var log: Array = world.deliveries.get(unit_id, [])
	for entry: Array in log:
		if not entry.is_empty():
			out.append(int(entry[0]))
	return out


func _reflect_sent(world: ReflectCarapaceWorld, attacker_id: int) -> int:
	var log: Array = world.deliveries.get(attacker_id, [])
	if log.is_empty():
		return 0
	return int((log[0] as Array)[0])


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
	valid = valid and int(shape.get("reflect_take_damage_positional_args", 0)) == 3
	valid = valid and (shape.get("reflect_take_damage_keywords", [1]) as Array).is_empty()
	valid = valid and String(shape.get("reflect_take_damage_third_arg", "")) == "'magic'"
	valid = (valid and int(shape.get("reflect_take_damage_fallback_positional_args", 0)) == 2)
	valid = (
		valid and (shape.get("reflect_take_damage_fallback_keywords", [1]) as Array).is_empty()
	)
	for flag: String in SOURCE_FLAGS:
		valid = valid and bool(shape.get(flag, false))
	check.call(valid, "9i Python AST proves the reflect arm omits source and school")
	var arm: Dictionary = source.get("arm", {})
	var payload: Dictionary = arm.get("payload", {})
	check.call(
		float(payload.get("reflect_pct", 0.0)) == 0.85,
		"9i fixture records the source reflect fraction"
	)
	check.call(
		int(payload.get("duration", 0)) == 270, "9i fixture records the source thorn duration"
	)
	check.call(
		(
			int(fixture.get("boss_type_count", 0)) == BOSS_TYPES
			and int(fixture.get("case_count", 0)) == CASE_COUNT
		),
		"9i fixture carries four counterfactual cases for every boss type"
	)
	check.call(
		int(source.get("incoming_damage", 0)) == 200,
		"9i the incoming victim damage matches the replay"
	)


func _label(row: Dictionary) -> String:
	return (
		String(row.get("boss_type", ""))
		+ "/"
		+ String(row.get("arm", ""))
		+ "/"
		+ String(row.get("scenario", ""))
	)
