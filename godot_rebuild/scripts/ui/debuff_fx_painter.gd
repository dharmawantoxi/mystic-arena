extends RefCounted
## Layer 9bq10: paints the `boss_debuff_fx_layout.gd` ops outside the boss path, so the same
## source indicator (slow ring, burn flames, pip row) reaches heroes and minions without a
## second copy of the geometry. Only the three primitive kinds that layout emits exist here:
##
##   "rect"    fill, or a `width` px border drawn inside the rect like pygame
##   "circle"  fill, or a `width` px border centred on the radius
##   "ellipse" fill, or a `width` px border pulled in by half the stroke like pygame
##
## `mult` is always 255 in this layout (raw source tuples), so the op colour is used as is.


static func paint(canvas: CanvasItem, ops: Array) -> void:
	for op in ops:
		_paint_op(canvas, op)


static func _paint_op(canvas: CanvasItem, op: Dictionary) -> void:
	var color := _color(op)
	if color.a <= 0.0:
		return
	var width := int(op.get("width", 0))
	match String(op.get("kind", "")):
		"rect", "fill":
			var box: Array = op.get("rect", [0, 0, 0, 0])
			var rect := Rect2(float(box[0]), float(box[1]), float(box[2]), float(box[3]))
			if width > 0:
				canvas.draw_rect(rect, color, false, float(width))
			else:
				canvas.draw_rect(rect, color)
		"circle":
			var center: Array = op.get("center", [0, 0])
			var at := Vector2(float(center[0]), float(center[1]))
			var radius := float(op.get("radius", 1))
			if width > 0:
				canvas.draw_arc(at, radius, 0.0, TAU, 48, color, float(width), true)
			else:
				canvas.draw_circle(at, radius, color)
		"ellipse":
			var box: Array = op.get("rect", [0, 0, 0, 0])
			var rect := Rect2(float(box[0]), float(box[1]), float(box[2]), float(box[3]))
			if rect.size.x <= 0.0 or rect.size.y <= 0.0:
				return
			if width > 0:
				var path := _ellipse_outline(rect.grow(-float(width) * 0.5))
				path.append(path[0])
				canvas.draw_polyline(path, color, float(width), true)
			else:
				canvas.draw_colored_polygon(_ellipse_outline(rect), color)


static func _color(op: Dictionary) -> Color:
	var rgba: Array = op.get("color", [255, 255, 255, 255])
	var alpha := 255
	if rgba.size() > 3:
		alpha = int(rgba[3])
	return Color8(int(rgba[0]), int(rgba[1]), int(rgba[2]), alpha)


static func _ellipse_outline(rect: Rect2) -> PackedVector2Array:
	var center := rect.get_center()
	var radii := rect.size * 0.5
	var points := PackedVector2Array()
	for step in range(48):
		var angle := TAU * float(step) / 48.0
		points.append(center + Vector2(cos(angle) * radii.x, sin(angle) * radii.y))
	return points
