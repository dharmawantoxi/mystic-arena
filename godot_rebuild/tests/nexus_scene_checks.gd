extends RefCounted
## Nexus UI lifecycle through the real scene/session.


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var world = session.world
	session.set_physics_process(false)
	world.defender_enabled = false
	var nexus = world.nexuses[0]
	session.selected_id = nexus.id
	session.selected_slot_id = -1
	await _settle(tree)
	check.call(
		(
			not screen.get_node("%NexusButton").disabled
			and screen.get_node("%NexusButton").text.contains("500")
		),
		"nexus UI quotes level-two price"
	)
	check.call(screen.get_node("%UpgradeButton").disabled, "archer button stays idle")
	screen.get_node("%NexusButton").pressed.emit()
	screen.get_node("%NexusButton").pressed.emit()
	check.call(
		(
			session.command.id == nexus.id
			and session.command.level == 1
			and nexus.settings().level == 1
			and world.economy.gold[0] == 1000
		),
		"nexus click captures ID/level without charge"
	)
	session.select_at(world.slots[2].position)
	session._physics_process(1.0 / 60.0)
	check.call(
		nexus.settings().level == 2 and world.economy.gold[0] == 500,
		"nexus upgrades captured target once"
	)
	check.call(session.selected_slot_id == 2, "nexus keeps newer slot selection")
	session.selected_id = nexus.id
	session.selected_slot_id = -1
	await _settle(tree)
	check.call(
		screen.get_node("%NexusButton").text.contains("900"), "nexus UI refreshes next price"
	)
	check.call(
		not screen.get_node("%SelectionLabel").text.contains("panah"),
		"nexus inspection has no arrow count"
	)
	world.economy.credit_kill(0, 1000)
	session.request_nexus_upgrade(nexus.id)
	world.upgrade_nexus(nexus.id, 2)
	var before: int = world.economy.gold[0]
	session._physics_process(1.0 / 60.0)
	check.call(
		(
			nexus.settings().level == 3
			and world.economy.gold[0] == before
			and session.last_action.contains("berubah")
		),
		"stale nexus level cannot buy twice"
	)
	await _settle(tree)
	check.call(screen.get_node("%NexusButton").disabled, "poor nexus disabled")
	session.request_nexus_upgrade(nexus.id)
	screen.pause_match()
	check.call(
		session.command.is_empty() and not session.request_nexus_upgrade(nexus.id),
		"pause cancels nexus command"
	)
	screen.resume_match()
	session.request_nexus_upgrade(nexus.id)
	app._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check.call(session.command.is_empty() and tree.paused, "focus cancels nexus")
	screen.resume_match()
	world.economy.credit_kill(0, 8000)
	for level in range(3, 5):
		check.call(session.request_nexus_upgrade(nexus.id), "nexus queues")
		session._physics_process(1.0 / 60.0)
	await _settle(tree)
	check.call(
		(
			nexus.settings().level == 5
			and screen.get_node("%NexusButton").disabled
			and screen.get_node("%NexusButton").text.contains("maksimum")
		),
		"max nexus presented"
	)
	check.call(
		screen.get_node("HUD/BottomBar").get_global_rect().end.x <= 1280.0,
		"four command buttons fit reference HUD"
	)
	session.selected_id = world.nexuses[1].id
	await _settle(tree)
	check.call(
		(
			screen.get_node("%NexusButton").disabled
			and screen.get_node("%NexusButton").text.contains("lawan")
		),
		"enemy nexus cannot upgrade"
	)
	world.build_tower(0, 2)
	session.select_at(world.slots[2].position)
	await _settle(tree)
	check.call(screen.get_node("%NexusButton").disabled, "tower selection hides nexus")
	check.call(world.economy.is_balanced(), "nexus UI ledger reconciles")
	world.winner = 1
	await _settle(tree)
	check.call(
		(
			tree.paused
			and screen.get_node("%NexusButton").disabled
			and not session.request_nexus_upgrade(nexus.id)
		),
		"result disables nexus"
	)
	var old_id: int = screen.get_instance_id()
	screen.get_node("%RestartButton").pressed.emit()
	await _settle(tree)
	check.call(not is_instance_id_valid(old_id) and not tree.paused, "nexus scene disposed")
	world = app.current_screen.simulation.world
	check.call(
		world.nexuses[0].settings().level == 1 and world.economy.gold[0] == 1000,
		"restart resets nexus without inheritance"
	)
	app.show_menu()
	await _settle(tree)
	check.call(tree.get_node_count() == baseline, "nexus lifecycle clean")


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
