extends RefCounted
## End-to-end playable-scene proof for tactical panel, keyboard hold/release,
## ordered session transactions, feedback, and the world marker payload.


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var world = session.world
	session.set_physics_process(false)

	var panel = screen.get_node("%TacticalPanel")
	var gather: Button = screen.get_node("%GatherButton")
	var protect_tower: Button = screen.get_node("%ProtectTowerButton")
	var protect_castle: Button = screen.get_node("%ProtectCastleButton")
	var attack_boss: Button = screen.get_node("%AttackBossButton")
	var attack_dealer: Button = screen.get_node("%AttackDealerButton")
	check.call(
		(
			panel != null
			and gather != null
			and protect_tower != null
			and protect_castle != null
			and attack_boss != null
			and attack_dealer != null
		),
		"Playable match installs all five tactical hold buttons"
	)

	# A complete pointer tap may happen between physics ticks. Both edges must be
	# queued in order instead of the release being lost behind a single command.
	gather.button_down.emit()
	gather.button_up.emit()
	check.call(session.tactical_queue.size() == 2, "Tactical pointer tap queues press and release")
	check.call(
		world.tactical.active_command.is_empty(), "Tactical UI cannot mutate before fixed tick"
	)
	session._physics_process(1.0 / 60.0)
	check.call(
		session.tactical_queue.is_empty(), "Fixed tick drains tactical transactions atomically"
	)
	check.call(
		(
			world.tactical.active_command == "gather"
			and not world.tactical.hold_active()
			and world.tactical.command_timer == 599
		),
		"Same-frame pointer tap keeps normal command duration without sticky hold"
	)
	check.call(
		world.tactical.gather_point_active and world.tactical.gather_point_timer == 149,
		"Playable command publishes the source map-marker payload"
	)
	screen._process(0.0)
	check.call(
		(
			screen.get_node("%TacticalFeedback").visible
			and "GATHER" in screen.get_node("%TacticalFeedback").text
		),
		"Tactical feedback is visible in the playable HUD"
	)
	check.call(
		"GATHER" in screen.get_node("%TacticalStatus").text,
		"Tactical panel reflects active world state"
	)

	# Panel Protect Tower captures the selected blue tower ID, matching the
	# source side panel instead of resolving a mutable selection next tick.
	check.call(world.build_tower(world.BLUE, 0), "Tactical scene creates selected blue tower")
	var tower_id: int = world.slots[0].structure_id
	session.selected_id = tower_id
	protect_tower.button_down.emit()
	check.call(
		session.tactical_queue.back().target_id == tower_id,
		"Protect Tower press captures selected tower ID"
	)
	protect_tower.button_up.emit()
	session._physics_process(1.0 / 60.0)
	check.call(
		(
			world.tactical.active_command == "protect_tower"
			and world.tactical.command_target_id == tower_id
		),
		"Selected tower command executes through the fixed-tick session"
	)
	for tick in range(30):
		session._physics_process(1.0 / 60.0)

	# Long hold stays armed, then releases to the 30-tick source tail. The fixed
	# tick containing release consumes one tail tick, hence 29 here.
	protect_castle.button_down.emit()
	for tick in range(25):
		session._physics_process(1.0 / 60.0)
	check.call(
		world.tactical.held_command == "protect_castle" and world.tactical.hold_elapsed == 25,
		"Pointer button_down enforces a tactical command while held"
	)
	protect_castle.button_up.emit()
	session._physics_process(1.0 / 60.0)
	check.call(
		not world.tactical.hold_active() and world.tactical.command_timer == 29,
		"Pointer button_up ends long hold with source release tail"
	)

	# Keyboard G/F follows the arena cursor, while release is a true KEYUP edge.
	for tick in range(30):
		session._physics_process(1.0 / 60.0)
	session.set_tactical_cursor(Vector2(620, 330), true)
	var key_down := InputEventKey.new()
	key_down.physical_keycode = KEY_G
	key_down.pressed = true
	var key_up := InputEventKey.new()
	key_up.physical_keycode = KEY_G
	key_up.pressed = false
	check.call(screen._handle_keyboard_input(key_down), "Tactical G keydown is handled")
	check.call(
		(
			session.tactical_queue.back().name == "gather"
			and session.tactical_queue.back().follow_cursor
			and session.tactical_queue.back().has_point
		),
		"Keyboard Gather captures cursor-follow hold transaction"
	)
	check.call(screen._handle_keyboard_input(key_up), "Tactical G keyup is handled")
	session._physics_process(1.0 / 60.0)
	check.call(
		world.tactical.gather_point == Vector2(620, 330) and not world.tactical.hold_active(),
		"Keyboard tap uses cursor point and releases cleanly"
	)

	# Every source hotkey must route both edges to its exact command name.
	var hotkeys := {
		KEY_F: "gather",
		KEY_T: "protect_tower",
		KEY_C: "protect_castle",
		KEY_B: "attack_boss",
		KEY_D: "attack_damage_dealer",
	}
	for key: int in hotkeys:
		key_down = InputEventKey.new()
		key_down.physical_keycode = key
		key_down.pressed = true
		key_up = InputEventKey.new()
		key_up.physical_keycode = key
		key_up.pressed = false
		screen._handle_keyboard_input(key_down)
		check.call(
			(
				session.tactical_queue.back().name == hotkeys[key]
				and session.tactical_queue.back().kind == "start"
			),
			"Tactical hotkey %s queues exact press" % hotkeys[key]
		)
		screen._handle_keyboard_input(key_up)
		check.call(
			(
				session.tactical_queue.back().name == hotkeys[key]
				and session.tactical_queue.back().kind == "end"
			),
			"Tactical hotkey %s queues exact release" % hotkeys[key]
		)
	session._physics_process(1.0 / 60.0)
	check.call(
		not world.tactical.hold_active(), "Mixed hotkey releases cannot leave tactical hold stuck"
	)

	# Pause adds a release transaction even though physics is suspended; resume
	# drains it before the next simulation step.
	for tick in range(30):
		session._physics_process(1.0 / 60.0)
	attack_dealer.button_down.emit()
	session._physics_process(1.0 / 60.0)
	check.call(world.tactical.hold_active(), "Attack Dealer panel button enters hold state")
	screen.pause_match()
	check.call(
		tree.paused and not session.tactical_queue.is_empty(), "Pause queues tactical release"
	)
	screen.resume_match()
	session._physics_process(1.0 / 60.0)
	check.call(not world.tactical.hold_active(), "Resume drains pause-time tactical release")

	screen.get_node("%BackButton").pressed.emit()
	await _settle(tree)
	check.call(app.current_screen.name == "MainMenu", "Tactical scene exits cleanly")
	check.call(tree.get_node_count() == baseline, "Tactical scene leaves no orphan controls")


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
