extends Node
## Applies the source user-selected render cap without changing fixed physics ticks.

signal limit_changed(requested: int, effective: int)

const Store = preload("res://scripts/settings/frame_rate_limit_store.gd")
const DESKTOP_TARGET_FPS := 60
const ANDROID_TARGET_FPS := 30

var settings_path := Store.PATH
var selected_limit := Store.DEFAULT_LIMIT
var effective_limit := Store.DEFAULT_LIMIT
var quality_target_fps := DESKTOP_TARGET_FPS
var touch_mode := false
var last_save_ok := true


func _ready() -> void:
	touch_mode = OS.has_feature("android")
	quality_target_fps = ANDROID_TARGET_FPS if touch_mode else DESKTOP_TARGET_FPS
	load_settings()


func load_settings(path: String = Store.PATH) -> int:
	settings_path = path
	selected_limit = Store.load_limit(settings_path)
	_apply_limit()
	return selected_limit


func set_limit(value: int) -> bool:
	if not Store.is_valid_limit(value):
		return false
	selected_limit = value
	_apply_limit()
	last_save_ok = Store.save_limit(selected_limit, settings_path)
	return true


func cycle_limit(direction: int) -> bool:
	if direction == 0:
		return false
	var index := Store.PRESETS.find(selected_limit)
	if index < 0:
		index = Store.PRESETS.find(Store.DEFAULT_LIMIT)
	var next_index := posmod(index + signi(direction), Store.PRESETS.size())
	return set_limit(Store.PRESETS[next_index])


func limit_label() -> String:
	return "Unlimited" if selected_limit == 0 else "%d FPS" % selected_limit


func set_quality_target_fps(value: int) -> void:
	if value < 0:
		return
	quality_target_fps = value
	_apply_limit()


func resolve_limit(limit: int, target_fps: int, is_touch: bool) -> int:
	if limit <= 0:
		return target_fps
	return mini(limit, target_fps) if is_touch else limit


func _apply_limit() -> void:
	effective_limit = resolve_limit(selected_limit, quality_target_fps, touch_mode)
	Engine.max_fps = effective_limit
	limit_changed.emit(selected_limit, effective_limit)
