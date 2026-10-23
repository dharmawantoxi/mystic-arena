extends RefCounted
## Native canvas portrait: Aeralith, The West Gale / Wind Ranger.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(13, 32, 34)
	var cloak := Color8(33, 91, 78)
	var leaf := Color8(79, 143, 102)
	var mint := Color8(164, 232, 191)
	var sky := Color8(211, 245, 231)
	var skin := Color8(209, 171, 128)
	var hair := Color8(74, 56, 38)
	var leather := Color8(119, 79, 45)
	var gold := Color8(201, 174, 96)
	_backdrop(canvas, box, Color8(42, 107, 110), Color8(12, 32, 43))

	# Sweeping gusts and a long bow frame a wind-swept ranger hood.
	canvas.draw_arc(
		_p(box, 45.0, 44.0),
		36.0 * unit,
		PI * -0.95,
		PI * -0.16,
		32,
		mint,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 44.0, 49.0),
		41.0 * unit,
		PI * 0.15,
		PI * 0.88,
		32,
		leaf,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 8.0, 39.0), _p(box, 22.0, 35.0), sky, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 8.0, 44.0), _p(box, 17.0, 42.0), mint, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 68.0, 14.0), _p(box, 84.0, 11.0), sky, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 19.0, 76.0), _p(box, 27.0, 17.0), ink, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 19.0, 76.0), _p(box, 27.0, 17.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(canvas, box, [Vector2(27.0, 13.0), Vector2(23.0, 22.0), Vector2(29.0, 20.0)], sky)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 96.0),
			Vector2(19.0, 69.0),
			Vector2(31.0, 58.0),
			Vector2(63.0, 55.0),
			Vector2(78.0, 68.0),
			Vector2(86.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 94.0),
			Vector2(23.0, 70.0),
			Vector2(33.0, 62.0),
			Vector2(61.0, 59.0),
			Vector2(74.0, 70.0),
			Vector2(81.0, 94.0)
		],
		cloak
	)
	_fill(
		canvas,
		box,
		[
			Vector2(22.0, 72.0),
			Vector2(35.0, 63.0),
			Vector2(48.0, 68.0),
			Vector2(35.0, 83.0),
			Vector2(18.0, 89.0)
		],
		leaf
	)
	_fill(
		canvas,
		box,
		[Vector2(38.0, 65.0), Vector2(58.0, 63.0), Vector2(67.0, 94.0), Vector2(32.0, 94.0)],
		leather
	)
	canvas.draw_line(_p(box, 42.0, 71.0), _p(box, 57.0, 87.0), gold, maxf(2.0 * unit, 1.0), true)

	# Pointed hood and off-centre hair distinguish the face from generic busts.
	_fill(
		canvas,
		box,
		[
			Vector2(23.0, 49.0),
			Vector2(26.0, 29.0),
			Vector2(43.0, 14.0),
			Vector2(59.0, 18.0),
			Vector2(70.0, 32.0),
			Vector2(71.0, 55.0),
			Vector2(59.0, 64.0),
			Vector2(33.0, 60.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 48.0),
			Vector2(30.0, 31.0),
			Vector2(44.0, 18.0),
			Vector2(57.0, 22.0),
			Vector2(66.0, 34.0),
			Vector2(67.0, 53.0),
			Vector2(57.0, 59.0),
			Vector2(34.0, 56.0)
		],
		cloak
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 32.0),
			Vector2(44.0, 20.0),
			Vector2(55.0, 23.0),
			Vector2(49.0, 28.0),
			Vector2(37.0, 36.0),
			Vector2(30.0, 47.0)
		],
		leaf
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 33.0),
			Vector2(45.0, 27.0),
			Vector2(57.0, 30.0),
			Vector2(62.0, 39.0),
			Vector2(59.0, 50.0),
			Vector2(48.0, 57.0),
			Vector2(37.0, 49.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(38.0, 34.0),
			Vector2(46.0, 30.0),
			Vector2(55.0, 33.0),
			Vector2(59.0, 39.0),
			Vector2(56.0, 48.0),
			Vector2(48.0, 53.0),
			Vector2(40.0, 47.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 33.0),
			Vector2(44.0, 26.0),
			Vector2(56.0, 29.0),
			Vector2(60.0, 36.0),
			Vector2(50.0, 33.0),
			Vector2(43.0, 40.0),
			Vector2(43.0, 34.0),
			Vector2(36.0, 42.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 40.0, 41.0), _p(box, 46.0, 40.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 40.0), _p(box, 57.0, 41.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 41.0, 41.0), _p(box, 45.0, 41.0), mint, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 41.0), _p(box, 56.0, 41.0), mint, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 42.0), _p(box, 47.0, 46.0), leather, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 45.0, 49.0), _p(box, 52.0, 49.0), leather, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 51.0),
			Vector2(45.0, 58.0),
			Vector2(63.0, 52.0),
			Vector2(60.0, 65.0),
			Vector2(45.0, 69.0),
			Vector2(31.0, 62.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 55.0),
			Vector2(45.0, 61.0),
			Vector2(61.0, 56.0),
			Vector2(58.0, 62.0),
			Vector2(45.0, 65.0),
			Vector2(33.0, 60.0)
		],
		mint
	)

	# A trailing scarf and feather fletching show the westward gale.
	_fill(
		canvas,
		box,
		[
			Vector2(61.0, 57.0),
			Vector2(74.0, 52.0),
			Vector2(88.0, 54.0),
			Vector2(79.0, 60.0),
			Vector2(90.0, 64.0),
			Vector2(72.0, 65.0),
			Vector2(59.0, 63.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(64.0, 58.0),
			Vector2(75.0, 55.0),
			Vector2(83.0, 55.0),
			Vector2(76.0, 60.0),
			Vector2(84.0, 62.0),
			Vector2(72.0, 62.0),
			Vector2(63.0, 61.0)
		],
		leaf
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 29.0),
			Vector2(17.0, 20.0),
			Vector2(16.0, 8.0),
			Vector2(24.0, 16.0),
			Vector2(29.0, 25.0)
		],
		mint
	)
	canvas.draw_line(_p(box, 19.0, 13.0), _p(box, 29.0, 32.0), gold, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 24.0),
			Vector2(24.0, 12.0),
			Vector2(30.0, 7.0),
			Vector2(32.0, 17.0),
			Vector2(30.0, 26.0)
		],
		sky
	)
	canvas.draw_line(_p(box, 29.0, 11.0), _p(box, 29.0, 30.0), gold, maxf(1.5 * unit, 1.0), true)

	# Recurve bow, taut string, and a diagonal quiver strap.
	canvas.draw_arc(
		_p(box, 57.0, 53.0),
		29.0 * unit,
		PI * -0.42,
		PI * 0.42,
		32,
		ink,
		maxf(5.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 57.0, 53.0),
		29.0 * unit,
		PI * -0.42,
		PI * 0.42,
		32,
		gold,
		maxf(2.5 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 64.0, 25.0), _p(box, 64.0, 81.0), sky, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 30.0, 66.0), _p(box, 65.0, 94.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 30.0, 66.0), _p(box, 65.0, 94.0), leather, maxf(3.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 47.0, 79.0), 4.0 * unit, gold)
	canvas.draw_circle(_p(box, 47.0, 79.0), 2.0 * unit, ink)
	_fill(
		canvas,
		box,
		[
			Vector2(60.0, 76.0),
			Vector2(66.0, 73.0),
			Vector2(70.0, 78.0),
			Vector2(69.0, 86.0),
			Vector2(62.0, 86.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 78.0),
			Vector2(66.0, 76.0),
			Vector2(68.0, 79.0),
			Vector2(67.0, 83.0),
			Vector2(63.0, 83.0)
		],
		skin
	)
	canvas.draw_line(_p(box, 24.0, 84.0), _p(box, 31.0, 79.0), mint, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 22.0, 90.0), _p(box, 29.0, 85.0), mint, maxf(2.0 * unit, 1.0), true)


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
