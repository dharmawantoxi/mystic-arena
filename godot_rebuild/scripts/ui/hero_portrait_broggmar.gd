extends RefCounted
## Native canvas portrait: Broggmar, The Caskbreaker / Cask Brawler.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(40, 28, 24)
	var skin := Color8(202, 147, 108)
	var shade := Color8(153, 95, 66)
	var light := Color8(246, 208, 151)
	var hair := Color8(132, 64, 32)
	var beard := Color8(94, 43, 25)
	var cloth := Color8(82, 60, 48)
	var wood := Color8(151, 99, 48)
	var darkwood := Color8(99, 61, 33)
	var iron := Color8(115, 126, 125)
	var steel := Color8(189, 195, 177)
	var ale := Color8(222, 166, 64)
	_backdrop(canvas, box, Color8(98, 70, 42), Color8(35, 29, 26))

	# Broken staves, flying splinters and a cask rim signal the caskbreaker.
	canvas.draw_arc(
		_p(box, 47.0, 46.0),
		36.0 * unit,
		PI * -0.94,
		PI * -0.1,
		40,
		darkwood,
		maxf(5.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 47.0, 46.0),
		38.0 * unit,
		PI * -0.9,
		PI * -0.15,
		40,
		iron,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 12.0, 27.0), _p(box, 17.0, 33.0), wood, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 20.0), _p(box, 82.0, 15.0), wood, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 85.0, 41.0), _p(box, 89.0, 37.0), wood, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(6.0, 96.0),
			Vector2(11.0, 70.0),
			Vector2(27.0, 55.0),
			Vector2(65.0, 55.0),
			Vector2(85.0, 71.0),
			Vector2(92.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 94.0),
			Vector2(17.0, 72.0),
			Vector2(30.0, 60.0),
			Vector2(63.0, 60.0),
			Vector2(79.0, 73.0),
			Vector2(86.0, 94.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(54.0, 61.0),
			Vector2(65.0, 64.0),
			Vector2(79.0, 76.0),
			Vector2(84.0, 94.0),
			Vector2(55.0, 94.0)
		],
		shade
	)

	# Bare rounded shoulders, a stitched vest and a broad leather barrel harness.
	_fill(
		canvas,
		box,
		[
			Vector2(20.0, 69.0),
			Vector2(29.0, 60.0),
			Vector2(34.0, 65.0),
			Vector2(30.0, 81.0),
			Vector2(34.0, 94.0),
			Vector2(17.0, 94.0)
		],
		cloth
	)
	_fill(
		canvas,
		box,
		[
			Vector2(60.0, 62.0),
			Vector2(67.0, 63.0),
			Vector2(76.0, 72.0),
			Vector2(79.0, 94.0),
			Vector2(61.0, 94.0),
			Vector2(63.0, 81.0)
		],
		cloth
	)
	canvas.draw_line(_p(box, 26.0, 70.0), _p(box, 24.0, 76.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 25.0, 79.0), _p(box, 25.0, 85.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 67.0, 71.0), _p(box, 69.0, 75.0), iron, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 70.0, 79.0), _p(box, 71.0, 85.0), iron, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 31.0, 65.0), _p(box, 63.0, 94.0), ink, maxf(8.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 31.0, 65.0), _p(box, 63.0, 94.0), darkwood, maxf(4.0 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[Vector2(43.0, 76.0), Vector2(48.0, 72.0), Vector2(56.0, 80.0), Vector2(51.0, 85.0)],
		iron
	)
	_fill(
		canvas,
		box,
		[Vector2(46.0, 77.0), Vector2(48.0, 76.0), Vector2(52.0, 80.0), Vector2(50.0, 82.0)],
		darkwood
	)

	# A lopsided cap, broad nose, bushy moustache and split red beard.
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 30.0),
			Vector2(33.0, 20.0),
			Vector2(56.0, 20.0),
			Vector2(67.0, 31.0),
			Vector2(65.0, 46.0),
			Vector2(57.0, 60.0),
			Vector2(39.0, 62.0),
			Vector2(28.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 31.0),
			Vector2(37.0, 25.0),
			Vector2(55.0, 25.0),
			Vector2(61.0, 32.0),
			Vector2(60.0, 45.0),
			Vector2(54.0, 55.0),
			Vector2(41.0, 56.0),
			Vector2(34.0, 46.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 27.0),
			Vector2(57.0, 28.0),
			Vector2(61.0, 33.0),
			Vector2(59.0, 46.0),
			Vector2(53.0, 53.0),
			Vector2(48.0, 49.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 29.0),
			Vector2(24.0, 20.0),
			Vector2(35.0, 12.0),
			Vector2(53.0, 13.0),
			Vector2(65.0, 22.0),
			Vector2(67.0, 32.0),
			Vector2(56.0, 28.0),
			Vector2(37.0, 30.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 25.0),
			Vector2(28.0, 21.0),
			Vector2(37.0, 16.0),
			Vector2(52.0, 17.0),
			Vector2(60.0, 22.0),
			Vector2(62.0, 27.0),
			Vector2(54.0, 24.0),
			Vector2(37.0, 26.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 26.0),
			Vector2(38.0, 23.0),
			Vector2(54.0, 23.0),
			Vector2(65.0, 28.0),
			Vector2(65.0, 31.0),
			Vector2(53.0, 27.0),
			Vector2(38.0, 27.0),
			Vector2(28.0, 30.0)
		],
		iron
	)
	canvas.draw_circle(_p(box, 45.0, 25.0), 2.0 * unit, steel)
	canvas.draw_line(_p(box, 35.0, 35.0), _p(box, 42.0, 35.0), beard, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 35.0), _p(box, 58.0, 34.0), beard, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 38.0), _p(box, 41.0, 38.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 38.0), _p(box, 57.0, 37.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 47.0, 42.0), 5.0 * unit, shade)
	canvas.draw_circle(_p(box, 46.0, 40.0), 4.0 * unit, skin)
	_fill(
		canvas,
		box,
		[
			Vector2(45.0, 45.0),
			Vector2(42.0, 42.0),
			Vector2(36.0, 44.0),
			Vector2(32.0, 50.0),
			Vector2(41.0, 49.0),
			Vector2(47.0, 47.0),
			Vector2(53.0, 50.0),
			Vector2(62.0, 48.0),
			Vector2(57.0, 43.0),
			Vector2(51.0, 43.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 49.0),
			Vector2(40.0, 52.0),
			Vector2(47.0, 50.0),
			Vector2(55.0, 52.0),
			Vector2(62.0, 48.0),
			Vector2(59.0, 61.0),
			Vector2(52.0, 70.0),
			Vector2(47.0, 66.0),
			Vector2(42.0, 71.0),
			Vector2(35.0, 62.0)
		],
		beard
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 52.0),
			Vector2(42.0, 55.0),
			Vector2(47.0, 53.0),
			Vector2(53.0, 55.0),
			Vector2(57.0, 52.0),
			Vector2(55.0, 61.0),
			Vector2(51.0, 65.0),
			Vector2(47.0, 61.0),
			Vector2(43.0, 66.0),
			Vector2(39.0, 61.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 42.0, 51.0), _p(box, 51.0, 51.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 40.0, 58.0), _p(box, 43.0, 62.0), wood, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 57.0), _p(box, 51.0, 61.0), wood, maxf(1.5 * unit, 1.0), true)

	# A barrel-bound fist on one side and a foaming iron-rimmed tankard on the other.
	_fill(
		canvas,
		box,
		[
			Vector2(5.0, 78.0),
			Vector2(12.0, 69.0),
			Vector2(24.0, 70.0),
			Vector2(32.0, 81.0),
			Vector2(30.0, 94.0),
			Vector2(8.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 79.0),
			Vector2(15.0, 74.0),
			Vector2(23.0, 75.0),
			Vector2(27.0, 83.0),
			Vector2(25.0, 92.0),
			Vector2(12.0, 92.0)
		],
		wood
	)
	canvas.draw_line(
		_p(box, 16.0, 78.0), _p(box, 17.0, 91.0), darkwood, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 22.0, 78.0), _p(box, 23.0, 90.0), darkwood, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 11.0, 80.0), _p(box, 25.0, 80.0), iron, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 12.0, 88.0), _p(box, 26.0, 88.0), iron, maxf(3.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 15.0, 80.0), 1.0 * unit, steel)
	canvas.draw_circle(_p(box, 23.0, 88.0), 1.0 * unit, steel)
	_fill(
		canvas,
		box,
		[
			Vector2(64.0, 66.0),
			Vector2(82.0, 64.0),
			Vector2(89.0, 71.0),
			Vector2(89.0, 87.0),
			Vector2(82.0, 94.0),
			Vector2(67.0, 90.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 68.0),
			Vector2(81.0, 67.0),
			Vector2(85.0, 73.0),
			Vector2(85.0, 85.0),
			Vector2(80.0, 90.0),
			Vector2(70.0, 87.0)
		],
		iron
	)
	_fill(
		canvas,
		box,
		[
			Vector2(69.0, 72.0),
			Vector2(80.0, 71.0),
			Vector2(82.0, 75.0),
			Vector2(81.0, 85.0),
			Vector2(72.0, 83.0)
		],
		wood
	)
	canvas.draw_line(
		_p(box, 75.0, 73.0), _p(box, 76.0, 83.0), darkwood, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 86.0, 78.0), 6.0 * unit, PI * -0.5, PI * 0.5, 40, ink, maxf(4.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 86.0, 78.0), 5.0 * unit, PI * -0.5, PI * 0.5, 40, steel, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 68.0, 69.0), _p(box, 81.0, 68.0), steel, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 71.0, 86.0), _p(box, 80.0, 88.0), steel, maxf(3.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 73.0, 68.0), 4.0 * unit, ale)
	canvas.draw_circle(_p(box, 72.0, 65.0), 3.0 * unit, light)
	canvas.draw_circle(_p(box, 78.0, 65.0), 3.5 * unit, light)
	canvas.draw_circle(_p(box, 82.0, 67.0), 2.5 * unit, light)
	canvas.draw_line(_p(box, 80.0, 69.0), _p(box, 81.0, 75.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 65.0, 82.0), 4.0 * unit, skin)
	canvas.draw_line(_p(box, 64.0, 84.0), _p(box, 68.0, 84.0), shade, maxf(1.5 * unit, 1.0), true)


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
