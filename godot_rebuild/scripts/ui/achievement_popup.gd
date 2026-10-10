extends RefCounted
## Achievement notification popup, ported from `_render.py::AchievementPopup`.
##
## `unlock()` queues a notification and `update()` drains the queue strictly
## FIFO, giving each one a 180 tick slot. `get_offset_x()` / `get_alpha()` /
## `get_glow_alpha()` expose the presentation curve the source computes inside
## `draw()`: slide in from the right (progress < 0.15, eased with
## `_ease_out_back`, which overshoots slightly past 0), hold to 0.85, then
## slide back out. A short glow rides the first 30% of the slot.
##
## Left unported: the panel gradient, gold border, `corner_ticks`, the
## per-`icon_type` icon geometry, and the text/ellipsis rendering — all pygame
## drawing rather than state. `get_glow_alpha()` returns -1 for "no glow",
## matching the source's `if progress < 0.3` guard.

const DURATION := 180
const SLIDE_IN_END := 0.15
const SLIDE_IN_SPAN := 0.15
const HOLD_END := 0.85
const SLIDE_OUT_SPAN := 0.15
const SLIDE_DISTANCE := 300.0
const GLOW_END := 0.3
const GLOW_MAX := 150
const NO_GLOW := -1
const EASE_C1 := 1.70158

const PANEL_W := 280
const PANEL_H := 60
const PANEL_MARGIN := 20
const PANEL_TOP := 180

var queue: Array = []
var current: Dictionary = {}
var timer := 0
var duration := DURATION


func unlock(title: String, description: String, icon_type: String = "star") -> void:
	queue.append({"title": title, "description": description, "icon_type": icon_type})


func update() -> void:
	if is_showing():
		timer -= 1
		if timer <= 0:
			current = {}
	if not is_showing() and not queue.is_empty():
		current = queue.pop_front()
		timer = duration


func is_showing() -> bool:
	return not current.is_empty()


func progress() -> float:
	return 1.0 - (float(timer) / float(duration))


func get_offset_x() -> int:
	var elapsed := progress()
	if elapsed < SLIDE_IN_END:
		var slide := elapsed / SLIDE_IN_SPAN
		return int((1.0 - _ease_out_back(slide)) * SLIDE_DISTANCE)
	if elapsed < HOLD_END:
		return 0
	var slide_out := (elapsed - HOLD_END) / SLIDE_OUT_SPAN
	return int(slide_out * SLIDE_DISTANCE)


func get_alpha() -> int:
	var elapsed := progress()
	if elapsed < SLIDE_IN_END:
		var slide := elapsed / SLIDE_IN_SPAN
		return int(255.0 * slide)
	if elapsed < HOLD_END:
		return 255
	var slide_out := (elapsed - HOLD_END) / SLIDE_OUT_SPAN
	return int(255.0 * (1.0 - slide_out))


func get_glow_alpha() -> int:
	var elapsed := progress()
	if elapsed >= GLOW_END:
		return NO_GLOW
	return int(float(GLOW_MAX) * (1.0 - elapsed / GLOW_END))


func panel_x(screen_w: int) -> int:
	return screen_w - PANEL_W - PANEL_MARGIN + get_offset_x()


func panel_y() -> int:
	return PANEL_TOP


static func _ease_out_back(t: float) -> float:
	var c1 := EASE_C1
	var c3 := c1 + 1.0
	var t1 := t - 1.0
	return 1.0 + c3 * (t1 * t1 * t1) + c1 * (t1 * t1)
