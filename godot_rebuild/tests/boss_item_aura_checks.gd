# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8y native suite: the hero item enemy-unit auras call `u.apply_debuff`
## on every living unit in the source - Everfrost Guard Freezing Aura
## `u.apply_debuff("atk_slow", f_as, 30)` / `u.apply_debuff("anti_heal", ...)`
## (`hero_items.py:2826-2844`), Solar Brand Scorched Earth
## `u.apply_debuff("burn", s_burn, 30, source_team=src.team)` plus
## `u.apply_miss_chance(s_blind, 30)` (`hero_items.py:2845-2860`) and Searbrand
## Cauterize `u.apply_debuff("anti_heal", se_heal, 30)` /
## `u.apply_debuff("burn", se_burn, 30, ...)` (`hero_items.py:2861-2873`) - and
## `update_auras` iterates `all_units = _collect_all_units(all_heroes)`, which
## appends the live `active_boss` (`hero_items.py:2772`, `2913-2930`).
## `Boss.apply_debuff` (`bosses/base_boss.py:540-552`) cuts only `atk_slow`
## (tenacity 0.50: 0.30/30 becomes 0.15/15) and its burn branch resets
## `burn_accum`/`burn_tick_cd` for a burn that starts after the previous one
## expired, so:
## * `PrototypeBattle._update_auras` delivers the Freezing Aura atk_slow through
##   `_aura_item_effects()` -> `BattleItemEffects.apply_atk_slow` -> `BossState`.
## * `BattleItemEffects.apply_burn` (Searbrand Brand Burst) delegates to
##   `BossState.apply_debuff` instead of writing the boss burn fields raw, which
##   used to keep the stale tick clock of the expired burn.

const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const FIXTURE := "res://tests/fixtures/boss_item_aura_source.json"

const SOURCE_FLAGS := [
	"auras_loop_over_collected_units",
	"collect_all_units_appends_live_boss",
	"collect_all_units_requires_alive_boss",
	"everfrost_aura_applies_atk_slow_and_anti_heal",
	"solar_aura_burns_with_source_team",
	"solar_aura_blinds_via_miss_chance",
	"searbrand_aura_applies_anti_heal_and_burn",
	"aura_arms_skip_the_source_team",
	"boss_apply_debuff_cuts_only_atk_slow",
	"tower_store_resets_expired_burn_clock"
]

const FROST_SCENARIO := "everfrost_freezing_aura_on_boss"
const SOLAR_SCENARIO := "solar_scorched_earth_on_boss"
const SEAR_SCENARIO := "searbrand_cauterize_on_boss"
const BURST_SCENARIO := "brand_burst_burn_after_expired_burn"
const AURA_ITEM := {
	"everfrost_freezing_aura_on_boss": "everfrost_guard",
	"solar_scorched_earth_on_boss": "solar_brand",
	"searbrand_cauterize_on_boss": "searbrand",
}
# Pre-layer native delivery: the aura arms called the world-level strongest-wins
# store (`minion_battle.apply_atk_slow` / `apply_anti_heal` / `apply_burn`),
# while `BattleItemEffects.apply_burn` wrote the boss burn fields directly.
const PRE_FIX_WORLD_STORE := "world_store"
const PRE_FIX_BURN_FIELD_WRITE := "burn_field_write"

const AURA_DURATION := 30
const BURN_TICK := 30
const EXPIRED_BURN_DPS := 21.0
const EXPIRED_BURN_TICKS := 7
const BRAND_BURST_DPS := 22.0
const BRAND_BURST_DURATION := 180
const BRAND_BURST_TICKS := 23


class ItemAuraBus:
	extends BattleItemEffects
	var pre_fix_mode := ""
	var atk_slow_calls: Array = []
	var anti_heal_calls: Array = []
	var burn_calls: Array = []

	func apply_atk_slow(target_id: int, amount: float, duration: int) -> void:
		var t: Object = world.get_unit(target_id)
		if t is BossState:
			atk_slow_calls.append([amount, duration])
			if pre_fix_mode == PRE_FIX_WORLD_STORE:
				# Pre-8y `world.apply_atk_slow`: strongest-wins store, no tenacity.
				var boss := t as BossState
				if amount > boss.atk_slow_amount or boss.atk_slow_timer < duration:
					boss.atk_slow_amount = amount
					boss.atk_slow_timer = duration
				return
		super.apply_atk_slow(target_id, amount, duration)

	func apply_anti_heal(target_id: int, amount: float, duration: int) -> void:
		var t: Object = world.get_unit(target_id)
		if t is BossState:
			anti_heal_calls.append([amount, duration])
			if not pre_fix_mode.is_empty():
				# Pre-8y `world.apply_anti_heal`: untempered strongest-wins store.
				var boss := t as BossState
				if amount > boss.anti_heal_amount or boss.anti_heal_timer < duration:
					boss.anti_heal_amount = amount
					boss.anti_heal_timer = duration
				return
		super.apply_anti_heal(target_id, amount, duration)

	func apply_burn(target_id: int, dps: float, duration: int, source_team: int) -> void:
		var t: Object = world.get_unit(target_id)
		if t is BossState:
			burn_calls.append([dps, duration, source_team])
			var boss := t as BossState
			if pre_fix_mode == PRE_FIX_WORLD_STORE:
				# Pre-8y aura arm: `minion_battle.apply_burn` world store, which
				# did reset the clock but wrote the team unconditionally.
				if boss.burn_timer <= 0:
					boss.burn_dps = dps
					boss.burn_accum = 0.0
					boss.burn_tick_cd = BURN_TICK
				else:
					boss.burn_dps = maxf(boss.burn_dps, dps)
				boss.burn_timer = maxi(boss.burn_timer, duration)
				boss.burn_team = source_team
				return
			if pre_fix_mode == PRE_FIX_BURN_FIELD_WRITE:
				# Pre-8y `BattleItemEffects.apply_burn`: raw field write that
				# kept the stale `burn_tick_cd` of the expired burn.
				boss.burn_dps = maxf(boss.burn_dps, dps)
				boss.burn_timer = maxi(boss.burn_timer, duration)
				boss.burn_team = source_team
				return
		super.apply_burn(target_id, dps, duration, source_team)


class ItemAuraWorld:
	extends Prototype
	var pre_fix_mode := ""
	var last_aura_bus: ItemAuraBus = null

	func _aura_item_effects() -> BattleItemEffects:
		var bus := ItemAuraBus.new()
		bus.world = self
		bus.pre_fix_mode = pre_fix_mode
		last_aura_bus = bus
		return bus

	func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
		var bus := ItemAuraBus.new()
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
	check.call(parsed, "boss item aura fixture parses with every source flag")
	if not fixture is Dictionary:
		return
	_check_source_meta(check, fixture)
	_check_fixture_payloads(check, fixture)
	_replay_cases(check, fixture)
	_live_match_contrasts(check)


func _check_source_meta(check: Callable, fixture: Dictionary) -> void:
	var src: Dictionary = fixture.get("source", {})
	check.call(
		(
			is_equal_approx(float(src.get("everfrost_aura_radius", 0.0)), 300.0)
			and is_equal_approx(float(src.get("everfrost_aura_atk_slow", 0.0)), 0.30)
			and is_equal_approx(float(src.get("everfrost_aura_anti_heal", 0.0)), 0.40)
			and is_equal_approx(float(src.get("solar_aura_radius", 0.0)), 280.0)
			and is_equal_approx(float(src.get("solar_aura_burn_dps", 0.0)), 28.0)
			and is_equal_approx(float(src.get("solar_aura_blind", 0.0)), 0.18)
			and is_equal_approx(float(src.get("searbrand_aura_radius", 0.0)), 300.0)
			and is_equal_approx(float(src.get("searbrand_aura_anti_heal", 0.0)), 0.50)
			and is_equal_approx(float(src.get("searbrand_aura_burn_dps", 0.0)), 6.0)
			and is_equal_approx(float(src.get("searbrand_burst_burn_dps", 0.0)), 22.0)
			and int(src.get("searbrand_burst_burn_duration", 0)) == 180
			and int(src.get("aura_debuff_ticks", 0)) == AURA_DURATION
			and int(src.get("burn_tick", 0)) == BURN_TICK
			and int(fixture.get("boss_type_count", 0)) == 216
			and int(fixture.get("case_count", 0)) == 864
		),
		"source metadata records aura payloads, burn clocks, and 864 boss cases"
	)


func _same_calls(actual: Variant, exp: Variant) -> bool:
	var left: Array = actual if actual is Array else []
	var right: Array = exp if exp is Array else []
	if left.size() != right.size():
		return false
	for index in range(left.size()):
		var a: Array = left[index]
		var b: Array = right[index]
		if a.size() != b.size():
			return false
		for slot in range(a.size()):
			if not is_equal_approx(float(a[slot]), float(b[slot])):
				return false
	return true


func _same_meta(actual: Variant, exp: Variant) -> bool:
	var left: Dictionary = actual if actual is Dictionary else {}
	var right: Dictionary = exp if exp is Dictionary else {}
	if left.size() != right.size():
		return false
	for key in right:
		if not left.has(key):
			return false
		var want: float = float(right[key])
		var got: float = float(left[key])
		if key == "burn_dps" or key == "burn_accum":
			if not is_equal_approx(got, want):
				return false
		elif int(got) != int(want):
			return false
	return true


func _matches_row(actual: Dictionary, exp: Dictionary) -> bool:
	# Only `apply_atk_slow_calls` is bus-recorded natively (the layer 8y aura arm
	# and, for the Brand Burst row, `apply_burn_calls` in `_cross_column_ok`).
	# `apply_anti_heal_calls` / `apply_miss_chance_calls` stay on the direct
	# world/unit path, so `_check_fixture_payloads` keeps those source payloads
	# and the `boss_anti_heal_*`/`boss_blind_*` fields below carry the native
	# result of the same arms.
	return (
		_same_calls(actual.get("apply_atk_slow_calls", []), exp.get("apply_atk_slow_calls", []))
		and _same_meta(actual.get("before_delivery", {}), exp.get("before_delivery", {}))
		and _same_meta(actual.get("after_delivery", {}), exp.get("after_delivery", {}))
		and is_equal_approx(
			float(actual.get("boss_atk_slow_amount", -1.0)),
			float(exp.get("boss_atk_slow_amount", -2.0))
		)
		and int(actual.get("boss_atk_slow_timer", -1)) == int(exp.get("boss_atk_slow_timer", -2))
		and is_equal_approx(
			float(actual.get("boss_anti_heal_amount", -1.0)),
			float(exp.get("boss_anti_heal_amount", -2.0))
		)
		and (
			int(actual.get("boss_anti_heal_timer", -1)) == int(exp.get("boss_anti_heal_timer", -2))
		)
		and is_equal_approx(
			float(actual.get("boss_burn_dps", -1.0)), float(exp.get("boss_burn_dps", -2.0))
		)
		and int(actual.get("boss_burn_timer", -1)) == int(exp.get("boss_burn_timer", -2))
		and int(actual.get("boss_burn_team", -2)) == int(exp.get("boss_burn_team", -3))
		and is_equal_approx(
			float(actual.get("boss_burn_accum", -1.0)), float(exp.get("boss_burn_accum", -2.0))
		)
		and int(actual.get("boss_burn_tick_cd", -1)) == int(exp.get("boss_burn_tick_cd", -2))
		and is_equal_approx(
			float(actual.get("boss_blind_amount", -1.0)), float(exp.get("boss_blind_amount", -2.0))
		)
		and int(actual.get("boss_blind_timer", -1)) == int(exp.get("boss_blind_timer", -2))
		and (
			int(actual.get("burn_damage_after_23_ticks", -1))
			== int(exp.get("burn_damage_after_23_ticks", -2))
		)
	)


func _check_fixture_payloads(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	var frost_payloads := true
	var solar_payloads := true
	var sear_payloads := true
	var burst_payloads := true
	var cross_columns := true
	for entry in cases:
		var scenario: String = String(entry.get("scenario", ""))
		var exp: Dictionary = entry.get("expected", {})
		var without: Dictionary = entry.get("expected_without_boss_store", {})
		cross_columns = (
			cross_columns
			and (
				exp.get("apply_atk_slow_calls", []) == without.get("apply_atk_slow_calls", [])
				and exp.get("apply_anti_heal_calls", []) == without.get("apply_anti_heal_calls", [])
				and exp.get("apply_burn_calls", []) == without.get("apply_burn_calls", [])
			)
		)
		if scenario == FROST_SCENARIO:
			frost_payloads = (
				frost_payloads
				and (
					_same_calls(exp.get("apply_atk_slow_calls", []), [[0.30, AURA_DURATION]])
					and _same_calls(exp.get("apply_anti_heal_calls", []), [[0.40, AURA_DURATION]])
				)
			)
		elif scenario == SOLAR_SCENARIO:
			solar_payloads = (
				solar_payloads
				and (
					_same_calls(exp.get("apply_burn_calls", []), [[28.0, AURA_DURATION, 0]])
					and _same_calls(exp.get("apply_miss_chance_calls", []), [[0.18, AURA_DURATION]])
				)
			)
		elif scenario == SEAR_SCENARIO:
			sear_payloads = (
				sear_payloads
				and (
					_same_calls(exp.get("apply_anti_heal_calls", []), [[0.50, AURA_DURATION]])
					and _same_calls(exp.get("apply_burn_calls", []), [[6.0, AURA_DURATION, 0]])
				)
			)
		else:
			burst_payloads = (
				burst_payloads
				and (_same_calls(exp.get("apply_burn_calls", []), [[22.0, 180.0, 0]]))
			)
	check.call(
		frost_payloads, "Freezing Aura delivers atk_slow 0.30/30 and anti_heal 0.40/30 to the boss"
	)
	check.call(
		solar_payloads, "Scorched Earth delivers burn 28/30 in blue and blind 0.18/30 to the boss"
	)
	check.call(sear_payloads, "Cauterize delivers anti_heal 0.50/30 and burn 6/30 to the boss")
	check.call(burst_payloads, "Brand Burst delivers burn 22/180 to the boss in both columns")
	check.call(cross_columns, "both columns deliver the same raw aura payloads")


func _reset_world(world: ItemAuraWorld, pre_fix_mode: String) -> void:
	world.pre_fix_mode = pre_fix_mode
	world.last_aura_bus = null
	world.units.clear()
	world.projectiles.clear()
	world.recent_events.clear()
	if world.active_boss != null:
		world._by_id.erase(world.active_boss.id)
		world.active_boss = null
	world._by_id.clear()


func _spawn_case_units(world: ItemAuraWorld, boss_type: String) -> Array:
	var boss: BossState = world._spawn_boss(boss_type)
	if boss == null:
		return []
	boss.position = Vector2(200.0, 0.0)
	boss.previous_position = boss.position
	boss.entrance_timer = 0
	boss.timer = 0
	boss.atk_slow_amount = 0.0
	boss.atk_slow_timer = 0
	boss.anti_heal_amount = 0.0
	boss.anti_heal_timer = 0
	boss.burn_dps = 0.0
	boss.burn_timer = 0
	boss.burn_accum = 0.0
	boss.burn_tick_cd = BURN_TICK
	boss.burn_team = -1
	boss.blind_amount = 0.0
	boss.blind_timer = 0
	var hero: HeroState = world.spawn_hero(KAIZEN, world.BLUE, Vector2(0.0, 0.0))
	hero.max_hp = 10000.0
	hero.hp = 10000.0
	hero.alive = true
	hero.target_id = boss.id
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
	var far: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
	if far != null:
		far.position = Vector2(900.0, 0.0)
	return [boss, hero]


func _run_scenario(
	world: ItemAuraWorld, boss_type: String, scenario: String, pre_fix_mode: String
) -> Dictionary:
	_reset_world(world, pre_fix_mode)
	var spawned: Array = _spawn_case_units(world, boss_type)
	if spawned.is_empty():
		return {}
	var boss: BossState = spawned[0]
	var hero: HeroState = spawned[1]
	var before: Dictionary = {}
	var delivered: Dictionary = {}
	var burn_damage := 0
	var calls: ItemAuraBus = null

	if scenario == BURST_SCENARIO:
		# Set-up burn (identical in both columns) through the boss store, then
		# let it tick out: burn_timer 0, burn_accum 0, stale burn_tick_cd 23.
		boss.apply_debuff("burn", EXPIRED_BURN_DPS, EXPIRED_BURN_TICKS, world.BLUE)
		for _tick in range(EXPIRED_BURN_TICKS):
			boss.tick_tower_debuffs()
		before = {
			"burn_dps": boss.burn_dps,
			"burn_timer": boss.burn_timer,
			"burn_accum": boss.burn_accum,
			"burn_tick_cd": boss.burn_tick_cd,
		}
		# Searbrand Brand Burst item burn delivery onto the active boss
		# (`hero_item_inventory.gd`: `effects.apply_burn(eid, ...)`).
		calls = world._battle_item_effects(hero) as ItemAuraBus
		calls.apply_burn(boss.id, BRAND_BURST_DPS, BRAND_BURST_DURATION, world.BLUE)
		delivered = {
			"burn_dps": boss.burn_dps,
			"burn_timer": boss.burn_timer,
			"burn_accum": boss.burn_accum,
			"burn_tick_cd": boss.burn_tick_cd,
			"burn_team": boss.burn_team,
		}
		for _tick in range(BRAND_BURST_TICKS):
			burn_damage += boss.tick_tower_debuffs()
	else:
		var item_id: String = String(AURA_ITEM.get(scenario, ""))
		if item_id.is_empty() or not hero.items.add(item_id):
			return {}
		world._tick_auras_and_items()
		calls = world.last_aura_bus

	if calls == null:
		return {}
	return {
		"before_delivery": before,
		"after_delivery": delivered,
		"apply_atk_slow_calls": calls.atk_slow_calls,
		"apply_anti_heal_calls": calls.anti_heal_calls,
		"apply_burn_calls": calls.burn_calls,
		"boss_atk_slow_amount": boss.atk_slow_amount,
		"boss_atk_slow_timer": boss.atk_slow_timer,
		"boss_anti_heal_amount": boss.anti_heal_amount,
		"boss_anti_heal_timer": boss.anti_heal_timer,
		"boss_burn_dps": boss.burn_dps,
		"boss_burn_timer": boss.burn_timer,
		"boss_burn_team": boss.burn_team,
		"boss_burn_accum": boss.burn_accum,
		"boss_burn_tick_cd": boss.burn_tick_cd,
		"boss_blind_amount": boss.blind_amount,
		"boss_blind_timer": boss.blind_timer,
		"burn_damage_after_23_ticks": burn_damage,
	}


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == 864, "boss item aura fixture has 864 cases (216 bosses x 4)")
	var world := ItemAuraWorld.new()
	var burst_want := int(BRAND_BURST_DPS / 60.0 * BRAND_BURST_TICKS)
	for entry in cases:
		var boss_type: String = String(entry.get("boss_type", ""))
		var scenario: String = String(entry.get("scenario", ""))
		var exp: Dictionary = entry.get("expected", {})
		var without: Dictionary = entry.get("expected_without_boss_store", {})
		var pre_fix: String = String(entry.get("pre_fix_delivery", ""))
		var mode := (
			PRE_FIX_WORLD_STORE if pre_fix == PRE_FIX_WORLD_STORE else (PRE_FIX_BURN_FIELD_WRITE)
		)
		var actual := _run_scenario(world, boss_type, scenario, "")
		var contrast := _run_scenario(world, boss_type, scenario, mode)
		var label := "%s:%s" % [boss_type, scenario]
		check.call(_matches_row(actual, exp), "item aura expected parity %s" % label)
		check.call(_matches_row(contrast, without), "item aura pre-fix contrast parity %s" % label)
		check.call(
			_cross_column_ok(actual, contrast, scenario, burst_want),
			"item aura cross-column contrast %s" % label
		)


func _cross_column_ok(
	actual: Dictionary, contrast: Dictionary, scenario: String, burst_want: int
) -> bool:
	if scenario == FROST_SCENARIO:
		# 0.30/30 raw vs the tenacity-cut 0.15/15 on the boss.
		return (
			is_equal_approx(float(actual.get("boss_atk_slow_amount", 0.0)), 0.15)
			and int(actual.get("boss_atk_slow_timer", 0)) == 15
			and is_equal_approx(float(contrast.get("boss_atk_slow_amount", 0.0)), 0.30)
			and int(contrast.get("boss_atk_slow_timer", 0)) == 30
			and (
				float(actual.get("boss_atk_slow_amount", 0.0))
				< float(contrast.get("boss_atk_slow_amount", 0.0))
			)
			and (
				int(actual.get("boss_atk_slow_timer", 0))
				< int(contrast.get("boss_atk_slow_timer", 0))
			)
			and not (actual.get("apply_atk_slow_calls", []) as Array).is_empty()
			and is_equal_approx(float(actual.get("boss_anti_heal_amount", 0.0)), 0.40)
		)
	if scenario == SOLAR_SCENARIO:
		# Burn and blind land identically in both deliveries: only the Freezing
		# Aura atk_slow is a tenacity divergence, the burn clock is already
		# reset by the world store.
		return (
			is_equal_approx(float(actual.get("boss_burn_dps", 0.0)), 28.0)
			and int(actual.get("boss_burn_timer", 0)) == AURA_DURATION
			and int(actual.get("boss_burn_tick_cd", 0)) == BURN_TICK
			and int(contrast.get("boss_burn_tick_cd", 0)) == BURN_TICK
			and is_equal_approx(float(actual.get("boss_blind_amount", 0.0)), 0.18)
			and int(actual.get("boss_blind_timer", 0)) == AURA_DURATION
		)
	if scenario == SEAR_SCENARIO:
		return (
			is_equal_approx(float(actual.get("boss_anti_heal_amount", 0.0)), 0.50)
			and int(actual.get("boss_anti_heal_timer", 0)) == AURA_DURATION
			and is_equal_approx(float(contrast.get("boss_anti_heal_amount", 0.0)), 0.50)
			and is_equal_approx(float(actual.get("boss_burn_dps", 0.0)), 6.0)
			and int(actual.get("boss_burn_team", -2)) == 0
		)
	var actual_delivered: Dictionary = actual.get("after_delivery", {})
	var contrast_delivered: Dictionary = contrast.get("after_delivery", {})
	var burst_call: Array = [[BRAND_BURST_DPS, BRAND_BURST_DURATION, 0]]
	return (
		int(actual_delivered.get("burn_tick_cd", -1)) == BURN_TICK
		and int(contrast_delivered.get("burn_tick_cd", -1)) == BURN_TICK - EXPIRED_BURN_TICKS
		and int(actual.get("burn_damage_after_23_ticks", -1)) == 0
		and int(contrast.get("burn_damage_after_23_ticks", -1)) == burst_want
		and _same_calls(actual.get("apply_burn_calls", []), burst_call)
		and _same_calls(contrast.get("apply_burn_calls", []), burst_call)
		and burst_want > 0
	)


func _live_match_contrasts(check: Callable) -> void:
	for boss_type in ["gornak", "morgath"]:
		# 1. Everfrost Freezing Aura through the live _tick_auras_and_items()
		# path: the boss inside the 300 px radius takes the tenacity-cut
		# atk_slow, while a minion inside the same radius keeps the raw payload.
		var world := ItemAuraWorld.new()
		var boss: BossState = world._spawn_boss(boss_type)
		boss.position = Vector2(300.0, 380.0)
		boss.previous_position = boss.position
		boss.entrance_timer = 0
		boss.timer = 0
		var hero: HeroState = world.spawn_hero(KAIZEN, world.BLUE, Vector2(280.0, 380.0))
		hero.max_hp = 10000.0
		hero.hp = 10000.0
		hero.target_id = boss.id
		var minion: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
		minion.position = Vector2(570.0, 380.0)
		if not hero.items.add("everfrost_guard"):
			check.call(false, "%s Everfrost Guard equips" % boss_type)
			continue
		world._tick_auras_and_items()
		var aura_cd := boss.effective_attack_cooldown()
		check.call(
			(
				is_equal_approx(boss.atk_slow_amount, 0.15)
				and boss.atk_slow_timer == 15
				and is_equal_approx(boss.anti_heal_amount, 0.40)
				and boss.anti_heal_timer == AURA_DURATION
				and is_equal_approx(minion.atk_slow_amount, 0.30)
				and minion.atk_slow_timer == AURA_DURATION
				and aura_cd > boss.attack_cooldown
			),
			(
				(
					"%s Freezing Aura cuts the boss atk_slow to 0.15/15 "
					+ "(cooldown %d) and keeps the minion at 0.30/30"
				)
				% [boss_type, aura_cd]
			)
		)

		var bug_world := ItemAuraWorld.new()
		bug_world.pre_fix_mode = PRE_FIX_WORLD_STORE
		var bug_boss: BossState = bug_world._spawn_boss(boss_type)
		bug_boss.position = Vector2(300.0, 380.0)
		bug_boss.previous_position = bug_boss.position
		bug_boss.entrance_timer = 0
		bug_boss.timer = 0
		var bug_hero: HeroState = bug_world.spawn_hero(
			KAIZEN, bug_world.BLUE, Vector2(280.0, 380.0)
		)
		bug_hero.max_hp = 10000.0
		bug_hero.hp = 10000.0
		bug_hero.target_id = bug_boss.id
		bug_hero.items.add("everfrost_guard")
		bug_world._tick_auras_and_items()
		check.call(
			(
				is_equal_approx(bug_boss.atk_slow_amount, 0.30)
				and bug_boss.atk_slow_timer == AURA_DURATION
				and bug_boss.effective_attack_cooldown() > aura_cd
			),
			(
				"%s pre-8y world store kept the raw 0.30/30 aura atk_slow (cooldown %d)"
				% [boss_type, bug_boss.effective_attack_cooldown()]
			)
		)

		# 2. Solar Brand Scorched Earth: burn lands with the aura team, the
		# blind lands on the boss, and the burn clock ticks inside the boss step.
		var solar_world := ItemAuraWorld.new()
		var solar_boss: BossState = solar_world._spawn_boss(boss_type)
		solar_boss.position = Vector2(300.0, 380.0)
		solar_boss.previous_position = solar_boss.position
		solar_boss.entrance_timer = 0
		solar_boss.timer = 0
		var solar_hero: HeroState = solar_world.spawn_hero(
			KAIZEN, solar_world.BLUE, Vector2(280.0, 380.0)
		)
		solar_hero.max_hp = 10000.0
		solar_hero.hp = 10000.0
		solar_hero.target_id = solar_boss.id
		if not solar_hero.items.add("solar_brand"):
			check.call(false, "%s Solar Brand equips" % boss_type)
			continue
		solar_world._tick_auras_and_items()
		check.call(
			(
				solar_boss.burn_dps == 28.0
				and solar_boss.burn_timer == AURA_DURATION
				and solar_boss.burn_team == solar_world.BLUE
				and solar_boss.burn_tick_cd == BURN_TICK
				and solar_boss.blind_amount == 0.18
				and solar_boss.blind_timer == AURA_DURATION
			),
			"%s Scorched Earth burns 28 dps in blue and blinds 0.18/30" % boss_type
		)
		solar_world._step_active_boss()
		var burn_total := 0
		for _tick in range(BURN_TICK - 1):
			burn_total += solar_boss.tick_tower_debuffs()
		check.call(
			(
				solar_boss.burn_timer == AURA_DURATION - BURN_TICK
				and burn_total == int(28.0 / 60.0 * BURN_TICK)
			),
			"%s Scorched Earth burn ticks %d fire damage over 30 ticks" % [boss_type, burn_total]
		)

		# 3. Searbrand Cauterize: the boss keeps 50% of every heal.
		var sear_world := ItemAuraWorld.new()
		var sear_boss: BossState = sear_world._spawn_boss(boss_type)
		sear_boss.position = Vector2(300.0, 380.0)
		sear_boss.previous_position = sear_boss.position
		sear_boss.entrance_timer = 0
		sear_boss.timer = 0
		var sear_hero: HeroState = sear_world.spawn_hero(
			KAIZEN, sear_world.BLUE, Vector2(280.0, 380.0)
		)
		sear_hero.max_hp = 10000.0
		sear_hero.hp = 10000.0
		sear_hero.target_id = sear_boss.id
		if not sear_hero.items.add("searbrand"):
			check.call(false, "%s Searbrand equips" % boss_type)
			continue
		sear_world._tick_auras_and_items()
		sear_boss.hp = 1000.0
		sear_boss.set_hp_value(1100.0)
		check.call(
			(
				is_equal_approx(sear_boss.anti_heal_amount, 0.50)
				and sear_boss.anti_heal_timer == AURA_DURATION
				and is_equal_approx(sear_boss.burn_dps, 6.0)
				and is_equal_approx(sear_boss.hp, 1050.0)
			),
			(
				"%s Cauterize halves boss healing (1000 hp +100 heal -> %.1f)"
				% [boss_type, sear_boss.hp]
			)
		)
