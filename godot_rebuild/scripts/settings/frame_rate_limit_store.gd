extends RefCounted
## Atomic, corruption-guarded native storage for the source FPS-limit preference.

const DEFAULT_LIMIT := 60
const PRESETS: Array[int] = [30, 60, 120, 0]
const PATH := "user://frame_rate_limit_v1.json"
const VERSION := 1
const INVALID_LIMIT := -1


static func is_valid_limit(value: int) -> bool:
	return PRESETS.has(value)


static func decode_limit(text: String) -> int:
	var parser := JSON.new()
	if parser.parse(text) != OK:
		return INVALID_LIMIT
	var parsed: Variant = parser.data
	if typeof(parsed) != TYPE_DICTIONARY:
		return INVALID_LIMIT
	var raw_version: Variant = parsed.get("version", null)
	if typeof(raw_version) not in [TYPE_INT, TYPE_FLOAT] or float(raw_version) != float(VERSION):
		return INVALID_LIMIT
	var raw_limit: Variant = parsed.get("fps_limit", null)
	if typeof(raw_limit) not in [TYPE_INT, TYPE_FLOAT]:
		return INVALID_LIMIT
	var numeric_limit := float(raw_limit)
	if numeric_limit not in [0.0, 30.0, 60.0, 120.0]:
		return INVALID_LIMIT
	var limit := int(numeric_limit)
	return limit if is_valid_limit(limit) else INVALID_LIMIT


static func load_limit(path: String = PATH) -> int:
	if not FileAccess.file_exists(path):
		return DEFAULT_LIMIT
	var limit := _read_limit(path)
	return limit if is_valid_limit(limit) else DEFAULT_LIMIT


static func save_limit(limit: int, path: String = PATH) -> bool:
	if not is_valid_limit(limit):
		return false
	var backup_path := path + ".bak"
	var temporary_path := path + ".tmp"
	if FileAccess.file_exists(backup_path):
		return false
	if FileAccess.file_exists(path) and not is_valid_limit(_read_limit(path)):
		return false
	_remove(temporary_path)
	var file := FileAccess.open(temporary_path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify({"version": VERSION, "fps_limit": limit}) + "\n")
	file.flush()
	file.close()
	if _read_limit(temporary_path) != limit:
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
	if _read_limit(path) != limit:
		_remove(path)
		if had_current:
			_rename(backup_path, path)
		return false
	if had_current:
		_remove(backup_path)
	return true


static func _read_limit(path: String) -> int:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return INVALID_LIMIT
	var text := file.get_as_text()
	file.close()
	return decode_limit(text)


static func _rename(source: String, destination: String) -> Error:
	return DirAccess.rename_absolute(
		ProjectSettings.globalize_path(source), ProjectSettings.globalize_path(destination)
	)


static func _remove(path: String) -> void:
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
