extends RefCounted
## Native canvas portrait: Garumenshi, The Sage Toad Hermit / Summoner.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(30, 37, 30)
	var robe := Color8(103, 53, 45)
	var red := Color8(159, 75, 54)
	var green := Color8(93, 116, 63)
	var light := Color8(222, 218, 174)
	var skin := Color8(194, 161, 120)
	var shade := Color8(138, 110, 82)
	var hair := Color8(217, 219, 193)
	var iron := Color8(125, 143, 130)
	var paper := Color8(199, 182, 128)
	var wood := Color8(104, 77, 49)
	var toad := Color8(139, 162, 79)
	var eye := Color8(237, 201, 88)
	_backdrop(canvas, box, Color8(63, 89, 62), Color8(25, 33, 29))

	# A broad travel scroll and reed strokes frame the sage rather than a warrior.
	canvas.draw_line(_p(box, 10.0, 62.0), _p(box, 10.0, 27.0), wood, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 85.0, 62.0), _p(box, 85.0, 25.0), wood, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 31.0),
			Vector2(17.0, 24.0),
			Vector2(76.0, 24.0),
			Vector2(86.0, 31.0),
			Vector2(84.0, 44.0),
			Vector2(74.0, 48.0),
			Vector2(18.0, 47.0),
			Vector2(8.0, 40.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 32.0),
			Vector2(20.0, 29.0),
			Vector2(74.0, 29.0),
			Vector2(80.0, 33.0),
			Vector2(79.0, 39.0),
			Vector2(73.0, 43.0),
			Vector2(20.0, 42.0),
			Vector2(13.0, 38.0)
		],
		paper
	)
	canvas.draw_circle(_p(box, 13.0, 35.0), 6.0 * unit, wood)
	canvas.draw_circle(_p(box, 13.0, 35.0), 3.0 * unit, paper)
	canvas.draw_circle(_p(box, 81.0, 35.0), 6.0 * unit, wood)
	canvas.draw_circle(_p(box, 81.0, 35.0), 3.0 * unit, paper)
	canvas.draw_line(_p(box, 8.0, 58.0), _p(box, 14.0, 45.0), green, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 86.0, 58.0), _p(box, 80.0, 45.0), green, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 96.0),
			Vector2(16.0, 69.0),
			Vector2(31.0, 58.0),
			Vector2(61.0, 58.0),
			Vector2(80.0, 71.0),
			Vector2(88.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 94.0),
			Vector2(22.0, 72.0),
			Vector2(33.0, 63.0),
			Vector2(58.0, 63.0),
			Vector2(74.0, 74.0),
			Vector2(82.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 67.0),
			Vector2(45.0, 72.0),
			Vector2(58.0, 67.0),
			Vector2(65.0, 94.0),
			Vector2(25.0, 94.0)
		],
		green
	)
	canvas.draw_line(_p(box, 30.0, 74.0), _p(box, 59.0, 94.0), ink, maxf(7.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 30.0, 74.0), _p(box, 59.0, 94.0), wood, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(21.0, 71.0),
			Vector2(31.0, 64.0),
			Vector2(39.0, 72.0),
			Vector2(33.0, 94.0),
			Vector2(17.0, 94.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(53.0, 72.0),
			Vector2(62.0, 64.0),
			Vector2(72.0, 72.0),
			Vector2(79.0, 94.0),
			Vector2(59.0, 94.0)
		],
		red
	)

	# Wild white hair, a metal forehead plate and red tear-shaped sage markings.
	_fill(
		canvas,
		box,
		[
			Vector2(25.0, 41.0),
			Vector2(22.0, 27.0),
			Vector2(29.0, 30.0),
			Vector2(28.0, 18.0),
			Vector2(37.0, 22.0),
			Vector2(41.0, 11.0),
			Vector2(48.0, 19.0),
			Vector2(56.0, 11.0),
			Vector2(60.0, 23.0),
			Vector2(69.0, 19.0),
			Vector2(66.0, 32.0),
			Vector2(72.0, 31.0),
			Vector2(66.0, 49.0),
			Vector2(68.0, 60.0),
			Vector2(57.0, 64.0),
			Vector2(36.0, 63.0),
			Vector2(25.0, 57.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 41.0),
			Vector2(27.0, 33.0),
			Vector2(33.0, 35.0),
			Vector2(33.0, 24.0),
			Vector2(39.0, 28.0),
			Vector2(43.0, 18.0),
			Vector2(48.0, 25.0),
			Vector2(54.0, 19.0),
			Vector2(57.0, 28.0),
			Vector2(63.0, 25.0),
			Vector2(61.0, 36.0),
			Vector2(66.0, 36.0),
			Vector2(61.0, 48.0),
			Vector2(64.0, 56.0),
			Vector2(56.0, 58.0),
			Vector2(37.0, 58.0),
			Vector2(30.0, 54.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 32.0),
			Vector2(38.0, 24.0),
			Vector2(55.0, 24.0),
			Vector2(63.0, 32.0),
			Vector2(61.0, 47.0),
			Vector2(55.0, 58.0),
			Vector2(42.0, 60.0),
			Vector2(33.0, 49.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 33.0),
			Vector2(40.0, 28.0),
			Vector2(54.0, 28.0),
			Vector2(58.0, 34.0),
			Vector2(57.0, 45.0),
			Vector2(52.0, 54.0),
			Vector2(43.0, 55.0),
			Vector2(38.0, 47.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 30.0),
			Vector2(58.0, 34.0),
			Vector2(57.0, 45.0),
			Vector2(52.0, 53.0),
			Vector2(49.0, 49.0),
			Vector2(50.0, 41.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 30.0),
			Vector2(39.0, 26.0),
			Vector2(55.0, 26.0),
			Vector2(61.0, 30.0),
			Vector2(60.0, 35.0),
			Vector2(54.0, 32.0),
			Vector2(40.0, 32.0),
			Vector2(33.0, 35.0)
		],
		iron
	)
	canvas.draw_line(_p(box, 39.0, 29.0), _p(box, 53.0, 29.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 46.0, 27.0), _p(box, 46.0, 31.0), ink, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 43.0, 29.0), _p(box, 49.0, 29.0), ink, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 37.0), _p(box, 44.0, 38.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 38.0), _p(box, 57.0, 36.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 40.0), _p(box, 43.0, 40.0), eye, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 40.0), _p(box, 56.0, 39.0), eye, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(38.0, 42.0), Vector2(41.0, 43.0), Vector2(40.0, 51.0), Vector2(37.0, 47.0)],
		red
	)
	_fill(
		canvas,
		box,
		[Vector2(53.0, 43.0), Vector2(56.0, 42.0), Vector2(57.0, 47.0), Vector2(54.0, 51.0)],
		red
	)
	canvas.draw_line(_p(box, 48.0, 38.0), _p(box, 46.0, 45.0), skin, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 44.0, 50.0), _p(box, 51.0, 49.0), ink, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(40.0, 54.0),
			Vector2(45.0, 56.0),
			Vector2(51.0, 54.0),
			Vector2(54.0, 58.0),
			Vector2(48.0, 66.0),
			Vector2(42.0, 62.0)
		],
		hair
	)

	# A small summoned toad sits on one shoulder with bulbous gold eyes.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 71.0),
			Vector2(11.0, 60.0),
			Vector2(15.0, 55.0),
			Vector2(22.0, 56.0),
			Vector2(28.0, 63.0),
			Vector2(30.0, 73.0),
			Vector2(23.0, 78.0),
			Vector2(13.0, 77.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 70.0),
			Vector2(14.0, 61.0),
			Vector2(19.0, 59.0),
			Vector2(24.0, 63.0),
			Vector2(26.0, 72.0),
			Vector2(22.0, 74.0),
			Vector2(15.0, 74.0)
		],
		toad
	)
	canvas.draw_circle(_p(box, 14.0, 60.0), 4.0 * unit, ink)
	canvas.draw_circle(_p(box, 14.0, 60.0), 2.7 * unit, eye)
	canvas.draw_circle(_p(box, 14.0, 60.0), 1.0 * unit, ink)
	canvas.draw_circle(_p(box, 24.0, 61.0), 4.0 * unit, ink)
	canvas.draw_circle(_p(box, 24.0, 61.0), 2.7 * unit, eye)
	canvas.draw_circle(_p(box, 24.0, 61.0), 1.0 * unit, ink)
	canvas.draw_line(_p(box, 14.0, 68.0), _p(box, 24.0, 68.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 17.0, 72.0), 1.0 * unit, green)
	canvas.draw_circle(_p(box, 23.0, 70.0), 1.0 * unit, green)
	canvas.draw_line(_p(box, 10.0, 75.0), _p(box, 15.0, 74.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 24.0, 75.0), _p(box, 29.0, 76.0), light, maxf(2.0 * unit, 1.0), true)

	# Two hands form a compact summoning seal over a tied front pouch.
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 83.0),
			Vector2(37.0, 77.0),
			Vector2(42.0, 78.0),
			Vector2(43.0, 69.0),
			Vector2(47.0, 67.0),
			Vector2(50.0, 76.0),
			Vector2(53.0, 70.0),
			Vector2(57.0, 71.0),
			Vector2(57.0, 81.0),
			Vector2(64.0, 85.0),
			Vector2(58.0, 92.0),
			Vector2(49.0, 90.0),
			Vector2(41.0, 94.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 84.0),
			Vector2(39.0, 81.0),
			Vector2(45.0, 82.0),
			Vector2(46.0, 72.0),
			Vector2(47.0, 72.0),
			Vector2(48.0, 82.0),
			Vector2(52.0, 83.0),
			Vector2(55.0, 75.0),
			Vector2(55.0, 83.0),
			Vector2(60.0, 86.0),
			Vector2(56.0, 88.0),
			Vector2(49.0, 87.0),
			Vector2(41.0, 90.0)
		],
		skin
	)
	canvas.draw_line(_p(box, 42.0, 85.0), _p(box, 50.0, 85.0), shade, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 46.0, 80.0), _p(box, 49.0, 80.0), light, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(65.0, 81.0),
			Vector2(74.0, 79.0),
			Vector2(79.0, 85.0),
			Vector2(77.0, 95.0),
			Vector2(65.0, 94.0)
		],
		wood
	)
	canvas.draw_line(_p(box, 67.0, 83.0), _p(box, 75.0, 83.0), paper, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 71.0, 88.0), 2.0 * unit, iron)


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
