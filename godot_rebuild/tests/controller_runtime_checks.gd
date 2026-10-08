extends RefCounted
## Deterministic replay of _core.py::ControllerManager's source fixture.

const Runtime = preload("res://scripts/input/controller_runtime.gd")
const FIXTURE := "res://tests/fixtures/controller_source.json"
const BUTTONS := {
	"confirm": JOY_BUTTON_A,
	"cancel": JOY_BUTTON_B,
	"skill_q": JOY_BUTTON_X,
	"skill_w": JOY_BUTTON_Y,
	"skill_e": JOY_BUTTON_LEFT_SHOULDER,
	"skill_r": JOY_BUTTON_RIGHT_SHOULDER,
	"start": JOY_BUTTON_START,
	"back": JOY_BUTTON_BACK,
	"stick_left": JOY_BUTTON_LEFT_STICK,
	"stick_right": JOY_BUTTON_RIGHT_STICK,
}
const DPAD := {
	"up": [JOY_BUTTON_DPAD_UP],
	"down": [JOY_BUTTON_DPAD_DOWN],
	"left": [JOY_BUTTON_DPAD_LEFT],
	"right": [JOY_BUTTON_DPAD_RIGHT],
	"up_right": [JOY_BUTTON_DPAD_UP, JOY_BUTTON_DPAD_RIGHT],
}


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Controller source fixture parses")
	if not (parsed is Dictionary):
		return
	var fixture: Dictionary = parsed
	_check_policy(fixture.policy, check)
	_check_cursor(fixture.cursor, check)
	_check_buttons(fixture.buttons, check)
	_check_dpad(fixture.dpad, check)
	_check_triggers(fixture.triggers, check)
	_check_scroll(fixture.scroll, check)
	_check_snap(fixture.snap, check)
	_check_hints(fixture.hints, check)


func _runtime(controller_type: String = "xbox"):
	var runtime = Runtime.new()
	runtime.logical_size = Vector2(1280, 720)
	runtime.activate(0, controller_type)
	return runtime


func _check_policy(policy: Dictionary, check: Callable) -> void:
	check.call(
		int(policy.screen[0]) == 1280 and int(policy.screen[1]) == 720,
		"Controller source logical viewport is 1280x720"
	)
	check.call(
		is_equal_approx(float(policy.cursor_speed), Runtime.CURSOR_SPEED),
		"Controller base cursor speed matches source"
	)
	check.call(
		is_equal_approx(float(policy.cursor_max_speed), Runtime.CURSOR_MAX_SPEED),
		"Controller maximum cursor speed matches source"
	)
	check.call(
		is_equal_approx(float(policy.cursor_acceleration), Runtime.CURSOR_ACCELERATION),
		"Controller cursor acceleration matches source"
	)
	check.call(
		is_equal_approx(float(policy.deadzone), Runtime.DEADZONE),
		"Controller cursor deadzone matches source"
	)
	check.call(
		int(policy.hat_repeat_delay) == Runtime.HAT_REPEAT_DELAY,
		"Controller D-pad repeat delay matches source"
	)
	check.call(
		int(policy.hat_repeat_rate) == Runtime.HAT_REPEAT_RATE,
		"Controller D-pad repeat rate matches source"
	)
	check.call(
		is_equal_approx(float(policy.scroll_speed), Runtime.SCROLL_SPEED),
		"Controller scroll speed matches source"
	)
	check.call(
		is_equal_approx(float(policy.scroll_deadzone), Runtime.SCROLL_DEADZONE),
		"Controller scroll deadzone matches source"
	)
	var actions: Array[String] = []
	for action in Runtime.BUTTON_ACTIONS.values():
		actions.append(String(action))
	for action in Runtime.DPAD_ACTIONS.values():
		actions.append(String(action))
	actions.append_array(["left_trigger", "right_trigger", "scroll_up", "scroll_down"])
	actions.sort()
	var source_actions: Array[String] = []
	for action in policy.gameplay_actions:
		source_actions.append(String(action))
	source_actions.sort()
	check.call(actions == source_actions, "Native controller exposes every source gameplay action")


func _check_cursor(rows: Array, check: Callable) -> void:
	for row in rows:
		var runtime = _runtime()
		runtime.feed_axis(JOY_AXIS_LEFT_X, float(row.axes[0]))
		runtime.feed_axis(JOY_AXIS_LEFT_Y, float(row.axes[1]))
		for frame in range(int(row.frames)):
			runtime.advance_frame()
		var expected := Vector2(float(row.position[0]), float(row.position[1]))
		check.call(
			runtime.cursor_position.is_equal_approx(expected),
			"Controller cursor replay: " + String(row.label)
		)
		check.call(
			(
				Vector2i(runtime.cursor_position)
				== Vector2i(int(row.integer_position[0]), int(row.integer_position[1]))
			),
			"Controller integer cursor replay: " + String(row.label)
		)
		runtime.free()


func _check_buttons(rows: Array, check: Callable) -> void:
	for row in rows:
		# Godot's input map normalizes all three source hardware layouts. Replay
		# one logical edge sequence per source row against that normalized button.
		var runtime = _runtime(String(row.mapping))
		var button: JoyButton = BUTTONS[String(row.action)]
		var sequence := [
			runtime.feed_button(button, true),
			runtime.feed_button(button, true),
			runtime.feed_button(button, false),
			runtime.feed_button(button, true),
		]
		check.call(
			sequence == row.sequence,
			"Controller button edge replay: %s/%s" % [row.mapping, row.action]
		)
		runtime.free()


func _check_dpad(rows: Array, check: Callable) -> void:
	for row in rows:
		var runtime = _runtime()
		var buttons: Array = DPAD[String(row.label)]
		var events: Array = []
		var initial: Array[String] = []
		for button in buttons:
			initial.append_array(runtime.feed_button(button, true))
		if not initial.is_empty():
			events.append({"frame": 0, "actions": initial})
		for frame in range(1, 31):
			var actions: Array[String] = runtime.advance_frame()
			if not actions.is_empty():
				events.append({"frame": frame, "actions": actions})
		for button in buttons:
			runtime.feed_button(button, false)
		var repressed: Array[String] = []
		for button in buttons:
			repressed.append_array(runtime.feed_button(button, true))
		events.append({"frame": "repress", "actions": repressed})
		check.call(
			_events_match(events, row.events),
			"Controller D-pad repeat replay: " + String(row.label)
		)
		runtime.free()


func _check_triggers(rows: Array, check: Callable) -> void:
	var runtime = _runtime()
	for index in range(rows.size()):
		var row: Dictionary = rows[index]
		var actions: Array[String] = []
		actions.append_array(runtime.feed_axis(JOY_AXIS_TRIGGER_LEFT, float(row.axes[0])))
		actions.append_array(runtime.feed_axis(JOY_AXIS_TRIGGER_RIGHT, float(row.axes[1])))
		check.call(actions == row.actions, "Controller trigger edge replay %d" % index)
	runtime.free()


func _check_scroll(rows: Array, check: Callable) -> void:
	for row in rows:
		var runtime = _runtime()
		var value := float(row.alternate) if float(row.alternate) != 0.0 else float(row.mapped)
		runtime.feed_axis(JOY_AXIS_RIGHT_Y, value)
		var events: Array = []
		var frame_count := _scroll_frame_count(String(row.label))
		for frame in range(frame_count):
			var actions: Array[String] = runtime.advance_frame()
			if not actions.is_empty():
				events.append({"frame": frame, "actions": actions})
		check.call(
			_events_match(events, row.events), "Controller right-stick replay: " + String(row.label)
		)
		check.call(
			is_equal_approx(runtime._scroll_accumulator, float(row.accumulator)),
			"Controller scroll accumulator replay: " + String(row.label)
		)
		runtime.free()


func _events_match(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size():
		return false
	for index in range(actual.size()):
		var actual_row: Dictionary = actual[index]
		var expected_row: Dictionary = expected[index]
		var actual_frame: Variant = actual_row.frame
		var expected_frame: Variant = expected_row.frame
		if actual_frame is String or expected_frame is String:
			if String(actual_frame) != String(expected_frame):
				return false
		elif int(actual_frame) != int(expected_frame):
			return false
		if actual_row.actions != expected_row.actions:
			return false
	return true


func _scroll_frame_count(label: String) -> int:
	match label:
		"deadzone":
			return 5
		"positive_half":
			return 12
		_:
			return 8


func _check_snap(rows: Array, check: Callable) -> void:
	var rects: Array[Rect2] = [
		Rect2(Vector2(90, 90), Vector2(20, 20)),
		Rect2(Vector2(630, 350), Vector2(20, 20)),
		Rect2(Vector2(1170, 610), Vector2(20, 20)),
	]
	for row in rows:
		var runtime = _runtime()
		runtime.cursor_position = Vector2(float(row.start[0]), float(row.start[1]))
		check.call(runtime.snap_to_nearest(rects), "Controller snap accepts authored controls")
		var expected := Vector2(float(row.position[0]), float(row.position[1]))
		check.call(
			runtime.cursor_position == expected,
			"Controller nearest-control replay from %s" % [row.start]
		)
		runtime.free()


func _check_hints(hints: Dictionary, check: Callable) -> void:
	var runtime = _runtime("xbox")
	for context in hints:
		check.call(
			runtime.get_hints(String(context)) == hints[context],
			"Controller %s hint bindings match source" % context
		)
	runtime.free()
