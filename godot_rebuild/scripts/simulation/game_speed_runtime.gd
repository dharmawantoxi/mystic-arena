extends Node
## Source Game.update pacing, expressed as whole authoritative physics ticks.

signal speed_changed(value: float)

const Store = preload("res://scripts/simulation/game_speed_store.gd")
const SPEEDS: Array[float] = Store.PRESETS

var settings_path := Store.PATH
var speed := Store.DEFAULT_SPEED
var slow_skip_counter := 0
var last_save_ok := true


func _ready() -> void:
	speed = Store.load_speed(settings_path)


func speed_index() -> int:
	for index in range(SPEEDS.size()):
		if is_equal_approx(speed, SPEEDS[index]):
			return index
	return 1


func set_speed_index(index: int) -> bool:
	if index < 0 or index >= SPEEDS.size():
		return false
	return set_speed(SPEEDS[index])


func set_speed(value: float) -> bool:
	if not is_finite(value):
		return false
	speed = clampf(value, Store.MIN_SPEED, Store.MAX_SPEED)
	last_save_ok = Store.save_speed(speed, settings_path)
	speed_changed.emit(speed)
	return true


func ticks_for_physics_frame(force_normal_speed: bool = false) -> int:
	# The Python Game.update skips its multiplier during level/boss intro.
	if force_normal_speed:
		return 1
	if speed > 1.0:
		# Keep the active Python behavior: int(1.5) - 1 is zero, so 1.5x
		# currently advances one gameplay tick (rather than 1.5 ticks).
		return int(speed)
	if speed < 1.0:
		slow_skip_counter += 1
		if slow_skip_counter % 2 == 0:
			return 0
	return 1


func reset_match_clock() -> void:
	slow_skip_counter = 0
