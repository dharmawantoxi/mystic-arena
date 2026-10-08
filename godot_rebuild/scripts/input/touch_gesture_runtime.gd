extends RefCounted
## Deterministic port of mobile/touch.py::TouchManager.
##
## The scene supplies monotonic milliseconds, making tap/hold behavior testable
## without wall-clock sleeps. Actions preserve the source vocabulary and signs:
## a downward drag emits scroll value -1 (wheel up), while upward emits +1.

const TAP_SLOP := 14.0
const LONG_PRESS_MS := 450.0
const DOUBLE_TAP_MS := 280.0
const SCROLL_STEP := 42.0
const FLING_FRICTION := 0.90
const FLING_MIN_SPEED := 0.6

var points: Dictionary = {}
var active_pos: Variant = null
var fling_velocity := 0.0
var fling_pos := Vector2.ZERO
var tap_count := 0

var _last_tap_time_ms := 0.0
var _last_tap_pos := Vector2.ZERO


func touch_down(touch_id: int, position: Vector2, now_ms: float) -> Array[Dictionary]:
	points[touch_id] = {
		"start_pos": position,
		"pos": position,
		"prev_pos": position,
		"start_time_ms": now_ms,
		"moved": false,
		"long_fired": false,
		"scroll_accum": 0.0,
		"velocity": 0.0,
	}
	active_pos = position
	fling_velocity = 0.0
	return [_action("down", position, Vector2.ZERO, 0.0, touch_id)]


func touch_motion(touch_id: int, position: Vector2) -> Array[Dictionary]:
	if not points.has(touch_id):
		return []
	var point: Dictionary = points[touch_id]
	var previous: Vector2 = point.pos
	var delta := position - previous
	point.prev_pos = previous
	point.pos = position
	active_pos = position
	var total: float = (position - Vector2(point.start_pos)).length()
	if total > TAP_SLOP:
		point.moved = true
	var actions: Array[Dictionary] = []
	if bool(point.moved):
		point.velocity = float(point.velocity) * 0.6 + delta.y * 0.4
		actions.append(_action("drag", position, delta, 0.0, touch_id))
		point.scroll_accum = float(point.scroll_accum) + delta.y
		while absf(float(point.scroll_accum)) >= SCROLL_STEP:
			var direction := -1.0 if float(point.scroll_accum) > 0.0 else 1.0
			var sign_value := 1.0 if float(point.scroll_accum) > 0.0 else -1.0
			point.scroll_accum = float(point.scroll_accum) - SCROLL_STEP * sign_value
			actions.append(_action("scroll", position, Vector2.ZERO, direction, touch_id))
	points[touch_id] = point
	return actions


func touch_up(touch_id: int, position: Vector2, now_ms: float) -> Array[Dictionary]:
	if not points.has(touch_id):
		return []
	var point: Dictionary = points[touch_id]
	points.erase(touch_id)
	var held_ms := now_ms - float(point.start_time_ms)
	var actions: Array[Dictionary] = []
	if not bool(point.moved) and not bool(point.long_fired):
		var is_double := (
			now_ms - _last_tap_time_ms < DOUBLE_TAP_MS
			and absf(position.x - _last_tap_pos.x) < 40.0
			and absf(position.y - _last_tap_pos.y) < 40.0
		)
		tap_count += 1
		if is_double:
			actions.append(_action("double_tap", position, Vector2.ZERO, 0.0, touch_id))
			_last_tap_time_ms = 0.0
		else:
			actions.append(_action("tap", position, Vector2.ZERO, held_ms, touch_id))
			_last_tap_time_ms = now_ms
			_last_tap_pos = position
	elif bool(point.moved) and absf(float(point.velocity)) > 4.0:
		fling_velocity = float(point.velocity)
		fling_pos = position
		actions.append(_action("fling", position, Vector2.ZERO, fling_velocity, touch_id))
	actions.append(_action("release", position, Vector2.ZERO, 0.0, touch_id))
	if points.is_empty():
		active_pos = null
	return actions


func advance(now_ms: float) -> Array[Dictionary]:
	var actions: Array[Dictionary] = []
	for touch_id in points:
		var point: Dictionary = points[touch_id]
		if bool(point.long_fired) or bool(point.moved):
			continue
		if now_ms - float(point.start_time_ms) >= LONG_PRESS_MS:
			point.long_fired = true
			points[touch_id] = point
			actions.append(
				_action("long_press", Vector2(point.pos), Vector2.ZERO, 0.0, int(touch_id))
			)
	if absf(fling_velocity) > FLING_MIN_SPEED:
		fling_velocity *= FLING_FRICTION
		var steps := int(absf(fling_velocity) / (SCROLL_STEP * 0.35))
		for index in range(mini(steps, 3)):
			actions.append(
				_action("scroll", fling_pos, Vector2.ZERO, -1.0 if fling_velocity > 0.0 else 1.0, 0)
			)
	else:
		fling_velocity = 0.0
	return actions


func cancel_touch(touch_id: int) -> void:
	points.erase(touch_id)
	if points.is_empty():
		active_pos = null


func cancel() -> void:
	points.clear()
	fling_velocity = 0.0


func _action(
	kind: String, position: Vector2, delta: Vector2, value: float, touch_id: int
) -> Dictionary:
	return {
		"kind": kind,
		"pos": position,
		"delta": delta,
		"value": value,
		"touch_id": touch_id,
	}
