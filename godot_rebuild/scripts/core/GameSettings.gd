class_name GameSettings
extends RefCounted

## App-shell preferences only; never writes the Python progress/save slots.
const DEFAULTS := {
	"master_volume": 0.7,
	"sfx_volume": 0.6,
	"bgm_volume": 0.35,
	"ambient_volume": 0.25,
	"fps_limit": 60,
	"debug": false,
}
var values: Dictionary = DEFAULTS.duplicate()
var path := "user://godot_settings.cfg"
var last_error := OK


func load_values() -> void:
	var config := ConfigFile.new()
	last_error = config.load(path)
	if last_error != OK:
		return
	for key: String in DEFAULTS:
		var candidate: Variant = config.get_value("settings", key, DEFAULTS[key])
		if typeof(candidate) == typeof(DEFAULTS[key]):
			values[key] = candidate
		elif DEFAULTS[key] is float and candidate is int:
			values[key] = float(candidate)
	for key: String in ["master_volume", "sfx_volume", "bgm_volume", "ambient_volume"]:
		values[key] = clampf(values[key], 0.0, 1.0)
	if not values.fps_limit in [0, 30, 60, 120]:
		values.fps_limit = 60


func set_value(key: String, value: Variant) -> void:
	if not DEFAULTS.has(key) or typeof(value) != typeof(DEFAULTS[key]):
		return
	values[key] = value
	save()


func save() -> Error:
	var config := ConfigFile.new()
	for key: String in values:
		config.set_value("settings", key, values[key])
	last_error = config.save(path)
	return last_error


func effective_fps(touch_mode: bool) -> int:
	var limit: int = values.fps_limit
	var quality_cap := 60
	if limit == 0:
		return quality_cap
	return mini(limit, quality_cap) if touch_mode else limit
