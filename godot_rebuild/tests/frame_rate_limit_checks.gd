extends RefCounted
## Native tests for source presets, atomic preferences, and render-only cap semantics.

const Store = preload("res://scripts/settings/frame_rate_limit_store.gd")
const RuntimeScript = preload("res://scripts/settings/frame_rate_limit_runtime.gd")
const FIXTURE := "res://tests/fixtures/frame_rate_limit_source.json"
const TEST_PATH := "user://frame_rate_limit_native_test.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary, "frame-rate source fixture parses")
	if not fixture is Dictionary:
		return
	var presets_match := Store.PRESETS.size() == fixture.presets.size()
	if presets_match:
		for index in Store.PRESETS.size():
			presets_match = presets_match and Store.PRESETS[index] == int(fixture.presets[index])
	check.call(
		Store.DEFAULT_LIMIT == int(fixture.default) and presets_match,
		"native default and cycle presets match active Python settings"
	)
	check.call(
		(
			RuntimeScript.DESKTOP_TARGET_FPS == fixture.quality_targets.desktop_high
			and RuntimeScript.ANDROID_TARGET_FPS == fixture.quality_targets.android_low
		),
		"native platform fallback caps match Python startup quality targets"
	)
	check.call(
		(
			Store.decode_limit('{"version":1,"fps_limit":120}') == 120
			and Store.decode_limit('{"version":1,"fps_limit":120.0}') == 120
			and Store.decode_limit('{"version":1,"fps_limit":0}') == 0
		),
		"native decoder accepts only supported source values"
	)
	check.call(
		(
			Store.decode_limit('{"version":1,"fps_limit":90}') == Store.INVALID_LIMIT
			and Store.decode_limit('{"version":1,"fps_limit":120.5}') == Store.INVALID_LIMIT
			and Store.decode_limit('{"version":"1","fps_limit":120}') == Store.INVALID_LIMIT
			and Store.decode_limit("broken") == Store.INVALID_LIMIT
		),
		"native decoder rejects unknown values, numeric type drift, and corruption"
	)

	_remove_test_files()
	check.call(Store.save_limit(120, TEST_PATH), "native store writes a valid frame limit")
	check.call(
		(
			Store.load_limit(TEST_PATH) == 120
			and not FileAccess.file_exists(TEST_PATH + ".tmp")
			and not FileAccess.file_exists(TEST_PATH + ".bak")
		),
		"atomic frame-limit save verifies final data and removes transaction files"
	)
	check.call(Store.save_limit(30, TEST_PATH), "native store atomically replaces valid settings")
	check.call(Store.load_limit(TEST_PATH) == 30, "replaced frame-limit setting reloads")
	check.call(not Store.save_limit(90, TEST_PATH), "unsupported frame limit cannot be saved")

	var corrupt := FileAccess.open(TEST_PATH, FileAccess.WRITE)
	corrupt.store_string("broken source setting")
	corrupt.close()
	check.call(not Store.save_limit(60, TEST_PATH), "corrupt preferences are never overwritten")
	check.call(
		FileAccess.get_file_as_string(TEST_PATH) == "broken source setting",
		"corrupt frame-limit bytes remain intact after a rejected save"
	)
	_remove_test_files()
	var backup := FileAccess.open(TEST_PATH + ".bak", FileAccess.WRITE)
	backup.store_string("unfinished transaction")
	backup.close()
	check.call(not Store.save_limit(60, TEST_PATH), "unfinished backup blocks frame-limit writes")
	_remove_test_files()

	var tree := Engine.get_main_loop() as SceneTree
	var runtime: Variant = tree.root.get_node_or_null("FrameRateLimit")
	check.call(runtime != null, "frame-rate runtime autoload is available")
	if runtime == null:
		return
	var old_path: String = String(runtime.settings_path)
	var old_quality_target := int(runtime.quality_target_fps)
	var speed_runtime: Variant = tree.root.get_node("GameSpeed")
	var old_speed := float(speed_runtime.get("speed"))
	var old_ticks := Engine.physics_ticks_per_second
	runtime.load_settings(TEST_PATH)
	check.call(
		runtime.selected_limit == Store.DEFAULT_LIMIT, "missing native setting uses source default"
	)
	check.call(runtime.set_limit(120), "runtime accepts a valid user-selected cap")
	check.call(
		Engine.max_fps == runtime.effective_limit and Store.load_limit(TEST_PATH) == 120,
		"runtime applies and persists the platform-effective render cap"
	)
	runtime.set_quality_target_fps(30)
	runtime.set_limit(0)
	check.call(
		Engine.max_fps == 30 and Store.load_limit(TEST_PATH) == 0,
		"quality-target updates recalculate unlimited and touch-clamped render caps"
	)
	runtime.set_quality_target_fps(old_quality_target)
	runtime.set_limit(120)
	check.call(
		(
			runtime.resolve_limit(0, 60, false) == 60
			and runtime.resolve_limit(120, 30, true) == 30
			and runtime.resolve_limit(120, 60, false) == 120
		),
		"effective cap matches source unlimited fallback and touch-mode clamp"
	)
	check.call(
		(
			Engine.physics_ticks_per_second == old_ticks
			and is_equal_approx(float(speed_runtime.get("speed")), old_speed)
		),
		"render FPS changes leave 60 Hz physics and GameSpeed untouched"
	)
	runtime.load_settings(old_path)
	_remove_test_files()


func _remove_test_files() -> void:
	for path in [TEST_PATH, TEST_PATH + ".bak", TEST_PATH + ".tmp"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
