extends RefCounted
## Full playable-match route for the source boss-death simulation pause.

const Playable = preload("res://scenes/prototype/PrototypeMatch.tscn")
const HeroState = preload("res://scripts/combat/hero_state.gd")


func run(tree: SceneTree, check: Callable) -> void:
	var baseline_nodes := tree.get_node_count()
	var speed_runtime = tree.root.get_node("GameSpeed")
	var old_speed: float = speed_runtime.speed
	speed_runtime.speed = 1.0
	speed_runtime.reset_match_clock()
	var screen = Playable.instantiate()
	var session = screen.get_node("Simulation")
	session.set_physics_process(false)
	tree.root.add_child(screen)
	await tree.process_frame
	var world = session.world
	world.set_ai_enabled(false)
	world.ai_hero_control_enabled = false
	check.call(
		(
			bool(screen.level_intro_state().get("active", false))
			and bool(screen.arena.overlay_draw_summary().get("level_intro_active", false))
		),
		"playable match starts with active LevelIntroScreen state and view summary"
	)
	var space_key := InputEventKey.new()
	space_key.physical_keycode = KEY_SPACE
	space_key.pressed = true
	check.call(
		(
			screen._handle_keyboard_input(space_key)
			and not bool(screen.level_intro_state().get("active", true))
		),
		"playable match Space key skips LevelIntroScreen"
	)
	var hero: HeroState = world.blue_hero()
	var boss = world._spawn_boss("gornak")
	check.call(
		screen.name == "PrototypeMatch" and hero != null and boss != null,
		"playable match creates a live hero and mini-boss"
	)
	check.call(
		(
			bool(screen.boss_intro_state().get("active", false))
			and bool(screen.arena.overlay_draw_summary().get("boss_intro_active", false))
		),
		"playable boss spawn activates BossIntroCinematic state and view summary"
	)
	check.call(
		(
			screen._handle_keyboard_input(space_key)
			and not bool(screen.boss_intro_state().get("active", true))
		),
		"playable match Space key skips BossIntroCinematic"
	)
	if hero != null and boss != null:
		boss.entrance_timer = 0
		boss.hp = 1.0
		boss.alive = true
		boss.defeated = false
		var killed: bool = world._deliver_hit(
			hero.id, world.BLUE, boss, 99999, "physical", boss.position
		)
		world._process_boss_result()
		check.call(
			killed and world.active_boss == null and world.boss_death_pause_ticks == 60,
			"playable boss death arms the source 60-tick pause"
		)
		var tick_before: int = world.tick_count
		var gold_before: Array = world.economy.gold.duplicate()
		var wave_before: int = world.wave_count
		speed_runtime.speed = 0.5
		speed_runtime.reset_match_clock()
		session._physics_process(1.0 / 60.0)
		var pause_after_slow_tick: int = world.boss_death_pause_ticks
		session._physics_process(1.0 / 60.0)
		check.call(
			(
				pause_after_slow_tick == 59
				and world.boss_death_pause_ticks == pause_after_slow_tick
				and world.tick_count == tick_before
			),
			"playable death timer follows fixed ticks, not skipped half-speed callbacks"
		)
		speed_runtime.speed = 1.0
		speed_runtime.reset_match_clock()
		for _frame in range(59):
			session._physics_process(1.0 / 60.0)
		check.call(
			(
				world.tick_count == tick_before
				and world.boss_death_pause_ticks == 0
				and world.boss_death_froze_last_step
				and world.economy.gold == gold_before
				and world.wave_count == wave_before
			),
			"playable session holds economy and waves for 60 authoritative pause ticks"
		)
		session._physics_process(1.0 / 60.0)
		check.call(
			world.tick_count == tick_before + 1 and not world.boss_death_froze_last_step,
			"playable simulation resumes immediately after boss-death phase"
		)
		var accelerated_boss = world._spawn_boss("gornak")
		if accelerated_boss != null:
			accelerated_boss.entrance_timer = 0
			accelerated_boss.hp = 1.0
			accelerated_boss.alive = true
			accelerated_boss.defeated = false
			var second_kill: bool = world._deliver_hit(
				hero.id, world.BLUE, accelerated_boss, 99999, "physical", accelerated_boss.position
			)
			world._process_boss_result()
			var tick_before_fast_frame: int = world.tick_count
			speed_runtime.speed = 2.0
			speed_runtime.reset_match_clock()
			session._physics_process(1.0 / 60.0)
			check.call(
				(
					second_kill
					and world.tick_count == tick_before_fast_frame
					and world.boss_death_pause_ticks == 58
					and bool(screen.boss_death_state().get("death_active", false))
				),
				"playable double-speed callback consumes two gated fixed ticks"
			)
			speed_runtime.speed = 1.0
			speed_runtime.reset_match_clock()
			for _frame in range(58):
				session._physics_process(1.0 / 60.0)
		var true_boss = world._spawn_boss("abaddon")
		if true_boss != null:
			true_boss.entrance_timer = 0
			true_boss.hp = 1.0
			true_boss.alive = true
			true_boss.defeated = false
			world._deliver_hit(
				hero.id, world.BLUE, true_boss, 99999, "physical", true_boss.position
			)
			world._process_boss_result()
			for _frame in range(90):
				session._physics_process(1.0 / 60.0)
			check.call(
				(
					bool(screen.boss_death_state().get("celebration_active", false))
					and bool(
						screen.arena.overlay_draw_summary().get("boss_celebration_active", false)
					)
				),
				"playable true-boss defeat enters celebration overlay after 90-tick pause"
			)
			var esc_key := InputEventKey.new()
			esc_key.physical_keycode = KEY_ESCAPE
			esc_key.pressed = true
			check.call(
				(
					screen._handle_keyboard_input(esc_key)
					and not bool(screen.boss_death_state().get("celebration_active", true))
				),
				"playable Escape key skips active true-boss celebration"
			)
	screen.queue_free()
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
	check.call(tree.get_node_count() == baseline_nodes, "boss-death playable scene frees cleanly")
	speed_runtime.speed = old_speed
	speed_runtime.reset_match_clock()
