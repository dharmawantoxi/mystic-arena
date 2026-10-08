extends RefCounted
## Exercises the source-mapped cast freeze through the real playable match scene.

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
	var foe: HeroState = null
	for unit in world.units:
		if unit is HeroState and unit.team == world.RED:
			foe = unit as HeroState
			break
	check.call(
		screen.name == "PrototypeMatch" and hero != null and foe != null,
		"playable match scene has the source-mapped Kaizen pair"
	)
	if hero != null and foe != null:
		foe.position = hero.position + Vector2(48, 0)
		var tick_before_cast: int = world.tick_count
		check.call(session.request_skill_r(hero.id), "playable UI command queues Kaizen R")
		session._physics_process(1.0 / 60.0)
		var tick_after_cast: int = world.tick_count
		var skill_clock_after_cast: int = hero.active_skill_timer
		check.call(
			(
				tick_after_cast == tick_before_cast + 1
				and world.hit_stop_state.is_active()
				and world.hit_stop_state.frames == 2
				and hero.r_cooldown > 0
			),
			"source R cast runs its action, then arms the global two-frame freeze"
		)
		speed_runtime.speed = 0.5
		speed_runtime.reset_match_clock()
		session._physics_process(1.0 / 60.0)
		session._physics_process(1.0 / 60.0)
		check.call(
			(
				world.tick_count == tick_after_cast
				and not world.hit_stop_state.is_active()
				and hero.active_skill_timer == skill_clock_after_cast - 2
			),
			"hit-stop bypasses 0.5x skipping while advancing the skill clock twice"
		)
		speed_runtime.speed = 1.0
		speed_runtime.reset_match_clock()
		session._physics_process(1.0 / 60.0)
		check.call(
			world.tick_count == tick_after_cast + 1,
			"playable match resumes on the first non-frozen physics callback"
		)

	screen.queue_free()
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
	check.call(tree.get_node_count() == baseline_nodes, "hit-stop playable scene frees cleanly")
	speed_runtime.speed = old_speed
	speed_runtime.reset_match_clock()
