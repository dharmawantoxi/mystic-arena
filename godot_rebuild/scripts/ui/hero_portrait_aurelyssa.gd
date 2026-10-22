extends RefCounted
## Native canvas portrait: Aurelyssa, The Golden Blade Dancer / Blade Dancer.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(38, 25, 35)
	var cloth := Color8(103, 32, 76)
	var rose := Color8(177, 68, 114)
	var gold := Color8(216, 164, 66)
	var light := Color8(255, 225, 149)
	var bronze := Color8(138, 88, 43)
	var skin := Color8(220, 166, 131)
	var shade := Color8(166, 106, 91)
	var hair := Color8(61, 34, 46)
	var steel := Color8(220, 232, 216)
	_backdrop(canvas, box, Color8(99, 51, 70), Color8(31, 24, 39))

	# Arcing ribbons and a long high ponytail suggest a turning dance pose.
	canvas.draw_arc(
		_p(box, 48.0, 52.0),
		40.0 * unit,
		PI * -0.95,
		PI * -0.15,
		48,
		bronze,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 52.0), 37.0 * unit, PI * 0.1, PI * 0.8, 48, gold, maxf(1.5 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[
			Vector2(54.0, 26.0),
			Vector2(65.0, 16.0),
			Vector2(77.0, 19.0),
			Vector2(83.0, 32.0),
			Vector2(78.0, 47.0),
			Vector2(84.0, 59.0),
			Vector2(70.0, 52.0),
			Vector2(68.0, 36.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 26.0),
			Vector2(66.0, 20.0),
			Vector2(74.0, 23.0),
			Vector2(78.0, 33.0),
			Vector2(74.0, 46.0),
			Vector2(78.0, 53.0),
			Vector2(72.0, 49.0),
			Vector2(72.0, 34.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 68.0, 24.0), _p(box, 75.0, 34.0), rose, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 58.0),
			Vector2(20.0, 48.0),
			Vector2(12.0, 49.0),
			Vector2(18.0, 56.0),
			Vector2(12.0, 63.0),
			Vector2(25.0, 66.0),
			Vector2(39.0, 67.0)
		],
		rose
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 60.0),
			Vector2(20.0, 53.0),
			Vector2(17.0, 53.0),
			Vector2(22.0, 58.0),
			Vector2(18.0, 61.0),
			Vector2(27.0, 63.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 96.0),
			Vector2(22.0, 77.0),
			Vector2(34.0, 64.0),
			Vector2(53.0, 60.0),
			Vector2(67.0, 70.0),
			Vector2(80.0, 95.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(20.0, 94.0),
			Vector2(26.0, 79.0),
			Vector2(36.0, 68.0),
			Vector2(52.0, 64.0),
			Vector2(63.0, 73.0),
			Vector2(74.0, 94.0)
		],
		cloth
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 66.0),
			Vector2(40.0, 59.0),
			Vector2(51.0, 58.0),
			Vector2(57.0, 67.0),
			Vector2(50.0, 77.0),
			Vector2(40.0, 77.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(48.0, 61.0),
			Vector2(53.0, 63.0),
			Vector2(56.0, 68.0),
			Vector2(49.0, 74.0),
			Vector2(46.0, 70.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 68.0),
			Vector2(41.0, 76.0),
			Vector2(50.0, 76.0),
			Vector2(57.0, 67.0),
			Vector2(60.0, 73.0),
			Vector2(51.0, 82.0),
			Vector2(39.0, 81.0),
			Vector2(30.0, 74.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[Vector2(37.0, 83.0), Vector2(49.0, 83.0), Vector2(57.0, 94.0), Vector2(29.0, 94.0)],
		rose
	)
	canvas.draw_line(_p(box, 34.0, 73.0), _p(box, 41.0, 79.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 78.0), _p(box, 57.0, 72.0), light, maxf(1.5 * unit, 1.0), true)

	# An asymmetric gold circlet and swept fringe frame a turned face.
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 29.0),
			Vector2(38.0, 20.0),
			Vector2(53.0, 19.0),
			Vector2(63.0, 27.0),
			Vector2(62.0, 42.0),
			Vector2(55.0, 53.0),
			Vector2(45.0, 58.0),
			Vector2(34.0, 49.0),
			Vector2(29.0, 39.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 30.0),
			Vector2(40.0, 24.0),
			Vector2(52.0, 23.0),
			Vector2(58.0, 29.0),
			Vector2(58.0, 40.0),
			Vector2(52.0, 50.0),
			Vector2(45.0, 54.0),
			Vector2(37.0, 47.0),
			Vector2(33.0, 38.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 25.0),
			Vector2(58.0, 29.0),
			Vector2(58.0, 40.0),
			Vector2(51.0, 49.0),
			Vector2(46.0, 51.0),
			Vector2(48.0, 42.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 34.0),
			Vector2(29.0, 23.0),
			Vector2(36.0, 24.0),
			Vector2(40.0, 15.0),
			Vector2(49.0, 17.0),
			Vector2(57.0, 16.0),
			Vector2(64.0, 25.0),
			Vector2(65.0, 38.0),
			Vector2(58.0, 33.0),
			Vector2(53.0, 24.0),
			Vector2(45.0, 30.0),
			Vector2(42.0, 26.0),
			Vector2(35.0, 37.0),
			Vector2(34.0, 49.0),
			Vector2(29.0, 44.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 27.0),
			Vector2(42.0, 22.0),
			Vector2(54.0, 22.0),
			Vector2(61.0, 28.0),
			Vector2(60.0, 31.0),
			Vector2(52.0, 25.0),
			Vector2(43.0, 25.0),
			Vector2(34.0, 30.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 23.0), Vector2(51.0, 26.0), Vector2(48.0, 30.0), Vector2(45.0, 26.0)],
		light
	)
	canvas.draw_line(_p(box, 36.0, 35.0), _p(box, 43.0, 36.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 36.0), _p(box, 56.0, 34.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 38.0), _p(box, 42.0, 38.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 38.0), _p(box, 55.0, 37.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 46.0, 36.0), _p(box, 44.0, 43.0), skin, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 42.0, 48.0), _p(box, 50.0, 47.0), cloth, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 34.0, 44.0), 2.0 * unit, gold)
	canvas.draw_circle(_p(box, 34.0, 48.0), 1.5 * unit, light)
	canvas.draw_circle(_p(box, 59.0, 43.0), 2.0 * unit, gold)
	canvas.draw_circle(_p(box, 59.0, 47.0), 1.5 * unit, light)
	_fill(
		canvas,
		box,
		[
			Vector2(39.0, 53.0),
			Vector2(45.0, 57.0),
			Vector2(54.0, 52.0),
			Vector2(54.0, 56.0),
			Vector2(46.0, 62.0),
			Vector2(40.0, 58.0)
		],
		gold
	)

	# Twin crescent blades curl inward around raised hands, not a static sword.
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 23.0),
			Vector2(16.0, 32.0),
			Vector2(19.0, 48.0),
			Vector2(28.0, 58.0),
			Vector2(28.0, 66.0),
			Vector2(18.0, 61.0),
			Vector2(11.0, 49.0),
			Vector2(7.0, 34.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 29.0),
			Vector2(14.0, 34.0),
			Vector2(17.0, 49.0),
			Vector2(24.0, 58.0),
			Vector2(23.0, 61.0),
			Vector2(15.0, 55.0),
			Vector2(10.0, 44.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 19.0, 61.0), _p(box, 32.0, 66.0), gold, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 26.0, 65.0), _p(box, 23.0, 77.0), ink, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 26.0, 65.0), _p(box, 23.0, 76.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(87.0, 21.0),
			Vector2(90.0, 34.0),
			Vector2(86.0, 49.0),
			Vector2(77.0, 60.0),
			Vector2(68.0, 65.0),
			Vector2(67.0, 58.0),
			Vector2(78.0, 49.0),
			Vector2(83.0, 33.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(86.0, 28.0),
			Vector2(87.0, 35.0),
			Vector2(83.0, 48.0),
			Vector2(76.0, 55.0),
			Vector2(72.0, 57.0),
			Vector2(72.0, 55.0),
			Vector2(80.0, 45.0),
			Vector2(85.0, 33.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 64.0, 64.0), _p(box, 78.0, 59.0), gold, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 70.0, 64.0), _p(box, 74.0, 76.0), ink, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 70.0, 64.0), _p(box, 74.0, 75.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(23.0, 72.0),
			Vector2(28.0, 70.0),
			Vector2(36.0, 80.0),
			Vector2(33.0, 86.0),
			Vector2(28.0, 82.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(69.0, 70.0),
			Vector2(74.0, 71.0),
			Vector2(70.0, 82.0),
			Vector2(63.0, 85.0),
			Vector2(60.0, 80.0)
		],
		skin
	)
	canvas.draw_line(_p(box, 27.0, 76.0), _p(box, 31.0, 74.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 67.0, 76.0), _p(box, 72.0, 77.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 46.0, 84.0), 4.0 * unit, ink)
	canvas.draw_circle(_p(box, 46.0, 84.0), 2.5 * unit, gold)
	canvas.draw_line(_p(box, 31.0, 90.0), _p(box, 40.0, 87.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 87.0), _p(box, 62.0, 91.0), gold, maxf(2.0 * unit, 1.0), true)


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
