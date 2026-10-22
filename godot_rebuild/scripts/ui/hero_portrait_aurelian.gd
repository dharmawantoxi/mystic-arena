extends RefCounted
## Native canvas portrait: Aurelian, The Goldspear Sovereign / Fighter-Tank.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(34, 28, 24)
	var gold := Color8(203, 153, 60)
	var light := Color8(250, 219, 139)
	var bronze := Color8(129, 89, 38)
	var steel := Color8(88, 98, 105)
	var cape := Color8(118, 31, 43)
	var red := Color8(191, 60, 65)
	var skin := Color8(204, 157, 116)
	var shade := Color8(142, 95, 71)
	var hair := Color8(70, 49, 34)
	_backdrop(canvas, box, Color8(91, 69, 41), Color8(28, 27, 30))

	# An engraved golden aureole rises above a broad sovereign silhouette.
	canvas.draw_arc(
		_p(box, 47.0, 40.0),
		33.0 * unit,
		PI * -0.94,
		PI * -0.06,
		32,
		bronze,
		maxf(3.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 47.0, 40.0),
		30.0 * unit,
		PI * -0.87,
		PI * -0.13,
		32,
		light,
		maxf(1.0 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 22.0, 15.0), _p(box, 27.0, 21.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 46.0, 6.0), _p(box, 46.0, 14.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 68.0, 15.0), _p(box, 64.0, 21.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(7.0, 96.0),
			Vector2(12.0, 69.0),
			Vector2(27.0, 56.0),
			Vector2(65.0, 55.0),
			Vector2(79.0, 66.0),
			Vector2(88.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 94.0),
			Vector2(17.0, 71.0),
			Vector2(29.0, 60.0),
			Vector2(63.0, 59.0),
			Vector2(75.0, 69.0),
			Vector2(83.0, 94.0)
		],
		cape
	)
	_fill(
		canvas,
		box,
		[Vector2(17.0, 74.0), Vector2(28.0, 65.0), Vector2(30.0, 93.0), Vector2(15.0, 93.0)],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 64.0),
			Vector2(39.0, 56.0),
			Vector2(57.0, 56.0),
			Vector2(68.0, 64.0),
			Vector2(66.0, 96.0),
			Vector2(27.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 66.0),
			Vector2(40.0, 60.0),
			Vector2(55.0, 60.0),
			Vector2(64.0, 66.0),
			Vector2(62.0, 94.0),
			Vector2(31.0, 94.0)
		],
		bronze
	)
	_fill(
		canvas,
		box,
		[Vector2(35.0, 65.0), Vector2(47.0, 70.0), Vector2(47.0, 86.0), Vector2(33.0, 79.0)],
		gold
	)
	_fill(
		canvas,
		box,
		[Vector2(50.0, 70.0), Vector2(60.0, 65.0), Vector2(62.0, 79.0), Vector2(50.0, 86.0)],
		gold
	)
	canvas.draw_line(_p(box, 36.0, 68.0), _p(box, 44.0, 72.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 72.0), _p(box, 59.0, 69.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 72.0), _p(box, 48.0, 94.0), ink, maxf(2.0 * unit, 1.0), true)

	# Heavy stepped pauldrons, rivets and a central royal seal.
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 67.0),
			Vector2(20.0, 53.0),
			Vector2(31.0, 57.0),
			Vector2(39.0, 67.0),
			Vector2(31.0, 82.0),
			Vector2(15.0, 80.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 67.0),
			Vector2(22.0, 58.0),
			Vector2(29.0, 61.0),
			Vector2(34.0, 68.0),
			Vector2(28.0, 77.0),
			Vector2(18.0, 76.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[Vector2(14.0, 72.0), Vector2(28.0, 73.0), Vector2(31.0, 78.0), Vector2(17.0, 79.0)],
		bronze
	)
	_fill(
		canvas,
		box,
		[
			Vector2(85.0, 67.0),
			Vector2(74.0, 53.0),
			Vector2(63.0, 57.0),
			Vector2(55.0, 67.0),
			Vector2(63.0, 82.0),
			Vector2(79.0, 80.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(80.0, 67.0),
			Vector2(72.0, 58.0),
			Vector2(65.0, 61.0),
			Vector2(60.0, 68.0),
			Vector2(66.0, 77.0),
			Vector2(76.0, 76.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[Vector2(80.0, 72.0), Vector2(66.0, 73.0), Vector2(63.0, 78.0), Vector2(77.0, 79.0)],
		bronze
	)
	canvas.draw_circle(_p(box, 22.0, 63.0), 1.5 * unit, light)
	canvas.draw_circle(_p(box, 29.0, 68.0), 1.5 * unit, light)
	canvas.draw_circle(_p(box, 72.0, 63.0), 1.5 * unit, light)
	canvas.draw_circle(_p(box, 65.0, 68.0), 1.5 * unit, light)
	canvas.draw_circle(_p(box, 48.0, 82.0), 6.0 * unit, ink)
	canvas.draw_circle(_p(box, 48.0, 82.0), 4.0 * unit, gold)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 78.0), Vector2(50.0, 82.0), Vector2(48.0, 86.0), Vector2(46.0, 82.0)],
		light
	)

	# A crowned open-faced helm, square beard and solemn amber eyes.
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 28.0),
			Vector2(36.0, 19.0),
			Vector2(56.0, 18.0),
			Vector2(65.0, 28.0),
			Vector2(64.0, 45.0),
			Vector2(56.0, 56.0),
			Vector2(40.0, 57.0),
			Vector2(31.0, 46.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 30.0),
			Vector2(39.0, 23.0),
			Vector2(54.0, 22.0),
			Vector2(61.0, 30.0),
			Vector2(60.0, 43.0),
			Vector2(54.0, 52.0),
			Vector2(42.0, 53.0),
			Vector2(35.0, 44.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 25.0),
			Vector2(59.0, 29.0),
			Vector2(61.0, 34.0),
			Vector2(58.0, 45.0),
			Vector2(53.0, 51.0),
			Vector2(48.0, 47.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 43.0),
			Vector2(42.0, 46.0),
			Vector2(48.0, 44.0),
			Vector2(55.0, 45.0),
			Vector2(61.0, 40.0),
			Vector2(58.0, 52.0),
			Vector2(49.0, 59.0),
			Vector2(39.0, 53.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 43.0, 48.0), _p(box, 52.0, 48.0), skin, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 46.0, 51.0), _p(box, 50.0, 51.0), light, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 32.0),
			Vector2(28.0, 15.0),
			Vector2(37.0, 20.0),
			Vector2(43.0, 9.0),
			Vector2(48.0, 20.0),
			Vector2(57.0, 9.0),
			Vector2(60.0, 21.0),
			Vector2(68.0, 16.0),
			Vector2(65.0, 33.0),
			Vector2(56.0, 29.0),
			Vector2(38.0, 30.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 29.0),
			Vector2(32.0, 21.0),
			Vector2(38.0, 24.0),
			Vector2(43.0, 15.0),
			Vector2(48.0, 25.0),
			Vector2(56.0, 15.0),
			Vector2(58.0, 25.0),
			Vector2(64.0, 22.0),
			Vector2(62.0, 29.0),
			Vector2(55.0, 26.0),
			Vector2(39.0, 27.0)
		],
		gold
	)
	canvas.draw_line(_p(box, 35.0, 26.0), _p(box, 61.0, 26.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 26.0), 2.5 * unit, red)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 30.0),
			Vector2(36.0, 30.0),
			Vector2(36.0, 40.0),
			Vector2(40.0, 46.0),
			Vector2(35.0, 48.0),
			Vector2(30.0, 41.0)
		],
		bronze
	)
	_fill(
		canvas,
		box,
		[
			Vector2(59.0, 30.0),
			Vector2(64.0, 30.0),
			Vector2(64.0, 41.0),
			Vector2(59.0, 48.0),
			Vector2(56.0, 45.0),
			Vector2(59.0, 39.0)
		],
		bronze
	)
	canvas.draw_line(_p(box, 38.0, 34.0), _p(box, 44.0, 36.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 36.0), _p(box, 58.0, 34.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 38.0), _p(box, 43.0, 38.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 38.0), _p(box, 57.0, 38.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 36.0), _p(box, 46.0, 43.0), skin, maxf(2.0 * unit, 1.0), true)

	# The gold spear remains the tallest prop; a compact shield anchors the opposite side.
	canvas.draw_line(_p(box, 80.0, 37.0), _p(box, 80.0, 94.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 80.0, 37.0), _p(box, 80.0, 94.0), gold, maxf(2.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(80.0, 7.0),
			Vector2(88.0, 26.0),
			Vector2(85.0, 36.0),
			Vector2(80.0, 42.0),
			Vector2(75.0, 36.0),
			Vector2(72.0, 26.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(80.0, 12.0),
			Vector2(85.0, 26.0),
			Vector2(83.0, 34.0),
			Vector2(80.0, 38.0),
			Vector2(77.0, 34.0),
			Vector2(75.0, 26.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[Vector2(80.0, 15.0), Vector2(82.0, 27.0), Vector2(80.0, 35.0), Vector2(78.0, 27.0)],
		light
	)
	canvas.draw_line(_p(box, 74.0, 40.0), _p(box, 86.0, 40.0), bronze, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 82.0),
			Vector2(20.0, 75.0),
			Vector2(33.0, 81.0),
			Vector2(32.0, 91.0),
			Vector2(22.0, 96.0),
			Vector2(11.0, 92.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 83.0),
			Vector2(20.0, 79.0),
			Vector2(29.0, 83.0),
			Vector2(28.0, 89.0),
			Vector2(22.0, 93.0),
			Vector2(14.0, 89.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(19.0, 81.0),
			Vector2(23.0, 81.0),
			Vector2(24.0, 88.0),
			Vector2(21.0, 92.0),
			Vector2(18.0, 87.0)
		],
		gold
	)
	canvas.draw_circle(_p(box, 77.0, 81.0), 4.0 * unit, skin)
	canvas.draw_line(_p(box, 75.0, 83.0), _p(box, 80.0, 83.0), bronze, maxf(2.0 * unit, 1.0), true)


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
