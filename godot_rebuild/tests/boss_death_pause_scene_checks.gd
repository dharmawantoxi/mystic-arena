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
	var hero: HeroState = world.blue_hero()
	var boss = world._spawn_boss("gornak")
	check.call(
		screen.name == "PrototypeMatch" and hero != null and boss != null,
		"playable match creates a live hero and mini-boss"
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
				),
				"playable double-speed callback consumes two gated fixed ticks"
			)
	screen.queue_free()
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
	check.call(tree.get_node_count() == baseline_nodes, "boss-death playable scene frees cleanly")
	speed_runtime.speed = old_speed
	speed_runtime.reset_match_clock()
