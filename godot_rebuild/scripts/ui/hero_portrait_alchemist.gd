extends RefCounted
## Native canvas painter for Alchemist, The Greed is Good Boss/Bruiser portrait.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(32, 21, 17)
	var leather := Color8(76, 43, 25)
	var bronze := Color8(143, 92, 42)
	var gold := Color8(234, 183, 63)
	var skin := Color8(177, 137, 84)
	var mask := Color8(54, 63, 48)
	var emerald := Color8(133, 224, 94)
	var glass := Color8(81, 215, 115)
	var shade := Color8(45, 65, 39)

	_backdrop(canvas, box, Color8(92, 59, 27), Color8(19, 20, 15))
	canvas.draw_arc(
		_p(box, 48.0, 43.0),
		36.0 * unit,
		-PI * 0.90,
		PI * 0.18,
		32,
		Color(gold.r, gold.g, gold.b, 0.24),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 43.0),
		28.0 * unit,
		PI * 0.20,
		PI * 0.88,
		28,
		Color(emerald.r, emerald.g, emerald.b, 0.20),
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 17.0, 34.0), 3.0 * unit, gold)
	canvas.draw_circle(_p(box, 78.0, 34.0), 2.5 * unit, emerald)

	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 88.0),
			Vector2(15.0, 68.0),
			Vector2(25.0, 58.0),
			Vector2(38.0, 53.0),
			Vector2(58.0, 53.0),
			Vector2(72.0, 60.0),
			Vector2(84.0, 88.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 86.0),
			Vector2(22.0, 68.0),
			Vector2(32.0, 61.0),
			Vector2(44.0, 57.0),
			Vector2(57.0, 59.0),
			Vector2(70.0, 67.0),
			Vector2(76.0, 86.0),
		],
		leather
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 66.0),
			Vector2(24.0, 56.0),
			Vector2(37.0, 54.0),
			Vector2(44.0, 62.0),
			Vector2(38.0, 74.0),
			Vector2(23.0, 73.0),
		],
		bronze
	)
	_fill(
		canvas,
		box,
		[
			Vector2(53.0, 62.0),
			Vector2(60.0, 54.0),
			Vector2(73.0, 58.0),
			Vector2(80.0, 69.0),
			Vector2(74.0, 74.0),
			Vector2(58.0, 72.0),
		],
		bronze
	)
	canvas.draw_line(_p(box, 26.0, 63.0), _p(box, 37.0, 59.0), gold, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 60.0, 59.0), _p(box, 72.0, 64.0), gold, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 59.0), _p(box, 48.0, 84.0), gold, maxf(2.0 * unit, 1.0), true)

	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 29.0),
			Vector2(31.0, 20.0),
			Vector2(39.0, 12.0),
			Vector2(51.0, 10.0),
			Vector2(62.0, 17.0),
			Vector2(66.0, 29.0),
			Vector2(64.0, 42.0),
			Vector2(57.0, 52.0),
			Vector2(47.0, 56.0),
			Vector2(37.0, 51.0),
			Vector2(31.0, 42.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 27.0),
			Vector2(42.0, 20.0),
			Vector2(53.0, 20.0),
			Vector2(59.0, 27.0),
			Vector2(59.0, 39.0),
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
			Vector2(30.0, 31.0),
			Vector2(28.0, 20.0),
			Vector2(37.0, 12.0),
			Vector2(50.0, 8.0),
			Vector2(62.0, 15.0),
			Vector2(68.0, 25.0),
			Vector2(62.0, 28.0),
			Vector2(55.0, 22.0),
			Vector2(47.0, 20.0),
			Vector2(39.0, 24.0),
			Vector2(34.0, 31.0),
		],
		leather
	)
	canvas.draw_line(_p(box, 34.0, 21.0), _p(box, 61.0, 21.0), gold, maxf(2.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 41.0, 34.0), 6.0 * unit, bronze)
	canvas.draw_circle(_p(box, 55.0, 34.0), 6.0 * unit, bronze)
	canvas.draw_circle(_p(box, 41.0, 34.0), 3.7 * unit, shade)
	canvas.draw_circle(_p(box, 55.0, 34.0), 3.7 * unit, shade)
	canvas.draw_circle(_p(box, 41.0, 34.0), 1.7 * unit, emerald)
	canvas.draw_circle(_p(box, 55.0, 34.0), 1.7 * unit, emerald)
	canvas.draw_line(_p(box, 46.0, 34.0), _p(box, 50.0, 34.0), gold, maxf(2.0 * unit, 1.0), true)

	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 39.0),
			Vector2(42.0, 41.0),
			Vector2(49.0, 41.0),
			Vector2(57.0, 38.0),
			Vector2(57.0, 47.0),
			Vector2(51.0, 51.0),
			Vector2(41.0, 49.0),
		],
		mask
	)
	canvas.draw_line(_p(box, 43.0, 44.0), _p(box, 44.0, 49.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 44.0), _p(box, 49.0, 49.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 47.0, 46.0), 2.0 * unit, emerald)

	canvas.draw_circle(_p(box, 48.0, 70.0), 8.0 * unit, gold)
	canvas.draw_circle(_p(box, 48.0, 70.0), 5.0 * unit, leather)
	canvas.draw_colored_polygon(
		_poly(
			box,
			[Vector2(48.0, 64.0), Vector2(52.0, 70.0), Vector2(48.0, 76.0), Vector2(44.0, 70.0)]
		),
		emerald
	)

	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 42.0),
			Vector2(77.0, 45.0),
			Vector2(81.0, 55.0),
			Vector2(78.0, 68.0),
			Vector2(66.0, 66.0),
			Vector2(63.0, 55.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(70.0, 46.0),
			Vector2(76.0, 48.0),
			Vector2(78.0, 56.0),
			Vector2(75.0, 64.0),
			Vector2(68.0, 62.0),
			Vector2(66.0, 55.0),
		],
		glass
	)
	canvas.draw_line(_p(box, 70.0, 42.0), _p(box, 77.0, 44.0), gold, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 74.0, 48.0), _p(box, 74.0, 60.0), Color8(214, 255, 187), maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 72.0, 53.0), 1.8 * unit, Color8(228, 255, 196))


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
