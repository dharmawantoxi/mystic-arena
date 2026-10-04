# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8v native suite: `hero_items._apply_stun_to(target, duration)`
## (`hero_items.py:2681-2684`) delegates to `target.apply_stun(duration)` when
## the target implements `apply_stun`. `Boss` inherits
## `TowerDebuffMixin.apply_stun(duration)` (`_core.py:870-879`), which applies
## 55% boss stun resistance (`int(duration * 0.45)`) and stores the longest
## remaining duration on `boss.stun_timer`. `Boss.update`
## (`bosses/base_boss.py:595-600`) ticks `_tick_tower_debuffs()` and exits
## before entrance, enrage, true-boss heal, movement, basic attack, and
## smart/generic abilities while `boss.stun_timer > 0`.
## `BattleItemEffects.apply_stun` therefore delegates to `t.apply_stun(duration)`
## when `t` is `BossState`.

const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const VEX = preload("res://data/heroes/vex.tres")
const FIXTURE := "res://tests/fixtures/boss_item_stun_source.json"

const SOURCE_FLAGS := [
	"apply_stun_to_uses_getattr_apply_stun",
	"boss_apply_stun_scales_by_0_45",
	"boss_apply_stun_uses_max_timer",
	"boss_update_ticks_debuffs_before_stun_gate",
	"boss_update_stun_gate_returns_before_combat"
]


class ItemStunBus:
	extends BattleItemEffects
	var ignore_boss_stun := false

	func apply_stun(target_id: int, duration: int) -> void:
		if ignore_boss_stun:
			var t: Object = world.get_unit(target_id)
			if t is HeroState:
				(t as HeroState).stun_timer = maxi((t as HeroState).stun_timer, duration)
			return
		super.apply_stun(target_id, duration)


class ItemStunWorld:
	extends Prototype
	var ignore_boss_stun := false

	func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
		var bus := ItemStunBus.new()
		bus.world = self
		bus.dealer_id = source_hero.id
		bus.dealer_team = source_hero.team
		bus.dealer_pos = source_hero.position
		bus.ignore_boss_stun = ignore_boss_stun
		return bus


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var parsed: bool = fixture is Dictionary and fixture.has("source") and fixture.has("cases")
	if parsed:
		for flag in SOURCE_FLAGS:
			parsed = parsed and bool(fixture.source.get(flag, false))
	check.call(parsed, "boss item stun fixture parses with every source flag")
	if not fixture is Dictionary:
		return
	_check_source_meta(check, fixture)
	_replay_cases(check, fixture)
	_live_match_contrasts(check)


func _check_source_meta(check: Callable, fixture: Dictionary) -> void:
	var src: Dictionary = fixture.get("source", {})
	check.call(
		(
			int(src.get("sundering_cudgel_stun_ticks", 0)) == 15
			and int(src.get("sundering_cudgel_cooldown", 0)) == 120
			and int(src.get("abyss_breaker_bash_stun_ticks", 0)) == 54
			and int(src.get("abyss_breaker_bash_cooldown", 0)) == 140
			and int(src.get("abyss_breaker_overwhelm_stun_ticks", 0)) == 72
			and int(src.get("abyss_breaker_overwhelm_cooldown", 0)) == 1500
			and int(src.get("fenrir_chain_root_duration", 0)) == 72
			and int(src.get("fenrir_chain_cooldown", 0)) == 1080
			and int(src.get("hex_idol_stun_ticks", 0)) == 150
			and int(src.get("hex_idol_cooldown", 0)) == 1800
			and int(fixture.get("boss_type_count", 0)) == 216
			and int(fixture.get("case_count", 0)) == 864
		),
		"source metadata records item stun durations, cooldowns, and 864 boss cases"
	)


func _proc_seed_below(threshold: float) -> int:
	for seed_val in range(1, 128):
		var probe := RandomNumberGenerator.new()
		probe.seed = seed_val
		if probe.randf() < threshold:
			return seed_val
	return 1


func _run_single_scenario(
	world: ItemStunWorld, boss_type: String, scenario: String, ignore_boss_stun: bool
) -> Dictionary:
	world.units.clear()
	world.projectiles.clear()
	world.recent_events.clear()
	world.ignore_boss_stun = ignore_boss_stun
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

	var hero_def = VEX if scenario == "hex_idol_hexcraft" else KAIZEN
	var hero: HeroState = world.spawn_hero(hero_def, world.BLUE, Vector2(20.0, 0.0))
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
	var enemies: Array = world._hero_enemy_list()
	var bus: BattleItemEffects = world._battle_item_effects(hero)
	var item_cooldown := 0

	if scenario == "sundering_cudgel_pierce_bash":
		hero.items.add("sundering_cudgel")
		world._item_rng.seed = _proc_seed_below(0.28)
		hero.items.on_basic_attack_hit(boss.id, 50, enemies, world._item_rng, bus)
		item_cooldown = hero.items.pierce_bash_cd
	elif scenario == "abyss_breaker_bash":
		hero.items.add("abyss_breaker")
		world._item_rng.seed = _proc_seed_below(0.22)
		hero.items.on_basic_attack_hit(boss.id, 50, enemies, world._item_rng, bus)
		item_cooldown = hero.items.bash_cd
	elif scenario == "abyss_breaker_overwhelm":
		hero.items.add("abyss_breaker")
		hero.items.tick_auto(1, enemies, bus, world._item_rng)
		item_cooldown = hero.items.overwhelm_cd
	elif scenario == "hex_idol_hexcraft":
		hero.items.add("hex_idol")
		hero.items.tick_auto(1, enemies, bus, world._item_rng)
		item_cooldown = hero.items.hex_cd

	# Keep boss HP at 25% max_hp after any on-hit proc bonus damage so the
	# subsequent _step_active_boss() starts from the exact 25% HP threshold.
	boss.hp = float(int(float(boss.max_hp) * 0.25))
	var stun_on_apply := boss.stun_timer

	world._step_active_boss()
	var stun_after_step := boss.stun_timer
	var boss_enraged := boss.is_enraged
	var boss_basic_attack_fired := boss.basic_attack_seq > 0
	var boss_timer_after := boss.timer
	var boss_ability2_timer_after := boss.ability2_timer

	if stun_after_step > 0:
		for _tick in range(stun_after_step):
			world._step_active_boss()
	var stun_on_resume := boss.stun_timer
	var boss_enraged_on_resume := boss.is_enraged
	var boss_basic_attack_fired_on_resume := boss.basic_attack_seq > 0
	var boss_timer_on_resume := boss.timer
	var boss_ability2_timer_on_resume := boss.ability2_timer

	return {
		"stun_on_apply": stun_on_apply,
		"item_cooldown": item_cooldown,
		"stun_after_step": stun_after_step,
		"boss_enraged": boss_enraged,
		"boss_basic_attack_fired": boss_basic_attack_fired,
		"boss_timer_after": boss_timer_after,
		"boss_ability2_timer_after": boss_ability2_timer_after,
		"stun_on_resume": stun_on_resume,
		"boss_enraged_on_resume": boss_enraged_on_resume,
		"boss_basic_attack_fired_on_resume": boss_basic_attack_fired_on_resume,
		"boss_timer_on_resume": boss_timer_on_resume,
		"boss_ability2_timer_on_resume": boss_ability2_timer_on_resume
	}


func _matches_row(actual: Dictionary, exp: Dictionary) -> bool:
	return (
		int(actual.get("stun_on_apply", -1)) == int(exp.get("stun_on_apply", -2))
		and int(actual.get("item_cooldown", -1)) == int(exp.get("item_cooldown", -2))
		and int(actual.get("stun_after_step", -1)) == int(exp.get("stun_after_step", -2))
		and bool(actual.get("boss_enraged", true)) == bool(exp.get("boss_enraged", false))
		and (
			bool(actual.get("boss_basic_attack_fired", true))
			== bool(exp.get("boss_basic_attack_fired", false))
		)
		and int(actual.get("boss_timer_after", -1)) == int(exp.get("boss_timer_after", -2))
		and (
			int(actual.get("boss_ability2_timer_after", -1))
			== int(exp.get("boss_ability2_timer_after", -2))
		)
		and int(actual.get("stun_on_resume", -1)) == int(exp.get("stun_on_resume", -2))
		and (
			bool(actual.get("boss_enraged_on_resume", false))
			== bool(exp.get("boss_enraged_on_resume", true))
		)
		and (
			bool(actual.get("boss_basic_attack_fired_on_resume", false))
			== bool(exp.get("boss_basic_attack_fired_on_resume", true))
		)
		and int(actual.get("boss_timer_on_resume", -1)) == int(exp.get("boss_timer_on_resume", -2))
		and (
			int(actual.get("boss_ability2_timer_on_resume", -1))
			== int(exp.get("boss_ability2_timer_on_resume", -2))
		)
	)


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == 864, "boss item stun fixture has 864 cases (216 bosses x 4)")
	var world := ItemStunWorld.new()
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		var boss_class := String(entry.get("boss_class", ""))
		var scenario := String(entry.get("scenario", ""))
		var exp: Dictionary = entry.get("expected", {})
		var without_stun: Dictionary = entry.get("expected_without_boss_stun", {})
		var actual := _run_single_scenario(world, boss_type, scenario, false)
		var contrast := _run_single_scenario(world, boss_type, scenario, true)
		var label := "%s:%s" % [boss_type, scenario]
		check.call(_matches_row(actual, exp), "item stun expected parity %s" % label)
		check.call(
			_matches_row(contrast, without_stun), "item stun pre-fix contrast parity %s" % label
		)
		check.call(
			(
				int(actual.get("stun_on_apply", 0)) > 0
				and int(contrast.get("stun_on_apply", -1)) == 0
				and not bool(actual.get("boss_basic_attack_fired", true))
				and bool(contrast.get("boss_basic_attack_fired", false))
				and int(actual.get("boss_timer_after", -1)) == 0
				and int(contrast.get("boss_timer_after", 0)) > 0
				and (
					boss_class != "true"
					or (
						int(actual.get("boss_ability2_timer_after", -1)) == 0
						and int(contrast.get("boss_ability2_timer_after", 0)) > 0
					)
				)
			),
			"item stun cross-column contrast %s" % label
		)


func _live_match_contrasts(check: Callable) -> void:
	for boss_type in ["gornak", "morgath"]:
		# 1. Fenrir Chain Binding Chains (2+ enemies within 220px): 72 raw -> 32 boss stun.
		var world := ItemStunWorld.new()
		var boss: BossState = world._spawn_boss(boss_type)
		boss.position = Vector2(200.0, 200.0)
		boss.previous_position = boss.position
		boss.entrance_timer = 0
		boss.timer = 0
		var extra: UnitState = world.spawn_unit(GOBLIN, world.RED, 1)
		extra.position = Vector2(240.0, 200.0)
		var hero: HeroState = world.spawn_hero(KAIZEN, world.BLUE, Vector2(180.0, 200.0))
		hero.target_id = boss.id
		check.call(
			hero.items.add("fenrir_chain"), "Fenrir Chain equips for %s stun check" % boss_type
		)
		world._tick_hero_items(hero)
		check.call(
			boss.stun_timer == 32 and hero.items.chains_cd == 1080,
			"%s Fenrir Chain Binding Chains applies 32-tick stun (72 * 0.45)" % boss_type
		)
		world._step_active_boss()
		check.call(
			boss.stun_timer == 31 and boss.basic_attack_seq == 0 and boss.timer == 0,
			"%s Fenrir Chain stun gates _step_active_boss()" % boss_type
		)

		# 2. Stacking rule via BattleItemEffects.apply_stun: max duration wins.
		var stack_bus: BattleItemEffects = world._battle_item_effects(hero)
		boss.stun_timer = 10
		stack_bus.apply_stun(boss.id, 15)  # 15 * 0.45 = 6 < 10
		var kept_longer := boss.stun_timer == 10
		stack_bus.apply_stun(boss.id, 150)  # 150 * 0.45 = 67 > 10
		var took_stronger := boss.stun_timer == 67
		(
			check
			. call(
				kept_longer and took_stronger,
				(
					"%s BattleItemEffects.apply_stun preserves longer stun and upgrades to stronger stun"
					% boss_type
				)
			)
		)

		# 3. Live _tick_auras_and_items() + _step_active_boss() contrast with Abyss Breaker Overwhelm.
		var live_fixed := ItemStunWorld.new()
		live_fixed.ignore_boss_stun = false
		var b_fixed: BossState = live_fixed._spawn_boss(boss_type)
		b_fixed.position = Vector2(300.0, 380.0)
		b_fixed.previous_position = b_fixed.position
		b_fixed.entrance_timer = 0
		b_fixed.timer = 0
		var h_fixed: HeroState = live_fixed.spawn_hero(
			KAIZEN, live_fixed.BLUE, Vector2(280.0, 380.0)
		)
		h_fixed.max_hp = 10000.0
		h_fixed.hp = 10000.0
		h_fixed.target_id = b_fixed.id
		h_fixed.items.add("abyss_breaker")

		var live_bug := ItemStunWorld.new()
		live_bug.ignore_boss_stun = true
		var b_bug: BossState = live_bug._spawn_boss(boss_type)
		b_bug.position = Vector2(300.0, 380.0)
		b_bug.previous_position = b_bug.position
		b_bug.entrance_timer = 0
		b_bug.timer = 0
		var h_bug: HeroState = live_bug.spawn_hero(KAIZEN, live_bug.BLUE, Vector2(280.0, 380.0))
		h_bug.max_hp = 10000.0
		h_bug.hp = 10000.0
		h_bug.target_id = b_bug.id
		h_bug.items.add("abyss_breaker")

		live_fixed._tick_auras_and_items()
		live_bug._tick_auras_and_items()
		var after_t1_fixed := b_fixed.stun_timer
		var after_t1_bug := b_bug.stun_timer
		live_fixed._step_active_boss()
		live_bug._step_active_boss()
		(
			check
			. call(
				(
					after_t1_fixed == 32
					and after_t1_bug == 0
					and b_fixed.stun_timer == 31
					and b_fixed.basic_attack_seq == 0
					and b_bug.basic_attack_seq == 1
				),
				(
					"%s live _tick_auras_and_items() Abyss Breaker Overwhelm stuns boss and blocks basic attack"
					% boss_type
				)
			)
		)
