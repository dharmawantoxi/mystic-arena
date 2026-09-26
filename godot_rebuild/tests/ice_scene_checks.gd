extends RefCounted
## Ice path UI lifecycle through the real scene/session.


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var world = session.world
	session.set_physics_process(false)
	world.defender_enabled = false
	world.build_tower(0, 0)
	var tower = world.get_unit(world.slots[0].structure_id)
	session.selected_id = tower.id
	session.selected_slot_id = 0
	await _settle(tree)
	check.call(
		(
			not screen.get_node("%UpgradeButton").disabled
			and screen.get_node("%UpgradeButton").text.contains("175")
			and not screen.get_node("%IceButton").disabled
			and screen.get_node("%IceButton").text.contains("175")
		),
		"level-one tower offers the ice path"
	)
	check.call(
		(
			screen.get_node("%CannonButton").visible
			and screen.get_node("%IceButton").visible
			and not screen.get_node("%NexusButton").visible
		),
		"contextual paths show for blue level 1"
	)
	screen.get_node("%IceButton").pressed.emit()
	screen.get_node("%IceButton").pressed.emit()
	check.call(
		(
			session.command.id == tower.id
			and session.command.level == 1
			and session.command.path == "ice"
			and tower.settings().tower_path == "archer"
			and world.economy.gold[0] == 900
		),
		"ice click captures ID/level/path without charge"
	)
	session.select_at(world.slots[2].position)
	session._physics_process(1.0 / 60.0)
	check.call(
		(
			tower.settings().tower_path == "ice"
			and tower.settings().level == 2
			and world.economy.gold[0] == 725
			and session.last_action.contains("Ice")
		),
		"ice buys captured path once"
	)
	session.selected_id = tower.id
	session.selected_slot_id = 0
	await _settle(tree)
	check.call(
		(
			not screen.get_node("%IceButton").visible
			and screen.get_node("%IceButton").disabled
			and not screen.get_node("%CannonButton").visible
			and screen.get_node("%NexusButton").visible
		),
		"paths hide past level 1, nexus returns"
	)
	check.call(
		screen.get_node("%UpgradeButton").text.contains("325"),
		"upgrade button continues the ice path"
	)
	check.call(
		(
			screen.get_node("%SelectionLabel").text.contains("Ice")
			and screen.get_node("%SelectionLabel").text.contains("kristal")
			and not screen.get_node("%SelectionLabel").text.contains("panah")
		),
		"ice inspection names crystals, not arrows"
	)
	screen.get_node("%UpgradeButton").pressed.emit()
	session._physics_process(1.0 / 60.0)
	check.call(
		tower.settings().level == 3 and world.economy.gold[0] == 400,
		"ice follows its own path past level 1"
	)
	world.economy.credit_kill(0, 1000)
	session.request_upgrade(tower.id, "ice")
	world.upgrade_tower(tower.id, 3)
	var before: int = world.economy.gold[0]
	session._physics_process(1.0 / 60.0)
	check.call(
		(
			tower.settings().level == 4
			and world.economy.gold[0] == before
			and session.last_action.contains("berubah")
		),
		"stale ice level cannot buy twice"
	)
	for slot_id in range(1, 9):
		world.build_tower(0, slot_id)
	var choice = world.get_unit(world.slots[8].structure_id)
	session.selected_id = choice.id
	session.selected_slot_id = 8
	await _settle(tree)
	check.call(
		screen.get_node("%UpgradeButton").disabled and screen.get_node("%IceButton").disabled,
		"poor paths stay disabled"
	)
	check.call(
		screen.get_node("%IceButton").visible and not screen.get_node("%NexusButton").visible,
		"poor level 1 still shows paths, not nexus"
	)
	world.economy.credit_kill(0, 5000)
	await _settle(tree)
	session.request_upgrade(choice.id, "ice")
	screen.pause_match()
	check.call(
		session.command.is_empty() and not session.request_upgrade(choice.id, "ice"),
		"pause cancels ice command"
	)
	screen.resume_match()
	session.request_upgrade(choice.id, "ice")
	app._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check.call(session.command.is_empty() and tree.paused, "focus cancels ice")
	screen.resume_match()
	check.call(session.request_upgrade(choice.id, "ice"), "ice queues")
	session._physics_process(1.0 / 60.0)
	for level in range(2, 6):
		check.call(session.request_upgrade(choice.id), "locked path queues")
		session._physics_process(1.0 / 60.0)
	await _settle(tree)
	check.call(
		(
			choice.settings().level == 6
			and choice.settings().tower_path == "ice"
			and screen.get_node("%UpgradeButton").disabled
			and screen.get_node("%UpgradeButton").text.contains("maksimum")
			and screen.get_node("%IceButton").disabled
		),
		"max ice presented"
	)
	check.call(
		screen.get_node("HUD/BottomBar").get_global_rect().end.x <= 1280.0,
		"six command buttons fit reference HUD"
	)
	world.build_tower(1, 9)
	session.select_at(world.slots[9].position)
	await _settle(tree)
	check.call(
		(
			screen.get_node("%IceButton").disabled
			and not screen.get_node("%IceButton").visible
			and screen.get_node("%IceButton").text.contains("lawan")
		),
		"enemy tower cannot choose ice"
	)
	session.selected_id = world.nexuses[0].id
	session.selected_slot_id = -1
	await _settle(tree)
	check.call(
		(
			screen.get_node("%IceButton").disabled
			and not screen.get_node("%IceButton").visible
			and screen.get_node("%NexusButton").visible
		),
		"nexus selection hides ice"
	)
	check.call(world.economy.is_balanced(), "ice UI ledger reconciles")
	world.winner = 1
	await _settle(tree)
	check.call(
		(
			tree.paused
			and screen.get_node("%IceButton").disabled
			and not session.request_upgrade(choice.id, "ice")
		),
		"result disables ice"
	)
	var old_id: int = screen.get_instance_id()
	screen.get_node("%RestartButton").pressed.emit()
	await _settle(tree)
	check.call(not is_instance_id_valid(old_id) and not tree.paused, "ice scene disposed")
	world = app.current_screen.simulation.world
	world.build_tower(0, 0)
	check.call(
		(
			world.get_unit(world.slots[0].structure_id).settings().tower_path == "archer"
			and world.economy.gold[0] == 900
		),
		"restart resets paths without inheritance"
	)
	app.show_menu()
	await _settle(tree)
	check.call(tree.get_node_count() == baseline, "ice lifecycle clean")


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
