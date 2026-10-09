extends RefCounted

const Runtime = preload("res://scripts/simulation/game_speed_runtime.gd")
const Store = preload("res://scripts/simulation/game_speed_store.gd")


func run(check: Callable) -> void:
	check.call(Runtime.SPEEDS == [0.5, 1.0, 1.5, 2.0], "source speed presets are unchanged")
	var runtime = Runtime.new()
	var path := "user://game_speed_checks_%d.json" % Time.get_ticks_usec()
	runtime.settings_path = path + ".runtime"
	check.call(
		runtime.set_speed(2.5) and runtime.speed == 2.0, "source setter clamps high values to 2.0x"
	)
	check.call(
		runtime.set_speed(0.1) and runtime.speed == 0.5, "source setter clamps low values to 0.5x"
	)
	var cases := [
		{"speed": 0.5, "ticks": [1, 0, 1, 0]},
		{"speed": 1.0, "ticks": [1, 1, 1, 1]},
		{"speed": 1.5, "ticks": [1, 1, 1, 1]},
		{"speed": 2.0, "ticks": [2, 2, 2, 2]},
	]
	for row in cases:
		runtime.speed = row.speed
		runtime.reset_match_clock()
		var observed: Array[int] = []
		for _frame in range(4):
			observed.append(runtime.ticks_for_physics_frame())
		check.call(observed == row.ticks, "fixed-tick policy for %.1fx" % row.speed)
	check.call(runtime.speed_index() == 3, "2.0x resolves to the final option")
	check.call(not runtime.set_speed_index(-1), "negative speed option is rejected")
	check.call(not runtime.set_speed_index(4), "out-of-range speed option is rejected")
	runtime.speed = 0.5
	runtime.reset_match_clock()
	runtime.ticks_for_physics_frame()
	var slow_counter: int = runtime.slow_skip_counter
	check.call(
		runtime.ticks_for_physics_frame(true) == 1 and runtime.slow_skip_counter == slow_counter,
		"normal-speed cinematic tick does not consume half-speed phase"
	)

	var runtime_path := path + ".runtime"
	check.call(FileAccess.file_exists(runtime_path), "runtime speed setter writes its preference")
	check.call(Store.load_speed(runtime_path) == 0.5, "runtime clamp persists the clamped value")
	check.call(Store.load_speed(path) == Store.DEFAULT_SPEED, "missing setting uses source default")
	check.call(Store.save_speed(2.0, path), "atomic speed preference write succeeds")
	check.call(Store.load_speed(path) == 2.0, "saved setting round-trips")
	check.call(
		not FileAccess.file_exists(path + ".tmp") and not FileAccess.file_exists(path + ".bak"),
		"successful write leaves no transaction debris"
	)
	var corrupt := FileAccess.open(path, FileAccess.WRITE)
	corrupt.store_string("{truncated")
	corrupt.close()
	var corrupt_reader := FileAccess.open(path, FileAccess.READ)
	var corrupted_text := corrupt_reader.get_as_text()
	corrupt_reader.close()
	check.call(
		Store.load_speed(path) == Store.DEFAULT_SPEED,
		"corrupt setting falls back without parsing data"
	)
	check.call(not Store.save_speed(0.5, path), "corrupt preference cannot be overwritten")
	var current_reader := FileAccess.open(path, FileAccess.READ)
	var still_corrupt := current_reader.get_as_text()
	current_reader.close()
	check.call(still_corrupt == corrupted_text, "corruption guard preserves original bytes")
	var backup := FileAccess.open(path + ".bak", FileAccess.WRITE)
	backup.store_string("recovery required")
	backup.close()
	check.call(not Store.save_speed(1.0, path), "unfinished backup blocks preference overwrite")
	_remove(path)
	_remove(path + ".tmp")
	_remove(path + ".bak")
	_remove(runtime_path)
	_remove(runtime_path + ".tmp")
	_remove(runtime_path + ".bak")
	runtime.free()


func _remove(path: String) -> void:
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
