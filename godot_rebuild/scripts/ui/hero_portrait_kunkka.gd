extends RefCounted
## Native canvas painter for Kunkka, the True Boss/Naval Admiral.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(9, 15, 27)
	var coat := Color8(25, 48, 79)
	var coat_light := Color8(43, 82, 119)
	var sea := Color8(40, 126, 159)
	var foam := Color8(135, 222, 220)
	var gold := Color8(218, 170, 79)
	var gold_light := Color8(251, 222, 145)
	var skin := Color8(211, 157, 118)
	var skin_light := Color8(239, 194, 150)
	var beard := Color8(62, 39, 34)
	var beard_light := Color8(103, 59, 43)
	var ivory := Color8(235, 228, 205)
	var steel := Color8(176, 199, 207)
	var red := Color8(157, 48, 51)

	_backdrop(canvas, box, Color8(48, 119, 151), Color8(9, 20, 38))
	canvas.draw_arc(
		_p(box, 48.0, 46.0),
		38.0 * unit,
		-PI * 0.88,
		-PI * 0.12,
		32,
		Color(sea.r, sea.g, sea.b, 0.34),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 47.0),
		31.0 * unit,
		PI * 0.14,
		PI * 0.86,
		28,
		Color(foam.r, foam.g, foam.b, 0.18),
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 14.0, 37.0), 2.0 * unit, foam)
	canvas.draw_circle(_p(box, 80.0, 35.0), 2.2 * unit, gold_light)
	canvas.draw_circle(_p(box, 18.0, 56.0), 1.5 * unit, sea)
	canvas.draw_circle(_p(box, 78.0, 63.0), 1.8 * unit, foam)

	# A curved naval cutlass rises behind the admiral's right shoulder.
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 59.0),
			Vector2(78.0, 42.0),
			Vector2(86.0, 26.0),
			Vector2(91.0, 19.0),
			Vector2(90.0, 32.0),
			Vector2(86.0, 49.0),
			Vector2(79.0, 64.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 55.0),
			Vector2(81.0, 42.0),
			Vector2(87.0, 29.0),
			Vector2(88.0, 26.0),
			Vector2(87.0, 38.0),
			Vector2(83.0, 50.0),
			Vector2(79.0, 58.0),
		],
		steel
	)
	canvas.draw_line(_p(box, 79.0, 57.0), _p(box, 85.0, 60.0), outline, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 79.0, 57.0), _p(box, 84.0, 59.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 80.0, 59.0), _p(box, 69.0, 78.0), outline, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 80.0, 59.0), _p(box, 70.0, 76.0), gold_light, maxf(1.7 * unit, 1.0), true
	)

	# Broad blue coat, raised shoulders, and gold naval epaulettes.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 96.0),
			Vector2(12.0, 77.0),
			Vector2(21.0, 66.0),
			Vector2(34.0, 59.0),
			Vector2(61.0, 59.0),
			Vector2(75.0, 65.0),
			Vector2(85.0, 77.0),
			Vector2(89.0, 96.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 94.0),
			Vector2(19.0, 78.0),
			Vector2(28.0, 69.0),
			Vector2(39.0, 64.0),
			Vector2(57.0, 64.0),
			Vector2(69.0, 70.0),
			Vector2(78.0, 80.0),
			Vector2(81.0, 94.0),
		],
		coat
	)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 71.0),
			Vector2(15.0, 62.0),
			Vector2(27.0, 59.0),
			Vector2(38.0, 65.0),
			Vector2(35.0, 76.0),
			Vector2(23.0, 82.0),
			Vector2(14.0, 78.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 70.0),
			Vector2(18.0, 65.0),
			Vector2(27.0, 63.0),
			Vector2(34.0, 67.0),
			Vector2(32.0, 74.0),
			Vector2(23.0, 78.0),
			Vector2(17.0, 76.0),
		],
		coat_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 65.0),
			Vector2(69.0, 59.0),
			Vector2(82.0, 63.0),
			Vector2(86.0, 72.0),
			Vector2(82.0, 80.0),
			Vector2(70.0, 82.0),
			Vector2(60.0, 76.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(63.0, 67.0),
			Vector2(70.0, 63.0),
			Vector2(79.0, 66.0),
			Vector2(82.0, 72.0),
			Vector2(79.0, 76.0),
			Vector2(71.0, 78.0),
			Vector2(64.0, 74.0),
		],
		coat_light
	)
	canvas.draw_line(_p(box, 18.0, 68.0), _p(box, 31.0, 67.0), gold, maxf(2.4 * unit, 1.0), true)
	canvas.draw_line(_p(box, 65.0, 68.0), _p(box, 79.0, 68.0), gold, maxf(2.4 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 25.0, 72.0), 2.0 * unit, gold_light)
	canvas.draw_circle(_p(box, 73.0, 72.0), 2.0 * unit, gold_light)

	# The red sash and pale collar break up the dark uniform.
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 58.0),
			Vector2(36.0, 59.0),
			Vector2(70.0, 91.0),
			Vector2(66.0, 96.0),
			Vector2(58.0, 96.0),
			Vector2(26.0, 67.0),
		],
		red
	)
	canvas.draw_line(
		_p(box, 31.0, 60.0), _p(box, 67.0, 93.0), gold_light, maxf(1.3 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[Vector2(38.0, 49.0), Vector2(48.0, 59.0), Vector2(42.0, 68.0), Vector2(34.0, 56.0)],
		outline
	)
	_fill(
		canvas,
		box,
		[Vector2(58.0, 49.0), Vector2(49.0, 59.0), Vector2(55.0, 68.0), Vector2(63.0, 56.0)],
		outline
	)
	_fill(
		canvas,
		box,
		[Vector2(39.0, 51.0), Vector2(47.0, 59.0), Vector2(42.0, 64.0), Vector2(37.0, 56.0)],
		ivory
	)
	_fill(
		canvas,
		box,
		[Vector2(57.0, 51.0), Vector2(50.0, 59.0), Vector2(54.0, 64.0), Vector2(60.0, 56.0)],
		ivory
	)
	canvas.draw_line(_p(box, 48.0, 65.0), _p(box, 48.0, 88.0), gold, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 43.0, 73.0), _p(box, 53.0, 73.0), gold_light, maxf(1.6 * unit, 1.0), true
	)
	canvas.draw_arc(_p(box, 48.0, 79.0), 5.0 * unit, 0.0, PI, 14, gold, maxf(1.6 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 67.0), 2.1 * unit, gold_light)
	canvas.draw_circle(_p(box, 58.0, 78.0), 1.5 * unit, gold_light)
	canvas.draw_circle(_p(box, 58.0, 86.0), 1.5 * unit, gold_light)

	# Weathered face, framed by dark sideburns and a captain's beard.
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 30.0),
			Vector2(33.0, 21.0),
			Vector2(41.0, 15.0),
			Vector2(53.0, 15.0),
			Vector2(62.0, 22.0),
			Vector2(66.0, 32.0),
			Vector2(63.0, 43.0),
			Vector2(58.0, 52.0),
			Vector2(49.0, 58.0),
			Vector2(40.0, 55.0),
			Vector2(34.0, 48.0),
			Vector2(30.0, 39.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 30.0),
			Vector2(37.0, 23.0),
			Vector2(43.0, 19.0),
			Vector2(52.0, 19.0),
			Vector2(59.0, 25.0),
			Vector2(62.0, 33.0),
			Vector2(59.0, 41.0),
			Vector2(55.0, 47.0),
			Vector2(48.0, 51.0),
			Vector2(41.0, 48.0),
			Vector2(36.0, 42.0),
			Vector2(34.0, 35.0),
		],
		skin
	)
	canvas.draw_circle(_p(box, 30.0, 36.0), 4.0 * unit, outline)
	canvas.draw_circle(_p(box, 30.0, 36.0), 2.1 * unit, skin)
	canvas.draw_circle(_p(box, 65.0, 36.0), 4.0 * unit, outline)
	canvas.draw_circle(_p(box, 65.0, 36.0), 2.1 * unit, skin)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 40.0),
			Vector2(39.0, 45.0),
			Vector2(47.0, 48.0),
			Vector2(56.0, 44.0),
			Vector2(62.0, 39.0),
			Vector2(60.0, 49.0),
			Vector2(55.0, 56.0),
			Vector2(48.0, 60.0),
			Vector2(41.0, 56.0),
			Vector2(36.0, 50.0),
		],
		beard
	)
	_fill(
		canvas,
		box,
		[
			Vector2(38.0, 46.0),
			Vector2(44.0, 49.0),
			Vector2(50.0, 49.0),
			Vector2(58.0, 45.0),
			Vector2(55.0, 52.0),
			Vector2(48.0, 56.0),
			Vector2(42.0, 53.0),
		],
		beard_light
	)
	canvas.draw_line(_p(box, 38.0, 33.0), _p(box, 45.0, 34.0), outline, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 34.0), _p(box, 59.0, 33.0), outline, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 36.0), _p(box, 44.0, 36.0), ivory, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 36.0), _p(box, 58.0, 36.0), ivory, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 48.0, 35.0), _p(box, 47.0, 41.0), beard_light, maxf(1.6 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[Vector2(40.0, 40.0), Vector2(46.0, 42.0), Vector2(48.0, 45.0), Vector2(43.0, 45.0)],
		beard
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 42.0), Vector2(54.0, 40.0), Vector2(57.0, 43.0), Vector2(51.0, 46.0)],
		beard
	)
	canvas.draw_line(
		_p(box, 43.0, 44.0), _p(box, 48.0, 45.0), skin_light, maxf(1.0 * unit, 1.0), true
	)

	# Three-point admiral's hat, fine gold trim, and a pale sea-feather.
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 27.0),
			Vector2(19.0, 21.0),
			Vector2(29.0, 18.0),
			Vector2(35.0, 13.0),
			Vector2(42.0, 16.0),
			Vector2(48.0, 7.0),
			Vector2(54.0, 16.0),
			Vector2(61.0, 13.0),
			Vector2(67.0, 18.0),
			Vector2(77.0, 20.0),
			Vector2(82.0, 26.0),
			Vector2(75.0, 29.0),
			Vector2(64.0, 27.0),
			Vector2(55.0, 29.0),
			Vector2(47.0, 27.0),
			Vector2(38.0, 29.0),
			Vector2(28.0, 27.0),
			Vector2(21.0, 29.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(21.0, 24.0),
			Vector2(26.0, 21.0),
			Vector2(34.0, 20.0),
			Vector2(38.0, 16.0),
			Vector2(43.0, 19.0),
			Vector2(48.0, 12.0),
			Vector2(53.0, 19.0),
			Vector2(61.0, 16.0),
			Vector2(66.0, 21.0),
			Vector2(76.0, 23.0),
			Vector2(78.0, 25.0),
			Vector2(66.0, 24.0),
			Vector2(56.0, 26.0),
			Vector2(48.0, 24.0),
			Vector2(39.0, 26.0),
			Vector2(29.0, 24.0),
		],
		coat_light
	)
	canvas.draw_line(_p(box, 20.0, 24.0), _p(box, 77.0, 25.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 49.0, 19.0), 3.0 * unit, gold_light)
	canvas.draw_circle(_p(box, 49.0, 19.0), 1.2 * unit, coat)
	_fill(
		canvas,
		box,
		[
			Vector2(64.0, 17.0),
			Vector2(69.0, 7.0),
			Vector2(79.0, 5.0),
			Vector2(75.0, 11.0),
			Vector2(82.0, 12.0),
			Vector2(73.0, 16.0),
			Vector2(69.0, 21.0),
		],
		ivory
	)
	canvas.draw_line(_p(box, 70.0, 10.0), _p(box, 75.0, 8.0), foam, maxf(1.4 * unit, 1.0), true)


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
