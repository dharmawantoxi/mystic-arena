extends RefCounted
## End-to-end mobile gesture routing through PrototypeMatch and fixed ticks.

const HERO_ROSTER = preload("res://scripts/data/hero_roster.gd").DEFINITIONS


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var world = session.world
	session.set_physics_process(false)
	world.set_ai_enabled(false)
	var hero = world.player_roster()[0]
	var hero_point: Vector2 = screen.arena.get_global_transform_with_canvas() * hero.position

	session.selected_id = -1
	session.selected_slot_id = -1
	_touch(screen, 0, hero_point, true, 10_000.0)
	check.call(
		session.selected_id == -1, "Touch-down alone cannot select before the source release gate"
	)
	_touch(screen, 0, hero_point, false, 10_100.0)
	check.call(session.selected_id == hero.id, "Released tap selects the exact touched player hero")

	var enemy
	for unit in world.units:
		if unit.is_hero and unit.team == world.RED:
			enemy = unit
			break
	check.call(enemy != null, "Touch follow fixture finds the source red hero")
	if enemy != null:
		var enemy_point: Vector2 = screen.arena.get_global_transform_with_canvas() * enemy.position
		_touch(screen, 1, enemy_point, true, 10_300.0)
		check.call(session.command.is_empty(), "Enemy touch cannot queue follow on press")
		_touch(screen, 1, enemy_point, false, 10_400.0)
		check.call(
			(
				session.command.kind == "follow"
				and session.command.id == hero.id
				and session.command.target_id == enemy.id
			),
			"Released enemy tap captures the source follow command"
		)
		session._physics_process(1.0 / 60.0)
		check.call(hero.follow_id == enemy.id, "Fixed tick executes the touch follow target")

	var destination: Vector2 = hero.position + Vector2(150, -90)
	var destination_point: Vector2 = screen.arena.get_global_transform_with_canvas() * destination
	_touch(screen, 1, destination_point, true, 11_000.0)
	check.call(session.command.is_empty(), "Touch move tap cannot mutate or queue on press")
	_touch(screen, 1, destination_point, false, 11_100.0)
	check.call(
		(
			session.command.kind == "move"
			and session.command.id == hero.id
			and Vector2(session.command.point).is_equal_approx(destination)
		),
		"Released tap captures the selected hero and destination"
	)
	check.call(not hero.has_destination, "Touch move waits at the fixed-tick boundary")
	session._physics_process(1.0 / 60.0)
	check.call(
		hero.has_destination and hero.destination.is_equal_approx(destination),
		"Fixed tick executes the touch tap move"
	)

	var hold_destination: Vector2 = hero.position + Vector2(210, -120)
	var hold_point: Vector2 = screen.arena.get_global_transform_with_canvas() * hold_destination
	_touch(screen, 2, hold_point, true, 12_000.0)
	screen._route_touch_actions(screen.touch_gestures.advance(12_449.0))
	check.call(session.command.is_empty(), "Touch hold stays inert before 450 ms")
	screen._route_touch_actions(screen.touch_gestures.advance(12_451.0))
	check.call(
		(
			session.command.kind == "move"
			and Vector2(session.command.point).is_equal_approx(hold_destination)
		),
		"Long press emits the source right-click move exactly once"
	)
	_touch(screen, 2, hold_point, false, 12_700.0)
	check.call(session.command.kind == "move", "Long-press release cannot replace its command")
	session._physics_process(1.0 / 60.0)

	var drag_start := hero_point + Vector2(80, -30)
	_touch(screen, 3, drag_start, true, 13_000.0)
	_drag(screen, 3, drag_start + Vector2(30, 0), 13_020.0)
	_touch(screen, 3, drag_start + Vector2(30, 0), false, 13_040.0)
	check.call(session.command.is_empty(), "Drag beyond source slop suppresses tap commands")
	screen.touch_gestures.cancel()

	var first_double_point: Vector2 = hero.position + Vector2(260, -150)
	var first_double_screen: Vector2 = (
		screen.arena.get_global_transform_with_canvas() * first_double_point
	)
	_touch(screen, 4, first_double_screen, true, 14_000.0)
	_touch(screen, 4, first_double_screen, false, 14_050.0)
	check.call(session.command.kind == "move", "First double-tap edge remains a normal tap")
	session._physics_process(1.0 / 60.0)
	_touch(screen, 4, first_double_screen + Vector2(10, 10), true, 14_150.0)
	_touch(screen, 4, first_double_screen + Vector2(10, 10), false, 14_200.0)
	check.call(session.command.is_empty(), "Second close tap emits double_tap and no world click")

	_add_boss_shop_rows(world)
	screen.hero_shop_panel.tab = "boss"
	screen.hero_shop_panel.set_open(true)
	await _settle(tree)
	var scroll: ScrollContainer
	for node in screen.hero_shop_panel.find_children("*", "ScrollContainer", true, false):
		scroll = node as ScrollContainer
		break
	check.call(scroll != null, "Touch scene finds the runtime Hero Shop scroller")
	if scroll != null:
		var bar := scroll.get_v_scroll_bar()
		check.call(bar.max_value > scroll.size.y, "Boss catalog exceeds the touch viewport")
		scroll.scroll_vertical = 200
		var before_scroll := scroll.scroll_vertical
		var scroll_point := scroll.get_global_rect().get_center()
		_touch(screen, 5, scroll_point, true, 15_000.0)
		_drag(screen, 5, scroll_point + Vector2(0, 90), 15_016.0)
		_touch(screen, 5, scroll_point + Vector2(0, 90), false, 15_032.0)
		check.call(
			scroll.scroll_vertical < before_scroll,
			"Vertical drag converts source notches into Hero Shop scrolling"
		)
		var after_drag := scroll.scroll_vertical
		screen._route_touch_actions(screen.touch_gestures.advance(15_048.0))
		check.call(
			scroll.scroll_vertical <= after_drag,
			"Released fast drag continues with source fling inertia"
		)
	screen.hero_shop_panel.set_open(false)
	screen.touch_gestures.cancel()

	check.call(hero.items.add("dead_edge"), "Touch Forge fixture equips a source item")
	screen.forge_panel.set_open(true)
	await _settle(tree)
	var slots: Node = screen.forge_panel.find_child("ItemForgeSlots", true, false)
	var slot_button := slots.get_child(0) as Button
	var slot_point := slot_button.get_global_rect().get_center()
	_touch(screen, 6, slot_point, true, 16_000.0)
	screen._route_touch_actions(screen.touch_gestures.advance(16_451.0))
	check.call(
		hero.items.slots[0] == null,
		"Long press on an equipped Forge slot preserves source right-click drop"
	)
	_touch(screen, 6, slot_point, false, 16_500.0)
	await _settle(tree)
	check.call(hero.items.add("dead_edge"), "Touch Forge outside-click fixture re-equips")
	screen.forge_panel.set_open(true)
	_touch(screen, 6, Vector2(24, 24), true, 16_600.0)
	_touch(screen, 6, Vector2(24, 24), false, 16_650.0)
	check.call(
		not screen.forge_panel.visible,
		"Released touch outside Forge keeps source modal close behavior"
	)

	var gather: Button = screen.get_node("%GatherButton")
	var gather_rect := gather.get_global_rect()
	var gather_point := Vector2(gather_rect.get_center().x, gather_rect.position.y - 4.0)
	check.call(
		not gather_rect.has_point(gather_point),
		"Tactical touch probe starts outside the visual button"
	)
	_touch(screen, 7, gather_point, true, 17_000.0)
	_touch(screen, 8, hero_point, true, 17_010.0)
	check.call(
		screen._touch_tactical_claims.has(7) and screen.touch_gestures.points.has(8),
		"Independent fingers can hold tactical UI and touch the arena"
	)
	_touch(screen, 7, gather_point, false, 17_030.0)
	_cancel_touch(screen, 8, hero_point, 17_040.0)
	check.call(
		session.tactical_queue.size() == 2,
		"Tactical touch queues exact button_down/button_up edges"
	)
	session._physics_process(1.0 / 60.0)
	check.call(not world.tactical.hold_active(), "Tactical touch release cannot remain sticky")

	_touch(screen, 9, hero_point, true, 18_000.0)
	screen.touch_gestures.fling_velocity = 12.0
	screen.pause_match()
	check.call(
		(
			tree.paused
			and screen.touch_gestures.points.is_empty()
			and screen._touch_tactical_claims.is_empty()
			and is_zero_approx(screen.touch_gestures.fling_velocity)
		),
		"Pause cancels active touches, holds and fling state"
	)
	screen.resume_match()
	screen.get_node("%BackButton").pressed.emit()
	await _settle(tree)
	check.call(app.current_screen.name == "MainMenu", "Touch gesture scene exits cleanly")
	check.call(tree.get_node_count() == baseline, "Touch gesture lifecycle leaves no orphan nodes")


func _add_boss_shop_rows(world) -> void:
	var added := 0
	for hero_type in HERO_ROSTER:
		if not HERO_ROSTER[hero_type].is_boss_hero:
			continue
		if hero_type not in world.purchased_heroes:
			world.purchased_heroes.append(hero_type)
		added += 1
		if added >= 14:
			return


func _touch(screen, touch_id: int, position: Vector2, pressed: bool, now_ms: float) -> void:
	var event := InputEventScreenTouch.new()
	event.index = touch_id
	event.position = position
	event.pressed = pressed
	screen._handle_touch_event(event, now_ms)


func _cancel_touch(screen, touch_id: int, position: Vector2, now_ms: float) -> void:
	var event := InputEventScreenTouch.new()
	event.index = touch_id
	event.position = position
	event.pressed = false
	event.canceled = true
	screen._handle_touch_event(event, now_ms)


func _drag(screen, touch_id: int, position: Vector2, now_ms: float) -> void:
	var event := InputEventScreenDrag.new()
	event.index = touch_id
	event.position = position
	screen._handle_touch_event(event, now_ms)


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
