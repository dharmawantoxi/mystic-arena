extends RefCounted
## Verifies adaptive quality changes the real frame cap in a playable match.

const Controller = preload("res://scripts/settings/adaptive_quality_controller.gd")
const Store = preload("res://scripts/settings/frame_rate_limit_store.gd")
const TEST_PATH := "user://adaptive_quality_scene_test.json"


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var quality: Variant = tree.root.get_node_or_null("AdaptiveQuality")
	var frame_limiter: Variant = tree.root.get_node_or_null("FrameRateLimit")
	check.call(
		quality != null and frame_limiter != null,
		"playable app owns adaptive-quality and frame-limit runtimes"
	)
	if quality == null or frame_limiter == null:
		return

	var original_path := String(frame_limiter.settings_path)
	var original_quality := String(quality.quality_level)
	var original_enabled: bool = bool(quality.controller.enabled)
	quality.controller.enabled = false
	var speed_runtime: Variant = tree.root.get_node("GameSpeed")
	var original_speed := float(speed_runtime.get("speed"))
	var original_ticks := Engine.physics_ticks_per_second
	_remove_test_files()
	frame_limiter.load_settings(TEST_PATH)
	frame_limiter.set_limit(0)
	quality.apply_quality(Controller.LOW)
	check.call(
		(
			quality.target_fps == 30
			and frame_limiter.quality_target_fps == 30
			and Store.load_limit(TEST_PATH) == 0
			and Engine.max_fps == 30
		),
		"Low quality updates unlimited FPS preference to the source 30 FPS target"
	)

	check.call(
		app.current_screen.name == "MainMenu",
		"adaptive-quality playable-scene test starts from MainMenu"
	)
	app.start_prototype()
	await _settle(tree)
	check.call(app.current_screen.name == "PrototypeMatch", "adaptive quality enters live combat")
	if app.current_screen.name == "PrototypeMatch":
		var screen = app.current_screen
		var simulation = screen.simulation
		var tick_before: int = simulation.world.tick_count
		await tree.physics_frame
		await tree.physics_frame
		check.call(
			(
				Engine.max_fps == frame_limiter.effective_limit
				and simulation.world.tick_count > tick_before
				and Engine.physics_ticks_per_second == original_ticks
				and is_equal_approx(float(speed_runtime.get("speed")), original_speed)
			),
			"adaptive render cap leaves authoritative combat ticks and GameSpeed unchanged"
		)
	app.show_menu()
	await _settle(tree)
	check.call(app.current_screen.name == "MainMenu", "adaptive-quality scene returns to menu")
	_restore(quality, frame_limiter, original_quality, original_path, original_enabled)


func _restore(
	quality: Variant,
	frame_limiter: Variant,
	quality_level: String,
	settings_path: String,
	enabled: bool
) -> void:
	quality.apply_quality(quality_level)
	quality.controller.enabled = enabled
	frame_limiter.load_settings(settings_path)
	_remove_test_files()


func _remove_test_files() -> void:
	for path in [TEST_PATH, TEST_PATH + ".bak", TEST_PATH + ".tmp"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
