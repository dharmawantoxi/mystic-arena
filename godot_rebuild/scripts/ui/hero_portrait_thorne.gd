extends RefCounted
## Native canvas portrait: Thorne, The Quill Sprayer.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := _scale(box)
	var outline := Color8(38, 26, 10)
	var dark := Color8(96, 60, 14)
	var body := Color8(215, 155, 30)
	var shade := Color8(150, 95, 20)
	var light := Color8(245, 205, 110)
	var goop := Color8(120, 190, 90)

	_backdrop(canvas, box, Color8(58, 40, 18), Color8(26, 20, 12))
	var base := _p(box, 48.0, 52.0)
	for index in 7:
		var angle := -PI * 0.92 + PI * 0.84 * (float(index) / 6.0)
		var direction := Vector2(cos(angle), sin(angle))
		var tip := base + direction * 40.0 * unit
		var side := Vector2(-direction.y, direction.x) * 3.5 * unit
		canvas.draw_colored_polygon(PackedVector2Array([base - side, base + side, tip]), shade)
	canvas.draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(30.0, 38.0),
				Vector2(66.0, 38.0),
				Vector2(72.0, 62.0),
				Vector2(66.0, 86.0),
				Vector2(30.0, 86.0),
				Vector2(24.0, 62.0)
			]
		),
		dark
	)
	canvas.draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(34.0, 42.0),
				Vector2(62.0, 42.0),
				Vector2(67.0, 62.0),
				Vector2(62.0, 84.0),
				Vector2(34.0, 84.0),
				Vector2(29.0, 62.0)
			]
		),
		body
	)
	canvas.draw_colored_polygon(
		_poly(
			box,
			[Vector2(40.0, 50.0), Vector2(56.0, 50.0), Vector2(58.0, 66.0), Vector2(38.0, 66.0)]
		),
		light
	)
	canvas.draw_circle(_p(box, 48.0, 30.0), 11.0 * unit, body)
	canvas.draw_colored_polygon(
		_poly(box, [Vector2(54.0, 30.0), Vector2(72.0, 34.0), Vector2(54.0, 40.0)]), shade
	)
	canvas.draw_circle(_p(box, 43.0, 27.0), 2.2 * unit, outline)
	canvas.draw_circle(_p(box, 51.0, 27.0), 2.2 * unit, outline)
	canvas.draw_circle(_p(box, 77.0, 38.0), 3.0 * unit, goop)
	canvas.draw_circle(_p(box, 85.0, 45.0), 2.0 * unit, goop)


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
