class_name GestureTracker
extends RefCounted

## Deterministic port of mobile/touch.py. Time is supplied by the caller.
const TAP_SLOP := 14.0
const LONG_PRESS_SECONDS := 0.450
const DOUBLE_TAP_SECONDS := 0.280
const SCROLL_STEP := 42.0
const FLING_FRICTION := 0.90
const FLING_MIN_SPEED := 0.6
const EPSILON := 0.000000001

var points: Dictionary = {}
var actions: Array[Dictionary] = []
var fling_velocity := 0.0
var fling_position := Vector2.ZERO
var _last_tap_time := -INF
var _last_tap_position := Vector2.ZERO


func _emit(kind: String, position: Vector2, id: int, delta := Vector2.ZERO, value := 0.0) -> void:
	actions.append({"kind": kind, "pos": position, "id": id, "delta": delta, "value": value})


func down(id: int, position: Vector2, now: float) -> void:
	points[id] = {
		"start": position,
		"pos": position,
		"time": now,
		"moved": false,
		"long_fired": false,
		"scroll": 0.0,
		"velocity": 0.0,
	}
	fling_velocity = 0.0
	_emit("down", position, id)


func motion(id: int, position: Vector2) -> void:
	if not points.has(id):
		return
	var point: Dictionary = points[id]
	var delta: Vector2 = position - point.pos
	point.pos = position
	if position.distance_to(point.start) > TAP_SLOP:
		point.moved = true
	if not point.moved:
		return
	point.velocity = lerpf(point.velocity, delta.y, 0.4)
	_emit("drag", position, id, delta)
	point.scroll += delta.y
	while absf(point.scroll) >= SCROLL_STEP:
		var direction := signf(point.scroll)
		point.scroll -= direction * SCROLL_STEP
		_emit("scroll", position, id, Vector2.ZERO, -direction)


func up(id: int, position: Vector2, now: float) -> void:
	if not points.has(id):
		return
	var point: Dictionary = points[id]
	points.erase(id)
	if not point.moved and not point.long_fired:
		var nearby := position.distance_to(_last_tap_position) < 40.0
		if now - _last_tap_time + EPSILON < DOUBLE_TAP_SECONDS and nearby:
			_emit("double_tap", position, id)
			_last_tap_time = -INF
		else:
			_emit("tap", position, id, Vector2.ZERO, now - point.time)
			_last_tap_time = now
			_last_tap_position = position
	elif point.moved and absf(point.velocity) > 4.0:
		fling_velocity = point.velocity
		fling_position = position
		_emit("fling", position, id, Vector2.ZERO, fling_velocity)
	_emit("release", position, id)


func update(now: float) -> void:
	for id: int in points:
		var point: Dictionary = points[id]
		if (
			not point.moved
			and not point.long_fired
			and now - point.time + EPSILON >= LONG_PRESS_SECONDS
		):
			point.long_fired = true
			_emit("long_press", point.pos, id)
	if absf(fling_velocity) > FLING_MIN_SPEED:
		fling_velocity *= FLING_FRICTION
		var steps := mini(int(absf(fling_velocity) / (SCROLL_STEP * 0.35)), 3)
		for _index in range(steps):
			_emit("scroll", fling_position, -1, Vector2.ZERO, -signf(fling_velocity))
	else:
		fling_velocity = 0.0


func collect() -> Array[Dictionary]:
	var result := actions
	actions = []
	return result


func cancel() -> void:
	points.clear()
	actions.clear()
	fling_velocity = 0.0
	_last_tap_time = -INF
