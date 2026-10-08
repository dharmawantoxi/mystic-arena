extends Control
## Source-faithful gamepad adapter for the playable match.
##
## Godot normalizes Xbox/PlayStation/generic devices to the same JoyButton and
## JoyAxis vocabulary, so this layer ports ControllerManager's behavior rather
## than its SDL device-index guesses: accelerated virtual cursor, edge actions,
## D-pad repeat, trigger edges, right-stick scroll, snapping and rumble.

signal action_requested(action: String)

const FRAME_RATE := 60.0
const CURSOR_SPEED := 12.0
const CURSOR_MAX_SPEED := 25.0
const CURSOR_ACCELERATION := 1.5
const DEADZONE := 0.25
const HAT_REPEAT_DELAY := 22
const HAT_REPEAT_RATE := 5
const SCROLL_STEP := 1.0
const SCROLL_SPEED := 0.55
const SCROLL_DEADZONE := 0.18
const TRIGGER_THRESHOLD := 0.5

const BUTTON_ACTIONS := {
	JOY_BUTTON_A: "confirm",
	JOY_BUTTON_B: "cancel",
	JOY_BUTTON_X: "skill_q",
	JOY_BUTTON_Y: "skill_w",
	JOY_BUTTON_LEFT_SHOULDER: "skill_e",
	JOY_BUTTON_RIGHT_SHOULDER: "skill_r",
	JOY_BUTTON_START: "start",
	JOY_BUTTON_BACK: "back",
	JOY_BUTTON_LEFT_STICK: "stick_left",
	JOY_BUTTON_RIGHT_STICK: "stick_right",
}
const DPAD_ACTIONS := {
	JOY_BUTTON_DPAD_UP: "dpad_up",
	JOY_BUTTON_DPAD_DOWN: "dpad_down",
	JOY_BUTTON_DPAD_LEFT: "dpad_left",
	JOY_BUTTON_DPAD_RIGHT: "dpad_right",
}
const LABELS := {
	"xbox":
	{
		"confirm": "A",
		"cancel": "B",
		"skill_q": "X",
		"skill_w": "Y",
		"skill_e": "LB",
		"skill_r": "RB",
		"start": "MENU",
		"back": "VIEW",
		"left_trigger": "LT",
		"right_trigger": "RT",
		"stick_left": "L3",
		"stick_right": "R3",
		"dpad": "D-PAD",
		"left_stick": "L-STICK",
		"right_stick": "R-STICK",
	},
	"ps":
	{
		"confirm": "X",
		"cancel": "O",
		"skill_q": "SQUARE",
		"skill_w": "TRIANGLE",
		"skill_e": "L1",
		"skill_r": "R1",
		"start": "OPTIONS",
		"back": "SHARE",
		"left_trigger": "L2",
		"right_trigger": "R2",
		"stick_left": "L3",
		"stick_right": "R3",
		"dpad": "D-PAD",
		"left_stick": "L-STICK",
		"right_stick": "R-STICK",
	},
	"generic":
	{
		"confirm": "BTN1",
		"cancel": "BTN2",
		"skill_q": "BTN3",
		"skill_w": "BTN4",
		"skill_e": "L1",
		"skill_r": "R1",
		"start": "START",
		"back": "SELECT",
		"left_trigger": "L2",
		"right_trigger": "R2",
		"stick_left": "L3",
		"stick_right": "R3",
		"dpad": "D-PAD",
		"left_stick": "L-STICK",
		"right_stick": "R-STICK",
	},
}
const ACTION_BINDINGS := {
	"skip": "confirm",
	"shop": "left_trigger",
	"move_hero": "right_trigger",
	"select": "confirm",
	"back": "cancel",
	"pause": "start",
	"to_menu": "back",
	"replay": "skill_q",
	"next_level": "skill_r",
	"fps": "stick_left",
	"snap": "stick_right",
	"scroll": "right_stick",
	"cursor": "left_stick",
}

@export var logical_size := Vector2(1280.0, 720.0)

var active := false
var device_id := -1
var controller_type := "generic"
var cursor_position := Vector2(640.0, 360.0)
var rumble_requests := 0

var _left_stick := Vector2.ZERO
var _right_stick_y := 0.0
var _left_trigger_pressed := false
var _right_trigger_pressed := false
var _button_pressed: Dictionary = {}
var _dpad_pressed := {
	JOY_BUTTON_DPAD_UP: false,
	JOY_BUTTON_DPAD_DOWN: false,
	JOY_BUTTON_DPAD_LEFT: false,
	JOY_BUTTON_DPAD_RIGHT: false,
}
var _hat_hold_frames := 0
var _hat_repeat_direction := Vector2i.ZERO
var _scroll_accumulator := 0.0
var _frame_accumulator := 0.0
var _hover_rect := Rect2()
var _has_hover := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	if not Input.joy_connection_changed.is_connected(_on_joy_connection_changed):
		Input.joy_connection_changed.connect(_on_joy_connection_changed)
	queue_redraw()


func activate(controller_device: int = 0, forced_type: String = "") -> void:
	var first_activation := not active
	active = true
	device_id = controller_device
	if not forced_type.is_empty():
		controller_type = forced_type
	else:
		controller_type = _detect_controller_type(Input.get_joy_name(controller_device))
	if first_activation:
		cursor_position = logical_size * 0.5
	queue_redraw()


func deactivate() -> void:
	active = false
	device_id = -1
	_left_stick = Vector2.ZERO
	_right_stick_y = 0.0
	_left_trigger_pressed = false
	_right_trigger_pressed = false
	_button_pressed.clear()
	for button in _dpad_pressed:
		_dpad_pressed[button] = false
	_hat_hold_frames = 0
	_hat_repeat_direction = Vector2i.ZERO
	_scroll_accumulator = 0.0
	_has_hover = false
	queue_redraw()


func _input(event: InputEvent) -> void:
	if not (event is InputEventJoypadButton or event is InputEventJoypadMotion):
		return
	dispatch_event(event)
	if active:
		get_viewport().set_input_as_handled()


func dispatch_event(event: InputEvent) -> Array[String]:
	var actions := feed_event(event)
	_emit_actions(actions)
	return actions


func feed_event(event: InputEvent) -> Array[String]:
	if event is InputEventJoypadButton:
		var button_event := event as InputEventJoypadButton
		return feed_button(button_event.button_index, button_event.pressed, button_event.device)
	if event is InputEventJoypadMotion:
		var motion_event := event as InputEventJoypadMotion
		return feed_axis(motion_event.axis, motion_event.axis_value, motion_event.device)
	return []


func feed_button(button: JoyButton, pressed: bool, controller_device: int = 0) -> Array[String]:
	if not active:
		if not pressed:
			return []
		activate(controller_device)
	elif controller_device != device_id:
		return []
	var was_pressed := bool(_button_pressed.get(button, false))
	_button_pressed[button] = pressed
	if DPAD_ACTIONS.has(button):
		_dpad_pressed[button] = pressed
		var direction := _dpad_direction()
		if direction != _hat_repeat_direction:
			_hat_repeat_direction = direction
			_hat_hold_frames = 0
		if pressed and not was_pressed:
			return [String(DPAD_ACTIONS[button])]
		return []
	if pressed and not was_pressed and BUTTON_ACTIONS.has(button):
		return [String(BUTTON_ACTIONS[button])]
	return []


func feed_axis(axis: JoyAxis, value: float, controller_device: int = 0) -> Array[String]:
	if not active:
		var meaningful := absf(value) >= DEADZONE
		if axis in [JOY_AXIS_TRIGGER_LEFT, JOY_AXIS_TRIGGER_RIGHT]:
			meaningful = value > TRIGGER_THRESHOLD
		if not meaningful:
			return []
		activate(controller_device)
	elif controller_device != device_id:
		return []
	var actions: Array[String] = []
	match axis:
		JOY_AXIS_LEFT_X:
			_left_stick.x = value
		JOY_AXIS_LEFT_Y:
			_left_stick.y = value
		JOY_AXIS_RIGHT_Y:
			_right_stick_y = value
		JOY_AXIS_TRIGGER_LEFT:
			var left_pressed := value > TRIGGER_THRESHOLD
			if left_pressed and not _left_trigger_pressed:
				actions.append("left_trigger")
			_left_trigger_pressed = left_pressed
		JOY_AXIS_TRIGGER_RIGHT:
			var right_pressed := value > TRIGGER_THRESHOLD
			if right_pressed and not _right_trigger_pressed:
				actions.append("right_trigger")
			_right_trigger_pressed = right_pressed
	return actions


func _process(delta: float) -> void:
	if not active:
		return
	_frame_accumulator += minf(delta, 0.25) * FRAME_RATE
	var guard := 0
	while _frame_accumulator >= 1.0 and guard < 8:
		_frame_accumulator -= 1.0
		_emit_actions(advance_frame())
		guard += 1
	if guard == 8 and _frame_accumulator > 8.0:
		_frame_accumulator = 8.0


func advance_frame() -> Array[String]:
	if not active:
		return []
	_move_cursor()
	var actions: Array[String] = []
	actions.append_array(_advance_dpad())
	actions.append_array(_advance_scroll())
	queue_redraw()
	return actions


func _move_cursor() -> void:
	var axis_x := _left_stick.x if absf(_left_stick.x) >= DEADZONE else 0.0
	var axis_y := _left_stick.y if absf(_left_stick.y) >= DEADZONE else 0.0
	var magnitude := sqrt(axis_x * axis_x + axis_y * axis_y)
	if magnitude > 0.0:
		var speed := (
			CURSOR_SPEED + (CURSOR_MAX_SPEED - CURSOR_SPEED) * pow(magnitude, CURSOR_ACCELERATION)
		)
		cursor_position += Vector2(axis_x, axis_y) * speed
	cursor_position.x = clampf(cursor_position.x, 0.0, logical_size.x)
	cursor_position.y = clampf(cursor_position.y, 0.0, logical_size.y)


func _advance_dpad() -> Array[String]:
	var direction := _dpad_direction()
	if direction == Vector2i.ZERO:
		_hat_hold_frames = 0
		_hat_repeat_direction = Vector2i.ZERO
		return []
	if direction != _hat_repeat_direction:
		_hat_repeat_direction = direction
		_hat_hold_frames = 0
		return []
	_hat_hold_frames += 1
	var past := _hat_hold_frames - HAT_REPEAT_DELAY
	if past < 0 or past % HAT_REPEAT_RATE != 0:
		return []
	return _dpad_actions(direction)


func _advance_scroll() -> Array[String]:
	var actions: Array[String] = []
	if absf(_right_stick_y) <= SCROLL_DEADZONE:
		_scroll_accumulator = 0.0
		return actions
	_scroll_accumulator += _right_stick_y * SCROLL_SPEED
	var guard := 0
	while _scroll_accumulator >= SCROLL_STEP and guard < 8:
		actions.append("scroll_down")
		_scroll_accumulator -= SCROLL_STEP
		guard += 1
	guard = 0
	while _scroll_accumulator <= -SCROLL_STEP and guard < 8:
		actions.append("scroll_up")
		_scroll_accumulator += SCROLL_STEP
		guard += 1
	return actions


func _dpad_direction() -> Vector2i:
	var horizontal := int(bool(_dpad_pressed[JOY_BUTTON_DPAD_RIGHT]))
	horizontal -= int(bool(_dpad_pressed[JOY_BUTTON_DPAD_LEFT]))
	var vertical := int(bool(_dpad_pressed[JOY_BUTTON_DPAD_UP]))
	vertical -= int(bool(_dpad_pressed[JOY_BUTTON_DPAD_DOWN]))
	return Vector2i(horizontal, vertical)


func _dpad_actions(direction: Vector2i) -> Array[String]:
	var actions: Array[String] = []
	if direction.y > 0:
		actions.append("dpad_up")
	elif direction.y < 0:
		actions.append("dpad_down")
	if direction.x < 0:
		actions.append("dpad_left")
	elif direction.x > 0:
		actions.append("dpad_right")
	return actions


func _emit_actions(actions: Array[String]) -> void:
	for action in actions:
		action_requested.emit(action)


func nudge_cursor(offset: Vector2) -> void:
	cursor_position += offset
	cursor_position.x = clampf(cursor_position.x, 0.0, logical_size.x)
	cursor_position.y = clampf(cursor_position.y, 0.0, logical_size.y)
	queue_redraw()


func snap_to_nearest(rects: Array) -> bool:
	if not active or rects.is_empty():
		return false
	var nearest := Rect2()
	var nearest_distance := INF
	for value in rects:
		var rect: Rect2 = value
		var distance := cursor_position.distance_to(rect.get_center())
		if distance < nearest_distance:
			nearest_distance = distance
			nearest = rect
	cursor_position = nearest.get_center()
	queue_redraw()
	return true


func set_hover_rect(rect: Rect2, has_hover: bool) -> void:
	if rect == _hover_rect and has_hover == _has_hover:
		return
	_hover_rect = rect
	_has_hover = has_hover
	queue_redraw()


func rumble(intensity: float = 0.5, duration_frames: int = 15) -> void:
	if not active or device_id < 0:
		return
	rumble_requests += 1
	if device_id in Input.get_connected_joypads():
		Input.start_joy_vibration(
			device_id,
			clampf(intensity, 0.0, 1.0),
			clampf(intensity * 0.7, 0.0, 1.0),
			float(duration_frames) / FRAME_RATE
		)


func get_button_label(action: String) -> String:
	var table: Dictionary = LABELS.get(controller_type, LABELS.generic)
	return String(table.get(action, "?"))


func get_action_label(gameplay_action: String) -> String:
	var button := String(ACTION_BINDINGS.get(gameplay_action, ""))
	return get_button_label(button) if not button.is_empty() else "?"


func get_hints(context: String = "game") -> Array:
	if context == "pause":
		return [
			[get_action_label("select"), "Select"],
			[get_action_label("pause"), "Resume"],
		]
	if context == "shop":
		return [
			[get_action_label("select"), "Buy"],
			[get_action_label("back"), "Close"],
			["%s/%s" % [get_button_label("right_stick"), get_button_label("dpad")], "Scroll"],
			[get_action_label("snap"), "Snap"],
		]
	if context == "victory":
		return [
			[get_action_label("next_level"), "Next Level"],
			[get_action_label("replay"), "Replay"],
			[get_action_label("to_menu"), "Menu"],
		]
	if context == "defeat":
		return [
			[get_action_label("replay"), "Replay"],
			[get_action_label("to_menu"), "Menu"],
		]
	return [
		[get_button_label("skill_q"), "Q"],
		[get_button_label("skill_w"), "W"],
		[get_button_label("skill_e"), "E"],
		[get_button_label("skill_r"), "R"],
		[get_action_label("shop"), "Shop"],
		[get_action_label("move_hero"), "Move Hero"],
		[get_action_label("pause"), "Pause"],
	]


func _detect_controller_type(controller_name: String) -> String:
	var normalized := controller_name.to_lower()
	for keyword in [
		"playstation",
		"ps3",
		"ps4",
		"ps5",
		"dualshock",
		"dualsense",
		"sony",
		"wireless controller",
	]:
		if keyword in normalized:
			return "ps"
	for keyword in [
		"xbox",
		"xinput",
		"x-box",
		"microsoft",
		"x360",
		"xone",
		"xb1",
		"rog",
		"asus",
		"ally",
		"steam",
		"valve",
		"gamesir",
		"razer",
		"8bitdo",
		"logitech",
		"thrustmaster",
	]:
		if keyword in normalized:
			return "xbox"
	return "generic"


func _on_joy_connection_changed(controller_device: int, connected: bool) -> void:
	if not connected and controller_device == device_id:
		deactivate()


func _draw() -> void:
	if not active:
		return
	if _has_hover:
		draw_rect(_hover_rect.grow(10.0), Color(1.0, 1.0, 0.4, 0.16), true)
		draw_rect(_hover_rect.grow(5.0), Color(1.0, 1.0, 0.75), false, 3.0)
	var pulse := sin(float(Time.get_ticks_msec()) * 0.006) * 0.15 + 0.75
	draw_circle(cursor_position, 12.0, Color(1.0, 0.95, 0.35, 0.12 * pulse))
	var color := Color(1.0, 1.0, 0.8)
	draw_line(cursor_position + Vector2(-8, 0), cursor_position + Vector2(-3, 0), color, 2.0)
	draw_line(cursor_position + Vector2(3, 0), cursor_position + Vector2(8, 0), color, 2.0)
	draw_line(cursor_position + Vector2(0, -8), cursor_position + Vector2(0, -3), color, 2.0)
	draw_line(cursor_position + Vector2(0, 3), cursor_position + Vector2(0, 8), color, 2.0)
	draw_circle(cursor_position, 2.0, Color.WHITE)
	draw_circle(cursor_position, 1.0, Color(1.0, 0.78, 0.2))
