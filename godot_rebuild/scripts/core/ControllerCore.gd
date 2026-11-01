class_name ControllerCore
extends RefCounted

## Pure controller state machine ported from _core.ControllerManager.
## Device polling lives in ControllerManager; this class is unit-testable.
const DEADZONE := 0.18
const CURSOR_BASE := 180.0
const CURSOR_MAX := 900.0
const CURSOR_ACCEL := 2.2
const DPAD_DELAY := 0.35
const DPAD_REPEAT := 0.12
const TRIGGER_THRESHOLD := 0.5
var family := "generic"
var mapping: Dictionary = {}
var cursor := Vector2(640, 360)
var cursor_velocity := Vector2.ZERO
var previous_buttons: Dictionary = {}
var previous_triggers := {"left": false, "right": false}
var dpad_direction := Vector2i.ZERO
var dpad_timer := 0.0
var dpad_repeating := false
var scroll_axis := -1
var scroll_candidates := [3, 2, 4, 5]
var scroll_idle: Dictionary = {}
var rumble_timer := 0.0
var last_actions: Array[String] = []


func configure(map_data: Dictionary, device_name: String) -> void:
	var lower := device_name.to_lower()
	if "xbox" in lower or "xinput" in lower:
		family = "xbox"
		mapping = map_data.get("XBOX_MAP", {})
	elif "playstation" in lower or "dualshock" in lower or "dualsense" in lower or "sony" in lower:
		family = "ps"
		mapping = map_data.get("PS_MAP", {})
	else:
		family = "generic"
		mapping = map_data.get("GENERIC_MAP", {})
	scroll_axis = int(mapping.get("right_stick_y", 3))
	for candidate: int in scroll_candidates:
		scroll_idle[candidate] = true


static func apply_deadzone(value: float) -> float:
	if absf(value) < DEADZONE:
		return 0.0
	return signf(value) * (absf(value) - DEADZONE) / (1.0 - DEADZONE)


func button_name(index: int) -> String:
	for action: String in [
		"confirm",
		"cancel",
		"skill_q",
		"skill_w",
		"skill_e",
		"skill_r",
		"start",
		"back",
		"shop",
		"stick_left",
		"stick_right"
	]:
		if int(mapping.get(action, -1)) == index:
			return action
	return ""


func update(axes: Dictionary, buttons: Dictionary, delta: float, bounds: Rect2) -> Array[String]:
	last_actions = []
	var lx := apply_deadzone(float(axes.get(int(mapping.get("left_stick_x", 0)), 0.0)))
	var ly := apply_deadzone(float(axes.get(int(mapping.get("left_stick_y", 1)), 0.0)))
	var magnitude := clampf(Vector2(lx, ly).length(), 0.0, 1.0)
	var speed := CURSOR_BASE + (CURSOR_MAX - CURSOR_BASE) * pow(magnitude, CURSOR_ACCEL)
	cursor_velocity = Vector2(lx, ly) * speed
	cursor += cursor_velocity * delta
	cursor.x = clampf(cursor.x, bounds.position.x, bounds.end.x)
	cursor.y = clampf(cursor.y, bounds.position.y, bounds.end.y)
	for action: String in [
		"confirm",
		"cancel",
		"skill_q",
		"skill_w",
		"skill_e",
		"skill_r",
		"start",
		"back",
		"shop",
		"stick_left",
		"stick_right"
	]:
		var index := int(mapping.get(action, -1))
		if index < 0:
			continue
		var pressed := bool(buttons.get(index, false))
		if pressed and not bool(previous_buttons.get(index, false)):
			last_actions.append(action)
		previous_buttons[index] = pressed
	for side: String in ["left", "right"]:
		var axis := int(mapping.get(side + "_trigger", 4 if side == "left" else 5))
		var pressed := float(axes.get(axis, 0.0)) > TRIGGER_THRESHOLD
		if pressed and not bool(previous_triggers[side]):
			last_actions.append("trigger_" + side)
		previous_triggers[side] = pressed
	var direction := Vector2i.ZERO
	if bool(buttons.get(11, false)):
		direction.y = -1
	elif bool(buttons.get(12, false)):
		direction.y = 1
	if bool(buttons.get(13, false)):
		direction.x = -1
	elif bool(buttons.get(14, false)):
		direction.x = 1
	if direction != dpad_direction:
		dpad_direction = direction
		dpad_timer = 0.0
		dpad_repeating = false
		if direction != Vector2i.ZERO:
			last_actions.append("dpad_%d_%d" % [direction.x, direction.y])
	elif direction != Vector2i.ZERO:
		dpad_timer += delta
		var threshold := DPAD_REPEAT if dpad_repeating else DPAD_DELAY
		if dpad_timer >= threshold:
			dpad_timer = 0.0
			dpad_repeating = true
			last_actions.append("dpad_%d_%d" % [direction.x, direction.y])
	_update_scroll_axis(axes)
	rumble_timer = maxf(0.0, rumble_timer - delta)
	return last_actions


func _update_scroll_axis(axes: Dictionary) -> void:
	if scroll_axis >= 0 and absf(float(axes.get(scroll_axis, 0.0))) > 0.25:
		return
	for candidate: int in scroll_candidates:
		var value := float(axes.get(candidate, 0.0))
		if absf(value) > 0.95:
			scroll_idle[candidate] = false
		elif absf(value) < 0.2 and not bool(scroll_idle.get(candidate, true)):
			scroll_axis = candidate
			scroll_idle[candidate] = true
			return
		elif absf(value) < 0.2:
			scroll_idle[candidate] = true


func scroll_value(axes: Dictionary) -> float:
	if scroll_axis < 0:
		return 0.0
	var value := float(axes.get(scroll_axis, 0.0))
	return apply_deadzone(value)


func rumble(seconds: float) -> void:
	rumble_timer = maxf(rumble_timer, seconds)


func label(action: String) -> String:
	var xbox := {
		"confirm": "A",
		"cancel": "B",
		"skill_q": "X",
		"skill_w": "Y",
		"skill_e": "LB",
		"skill_r": "RB",
		"start": "Menu",
		"back": "View",
		"shop": "R3"
	}
	var ps := {
		"confirm": "Cross",
		"cancel": "Circle",
		"skill_q": "Square",
		"skill_w": "Triangle",
		"skill_e": "L1",
		"skill_r": "R1",
		"start": "Options",
		"back": "Share",
		"shop": "R3"
	}
	if family == "xbox":
		return str(xbox.get(action, action))
	if family == "ps":
		return str(ps.get(action, action))
	return action
