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
## The full per-type achievement icon is exposed by `icon_ops()` so the native
## renderer and the source oracle share a geometry contract. Remaining panel
## typography/layout details are handled by PrototypeView.

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


func icon_ops(icon_type: String, center: Vector2, alpha: int) -> Array:
	var ops: Array = []
	_icon_circle(ops, center, 16.0, [60, 40, 10, alpha], 0)
	_icon_circle(ops, center, 16.0, [255, 220, 50, alpha], 2)
	if icon_type == "star":
		var points: Array = []
		for index in range(10):
			var angle := float(index) * PI / 5.0 - PI / 2.0
			var radius := 8.0 if index % 2 == 0 else 4.0
			points.append([center.x + cos(angle) * radius, center.y + sin(angle) * radius])
		_icon_polygon(ops, points, [255, 220, 50, 255], 0)
		_icon_polygon(ops, points, [255, 250, 180, 255], 1)
	elif icon_type == "sword":
		_icon_polygon(
			ops,
			[
				[center.x, center.y - 10.0],
				[center.x + 3.0, center.y - 7.0],
				[center.x + 3.0, center.y + 5.0],
				[center.x - 3.0, center.y + 5.0],
				[center.x - 3.0, center.y - 7.0],
			],
			[200, 200, 220, 255],
			0
		)
		_icon_rect(ops, [center.x - 5.0, center.y + 5.0, 10.0, 3.0], [100, 60, 30, 255])
		_icon_rect(ops, [center.x - 2.0, center.y + 8.0, 4.0, 4.0], [60, 40, 20, 255])
	elif icon_type == "skull":
		_icon_circle(ops, center + Vector2(0.0, -2.0), 8.0, [240, 240, 220, 255], 0)
		_icon_rect(ops, [center.x - 3.0, center.y - 4.0, 2.0, 2.0], [0, 0, 0, 255])
		_icon_rect(ops, [center.x + 1.0, center.y - 4.0, 2.0, 2.0], [0, 0, 0, 255])
		_icon_rect(ops, [center.x - 4.0, center.y + 4.0, 8.0, 4.0], [240, 240, 220, 255])
		_icon_rect(ops, [center.x - 2.0, center.y + 5.0, 1.0, 3.0], [0, 0, 0, 255])
		_icon_rect(ops, [center.x + 1.0, center.y + 5.0, 1.0, 3.0], [0, 0, 0, 255])
	elif icon_type == "shield":
		var shield := _shield_points(center)
		_icon_polygon(ops, shield, [100, 200, 255, 255], 0)
		_icon_polygon(ops, shield, [255, 255, 255, 255], 2)
	elif icon_type == "gold":
		_icon_circle(ops, center, 10.0, [200, 150, 20, 255], 0)
		_icon_circle(ops, center, 9.0, [255, 220, 50, 255], 0)
		_icon_circle(ops, center + Vector2(-2.0, -2.0), 4.0, [255, 250, 180, 255], 0)
		(
			ops
			. append(
				{
					"type": "text",
					"text": "$",
					"center": [center.x, center.y],
					"size": 20,
					"color": [100, 60, 10, 255],
				}
			)
		)
	return ops


func _shield_points(center: Vector2) -> Array:
	return [
		[center.x, center.y - 8.0],
		[center.x + 7.0, center.y - 5.0],
		[center.x + 7.0, center.y + 3.0],
		[center.x, center.y + 8.0],
		[center.x - 7.0, center.y + 3.0],
		[center.x - 7.0, center.y - 5.0],
	]


func _icon_circle(ops: Array, center: Vector2, radius: float, color: Array, width: int) -> void:
	(
		ops
		. append(
			{
				"type": "circle",
				"center": [center.x, center.y],
				"radius": radius,
				"color": color,
				"width": width,
			}
		)
	)


func _icon_rect(ops: Array, rect: Array, color: Array) -> void:
	ops.append({"type": "rect", "rect": rect, "color": color, "width": 0})


func _icon_polygon(ops: Array, points: Array, color: Array, width: int) -> void:
	ops.append({"type": "polygon", "points": points, "color": color, "width": width})


static func _ease_out_back(t: float) -> float:
	var c1 := EASE_C1
	var c3 := c1 + 1.0
	var t1 := t - 1.0
	return 1.0 + c3 * (t1 * t1 * t1) + c1 * (t1 * t1)
