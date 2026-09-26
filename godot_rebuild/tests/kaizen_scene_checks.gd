extends RefCounted
## Kaizen-1 prototype UI: spawn, inspect, Q command lifecycle.


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var world = session.world
	session.set_physics_process(false)
	world.defender_enabled = false
	var hero = world.blue_hero()
	check.call(hero != null and hero.alive and hero.level == 1, "prototype spawns Kaizen")
	session.selected_id = hero.id
	session.selected_slot_id = -1
	await _settle(tree)
	check.call(
		(
			screen.get_node("%SkillQButton").visible
			and screen.get_node("%SelectionLabel").text.contains("Kaizen")
			and screen.get_node("%SelectionLabel").text.contains("Q stack")
		),
		"hero inspection names Kaizen and Q"
	)
	check.call(screen.get_node("%SkillQButton").disabled, "Q stays gated without a target")
	check.call(
		screen.get_node("%SkillWButton").visible and not screen.get_node("%SkillWButton").disabled,
		"W is ready without a target"
	)
	check.call(screen.get_node("%SkillEButton").disabled, "E stays gated without a target")
	check.call(screen.get_node("%SkillRButton").disabled, "R stays gated without a target")
	screen.get_node("%SkillQButton").pressed.emit()
	session._physics_process(1.0 / 60.0)
	check.call(
		hero.skill_timer == 0 and session.last_action.contains("tidak"),
		"empty-field Q fizzles without cooldown"
	)
	var foe = world.spawn_unit(world.MINIONS["goblin"], 1, 1)
	foe.position = hero.position + Vector2(40, 0)
	foe.hp = 100000.0
	foe.waypoint_index = 8
	session.selected_id = hero.id
	await _settle(tree)
	check.call(not screen.get_node("%SkillQButton").disabled, "Q enables with a target")
	check.call(not screen.get_node("%SkillEButton").disabled, "E enables with a target")
	check.call(not screen.get_node("%SkillRButton").disabled, "R enables with a target")
	screen.get_node("%SkillQButton").pressed.emit()
	screen.get_node("%SkillQButton").pressed.emit()
	check.call(
		session.command.kind == "skill_q" and session.command.id == hero.id,
		"Q click captures hero ID once"
	)
	session._physics_process(1.0 / 60.0)
	check.call(
		(
			hero.skill_timer == hero.skill_cd_max - 1
			and hero.q_stack == 1
			and session.last_action.contains("Steel Wind")
		),
		"queued Q casts once"
	)
	await _settle(tree)
	check.call(
		(
			screen.get_node("%SkillQButton").disabled
			and screen.get_node("%SkillQButton").text.contains("CD")
		),
		"cooldown presented on Q button"
	)
	session.request_skill_q(hero.id)
	screen.pause_match()
	check.call(
		session.command.is_empty() and not session.request_skill_q(hero.id), "pause cancels Q"
	)
	screen.resume_match()
	app._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check.call(session.command.is_empty() and tree.paused, "focus cancels Q")
	screen.resume_match()
	var dest: Vector2 = hero.position + Vector2(40, 0)
	check.call(session.request_hero_move(hero.id, dest), "move queues")
	session.request_hero_move(hero.id, dest)
	check.call(
		session.command.kind == "move" and session.command.point == dest, "move captures point once"
	)
	session._physics_process(1.0 / 60.0)
	check.call(
		hero.has_destination and session.last_action.contains("titik"),
		"queued move sets destination"
	)
	screen.pause_match()
	check.call(
		session.command.is_empty() and not session.request_hero_move(hero.id, dest),
		"pause cancels move"
	)
	screen.resume_match()
	if foe == null or not foe.alive or world.get_unit(foe.id) == null:
		foe = world.spawn_unit(world.MINIONS["goblin"], 1, 1)
	foe.alive = true
	foe.hp = 100000.0
	foe.waypoint_index = 8
	foe.position = hero.position + Vector2(80, 0)
	session.selected_id = hero.id
	check.call(session.request_hero_follow(hero.id, foe.id), "follow queues")
	session.request_hero_follow(hero.id, foe.id)
	check.call(
		session.command.kind == "follow" and session.command.target_id == foe.id,
		"follow captures once"
	)
	session._physics_process(1.0 / 60.0)
	check.call(
		(
			hero.follow_id == foe.id
			and not hero.has_destination
			and session.last_action.contains("mengikuti")
		),
		"queued follow replaces destination"
	)
	hero.w_cooldown = 0
	screen.get_node("%SkillWButton").pressed.emit()
	session._physics_process(1.0 / 60.0)
	check.call(
		hero.wind_wall_timer > 0 and session.last_action.contains("Wind Wall"),
		"queued W raises the wall"
	)
	if world.get_unit(foe.id) == null:
		foe = world.spawn_unit(world.MINIONS["goblin"], 1, 1)
	foe.alive = true
	foe.hp = 100000.0
	foe.waypoint_index = 8
	foe.position = hero.position + Vector2(40, 0)
	hero.e_cooldown = 0
	session.selected_id = hero.id
	screen.get_node("%SkillEButton").pressed.emit()
	session._physics_process(1.0 / 60.0)
	check.call(hero.e_cooldown > 0 and session.last_action.contains("Sweep"), "queued E sweeps")
	if world.get_unit(foe.id) == null:
		foe = world.spawn_unit(world.MINIONS["goblin"], 1, 1)
	foe.alive = true
	foe.hp = 100000.0
	foe.waypoint_index = 8
	foe.position = hero.position + Vector2(40, 0)
	hero.r_cooldown = 0
	session.selected_id = hero.id
	screen.get_node("%SkillRButton").pressed.emit()
	session._physics_process(1.0 / 60.0)
	check.call(hero.ulti_active and session.last_action.contains("Tornado"), "queued R tornados")
	await _settle(tree)
	session.selected_id = hero.id
	check.call(not screen.get_node("%HeroUpgradeButton").disabled, "hero upgrade offered")
	screen.get_node("%HeroUpgradeButton").pressed.emit()
	session._physics_process(1.0 / 60.0)
	check.call(
		hero.level == 2 and world.economy.gold[0] == 700 and session.last_action.contains("naik"),
		"queued hero upgrade spends once"
	)
	world.winner = 1
	await _settle(tree)
	check.call(
		screen.get_node("%SkillQButton").disabled and not session.request_skill_q(hero.id),
		"result disables Q"
	)
	var old_id: int = screen.get_instance_id()
	screen.get_node("%RestartButton").pressed.emit()
	await _settle(tree)
	check.call(not is_instance_id_valid(old_id) and not tree.paused, "hero scene disposed")
	world = app.current_screen.simulation.world
	check.call(
		world.blue_hero() != null and world.blue_hero().skill_timer == 0,
		"restart respawns a fresh Kaizen"
	)
	app.show_menu()
	await _settle(tree)
	check.call(tree.get_node_count() == baseline, "hero lifecycle clean")


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
