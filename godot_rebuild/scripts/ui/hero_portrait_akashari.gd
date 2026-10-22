extends RefCounted
## Native canvas portrait: Akashari, The Painbringer / Queen of Pain.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(25, 14, 34)
	var wing := Color8(80, 25, 64)
	var membrane := Color8(140, 44, 87)
	var red := Color8(193, 49, 92)
	var rose := Color8(255, 135, 177)
	var skin := Color8(190, 132, 170)
	var light := Color8(234, 187, 216)
	var hair := Color8(40, 22, 50)
	var steel := Color8(129, 105, 157)
	var gold := Color8(220, 166, 105)
	_backdrop(canvas, box, Color8(83, 38, 98), Color8(23, 13, 33))

	# Tall bat wings frame a horn-crowned sorceress rather than a generic bust.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 81.0),
			Vector2(7.0, 25.0),
			Vector2(14.0, 11.0),
			Vector2(25.0, 29.0),
			Vector2(35.0, 46.0),
			Vector2(34.0, 67.0),
			Vector2(22.0, 62.0),
			Vector2(16.0, 69.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 73.0),
			Vector2(11.0, 27.0),
			Vector2(15.0, 18.0),
			Vector2(23.0, 32.0),
			Vector2(31.0, 47.0),
			Vector2(30.0, 61.0),
			Vector2(21.0, 58.0),
			Vector2(15.0, 64.0)
		],
		wing
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 31.0),
			Vector2(19.0, 35.0),
			Vector2(27.0, 48.0),
			Vector2(20.0, 54.0),
			Vector2(15.0, 58.0)
		],
		membrane
	)
	canvas.draw_line(_p(box, 14.0, 23.0), _p(box, 20.0, 56.0), red, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 20.0, 56.0), _p(box, 29.0, 61.0), red, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(88.0, 81.0),
			Vector2(89.0, 25.0),
			Vector2(82.0, 11.0),
			Vector2(71.0, 29.0),
			Vector2(61.0, 46.0),
			Vector2(62.0, 67.0),
			Vector2(74.0, 62.0),
			Vector2(80.0, 69.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(85.0, 73.0),
			Vector2(85.0, 27.0),
			Vector2(81.0, 18.0),
			Vector2(73.0, 32.0),
			Vector2(65.0, 47.0),
			Vector2(66.0, 61.0),
			Vector2(75.0, 58.0),
			Vector2(81.0, 64.0)
		],
		wing
	)
	_fill(
		canvas,
		box,
		[
			Vector2(83.0, 31.0),
			Vector2(77.0, 35.0),
			Vector2(69.0, 48.0),
			Vector2(76.0, 54.0),
			Vector2(81.0, 58.0)
		],
		membrane
	)
	canvas.draw_line(_p(box, 82.0, 23.0), _p(box, 76.0, 56.0), red, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 76.0, 56.0), _p(box, 67.0, 61.0), red, maxf(1.5 * unit, 1.0), true)

	# Black hair, a high barbed collar and a ruby corset.
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 31.0),
			Vector2(32.0, 21.0),
			Vector2(43.0, 16.0),
			Vector2(56.0, 18.0),
			Vector2(65.0, 26.0),
			Vector2(69.0, 58.0),
			Vector2(63.0, 71.0),
			Vector2(33.0, 72.0),
			Vector2(26.0, 57.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 31.0),
			Vector2(36.0, 24.0),
			Vector2(44.0, 20.0),
			Vector2(55.0, 22.0),
			Vector2(61.0, 28.0),
			Vector2(65.0, 57.0),
			Vector2(60.0, 66.0),
			Vector2(35.0, 67.0),
			Vector2(30.0, 55.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 96.0),
			Vector2(20.0, 73.0),
			Vector2(31.0, 63.0),
			Vector2(33.0, 52.0),
			Vector2(45.0, 63.0),
			Vector2(51.0, 63.0),
			Vector2(63.0, 52.0),
			Vector2(65.0, 63.0),
			Vector2(76.0, 73.0),
			Vector2(82.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(19.0, 94.0),
			Vector2(25.0, 75.0),
			Vector2(35.0, 66.0),
			Vector2(36.0, 59.0),
			Vector2(45.0, 68.0),
			Vector2(51.0, 68.0),
			Vector2(60.0, 59.0),
			Vector2(61.0, 66.0),
			Vector2(71.0, 75.0),
			Vector2(77.0, 94.0)
		],
		wing
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 73.0),
			Vector2(39.0, 65.0),
			Vector2(57.0, 65.0),
			Vector2(67.0, 73.0),
			Vector2(60.0, 83.0),
			Vector2(36.0, 83.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 76.0),
			Vector2(40.0, 78.0),
			Vector2(48.0, 73.0),
			Vector2(56.0, 78.0),
			Vector2(65.0, 76.0),
			Vector2(61.0, 94.0),
			Vector2(35.0, 94.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 81.0),
			Vector2(41.0, 82.0),
			Vector2(48.0, 77.0),
			Vector2(55.0, 82.0),
			Vector2(61.0, 81.0),
			Vector2(58.0, 94.0),
			Vector2(38.0, 94.0)
		],
		red
	)
	canvas.draw_line(_p(box, 41.0, 84.0), _p(box, 54.0, 92.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 55.0, 84.0), _p(box, 42.0, 92.0), gold, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 29.0),
			Vector2(42.0, 24.0),
			Vector2(54.0, 24.0),
			Vector2(62.0, 30.0),
			Vector2(60.0, 43.0),
			Vector2(54.0, 53.0),
			Vector2(46.0, 57.0),
			Vector2(37.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 31.0),
			Vector2(43.0, 27.0),
			Vector2(53.0, 27.0),
			Vector2(59.0, 32.0),
			Vector2(57.0, 42.0),
			Vector2(52.0, 50.0),
			Vector2(46.0, 53.0),
			Vector2(40.0, 46.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 31.0),
			Vector2(34.0, 22.0),
			Vector2(45.0, 18.0),
			Vector2(58.0, 21.0),
			Vector2(64.0, 30.0),
			Vector2(61.0, 39.0),
			Vector2(53.0, 29.0),
			Vector2(47.0, 25.0),
			Vector2(41.0, 32.0),
			Vector2(35.0, 40.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 38.0, 36.0), _p(box, 44.0, 38.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 38.0), _p(box, 58.0, 35.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 39.0), _p(box, 44.0, 39.0), rose, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 39.0), _p(box, 57.0, 38.0), rose, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 38.0), _p(box, 46.0, 44.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 43.0, 48.0), _p(box, 52.0, 47.0), red, maxf(2.0 * unit, 1.0), true)
	_fill(canvas, box, [Vector2(43.0, 48.0), Vector2(45.0, 48.0), Vector2(45.0, 51.0)], light)
	_fill(canvas, box, [Vector2(50.0, 48.0), Vector2(52.0, 47.0), Vector2(50.0, 51.0)], light)

	# Swept horns and a suspended jewel emphasize the queen silhouette.
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 28.0),
			Vector2(28.0, 19.0),
			Vector2(28.0, 8.0),
			Vector2(34.0, 14.0),
			Vector2(37.0, 21.0),
			Vector2(43.0, 25.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 25.0),
			Vector2(31.0, 18.0),
			Vector2(30.0, 12.0),
			Vector2(34.0, 17.0),
			Vector2(39.0, 25.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(54.0, 25.0),
			Vector2(60.0, 17.0),
			Vector2(66.0, 8.0),
			Vector2(67.0, 18.0),
			Vector2(62.0, 28.0),
			Vector2(57.0, 30.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 25.0),
			Vector2(62.0, 18.0),
			Vector2(65.0, 12.0),
			Vector2(64.0, 18.0),
			Vector2(60.0, 26.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 38.0, 29.0), _p(box, 58.0, 29.0), gold, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 27.0), Vector2(51.0, 31.0), Vector2(48.0, 35.0), Vector2(45.0, 31.0)],
		rose
	)
	canvas.draw_circle(_p(box, 36.0, 45.0), 1.6 * unit, gold)
	canvas.draw_circle(_p(box, 60.0, 44.0), 1.6 * unit, gold)
	canvas.draw_line(_p(box, 48.0, 56.0), _p(box, 48.0, 66.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 66.0), 2.0 * unit, rose)

	# A hooked lash curls along the left edge; a dagger guards the right.
	canvas.draw_arc(
		_p(box, 16.0, 84.0), 9.0 * unit, PI * -0.8, PI * 0.9, 32, gold, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 10.0, 79.0), _p(box, 14.0, 67.0), gold, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(71.0, 91.0),
			Vector2(73.0, 66.0),
			Vector2(79.0, 53.0),
			Vector2(80.0, 76.0),
			Vector2(76.0, 91.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(74.0, 85.0),
			Vector2(76.0, 68.0),
			Vector2(78.0, 61.0),
			Vector2(78.0, 75.0),
			Vector2(75.0, 86.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 69.0, 87.0), _p(box, 81.0, 88.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 25.0, 85.0), 4.0 * unit, skin)
	canvas.draw_line(_p(box, 22.0, 84.0), _p(box, 28.0, 87.0), red, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 73.0, 90.0), 3.0 * unit, skin)


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
