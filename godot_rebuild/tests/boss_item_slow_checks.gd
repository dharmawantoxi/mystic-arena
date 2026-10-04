# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8x native suite: the source item slow/root arms call the target
## method directly - `target.apply_slow(1.0, vr['root_duration'])` Vine Rod
## Entangle (`hero_items.py:2662`), `e.apply_slow(act['slow'],
## act['slow_duration'])` Everfrost Arctic Blast (`hero_items.py:2290-2291`) and
## `target.apply_slow(oa['slow'], oa['duration'])` plus
## `target.apply_debuff('atk_slow', ...)` Frostbound Frostbite
## (`hero_items.py:2594-2599`). `Boss.apply_slow`
## (`bosses/base_boss.py:528-538`) cuts magnitude and duration by tenacity 0.50
## (`min(0.35, ...)`, `int(duration * 0.5)`) and stores with the
## amount-greater-or-longer-refresh rule, so `BattleItemEffects.apply_slow` and
## `apply_atk_slow` delegate to `BossState` when the target implements them.

const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const VEX = preload("res://data/heroes/vex.tres")
const FIXTURE := "res://tests/fixtures/boss_item_slow_source.json"

const SOURCE_FLAGS := [
	"vine_rod_roots_with_full_slow",
	"vine_rod_cooldown_armed_before_root",
	"arctic_blast_slows_each_nearby_enemy",
	"arctic_blast_uses_hasattr_gate",
	"frostbite_slows_target",
	"frostbite_applies_atk_slow_and_anti_heal",
	"boss_apply_slow_cuts_by_tenacity",
	"boss_apply_slow_uses_amount_or_timer_store",
	"boss_apply_debuff_cuts_only_atk_slow"
]

const VINE_SCENARIOS := ["vine_rod_root_on_boss", "root_then_frostbite_store_rule"]

const EXPECTED_SLOW := {
	"vine_rod_root_on_boss": [0.35, 30],
	"everfrost_arctic_blast_on_boss": [0.225, 105],
	"frostbound_frostbite_on_boss": [0.14, 90],
	"root_then_frostbite_store_rule": [0.14, 90],
}
const EXPECTED_WITHOUT_TENACITY := {
	"vine_rod_root_on_boss": [1.0, 60],
	"everfrost_arctic_blast_on_boss": [0.45, 210],
	"frostbound_frostbite_on_boss": [0.28, 180],
	"root_then_frostbite_store_rule": [1.0, 180],
}


class ItemSlowBus:
	extends BattleItemEffects
	var ignore_boss_tenacity := false
	var slow_calls: Array = []
	var atk_slow_calls: Array = []
	var anti_heal_calls: Array = []

	func apply_slow(target_id: int, amount: float, duration: int) -> void:
		var t: Object = world.get_unit(target_id)
		if t is BossState:
			slow_calls.append([amount, duration])
			if ignore_boss_tenacity:
				# Pre-8x `BattleItemEffects.apply_slow`: raw max-wins write that
				# skipped the `Boss.apply_slow` tenacity cut and store rule.
				var boss := t as BossState
				boss.slow_amount = maxf(boss.slow_amount, amount)
				boss.slow_timer = maxi(boss.slow_timer, duration)
				return
		super.apply_slow(target_id, amount, duration)

	func apply_atk_slow(target_id: int, amount: float, duration: int) -> void:
		var t: Object = world.get_unit(target_id)
		if t is BossState:
			atk_slow_calls.append([amount, duration])
			if ignore_boss_tenacity:
				# Pre-8x: `world.apply_atk_slow` strongest-wins store, untempered.
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
		super.apply_anti_heal(target_id, amount, duration)


class ItemSlowWorld:
	extends Prototype
	var ignore_boss_tenacity := false

	func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
		var bus := ItemSlowBus.new()
		bus.world = self
		bus.dealer_id = source_hero.id
		bus.dealer_team = source_hero.team
		bus.dealer_pos = source_hero.position
		bus.ignore_boss_tenacity = ignore_boss_tenacity
		return bus


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var parsed: bool = fixture is Dictionary and fixture.has("source") and fixture.has("cases")
	if parsed:
		for flag in SOURCE_FLAGS:
			parsed = parsed and bool(fixture.source.get(flag, false))
	check.call(parsed, "boss item slow fixture parses with every source flag")
	if not fixture is Dictionary:
		return
	_check_source_meta(check, fixture)
	_replay_cases(check, fixture)
	_live_match_contrasts(check)


func _check_source_meta(check: Callable, fixture: Dictionary) -> void:
	var src: Dictionary = fixture.get("source", {})
	check.call(
		(
			is_equal_approx(float(src.get("vine_rod_root_magnitude", 0.0)), 1.0)
			and int(src.get("vine_rod_root_duration", 0)) == 60
			and int(src.get("vine_rod_cooldown", 0)) == 540
			and is_equal_approx(float(src.get("everfrost_slow", 0.0)), 0.45)
			and int(src.get("everfrost_slow_duration", 0)) == 210
			and is_equal_approx(float(src.get("everfrost_radius", 0.0)), 280.0)
			and int(src.get("everfrost_trigger_enemies", 0)) == 2
			and int(src.get("everfrost_cooldown", 0)) == 1440
			and is_equal_approx(float(src.get("frostbound_slow", 0.0)), 0.28)
			and is_equal_approx(float(src.get("frostbound_atk_slow", 0.0)), 0.28)
			and is_equal_approx(float(src.get("frostbound_anti_heal", 0.0)), 0.45)
			and int(src.get("frostbound_duration", 0)) == 180
			and int(fixture.get("boss_type_count", 0)) == 216
			and int(fixture.get("case_count", 0)) == 864
		),
		"source metadata records item slow payloads, cooldowns, and 864 boss cases"
	)


func _same_calls(actual: Variant, exp: Variant) -> bool:
	var left: Array = actual if actual is Array else []
	var right: Array = exp if exp is Array else []
	if left.size() != right.size():
		return false
	for index in range(left.size()):
		var a: Array = left[index]
		var b: Array = right[index]
		if a.size() != 2 or b.size() != 2:
			return false
		if not is_equal_approx(float(a[0]), float(b[0])) or int(a[1]) != int(b[1]):
			return false
	return true


func _matches_row(actual: Dictionary, exp: Dictionary) -> bool:
	return (
		_same_calls(actual.get("slow_calls", []), exp.get("slow_calls", []))
		and _same_calls(actual.get("atk_slow_calls", []), exp.get("atk_slow_calls", []))
		and _same_calls(actual.get("anti_heal_calls", []), exp.get("anti_heal_calls", []))
		and is_equal_approx(
			float(actual.get("boss_slow_amount", -1.0)), float(exp.get("boss_slow_amount", -2.0))
		)
		and int(actual.get("boss_slow_timer", -1)) == int(exp.get("boss_slow_timer", -2))
		and is_equal_approx(
			float(actual.get("boss_atk_slow_amount", -1.0)),
			float(exp.get("boss_atk_slow_amount", -2.0))
		)
		and int(actual.get("boss_atk_slow_timer", -1)) == int(exp.get("boss_atk_slow_timer", -2))
		and is_equal_approx(
			float(actual.get("boss_anti_heal_amount", -1.0)),
			float(exp.get("boss_anti_heal_amount", -2.0))
		)
		and int(actual.get("boss_anti_heal_timer", -1)) == int(exp.get("boss_anti_heal_timer", -2))
		and (
			int(actual.get("cooldowns", {}).get("vine_rod", -1))
			== int(exp.get("cooldowns", {}).get("vine_rod", -2))
		)
		and (
			int(actual.get("cooldowns", {}).get("everfrost_guard", -1))
			== int(exp.get("cooldowns", {}).get("everfrost_guard", -2))
		)
	)


func _run_single_scenario(
	world: ItemSlowWorld, boss_type: String, scenario: String, ignore_boss_tenacity: bool
) -> Dictionary:
	world.units.clear()
	world.projectiles.clear()
	world.recent_events.clear()
	world.ignore_boss_tenacity = ignore_boss_tenacity
	if world.active_boss != null:
		world._by_id.erase(world.active_boss.id)
		world.active_boss = null
	var boss: BossState = world._spawn_boss(boss_type)
	if boss == null:
		return {}
	boss.position = Vector2.ZERO
	boss.previous_position = boss.position
	boss.entrance_timer = 0
	boss.timer = 0
	boss.slow_amount = 0.0
	boss.slow_timer = 0
	boss.atk_slow_amount = 0.0
	boss.atk_slow_timer = 0
	boss.anti_heal_amount = 0.0
	boss.anti_heal_timer = 0

	var hero_def = VEX if scenario in VINE_SCENARIOS else KAIZEN
	var hero: HeroState = world.spawn_hero(hero_def, world.BLUE, Vector2(20.0, 0.0))
	hero.max_hp = 10000.0
	hero.hp = 10000.0
	hero.alive = true
	hero.target_id = boss.id
	if scenario == "everfrost_arctic_blast_on_boss":
		var extra: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
		extra.position = Vector2(30.0, 0.0)
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
	var opening_item := String(
		(
			{
				"vine_rod_root_on_boss": "vine_rod",
				"everfrost_arctic_blast_on_boss": "everfrost_guard",
				"frostbound_frostbite_on_boss": "frostbound_eye",
				"root_then_frostbite_store_rule": "vine_rod",
			}
			. get(scenario, "")
		)
	)
	if opening_item.is_empty() or not hero.items.add(opening_item):
		return {}

	var enemies: Array = world._hero_enemy_list()
	var bus: ItemSlowBus = world._battle_item_effects(hero) as ItemSlowBus
	if scenario == "everfrost_arctic_blast_on_boss":
		hero.items.tick_auto(1, enemies, bus, world._item_rng)
	elif scenario == "root_then_frostbite_store_rule":
		hero.items._on_hit_common(boss.id, 50, enemies, world._item_rng, bus)
		if not hero.items.add("frostbound_eye"):
			return {}
		hero.items._on_hit_common(boss.id, 50, enemies, world._item_rng, bus)
	else:
		hero.items._on_hit_common(boss.id, 50, enemies, world._item_rng, bus)

	return {
		"slow_calls": bus.slow_calls,
		"atk_slow_calls": bus.atk_slow_calls,
		"anti_heal_calls": bus.anti_heal_calls,
		"boss_slow_amount": boss.slow_amount,
		"boss_slow_timer": boss.slow_timer,
		"boss_atk_slow_amount": boss.atk_slow_amount,
		"boss_atk_slow_timer": boss.atk_slow_timer,
		"boss_anti_heal_amount": boss.anti_heal_amount,
		"boss_anti_heal_timer": boss.anti_heal_timer,
		"cooldowns":
		{
			"vine_rod": hero.items.vine_cd,
			"everfrost_guard": hero.items.arctic_cd,
		},
	}


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == 864, "boss item slow fixture has 864 cases (216 bosses x 4)")
	var world := ItemSlowWorld.new()
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		var scenario := String(entry.get("scenario", ""))
		var exp: Dictionary = entry.get("expected", {})
		var without_tenacity: Dictionary = entry.get("expected_without_boss_tenacity", {})
		var actual := _run_single_scenario(world, boss_type, scenario, false)
		var contrast := _run_single_scenario(world, boss_type, scenario, true)
		var label := "%s:%s" % [boss_type, scenario]
		check.call(_matches_row(actual, exp), "item slow expected parity %s" % label)
		check.call(
			_matches_row(contrast, without_tenacity), "item slow pre-fix contrast parity %s" % label
		)
		check.call(
			_cross_column_ok(actual, contrast, scenario),
			"item slow cross-column contrast %s" % label
		)


func _cross_column_ok(actual: Dictionary, contrast: Dictionary, scenario: String) -> bool:
	var want: Array = EXPECTED_SLOW.get(scenario, [])
	var want_raw: Array = EXPECTED_WITHOUT_TENACITY.get(scenario, [])
	if want.is_empty() or want_raw.is_empty():
		return false
	return (
		is_equal_approx(float(actual.get("boss_slow_amount", 0.0)), float(want[0]))
		and int(actual.get("boss_slow_timer", 0)) == int(want[1])
		and is_equal_approx(float(contrast.get("boss_slow_amount", 0.0)), float(want_raw[0]))
		and int(contrast.get("boss_slow_timer", 0)) == int(want_raw[1])
		and (
			float(actual.get("boss_slow_amount", 0.0))
			< float(contrast.get("boss_slow_amount", 0.0))
		)
		and int(actual.get("boss_slow_timer", 0)) < int(contrast.get("boss_slow_timer", 0))
		and not (actual.get("slow_calls", []) as Array).is_empty()
	)


func _live_match_contrasts(check: Callable) -> void:
	for boss_type in ["gornak", "morgath"]:
		var world := ItemSlowWorld.new()
		var boss: BossState = world._spawn_boss(boss_type)
		boss.position = Vector2(300.0, 380.0)
		boss.previous_position = boss.position
		boss.entrance_timer = 0
		boss.timer = 0
		var hero: HeroState = world.spawn_hero(VEX, world.BLUE, Vector2(280.0, 380.0))
		hero.max_hp = 10000.0
		hero.hp = 10000.0
		hero.target_id = boss.id
		world._tick_auras_and_items()
		# 1. Vine Rod root: 1.0/60 raw becomes 0.35/30 on the boss, while the
		# pre-8x bus froze it completely for 60 ticks.
		check.call(hero.items.add("vine_rod"), "%s Vine Rod equips" % boss_type)
		var bus: ItemSlowBus = world._battle_item_effects(hero) as ItemSlowBus
		hero.items._on_hit_common(boss.id, 50, world._hero_enemy_list(), world._item_rng, bus)
		var speed := boss.eff_speed()
		check.call(
			(
				hero.items.vine_cd == 540
				and boss.slow_amount == 0.35
				and boss.slow_timer == 30
				and speed > 0.0
				and is_equal_approx(speed, boss.speed_px_per_tick * 0.65)
			),
			(
				"%s Vine Rod Entangle roots the boss with tenacity (0.35/30, speed %.3f)"
				% [boss_type, speed]
			)
		)
		world._step_active_boss()
		check.call(
			boss.slow_timer == 29 and boss.slow_amount == 0.35,
			"%s root slow ticks down inside _step_active_boss()" % boss_type
		)

		var bug_world := ItemSlowWorld.new()
		bug_world.ignore_boss_tenacity = true
		var bug_boss: BossState = bug_world._spawn_boss(boss_type)
		bug_boss.position = Vector2(300.0, 380.0)
		bug_boss.previous_position = bug_boss.position
		bug_boss.entrance_timer = 0
		bug_boss.timer = 0
		var bug_hero: HeroState = bug_world.spawn_hero(VEX, bug_world.BLUE, Vector2(280.0, 380.0))
		bug_hero.max_hp = 10000.0
		bug_hero.hp = 10000.0
		bug_hero.target_id = bug_boss.id
		bug_hero.items.add("vine_rod")
		var bug_bus: ItemSlowBus = bug_world._battle_item_effects(bug_hero) as ItemSlowBus
		bug_hero.items._on_hit_common(
			bug_boss.id, 50, bug_world._hero_enemy_list(), bug_world._item_rng, bug_bus
		)
		check.call(
			(
				bug_boss.slow_amount == 1.0
				and bug_boss.slow_timer == 60
				and bug_boss.eff_speed() == 0.0
			),
			"%s pre-fix bus root froze the boss for the full 60 ticks" % boss_type
		)

		# 2. Frostbound Frostbite: slow and atk_slow both run tenacity, anti_heal
		# keeps the raw payload.
		var fb_bus: ItemSlowBus = world._battle_item_effects(hero) as ItemSlowBus
		boss.slow_amount = 0.0
		boss.slow_timer = 0
		if not hero.items.add("frostbound_eye"):
			check.call(false, "%s Frostbound Eye equips" % boss_type)
			continue
		hero.items._on_hit_common(boss.id, 50, world._hero_enemy_list(), world._item_rng, fb_bus)
		check.call(
			(
				is_equal_approx(boss.slow_amount, 0.14)
				and boss.slow_timer == 90
				and is_equal_approx(boss.atk_slow_amount, 0.14)
				and boss.atk_slow_timer == 90
				and is_equal_approx(boss.anti_heal_amount, 0.45)
				and boss.anti_heal_timer == 180
			),
			"%s Frostbite halves slow/atk_slow to 0.14/90 and keeps anti_heal 0.45/180" % boss_type
		)
		check.call(
			boss.effective_attack_cooldown() > boss.attack_cooldown,
			"%s Frostbite atk_slow lengthens the boss attack cooldown" % boss_type
		)

		# 3. Everfrost Arctic Blast through the live _tick_auras_and_items() path.
		var ef_world := ItemSlowWorld.new()
		var ef_boss: BossState = ef_world._spawn_boss(boss_type)
		ef_boss.position = Vector2(300.0, 380.0)
		ef_boss.previous_position = ef_boss.position
		ef_boss.entrance_timer = 0
		ef_boss.timer = 0
		var ef_hero: HeroState = ef_world.spawn_hero(KAIZEN, ef_world.BLUE, Vector2(280.0, 380.0))
		ef_hero.max_hp = 10000.0
		ef_hero.hp = 10000.0
		ef_hero.target_id = ef_boss.id
		var minion: UnitState = ef_world.spawn_unit(GOBLIN, ef_world.RED, 1)
		minion.position = Vector2(290.0, 380.0)
		if not ef_hero.items.add("everfrost_guard"):
			check.call(false, "%s Everfrost Guard equips" % boss_type)
			continue
		ef_world._tick_auras_and_items()
		check.call(
			(
				ef_hero.items.arctic_cd == 1440
				and is_equal_approx(ef_boss.slow_amount, 0.225)
				and ef_boss.slow_timer == 105
				and minion.slow_amount == 0.45
				and minion.slow_timer == 210
			),
			"%s Arctic Blast slows the boss 0.225/105 and the minion 0.45/210" % boss_type
		)
