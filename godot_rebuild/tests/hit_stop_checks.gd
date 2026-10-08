extends RefCounted
## Native checks for the source-global hit-stop state and fixed-tick freeze.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const Runtime = preload("res://scripts/match/hit_stop_runtime.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const FIXTURE := "res://tests/fixtures/hit_stop_source.json"


class HitStopProbe:
	extends RefCounted
	var requests: Array[float] = []

	func trigger(seconds: float) -> void:
		requests.append(seconds)


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary, "hit-stop source fixture parses")
	if not fixture is Dictionary:
		return
	var bus: Dictionary = fixture.get("bus", {})
	check.call(
		(
			is_equal_approx(Runtime.MIN_SECONDS, float(bus.get("min_seconds", -1)))
			and is_equal_approx(Runtime.MAX_SECONDS, float(bus.get("max_seconds", -1)))
			and is_equal_approx(Runtime.FIXED_DT, float(bus.get("fixed_dt", -1)))
			and Runtime.MAX_FRAMES == int(bus.get("max_frames", -1))
		),
		"native global bus limits match source"
	)
	check.call(
		Prototype.SOURCE_CAST_HIT_STOP_SECONDS == fixture.get("cast_triggers", {}),
		"native gameplay cast triggers match source FX-director events"
	)
	check.call(
		Prototype.SOURCE_DASH_HIT_STOP_SECONDS == fixture.get("dash_triggers", {}),
		"native dash triggers match source Kaizen on_dash edge"
	)
	var freeze: Dictionary = fixture.get("freeze_contract", {})
	check.call(
		(
			bool(freeze.get("checks_before_game_speed", false))
			and bool(freeze.get("uses_global_consumer", false))
			and bool(freeze.get("advances_active_skill_timer", false))
			and bool(freeze.get("advances_skill_cooldowns", false))
			and bool(freeze.get("ticks_tower_debuffs", false))
			and bool(freeze.get("updates_effects", false))
			and bool(freeze.get("returns_before_regular_simulation", false))
			and bool(freeze.get("reset_clears_shared_state", false))
		),
		"source freeze exception contract is present"
	)
	_runtime_cases(check, bus)
	_match_freeze_case(check)


func _runtime_cases(check: Callable, source: Dictionary) -> void:
	var lower := Runtime.new()
	lower.trigger(0.01)
	check.call(
		lower.pending_frames == int(source.get("low_clamp_frames", -1)) and not lower.is_active(),
		"short cast queues source-clamped frames for end of physics update"
	)
	lower.activate_pending()
	check.call(
		lower.frames == 2 and lower.total == 2, "pending request activates as one shared window"
	)
	lower.trigger(0.02)
	check.call(lower.frames == 2 and lower.total == 2, "weaker request does not stack or shorten")
	lower.trigger(0.08)
	check.call(
		(
			lower.frames == int(source.get("stronger_request_frames", -1))
			and lower.total == lower.frames
		),
		"stronger request replaces, rather than stacks, the active window"
	)
	var consumed: Array[bool] = []
	for _frame in range(lower.frames):
		consumed.append(lower.consume_frame())
	check.call(
		(
			consumed == source.get("consume_sequence", [])
			and lower.total == int(source.get("total_after_last_freeze", -1))
		),
		"source consumes exactly one global freeze per physics callback"
	)
	check.call(
		(
			not lower.consume_frame()
			and lower.total == int(source.get("total_after_empty_consume", -1))
		),
		"empty consume clears completed hit-stop total"
	)
	var tie := Runtime.new()
	tie.trigger(0.075)
	check.call(
		tie.pending_frames == int(source.get("half_tie_to_even_frames", -1)),
		"fixed-delta rounding matches Python ties-to-even"
	)
	var high := Runtime.new()
	high.trigger(0.08)
	check.call(high.pending_frames == Runtime.MAX_FRAMES, "maximum duration caps at five frames")
	high.clear()
	check.call(
		high.frames == 0 and high.total == 0 and high.pending_frames == 0,
		"match reset clears current and queued hit-stop"
	)


func _source_dash_case(check: Callable, world, hero: HeroState) -> void:
	var foe: HeroState = null
	for unit in world.units:
		if unit is HeroState and unit.team == world.RED:
			foe = unit as HeroState
			break
	check.call(foe != null, "Kaizen Q2 source trigger has an opposing hero target")
	if foe == null:
		return
	var old_hit_stop = world.hit_stop_state
	var probe := HitStopProbe.new()
	var old_hero_position: Vector2 = hero.position
	var old_foe_position: Vector2 = foe.position
	var old_foe_hp: float = foe.hp
	world.hit_stop_state = probe
	hero.position = Vector2(220, 540)
	foe.position = hero.position + Vector2(48, 0)
	hero.q_stack = 1
	hero.skill_timer = 0
	hero.target_id = -1
	hero.target_struct = null
	var cast := world.cast_hero_q(hero.id)
	check.call(
		cast and hero.is_dashing and probe.requests == [0.021, 0.027],
		"Kaizen Q2 queues source cast and dash-edge hit-stop requests"
	)
	world.hit_stop_state = old_hit_stop
	hero.position = old_hero_position
	foe.position = old_foe_position
	foe.hp = old_foe_hp
	hero.q_stack = 0
	hero.q_reset_timer = 0
	hero.skill_timer = 0
	hero.active_skill = ""
	hero.active_skill_timer = 0
	hero.is_dashing = false
	hero.dash_timer = 0
	hero.target_id = -1
	hero.target_struct = null


func _match_freeze_case(check: Callable) -> void:
	var world := Prototype.new()
	check.call(world.setup_arena(), "match initializes shared hit-stop state")
	world.set_ai_enabled(false)
	world.ai_hero_control_enabled = false
	var hero: HeroState = world.blue_hero()
	check.call(hero != null, "hit-stop match has player hero")
	if hero == null:
		return
	var source_no_stop_cast := world.cast_hero_w(hero.id)
	check.call(
		source_no_stop_cast and world.hit_stop_state.pending_frames == 0,
		"source Kaizen W cast does not request hit-stop"
	)
	_source_dash_case(check, world, hero)
	world.hit_stop_state.trigger(0.04)
	world.step_tick()
	world.activate_pending_hit_stop()
	var frozen_tick := world.tick_count
	var frozen_gold: Array = world.economy.gold.duplicate()
	var frozen_wave := world.wave_count
	var frozen_wave_timer := world.scheduler.remaining_ticks
	var frozen_position := hero.position
	hero.active_skill = "r"
	hero.active_skill_timer = 2
	hero.skill_timer = 4
	hero.w_cooldown = 6
	hero.e_cooldown = 7
	hero.r_cooldown = 8
	hero.stun_timer = 5
	hero.attack_timer = 9
	hero.slow_amount = 0.25
	hero.slow_timer = 4
	hero.dmg_amp_amount = 0.2
	hero.dmg_amp_timer = 4
	world.step_tick()
	check.call(
		(
			world.hit_stop_froze_last_step
			and world.tick_count == frozen_tick
			and world.economy.gold == frozen_gold
			and world.wave_count == frozen_wave
			and world.scheduler.remaining_ticks == frozen_wave_timer
			and hero.position == frozen_position
			and hero.active_skill == "r"
			and hero.active_skill_timer == 1
			and hero.skill_timer == 3
			and hero.w_cooldown == 5
			and hero.e_cooldown == 6
			and hero.r_cooldown == 7
			and hero.stun_timer == 4
			and hero.attack_timer == 9
			and hero.slow_timer == 3
			and hero.dmg_amp_timer == 3
		),
		"freeze holds gameplay while source-authorized hero clocks and debuffs advance"
	)
	world.step_tick()
	check.call(
		(
			world.hit_stop_froze_last_step
			and not world.hit_stop_state.is_active()
			and hero.active_skill_timer == 0
			and hero.active_skill.is_empty()
		),
		"last frozen frame finishes skill clock without advancing match tick"
	)
	check.call(world.tick_count == frozen_tick, "hit-stop never increments fixed match tick")
	world.step_tick()
	check.call(
		world.tick_count == frozen_tick + 1 and not world.hit_stop_froze_last_step,
		"fixed simulation resumes on the first callback after hit-stop"
	)
