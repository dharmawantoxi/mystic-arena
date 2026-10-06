# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8z native suite: hero item cleave and arc chain pick the active boss as
## a secondary target. The source melee call site builds
## `_all_units = list(gi.minions) + list(gi.get_all_heroes())` and appends the
## living boss (`_all_units.append(gi.active_boss)`, `_entity.py:4401-4410`); the
## ranged call site uses `Hero._collect_onhit_units()` (`_entity.py:4215-4232`),
## which appends it the same way. Cleave (`hero_items.py:2504-2518`) splashes
## `int(damage * pct)` on every living enemy unit inside the inclusive radius
## measured from the main target, and arc chain (`hero_items.py:2552-2560`)
## appends every living enemy unit inside `chain["radius"]` in list order, breaks
## once `len(hit) >= chain["targets"]` and damages each entry with
## `u.take_damage(chain["damage"], h.team, "magic")`.
## Before this layer `BattleItemEffects.cleave_splash` / `chain_targets` scanned
## only `world.units`, and the registry never holds the boss (`active_boss` only
## lives in `_by_id`), so a boss inside the cleave/arc radius took no splash and
## was never chained. Both arms now consult `world.active_boss` last.

const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const FIXTURE := "res://tests/fixtures/boss_item_cleave_chain_source.json"

const SOURCE_FLAGS := [
	"melee_onhit_list_appends_live_boss",
	"collect_onhit_units_appends_live_boss",
	"cleave_iterates_all_units",
	"cleave_radius_is_inclusive",
	"cleave_skips_same_team",
	"cleave_skips_the_main_target",
	"chain_iterates_all_units",
	"chain_appends_inside_radius",
	"chain_breaks_when_slots_are_full",
	"chain_damage_is_magic"
]

const CLEAVE_BOSS := "cleave_splashes_boss_inside_radius"
const CLEAVE_OUT := "cleave_skips_boss_outside_radius"
const CHAIN_BOSS := "fenrir_chain_hits_boss"
const CHAIN_FULL := "chain_slots_fill_before_boss"
const CLEAVE_ITEM := "cleave_axe"
const CHAIN_ITEM := "fenrir_chain"
# Native delivery schools for the two arms. Arc chain deals
# `effects.deal_damage(..., "magic")` like the source third positional argument.
# Cleave still splashes physical onto regular units, but layer 9e delivers the
# boss arm as "neutral": the source call `u.take_damage(splash, h.team)` passes
# no school, so `resolve_damage_school` returns `None` for the boss.
const CLEAVE_SCHOOL := "neutral"
const CHAIN_SCHOOL := "magic"
const BASIC_DAMAGE := 50
const SEED_SCAN_LIMIT := 4096


class CleaveChainBus:
	extends BattleItemEffects
	# The recording dictionary is owned by the world. The bus must never be
	# stored back on the world: two RefCounted objects referencing each other
	# form a cycle that survives to engine exit and trips the CI gate with
	# `ERROR: resources still in use at exit`.
	var pre_fix_mode := false

	func cleave_splash(
		target_id: int, src_team: int, src_pos: Vector2, splash: int, radius: float
	) -> void:
		if pre_fix_mode:
			_pre_fix_cleave(target_id, src_team, src_pos, splash, radius)
			return
		super.cleave_splash(target_id, src_team, src_pos, splash, radius)

	func chain_targets(target_id: int, src_team: int, radius: float, count: int) -> Array:
		if pre_fix_mode:
			return _pre_fix_chain(target_id, src_team, radius, count)
		return super.chain_targets(target_id, src_team, radius, count)

	func _pre_fix_cleave(
		target_id: int, src_team: int, src_pos: Vector2, splash: int, radius: float
	) -> void:
		# Pre-8z body: `world.units` only, so the boss was never a candidate.
		var center: Object = world.get_unit(target_id)
		if center == null:
			return
		var center_pos: Vector2 = center.position
		for u in world.units:
			if u == null or not u.alive or u.team == src_team or u.id == target_id:
				continue
			if center_pos.distance_to(u.position) <= radius:
				world._deliver_hit(dealer_id, src_team, u, splash, "physical", src_pos)

	func _pre_fix_chain(target_id: int, src_team: int, radius: float, count: int) -> Array:
		var tgt: Object = world.get_unit(target_id)
		if tgt == null or not tgt.alive:
			return []
		var center: Vector2 = tgt.position
		var hits: Array = [target_id]
		for u in world.units:
			if u == null or not u.alive or u.team == src_team or u.id == target_id:
				continue
			if center.distance_to(u.position) <= radius:
				hits.append(u.id)
				if hits.size() >= count:
					break
		return hits


class CleaveChainWorld:
	extends Prototype
	var pre_fix_mode := false
	var deliveries: Dictionary = {}
	var roles: Dictionary = {}
	var hit_order: Array = []

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
		var bus := CleaveChainBus.new()
		bus.world = self
		bus.pre_fix_mode = pre_fix_mode
		bus.dealer_id = source_hero.id
		bus.dealer_team = source_hero.team
		bus.dealer_pos = source_hero.position
		return bus


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var parsed: bool = fixture is Dictionary and fixture.has("source") and fixture.has("cases")
	if parsed:
		for flag in SOURCE_FLAGS:
			parsed = parsed and bool(fixture.source.get(flag, false))
	check.call(parsed, "boss item cleave/chain fixture parses with every source flag")
	if not fixture is Dictionary:
		return
	_check_source_meta(check, fixture)
	_check_fixture_payloads(check, fixture)
	_replay_cases(check, fixture)
	_live_match_contrasts(check, fixture)


func _check_source_meta(check: Callable, fixture: Dictionary) -> void:
	var src: Dictionary = fixture.get("source", {})
	check.call(
		(
			is_equal_approx(float(src.get("cleave_pct", 0.0)), 0.50)
			and is_equal_approx(float(src.get("cleave_radius", 0.0)), 110.0)
			and int(src.get("chain_damage", 0)) == 45
			and int(src.get("chain_targets", 0)) == 3
			and is_equal_approx(float(src.get("chain_radius", 0.0)), 240.0)
			and int(src.get("coil_damage", 0)) == 40
			and int(src.get("coil_targets", 0)) == 3
			and is_equal_approx(float(src.get("coil_radius", 0.0)), 240.0)
			and int(src.get("basic_damage", 0)) == BASIC_DAMAGE
			and int(fixture.get("boss_type_count", 0)) == 216
			and int(fixture.get("case_count", 0)) == 864
		),
		"source metadata records cleave/chain payloads and 864 boss cases"
	)


func _layout(fixture: Dictionary, scenario: String) -> Dictionary:
	var layouts: Dictionary = fixture.get("source", {}).get("scenario_layout", {})
	return layouts.get(scenario, {})


func _same_hits(actual: Variant, exp: Variant) -> bool:
	var left: Array = actual if actual is Array else []
	var right: Array = exp if exp is Array else []
	if left.size() != right.size():
		return false
	for index in range(left.size()):
		var got: Array = left[index]
		if got.is_empty() or int(got[0]) != int(float(right[index])):
			return false
	return true


func _same_numbers(actual: Variant, exp: Variant) -> bool:
	# Fixture numbers arrive as JSON floats; GDScript `Array ==` compares element
	# hashes, so `[25.0] == [25]` is false. Compare numerically instead.
	var left: Array = actual if actual is Array else []
	var right: Array = exp if exp is Array else []
	if left.size() != right.size():
		return false
	for index in range(left.size()):
		if int(float(left[index])) != int(float(right[index])):
			return false
	return true


func _schools_of(actual: Variant) -> Array:
	var out: Array = []
	var left: Array = actual if actual is Array else []
	for entry in left:
		var got: Array = entry
		if got.size() > 1:
			out.append(String(got[1]))
	return out


func _same_roles(actual: Variant, exp: Variant) -> bool:
	var left: Array = actual if actual is Array else []
	var right: Array = exp if exp is Array else []
	if left.size() != right.size():
		return false
	for index in range(left.size()):
		if String(left[index]) != String(right[index]):
			return false
	return true


func _matches_row(actual: Dictionary, exp: Dictionary) -> bool:
	return (
		_same_hits(actual.get("target_hits", []), exp.get("target_hits", []))
		and _same_hits(actual.get("minion_hits", []), exp.get("minion_hits", []))
		and _same_hits(actual.get("boss_hits", []), exp.get("boss_hits", []))
		and _same_roles(actual.get("chain_roles", []), exp.get("chain_roles", []))
	)


func _check_fixture_payloads(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	var cleave_rows := true
	var cleave_out_rows := true
	var chain_rows := true
	var full_rows := true
	var minion_arm := true
	for entry in cases:
		var scenario: String = String(entry.get("scenario", ""))
		var exp: Dictionary = entry.get("expected", {})
		var without: Dictionary = entry.get("expected_without_boss", {})
		minion_arm = (
			minion_arm and _same_numbers(exp.get("minion_hits", []), without.get("minion_hits", []))
		)
		if scenario == CLEAVE_BOSS:
			cleave_rows = (
				cleave_rows
				and _same_numbers(exp.get("boss_hits", []), [25])
				and _same_numbers(exp.get("minion_hits", []), [25])
				and _same_numbers(exp.get("target_hits", []), [])
				and _same_numbers(without.get("boss_hits", []), [])
			)
		elif scenario == CLEAVE_OUT:
			cleave_out_rows = (
				cleave_out_rows
				and _same_numbers(exp.get("boss_hits", []), [])
				and _same_numbers(without.get("boss_hits", []), [])
				and _same_numbers(exp.get("minion_hits", []), [25])
			)
		elif scenario == CHAIN_BOSS:
			chain_rows = (
				chain_rows
				and _same_numbers(exp.get("boss_hits", []), [45])
				and _same_numbers(exp.get("target_hits", []), [45])
				and _same_roles(exp.get("chain_roles", []), ["target", "minion", "boss"])
				and _same_numbers(without.get("boss_hits", []), [])
				and _same_roles(without.get("chain_roles", []), ["target", "minion"])
				and String(exp.get("chain_damage_type", "")) == CHAIN_SCHOOL
			)
		else:
			full_rows = (
				full_rows
				and _same_numbers(exp.get("boss_hits", []), [])
				and _same_numbers(without.get("boss_hits", []), [])
				and _same_roles(exp.get("chain_roles", []), ["target", "minion", "minion"])
				and _same_roles(without.get("chain_roles", []), ["target", "minion", "minion"])
			)
	check.call(cleave_rows, "cleave splashes 25 onto the boss inside the 110 px radius")
	check.call(cleave_out_rows, "cleave skips the boss outside the radius in both columns")
	check.call(chain_rows, "arc chain appends the boss as the last slot and deals 45 magic")
	check.call(full_rows, "full chain slots end the scan before the boss in both columns")
	check.call(minion_arm, "the regular-unit arm of cleave/chain is identical in both columns")


func _reset_world(world: CleaveChainWorld, pre_fix_mode: bool) -> void:
	world.pre_fix_mode = pre_fix_mode
	world.deliveries = {}
	world.roles = {}
	world.hit_order = []
	world.units.clear()
	world.projectiles.clear()
	world.recent_events.clear()
	if world.active_boss != null:
		world._by_id.erase(world.active_boss.id)
		world.active_boss = null
	world._by_id.clear()


func _seed_below(threshold: float) -> int:
	# Deterministic roll control: the first `randf()` of this seed is below the
	# item chance, so the on-hit arm always fires (mirrors the oracle's
	# `random.random() -> 0.0`).
	for seed_value in range(SEED_SCAN_LIMIT):
		var probe := RandomNumberGenerator.new()
		probe.seed = seed_value
		if probe.randf() < threshold:
			return seed_value
	return 0


func _spawn_case_units(world: CleaveChainWorld, boss_type: String, layout: Dictionary) -> Array:
	var boss: BossState = world._spawn_boss(boss_type)
	if boss == null:
		return []
	boss.position = Vector2(float(layout.get("boss_offset", 0.0)), 0.0)
	boss.previous_position = boss.position
	boss.entrance_timer = 0
	boss.timer = 0
	var target: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
	if target == null:
		return []
	target.position = Vector2.ZERO
	world.roles[int(target.id)] = "target"
	var minions: Array = []
	for entry in layout.get("minion_offsets", []):
		var offsets: Array = entry
		var minion: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
		if minion == null:
			return []
		minion.position = Vector2(float(offsets[1]), 0.0)
		world.roles[int(minion.id)] = "minion"
		minions.append(minion)
	world.roles[int(boss.id)] = "boss"
	var hero: HeroState = world.spawn_hero(KAIZEN, world.BLUE, Vector2(-40.0, 0.0))
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
	return [boss, hero, target, minions]


func _run_scenario(
	world: CleaveChainWorld,
	fixture: Dictionary,
	boss_type: String,
	scenario: String,
	pre_fix_mode: bool
) -> Dictionary:
	_reset_world(world, pre_fix_mode)
	var layout: Dictionary = _layout(fixture, scenario)
	if layout.is_empty():
		return {}
	var spawned: Array = _spawn_case_units(world, boss_type, layout)
	if spawned.is_empty():
		return {}
	var boss: BossState = spawned[0]
	var hero: HeroState = spawned[1]
	var target: UnitState = spawned[2]
	var minions: Array = spawned[3]
	if minions.is_empty():
		return {}
	var near: UnitState = minions[0]
	if not hero.items.add(String(layout.get("item", ""))):
		return {}
	var src: Dictionary = fixture.get("source", {})
	var rng := RandomNumberGenerator.new()
	rng.seed = _seed_below(float(src.get("chain_chance", 0.2)))
	var bus: CleaveChainBus = world._battle_item_effects(hero) as CleaveChainBus
	var boss_hp := float(boss.hp)
	# Real inventory path: `on_basic_attack_hit` derives cleave/chain from the
	# equipped item and calls the bus, exactly like the source melee call site.
	hero.items.on_basic_attack_hit(int(target.id), BASIC_DAMAGE, [], rng, bus)
	var roles: Array = []
	if String(layout.get("item", "")) == CHAIN_ITEM:
		# Roles come from the delivery order, which is the source `hit` list order
		# (`for u in hit: u.take_damage(...)`); re-running `chain_targets` after
		# the damage would drop any victim the arc killed.
		for tid in world.hit_order:
			roles.append(String(world.roles.get(int(tid), "unknown")))
	return {
		"target_hits": world.deliveries.get(int(target.id), []),
		"minion_hits": world.deliveries.get(int(near.id), []),
		"boss_hits": world.deliveries.get(int(boss.id), []),
		"chain_roles": roles,
		"boss_hp_lost": boss_hp - float(boss.hp),
		"boss_schools": _schools_of(world.deliveries.get(int(boss.id), [])),
	}


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == 864, "boss item cleave/chain fixture has 864 cases (216 bosses x 4)")
	var world := CleaveChainWorld.new()
	var expected_rows := true
	var contrast_rows := true
	var boss_damage := true
	var chain_school := true
	for entry in cases:
		var boss_type: String = String(entry.get("boss_type", ""))
		var scenario: String = String(entry.get("scenario", ""))
		var exp: Dictionary = entry.get("expected", {})
		var without: Dictionary = entry.get("expected_without_boss", {})
		var got: Dictionary = _run_scenario(world, fixture, boss_type, scenario, false)
		var pre: Dictionary = _run_scenario(world, fixture, boss_type, scenario, true)
		if got.is_empty() or pre.is_empty():
			expected_rows = false
			contrast_rows = false
			continue
		expected_rows = expected_rows and _matches_row(got, exp)
		contrast_rows = contrast_rows and _matches_row(pre, without)
		var wants_boss: bool = not (exp.get("boss_hits", []) as Array).is_empty()
		boss_damage = (
			boss_damage
			and (float(got.get("boss_hp_lost", 0.0)) > 0.0) == wants_boss
			and is_equal_approx(float(pre.get("boss_hp_lost", -1.0)), 0.0)
		)
		if wants_boss and scenario == CHAIN_BOSS:
			chain_school = (
				chain_school and (got.get("boss_schools", []) as Array) == [CHAIN_SCHOOL]
			)
		elif wants_boss:
			chain_school = (
				chain_school and (got.get("boss_schools", []) as Array) == [CLEAVE_SCHOOL]
			)
	check.call(
		expected_rows, "native cleave/chain replay matches the source column for all 864 cases"
	)
	check.call(
		contrast_rows, "pre-layer scan matches the world.units-only column for all 864 cases"
	)
	check.call(boss_damage, "the boss only loses hp when the source list reaches it")
	check.call(chain_school, "boss splash stays physical and boss chain damage stays magic")


func _live_match_contrasts(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	if cases.is_empty():
		check.call(false, "fixture has no cases for the live contrast")
		return
	var boss_type: String = String((cases[0] as Dictionary).get("boss_type", ""))
	var world := CleaveChainWorld.new()
	var cleave_hits_boss := false
	var chain_hits_boss := false
	var dead_boss_safe := false
	var boss_main_target_safe := false
	for scenario in [CLEAVE_BOSS, CHAIN_BOSS]:
		var got: Dictionary = _run_scenario(world, fixture, boss_type, String(scenario), false)
		var pre: Dictionary = _run_scenario(world, fixture, boss_type, String(scenario), true)
		if got.is_empty() or pre.is_empty():
			continue
		if String(scenario) == CLEAVE_BOSS:
			cleave_hits_boss = (
				(got.get("boss_hits", []) as Array).size() == 1
				and (pre.get("boss_hits", []) as Array).is_empty()
				and float(got.get("boss_hp_lost", 0.0)) > 0.0
			)
		else:
			chain_hits_boss = (
				(got.get("boss_hits", []) as Array).size() == 1
				and (pre.get("boss_hits", []) as Array).is_empty()
				and _same_roles(got.get("chain_roles", []), ["target", "minion", "boss"])
				and _same_roles(pre.get("chain_roles", []), ["target", "minion"])
			)

	# Guards: a dead boss is not a candidate, and the boss as the main target is
	# never re-selected as its own secondary target.
	_reset_world(world, false)
	var layout: Dictionary = _layout(fixture, CHAIN_BOSS)
	var spawned: Array = _spawn_case_units(world, boss_type, layout)
	if not spawned.is_empty():
		var boss: BossState = spawned[0]
		var hero: HeroState = spawned[1]
		var target: UnitState = spawned[2]
		var bus: CleaveChainBus = world._battle_item_effects(hero) as CleaveChainBus
		var live_roles: Array = []
		for tid in bus.chain_targets(int(target.id), world.BLUE, 240.0, 3):
			live_roles.append(String(world.roles.get(int(tid), "unknown")))
		boss.alive = false
		var dead_roles: Array = []
		for tid in bus.chain_targets(int(target.id), world.BLUE, 240.0, 3):
			dead_roles.append(String(world.roles.get(int(tid), "unknown")))
		boss.alive = true
		dead_boss_safe = (
			_same_roles(live_roles, ["target", "minion", "boss"])
			and _same_roles(dead_roles, ["target", "minion"])
		)
		world.deliveries = {}
		hero.items.add(CLEAVE_ITEM)
		var rng := RandomNumberGenerator.new()
		rng.seed = _seed_below(0.5)
		hero.items.on_basic_attack_hit(int(boss.id), BASIC_DAMAGE, [], rng, bus)
		boss_main_target_safe = (world.deliveries.get(int(boss.id), []) as Array).is_empty()
	check.call(cleave_hits_boss, "live cleave splash lands on the active boss")
	check.call(chain_hits_boss, "live arc chain appends the active boss as a secondary target")
	check.call(dead_boss_safe, "a dead boss is never an on-hit candidate")
	check.call(boss_main_target_safe, "the boss as main target never cleaves itself")
