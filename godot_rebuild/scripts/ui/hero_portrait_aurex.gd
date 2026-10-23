extends RefCounted
## Native canvas portrait: Aurex, The Omega Knight.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(20, 26, 39)
	var steel := Color8(67, 83, 105)
	var shade := Color8(38, 49, 70)
	var silver := Color8(166, 185, 203)
	var gold := Color8(216, 167, 71)
	var light := Color8(255, 226, 151)
	var magic := Color8(116, 227, 244)
	var cape := Color8(55, 42, 97)
	_backdrop(canvas, box, Color8(37, 54, 79), Color8(16, 23, 37))

	# Broken luminous rings frame a fully enclosed, angular knight helm.
	canvas.draw_arc(
		_p(box, 47.0, 39.0),
		32.0 * unit,
		PI * -0.94,
		PI * -0.2,
		48,
		gold,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 47.0, 39.0),
		36.0 * unit,
		PI * 0.05,
		PI * 0.54,
		48,
		magic,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 14.0, 48.0), _p(box, 19.0, 44.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 73.0, 12.0), _p(box, 79.0, 17.0), magic, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 96.0),
			Vector2(17.0, 67.0),
			Vector2(31.0, 56.0),
			Vector2(61.0, 56.0),
			Vector2(78.0, 69.0),
			Vector2(86.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 94.0),
			Vector2(22.0, 69.0),
			Vector2(32.0, 60.0),
			Vector2(60.0, 60.0),
			Vector2(73.0, 71.0),
			Vector2(80.0, 94.0)
		],
		cape
	)

	# Faceted breastplate, deep collar and stepped shoulder plates.
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 62.0),
			Vector2(44.0, 56.0),
			Vector2(59.0, 61.0),
			Vector2(68.0, 94.0),
			Vector2(26.0, 94.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 65.0),
			Vector2(44.0, 61.0),
			Vector2(55.0, 65.0),
			Vector2(62.0, 92.0),
			Vector2(32.0, 92.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[Vector2(34.0, 65.0), Vector2(45.0, 71.0), Vector2(44.0, 83.0), Vector2(36.0, 78.0)],
		silver
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 71.0), Vector2(55.0, 66.0), Vector2(61.0, 82.0), Vector2(49.0, 88.0)],
		shade
	)
	canvas.draw_line(_p(box, 37.0, 85.0), _p(box, 44.0, 89.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 89.0), _p(box, 60.0, 85.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 66.0),
			Vector2(21.0, 53.0),
			Vector2(33.0, 57.0),
			Vector2(39.0, 68.0),
			Vector2(31.0, 82.0),
			Vector2(15.0, 79.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 66.0),
			Vector2(23.0, 58.0),
			Vector2(30.0, 61.0),
			Vector2(34.0, 68.0),
			Vector2(29.0, 76.0),
			Vector2(18.0, 75.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 66.0),
			Vector2(23.0, 58.0),
			Vector2(30.0, 61.0),
			Vector2(29.0, 64.0),
			Vector2(23.0, 62.0),
			Vector2(18.0, 69.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(85.0, 66.0),
			Vector2(74.0, 53.0),
			Vector2(62.0, 57.0),
			Vector2(55.0, 68.0),
			Vector2(63.0, 82.0),
			Vector2(80.0, 79.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(80.0, 66.0),
			Vector2(72.0, 58.0),
			Vector2(65.0, 61.0),
			Vector2(60.0, 68.0),
			Vector2(65.0, 76.0),
			Vector2(77.0, 75.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(80.0, 66.0),
			Vector2(72.0, 58.0),
			Vector2(65.0, 61.0),
			Vector2(66.0, 64.0),
			Vector2(72.0, 62.0),
			Vector2(77.0, 69.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 28.0),
			Vector2(36.0, 18.0),
			Vector2(54.0, 16.0),
			Vector2(65.0, 26.0),
			Vector2(66.0, 43.0),
			Vector2(58.0, 56.0),
			Vector2(44.0, 61.0),
			Vector2(32.0, 51.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 29.0),
			Vector2(39.0, 22.0),
			Vector2(53.0, 21.0),
			Vector2(60.0, 29.0),
			Vector2(61.0, 42.0),
			Vector2(55.0, 52.0),
			Vector2(45.0, 56.0),
			Vector2(36.0, 48.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 29.0),
			Vector2(40.0, 23.0),
			Vector2(46.0, 22.0),
			Vector2(45.0, 35.0),
			Vector2(35.0, 37.0)
		],
		silver
	)
	_fill(
		canvas,
		box,
		[
			Vector2(49.0, 22.0),
			Vector2(54.0, 23.0),
			Vector2(60.0, 30.0),
			Vector2(61.0, 41.0),
			Vector2(53.0, 48.0),
			Vector2(49.0, 37.0)
		],
		shade
	)

	# A swept central crest, gold brow and an unbroken cyan visor slit.
	_fill(
		canvas,
		box,
		[
			Vector2(39.0, 21.0),
			Vector2(43.0, 9.0),
			Vector2(48.0, 14.0),
			Vector2(54.0, 8.0),
			Vector2(55.0, 22.0),
			Vector2(49.0, 27.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(43.0, 20.0),
			Vector2(45.0, 14.0),
			Vector2(48.0, 19.0),
			Vector2(51.0, 15.0),
			Vector2(51.0, 22.0),
			Vector2(48.0, 24.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 34.0),
			Vector2(46.0, 31.0),
			Vector2(62.0, 34.0),
			Vector2(61.0, 41.0),
			Vector2(46.0, 39.0),
			Vector2(34.0, 42.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 33.0),
			Vector2(46.0, 30.0),
			Vector2(60.0, 32.0),
			Vector2(61.0, 34.0),
			Vector2(46.0, 33.0),
			Vector2(35.0, 36.0)
		],
		gold
	)
	canvas.draw_line(_p(box, 36.0, 38.0), _p(box, 45.0, 36.0), magic, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 49.0, 36.0), _p(box, 59.0, 37.0), magic, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(45.0, 39.0),
			Vector2(49.0, 39.0),
			Vector2(52.0, 49.0),
			Vector2(46.0, 54.0),
			Vector2(41.0, 49.0)
		],
		silver
	)
	canvas.draw_line(_p(box, 46.0, 42.0), _p(box, 46.0, 50.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 35.0, 47.0), _p(box, 40.0, 51.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 54.0, 51.0), _p(box, 59.0, 46.0), gold, maxf(1.5 * unit, 1.0), true)

	# The omega chest sigil is drawn as an open arc with two squared feet.
	canvas.draw_arc(
		_p(box, 47.0, 76.0), 9.0 * unit, PI * 0.77, PI * 2.23, 48, ink, maxf(4.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 47.0, 76.0),
		7.0 * unit,
		PI * 0.23,
		PI * 2.77,
		48,
		light,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 38.0, 82.0), _p(box, 43.0, 82.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 82.0), _p(box, 56.0, 82.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 47.0, 75.0), 2.0 * unit, magic)

	# A broad rune sword rises at the side, with a dark gauntlet on its grip.
	_fill(
		canvas,
		box,
		[
			Vector2(76.0, 9.0),
			Vector2(84.0, 23.0),
			Vector2(83.0, 65.0),
			Vector2(73.0, 65.0),
			Vector2(72.0, 23.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 15.0),
			Vector2(80.0, 24.0),
			Vector2(80.0, 61.0),
			Vector2(76.0, 61.0),
			Vector2(75.0, 24.0)
		],
		silver
	)
	_fill(
		canvas,
		box,
		[Vector2(77.0, 22.0), Vector2(79.0, 26.0), Vector2(79.0, 58.0), Vector2(77.0, 58.0)],
		shade
	)
	canvas.draw_line(_p(box, 78.0, 29.0), _p(box, 78.0, 51.0), magic, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 68.0, 67.0), _p(box, 88.0, 67.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 69.0, 67.0), _p(box, 87.0, 67.0), gold, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 70.0), _p(box, 78.0, 93.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 71.0), _p(box, 78.0, 92.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(69.0, 78.0),
			Vector2(78.0, 75.0),
			Vector2(84.0, 81.0),
			Vector2(82.0, 89.0),
			Vector2(73.0, 89.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(73.0, 80.0),
			Vector2(78.0, 79.0),
			Vector2(80.0, 82.0),
			Vector2(79.0, 86.0),
			Vector2(74.0, 86.0)
		],
		steel
	)
	canvas.draw_circle(_p(box, 78.0, 93.0), 2.0 * unit, magic)


static func _fill(canvas: CanvasItem, box: Rect2, points: Array[Vector2], color: Color) -> void:
	canvas.draw_colored_polygon(_poly(box, points), color)


static func _poly(box: Rect2, points: Array[Vector2]) -> PackedVector2Array:
	var result := PackedVector2Array()
	for point in points:
		result.append(_p(box, point.x, point.y))
	return result


static func _p(box: Rect2, x: float, y: float) -> Vector2:
	return box.position + Vector2(x, y) * box.size.x / SIZE


static func _backdrop(canvas: CanvasItem, box: Rect2, top: Color, bottom: Color) -> void:
	var bands := 18
	var height := box.size.y / float(bands)
	for index in bands:
		var band := Rect2(
			box.position.x, box.position.y + height * float(index), box.size.x, height + 1.0
		)
		canvas.draw_rect(band, top.lerp(bottom, float(index) / float(bands - 1)))
