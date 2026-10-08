extends RefCounted
## End-to-end controller proof through the playable PrototypeMatch and App.

const TEST_PATH := "user://controller_scene_test.json"


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	_cleanup()
	app.current_screen.progress_path = TEST_PATH
	app.start_prototype(1, "normal")
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var world = session.world
	session.set_physics_process(false)
	world.set_ai_enabled(false)
	var cursor = screen.get_node("%ControllerCursor")
	check.call(
		cursor != null and not cursor.active, "Playable match authors controller cursor runtime"
	)

	_axis(cursor, JOY_AXIS_LEFT_X, 0.5)
	cursor.advance_frame()
	check.call(cursor.active, "First gamepad axis lazily activates controller mode")
	check.call(
		cursor.cursor_position.x > 640.0 and is_equal_approx(cursor.cursor_position.y, 360.0),
		"Playable virtual cursor uses source acceleration"
	)

	var hero = world.player_roster()[0]
	session.selected_id = hero.id
	session.selected_slot_id = -1
	var destination := hero.position + Vector2(90, -65)
	cursor.cursor_position = screen.arena.get_global_transform_with_canvas() * destination
	_axis(cursor, JOY_AXIS_TRIGGER_RIGHT, 0.75)
	check.call(
		session.command.kind == "move" and session.command.id == hero.id,
		"RT routes cursor move through the fixed-tick session"
	)
	check.call(not hero.has_destination, "Controller move cannot mutate before fixed tick")
	session._physics_process(1.0 / 60.0)
	check.call(
		hero.has_destination and hero.destination.is_equal_approx(destination),
		"Fixed tick applies the exact controller cursor destination"
	)

	_button(cursor, JOY_BUTTON_X, true)
	check.call(
		session.command.kind == "skill_q" and session.command.id == hero.id,
		"X/Square routes source Q action through the session"
	)
	check.call(cursor.rumble_requests == 1, "Controller Q requests source-strength rumble")
	_button(cursor, JOY_BUTTON_X, false)
	session._physics_process(1.0 / 60.0)

	_axis(cursor, JOY_AXIS_TRIGGER_LEFT, 0.75)
	check.call(screen.hero_shop_panel.is_open, "LT opens the in-match Hero Shop")
	_button(cursor, JOY_BUTTON_B, true)
	check.call(not screen.hero_shop_panel.is_open, "B closes the modal controller stack first")
	_button(cursor, JOY_BUTTON_B, false)

	cursor.cursor_position = Vector2(400, 300)
	_button(cursor, JOY_BUTTON_DPAD_RIGHT, true)
	check.call(
		cursor.cursor_position == Vector2(500, 300),
		"Gameplay D-pad performs the source 100-pixel horizontal jump"
	)
	_button(cursor, JOY_BUTTON_DPAD_RIGHT, false)
	cursor.cursor_position = Vector2.ZERO
	_button(cursor, JOY_BUTTON_RIGHT_STICK, true)
	var snapped_button: Button = screen._controller_hover_button()
	check.call(
		(
			snapped_button != null
			and cursor.cursor_position == snapped_button.get_global_rect().get_center()
		),
		"R3 snaps and highlights the nearest live match control"
	)
	_button(cursor, JOY_BUTTON_RIGHT_STICK, false)

	_button(cursor, JOY_BUTTON_START, true)
	check.call(tree.paused and screen.pause_overlay.visible, "Start pauses the playable match")
	_button(cursor, JOY_BUTTON_START, false)
	_button(cursor, JOY_BUTTON_START, true)
	check.call(
		not tree.paused and not screen.pause_overlay.visible, "Start resumes from pause context"
	)
	_button(cursor, JOY_BUTTON_START, false)

	var old_screen_id: int = screen.get_instance_id()
	world.winner = world.BLUE
	screen._process(0.0)
	check.call(tree.paused and screen.result_shown, "Victory opens the controller result context")
	check.call(
		screen.get_node("%NextLevelButton").visible,
		"Victory result exposes the source next-level command"
	)
	_button(cursor, JOY_BUTTON_RIGHT_SHOULDER, true)
	await _settle(tree)
	check.call(not is_instance_id_valid(old_screen_id), "RB next-level frees the finished screen")
	check.call(
		(
			app.current_screen.name == "PrototypeMatch"
			and app.prototype_level == 2
			and app.current_screen.simulation.world.level_number == 2
		),
		"RB advances through App to the exact next level"
	)
	check.call(
		app.prototype_difficulty == "normal" and not app.current_screen.is_replay,
		"Next-level transition preserves difficulty and starts a fresh run"
	)
	check.call(not tree.paused, "Next-level controller transition clears global pause")

	screen = app.current_screen
	session = screen.simulation
	world = session.world
	session.set_physics_process(false)
	world.set_ai_enabled(false)
	world.winner = world.RED
	screen._process(0.0)
	cursor = screen.get_node("%ControllerCursor")
	_button(cursor, JOY_BUTTON_X, true)
	await _settle(tree)
	check.call(
		(
			app.current_screen.name == "PrototypeMatch"
			and app.prototype_level == 2
			and app.current_screen.is_replay
		),
		"X/Square defeat shortcut restarts the same level as a source replay"
	)
	check.call(not tree.paused, "Controller replay clears global pause")

	screen = app.current_screen
	session = screen.simulation
	world = session.world
	session.set_physics_process(false)
	world.set_ai_enabled(false)
	world.winner = world.RED
	screen._process(0.0)
	cursor = screen.get_node("%ControllerCursor")
	_button(cursor, JOY_BUTTON_BACK, true)
	await _settle(tree)
	check.call(app.current_screen.name == "MainMenu", "View/Share exits result to menu")
	check.call(not tree.paused, "Controller result-to-menu clears global pause")
	check.call(tree.get_node_count() == baseline, "Controller lifecycle leaves no orphan nodes")
	_cleanup()


func _button(cursor, button: JoyButton, pressed: bool) -> Array[String]:
	var event := InputEventJoypadButton.new()
	event.device = 0
	event.button_index = button
	event.pressed = pressed
	return cursor.dispatch_event(event)


func _axis(cursor, axis: JoyAxis, value: float) -> Array[String]:
	var event := InputEventJoypadMotion.new()
	event.device = 0
	event.axis = axis
	event.axis_value = value
	return cursor.dispatch_event(event)


func _cleanup() -> void:
	for suffix in ["", ".tmp", ".bak"]:
		var path := TEST_PATH + suffix
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
