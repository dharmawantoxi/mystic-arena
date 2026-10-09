extends RefCounted
## Exercises persisted FPS control through MainMenu and a live prototype match.

const Store = preload("res://scripts/settings/frame_rate_limit_store.gd")
const TEST_PATH := "user://frame_rate_limit_scene_test.json"


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var runtime: Variant = tree.root.get_node_or_null("FrameRateLimit")
	check.call(runtime != null, "playable menu scene has the frame-rate runtime")
	if runtime == null:
		return
	var original_path := String(runtime.settings_path)
	var speed_runtime: Variant = tree.root.get_node("GameSpeed")
	var old_speed := float(speed_runtime.get("speed"))
	var old_ticks := Engine.physics_ticks_per_second
	_remove_test_files()
	runtime.load_settings(TEST_PATH)

	var menu = app.current_screen
	var panel: Control = menu.get("audio_settings_panel")
	check.call(
		menu.name == "MainMenu" and panel != null, "MainMenu exposes the shared settings panel"
	)
	if panel == null:
		_restore(runtime, original_path)
		return
	menu.get_node("%SettingsButton").pressed.emit()
	await _settle(tree)
	var value := panel.find_child("FrameRateValue", true, false) as Label
	var next := panel.find_child("FrameRateNext", true, false) as Button
	var previous := panel.find_child("FrameRatePrevious", true, false) as Button
	check.call(
		panel.visible and value != null and next != null and previous != null,
		"playable Settings panel exposes previous/next FPS controls"
	)
	if value != null and next != null and previous != null:
		check.call(value.text == "60 FPS", "missing frame-limit file displays source default")
		next.pressed.emit()
		check.call(
			(
				runtime.selected_limit == 120
				and value.text == "120 FPS"
				and Engine.max_fps == runtime.effective_limit
			),
			"next control applies the source 120 FPS cap immediately"
		)
		next.pressed.emit()
		check.call(
			(
				runtime.selected_limit == 0
				and value.text == "Unlimited"
				and Engine.max_fps == runtime.quality_target_fps
			),
			"zero preset follows the source quality-target fallback"
		)
		next.pressed.emit()
		check.call(
			runtime.selected_limit == 30 and value.text == "30 FPS",
			"FPS presets wrap in the source order"
		)
		previous.pressed.emit()
		check.call(
			runtime.selected_limit == 0 and Store.load_limit(TEST_PATH) == 0,
			"previous control wraps and persists the unlimited preference"
		)
	check.call(
		(
			Engine.physics_ticks_per_second == old_ticks
			and is_equal_approx(float(speed_runtime.get("speed")), old_speed)
		),
		"render limit control leaves fixed ticks and GameSpeed unchanged"
	)
	var close_button := panel.find_child("CloseButton", true, false) as Button
	if close_button != null:
		close_button.pressed.emit()
	check.call(not panel.visible, "settings back closes after the frame-rate change")

	app.start_prototype()
	await _settle(tree)
	check.call(
		app.current_screen.name == "PrototypeMatch", "FPS preference follows into playable combat"
	)
	var screen = app.current_screen
	var simulation = screen.simulation
	var ticks_before: int = simulation.world.tick_count
	await tree.physics_frame
	await tree.physics_frame
	check.call(
		(
			Engine.max_fps == runtime.effective_limit
			and simulation.world.tick_count > ticks_before
			and Engine.physics_ticks_per_second == old_ticks
		),
		"render cap applies in combat while authoritative physics keeps advancing"
	)
	app.show_menu()
	await _settle(tree)
	check.call(app.current_screen.name == "MainMenu", "FPS playable-scene check exits cleanly")
	_restore(runtime, original_path)


func _restore(runtime: Variant, path: String) -> void:
	runtime.load_settings(path)
	_remove_test_files()


func _remove_test_files() -> void:
	for path in [TEST_PATH, TEST_PATH + ".bak", TEST_PATH + ".tmp"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
