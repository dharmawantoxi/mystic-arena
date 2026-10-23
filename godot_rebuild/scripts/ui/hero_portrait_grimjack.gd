extends RefCounted
## Native canvas portrait: Grimjack, The Cackling Fiend / Void Assassin.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(26, 21, 41)
	var cloth := Color8(58, 40, 87)
	var violet := Color8(114, 69, 151)
	var red := Color8(139, 49, 89)
	var mask := Color8(203, 190, 201)
	var shade := Color8(134, 114, 151)
	var light := Color8(247, 227, 203)
	var void_glow := Color8(118, 231, 199)
	var steel := Color8(166, 180, 204)
	var gold := Color8(201, 163, 92)
	_backdrop(canvas, box, Color8(58, 36, 83), Color8(20, 20, 38))

	# Broken void arcs and a crooked three-point cap frame a cackling masked fiend.
	canvas.draw_arc(
		_p(box, 46.0, 40.0),
		34.0 * unit,
		PI * -0.94,
		PI * -0.28,
		40,
		violet,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 46.0, 40.0),
		37.0 * unit,
		PI * 0.08,
		PI * 0.5,
		40,
		void_glow,
		maxf(1.0 * unit, 1.0),
		true
	)
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 32.0),
			Vector2(14.0, 21.0),
			Vector2(18.0, 10.0),
			Vector2(31.0, 16.0),
			Vector2(38.0, 24.0),
			Vector2(42.0, 10.0),
			Vector2(53.0, 7.0),
			Vector2(62.0, 16.0),
			Vector2(60.0, 24.0),
			Vector2(74.0, 18.0),
			Vector2(83.0, 27.0),
			Vector2(78.0, 39.0),
			Vector2(69.0, 34.0),
			Vector2(61.0, 31.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 28.0),
			Vector2(19.0, 20.0),
			Vector2(21.0, 15.0),
			Vector2(29.0, 20.0),
			Vector2(37.0, 29.0),
			Vector2(40.0, 27.0),
			Vector2(46.0, 15.0),
			Vector2(52.0, 12.0),
			Vector2(57.0, 17.0),
			Vector2(55.0, 28.0),
			Vector2(61.0, 28.0),
			Vector2(73.0, 23.0),
			Vector2(78.0, 28.0),
			Vector2(76.0, 33.0),
			Vector2(69.0, 29.0),
			Vector2(60.0, 32.0),
			Vector2(39.0, 33.0),
			Vector2(30.0, 32.0)
		],
		violet
	)
	canvas.draw_circle(_p(box, 18.0, 12.0), 2.0 * unit, gold)
	canvas.draw_circle(_p(box, 53.0, 9.0), 2.0 * unit, gold)
	canvas.draw_circle(_p(box, 80.0, 35.0), 2.0 * unit, gold)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 96.0),
			Vector2(22.0, 70.0),
			Vector2(34.0, 58.0),
			Vector2(57.0, 58.0),
			Vector2(72.0, 70.0),
			Vector2(82.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(20.0, 94.0),
			Vector2(27.0, 73.0),
			Vector2(36.0, 63.0),
			Vector2(55.0, 63.0),
			Vector2(67.0, 73.0),
			Vector2(76.0, 94.0)
		],
		cloth
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 72.0),
			Vector2(37.0, 66.0),
			Vector2(46.0, 76.0),
			Vector2(44.0, 94.0),
			Vector2(22.0, 94.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 76.0),
			Vector2(56.0, 65.0),
			Vector2(65.0, 73.0),
			Vector2(73.0, 94.0),
			Vector2(52.0, 94.0)
		],
		violet
	)

	# A pale asymmetric mask carries narrowed void eyes and a wide broken grin.
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 31.0),
			Vector2(37.0, 23.0),
			Vector2(55.0, 24.0),
			Vector2(65.0, 34.0),
			Vector2(62.0, 48.0),
			Vector2(54.0, 60.0),
			Vector2(42.0, 61.0),
			Vector2(31.0, 49.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 33.0),
			Vector2(40.0, 28.0),
			Vector2(54.0, 29.0),
			Vector2(59.0, 35.0),
			Vector2(57.0, 47.0),
			Vector2(51.0, 55.0),
			Vector2(43.0, 56.0),
			Vector2(36.0, 47.0)
		],
		mask
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 29.0),
			Vector2(58.0, 34.0),
			Vector2(58.0, 45.0),
			Vector2(51.0, 54.0),
			Vector2(47.0, 51.0),
			Vector2(49.0, 42.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[Vector2(34.0, 35.0), Vector2(43.0, 37.0), Vector2(44.0, 43.0), Vector2(35.0, 40.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(50.0, 38.0), Vector2(59.0, 34.0), Vector2(57.0, 41.0), Vector2(50.0, 43.0)],
		ink
	)
	canvas.draw_line(
		_p(box, 36.0, 38.0), _p(box, 41.0, 40.0), void_glow, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 52.0, 40.0), _p(box, 57.0, 37.0), void_glow, maxf(1.5 * unit, 1.0), true
	)
	_fill(canvas, box, [Vector2(36.0, 42.0), Vector2(41.0, 45.0), Vector2(38.0, 49.0)], red)
	_fill(canvas, box, [Vector2(54.0, 44.0), Vector2(58.0, 42.0), Vector2(55.0, 49.0)], violet)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 46.0),
			Vector2(43.0, 49.0),
			Vector2(51.0, 48.0),
			Vector2(59.0, 43.0),
			Vector2(55.0, 52.0),
			Vector2(49.0, 56.0),
			Vector2(41.0, 54.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(39.0, 48.0),
			Vector2(44.0, 51.0),
			Vector2(51.0, 50.0),
			Vector2(56.0, 47.0),
			Vector2(53.0, 52.0),
			Vector2(48.0, 54.0),
			Vector2(42.0, 52.0)
		],
		light
	)
	canvas.draw_line(_p(box, 44.0, 50.0), _p(box, 44.0, 53.0), ink, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 49.0, 50.0), _p(box, 49.0, 53.0), ink, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 49.0), _p(box, 52.0, 52.0), ink, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 46.0, 38.0), _p(box, 44.0, 45.0), light, maxf(1.2 * unit, 1.0), true)

	# A serrated ruff, diamond clasps and twin reverse-grip knives complete the assassin.
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 51.0),
			Vector2(39.0, 60.0),
			Vector2(46.0, 67.0),
			Vector2(59.0, 57.0),
			Vector2(66.0, 49.0),
			Vector2(64.0, 65.0),
			Vector2(58.0, 62.0),
			Vector2(55.0, 72.0),
			Vector2(49.0, 68.0),
			Vector2(45.0, 77.0),
			Vector2(40.0, 68.0),
			Vector2(35.0, 72.0),
			Vector2(33.0, 63.0),
			Vector2(28.0, 65.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 57.0),
			Vector2(39.0, 64.0),
			Vector2(45.0, 70.0),
			Vector2(48.0, 66.0),
			Vector2(56.0, 61.0),
			Vector2(61.0, 56.0),
			Vector2(59.0, 62.0),
			Vector2(55.0, 66.0),
			Vector2(50.0, 70.0),
			Vector2(46.0, 74.0),
			Vector2(40.0, 68.0),
			Vector2(35.0, 65.0)
		],
		violet
	)
	_fill(
		canvas,
		box,
		[Vector2(46.0, 75.0), Vector2(49.0, 78.0), Vector2(46.0, 81.0), Vector2(43.0, 78.0)],
		gold
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 84.0), Vector2(51.0, 87.0), Vector2(48.0, 90.0), Vector2(45.0, 87.0)],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(7.0, 67.0),
			Vector2(18.0, 72.0),
			Vector2(31.0, 88.0),
			Vector2(27.0, 94.0),
			Vector2(15.0, 77.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 71.0),
			Vector2(17.0, 75.0),
			Vector2(27.0, 88.0),
			Vector2(26.0, 90.0),
			Vector2(18.0, 80.0)
		],
		steel
	)
	canvas.draw_line(
		_p(box, 16.0, 77.0), _p(box, 25.0, 87.0), void_glow, maxf(1.0 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 21.0, 92.0), _p(box, 33.0, 85.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(89.0, 64.0),
			Vector2(85.0, 76.0),
			Vector2(72.0, 94.0),
			Vector2(66.0, 89.0),
			Vector2(80.0, 72.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(85.0, 70.0),
			Vector2(82.0, 76.0),
			Vector2(71.0, 90.0),
			Vector2(70.0, 88.0),
			Vector2(80.0, 75.0)
		],
		steel
	)
	canvas.draw_line(
		_p(box, 81.0, 77.0), _p(box, 72.0, 88.0), void_glow, maxf(1.0 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 64.0, 85.0), _p(box, 76.0, 92.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 27.0, 83.0), 3.0 * unit, mask)
	canvas.draw_circle(_p(box, 70.0, 82.0), 3.0 * unit, shade)


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
