extends RefCounted
## Popup slide-in, ported from `_render.py::PopupAnimation`. The update order,
## the snap threshold, the slide distance and the `_ease_out_back` constants
## mirror the source; `tests/popup_animation_checks.gd` replays the source
## oracle fixture. Presentation only: it drives a scale and a Y offset, it does
## not draw.

const SPEED := 0.15
const SNAP_EPSILON := 0.01
const SLIDE_DISTANCE := 30.0
const EASE_C1 := 1.70158

var progress := 0.0
var target := 1.0
var speed := SPEED


func show() -> void:
	progress = 0.0
	target = 1.0


func hide() -> void:
	target = 0.0


func update() -> void:
	var diff := target - progress
	progress += diff * speed
	if absf(diff) < SNAP_EPSILON:
		progress = target


func get_scale() -> float:
	return _ease_out_back(progress)


func get_offset_y() -> int:
	return int((1.0 - progress) * SLIDE_DISTANCE)


static func _ease_out_back(t: float) -> float:
	var c3 := EASE_C1 + 1.0
	var t1 := t - 1.0
	return 1.0 + c3 * (t1 * t1 * t1) + EASE_C1 * (t1 * t1)
