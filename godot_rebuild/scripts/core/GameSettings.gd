class_name GameSettings
extends RefCounted

## Native global settings port. Writes only user://godot_settings.cfg;
## Python saves/settings.json is never overwritten.
const DEFAULTS := {
	"master_volume": 0.7,
	"sfx_volume": 0.6,
	"bgm_volume": 0.35,
	"ambient_volume": 0.25,
	"voice_volume": 0.5,
	"difficulty": "normal",
	"screen_shake_enabled": false,
	"damage_numbers_enabled": true,
	"game_speed": 1.0,
	"fps_limit": 60,
	"language": "id",
	"input_mode": "keyboard",
	"debug": false,
}
const DIFFICULTY_MODES := ["easy", "normal", "hard"]
const SPEEDS := [0.5, 1.0, 1.5, 2.0]
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
	_normalize()


func _normalize() -> void:
	for key: String in [
		"master_volume", "sfx_volume", "bgm_volume", "ambient_volume", "voice_volume"
	]:
		values[key] = clampf(float(values[key]), 0.0, 1.0)
	if not values.difficulty in DIFFICULTY_MODES:
		values.difficulty = "normal"
	if not values.language in ["id", "en"]:
		values.language = "id"
	if not values.input_mode in ["keyboard", "controller"]:
		values.input_mode = "keyboard"
	if not values.fps_limit in [0, 30, 60, 120]:
		values.fps_limit = 60
	values.game_speed = clampf(float(values.game_speed), 0.5, 2.0)


func set_value(key: String, value: Variant) -> void:
	if not DEFAULTS.has(key):
		return
	if DEFAULTS[key] is float and value is int:
		value = float(value)
	elif DEFAULTS[key] is int and value is float and value == floorf(value):
		value = int(value)
	if typeof(value) != typeof(DEFAULTS[key]):
		return
	values[key] = value
	_normalize()
	save()


func cycle_difficulty(direction := 1) -> String:
	var index := DIFFICULTY_MODES.find(str(values.difficulty))
	if index < 0:
		index = 1
	var step := -1 if direction < 0 else 1
	values.difficulty = DIFFICULTY_MODES[(index + step) % DIFFICULTY_MODES.size()]
	save()
	return str(values.difficulty)


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


func difficulty_label() -> String:
	return str(values.difficulty).to_upper()


func speed_label() -> String:
	return "%.1fx" % float(values.game_speed)
