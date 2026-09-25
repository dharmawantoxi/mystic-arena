extends RefCounted
## Async checks through the actual scene/session, separate from pure domain fixture tests.


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var world = session.world
	session.set_physics_process(false)
	world.defender_enabled = false
	world.build_tower(0, 2)
	world.build_tower(0, 5)
	var tower = world.get_unit(world.slots[2].structure_id)
	session.select_at(tower.position)
	await _settle(tree)
	check.call(
		(
			not screen.get_node("%UpgradeButton").disabled
			and screen.get_node("%UpgradeButton").text.contains("175")
		),
		"UI quotes level-two price"
	)
	screen.get_node("%UpgradeButton").pressed.emit()
	screen.get_node("%UpgradeButton").pressed.emit()
	check.call(
		(
			session.command.id == tower.id
			and session.command.level == 1
			and tower.settings().level == 1
			and world.economy.gold[0] == 800
		),
		"upgrade click captures ID/level without immediate mutation"
	)
	session.select_at(world.slots[5].position)
	session._physics_process(1.0 / 60.0)
	check.call(
		tower.settings().level == 2 and world.economy.gold[0] == 625,
		"double click upgrades captured tower once, not current selection"
	)
	check.call(
		session.selected_slot_id == 5 and world.get_unit(session.selected_id).settings().level == 1,
		"upgrade does not steal later selection"
	)
	session.select_at(tower.position)
	await _settle(tree)
	check.call(
		(
			screen.get_node("%SellButton").text.contains("87")
			and screen.get_node("%UpgradeButton").text.contains("325")
		),
		"UI refreshes refund and next price"
	)
	session.request_upgrade(tower.id)
	world.upgrade_tower(tower.id, 2)
	var before: int = world.economy.gold[0]
	session._physics_process(1.0 / 60.0)
	check.call(
		(
			tower.settings().level == 3
			and world.economy.gold[0] == before
			and session.last_action.contains("berubah")
		),
		"queued stale level cannot accidentally buy a second upgrade"
	)
	await _settle(tree)
	check.call(screen.get_node("%UpgradeButton").disabled, "insufficient funds disable upgrade")
	session.request_upgrade(tower.id)
	screen.pause_match()
	check.call(
		session.command.is_empty() and not session.request_upgrade(tower.id),
		"pause cancels and rejects upgrade commands"
	)
	screen.resume_match()
	session.request_upgrade(tower.id)
	app._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check.call(session.command.is_empty() and tree.paused, "focus loss cancels upgrade")
	screen.resume_match()
	world.economy.credit_kill(0, 5000)
	for level in range(3, 6):
		check.call(session.request_upgrade(tower.id), "next upgrade queues")
		session._physics_process(1.0 / 60.0)
	await _settle(tree)
	check.call(
		(
			tower.settings().level == 6
			and screen.get_node("%UpgradeButton").disabled
			and screen.get_node("%UpgradeButton").text.contains("maksimum")
		),
		"max Archer presented without a zero-cost upgrade"
	)
	check.call(
		(
			screen.get_node("%SellButton").text.contains("1600")
			and screen.get_node("%SelectionLabel").text.contains("3 panah")
		),
		"max refund and actual volley count are visible"
	)
	check.call(
		screen.get_node("HUD/BottomBar").get_global_rect().end.x <= 1280.0,
		"three command buttons and stats fit reference HUD"
	)
	before = world.economy.gold[0]
	screen.get_node("%SellButton").pressed.emit()
	screen.get_node("%SellButton").pressed.emit()
	session._physics_process(1.0 / 60.0)
	check.call(
		world.economy.gold[0] == before + 1600 and session.last_action.contains("1600"),
		"sale message reports actual upgraded refund, not hard-coded 50"
	)
	check.call(world.economy.is_balanced(), "upgrade UI ledger reconciles")
	world.build_tower(1, 9)
	session.select_at(world.slots[9].position)
	await _settle(tree)
	check.call(screen.get_node("%UpgradeButton").disabled, "enemy selection cannot upgrade")
	session.selected_id = world.nexuses[0].id
	session.selected_slot_id = -1
	await _settle(tree)
	check.call(screen.get_node("%UpgradeButton").disabled, "nexus upgrade not misleadingly exposed")
	world.winner = 1
	await _settle(tree)
	check.call(
		(
			tree.paused
			and screen.get_node("%UpgradeButton").disabled
			and not session.request_upgrade(world.slots[5].structure_id)
		),
		"result disables upgrade"
	)
	var old_id: int = screen.get_instance_id()
	screen.get_node("%RestartButton").pressed.emit()
	await _settle(tree)
	check.call(
		not is_instance_id_valid(old_id) and not tree.paused,
		"upgraded scene disposed on result restart"
	)
	world = app.current_screen.simulation.world
	world.build_tower(0, 2)
	check.call(
		(
			world.get_unit(world.slots[2].structure_id).settings().level == 1
			and world.economy.gold[0] == 900
		),
		"restart has no inherited tower level or upgrade expense"
	)
	app.show_menu()
	await _settle(tree)
	check.call(tree.get_node_count() == baseline, "upgrade lifecycle does not leak nodes")


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
