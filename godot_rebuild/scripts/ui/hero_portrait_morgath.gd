extends RefCounted
## Native canvas painter for Morgath, the Boss/Temporal Mage Hero Shop portrait.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(17, 16, 40)
	var robe := Color8(34, 41, 82)
	var mantle := Color8(53, 63, 112)
	var silver := Color8(171, 184, 214)
	var pale := Color8(222, 232, 246)
	var skin := Color8(204, 178, 162)
	var hair := Color8(72, 96, 133)
	var gold := Color8(223, 186, 112)
	var chronal := Color8(100, 221, 233)
	var arcane := Color8(126, 118, 231)

	_backdrop(canvas, box, Color8(41, 43, 98), Color8(8, 13, 34))
	canvas.draw_arc(
		_p(box, 48.0, 43.0),
		37.0 * unit,
		-PI * 0.88,
		PI * 0.14,
		32,
		Color(chronal.r, chronal.g, chronal.b, 0.26),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 43.0),
		29.0 * unit,
		PI * 0.18,
		PI * 0.90,
		28,
		Color(gold.r, gold.g, gold.b, 0.23),
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 15.0, 39.0), _p(box, 22.0, 36.0), chronal, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 73.0, 38.0), _p(box, 80.0, 41.0), gold, maxf(1.5 * unit, 1.0), true)

	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 88.0),
			Vector2(17.0, 66.0),
			Vector2(28.0, 57.0),
			Vector2(39.0, 52.0),
			Vector2(57.0, 52.0),
			Vector2(70.0, 60.0),
			Vector2(83.0, 88.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(20.0, 86.0),
			Vector2(25.0, 68.0),
			Vector2(36.0, 60.0),
			Vector2(48.0, 57.0),
			Vector2(60.0, 60.0),
			Vector2(71.0, 68.0),
			Vector2(76.0, 86.0),
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(21.0, 64.0),
			Vector2(25.0, 56.0),
			Vector2(37.0, 53.0),
			Vector2(48.0, 61.0),
			Vector2(59.0, 53.0),
			Vector2(72.0, 57.0),
			Vector2(78.0, 67.0),
			Vector2(67.0, 75.0),
			Vector2(57.0, 68.0),
			Vector2(48.0, 74.0),
			Vector2(38.0, 68.0),
			Vector2(29.0, 75.0),
		],
		mantle
	)
	canvas.draw_line(_p(box, 28.0, 63.0), _p(box, 38.0, 58.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 58.0, 58.0), _p(box, 69.0, 63.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 70.0), _p(box, 48.0, 86.0), silver, maxf(2.0 * unit, 1.0), true)

	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 29.0),
			Vector2(33.0, 20.0),
			Vector2(42.0, 11.0),
			Vector2(52.0, 10.0),
			Vector2(62.0, 18.0),
			Vector2(66.0, 31.0),
			Vector2(63.0, 42.0),
			Vector2(57.0, 51.0),
			Vector2(48.0, 55.0),
			Vector2(38.0, 51.0),
			Vector2(32.0, 42.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 27.0),
			Vector2(42.0, 20.0),
			Vector2(52.0, 19.0),
			Vector2(59.0, 26.0),
			Vector2(60.0, 38.0),
			Vector2(54.0, 47.0),
			Vector2(47.0, 50.0),
			Vector2(40.0, 46.0),
			Vector2(36.0, 38.0),
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 30.0),
			Vector2(29.0, 20.0),
			Vector2(37.0, 12.0),
			Vector2(45.0, 8.0),
			Vector2(56.0, 11.0),
			Vector2(65.0, 20.0),
			Vector2(64.0, 28.0),
			Vector2(57.0, 23.0),
			Vector2(50.0, 18.0),
			Vector2(42.0, 19.0),
			Vector2(36.0, 26.0),
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 22.0),
			Vector2(41.0, 16.0),
			Vector2(53.0, 16.0),
			Vector2(63.0, 23.0),
			Vector2(58.0, 27.0),
			Vector2(50.0, 23.0),
			Vector2(42.0, 23.0),
			Vector2(36.0, 28.0),
		],
		gold
	)
	canvas.draw_line(_p(box, 39.0, 33.0), _p(box, 45.0, 32.0), outline, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 32.0), _p(box, 58.0, 33.0), outline, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 42.0, 34.0), 1.5 * unit, chronal)
	canvas.draw_circle(_p(box, 55.0, 34.0), 1.5 * unit, chronal)
	_fill(
		canvas,
		box,
		[
			Vector2(38.0, 39.0),
			Vector2(45.0, 42.0),
			Vector2(52.0, 41.0),
			Vector2(58.0, 38.0),
			Vector2(55.0, 48.0),
			Vector2(48.0, 55.0),
			Vector2(41.0, 49.0),
		],
		pale
	)
	canvas.draw_line(_p(box, 44.0, 42.0), _p(box, 51.0, 42.0), silver, maxf(1.5 * unit, 1.0), true)

	canvas.draw_arc(
		_p(box, 48.0, 70.0),
		8.0 * unit,
		-PI * 0.85,
		PI * 0.85,
		24,
		gold,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 48.0, 70.0), 3.0 * unit, chronal)
	canvas.draw_line(_p(box, 48.0, 70.0), _p(box, 48.0, 65.0), outline, maxf(1.5 * unit, 1.0))
	canvas.draw_line(_p(box, 48.0, 70.0), _p(box, 52.0, 72.0), outline, maxf(1.5 * unit, 1.0))
	canvas.draw_circle(_p(box, 48.0, 70.0), 1.0 * unit, pale)

	canvas.draw_circle(_p(box, 74.0, 53.0), 8.0 * unit, Color(arcane.r, arcane.g, arcane.b, 0.28))
	canvas.draw_arc(
		_p(box, 74.0, 53.0),
		6.0 * unit,
		-PI * 0.82,
		PI * 0.62,
		20,
		chronal,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 74.0, 53.0), _p(box, 74.0, 49.0), pale, maxf(1.2 * unit, 1.0))
	canvas.draw_line(_p(box, 74.0, 53.0), _p(box, 77.0, 54.0), pale, maxf(1.2 * unit, 1.0))
	canvas.draw_circle(_p(box, 74.0, 53.0), 1.5 * unit, gold)


static func _fill(canvas: CanvasItem, box: Rect2, points: Array[Vector2], color: Color) -> void:
	canvas.draw_colored_polygon(_poly(box, points), color)


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
