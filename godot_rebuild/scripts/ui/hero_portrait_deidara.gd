extends RefCounted
## Native canvas portrait: Deidara, The Explosive Artist.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(30, 28, 32)
	var cloak := Color8(44, 44, 53)
	var red := Color8(161, 52, 51)
	var gold := Color8(222, 181, 70)
	var light := Color8(255, 226, 135)
	var skin := Color8(217, 175, 139)
	var shade := Color8(164, 121, 101)
	var steel := Color8(144, 159, 169)
	var clay := Color8(226, 222, 201)
	var clay_shade := Color8(163, 171, 162)
	var spark := Color8(248, 154, 69)
	_backdrop(canvas, box, Color8(100, 75, 48), Color8(27, 28, 36))

	# Explosive sparks and sculpted clay birds establish the ranged artist role.
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 35.0),
			Vector2(19.0, 28.0),
			Vector2(15.0, 18.0),
			Vector2(25.0, 22.0),
			Vector2(30.0, 13.0),
			Vector2(32.0, 26.0),
			Vector2(43.0, 25.0),
			Vector2(36.0, 34.0),
			Vector2(40.0, 43.0),
			Vector2(28.0, 39.0),
			Vector2(23.0, 48.0),
			Vector2(21.0, 37.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 32.0),
			Vector2(24.0, 28.0),
			Vector2(24.0, 23.0),
			Vector2(29.0, 30.0),
			Vector2(35.0, 29.0),
			Vector2(30.0, 34.0),
			Vector2(32.0, 39.0),
			Vector2(26.0, 36.0),
			Vector2(23.0, 41.0),
			Vector2(23.0, 34.0)
		],
		spark
	)
	canvas.draw_line(_p(box, 10.0, 14.0), _p(box, 14.0, 19.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 7.0, 45.0), _p(box, 12.0, 42.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 40.0, 12.0), _p(box, 37.0, 18.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 83.0, 38.0), _p(box, 88.0, 35.0), light, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(59.0, 26.0),
			Vector2(65.0, 11.0),
			Vector2(75.0, 10.0),
			Vector2(81.0, 20.0),
			Vector2(77.0, 35.0),
			Vector2(82.0, 44.0),
			Vector2(69.0, 41.0),
			Vector2(67.0, 28.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(63.0, 25.0),
			Vector2(68.0, 15.0),
			Vector2(73.0, 14.0),
			Vector2(77.0, 21.0),
			Vector2(73.0, 34.0),
			Vector2(77.0, 39.0),
			Vector2(71.0, 36.0),
			Vector2(71.0, 24.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 96.0),
			Vector2(20.0, 70.0),
			Vector2(33.0, 59.0),
			Vector2(58.0, 57.0),
			Vector2(74.0, 70.0),
			Vector2(84.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 94.0),
			Vector2(25.0, 73.0),
			Vector2(35.0, 63.0),
			Vector2(57.0, 61.0),
			Vector2(69.0, 73.0),
			Vector2(78.0, 94.0)
		],
		cloak
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 61.0),
			Vector2(43.0, 67.0),
			Vector2(47.0, 79.0),
			Vector2(38.0, 74.0),
			Vector2(29.0, 68.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(49.0, 78.0),
			Vector2(55.0, 66.0),
			Vector2(65.0, 61.0),
			Vector2(62.0, 70.0),
			Vector2(55.0, 73.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 31.0),
			Vector2(36.0, 21.0),
			Vector2(54.0, 20.0),
			Vector2(64.0, 30.0),
			Vector2(62.0, 46.0),
			Vector2(55.0, 57.0),
			Vector2(42.0, 59.0),
			Vector2(32.0, 49.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 32.0),
			Vector2(39.0, 25.0),
			Vector2(53.0, 25.0),
			Vector2(59.0, 31.0),
			Vector2(58.0, 44.0),
			Vector2(52.0, 53.0),
			Vector2(43.0, 54.0),
			Vector2(37.0, 47.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 27.0),
			Vector2(58.0, 32.0),
			Vector2(58.0, 43.0),
			Vector2(52.0, 51.0),
			Vector2(48.0, 48.0),
			Vector2(50.0, 41.0)
		],
		shade
	)

	# A swept blond fringe covers one eye beneath an engraved forehead plate.
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 33.0),
			Vector2(28.0, 23.0),
			Vector2(35.0, 24.0),
			Vector2(39.0, 15.0),
			Vector2(46.0, 18.0),
			Vector2(54.0, 16.0),
			Vector2(63.0, 23.0),
			Vector2(65.0, 35.0),
			Vector2(59.0, 31.0),
			Vector2(56.0, 25.0),
			Vector2(48.0, 29.0),
			Vector2(45.0, 39.0),
			Vector2(41.0, 49.0),
			Vector2(40.0, 34.0),
			Vector2(34.0, 39.0),
			Vector2(34.0, 51.0),
			Vector2(29.0, 46.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[Vector2(34.0, 29.0), Vector2(38.0, 23.0), Vector2(42.0, 22.0), Vector2(39.0, 29.0)],
		light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 28.0),
			Vector2(43.0, 24.0),
			Vector2(58.0, 25.0),
			Vector2(61.0, 30.0),
			Vector2(59.0, 34.0),
			Vector2(44.0, 31.0),
			Vector2(35.0, 34.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 29.0),
			Vector2(44.0, 27.0),
			Vector2(56.0, 28.0),
			Vector2(58.0, 30.0),
			Vector2(57.0, 32.0),
			Vector2(44.0, 29.0),
			Vector2(37.0, 31.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 47.0, 28.0), _p(box, 53.0, 30.0), ink, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 49.0, 30.0), _p(box, 52.0, 28.0), ink, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 36.0), _p(box, 57.0, 35.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 39.0), _p(box, 55.0, 38.0), steel, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 38.0), _p(box, 45.0, 44.0), skin, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 44.0, 49.0), _p(box, 52.0, 48.0), ink, maxf(1.0 * unit, 1.0), true)

	# A high dark collar, red cloud motif and open sculpting palm.
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 49.0),
			Vector2(41.0, 59.0),
			Vector2(48.0, 68.0),
			Vector2(59.0, 57.0),
			Vector2(66.0, 49.0),
			Vector2(64.0, 65.0),
			Vector2(49.0, 81.0),
			Vector2(32.0, 66.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 56.0),
			Vector2(42.0, 63.0),
			Vector2(48.0, 74.0),
			Vector2(59.0, 62.0),
			Vector2(61.0, 56.0),
			Vector2(60.0, 65.0),
			Vector2(49.0, 77.0),
			Vector2(36.0, 64.0)
		],
		cloak
	)
	canvas.draw_line(_p(box, 35.0, 60.0), _p(box, 46.0, 73.0), red, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 73.0), _p(box, 60.0, 62.0), red, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 37.0, 86.0), 5.0 * unit, red)
	canvas.draw_circle(_p(box, 43.0, 83.0), 5.0 * unit, red)
	canvas.draw_circle(_p(box, 49.0, 86.0), 4.0 * unit, red)
	canvas.draw_line(_p(box, 33.0, 90.0), _p(box, 50.0, 90.0), clay, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(61.0, 89.0),
			Vector2(62.0, 78.0),
			Vector2(66.0, 74.0),
			Vector2(66.0, 64.0),
			Vector2(70.0, 61.0),
			Vector2(73.0, 72.0),
			Vector2(76.0, 64.0),
			Vector2(80.0, 64.0),
			Vector2(80.0, 77.0),
			Vector2(84.0, 73.0),
			Vector2(87.0, 76.0),
			Vector2(82.0, 85.0),
			Vector2(77.0, 93.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(65.0, 87.0),
			Vector2(66.0, 79.0),
			Vector2(69.0, 77.0),
			Vector2(69.0, 66.0),
			Vector2(70.0, 66.0),
			Vector2(71.0, 78.0),
			Vector2(76.0, 78.0),
			Vector2(78.0, 68.0),
			Vector2(78.0, 79.0),
			Vector2(83.0, 78.0),
			Vector2(79.0, 83.0),
			Vector2(75.0, 89.0)
		],
		skin
	)
	canvas.draw_arc(
		_p(box, 73.0, 81.0), 3.0 * unit, PI * 0.1, PI * 0.9, 40, ink, maxf(1.0 * unit, 1.0), true
	)

	# One clay bird rests on the palm while another flies behind the shoulder.
	_fill(
		canvas,
		box,
		[
			Vector2(55.0, 67.0),
			Vector2(65.0, 68.0),
			Vector2(73.0, 61.0),
			Vector2(77.0, 64.0),
			Vector2(76.0, 68.0),
			Vector2(87.0, 62.0),
			Vector2(83.0, 71.0),
			Vector2(75.0, 74.0),
			Vector2(65.0, 73.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(61.0, 69.0),
			Vector2(67.0, 70.0),
			Vector2(73.0, 64.0),
			Vector2(75.0, 65.0),
			Vector2(74.0, 69.0),
			Vector2(82.0, 66.0),
			Vector2(79.0, 70.0),
			Vector2(74.0, 72.0),
			Vector2(67.0, 72.0)
		],
		clay
	)
	canvas.draw_circle(_p(box, 74.0, 66.0), 0.8 * unit, ink)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 59.0),
			Vector2(17.0, 61.0),
			Vector2(24.0, 54.0),
			Vector2(29.0, 55.0),
			Vector2(28.0, 60.0),
			Vector2(35.0, 57.0),
			Vector2(32.0, 64.0),
			Vector2(26.0, 67.0),
			Vector2(17.0, 65.0)
		],
		clay
	)
	canvas.draw_line(
		_p(box, 18.0, 63.0), _p(box, 26.0, 64.0), clay_shade, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 26.0, 57.0), 0.8 * unit, ink)


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
