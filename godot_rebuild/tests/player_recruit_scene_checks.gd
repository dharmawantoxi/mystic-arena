extends RefCounted
## Playable-scene proof for the player Hero Shop command and multi-hero controls.


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var world = session.world
	session.set_physics_process(false)
	var toggle = screen.get_node("HUD/HeroShopButton")
	var panel = screen.get_node("HUD/HeroShop")
	check.call(toggle != null and panel != null, "Playable match installs Hero Shop controls")
	toggle.pressed.emit()
	await _settle(tree)
	check.call(panel.visible and panel.is_open, "Hero Shop button opens the runtime panel")
	check.call(panel._visible_ids().size() == 6, "Hero Shop exposes six purchased source starters")
	var thorne_button: Button = _card(panel, "thorne")
	var kaizen_button: Button = _card(panel, "kaizen")
	check.call(
		thorne_button != null and not thorne_button.disabled,
		"Affordable unlocked Thorne is buyable"
	)
	check.call(
		kaizen_button != null and kaizen_button.disabled, "Already-active Kaizen is disabled"
	)
	var purse: int = world.economy.gold[world.BLUE]
	thorne_button.pressed.emit()
	(
		check
		. call(
			session.command.kind == "hero_buy" and session.command.hero_type == "thorne",
			"Hero card captures one immutable recruit command",
		)
	)
	check.call(
		world.player_roster().size() == 1 and world.economy.gold[0] == purse,
		"UI never mutates before fixed tick"
	)
	thorne_button.pressed.emit()
	check.call(
		world.player_roster().size() == 1, "Repeated same-frame card press cannot double summon"
	)
	session._physics_process(1.0 / 60.0)
	var roster: Array = world.player_roster()
	check.call(
		roster.size() == 2 and roster[1].definition.id == "thorne",
		"Fixed tick summons exact selected hero"
	)
	check.call(
		world.economy.gold[0] == purse - roster[1].settings().cost,
		"Scene summon debits exact source cost"
	)
	check.call(
		session.selected_id == roster[1].id, "New player hero becomes the controlled selection"
	)
	check.call(
		world.forge.selected_hero_id == roster[1].id,
		"Forge target follows recruited hero selection"
	)
	panel.command_pending = false
	panel.refresh()
	await _settle(tree)
	thorne_button = _card(panel, "thorne")
	check.call(thorne_button != null and thorne_button.disabled, "Purchased card becomes ACTIVE")

	var destination: Vector2 = roster[1].position + Vector2(35, 0)
	check.call(
		session.request_hero_move(roster[1].id, destination),
		"Recruited hero accepts player move command"
	)
	session._physics_process(1.0 / 60.0)
	check.call(roster[1].has_destination, "Recruited hero executes movement through session")
	check.call(
		session.request_hero_upgrade(roster[1].id), "Recruited hero uses selected-ID upgrade path"
	)
	session._physics_process(1.0 / 60.0)
	check.call(roster[1].level == 2, "Recruited non-Kaizen upgrades through real domain")

	toggle.pressed.emit()
	check.call(not panel.visible, "Hero Shop toggles closed")
	toggle.pressed.emit()
	check.call(panel.visible, "Hero Shop reopens")
	screen.pause_match()
	check.call(
		not panel.visible and not panel.is_open, "Pause closes Hero Shop and cancels modal input"
	)
	check.call(session.command.is_empty(), "Pause leaves no pending Hero Shop transaction")
	screen.resume_match()
	screen.get_node("%BackButton").pressed.emit()
	await _settle(tree)
	check.call(app.current_screen.name == "MainMenu", "Hero Shop scene exits cleanly")
	check.call(tree.get_node_count() == baseline, "Hero Shop scene leaves no orphan controls")


func _card(panel: Control, hero_type: String) -> Button:
	for child in panel._grid.get_children():
		var button := child as Button
		if button != null and button.tooltip_text == hero_type:
			return button
	return null


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
