extends RefCounted
## ITEM FORGE overlay input through the real PrototypeMatch scene (layer 5f-4).
## The domain and button vocabulary are covered by ai_item_checks; this file
## locks the overlay's modal/background mouse behavior against the source.


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var panel = screen.forge_panel
	session.set_physics_process(false)
	var selected_before: int = int(session.selected_id)

	check.call(not panel.visible, "Forge overlay starts hidden in the scene")
	panel.set_open(true)
	await _settle(tree)
	check.call(panel.visible and panel.shop().is_open, "Forge toggle opens the scene overlay")
	check.call(
		(
			is_equal_approx(float(panel.popup_animation_state().get("target", 0.0)), 1.0)
			and float(panel.popup_animation_state().get("progress", 0.0)) > 0.0
		),
		"Opened scene Forge advances PopupAnimation in _process"
	)
	check.call(
		panel.find_child("ItemForgeGrid", true, false).get_child_count() == 8,
		"Opened scene Forge draws the current 4x2 item page"
	)

	var click := InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = Vector2(24, 24)
	tree.root.push_input(click, true)
	await _settle(tree)
	check.call(not panel.visible and not panel.shop().is_open, "Outside left click closes Forge")
	check.call(
		session.selected_id == selected_before, "Outside Forge click does not select the arena"
	)

	panel.set_open(true)
	await _settle(tree)
	check.call(panel.press("itemshop_card_dead_edge"), "Scene Forge card opens detail")
	await _settle(tree)
	check.call(panel.shop().inspect_item == "dead_edge", "Scene Forge detail state is modal")
	click = InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = Vector2(24, 24)
	tree.root.push_input(click, true)
	await _settle(tree)
	check.call(panel.visible, "Outside click keeps Forge open while detail closes")
	check.call(panel.shop().inspect_item == "", "Outside detail click closes only the popup")

	click = InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_RIGHT
	click.pressed = true
	click.position = Vector2(24, 24)
	tree.root.push_input(click, true)
	await _settle(tree)
	check.call(not panel.visible and not panel.shop().is_open, "Outside right click closes Forge")

	panel.set_open(true)
	await _settle(tree)
	click = InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = Vector2(640, 650)
	tree.root.push_input(click, true)
	await _settle(tree)
	check.call(panel.visible, "Empty click inside Forge card stays in the overlay")

	panel.set_open(false)
	await _settle(tree)
	click = InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = screen.arena.get_global_transform_with_canvas() * Vector2(340, 540)
	tree.root.push_input(click, true)
	await _settle(tree)
	check.call(
		panel.visible and panel.shop().is_open,
		"Radiant arena shop click opens Item Forge through MapRenderer hit-test"
	)
	panel.set_open(false)
	await _settle(tree)
	click = InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = screen.arena.get_global_transform_with_canvas() * Vector2(940, 180)
	tree.root.push_input(click, true)
	await _settle(tree)
	check.call(
		screen.hero_shop_panel.visible and screen.hero_shop_panel.is_open,
		"Dire arena shop click opens Hero Shop through MapRenderer hit-test"
	)
	check.call(
		(
			is_equal_approx(
				float(screen.hero_shop_panel.popup_animation_state().get("target", 0.0)), 1.0
			)
			and float(screen.hero_shop_panel.popup_animation_state().get("progress", 0.0)) > 0.0
		),
		"Opened scene Hero Shop advances PopupAnimation in _process"
	)
	screen.hero_shop_panel.set_open(false)
	await _settle(tree)

	app.show_menu()
	await _settle(tree)
	check.call(tree.get_node_count() == baseline, "Forge scene cycle leaves no orphan nodes")


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
