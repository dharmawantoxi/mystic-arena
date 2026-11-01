class_name GameplayPort
extends Control

## Implement this contract in a native gameplay scene and assign Main.game_scene.
## No Python code is executed by Godot. See docs/GODOT_MAIN_MIGRATION.md.
signal next_level_requested
signal replay_requested
signal menu_requested
signal pause_requested

var level_number := 1
var is_replay := false


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func configure(level: int, replay := false) -> void:
	level_number = level
	is_replay = replay


func combat_ready() -> bool:
	return false


func simulation_step() -> void:
	pass


func cinematic_active() -> bool:
	return false


func skip_cinematic() -> void:
	pass


func pointer_action(_action: Dictionary) -> void:
	pass


func key_pressed(_key: Key) -> void:
	pass


func key_released(_key: Key) -> void:
	pass


func hud_action(_action: String) -> void:
	pass


func hold_begin(_action: String) -> void:
	pass


func hold_end(_action: String) -> void:
	pass


func release_all_holds() -> void:
	pass


func toggle_review(_hero: String) -> void:
	pass
