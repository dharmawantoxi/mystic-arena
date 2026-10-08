# gdlint:disable=max-returns
extends RefCounted
## Replay mobile/touch.py fixtures through the native deterministic gesture engine.

const Gesture = preload("res://scripts/input/touch_gesture_runtime.gd")
const FIXTURE := "res://tests/fixtures/touch_gesture_source.json"
const BASE_MS := 10_000.0


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Touch gesture source fixture parses")
	if not (parsed is Dictionary):
		return
	var fixture: Dictionary = parsed
	_check_policy(fixture.policy, check)
	for spec in fixture.cases:
		_replay_case(spec, check)


func _check_policy(policy: Dictionary, check: Callable) -> void:
	check.call(
		is_equal_approx(float(policy.tap_slop), Gesture.TAP_SLOP), "Touch tap slop matches source"
	)
	check.call(
		is_equal_approx(float(policy.long_press_ms), Gesture.LONG_PRESS_MS),
		"Touch long-press clock matches source"
	)
	check.call(
		is_equal_approx(float(policy.double_tap_ms), Gesture.DOUBLE_TAP_MS),
		"Touch double-tap clock matches source"
	)
	check.call(
		is_equal_approx(float(policy.scroll_step), Gesture.SCROLL_STEP),
		"Touch scroll notch matches source"
	)
	check.call(
		is_equal_approx(float(policy.fling_friction), Gesture.FLING_FRICTION),
		"Touch fling friction matches source"
	)
	check.call(
		is_equal_approx(float(policy.fling_min_speed), Gesture.FLING_MIN_SPEED),
		"Touch fling stop speed matches source"
	)


func _replay_case(spec: Dictionary, check: Callable) -> void:
	var runtime = Gesture.new()
	var operations: Array = spec.ops
	var expected_steps: Array = spec.steps
	check.call(
		operations.size() == expected_steps.size(),
		"Touch fixture operation count: " + String(spec.label)
	)
	for index in range(operations.size()):
		var operation: Dictionary = operations[index]
		var expected: Dictionary = expected_steps[index]
		var actions := _apply(runtime, operation)
		check.call(
			_actions_match(actions, expected.actions),
			"Touch action replay: %s/%s/%d" % [spec.label, operation.op, index]
		)
		check.call(
			_state_matches(runtime, expected.state),
			"Touch state replay: %s/%s/%d" % [spec.label, operation.op, index]
		)


func _apply(runtime, operation: Dictionary) -> Array[Dictionary]:
	var now_ms := BASE_MS + float(operation.at)
	var touch_id := int(operation.get("id", 0))
	var raw_position: Array = operation.get("pos", [0, 0])
	var position := Vector2(float(raw_position[0]), float(raw_position[1]))
	match String(operation.op):
		"down":
			return runtime.touch_down(touch_id, position, now_ms)
		"motion":
			return runtime.touch_motion(touch_id, position)
		"up":
			return runtime.touch_up(touch_id, position, now_ms)
		"update":
			return runtime.advance(now_ms)
		"cancel":
			runtime.cancel()
	return []


func _actions_match(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size():
		return false
	for index in range(actual.size()):
		var left: Dictionary = actual[index]
		var right: Dictionary = expected[index]
		if String(left.kind) != String(right.kind):
			return false
		if int(left.touch_id) != int(right.touch_id):
			return false
		if not Vector2(left.pos).is_equal_approx(_fixture_vector(right.pos)):
			return false
		if not Vector2(left.delta).is_equal_approx(_fixture_vector(right.delta)):
			return false
		if not is_equal_approx(float(left.value), float(right.value)):
			return false
	return true


func _state_matches(runtime, expected: Dictionary) -> bool:
	var point_ids: Array[int] = []
	for touch_id in runtime.points:
		point_ids.append(int(touch_id))
	point_ids.sort()
	var expected_ids: Array[int] = []
	for touch_id in expected.points:
		expected_ids.append(int(touch_id))
	if point_ids != expected_ids:
		return false
	if expected.active_pos == null:
		if runtime.active_pos != null:
			return false
	elif (
		runtime.active_pos == null
		or not Vector2(runtime.active_pos).is_equal_approx(_fixture_vector(expected.active_pos))
	):
		return false
	return (
		is_equal_approx(runtime.fling_velocity, float(expected.fling_velocity))
		and runtime.fling_pos.is_equal_approx(_fixture_vector(expected.fling_pos))
		and runtime.tap_count == int(expected.tap_count)
	)


func _fixture_vector(value: Array) -> Vector2:
	return Vector2(float(value[0]), float(value[1]))
