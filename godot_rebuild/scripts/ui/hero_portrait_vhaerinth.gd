extends RefCounted
## Native canvas portrait: Vhaerinth, The Ink Mage.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(20, 24, 39)
	var robe := Color8(44, 53, 75)
	var indigo := Color8(57, 79, 111)
	var wash := Color8(73, 145, 165)
	var parchment := Color8(220, 211, 180)
	var paper_shade := Color8(163, 156, 145)
	var skin := Color8(190, 173, 165)
	var shade := Color8(125, 111, 125)
	var silver := Color8(157, 176, 184)
	var light := Color8(225, 244, 222)
	_backdrop(canvas, box, Color8(50, 67, 88), Color8(20, 25, 41))

	# A parchment moon, calligraphic strokes and ink drops frame the scholar-mage.
	canvas.draw_circle(_p(box, 47.0, 39.0), 32.0 * unit, paper_shade)
	canvas.draw_arc(
		_p(box, 47.0, 39.0), 33.0 * unit, PI * 0.3, PI * 1.65, 56, wash, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 11.0, 26.0), _p(box, 20.0, 22.0), parchment, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 13.0, 32.0), _p(box, 23.0, 29.0), parchment, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 74.0, 17.0), _p(box, 85.0, 22.0), wash, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 15.0, 43.0), 2.5 * unit, ink)
	canvas.draw_circle(_p(box, 84.0, 34.0), 1.5 * unit, light)
	_fill(
		canvas,
		box,
		[Vector2(9.0, 52.0), Vector2(12.0, 45.0), Vector2(15.0, 52.0), Vector2(12.0, 56.0)],
		ink
	)

	# Broad robe sleeves carry parchment panels marked with native line-script.
	_fill(
		canvas,
		box,
		[
			Vector2(5.0, 96.0),
			Vector2(10.0, 72.0),
			Vector2(29.0, 56.0),
			Vector2(64.0, 56.0),
			Vector2(85.0, 72.0),
			Vector2(92.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 94.0),
			Vector2(17.0, 74.0),
			Vector2(31.0, 62.0),
			Vector2(61.0, 62.0),
			Vector2(78.0, 74.0),
			Vector2(85.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 94.0),
			Vector2(18.0, 75.0),
			Vector2(31.0, 66.0),
			Vector2(41.0, 79.0),
			Vector2(34.0, 94.0)
		],
		indigo
	)
	_fill(
		canvas,
		box,
		[
			Vector2(54.0, 78.0),
			Vector2(62.0, 65.0),
			Vector2(77.0, 75.0),
			Vector2(84.0, 94.0),
			Vector2(61.0, 94.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 66.0),
			Vector2(28.0, 57.0),
			Vector2(39.0, 65.0),
			Vector2(34.0, 80.0),
			Vector2(21.0, 82.0)
		],
		parchment
	)
	_fill(
		canvas,
		box,
		[
			Vector2(57.0, 65.0),
			Vector2(68.0, 57.0),
			Vector2(79.0, 67.0),
			Vector2(75.0, 82.0),
			Vector2(62.0, 80.0)
		],
		paper_shade
	)
	canvas.draw_line(_p(box, 23.0, 67.0), _p(box, 32.0, 70.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 22.0, 72.0), _p(box, 30.0, 75.0), wash, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 64.0, 69.0), _p(box, 73.0, 66.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 66.0, 75.0), _p(box, 73.0, 72.0), wash, maxf(1.5 * unit, 1.0), true)

	# An inkpot clasp and flowing written seams decorate the central robe.
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 65.0),
			Vector2(46.0, 72.0),
			Vector2(59.0, 65.0),
			Vector2(56.0, 82.0),
			Vector2(47.0, 89.0),
			Vector2(37.0, 82.0)
		],
		ink
	)
	canvas.draw_circle(_p(box, 47.0, 77.0), 6.0 * unit, silver)
	canvas.draw_circle(_p(box, 47.0, 77.0), 4.0 * unit, ink)
	canvas.draw_arc(_p(box, 47.0, 76.0), 2.5 * unit, PI, TAU, 20, wash, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 35.0, 87.0), _p(box, 40.0, 91.0), parchment, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 54.0, 91.0), _p(box, 60.0, 86.0), parchment, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 47.0, 85.0), _p(box, 47.0, 94.0), wash, maxf(1.5 * unit, 1.0), true)

	# The face wears round scholar lenses beneath a broad, tilted ink-stained hat.
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 31.0),
			Vector2(37.0, 22.0),
			Vector2(56.0, 21.0),
			Vector2(65.0, 31.0),
			Vector2(62.0, 48.0),
			Vector2(55.0, 58.0),
			Vector2(41.0, 58.0),
			Vector2(32.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 33.0),
			Vector2(41.0, 27.0),
			Vector2(54.0, 26.0),
			Vector2(60.0, 32.0),
			Vector2(58.0, 45.0),
			Vector2(53.0, 53.0),
			Vector2(43.0, 53.0),
			Vector2(37.0, 45.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 27.0),
			Vector2(59.0, 32.0),
			Vector2(59.0, 40.0),
			Vector2(55.0, 48.0),
			Vector2(50.0, 52.0),
			Vector2(47.0, 47.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(16.0, 32.0),
			Vector2(28.0, 24.0),
			Vector2(33.0, 12.0),
			Vector2(45.0, 3.0),
			Vector2(51.0, 14.0),
			Vector2(64.0, 20.0),
			Vector2(79.0, 31.0),
			Vector2(65.0, 36.0),
			Vector2(31.0, 36.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(25.0, 30.0),
			Vector2(33.0, 25.0),
			Vector2(37.0, 15.0),
			Vector2(45.0, 9.0),
			Vector2(49.0, 19.0),
			Vector2(61.0, 24.0),
			Vector2(69.0, 30.0),
			Vector2(60.0, 32.0),
			Vector2(34.0, 32.0)
		],
		indigo
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 26.0),
			Vector2(42.0, 23.0),
			Vector2(61.0, 24.0),
			Vector2(69.0, 30.0),
			Vector2(61.0, 32.0),
			Vector2(35.0, 30.0)
		],
		parchment
	)
	_fill(
		canvas,
		box,
		[Vector2(53.0, 24.0), Vector2(59.0, 25.0), Vector2(56.0, 30.0), Vector2(51.0, 29.0)],
		ink
	)
	canvas.draw_arc(_p(box, 41.0, 38.0), 4.5 * unit, 0.0, TAU, 28, ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_arc(_p(box, 54.0, 38.0), 4.5 * unit, 0.0, TAU, 28, ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 45.0, 38.0), _p(box, 50.0, 38.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 41.0, 38.0), 1.2 * unit, wash)
	canvas.draw_circle(_p(box, 54.0, 38.0), 1.2 * unit, light)
	canvas.draw_line(_p(box, 47.0, 40.0), _p(box, 45.0, 45.0), skin, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 42.0, 49.0), _p(box, 51.0, 48.0), ink, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 57.0, 43.0), _p(box, 55.0, 47.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 58.0, 47.0), 1.0 * unit, ink)

	# A long calligraphy brush, dark bristles and a wrapped grip form the focus.
	canvas.draw_line(_p(box, 77.0, 40.0), _p(box, 73.0, 96.0), ink, maxf(7.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 77.0, 40.0), _p(box, 73.0, 96.0), parchment, maxf(3.0 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 39.0),
			Vector2(75.0, 26.0),
			Vector2(82.0, 15.0),
			Vector2(86.0, 28.0),
			Vector2(83.0, 41.0),
			Vector2(78.0, 45.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(76.0, 36.0),
			Vector2(78.0, 27.0),
			Vector2(82.0, 21.0),
			Vector2(83.0, 29.0),
			Vector2(81.0, 37.0)
		],
		wash
	)
	canvas.draw_line(_p(box, 73.0, 43.0), _p(box, 83.0, 44.0), silver, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 80.0),
			Vector2(74.0, 75.0),
			Vector2(81.0, 79.0),
			Vector2(81.0, 89.0),
			Vector2(73.0, 92.0),
			Vector2(68.0, 88.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 81.0),
			Vector2(75.0, 79.0),
			Vector2(78.0, 81.0),
			Vector2(77.0, 87.0),
			Vector2(73.0, 88.0)
		],
		skin
	)
	canvas.draw_line(_p(box, 71.0, 76.0), _p(box, 78.0, 75.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 70.0, 83.0), _p(box, 78.0, 82.0), silver, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(85.0, 47.0), Vector2(88.0, 41.0), Vector2(90.0, 48.0), Vector2(87.0, 52.0)],
		wash
	)


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
