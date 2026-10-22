extends RefCounted
## Existing Zephyr painter extracted without geometry or palette changes.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := _scale(box)
	var outline := Color8(14, 25, 41)
	var cloak := Color8(24, 63, 77)
	var robe := Color8(33, 115, 125)
	var trim := Color8(130, 224, 212)
	var skin := Color8(222, 179, 133)
	var hair := Color8(15, 39, 53)
	var wind := Color8(71, 227, 227)
	var gold := Color8(241, 197, 119)

	_backdrop(canvas, box, Color8(17, 79, 101), Color8(8, 19, 36))
	canvas.draw_arc(
		_p(box, 48.0, 43.0),
		36.0 * unit,
		-PI * 0.93,
		PI * 0.06,
		32,
		Color(wind.r, wind.g, wind.b, 0.28),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 43.0),
		29.0 * unit,
		PI * 0.14,
		PI * 0.93,
		28,
		Color(trim.r, trim.g, trim.b, 0.22),
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 12.0, 44.0), _p(box, 25.0, 39.0), wind, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 15.0, 49.0), _p(box, 26.0, 46.0), trim, maxf(1.0 * unit, 1.0), true)

	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(15.0, 88.0),
					Vector2(21.0, 64.0),
					Vector2(34.0, 54.0),
					Vector2(43.0, 51.0),
					Vector2(55.0, 52.0),
					Vector2(70.0, 59.0),
					Vector2(81.0, 88.0),
				],
			),
			outline
		)
	)
	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(21.0, 86.0),
					Vector2(27.0, 67.0),
					Vector2(37.0, 59.0),
					Vector2(45.0, 62.0),
					Vector2(48.0, 72.0),
					Vector2(55.0, 61.0),
					Vector2(66.0, 63.0),
					Vector2(74.0, 86.0),
				],
			),
			robe
		)
	)
	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(34.0, 53.0),
					Vector2(42.0, 49.0),
					Vector2(48.0, 58.0),
					Vector2(55.0, 50.0),
					Vector2(64.0, 55.0),
					Vector2(56.0, 68.0),
					Vector2(48.0, 73.0),
					Vector2(40.0, 67.0),
				],
			),
			trim
		)
	)
	canvas.draw_line(_p(box, 48.0, 59.0), _p(box, 48.0, 84.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 63.0), 3.0 * unit, gold)

	canvas.draw_line(_p(box, 59.0, 67.0), _p(box, 70.0, 57.0), outline, maxf(7.0 * unit, 2.0), true)
	canvas.draw_line(_p(box, 59.0, 67.0), _p(box, 70.0, 57.0), trim, maxf(3.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 72.0, 54.0), 7.0 * unit, Color(wind.r, wind.g, wind.b, 0.22))
	canvas.draw_arc(
		_p(box, 72.0, 54.0),
		6.0 * unit,
		-PI * 0.85,
		PI * 0.45,
		20,
		wind,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 72.0, 54.0), 2.5 * unit, Color8(222, 255, 241))

	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(30.0, 34.0),
					Vector2(31.0, 22.0),
					Vector2(41.0, 11.0),
					Vector2(53.0, 10.0),
					Vector2(64.0, 21.0),
					Vector2(67.0, 36.0),
					Vector2(62.0, 49.0),
					Vector2(56.0, 55.0),
					Vector2(38.0, 54.0),
					Vector2(32.0, 45.0),
				],
			),
			outline
		)
	)
	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(34.0, 32.0),
					Vector2(36.0, 23.0),
					Vector2(44.0, 16.0),
					Vector2(54.0, 17.0),
					Vector2(61.0, 25.0),
					Vector2(62.0, 38.0),
					Vector2(56.0, 48.0),
					Vector2(40.0, 48.0),
					Vector2(35.0, 41.0),
				],
			),
			cloak
		)
	)
	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(39.0, 25.0),
					Vector2(46.0, 20.0),
					Vector2(56.0, 23.0),
					Vector2(60.0, 31.0),
					Vector2(58.0, 41.0),
					Vector2(52.0, 47.0),
					Vector2(42.0, 45.0),
					Vector2(37.0, 38.0),
				],
			),
			skin
		)
	)
	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(31.0, 34.0),
					Vector2(30.0, 22.0),
					Vector2(41.0, 12.0),
					Vector2(52.0, 14.0),
					Vector2(63.0, 23.0),
					Vector2(58.0, 26.0),
					Vector2(50.0, 22.0),
					Vector2(43.0, 27.0),
					Vector2(37.0, 33.0),
				],
			),
			hair
		)
	)
	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(50.0, 18.0),
					Vector2(67.0, 13.0),
					Vector2(61.0, 22.0),
					Vector2(56.0, 26.0),
				],
			),
			wind
		)
	)
	canvas.draw_line(_p(box, 42.0, 33.0), _p(box, 46.0, 32.0), outline, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 32.0), _p(box, 57.0, 33.0), outline, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 44.0, 34.0), 1.2 * unit, wind)
	canvas.draw_circle(_p(box, 55.0, 34.0), 1.2 * unit, wind)
	canvas.draw_line(
		_p(box, 49.0, 35.0), _p(box, 47.0, 40.0), Color8(148, 105, 79), maxf(1.3 * unit, 1.0)
	)
	canvas.draw_line(
		_p(box, 44.0, 43.0), _p(box, 53.0, 43.0), Color8(113, 69, 61), maxf(1.4 * unit, 1.0)
	)


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
