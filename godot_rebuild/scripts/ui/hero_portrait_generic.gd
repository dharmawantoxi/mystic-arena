extends RefCounted
## Deterministic generic Hero Shop bust for heroes without a custom portrait.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2, hue: float, accent: Color) -> void:
	var unit := box.size.x / SIZE
	var dark := Color.from_hsv(hue, 0.55, 0.22)
	var body := Color.from_hsv(hue, 0.42, 0.62)
	var light := Color.from_hsv(hue, 0.30, 0.86)

	_backdrop(canvas, box, dark, Color.from_hsv(hue, 0.45, 0.10))
	canvas.draw_circle(_p(box, 48.0, 44.0), 27.0 * unit, Color.from_hsv(hue, 0.40, 0.30))
	canvas.draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(26.0, 88.0),
				Vector2(32.0, 58.0),
				Vector2(48.0, 50.0),
				Vector2(64.0, 58.0),
				Vector2(70.0, 88.0)
			]
		),
		body
	)
	canvas.draw_circle(_p(box, 48.0, 34.0), 12.0 * unit, light)
	canvas.draw_rect(Rect2(_p(box, 40.0, 31.0), Vector2(16.0, 4.0) * unit), dark)
	canvas.draw_rect(Rect2(_p(box, 26.0, 88.0), Vector2(44.0, 4.0) * unit), accent)


static func _scale(box: Rect2) -> float:
	return box.size.x / SIZE


static func _p(box: Rect2, x: float, y: float) -> Vector2:
	return box.position + Vector2(x, y) * _scale(box)


static func _poly(box: Rect2, points: Array[Vector2]) -> PackedVector2Array:
	var result := PackedVector2Array()
	for point in points:
		result.append(box.position + point * _scale(box))
	return result


static func _backdrop(canvas: CanvasItem, box: Rect2, top: Color, bottom: Color) -> void:
	var bands := 18
	var height := box.size.y / float(bands)
	for index in bands:
		var band := Rect2(
			box.position.x, box.position.y + height * float(index), box.size.x, height + 1.0
		)
		canvas.draw_rect(band, top.lerp(bottom, float(index) / float(bands - 1)))
