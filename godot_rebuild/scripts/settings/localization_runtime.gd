extends Node
## Global two-language runtime backed by the source localization catalog.

signal language_changed(language: String)

const Store = preload("res://scripts/settings/language_store.gd")
const CATALOG_PATH := "res://data/localization_catalog.json"

var language := Store.DEFAULT_LANGUAGE
var settings_path := Store.PATH
var last_save_ok := true
var _catalog: Dictionary = {}


func _ready() -> void:
	_load_catalog()
	load_settings()


func load_settings(path: String = Store.PATH) -> String:
	settings_path = path
	language = Store.load_language(settings_path)
	return language


func set_language(value: String) -> bool:
	if not Store.is_valid_language(value):
		return false
	language = value
	last_save_ok = Store.save_language(language, settings_path)
	language_changed.emit(language)
	return true


func cycle_language(direction: int) -> bool:
	if direction == 0:
		return false
	var index := Store.LANGUAGES.find(language)
	if index < 0:
		index = Store.LANGUAGES.find(Store.DEFAULT_LANGUAGE)
	var next_index := posmod(index + signi(direction), Store.LANGUAGES.size())
	return set_language(Store.LANGUAGES[next_index])


func get_language_label(code: String = "") -> String:
	var selected := language if code.is_empty() else code
	var labels: Dictionary = _catalog.get("language_labels", {})
	return String(labels.get(selected, labels.get(Store.DEFAULT_LANGUAGE, "Bahasa Indonesia")))


func translate(key: String, values: Dictionary = {}) -> String:
	var texts: Dictionary = _catalog.get("texts", {})
	var fallback: Dictionary = texts.get(Store.DEFAULT_LANGUAGE, {})
	var active: Dictionary = texts.get(language, fallback)
	var template: Variant = active.get(key, null)
	if template == null:
		template = fallback.get(key, key)
	var result := String(template)
	if values.is_empty():
		return result
	var formatter := RegEx.new()
	if formatter.compile("\\{([A-Za-z_][A-Za-z0-9_]*)\\}") != OK:
		return result
	var placeholders := formatter.search_all(result)
	for match_result in placeholders:
		if not values.has(match_result.get_string(1)):
			return result
	for match_result in placeholders:
		result = result.replace(match_result.get_string(0), str(values[match_result.get_string(1)]))
	return result


func _load_catalog() -> void:
	var parser := JSON.new()
	if parser.parse(FileAccess.get_file_as_string(CATALOG_PATH)) == OK:
		var parsed: Variant = parser.data
		if typeof(parsed) == TYPE_DICTIONARY:
			_catalog = parsed
