extends RefCounted
## Native canvas painter for Gornak, the Boss/Anti-Mage Hero Shop portrait.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(20, 19, 37)
	var armor := Color8(66, 55, 76)
	var plate := Color8(119, 101, 117)
	var steel := Color8(183, 174, 186)
	var skin := Color8(135, 129, 145)
	var shadow := Color8(69, 58, 83)
	var horn := Color8(180, 141, 111)
	var aether := Color8(190, 83, 226)
	var ward := Color8(89, 228, 221)

	_backdrop(canvas, box, Color8(69, 40, 79), Color8(14, 18, 35))
	canvas.draw_arc(
		_p(box, 48.0, 43.0),
		36.0 * unit,
		-PI * 0.86,
		PI * 0.24,
		32,
		Color(aether.r, aether.g, aether.b, 0.28),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 43.0),
		28.0 * unit,
		PI * 0.18,
		PI * 0.92,
		28,
		Color(ward.r, ward.g, ward.b, 0.22),
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_colored_polygon(
		_poly(
			box, [Vector2(35.0, 30.0), Vector2(25.0, 8.0), Vector2(30.0, 28.0), Vector2(38.0, 36.0)]
		),
		horn
	)
	canvas.draw_colored_polygon(
		_poly(
			box, [Vector2(57.0, 30.0), Vector2(67.0, 8.0), Vector2(63.0, 29.0), Vector2(55.0, 36.0)]
		),
		horn
	)

	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(12.0, 88.0),
					Vector2(17.0, 67.0),
					Vector2(26.0, 58.0),
					Vector2(37.0, 53.0),
					Vector2(42.0, 50.0),
					Vector2(54.0, 50.0),
					Vector2(63.0, 54.0),
					Vector2(74.0, 58.0),
					Vector2(82.0, 69.0),
					Vector2(85.0, 88.0),
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
					Vector2(18.0, 86.0),
					Vector2(23.0, 68.0),
					Vector2(33.0, 61.0),
					Vector2(42.0, 57.0),
					Vector2(49.0, 62.0),
					Vector2(57.0, 57.0),
					Vector2(66.0, 61.0),
					Vector2(75.0, 68.0),
					Vector2(79.0, 86.0),
				],
			),
			armor
		)
	)
	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(20.0, 64.0),
					Vector2(24.0, 55.0),
					Vector2(37.0, 54.0),
					Vector2(43.0, 62.0),
					Vector2(38.0, 72.0),
					Vector2(22.0, 72.0),
				],
			),
			steel
		)
	)
	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(54.0, 62.0),
					Vector2(60.0, 54.0),
					Vector2(72.0, 56.0),
					Vector2(80.0, 67.0),
					Vector2(76.0, 73.0),
					Vector2(60.0, 71.0),
				],
			),
			steel
		)
	)
	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(24.0, 62.0),
					Vector2(28.0, 58.0),
					Vector2(36.0, 58.0),
					Vector2(39.0, 63.0),
					Vector2(35.0, 68.0),
					Vector2(25.0, 68.0),
				],
			),
			plate
		)
	)
	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(57.0, 63.0),
					Vector2(61.0, 58.0),
					Vector2(69.0, 59.0),
					Vector2(75.0, 67.0),
					Vector2(72.0, 69.0),
					Vector2(62.0, 68.0),
				],
			),
			plate
		)
	)
	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(36.0, 61.0),
					Vector2(48.0, 58.0),
					Vector2(60.0, 62.0),
					Vector2(57.0, 79.0),
					Vector2(48.0, 85.0),
					Vector2(39.0, 80.0),
				],
			),
			plate
		)
	)
	canvas.draw_line(_p(box, 35.0, 68.0), _p(box, 42.0, 74.0), steel, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 61.0, 68.0), _p(box, 54.0, 74.0), steel, maxf(2.0 * unit, 1.0), true)

	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(31.0, 28.0),
					Vector2(31.0, 19.0),
					Vector2(39.0, 11.0),
					Vector2(48.0, 8.0),
					Vector2(58.0, 12.0),
					Vector2(65.0, 22.0),
					Vector2(64.0, 39.0),
					Vector2(58.0, 50.0),
					Vector2(48.0, 55.0),
					Vector2(38.0, 51.0),
					Vector2(32.0, 41.0),
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
					Vector2(36.0, 26.0),
					Vector2(42.0, 19.0),
					Vector2(50.0, 18.0),
					Vector2(58.0, 24.0),
					Vector2(59.0, 38.0),
					Vector2(54.0, 47.0),
					Vector2(47.0, 51.0),
					Vector2(40.0, 47.0),
					Vector2(36.0, 39.0),
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
					Vector2(31.0, 28.0),
					Vector2(30.0, 20.0),
					Vector2(39.0, 11.0),
					Vector2(48.0, 8.0),
					Vector2(59.0, 13.0),
					Vector2(66.0, 23.0),
					Vector2(62.0, 30.0),
					Vector2(56.0, 25.0),
					Vector2(49.0, 21.0),
					Vector2(41.0, 23.0),
					Vector2(36.0, 31.0),
				],
			),
			armor
		)
	)
	canvas.draw_line(_p(box, 38.0, 24.0), _p(box, 47.0, 19.0), steel, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 19.0), _p(box, 60.0, 24.0), steel, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 40.0, 33.0), _p(box, 45.0, 32.0), ward, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 32.0), _p(box, 57.0, 33.0), ward, maxf(2.5 * unit, 1.0), true)
	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(37.0, 39.0),
					Vector2(44.0, 42.0),
					Vector2(51.0, 42.0),
					Vector2(58.0, 38.0),
					Vector2(56.0, 48.0),
					Vector2(48.0, 52.0),
					Vector2(40.0, 48.0),
				],
			),
			shadow
		)
	)
	canvas.draw_circle(_p(box, 40.0, 44.0), 2.0 * unit, horn)
	canvas.draw_circle(_p(box, 56.0, 44.0), 2.0 * unit, horn)
	canvas.draw_arc(
		_p(box, 48.0, 71.0),
		9.0 * unit,
		-PI * 0.82,
		PI * 0.82,
		24,
		aether,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 48.0, 71.0), 4.0 * unit, aether)
	(
		canvas
		. draw_colored_polygon(
			_poly(
				box,
				[
					Vector2(48.0, 64.0),
					Vector2(51.0, 71.0),
					Vector2(48.0, 78.0),
					Vector2(45.0, 71.0),
				],
			),
			Color8(244, 220, 255)
		)
	)


static func _p(box: Rect2, x: float, y: float) -> Vector2:
	return box.position + Vector2(x, y) * (box.size.x / SIZE)


static func _poly(box: Rect2, points: Array[Vector2]) -> PackedVector2Array:
	var result := PackedVector2Array()
	for point in points:
		result.append(box.position + point * (box.size.x / SIZE))
	return result


static func _backdrop(canvas: CanvasItem, box: Rect2, top: Color, bottom: Color) -> void:
	var bands := 18
	var height := box.size.y / float(bands)
	for index in bands:
		var band := Rect2(
			box.position.x, box.position.y + height * float(index), box.size.x, height + 1.0
		)
		canvas.draw_rect(band, top.lerp(bottom, float(index) / float(bands - 1)))
