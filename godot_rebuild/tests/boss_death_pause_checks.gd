extends RefCounted
## Source-backed boss-death pause gate: hit-stop priority, full freeze, and resume.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const FIXTURE := "res://tests/fixtures/boss_presentation_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary, "boss-death pause source fixture parses")
	if not fixture is Dictionary:
		return
	var source: Dictionary = fixture.get("death_pause", {})
	var expected := {
		"mini": int(source.get("mini_ticks", -1)), "true": int(source.get("true_ticks", -1))
	}
	check.call(
		Prototype.BOSS_DEATH_PAUSE_TICKS == expected,
		"native boss-death pause lengths match BossDeathAnimation source"
	)
	check.call(
		(
			bool(source.get("timer_decrements", false))
			and bool(source.get("ends_when_timer_reaches_zero", false))
			and bool(source.get("death_active_reads_active", false))
			and bool(source.get("updates_animation_before_return", false))
			and bool(source.get("returns_before_regular_gameplay", false))
			and bool(source.get("hit_stop_gate_precedes_death_gate", false))
		),
		"source pause gate/countdown contract is present"
	)
	_boss_case(check, "gornak", "mini", expected.mini)
	_boss_case(check, "abaddon", "true", int(expected["true"]))


func _boss_case(check: Callable, boss_type: String, boss_class: String, pause_ticks: int) -> void:
	var world := Prototype.new()
	check.call(world.setup_arena(), "boss-death pause world initializes: " + boss_class)
	world.set_ai_enabled(false)
	world.ai_hero_control_enabled = false
	var boss = world._spawn_boss(boss_type)
	var hero: HeroState = world.blue_hero()
	check.call(
		boss != null and hero != null and boss.boss_class == boss_class,
		"source-class boss spawns for death-pause check: " + boss_type
	)
	if boss == null or hero == null:
		return
	boss.entrance_timer = 0
	boss.hp = 1.0
	boss.alive = true
	boss.defeated = false
	hero.active_skill = "r"
	hero.active_skill_timer = 10
	check.call(
		world._deliver_hit(hero.id, world.BLUE, boss, 99999, "physical", boss.position),
		"boss death is produced through native damage resolution: " + boss_type
	)
	world._process_boss_result()
	check.call(
		world.active_boss == null and world.boss_death_pause_ticks == pause_ticks,
		"boss result arms the source-length gameplay pause: " + boss_type
	)
	var tick_before := world.tick_count
	var gold_before: Array = world.economy.gold.duplicate()
	var wave_before := world.wave_count
	var timer_before: int = world.scheduler.remaining_ticks
	world.hit_stop_state.trigger(0.04)
	world.hit_stop_state.activate_pending()
	for _frame in range(2):
		world.step_tick()
	check.call(
		(
			world.hit_stop_froze_last_step
			and world.boss_death_pause_ticks == pause_ticks
			and hero.active_skill_timer == 8
		),
		"hit-stop has precedence and leaves boss-death pause queued"
	)
	var skill_clock_at_death_gate: int = hero.active_skill_timer
	var remained_frozen := true
	for _frame in range(pause_ticks):
		world.step_tick()
		if not world.boss_death_froze_last_step:
			remained_frozen = false
	check.call(
		(
			remained_frozen
			and world.boss_death_pause_ticks == 0
			and world.tick_count == tick_before
			and world.economy.gold == gold_before
			and world.wave_count == wave_before
			and world.scheduler.remaining_ticks == timer_before
			and hero.active_skill_timer == skill_clock_at_death_gate
		),
		"boss-death phase freezes fixed simulation for its exact source duration: " + boss_type
	)
	world.step_tick()
	check.call(
		world.tick_count == tick_before + 1 and not world.boss_death_froze_last_step,
		"fixed simulation resumes on the callback after boss-death phase: " + boss_type
	)
