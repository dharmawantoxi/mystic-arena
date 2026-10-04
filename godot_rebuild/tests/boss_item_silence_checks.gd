# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8w native suite: `hero_items._apply_silence_to(target, duration)`
## (`hero_items.py:2693-2697`) calls `target.apply_debuff('atk_slow', 1.0,
## duration)` and then `target.apply_debuff('skill_down', 1.0, duration)`.
## `Boss` overrides `apply_debuff` (`bosses/base_boss.py:540-552`): `atk_slow`
## is cut by boss tenacity 0.50 (`min(0.35, 1.0 * (1.0 - 0.50))` magnitude,
## `int(duration * 0.50)` ticks) before the `TowerDebuffMixin` strongest-wins
## store (`_core.py:918-947`), while `skill_down` keeps the full payload.
## `BattleItemEffects.apply_silence` therefore delegates to
## `t.apply_debuff("atk_slow"|"skill_down", ...)` when `t` is `BossState`.

const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const VEX = preload("res://data/heroes/vex.tres")
const FIXTURE := "res://tests/fixtures/boss_item_silence_source.json"

const SOURCE_FLAGS := [
	"silence_applies_atk_slow_then_skill_down",
	"silence_uses_apply_debuff_branch",
	"boss_debuff_cuts_atk_slow_by_tenacity",
	"boss_debuff_leaves_skill_down_untouched",
	"boss_debuff_delegates_to_mixin_store",
	"mixin_store_is_strongest_wins"
]

const ASTRAL_SCENARIOS := [
	"astral_codex_arcane_nova", "soul_rend_and_arcane_nova_keep_longest_store"
]


class ItemSilenceBus:
	extends BattleItemEffects
	var ignore_boss_tenacity := false
	var silence_calls: Array = []

	func apply_silence(target_id: int, duration: int) -> void:
		var t: Object = world.get_unit(target_id)
		silence_calls.append({"duration": duration, "is_boss": t is BossState})
		if ignore_boss_tenacity and t is BossState:
			# Pre-8w `BattleItemEffects.apply_silence`: raw field writes with
			# no boss tenacity on either debuff.
			var boss := t as BossState
			boss.atk_slow_amount = 1.0
			boss.atk_slow_timer = maxi(boss.atk_slow_timer, duration)
			boss.skill_down_amount = 1.0
			boss.skill_down_timer = maxi(boss.skill_down_timer, duration)
			return
		super.apply_silence(target_id, duration)


class ItemSilenceWorld:
	extends Prototype
	var ignore_boss_tenacity := false

	func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
		var bus := ItemSilenceBus.new()
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
	check.call(parsed, "boss item silence fixture parses with every source flag")
	if not fixture is Dictionary:
		return
	_check_source_meta(check, fixture)
	_replay_cases(check, fixture)
	_live_match_contrasts(check)


func _check_source_meta(check: Callable, fixture: Dictionary) -> void:
	var src: Dictionary = fixture.get("source", {})
	check.call(
		(
			int(src.get("sanguine_thorn_silence_duration", 0)) == 300
			and int(src.get("sanguine_thorn_cooldown", 0)) == 1080
			and is_equal_approx(float(src.get("sanguine_thorn_damage_amp", 0.0)), 0.3)
			and int(src.get("astral_codex_silence_duration", 0)) == 90
			and int(src.get("astral_codex_trigger_enemies", 0)) == 2
			and int(src.get("astral_codex_cooldown", 0)) == 1440
			and int(src.get("hex_idol_silence_ticks", 0)) == 150
			and int(src.get("hex_idol_stun_ticks", 0)) == 150
			and int(src.get("hex_idol_cooldown", 0)) == 1800
			and int(fixture.get("boss_type_count", 0)) == 216
			and int(fixture.get("case_count", 0)) == 864
		),
		"source metadata records item silence durations, cooldowns, and 864 boss cases"
	)


func _same_ints(left_value: Variant, right_value: Variant) -> bool:
	var left: Array = left_value if left_value is Array else []
	var right: Array = right_value if right_value is Array else []
	if left.size() != right.size():
		return false
	for index in range(left.size()):
		if int(left[index]) != int(right[index]):
			return false
	return true


func _same_cooldowns(actual: Variant, exp: Variant) -> bool:
	var left: Dictionary = actual if actual is Dictionary else {}
	var right: Dictionary = exp if exp is Dictionary else {}
	for key in ["sanguine_thorn", "astral_codex", "hex_idol"]:
		if int(left.get(key, -1)) != int(right.get(key, -2)):
			return false
	return true


func _run_single_scenario(
	world: ItemSilenceWorld, boss_type: String, scenario: String, ignore_boss_tenacity: bool
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
	boss.ability_timer = 0
	boss.ability2_timer = 0
	boss.enrage_triggered = false
	boss.is_enraged = false
	boss.hp = float(int(float(boss.max_hp) * 0.25))
	boss.atk_slow_amount = 0.0
	boss.atk_slow_timer = 0
	boss.skill_down_amount = 0.0
	boss.skill_down_timer = 0
	boss.stun_timer = 0

	# `astral_codex` and `hex_idol` are magic_only, so the source `add()` gate
	# (`HeroItems.is_magic_hero(hero_role)`) only accepts them on the Mage hero.
	var hero_def = VEX if scenario != "sanguine_thorn_soul_rend" else KAIZEN
	var hero: HeroState = world.spawn_hero(hero_def, world.BLUE, Vector2(20.0, 0.0))
	hero.max_hp = 10000.0
	hero.hp = 10000.0
	hero.alive = true
	hero.target_id = boss.id
	var extra: UnitState = null
	if scenario in ASTRAL_SCENARIOS:
		extra = world.spawn_unit(GOBLIN, world.RED, 1)
		extra.position = Vector2(60.0, 0.0)
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
	if scenario == "sanguine_thorn_soul_rend":
		hero.items.add("sanguine_thorn")
	elif scenario == "astral_codex_arcane_nova":
		hero.items.add("astral_codex")
	elif scenario == "hex_idol_hexcraft":
		hero.items.add("hex_idol")
	elif scenario == "soul_rend_and_arcane_nova_keep_longest_store":
		hero.items.add("sanguine_thorn")
		hero.items.add("astral_codex")
	else:
		return {}

	var enemies: Array = world._hero_enemy_list()
	var bus: ItemSilenceBus = world._battle_item_effects(hero) as ItemSilenceBus
	hero.items.tick_auto(1, enemies, bus, world._item_rng)

	var is_boss_call := false
	var durations: Array = []
	for entry in bus.silence_calls:
		durations.append(int(entry.get("duration", 0)))
		is_boss_call = is_boss_call or bool(entry.get("is_boss", false))

	return {
		"raw_silence_durations": durations,
		"boss_silenced": is_boss_call,
		"atk_slow_amount": boss.atk_slow_amount,
		"atk_slow_timer": boss.atk_slow_timer,
		"skill_down_amount": boss.skill_down_amount,
		"skill_down_timer": boss.skill_down_timer,
		"stun_timer": boss.stun_timer,
		"attack_cooldown_ticks": boss.effective_attack_cooldown(),
		"ability_damage_after": boss.eff_ability_damage(),
		"cooldowns":
		{
			"sanguine_thorn": hero.items.rend_cd,
			"astral_codex": hero.items.arcane_cd,
			"hex_idol": hero.items.hex_cd,
		},
	}


func _matches_row(actual: Dictionary, exp: Dictionary) -> bool:
	return (
		_same_ints(actual.get("raw_silence_durations", []), exp.get("raw_silence_durations", []))
		and bool(actual.get("boss_silenced", false)) == bool(exp.get("boss_silenced", true))
		and is_equal_approx(
			float(actual.get("atk_slow_amount", -1.0)), float(exp.get("atk_slow_amount", -2.0))
		)
		and int(actual.get("atk_slow_timer", -1)) == int(exp.get("atk_slow_timer", -2))
		and is_equal_approx(
			float(actual.get("skill_down_amount", -1.0)), float(exp.get("skill_down_amount", -2.0))
		)
		and int(actual.get("skill_down_timer", -1)) == int(exp.get("skill_down_timer", -2))
		and int(actual.get("stun_timer", -1)) == int(exp.get("stun_timer", -2))
		and (
			int(actual.get("attack_cooldown_ticks", -1))
			== int(exp.get("attack_cooldown_ticks", -2))
		)
		and int(actual.get("ability_damage_after", -1)) == int(exp.get("ability_damage_after", -2))
		and _same_cooldowns(actual.get("cooldowns", {}), exp.get("cooldowns", {}))
	)


func _cross_column_ok(actual: Dictionary, contrast: Dictionary) -> bool:
	var base_ok := (
		bool(actual.get("boss_silenced", false))
		and is_equal_approx(float(actual.get("atk_slow_amount", 0.0)), 0.35)
		and is_equal_approx(float(actual.get("skill_down_amount", 0.0)), 1.0)
		and is_equal_approx(float(contrast.get("atk_slow_amount", 0.0)), 1.0)
		and int(actual.get("atk_slow_timer", 0)) < int(contrast.get("atk_slow_timer", 0))
		and int(actual.get("stun_timer", 0)) == int(contrast.get("stun_timer", 0))
	)
	if not base_ok:
		return false
	# Hexcraft stuns the boss (layer 8v), so its attack cooldown sits at 9999 in
	# both columns; the other three scenarios compare the tenacity-scaled value.
	if int(actual.get("stun_timer", 0)) > 0:
		return (
			int(actual.get("attack_cooldown_ticks", -1))
			== int(contrast.get("attack_cooldown_ticks", -2))
		)
	return (
		int(actual.get("attack_cooldown_ticks", 0)) < int(contrast.get("attack_cooldown_ticks", 0))
	)


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == 864, "boss item silence fixture has 864 cases (216 bosses x 4)")
	var world := ItemSilenceWorld.new()
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		var scenario := String(entry.get("scenario", ""))
		var exp: Dictionary = entry.get("expected", {})
		var without_tenacity: Dictionary = entry.get("expected_without_boss_tenacity", {})
		var actual := _run_single_scenario(world, boss_type, scenario, false)
		var contrast := _run_single_scenario(world, boss_type, scenario, true)
		var label := "%s:%s" % [boss_type, scenario]
		check.call(_matches_row(actual, exp), "item silence expected parity %s" % label)
		check.call(
			_matches_row(contrast, without_tenacity),
			"item silence pre-fix contrast parity %s" % label
		)
		check.call(
			_cross_column_ok(actual, contrast), "item silence cross-column contrast %s" % label
		)


func _live_match_contrasts(check: Callable) -> void:
	for boss_type in ["gornak", "morgath"]:
		# 1. Live _tick_auras_and_items() + _step_active_boss() with Soul Rend.
		var live_fixed := ItemSilenceWorld.new()
		live_fixed.ignore_boss_tenacity = false
		var boss_fixed: BossState = live_fixed._spawn_boss(boss_type)
		boss_fixed.position = Vector2(300.0, 380.0)
		boss_fixed.previous_position = boss_fixed.position
		boss_fixed.entrance_timer = 0
		boss_fixed.timer = 0
		var hero_fixed: HeroState = live_fixed.spawn_hero(
			KAIZEN, live_fixed.BLUE, Vector2(280.0, 380.0)
		)
		hero_fixed.max_hp = 10000.0
		hero_fixed.hp = 10000.0
		hero_fixed.target_id = boss_fixed.id
		hero_fixed.items.add("sanguine_thorn")
		hero_fixed.items.set_hero_runtime(
			hero_fixed.id,
			hero_fixed.alive,
			hero_fixed.hp,
			int(hero_fixed.max_hp),
			hero_fixed.team,
			hero_fixed.facing,
			hero_fixed.position,
			hero_fixed.target_id
		)

		var live_bug := ItemSilenceWorld.new()
		live_bug.ignore_boss_tenacity = true
		var boss_bug: BossState = live_bug._spawn_boss(boss_type)
		boss_bug.position = Vector2(300.0, 380.0)
		boss_bug.previous_position = boss_bug.position
		boss_bug.entrance_timer = 0
		boss_bug.timer = 0
		var hero_bug: HeroState = live_bug.spawn_hero(KAIZEN, live_bug.BLUE, Vector2(280.0, 380.0))
		hero_bug.max_hp = 10000.0
		hero_bug.hp = 10000.0
		hero_bug.target_id = boss_bug.id
		hero_bug.items.add("sanguine_thorn")
		hero_bug.items.set_hero_runtime(
			hero_bug.id,
			hero_bug.alive,
			hero_bug.hp,
			int(hero_bug.max_hp),
			hero_bug.team,
			hero_bug.facing,
			hero_bug.position,
			hero_bug.target_id
		)

		live_fixed._tick_auras_and_items()
		live_bug._tick_auras_and_items()
		var fixed_after_item := (
			hero_fixed.items.rend_cd == 1080
			and boss_fixed.atk_slow_amount == 0.35
			and boss_fixed.atk_slow_timer == 150
			and boss_fixed.skill_down_amount == 1.0
			and boss_fixed.skill_down_timer == 300
			and boss_fixed.stun_timer == 0
		)
		var bug_after_item := (
			hero_bug.items.rend_cd == 1080
			and boss_bug.atk_slow_amount == 1.0
			and boss_bug.atk_slow_timer == 300
			and boss_bug.skill_down_amount == 1.0
			and boss_bug.skill_down_timer == 300
		)
		check.call(
			fixed_after_item and bug_after_item,
			(
				(
					"%s live Soul Rend silence keeps 0.35/150 on the boss while the pre-fix bus"
					% boss_type
				)
				+ " wrote 1.0/300"
			)
		)
		var fixed_cd: int = boss_fixed.effective_attack_cooldown()
		var bug_cd: int = boss_bug.effective_attack_cooldown()
		check.call(
			fixed_cd > boss_fixed.attack_cooldown and bug_cd >= fixed_cd * 10,
			(
				(
					"%s silenced boss attack cooldown keeps tenacity scaling (%d) instead of"
					% [boss_type, fixed_cd]
				)
				+ " the raw 1.0 slow (%d)" % bug_cd
			)
		)
		live_fixed._step_active_boss()
		check.call(
			boss_fixed.atk_slow_timer == 149 and boss_fixed.skill_down_timer == 299,
			"%s silence ticks down inside _step_active_boss()" % boss_type
		)

		# 2. Store rule via BattleItemEffects.apply_silence: equal amount with a
		# longer stored duration is kept, a longer payload still refreshes it.
		var stack_bus: ItemSilenceBus = (
			live_fixed._battle_item_effects(hero_fixed) as ItemSilenceBus
		)
		boss_fixed.atk_slow_amount = 0.35
		boss_fixed.atk_slow_timer = 400
		boss_fixed.skill_down_amount = 1.0
		boss_fixed.skill_down_timer = 400
		stack_bus.apply_silence(boss_fixed.id, 90)
		var kept_longer := (
			boss_fixed.atk_slow_amount == 0.35
			and boss_fixed.atk_slow_timer == 400
			and boss_fixed.skill_down_amount == 1.0
			and boss_fixed.skill_down_timer == 400
		)
		# Tenacity halves the 600-tick payload to 300 for atk_slow, so the stored
		# 400 is NOT shortened, while the uncut skill_down duration refreshes.
		stack_bus.apply_silence(boss_fixed.id, 600)
		var refreshed_raw := (
			boss_fixed.atk_slow_amount == 0.35
			and boss_fixed.atk_slow_timer == 400
			and boss_fixed.skill_down_amount == 1.0
			and boss_fixed.skill_down_timer == 600
		)
		check.call(
			kept_longer and refreshed_raw,
			(
				"%s BattleItemEffects.apply_silence keeps the longer atk_slow store and" % boss_type
				+ " refreshes skill_down with the uncut duration"
			)
		)

		# 3. Non-boss targets keep the raw payload (source minions/heroes do not
		# run `Boss.apply_debuff`).
		var extra: UnitState = live_fixed.spawn_unit(GOBLIN, live_fixed.RED, 1)
		extra.position = Vector2(320.0, 380.0)
		stack_bus.apply_silence(extra.id, 120)
		check.call(
			extra.atk_slow_amount == 1.0 and extra.atk_slow_timer == 120,
			"%s item silence on a minion keeps the raw 1.0/120 payload" % boss_type
		)
