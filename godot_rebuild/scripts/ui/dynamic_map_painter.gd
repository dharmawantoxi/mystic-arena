extends RefCounted
## Native CanvasItem painter for DynamicRenderer's source-ordered ops.


static func draw(canvas: CanvasItem, operations: Array) -> void:
	for value in operations:
		var op: Dictionary = value
		var color := _color(op)
		match String(op.get("kind", "")):
			"rect":
				var rect := _rect(op["rect"])
				var width := int(op.get("width", 0))
				canvas.draw_rect(rect, color, width == 0, float(maxi(1, width)))
			"circle":
				var center := _point(op["center"])
				var radius := float(op["radius"])
				var width := int(op.get("width", 0))
				if width == 0:
					canvas.draw_circle(center, radius, color)
				else:
					canvas.draw_arc(center, radius, 0.0, TAU, 24, color, float(width), true)
			"ellipse":
				canvas.draw_colored_polygon(_ellipse_points(_rect(op["rect"]), 0.0, TAU, 40), color)
			"line":
				canvas.draw_line(
					_point(op["a"]), _point(op["b"]), color, float(op.get("width", 1)), true
				)
			"arc":
				var points := _ellipse_points(
					_rect(op["rect"]), float(op["start"]), float(op["end"]), 24
				)
				canvas.draw_polyline(points, color, float(op.get("width", 1)), true)


static func _rect(values: Array) -> Rect2:
	return Rect2(float(values[0]), float(values[1]), float(values[2]), float(values[3]))


static func _point(values: Array) -> Vector2:
	return Vector2(float(values[0]), float(values[1]))


static func _color(op: Dictionary) -> Color:
	var rgba: Array = op["color"]
	var alpha := int(float(rgba[3]) * float(op.get("mult", 255)) / 255.0)
	return Color8(int(rgba[0]), int(rgba[1]), int(rgba[2]), alpha)


static func _ellipse_points(
	rect: Rect2, start: float, end: float, segments: int
) -> PackedVector2Array:
	var points := PackedVector2Array()
	var center := rect.get_center()
	var radii := rect.size * 0.5
	var closed := absf(end - start) >= TAU - 0.001
	var count := segments if closed else segments + 1
	for index in range(count):
		var angle := lerpf(start, end, float(index) / float(segments))
		points.append(center + Vector2(cos(angle) * radii.x, sin(angle) * radii.y))
	return points
