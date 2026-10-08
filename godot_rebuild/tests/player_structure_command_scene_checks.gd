extends RefCounted
## End-to-end proof for all source player build choices and both paid shields.

const Structure = preload("res://scripts/combat/structure_state.gd")


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var world = session.world
	session.set_physics_process(false)
	world.set_ai_enabled(false)

	var build_buttons := {
		"archer": screen.get_node("%BuildButton"),
		"cannon": screen.get_node("%CannonButton"),
		"ice": screen.get_node("%IceButton"),
		"mage": screen.get_node("%MageButton"),
	}
	var all_build_controls := true
	for button in build_buttons.values():
		all_build_controls = all_build_controls and button != null
	check.call(all_build_controls, "Four build controls exist")
	check.call(
		(
			screen.get_node("%RegenShieldButton") != null
			and screen.get_node("%CastleShieldButton") != null
		),
		"Both source paid-shield controls exist"
	)

	for path: String in ["archer", "cannon", "ice", "mage"]:
		var slot_id: int = ["archer", "cannon", "ice", "mage"].find(path)
		var build_button := build_buttons[path] as Button
		_select_slot(session, slot_id)
		screen._process(0.0)
		check.call(screen.get_node("%Paths").visible, path + ": structure option row is visible")
		check.call(
			(
				screen.get_node("%CannonButton").visible
				and screen.get_node("%IceButton").visible
				and screen.get_node("%MageButton").visible
			),
			path + ": empty slot exposes all non-Archer source choices"
		)
		check.call(
			"Bangun" in build_button.text and not build_button.disabled,
			path + ": exact source build choice is enabled"
		)
		var before: int = world.economy.gold[world.BLUE]
		build_button.pressed.emit()
		check.call(
			(
				session.command.kind == "build"
				and session.command.id == slot_id
				and session.command.path == path
			),
			path + ": UI captures immutable slot and path"
		)
		check.call(
			world.get_slot(slot_id).structure_id == -1 and world.economy.gold[world.BLUE] == before,
			path + ": UI cannot mutate before fixed tick"
		)
		build_button.pressed.emit()
		check.call(
			session.command.kind == "build" and session.command.path == path,
			path + ": same-frame repeat cannot replace queued build"
		)
		session._physics_process(1.0 / 60.0)
		var tower = world.get_unit(world.get_slot(slot_id).structure_id) as Structure
		check.call(
			tower != null and tower.settings().tower_path == path and tower.settings().level == 1,
			path + ": fixed tick builds exact source Lv1 identity"
		)
		check.call(
			world.economy.gold[world.BLUE] == before - world.Economy.BUILD_COST,
			path + ": repeated press debits exactly once"
		)
		check.call(world.economy.is_balanced(), path + ": playable build ledger balances")

	var shield_tower = world.get_unit(world.get_slot(0).structure_id) as Structure
	world.economy.credit_kill(world.BLUE, 5000)
	while shield_tower.settings().level < Structure.REGEN_SHIELD_MIN_LEVEL:
		var level: int = shield_tower.settings().level
		check.call(
			world.upgrade_tower(shield_tower.id, level, "archer"),
			"Playable shield tower reaches source level gate"
		)
	session.selected_slot_id = 0
	session.selected_id = shield_tower.id
	screen._process(0.0)
	var regen: Button = screen.get_node("%RegenShieldButton")
	check.call(
		regen.visible and not regen.disabled and "850 G" in regen.text,
		"Level-four player tower exposes affordable Regen Shield"
	)
	check.call(
		not screen.get_node("%CannonButton").visible,
		"Regen context replaces irrelevant path controls"
	)
	var before_regen: int = world.economy.gold[world.BLUE]
	regen.pressed.emit()
	regen.pressed.emit()
	check.call(
		session.command.kind == "regen_shield" and session.command.id == shield_tower.id,
		"Regen UI captures selected tower once"
	)
	check.call(
		not shield_tower.regen_shield_active and world.economy.gold[world.BLUE] == before_regen,
		"Regen purchase waits for fixed tick"
	)
	session._physics_process(1.0 / 60.0)
	check.call(
		shield_tower.regen_shield_active and shield_tower.shield == shield_tower.shield_max,
		"Fixed tick activates and fills player Regen Shield"
	)
	check.call(
		world.economy.gold[world.BLUE] == before_regen - Structure.REGEN_SHIELD_COST,
		"Double Regen press spends source cost once"
	)
	screen._process(0.0)
	check.call(regen.disabled and "ON" in regen.text, "Purchased Regen control becomes ON status")
	var after_regen: int = world.economy.gold[world.BLUE]
	check.call(
		session.request_regen_shield(shield_tower.id),
		"Session accepts stale Regen request for fixed-tick revalidation"
	)
	session._physics_process(1.0 / 60.0)
	check.call(
		world.economy.gold[world.BLUE] == after_regen and world.transaction_error == "shield",
		"Repeated Regen transaction is rejected without debit"
	)

	var castle = world.nexuses[world.BLUE] as Structure
	session.selected_slot_id = -1
	session.selected_id = castle.id
	castle.set_wave(10)
	screen._process(0.0)
	var castle_button: Button = screen.get_node("%CastleShieldButton")
	check.call(
		castle_button.visible and castle_button.disabled and "FREE" in castle_button.text,
		"Free-wave Castle Shield is status-only"
	)
	castle.set_wave(11)
	screen._process(0.0)
	check.call(
		not castle_button.disabled and "850 G" in castle_button.text,
		"Post-wave-ten Castle Shield becomes buyable"
	)
	var before_castle: int = world.economy.gold[world.BLUE]
	castle_button.pressed.emit()
	castle_button.pressed.emit()
	check.call(
		session.command.kind == "castle_shield" and session.command.id == castle.id,
		"Castle UI captures selected nexus once"
	)
	check.call(
		not castle.castle_shield_purchased and world.economy.gold[world.BLUE] == before_castle,
		"Castle purchase waits for fixed tick"
	)
	session._physics_process(1.0 / 60.0)
	check.call(
		(
			castle.castle_shield_purchased
			and castle.shield_active
			and castle.shield == castle.shield_max
		),
		"Fixed tick activates and fills player Castle Shield"
	)
	check.call(
		world.economy.gold[world.BLUE] == before_castle - Structure.CASTLE_SHIELD_COST,
		"Double Castle press spends source cost once"
	)
	screen._process(0.0)
	check.call(
		castle_button.disabled and "ON" in castle_button.text,
		"Purchased Castle control becomes ON status"
	)
	check.call(world.economy.is_balanced(), "Playable structure command ledger remains balanced")

	var old_screen_id: int = screen.get_instance_id()
	screen.pause_match()
	screen.get_node("%RestartButton").pressed.emit()
	await _settle(tree)
	check.call(
		not is_instance_id_valid(old_screen_id) and not tree.paused,
		"Player structure command restart frees the old screen"
	)
	screen = app.current_screen
	session = screen.simulation
	world = session.world
	session.set_physics_process(false)
	var slots_clear := true
	for slot in world.slots:
		slots_clear = slots_clear and slot.structure_id == -1
	check.call(slots_clear, "Restart clears all four player build choices")
	check.call(
		(
			not world.nexuses[world.BLUE].castle_shield_purchased
			and world.nexuses[world.BLUE].free_shield_active
		),
		"Restart clears paid player Castle Shield state"
	)
	check.call(
		(
			screen.get_node("%RegenShieldButton") != null
			and screen.get_node("%CastleShieldButton") != null
		),
		"Restart reauthors both shield controls"
	)
	screen.get_node("%BackButton").pressed.emit()
	await _settle(tree)
	check.call(app.current_screen.name == "MainMenu", "Player structure scene exits cleanly")
	check.call(
		tree.get_node_count() == baseline, "Player structure scene leaves no orphan controls"
	)


func _select_slot(session, slot_id: int) -> void:
	session.selected_slot_id = slot_id
	session.selected_id = -1


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
