extends RefCounted
## Native canvas portrait: Nyxallaria, The Abyss Mage.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(18, 19, 35)
	var abyss := Color8(33, 37, 65)
	var robe := Color8(44, 43, 78)
	var teal := Color8(44, 136, 139)
	var sea := Color8(67, 189, 174)
	var magenta := Color8(183, 76, 145)
	var light := Color8(197, 240, 209)
	var skin := Color8(134, 129, 159)
	var shade := Color8(79, 76, 112)
	var pearl := Color8(180, 195, 192)
	_backdrop(canvas, box, Color8(42, 45, 74), Color8(15, 20, 35))

	# A broken abyssal portal and curling tendrils surround the crowned caster.
	canvas.draw_circle(_p(box, 47.0, 41.0), 34.0 * unit, abyss)
	canvas.draw_arc(
		_p(box, 47.0, 41.0),
		35.0 * unit,
		PI * 0.15,
		PI * 1.3,
		56,
		magenta,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 47.0, 41.0), 35.0 * unit, PI * 1.48, PI * 2.35, 48, sea, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 15.0, 67.0),
		17.0 * unit,
		PI * 0.55,
		PI * 1.75,
		40,
		ink,
		maxf(10.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 15.0, 67.0),
		17.0 * unit,
		PI * 0.55,
		PI * 1.75,
		40,
		teal,
		maxf(4.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 82.0, 67.0),
		17.0 * unit,
		PI * 1.25,
		PI * 2.45,
		40,
		ink,
		maxf(10.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 82.0, 67.0),
		17.0 * unit,
		PI * 1.25,
		PI * 2.45,
		40,
		magenta,
		maxf(4.0 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 10.0, 26.0), 1.2 * unit, light)
	canvas.draw_circle(_p(box, 84.0, 19.0), 1.4 * unit, magenta)
	canvas.draw_circle(_p(box, 88.0, 34.0), 0.9 * unit, sea)

	# The robe splits into weighted tendril panels beneath a shell-like cuirass.
	_fill(
		canvas,
		box,
		[
			Vector2(5.0, 96.0),
			Vector2(11.0, 72.0),
			Vector2(30.0, 57.0),
			Vector2(63.0, 57.0),
			Vector2(83.0, 72.0),
			Vector2(92.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 94.0),
			Vector2(18.0, 74.0),
			Vector2(32.0, 63.0),
			Vector2(60.0, 63.0),
			Vector2(77.0, 74.0),
			Vector2(85.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 94.0),
			Vector2(19.0, 75.0),
			Vector2(31.0, 66.0),
			Vector2(39.0, 79.0),
			Vector2(31.0, 88.0),
			Vector2(34.0, 96.0)
		],
		teal
	)
	_fill(
		canvas,
		box,
		[
			Vector2(55.0, 79.0),
			Vector2(62.0, 65.0),
			Vector2(76.0, 75.0),
			Vector2(84.0, 94.0),
			Vector2(65.0, 96.0),
			Vector2(67.0, 87.0)
		],
		abyss
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 94.0),
			Vector2(24.0, 82.0),
			Vector2(28.0, 94.0),
			Vector2(34.0, 85.0),
			Vector2(37.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(59.0, 96.0),
			Vector2(63.0, 84.0),
			Vector2(69.0, 94.0),
			Vector2(75.0, 83.0),
			Vector2(79.0, 96.0)
		],
		magenta
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 69.0),
			Vector2(39.0, 61.0),
			Vector2(47.0, 68.0),
			Vector2(56.0, 61.0),
			Vector2(66.0, 69.0),
			Vector2(59.0, 84.0),
			Vector2(48.0, 90.0),
			Vector2(36.0, 83.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 70.0),
			Vector2(40.0, 66.0),
			Vector2(47.0, 73.0),
			Vector2(55.0, 66.0),
			Vector2(61.0, 70.0),
			Vector2(56.0, 80.0),
			Vector2(48.0, 85.0),
			Vector2(39.0, 80.0)
		],
		abyss
	)
	canvas.draw_line(_p(box, 48.0, 84.0), _p(box, 35.0, 70.0), sea, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 84.0), _p(box, 47.0, 73.0), pearl, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 84.0), _p(box, 60.0, 70.0), magenta, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 84.0), 2.5 * unit, light)

	# Pearl-studded sea fans replace a conventional wizard collar.
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 68.0),
			Vector2(14.0, 53.0),
			Vector2(25.0, 48.0),
			Vector2(37.0, 61.0),
			Vector2(32.0, 76.0),
			Vector2(18.0, 80.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(17.0, 67.0),
			Vector2(19.0, 57.0),
			Vector2(25.0, 54.0),
			Vector2(32.0, 62.0),
			Vector2(28.0, 71.0),
			Vector2(20.0, 74.0)
		],
		teal
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 61.0),
			Vector2(70.0, 48.0),
			Vector2(81.0, 53.0),
			Vector2(86.0, 68.0),
			Vector2(78.0, 80.0),
			Vector2(64.0, 76.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(64.0, 62.0),
			Vector2(71.0, 54.0),
			Vector2(77.0, 57.0),
			Vector2(80.0, 67.0),
			Vector2(75.0, 74.0),
			Vector2(67.0, 71.0)
		],
		abyss
	)
	canvas.draw_circle(_p(box, 19.0, 57.0), 2.0 * unit, pearl)
	canvas.draw_circle(_p(box, 27.0, 59.0), 1.5 * unit, light)
	canvas.draw_circle(_p(box, 75.0, 57.0), 2.0 * unit, pearl)
	canvas.draw_circle(_p(box, 68.0, 61.0), 1.5 * unit, magenta)

	# A many-pointed crown and asymmetric shadow give the face an abyssal cast.
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 30.0),
			Vector2(25.0, 10.0),
			Vector2(37.0, 18.0),
			Vector2(41.0, 4.0),
			Vector2(48.0, 16.0),
			Vector2(56.0, 3.0),
			Vector2(59.0, 18.0),
			Vector2(71.0, 9.0),
			Vector2(65.0, 31.0),
			Vector2(55.0, 36.0),
			Vector2(38.0, 35.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 27.0),
			Vector2(31.0, 18.0),
			Vector2(40.0, 23.0),
			Vector2(42.0, 13.0),
			Vector2(48.0, 23.0),
			Vector2(55.0, 12.0),
			Vector2(56.0, 24.0),
			Vector2(64.0, 18.0),
			Vector2(61.0, 28.0),
			Vector2(48.0, 32.0)
		],
		teal
	)
	canvas.draw_circle(_p(box, 48.0, 25.0), 3.0 * unit, magenta)
	canvas.draw_circle(_p(box, 48.0, 25.0), 1.2 * unit, light)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 32.0),
			Vector2(37.0, 22.0),
			Vector2(56.0, 21.0),
			Vector2(65.0, 31.0),
			Vector2(62.0, 48.0),
			Vector2(55.0, 58.0),
			Vector2(41.0, 58.0),
			Vector2(32.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 33.0),
			Vector2(41.0, 27.0),
			Vector2(54.0, 26.0),
			Vector2(60.0, 32.0),
			Vector2(58.0, 45.0),
			Vector2(53.0, 53.0),
			Vector2(43.0, 53.0),
			Vector2(37.0, 45.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(49.0, 26.0),
			Vector2(57.0, 28.0),
			Vector2(61.0, 34.0),
			Vector2(58.0, 46.0),
			Vector2(52.0, 54.0),
			Vector2(47.0, 50.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 32.0),
			Vector2(37.0, 23.0),
			Vector2(47.0, 20.0),
			Vector2(58.0, 23.0),
			Vector2(64.0, 32.0),
			Vector2(56.0, 29.0),
			Vector2(48.0, 31.0),
			Vector2(39.0, 28.0)
		],
		abyss
	)
	canvas.draw_line(_p(box, 36.0, 35.0), _p(box, 43.0, 37.0), ink, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 37.0), _p(box, 59.0, 34.0), ink, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 39.0), _p(box, 43.0, 39.0), sea, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 39.0), _p(box, 57.0, 38.0), magenta, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 38.0), _p(box, 45.0, 44.0), pearl, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(41.0, 48.0), Vector2(47.0, 46.0), Vector2(53.0, 48.0), Vector2(47.0, 52.0)],
		magenta
	)
	canvas.draw_line(_p(box, 36.0, 43.0), _p(box, 39.0, 47.0), teal, maxf(1.2 * unit, 1.0), true)

	# A clawed hand suspends a dark focus ringed by abyssal light.
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 95.0),
			Vector2(65.0, 84.0),
			Vector2(70.0, 77.0),
			Vector2(71.0, 68.0),
			Vector2(75.0, 67.0),
			Vector2(78.0, 77.0),
			Vector2(82.0, 70.0),
			Vector2(86.0, 71.0),
			Vector2(85.0, 82.0),
			Vector2(90.0, 88.0),
			Vector2(87.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(71.0, 91.0),
			Vector2(70.0, 84.0),
			Vector2(75.0, 80.0),
			Vector2(81.0, 81.0),
			Vector2(85.0, 88.0),
			Vector2(82.0, 93.0)
		],
		skin
	)
	canvas.draw_line(_p(box, 74.0, 80.0), _p(box, 74.0, 71.0), pearl, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 79.0, 80.0), _p(box, 83.0, 73.0), pearl, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 79.0, 57.0), 11.0 * unit, magenta)
	canvas.draw_circle(_p(box, 79.0, 57.0), 8.5 * unit, ink)
	canvas.draw_circle(_p(box, 79.0, 57.0), 5.0 * unit, abyss)
	canvas.draw_arc(
		_p(box, 79.0, 57.0), 7.0 * unit, PI * -0.8, PI * 0.55, 32, sea, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 76.0, 54.0), 1.5 * unit, light)
	canvas.draw_line(_p(box, 75.0, 68.0), _p(box, 73.0, 73.0), magenta, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 83.0, 67.0), _p(box, 85.0, 72.0), sea, maxf(1.0 * unit, 1.0), true)


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
