extends SceneTree
## Native, dependency-free headless regression runner. Exit code 1 means failure.

const APP = preload("res://app/App.tscn")
const SIMULATION = preload("res://scripts/simulation/sandbox_simulation.gd")

var failures: Array[String] = []
var checks := 0


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		printerr("FAIL: " + message)


func _settle() -> void:
	await process_frame
	await process_frame
	await process_frame


func _physics_steps(count: int) -> void:
	for index in range(count):
		await physics_frame
	await process_frame


func _run() -> void:
	_check(Engine.physics_ticks_per_second == 60, "physics frequency is 60 Hz")
	_test_simulation()
	var app = APP.instantiate()
	root.add_child(app)
	await _settle()
	_check(app.current_screen.name == "MainMenu", "application boots into menu")
	var menu_child_count: int = app.current_screen.get_child_count()
	var menu_tree_count: int = root.get_tree().get_node_count()
	for cycle in range(10):
		app.current_screen.get_node("%PlayButton").pressed.emit()
		# Double activation in the same frame must not install two screens.
		app.current_screen.get_node("%PlayButton").pressed.emit()
		await _settle()
		_check(app.screen_root.get_child_count() == 1, "single match screen, cycle %d" % cycle)
		_check(app.current_screen.name == "Match", "play opens match, cycle %d" % cycle)
		var match_screen = app.current_screen
		var sim = match_screen.simulation
		sim.set_physics_process(false)
		_check(sim.probe_position == SIMULATION.SPAWN, "fresh probe position")
		_check(not sim.is_selected and not sim.has_move_target, "fresh input state")
		sim.select_at(sim.probe_position)
		_check(sim.command_move(Vector2(600, 400)), "selected marker accepts destination")
		sim.set_physics_process(true)
		var before: int = sim.tick_count
		await _physics_steps(4)
		_check(sim.tick_count > before, "physics advances while running")
		match_screen.get_node("%PauseButton").pressed.emit()
		_check(paused and match_screen.pause_overlay.visible, "pause shows overlay and stops tree")
		_check(not sim.has_move_target, "pause cancels pending movement")
		before = sim.tick_count
		await _physics_steps(4)
		_check(sim.tick_count == before, "physics does not advance during pause")
		match_screen.get_node("%ResumeButton").pressed.emit()
		_check(
			not paused and not match_screen.pause_overlay.visible, "resume clears overlay and pause"
		)
		await _physics_steps(4)
		_check(sim.tick_count > before, "physics resumes")
		# Background notification must have the same cleanup policy as manual pause.
		app.notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
		_check(paused, "focus loss pauses match")
		var old_id: int = match_screen.get_instance_id()
		var old_sim_id: int = sim.get_instance_id()
		match_screen.get_node("%RestartButton").pressed.emit()
		await _settle()
		_check(not paused, "restart clears global pause")
		_check(not is_instance_id_valid(old_id), "old match freed on restart")
		_check(not is_instance_id_valid(old_sim_id), "old simulation freed on restart")
		_check(
			app.current_screen.simulation.probe_position == SIMULATION.SPAWN,
			"restart resets movement"
		)
		_check(not app.current_screen.simulation.is_selected, "restart resets selection")
		_check(app.screen_root.get_child_count() == 1, "restart leaves one screen")
		app.current_screen.pause_match()
		old_id = app.current_screen.get_instance_id()
		app.current_screen.get_node("%MenuButton").pressed.emit()
		await _settle()
		_check(not paused, "return to menu unpauses tree")
		_check(not is_instance_id_valid(old_id), "match freed on return to menu")
		_check(app.current_screen.name == "MainMenu", "menu restored")
		_check(app.current_screen.get_child_count() == menu_child_count, "menu structure stable")
		_check(app.screen_root.get_child_count() == 1, "single menu instance")
		_check(
			root.get_tree().get_node_count() == menu_tree_count,
			"node count stable after full cycle"
		)
	await _test_input(app)
	app.queue_free()
	await _settle()
	_check(not paused, "app exit does not leave tree paused")
	if failures.is_empty():
		print(
			(
				"PASS: %d checks; fixed ticks, input, pause, lifecycle, 10 navigation/restart cycles."
				% checks
			)
		)
		quit(0)
	else:
		printerr("FAILED: %d of %d checks" % [failures.size(), checks])
		quit(1)


func _test_simulation() -> void:
	var first = SIMULATION.new()
	var second = SIMULATION.new()
	_check(not first.command_move(Vector2(400, 300)), "unselected probe rejects move")
	first.select_at(SIMULATION.SPAWN)
	_check(first.is_selected, "select within hit radius")
	_check(not first.command_move(Vector2(-10, -10)), "out of bounds move rejected")
	_check(first.command_move(SIMULATION.SPAWN + Vector2(30, 0)), "valid move accepted")
	for index in range(10):
		first.step_tick()
	_check(
		first.probe_position == SIMULATION.SPAWN + Vector2(30, 0),
		"3 pixels per tick, 10 ticks = 30 pixels"
	)
	_check(not first.has_move_target, "movement stops exactly at target")
	for index in range(590):
		first.step_tick()
	_check(first.tick_count == 600, "600 explicit steps are 600 ticks")
	_check(
		second.tick_count == 0 and second.probe_position == SIMULATION.SPAWN,
		"instances have independent state"
	)
	first.select_at(Vector2(1000, 400))
	_check(not first.is_selected, "click away deselects")
	first.free()
	second.free()


func _test_input(app: Node) -> void:
	app.start_match()
	await _settle()
	var match_screen = app.current_screen
	var sim = match_screen.simulation
	sim.set_physics_process(false)
	var click := InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = SIMULATION.SPAWN
	root.push_input(click, true)
	await _settle()
	_check(sim.is_selected, "viewport mouse input selects marker")
	click = InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_RIGHT
	click.pressed = true
	click.position = Vector2(600, 400)
	root.push_input(click, true)
	await _settle()
	_check(
		sim.has_move_target and sim.move_target == Vector2(600, 400),
		"viewport right click sends move command"
	)
	sim.cancel_pending_input()
	# A HUD panel consumes world clicks even when they are not on a button.
	click = InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = Vector2(500, 50)
	root.push_input(click, true)
	await _settle()
	_check(sim.is_selected, "HUD click does not deselect world marker")
	var key := InputEventKey.new()
	key.physical_keycode = KEY_ESCAPE
	key.pressed = true
	root.push_input(key, true)
	await _settle()
	_check(paused, "Escape pauses through real input routing")
	var tap := InputEventScreenTouch.new()
	tap.pressed = true
	tap.position = Vector2(700, 350)
	root.push_input(tap, true)
	await _settle()
	_check(not sim.has_move_target, "pause overlay prevents world commands")
	key = InputEventKey.new()
	key.physical_keycode = KEY_ESCAPE
	key.pressed = true
	root.push_input(key, true)
	await _settle()
	_check(not paused, "Escape resumes through real input routing")
	# Test native touch adapter without requiring physical touchscreen hardware.
	tap = InputEventScreenTouch.new()
	tap.pressed = true
	tap.position = Vector2(700, 350)
	match_screen._unhandled_input(tap)
	_check(
		sim.has_move_target and sim.move_target == tap.position,
		"touch dispatches selected marker movement"
	)
	sim.cancel_pending_input()
	click = InputEventMouseButton.new()
	click.device = InputEvent.DEVICE_ID_EMULATION
	click.button_index = MOUSE_BUTTON_RIGHT
	click.pressed = true
	click.position = Vector2(800, 400)
	match_screen._unhandled_input(click)
	_check(not sim.has_move_target, "synthetic mouse does not duplicate touch")
	app.show_menu()
	await _settle()
