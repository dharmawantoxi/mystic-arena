extends RefCounted
## Actual scene refund/command/button/reset checks. Player shield buttons now
## live in the HUD; player command path is exercised end-to-end.


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var world = session.world
	session.set_physics_process(false)
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
	# Player UI: regen shield row is visible for an Lv4 blue tower and shows
	# "AKTIF" label after purchase; button must be disabled since already bought.
	var regen_btn = screen.get_node("%RegenShieldButton")
	var shields_row = screen.get_node("%Shields")
	check.call(shields_row.visible, "Shield row visible for paid-capable tower")
	check.call(regen_btn.visible and regen_btn.disabled, "Regen button shown disabled when active")
	check.call(regen_btn.text.contains("AKTIF"), "Regen label reads active after purchase")
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
	# Build a fresh Lv4 tower and press the player regen shield button.
	world.build_tower(0, 2)
	var lv4 = world.get_unit(world.slots[2].structure_id)
	for previous in range(1, 4):
		world.upgrade_tower(lv4.id, previous)
	session.select_at(lv4.position)
	await _settle(tree)
	check.call(
		regen_btn.visible and not regen_btn.disabled and regen_btn.text.contains("850"),
		"Regen button advertises price when purchasable"
	)
	var g_before: int = world.economy.gold[0]
	regen_btn.pressed.emit()
	regen_btn.pressed.emit()
	session._physics_process(1.0 / 60.0)
	check.call(
		lv4.regen_shield_active and world.economy.gold[0] == g_before - 850,
		"Player button buys regen shield once, debits ledger"
	)
	await _settle(tree)
	check.call(
		regen_btn.disabled and regen_btn.text.contains("AKTIF"), "Regen label flips to active"
	)
	# Castle shield: at wave 1 the nexus shows free label, not a buy button.
	var blue_nexus = world.nexuses[0]
	session.selected_id = blue_nexus.id
	session.selected_slot_id = -1
	await _settle(tree)
	var castle_btn = screen.get_node("%CastleShieldButton")
	check.call(castle_btn.visible and castle_btn.disabled, "Castle row visible early-wave")
	check.call(castle_btn.text.contains("GRATIS"), "Early wave shows free-shield label")
	# Advance past wave 10 via set_wave and re-select; button must become purchasable.
	blue_nexus.set_wave(11)
	world.economy.credit_kill(0, 2000)
	await _settle(tree)
	check.call(
		castle_btn.visible and not castle_btn.disabled and castle_btn.text.contains("850"),
		"Post-wave-10 castle button becomes purchasable"
	)
	var c_before: int = world.economy.gold[0]
	castle_btn.pressed.emit()
	session._physics_process(1.0 / 60.0)
	check.call(
		blue_nexus.castle_shield_purchased and world.economy.gold[0] == c_before - 850,
		"Player button buys castle shield and debits ledger"
	)
	await _settle(tree)
	check.call(
		castle_btn.disabled and castle_btn.text.contains("AKTIF"), "Castle label flips to active"
	)
	# Level-3 tower must hide shield row.
	world.build_tower(0, 3)
	var t3 = world.get_unit(world.slots[3].structure_id)
	for previous in range(1, 3):
		world.upgrade_tower(t3.id, previous)
	session.select_at(t3.position)
	await _settle(tree)
	check.call(not shields_row.visible, "Shield row hidden below level 4")
	# Enemy selection must hide the row.
	var red_castle = world.nexuses[1]
	red_castle.set_wave(11)
	session.selected_id = red_castle.id
	await _settle(tree)
	check.call(not shields_row.visible, "Shield row hidden for enemy selection")
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
