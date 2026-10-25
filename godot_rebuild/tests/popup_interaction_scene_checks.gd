extends RefCounted
## Scene-level pointer/controller coverage for BuildPopup and HeroPanel (slice 9bv9).

const BuildLayout = preload("res://scripts/ui/build_popup_layout.gd")
const HeroLayout = preload("res://scripts/ui/hero_panel_layout.gd")
const Structure = preload("res://scripts/combat/structure_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var world = session.world
	session.set_physics_process(false)
	world.set_ai_enabled(false)
	world.economy.credit_kill(world.BLUE, 20_000)

	var paths := ["archer", "cannon", "ice", "mage"]
	for index in range(paths.size()):
		session.selected_slot_id = index
		session.selected_id = -1
		screen._process(0.0)
		var state: Dictionary = screen.arena.get("build_popup_state")
		var card: Rect2i = BuildLayout.state_button_rect(state, index)
		var before_gold: int = world.economy.gold[world.BLUE]
		var point := screen.arena.get_global_transform_with_canvas() * Vector2(card.get_center())
		match index:
			0:
				_mouse_press(screen, point, MOUSE_BUTTON_LEFT)
			1:
				_touch_tap(screen, point, 10_000.0 + index * 500.0)
			2:
				screen.controller_cursor.active = true
				screen.controller_cursor.cursor_position = point
				check.call(
					screen._controller_activate_hover(),
					"Controller confirm recognizes a painted BuildPopup card"
				)
				screen.controller_cursor.active = false
			_:
				screen._primary_action(point)
		check.call(
			(
				session.command.get("kind", "") == "build"
				and int(session.command.get("id", -1)) == index
				and String(session.command.get("path", "")) == paths[index]
			),
			"BuildPopup queues the exact %s path from its source card" % paths[index]
		)
		check.call(
			(
				world.get_slot(index).structure_id == -1
				and world.economy.gold[world.BLUE] == before_gold
			),
			"BuildPopup waits for the fixed tick before changing the match"
		)
		session._physics_process(1.0 / 60.0)
		var tower := world.get_unit(world.get_slot(index).structure_id) as Structure
		check.call(
			tower != null and tower.settings().tower_path == paths[index],
			"Fixed tick executes the %s BuildPopup request" % paths[index]
		)
		check.call(
			world.economy.gold[world.BLUE] == before_gold - world.Economy.BUILD_COST,
			"BuildPopup charges exactly one source build cost"
		)

	# Close is a distinct 48 px target; an unclaimed click closes and dispatches to the next slot.
	session.selected_slot_id = 4
	session.selected_id = -1
	screen._process(0.0)
	var state: Dictionary = screen.arena.get("build_popup_state")
	var close_rect: Rect2i = BuildLayout.state_close_rect(state)
	var close_target: Rect2i = screen._touch_target_rect(close_rect)
	check.call(
		close_target.size == Vector2i(48, 48),
		"BuildPopup close uses the source minimum touch target"
	)
	screen._primary_action(
		screen.arena.get_global_transform_with_canvas() * Vector2(close_rect.get_center())
	)
	check.call(session.selected_slot_id == -1, "BuildPopup close clears the selected build slot")

	session.selected_slot_id = 4
	screen._process(0.0)
	var next_slot = world.get_slot(8)
	var next_point: Vector2 = screen.arena.get_global_transform_with_canvas() * next_slot.position
	_mouse_press(screen, next_point, MOUSE_BUTTON_LEFT)
	check.call(
		session.selected_slot_id == 8 and session.command.is_empty(),
		"Clicking another world slot dismisses BuildPopup and continues world selection"
	)

	# The same handler is reachable from the actual wide-screen SidePanel Control.
	screen.side_panel.configure(1624)
	session.selected_slot_id = 4
	session.selected_id = -1
	screen._process(0.0)
	state = screen.arena.get("build_popup_state")
	check.call(
		state.has("panel_pos") and int(state.get("slot_id", -1)) == 4,
		"Docked BuildPopup retains its slot ID and mobile anchor"
	)
	var dock_card: Rect2i = BuildLayout.state_button_rect(state, 3)
	_side_panel_press(screen, Vector2i(dock_card.get_center()), MOUSE_BUTTON_LEFT)
	check.call(
		(
			session.command.get("kind", "") == "build"
			and int(session.command.get("id", -1)) == 4
			and String(session.command.get("path", "")) == "mage"
		),
		"SidePanel mouse input routes a docked BuildPopup card to PrototypeSession"
	)
	session._physics_process(1.0 / 60.0)
	var dock_tower := world.get_unit(world.get_slot(4).structure_id) as Structure
	check.call(
		dock_tower != null and dock_tower.settings().tower_path == "mage",
		"Docked BuildPopup uses the native build transaction"
	)
	session.selected_slot_id = 5
	screen._process(0.0)
	_side_panel_press(screen, Vector2i(1300, 700), MOUSE_BUTTON_LEFT)
	check.call(
		session.selected_slot_id == -1,
		"Unclaimed click on the side dock dismisses BuildPopup without reaching the arena"
	)

	var hero := world.player_roster()[0] as HeroState
	session.selected_slot_id = -1
	session.selected_id = hero.id
	hero.auto_cast_enabled = false
	screen._process(0.0)
	var hero_state: Dictionary = screen.arena.get("hero_panel_state")
	check.call(
		not hero_state.is_empty() and hero_state.has("panel_pos"),
		"Selected HeroPanel is anchored inside the wide-screen dock"
	)
	var autocast_rect: Rect2i = HeroLayout.autocast_rect(hero_state)
	_side_panel_press(screen, Vector2i(autocast_rect.get_center()), MOUSE_BUTTON_LEFT)
	check.call(
		(
			session.command.get("kind", "") == "autocast"
			and int(session.command.get("id", -1)) == hero.id
			and not hero.auto_cast_enabled
		),
		"Docked HeroPanel autocast button queues, but does not mutate, the hero"
	)
	session._physics_process(1.0 / 60.0)
	check.call(hero.auto_cast_enabled, "Fixed tick activates HeroPanel autocast")

	var forge_button_rect: Rect2i = HeroLayout.item_shop_rect(hero_state)
	_side_panel_press(screen, Vector2i(forge_button_rect.get_center()), MOUSE_BUTTON_LEFT)
	check.call(
		(
			screen.forge_panel.visible
			and world.forge.target_hero_id == hero.id
			and screen.forge_panel.shop().inspect_item.is_empty()
		),
		"HeroPanel ITEM FORGE button opens Forge for the selected hero"
	)
	screen.forge_panel.set_open(false)
	screen.forge_panel.shop().inspect_item = ""
	screen._process(0.0)
	hero_state = screen.arena.get("hero_panel_state")

	check.call(hero.items.add("dead_edge"), "HeroPanel interaction fixture equips a source item")
	hero.apply_item_change()
	screen._process(0.0)
	hero_state = screen.arena.get("hero_panel_state")
	var item_rect: Rect2i = HeroLayout.item_slot_rect(hero_state, 0)
	_side_panel_press(screen, Vector2i(item_rect.get_center()), MOUSE_BUTTON_LEFT)
	check.call(
		(
			screen.forge_panel.visible
			and screen.forge_panel.shop().inspect_item == "dead_edge"
			and world.forge.target_hero_id == hero.id
		),
		"Occupied HeroPanel slot opens Forge on the selected hero and inspects that item"
	)
	screen.forge_panel.set_open(false)
	screen.forge_panel.shop().inspect_item = ""
	screen._process(0.0)
	hero_state = screen.arena.get("hero_panel_state")
	var empty_rect: Rect2i = HeroLayout.item_slot_rect(hero_state, 2)
	_side_panel_press(screen, Vector2i(empty_rect.get_center()), MOUSE_BUTTON_LEFT)
	check.call(
		screen.forge_panel.visible and screen.forge_panel.shop().inspect_item.is_empty(),
		"Empty HeroPanel slot opens Forge without inventing an item detail"
	)
	screen.forge_panel.set_open(false)
	screen.forge_panel.shop().inspect_item = ""
	screen._process(0.0)

	# Fall back to the arena-anchored panel for desktop mouse/touch actions.
	screen.side_panel.configure(1280)
	world.economy.credit_kill(world.BLUE, 20_000)
	session.selected_id = hero.id
	screen._process(0.0)
	hero_state = screen.arena.get("hero_panel_state")
	var upgrade_rect: Rect2i = HeroLayout.upgrade_rect(hero_state)
	var before_level := hero.level
	var before_gold: int = world.economy.gold[world.BLUE]
	_mouse_press(
		screen,
		screen.arena.get_global_transform_with_canvas() * Vector2(upgrade_rect.get_center()),
		MOUSE_BUTTON_LEFT
	)
	check.call(
		(
			session.command.get("kind", "") == "hero_upgrade"
			and int(session.command.get("id", -1)) == hero.id
			and hero.level == before_level
			and world.economy.gold[world.BLUE] == before_gold
		),
		"HeroPanel upgrade click queues an immutable request without spending early"
	)
	session._physics_process(1.0 / 60.0)
	check.call(
		hero.level == before_level + 1 and world.economy.gold[world.BLUE] < before_gold,
		"HeroPanel upgrade executes through the existing session/forge transaction"
	)

	screen._process(0.0)
	hero_state = screen.arena.get("hero_panel_state")
	var blank_local := Vector2(
		HeroLayout.panel_rect(hero_state).position.x + 6,
		HeroLayout.panel_rect(hero_state).position.y + 54
	)
	var blank_point := screen.arena.get_global_transform_with_canvas() * blank_local
	screen._primary_action(blank_point)
	check.call(
		session.selected_id == hero.id, "Blank HeroPanel click is consumed without deselecting"
	)
	var item_hit := HeroLayout.item_slot_rect(hero_state, 0).get_center()
	var right_click := InputEventMouseButton.new()
	right_click.device = 0
	right_click.button_index = MOUSE_BUTTON_RIGHT
	right_click.pressed = true
	right_click.position = screen.arena.get_global_transform_with_canvas() * Vector2(item_hit)
	screen._unhandled_input(right_click)
	check.call(
		hero.items.slots[0] == "dead_edge",
		"HeroPanel preserves the source guard: its unreachable right-click drop branch stays inert"
	)
	_touch_long_press(
		screen, screen.arena.get_global_transform_with_canvas() * Vector2(item_hit), 30_000.0
	)
	check.call(
		hero.items.slots[0] == "dead_edge",
		"HeroPanel long-press preserves the same unreachable item-drop guard"
	)

	var close_hero: Rect2i = HeroLayout.close_rect(hero_state)
	_mouse_press(
		screen,
		screen.arena.get_global_transform_with_canvas() * Vector2(close_hero.get_center()),
		MOUSE_BUTTON_LEFT
	)
	check.call(session.selected_id == -1, "HeroPanel close button clears the selected hero")

	# Touch tap routes through the same helper while desktop uses _unhandled_input.
	session.selected_id = hero.id
	session.selected_slot_id = -1
	screen._process(0.0)
	hero_state = screen.arena.get("hero_panel_state")
	var autocast_touch: Rect2i = HeroLayout.autocast_rect(hero_state)
	hero.auto_cast_enabled = false
	screen._process(0.0)
	_touch_tap(
		screen,
		screen.arena.get_global_transform_with_canvas() * Vector2(autocast_touch.get_center()),
		20_000.0
	)
	check.call(
		session.command.get("kind", "") == "autocast",
		"Released touch on HeroPanel autocast reaches the same session request"
	)
	session._physics_process(1.0 / 60.0)
	check.call(hero.auto_cast_enabled, "Touch HeroPanel autocast commits on the fixed tick")

	app.show_menu()
	await _settle(tree)
	check.call(app.current_screen.name == "MainMenu", "Popup interaction scene exits cleanly")
	check.call(tree.get_node_count() == baseline, "Popup interaction scene leaves no orphan nodes")


func _mouse_press(screen: Node, point: Vector2, button_index: int) -> void:
	var event := InputEventMouseButton.new()
	event.device = 0
	event.button_index = button_index
	event.pressed = true
	event.position = point
	screen._unhandled_input(event)


func _touch_tap(screen: Node, point: Vector2, now_ms: float) -> void:
	var down := InputEventScreenTouch.new()
	down.index = 0
	down.pressed = true
	down.position = point
	screen._handle_touch_event(down, now_ms)
	var up := InputEventScreenTouch.new()
	up.index = 0
	up.position = point
	up.pressed = false
	screen._handle_touch_event(up, now_ms + 80.0)


func _touch_long_press(screen: Node, point: Vector2, now_ms: float) -> void:
	var down := InputEventScreenTouch.new()
	down.index = 0
	down.pressed = true
	down.position = point
	screen._handle_touch_event(down, now_ms)
	screen._route_touch_actions(screen.touch_gestures.advance(now_ms + 450.0))
	var up := InputEventScreenTouch.new()
	up.index = 0
	up.position = point
	up.pressed = false
	screen._handle_touch_event(up, now_ms + 500.0)


func _side_panel_press(screen: Node, point: Vector2i, button_index: int) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = button_index
	event.pressed = true
	event.position = Vector2(point - screen.side_panel.panel.position)
	screen.side_panel._gui_input(event)


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
