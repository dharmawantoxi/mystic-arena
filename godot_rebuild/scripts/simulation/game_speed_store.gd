extends RefCounted
## Small global preference store for the source game's simulation-speed setting.
## A corrupt value or unfinished backup is never overwritten automatically.

const DEFAULT_SPEED := 1.0
const MIN_SPEED := 0.5
const MAX_SPEED := 2.0
const PRESETS: Array[float] = [0.5, 1.0, 1.5, 2.0]
const PATH := "user://game_speed.json"
const VERSION := 1
const INVALID_SPEED := -1.0


static func is_valid_speed(value: float) -> bool:
	return is_finite(value) and value >= MIN_SPEED and value <= MAX_SPEED


static func decode_speed(text: String) -> float:
	var parser := JSON.new()
	if parser.parse(text) != OK:
		return INVALID_SPEED
	var parsed: Variant = parser.data
	if typeof(parsed) != TYPE_DICTIONARY or int(parsed.get("version", -1)) != VERSION:
		return INVALID_SPEED
	var raw_speed: Variant = parsed.get("speed", null)
	if typeof(raw_speed) not in [TYPE_FLOAT, TYPE_INT]:
		return INVALID_SPEED
	var speed := float(raw_speed)
	return speed if is_valid_speed(speed) else INVALID_SPEED


static func load_speed(path: String = PATH) -> float:
	return _read_speed(path) if FileAccess.file_exists(path) else DEFAULT_SPEED


static func save_speed(speed: float, path: String = PATH) -> bool:
	if not is_valid_speed(speed):
		return false
	var backup_path := path + ".bak"
	var temporary_path := path + ".tmp"
	if FileAccess.file_exists(backup_path):
		return false
	if FileAccess.file_exists(path) and _read_speed(path) == INVALID_SPEED:
		return false
	_remove(temporary_path)
	var file := FileAccess.open(temporary_path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify({"version": VERSION, "speed": speed}) + "\n")
	file.flush()
	file.close()
	if _read_speed(temporary_path) != speed:
		_remove(temporary_path)
		return false

	var had_current := FileAccess.file_exists(path)
	if had_current and _rename(path, backup_path) != OK:
		_remove(temporary_path)
		return false
	if _rename(temporary_path, path) != OK:
		if had_current:
			_rename(backup_path, path)
		_remove(temporary_path)
		return false
	if _read_speed(path) != speed:
		_remove(path)
		if had_current:
			_rename(backup_path, path)
		return false
	if had_current:
		_remove(backup_path)
	return true


static func _read_speed(path: String) -> float:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return INVALID_SPEED
	var text := file.get_as_text()
	file.close()
	return decode_speed(text)


static func _rename(source: String, destination: String) -> Error:
	return DirAccess.rename_absolute(
		ProjectSettings.globalize_path(source), ProjectSettings.globalize_path(destination)
	)


static func _remove(path: String) -> void:
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
