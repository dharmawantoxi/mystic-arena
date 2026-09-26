extends SceneTree
## Native, dependency-free headless regression runner. Exit code 1 means failure.

const NexusSceneChecks = preload("res://tests/nexus_scene_checks.gd")
const NexusChecks = preload("res://tests/nexus_checks.gd")
const CannonChecks = preload("res://tests/cannon_checks.gd")
const UpgradeSceneChecks = preload("res://tests/upgrade_scene_checks.gd")
const UpgradeChecks = preload("res://tests/upgrade_checks.gd")
const PrototypeChecks = preload("res://tests/prototype_checks.gd")
const SiegeChecks = preload("res://tests/siege_checks.gd")
const CombatChecks = preload("res://tests/combat_checks.gd")
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
	CombatChecks.new().run(_check)
	SiegeChecks.new().run(_check)
	PrototypeChecks.new().run(_check)
	UpgradeChecks.new().run(_check)
	NexusChecks.new().run(_check)
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
	await _test_combat_scene(app)
	await _test_siege_scene(app)
	await _test_prototype_scene(app)
	await UpgradeSceneChecks.new().run(self, app, _check)
	await NexusSceneChecks.new().run(self, app, _check)
	app.queue_free()
	await _settle()
	_check(not paused, "app exit does not leave tree paused")
	if failures.is_empty():
		print(
			(
				"PASS: %d checks; fixed ticks, source parity, combat/siege/prototype, input and lifecycle."
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


func _test_combat_scene(app: Node) -> void:
	var baseline_count: int = get_node_count()
	for cycle in range(3):
		app.current_screen.get_node("%CombatButton").pressed.emit()
		await _settle()
		await _physics_steps(2)
		var screen = app.current_screen
		var session = screen.simulation
		_check(screen.name == "MinionArena", "combat menu opens new lab")
		_check(session.world.units.size() == 6, "initial wave contains both teams in three lanes")
		_check(session.request_wave(1), "valid wave request queued")
		_check(not session.request_wave(1), "same-frame duplicate wave rejected")
		_check(session.world.units.size() == 6, "UI command does not mutate world before physics")
		await _physics_steps(2)
		_check(session.world.units.size() == 12, "queued wave consumed once on physics tick")
		_check(session.request_wave(0), "second wave can be queued")
		screen.pause_match()
		var ticks: int = session.world.tick_count
		_check(session.pending_wave == -1, "pause cancels queued spawn")
		_check(not session.request_wave(0), "paused session rejects new spawn")
		await _physics_steps(3)
		_check(
			session.world.tick_count == ticks and session.world.units.size() == 12,
			"pause freezes minion movement, combat, regen, cooldown and wave"
		)
		screen.resume_match()
		screen.arena.process_mode = Node.PROCESS_MODE_DISABLED
		await _physics_steps(3)
		_check(session.world.tick_count > ticks, "simulation runs with visual processing disabled")
		screen.arena.process_mode = Node.PROCESS_MODE_PAUSABLE
		session.set_physics_process(false)
		var unit = session.world.units[0]
		var click := InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		click.position = screen.arena.get_global_transform_with_canvas() * unit.position
		root.push_input(click, true)
		await _settle()
		_check(session.selected_id == unit.id, "scaled arena input maps to correct world unit")
		click = InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		click.position = Vector2(500, 50)
		root.push_input(click, true)
		await _settle()
		_check(session.selected_id == unit.id, "combat HUD click does not clear selection")
		var old_id: int = screen.get_instance_id()
		screen.pause_match()
		screen.get_node("%RestartButton").pressed.emit()
		await _settle()
		await _physics_steps(2)
		_check(not is_instance_id_valid(old_id), "restart frees prior combat screen")
		_check(
			not paused and app.current_screen.name == "MinionArena",
			"restart keeps correct arena type"
		)
		_check(app.current_screen.simulation.world.wave_count == 1, "restart resets waves")
		_check(app.current_screen.simulation.world.kills == [0, 0], "restart resets kill state")
		app.current_screen.pause_match()
		app.current_screen.get_node("%MenuButton").pressed.emit()
		await _settle()
		_check(
			not paused and app.current_screen.name == "MainMenu",
			"combat exits cleanly while paused"
		)
		_check(get_node_count() == baseline_count, "combat navigation does not accumulate nodes")


func _test_siege_scene(app: Node) -> void:
	var baseline: int = get_node_count()
	for cycle in range(3):
		app.current_screen.get_node("%SiegeButton").pressed.emit()
		await _settle()
		await _physics_steps(2)
		var screen = app.current_screen
		var session = screen.simulation
		var world = session.world
		_check(screen.name == "SiegeArena", "new siege menu opens correct scene")
		_check(
			world.structures.size() == 8 and world.units.size() == 6,
			"siege starts six towers, two nexuses, and one two-team wave"
		)
		screen.get_node("%TeamMode").select(1)
		screen.get_node("%SpawnButton").pressed.emit()
		screen.get_node("%SpawnButton").pressed.emit()
		_check(
			session.pending_team_mode == 0 and world.units.size() == 6,
			"UI captures blue-team command without immediate world mutation"
		)
		await _physics_steps(2)
		_check(world.units.size() == 9, "blue-only UI wave spawns once")
		var tower = world.structures[0]
		var victim = world.units[3]
		victim.position = tower.position + Vector2(60, 0)
		tower.cooldown_ticks = 0
		_check(world.fire_projectile(tower.id, victim.id), "scene can launch projectile")
		var shot = world.projectiles[-1]
		var position: Vector2 = shot.position
		var ticks: int = world.tick_count
		_check(session.request_assault(0, 1), "red-only wave queues before pause")
		screen.pause_match()
		await _physics_steps(3)
		_check(
			world.tick_count == ticks and shot.position == position,
			"pause freezes projectiles and structure clocks"
		)
		_check(
			session.pending_wave == -1 and session.pending_team_mode == -1,
			"pause clears both queued type and team"
		)
		_check(not session.request_assault(0, 0), "paused siege rejects waves")
		screen.resume_match()
		screen.arena.process_mode = Node.PROCESS_MODE_DISABLED
		await _physics_steps(2)
		_check(world.tick_count > ticks, "siege does not depend on visual processing")
		screen.arena.process_mode = Node.PROCESS_MODE_PAUSABLE
		session.set_physics_process(false)
		var click := InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		click.position = screen.arena.get_global_transform_with_canvas() * tower.position
		root.push_input(click, true)
		await _settle()
		_check(session.selected_id == tower.id, "scaled structure selection works")
		var old_id: int = screen.get_instance_id()
		screen.pause_match()
		screen.get_node("%RestartButton").pressed.emit()
		await _settle()
		await _physics_steps(2)
		_check(not is_instance_id_valid(old_id), "restart disposes siege scene")
		screen = app.current_screen
		session = screen.simulation
		world = session.world
		_check(not paused and screen.name == "SiegeArena", "restart retains siege mode")
		_check(
			world.is_running() and world.wave_count == 1 and world.structures.size() == 8,
			"restart resets structures, wave count and result"
		)
		_check(
			world.projectiles.is_empty() and world.credited_gold == [0, 0],
			"restart leaves no old projectiles or credit"
		)
		# Finish via a real minion hit against a deliberately weakened test nexus.
		var nexus = world.nexuses[1]
		nexus.shield_active = false
		nexus.shield = 0
		nexus.hp = 1
		var attacker = world.spawn_unit(session.DEFINITIONS[0], 0, 1)
		attacker.position = nexus.position - Vector2(20, 0)
		await _physics_steps(2)
		await _settle()
		_check(
			world.winner == 0 and screen.get_node("%ArenaTitle").text == "BIRU MENANG",
			"nexus defeat is presented in the UI"
		)
		_check(
			screen.get_node("%SpawnButton").disabled and not session.request_assault(0, 0),
			"finished scene cannot queue new combat"
		)
		ticks = world.tick_count
		await _physics_steps(3)
		_check(world.tick_count == ticks, "terminal siege stays frozen")
		screen.pause_match()
		_check(
			not screen.get_node("%ResumeButton").visible,
			"result menu offers restart/menu, not resume"
		)
		screen.get_node("%MenuButton").pressed.emit()
		await _settle()
		_check(not paused and app.current_screen.name == "MainMenu", "result exits cleanly to menu")
		_check(get_node_count() == baseline, "siege cycles leave no orphan scene nodes")


func _test_prototype_scene(app: Node) -> void:
	var baseline: int = get_node_count()
	for cycle in range(3):
		app.current_screen.get_node("%PrototypeButton").pressed.emit()
		app.current_screen.get_node("%PrototypeButton").pressed.emit()
		await _settle()
		var screen = app.current_screen
		var session = screen.simulation
		var world = session.world
		session.set_physics_process(false)
		world.defender_enabled = false
		_check(
			screen.name == "PrototypeMatch" and app.screen_root.get_child_count() == 1,
			"prototype has its own guarded menu route"
		)
		_check(
			(
				world.structures.size() == 2
				and world.units.is_empty()
				and world.economy.gold == [1000, 350]
			),
			"playable match starts empty with source budgets"
		)
		var click := InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		click.position = screen.arena.get_global_transform_with_canvas() * world.slots[2].position
		root.push_input(click, true)
		await _settle()
		_check(session.selected_slot_id == 2, "scaled mouse input selects blue build slot")
		_check(
			(
				not screen.get_node("%BuildButton").disabled
				and screen.get_node("%SellButton").disabled
			),
			"empty owned slot enables build, not sale"
		)
		click = InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		click.position = Vector2(500, 50)
		root.push_input(click, true)
		await _settle()
		_check(session.selected_slot_id == 2, "match HUD consumes clicks without changing slot")
		screen.get_node("%BuildButton").pressed.emit()
		screen.get_node("%BuildButton").pressed.emit()
		_check(
			session.command.id == 2 and world.economy.gold[0] == 1000,
			"build UI captures one command with no immediate charge"
		)
		session.select_at(world.slots[5].position)
		session._physics_process(1.0 / 60.0)
		var old_tower_id: int = world.slots[2].structure_id
		_check(
			old_tower_id > 0 and world.slots[5].structure_id == -1 and world.economy.gold[0] == 900,
			"build uses captured slot, not later selection"
		)
		_check(
			session.selected_slot_id == 5 and session.selected_id == -1,
			"completed build does not steal a newer selection"
		)
		session._physics_process(1.0 / 60.0)
		_check(
			world.economy.gold[0] == 900 and session.command.is_empty(), "build is consumed once"
		)
		session.select_at(world.slots[2].position)
		await _settle()
		_check(
			(
				screen.get_node("%BuildButton").disabled
				and not screen.get_node("%SellButton").disabled
			),
			"built own tower enables sale only"
		)
		_check(session.request_sell(old_tower_id), "sale ID captured")
		# Simulate invalidation between request and execution; the new ID must remain untouched.
		world.sell_tower(0, old_tower_id)
		world.build_tower(0, 2)
		var replacement_id: int = world.slots[2].structure_id
		session._physics_process(1.0 / 60.0)
		_check(
			world.economy.gold[0] == 850 and world.slots[2].structure_id == replacement_id,
			"queued stale sale cannot refund or remove a replacement"
		)
		session.select_at(world.slots[2].position)
		await _settle()
		screen.get_node("%SellButton").pressed.emit()
		screen.get_node("%SellButton").pressed.emit()
		session._physics_process(1.0 / 60.0)
		_check(
			world.economy.gold[0] == 900 and world.slots[2].structure_id == -1,
			"sale UI refunds exactly once"
		)
		_check(session.request_build(2), "build queues before pause")
		var ticks: int = world.tick_count
		var remaining: int = world.scheduler.remaining_ticks
		session.set_physics_process(true)
		screen.pause_match()
		await _physics_steps(3)
		_check(
			(
				session.command.is_empty()
				and world.tick_count == ticks
				and world.scheduler.remaining_ticks == remaining
				and world.economy.gold[0] == 900
			),
			"pause cancels transactions and freezes income/wave clocks"
		)
		_check(
			not session.request_build(2) and not session.request_sell(replacement_id),
			"paused match rejects new transactions"
		)
		screen.resume_match()
		screen.arena.process_mode = Node.PROCESS_MODE_DISABLED
		await _physics_steps(3)
		_check(world.tick_count > ticks, "prototype simulation is independent of rendering")
		screen.arena.process_mode = Node.PROCESS_MODE_PAUSABLE
		session.set_physics_process(false)
		session.request_build(2)
		app._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
		_check(paused and session.command.is_empty(), "focus loss cancels match transaction")
		screen.resume_match()
		var tap := InputEventScreenTouch.new()
		tap.pressed = true
		tap.position = screen.arena.get_global_transform_with_canvas() * world.slots[9].position
		screen._unhandled_input(tap)
		await _settle()
		_check(
			session.selected_slot_id == 9 and screen.get_node("%BuildButton").disabled,
			"touch adapter can inspect enemy slot but cannot build there"
		)
		session.request_build(9)
		session._physics_process(1.0 / 60.0)
		_check(
			world.slots[9].structure_id == -1 and world.economy.gold[0] == 900,
			"execution rejects enemy slot even when UI is bypassed"
		)
		click = InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		click.device = InputEvent.DEVICE_ID_EMULATION
		click.position = screen.arena.get_global_transform_with_canvas() * world.slots[2].position
		screen._unhandled_input(click)
		_check(session.selected_slot_id == 9, "touch emulation does not double-dispatch selection")
		_check(world.economy.is_balanced(), "UI transactions preserve ledger invariant")
		_check(
			(
				screen.get_node("HUD/TopBar").get_global_rect().end.x <= 1280.0
				and screen.get_node("HUD/BottomBar").get_global_rect().end.y <= 720.0
			),
			"prototype HUD fits reference viewport"
		)
		var winner: int = cycle % 2
		var nexus = world.nexuses[1 - winner]
		nexus.shield_active = false
		nexus.shield = 0
		nexus.hp = 1
		var attacker = world.spawn_unit(session.DEFINITIONS[0], winner, 1)
		attacker.position = nexus.position - Vector2(20, 0)
		world.apply_hit(attacker.id, nexus.id)
		await _settle()
		var title := "BIRU MENANG" if winner == 0 else "MERAH MENANG"
		_check(
			(
				paused
				and screen.get_node("%PauseOverlay").visible
				and screen.get_node("%PauseTitle").text == title
			),
			"match result opens automatically for either team"
		)
		_check(
			(
				not screen.get_node("%ResumeButton").visible
				and screen.get_node("%BuildButton").disabled
				and screen.get_node("%SellButton").disabled
			),
			"result offers restart/menu, no resume or transactions"
		)
		screen.resume_match()
		_check(paused and not session.request_build(2), "result cannot resume or accept build")
		var old_screen_id: int = screen.get_instance_id()
		screen.get_node("%RestartButton").pressed.emit()
		await _settle()
		screen = app.current_screen
		session = screen.simulation
		world = session.world
		_check(
			(
				not is_instance_id_valid(old_screen_id)
				and not paused
				and screen.name == "PrototypeMatch"
			),
			"restart disposes old scene and retains prototype mode"
		)
		_check(
			(
				world.economy.gold == [1000, 350]
				and world.economy.spent == [0, 0]
				and world.structures.size() == 2
				and world.wave_count == 0
				and world.winner == -1
			),
			"restart resets economy, slots, waves and result"
		)
		_check(
			(
				session.selected_slot_id == -1
				and session.command.is_empty()
				and world.scheduler.pending_count() == 0
				and world.projectiles.is_empty()
			),
			"restart leaves no stale input, queue or projectile"
		)
		screen.pause_match()
		screen.get_node("%MenuButton").pressed.emit()
		await _settle()
		_check(
			not paused and app.current_screen.name == "MainMenu",
			"prototype exits paused/result cleanly"
		)
		_check(get_node_count() == baseline, "prototype cycles do not leak scene nodes")
