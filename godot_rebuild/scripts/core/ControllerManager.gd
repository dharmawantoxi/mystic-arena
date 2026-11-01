class_name ControllerManager
extends Node

## Godot Input device adapter around ControllerCore. Emits semantic actions.
signal action_pressed(action: String)
signal cursor_moved(position: Vector2)
signal scroll_changed(value: float)
signal device_changed(connected: bool, device_name: String)

var core := ControllerCore.new()
var data := CoreData.new()
var device_id := -1
var device_name := ""
var enabled := true
var bounds := Rect2(0, 0, 1280, 720)


func _ready() -> void:
	Input.joy_connection_changed.connect(_on_joy_connection)
	rescan()


func rescan() -> void:
	var devices := Input.get_connected_joypads()
	if devices.is_empty():
		device_id = -1
		device_name = ""
		device_changed.emit(false, "")
		return
	device_id = devices[0]
	device_name = Input.get_joy_name(device_id)
	core.configure(data.data.get("rules", {}), device_name)
	device_changed.emit(true, device_name)


func _on_joy_connection(_device: int, _connected: bool) -> void:
	rescan()


func poll(delta: float) -> void:
	if not enabled or device_id < 0:
		return
	var axes: Dictionary = {}
	for axis in range(10):
		axes[axis] = Input.get_joy_axis(device_id, axis)
	var buttons: Dictionary = {}
	for button in range(21):
		buttons[button] = Input.is_joy_button_pressed(device_id, button)
	for action: String in core.update(axes, buttons, delta, bounds):
		action_pressed.emit(action)
	cursor_moved.emit(core.cursor)
	var scroll := core.scroll_value(axes)
	if absf(scroll) > 0.01:
		scroll_changed.emit(scroll)
	if core.rumble_timer > 0.0:
		Input.start_joy_vibration(device_id, 0.4, 0.6, 0.1)


func rumble(seconds: float) -> void:
	core.rumble(seconds)
	if device_id >= 0:
		Input.start_joy_vibration(device_id, 0.5, 0.7, seconds)
