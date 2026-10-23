extends RefCounted
## Native canvas portrait: Grondarthul, The Troll King.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(33, 32, 28)
	var skin := Color8(103, 143, 115)
	var shade := Color8(60, 96, 84)
	var light := Color8(192, 211, 164)
	var hair := Color8(63, 69, 54)
	var gold := Color8(188, 151, 66)
	var bronze := Color8(111, 88, 42)
	var bone := Color8(225, 211, 157)
	var cloth := Color8(105, 47, 61)
	var fur := Color8(157, 152, 117)
	var wood := Color8(99, 71, 41)
	_backdrop(canvas, box, Color8(63, 87, 64), Color8(25, 32, 29))

	# Totem uprights and a hammered crown frame a broad troll monarch.
	canvas.draw_line(_p(box, 12.0, 20.0), _p(box, 12.0, 90.0), ink, maxf(9.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 12.0, 20.0), _p(box, 12.0, 90.0), wood, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 82.0, 21.0), _p(box, 82.0, 90.0), ink, maxf(9.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 82.0, 21.0), _p(box, 82.0, 90.0), wood, maxf(5.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(6.0, 20.0),
			Vector2(12.0, 10.0),
			Vector2(18.0, 20.0),
			Vector2(15.0, 27.0),
			Vector2(9.0, 27.0)
		],
		bone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(76.0, 21.0),
			Vector2(82.0, 11.0),
			Vector2(88.0, 21.0),
			Vector2(85.0, 28.0),
			Vector2(79.0, 28.0)
		],
		bone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(5.0, 96.0),
			Vector2(12.0, 66.0),
			Vector2(27.0, 53.0),
			Vector2(64.0, 54.0),
			Vector2(83.0, 67.0),
			Vector2(92.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 94.0),
			Vector2(18.0, 69.0),
			Vector2(29.0, 59.0),
			Vector2(62.0, 60.0),
			Vector2(77.0, 70.0),
			Vector2(86.0, 94.0)
		],
		cloth
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 65.0),
			Vector2(40.0, 57.0),
			Vector2(56.0, 58.0),
			Vector2(67.0, 68.0),
			Vector2(70.0, 94.0),
			Vector2(26.0, 94.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 61.0),
			Vector2(59.0, 64.0),
			Vector2(65.0, 71.0),
			Vector2(67.0, 94.0),
			Vector2(50.0, 94.0)
		],
		shade
	)

	# An uneven fur mantle, trophy teeth and a heavy royal chain.
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 66.0),
			Vector2(25.0, 52.0),
			Vector2(38.0, 59.0),
			Vector2(46.0, 71.0),
			Vector2(58.0, 59.0),
			Vector2(69.0, 54.0),
			Vector2(81.0, 67.0),
			Vector2(74.0, 80.0),
			Vector2(61.0, 74.0),
			Vector2(47.0, 82.0),
			Vector2(33.0, 74.0),
			Vector2(20.0, 79.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 66.0),
			Vector2(26.0, 58.0),
			Vector2(35.0, 65.0),
			Vector2(44.0, 75.0),
			Vector2(48.0, 76.0),
			Vector2(59.0, 65.0),
			Vector2(68.0, 60.0),
			Vector2(75.0, 67.0),
			Vector2(70.0, 74.0),
			Vector2(60.0, 69.0),
			Vector2(47.0, 79.0),
			Vector2(34.0, 69.0),
			Vector2(22.0, 74.0)
		],
		fur
	)
	canvas.draw_line(_p(box, 32.0, 70.0), _p(box, 47.0, 83.0), gold, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 83.0), _p(box, 63.0, 69.0), gold, maxf(3.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 47.0, 84.0), 6.0 * unit, ink)
	canvas.draw_circle(_p(box, 47.0, 84.0), 4.0 * unit, gold)
	_fill(
		canvas,
		box,
		[Vector2(47.0, 81.0), Vector2(50.0, 84.0), Vector2(47.0, 88.0), Vector2(44.0, 84.0)],
		bone
	)
	_fill(canvas, box, [Vector2(23.0, 70.0), Vector2(27.0, 70.0), Vector2(25.0, 77.0)], bone)
	_fill(canvas, box, [Vector2(32.0, 67.0), Vector2(36.0, 67.0), Vector2(34.0, 74.0)], bone)
	_fill(canvas, box, [Vector2(63.0, 67.0), Vector2(67.0, 67.0), Vector2(65.0, 74.0)], bone)
	_fill(canvas, box, [Vector2(70.0, 70.0), Vector2(74.0, 70.0), Vector2(72.0, 77.0)], bone)

	# Long pointed ears, a heavy nose, swept mohawk and two oversized tusks.
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 31.0),
			Vector2(16.0, 25.0),
			Vector2(21.0, 40.0),
			Vector2(28.0, 44.0),
			Vector2(31.0, 51.0),
			Vector2(40.0, 61.0),
			Vector2(56.0, 60.0),
			Vector2(64.0, 50.0),
			Vector2(67.0, 43.0),
			Vector2(74.0, 38.0),
			Vector2(79.0, 24.0),
			Vector2(65.0, 30.0),
			Vector2(58.0, 20.0),
			Vector2(38.0, 20.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 32.0),
			Vector2(23.0, 30.0),
			Vector2(26.0, 37.0),
			Vector2(32.0, 39.0),
			Vector2(35.0, 48.0),
			Vector2(42.0, 55.0),
			Vector2(54.0, 55.0),
			Vector2(60.0, 47.0),
			Vector2(63.0, 38.0),
			Vector2(70.0, 35.0),
			Vector2(73.0, 30.0),
			Vector2(62.0, 35.0),
			Vector2(57.0, 25.0),
			Vector2(40.0, 25.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 27.0),
			Vector2(58.0, 30.0),
			Vector2(62.0, 37.0),
			Vector2(59.0, 47.0),
			Vector2(54.0, 53.0),
			Vector2(48.0, 50.0),
			Vector2(51.0, 41.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 30.0),
			Vector2(31.0, 21.0),
			Vector2(39.0, 22.0),
			Vector2(41.0, 12.0),
			Vector2(47.0, 18.0),
			Vector2(52.0, 10.0),
			Vector2(58.0, 17.0),
			Vector2(63.0, 23.0),
			Vector2(64.0, 31.0),
			Vector2(55.0, 27.0),
			Vector2(41.0, 28.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 26.0),
			Vector2(25.0, 12.0),
			Vector2(35.0, 18.0),
			Vector2(39.0, 7.0),
			Vector2(47.0, 17.0),
			Vector2(55.0, 7.0),
			Vector2(60.0, 19.0),
			Vector2(69.0, 13.0),
			Vector2(66.0, 28.0),
			Vector2(55.0, 31.0),
			Vector2(39.0, 30.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 25.0),
			Vector2(30.0, 19.0),
			Vector2(36.0, 23.0),
			Vector2(40.0, 14.0),
			Vector2(47.0, 23.0),
			Vector2(54.0, 14.0),
			Vector2(58.0, 24.0),
			Vector2(64.0, 20.0),
			Vector2(63.0, 25.0),
			Vector2(54.0, 27.0),
			Vector2(40.0, 26.0)
		],
		gold
	)
	canvas.draw_line(_p(box, 35.0, 25.0), _p(box, 60.0, 25.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 47.0, 24.0), 2.0 * unit, cloth)
	canvas.draw_line(_p(box, 34.0, 35.0), _p(box, 42.0, 37.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 37.0), _p(box, 60.0, 34.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 40.0), _p(box, 42.0, 40.0), bone, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 40.0), _p(box, 58.0, 39.0), bone, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(43.0, 36.0),
			Vector2(49.0, 36.0),
			Vector2(54.0, 45.0),
			Vector2(47.0, 49.0),
			Vector2(39.0, 45.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 44.0, 39.0), _p(box, 43.0, 43.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 50.0), _p(box, 57.0, 49.0), ink, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(35.0, 48.0), Vector2(33.0, 39.0), Vector2(39.0, 45.0), Vector2(42.0, 52.0)],
		bone
	)
	_fill(
		canvas,
		box,
		[Vector2(52.0, 51.0), Vector2(57.0, 44.0), Vector2(61.0, 38.0), Vector2(60.0, 48.0)],
		bone
	)
	canvas.draw_line(_p(box, 42.0, 54.0), _p(box, 53.0, 53.0), shade, maxf(1.5 * unit, 1.0), true)

	# A stone-topped sceptre, a bound grip and broad hands complete the king.
	canvas.draw_line(_p(box, 79.0, 48.0), _p(box, 76.0, 95.0), ink, maxf(7.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 79.0, 48.0), _p(box, 76.0, 95.0), wood, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 34.0),
			Vector2(81.0, 29.0),
			Vector2(89.0, 37.0),
			Vector2(87.0, 47.0),
			Vector2(78.0, 52.0),
			Vector2(70.0, 44.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(76.0, 36.0),
			Vector2(81.0, 34.0),
			Vector2(85.0, 39.0),
			Vector2(83.0, 45.0),
			Vector2(78.0, 47.0),
			Vector2(74.0, 42.0)
		],
		bronze
	)
	_fill(
		canvas,
		box,
		[Vector2(80.0, 34.0), Vector2(83.0, 39.0), Vector2(80.0, 43.0), Vector2(77.0, 39.0)],
		gold
	)
	canvas.draw_line(_p(box, 73.0, 52.0), _p(box, 84.0, 53.0), bone, maxf(3.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 74.0, 80.0), 5.0 * unit, skin)
	canvas.draw_line(_p(box, 71.0, 84.0), _p(box, 78.0, 85.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 82.0),
			Vector2(20.0, 78.0),
			Vector2(30.0, 85.0),
			Vector2(28.0, 96.0),
			Vector2(7.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 85.0),
			Vector2(20.0, 83.0),
			Vector2(25.0, 87.0),
			Vector2(24.0, 93.0),
			Vector2(12.0, 93.0)
		],
		skin
	)
	canvas.draw_line(_p(box, 16.0, 87.0), _p(box, 16.0, 91.0), shade, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 21.0, 87.0), _p(box, 21.0, 92.0), shade, maxf(1.5 * unit, 1.0), true)


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
