extends RefCounted
## Corruption-guarded preferences for the source screen-shake and damage-number toggles.

const PATH := "user://presentation_settings_v1.json"
const VERSION := 1
const INVALID := {}


static func defaults() -> Dictionary:
	return {"screen_shake": false, "damage_numbers": true}


static func decode_settings(text: String) -> Dictionary:
	var parser := JSON.new()
	if parser.parse(text) != OK:
		return INVALID.duplicate()
	var parsed: Variant = parser.data
	if typeof(parsed) != TYPE_DICTIONARY:
		return INVALID.duplicate()
	var row: Dictionary = parsed
	var version: Variant = row.get("version", null)
	if typeof(version) not in [TYPE_INT, TYPE_FLOAT] or float(version) != float(VERSION):
		return INVALID.duplicate()
	var shake: Variant = row.get("screen_shake", null)
	var damage: Variant = row.get("damage_numbers", null)
	if typeof(shake) != TYPE_BOOL or typeof(damage) != TYPE_BOOL:
		return INVALID.duplicate()
	return {"screen_shake": shake, "damage_numbers": damage}


static func load_settings(path: String = PATH) -> Dictionary:
	if not FileAccess.file_exists(path):
		return defaults()
	var decoded := _read_settings(path)
	return decoded if not decoded.is_empty() else defaults()


static func save_settings(settings: Dictionary, path: String = PATH) -> bool:
	if not _valid_settings(settings):
		return false
	var backup_path := path + ".bak"
	var temporary_path := path + ".tmp"
	if FileAccess.file_exists(backup_path):
		return false
	if FileAccess.file_exists(path) and _read_settings(path).is_empty():
		return false
	_remove(temporary_path)
	var file := FileAccess.open(temporary_path, FileAccess.WRITE)
	if file == null:
		return false
	(
		file
		. store_string(
			(
				(
					JSON
					. stringify(
						{
							"version": VERSION,
							"screen_shake": bool(settings.screen_shake),
							"damage_numbers": bool(settings.damage_numbers),
						}
					)
				)
				+ "\n"
			)
		)
	)
	file.flush()
	file.close()
	if not _read_settings(temporary_path).has("screen_shake"):
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
	var verified := _read_settings(path)
	if not _valid_settings(verified):
		_remove(path)
		if had_current:
			_rename(backup_path, path)
		return false
	if had_current:
		_remove(backup_path)
	return true


static func _valid_settings(settings: Dictionary) -> bool:
	return (
		settings.has("screen_shake")
		and settings.has("damage_numbers")
		and typeof(settings.screen_shake) == TYPE_BOOL
		and typeof(settings.damage_numbers) == TYPE_BOOL
	)


static func _read_settings(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return INVALID.duplicate()
	var text := file.get_as_text()
	file.close()
	return decode_settings(text)


static func _rename(source: String, destination: String) -> Error:
	return DirAccess.rename_absolute(
		ProjectSettings.globalize_path(source), ProjectSettings.globalize_path(destination)
	)


static func _remove(path: String) -> void:
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
