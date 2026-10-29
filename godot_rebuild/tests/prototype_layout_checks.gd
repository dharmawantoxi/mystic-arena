extends RefCounted
## Playable-scene proof for the full-screen arena and compact overlay HUD.


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	screen.simulation.set_physics_process(false)
	var arena: Node2D = screen.get_node("Arena")
	var quality_runtime: Node = tree.root.get_node("AdaptiveQuality")
	var previous_quality := String(quality_runtime.get("quality_level"))
	quality_runtime.call("apply_quality", "low")
	arena._sync_dynamic_map_quality()
	check.call(
		String(arena.dynamic_map.quality.get("level", "")) == "low",
		"Android LOW quality profile reaches the live DynamicRenderer"
	)
	quality_runtime.call("apply_quality", previous_quality)
	arena._sync_dynamic_map_quality()
	var top_bar: Control = screen.get_node("HUD/TopBar")
	var bottom_bar: Control = screen.get_node("HUD/BottomBar")
	var tactical_panel: Control = screen.get_node("%TacticalPanel")
	var tactical_toggle: Button = screen.get_node("%TacticalToggleButton")
	var command_toggle: Button = screen.get_node("%CommandDockToggle")
	check.call(
		arena.position == Vector2.ZERO and arena.scale == Vector2.ONE,
		"Playable arena fills the 1280 by 720 logical viewport"
	)
	var top_rect := top_bar.get_global_rect()
	var bottom_rect := bottom_bar.get_global_rect()
	var compact_hud := (
		top_rect.end.x <= 1280.0
		and top_bar.get_rect().size.y <= 64.0
		and bottom_rect.end.y <= 720.0
		and bottom_bar.get_rect().size.y <= 180.0
		and bottom_bar.position.y >= 540.0
		and not bottom_bar.visible
		and command_toggle.visible
	)
	check.call(
		compact_hud,
		(
			"Compact HUD bounds top=%s bottom=%s sizes=%s/%s visible=%s/%s"
			% [
				top_rect,
				bottom_rect,
				top_bar.size,
				bottom_bar.size,
				bottom_bar.visible,
				command_toggle.visible
			]
		)
	)
	# Layer 9bv2: the source gold chip sits on the map at the top-left; the bar starts right of
	# it (and the badge below it) so neither covers the other.
	var gold_ops: Array = arena.gold_hud_draw_ops(screen.match_session.world)
	var chip: Array = gold_ops[1]["rect"]
	var badge: Array = gold_ops[10]["rect"]
	check.call(
		(
			arena.gold_hud_visible
			and top_rect.position.x >= float(chip[0] + chip[2]) + 8.0
			and top_rect.position.x >= float(badge[0] + badge[2]) + 8.0
		),
		"Gold chip %s and badge %s stay clear of the top bar %s" % [chip, badge, top_rect]
	)
	command_toggle.toggled.emit(true)
	check.call(
		bottom_bar.visible and command_toggle.text == "Tutup",
		"Command toggle opens the bottom dock"
	)
	command_toggle.toggled.emit(false)
	check.call(
		not bottom_bar.visible and command_toggle.text == "Kontrol",
		"Command toggle closes the bottom dock"
	)
	var tactical_rect := tactical_panel.get_global_rect()
	check.call(
		(
			not tactical_panel.visible
			and tactical_toggle.visible
			and tactical_rect.position.x >= 1000.0
			and tactical_rect.position.x + tactical_rect.size.x <= 1280.0
		),
		"Tactical commands start closed in a right-side dock"
	)
	tactical_toggle.toggled.emit(true)
	check.call(tactical_panel.visible, "Tactical toggle opens the dock over the arena")
	tactical_toggle.toggled.emit(false)
	check.call(not tactical_panel.visible, "Tactical toggle restores the unobstructed arena")

	screen._configure_mobile_hud(true, true)
	check.call(
		(
			not top_bar.visible
			and not bottom_bar.visible
			and not command_toggle.visible
			and not screen.mobile_pause_button.visible
		),
		"Android wide-screen layout replaces desktop bars with the source side dock"
	)
	screen._configure_mobile_hud(true, false)
	var mobile_pause: Button = screen.mobile_pause_button
	var pause_rect := mobile_pause.get_global_rect()
	var pause_hit_rect: Rect2 = screen._touch_button_rect(mobile_pause)
	check.call(
		(
			not top_bar.visible
			and not screen.get_node("HUD/TopBar/Row/Names").visible
			and not screen.get_node("%GoldLabel").visible
			and not screen.get_node("%TickLabel").visible
			and not screen.get_node("%GameSpeedSelector").visible
			and not screen.get_node("%PauseButton").visible
			and not screen.get_node("%BackButton").visible
			and not screen.get_node("%TacticalToggleButton").visible
			and not bottom_bar.visible
			and mobile_pause.visible
			and pause_rect == Rect2(34.0, 158.0, 52.0, 52.0)
			and pause_hit_rect == Rect2(20.0, 144.0, 80.0, 80.0)
		),
		"Android 16:9 matches pygame: source-positioned pause circle and 80 px target only"
	)
	screen._touch_tap(pause_rect.get_center())
	check.call(tree.paused, "Source-positioned Android pause button opens the pause screen")
	screen.resume_match()
	check.call(not tree.paused, "Android pause button resumes through the shared pause flow")

	screen.get_node("%BackButton").pressed.emit()
	await _settle(tree)
	check.call(app.current_screen.name == "MainMenu", "Prototype layout exits cleanly")
	check.call(tree.get_node_count() == baseline, "Prototype layout leaves no orphan controls")


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
