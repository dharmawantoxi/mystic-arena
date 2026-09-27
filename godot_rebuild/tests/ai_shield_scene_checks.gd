extends RefCounted
## Actual scene refund/command/reset checks. Shield purchase is domain-only, no new UI button.


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var world = session.world
	session.set_physics_process(false)
	world.defender_enabled = false
	world.economy.credit_kill(0, 5000)
	world.build_tower(0, 2)
	var tower = world.get_unit(world.slots[2].structure_id)
	for previous in range(1, 4):
		world.upgrade_tower(tower.id, previous)
	check.call(
		world._activate_regen_shield_for(0, tower.id), "Scene fixture purchases shield via domain"
	)
	session.select_at(tower.position)
	await _settle(tree)
	var refund: int = tower.sale_value()
	check.call(refund == 950, "Source Archer Lv4 + paid shield refund")
	check.call(
		screen.get_node("%SellButton").text == "Jual · %d G" % refund,
		"UI quotes paid shield refund"
	)
	var before: int = world.economy.gold[0]
	screen.get_node("%SellButton").pressed.emit()
	screen.get_node("%SellButton").pressed.emit()
	check.call(world.economy.gold[0] == before, "Paid sale is queued, not immediate")
	session._physics_process(1.0 / 60.0)
	check.call(world.economy.gold[0] == before + refund, "Double click refunds paid tower once")
	check.call(
		world.get_unit(tower.id) == null and world.economy.is_balanced(),
		"Paid scene sale retires target and balances ledger"
	)
	world.economy.credit_kill(1, 1000)
	world.nexuses[1].set_wave(11)
	check.call(
		world._activate_castle_shield_for(1, world.nexuses[1].id),
		"Scene fixture purchases red castle shield"
	)
	screen.pause_match()
	var old_id: int = screen.get_instance_id()
	screen.get_node("%RestartButton").pressed.emit()
	await _settle(tree)
	check.call(
		not is_instance_id_valid(old_id) and not tree.paused,
		"Shield scene restart cleans old screen"
	)
	world = app.current_screen.simulation.world
	app.current_screen.simulation.set_physics_process(false)
	check.call(
		not world.nexuses[1].castle_shield_purchased and world.nexuses[1].free_shield_active,
		"Restart clears paid castle flag"
	)
	world.build_tower(0, 2)
	var fresh = world.get_unit(world.slots[2].structure_id)
	check.call(
		not fresh.regen_shield_active and fresh.sale_value() == 50,
		"Restart clears paid tower state and refund"
	)
	check.call(
		world.economy.gold == [900, 350] and world.economy.is_balanced(),
		"Restart resets shield spending"
	)
	app.show_menu()
	await _settle(tree)
	check.call(tree.get_node_count() == baseline, "Shield scene lifecycle does not leak nodes")


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
