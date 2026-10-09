extends RefCounted
## Atomic, corruption-guarded persistence for the global source language setting.

const DEFAULT_LANGUAGE := "id"
const LANGUAGES: Array[String] = ["id", "en"]
const PATH := "user://language_v1.json"
const VERSION := 1
const INVALID_LANGUAGE := ""


static func is_valid_language(language: String) -> bool:
	return LANGUAGES.has(language)


static func decode_language(text: String) -> String:
	var parser := JSON.new()
	if parser.parse(text) != OK:
		return INVALID_LANGUAGE
	var parsed: Variant = parser.data
	if typeof(parsed) != TYPE_DICTIONARY:
		return INVALID_LANGUAGE
	var raw_version: Variant = parsed.get("version", null)
	if typeof(raw_version) not in [TYPE_INT, TYPE_FLOAT] or float(raw_version) != float(VERSION):
		return INVALID_LANGUAGE
	var raw_language: Variant = parsed.get("language", null)
	if typeof(raw_language) != TYPE_STRING:
		return INVALID_LANGUAGE
	var language := String(raw_language)
	return language if is_valid_language(language) else INVALID_LANGUAGE


static func load_language(path: String = PATH) -> String:
	if not FileAccess.file_exists(path):
		return DEFAULT_LANGUAGE
	var language := _read_language(path)
	return language if is_valid_language(language) else DEFAULT_LANGUAGE


static func save_language(language: String, path: String = PATH) -> bool:
	if not is_valid_language(language):
		return false
	var backup_path := path + ".bak"
	var temporary_path := path + ".tmp"
	if FileAccess.file_exists(backup_path):
		return false
	if FileAccess.file_exists(path) and not is_valid_language(_read_language(path)):
		return false
	_remove(temporary_path)
	var file := FileAccess.open(temporary_path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify({"version": VERSION, "language": language}) + "\n")
	file.flush()
	file.close()
	if _read_language(temporary_path) != language:
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
	if _read_language(path) != language:
		_remove(path)
		if had_current:
			_rename(backup_path, path)
		return false
	if had_current:
		_remove(backup_path)
	return true


static func _read_language(path: String) -> String:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return INVALID_LANGUAGE
	var text := file.get_as_text()
	file.close()
	return decode_language(text)


static func _rename(source: String, destination: String) -> Error:
	return DirAccess.rename_absolute(
		ProjectSettings.globalize_path(source), ProjectSettings.globalize_path(destination)
	)


static func _remove(path: String) -> void:
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
