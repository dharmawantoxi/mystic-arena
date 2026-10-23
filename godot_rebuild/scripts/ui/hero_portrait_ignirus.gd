extends RefCounted
## Native canvas portrait: Ignirus, The Infernal Pyromancer / Infernal Mage.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(34, 23, 39)
	var robe := Color8(71, 33, 68)
	var purple := Color8(113, 47, 93)
	var red := Color8(163, 47, 49)
	var gold := Color8(208, 151, 66)
	var light := Color8(255, 228, 145)
	var fire := Color8(247, 119, 49)
	var skin := Color8(178, 122, 113)
	var shade := Color8(116, 75, 100)
	var bone := Color8(208, 186, 158)
	_backdrop(canvas, box, Color8(88, 40, 64), Color8(27, 21, 39))

	# An infernal sigil floats behind a tall horn-shaped cowl and narrow robe.
	canvas.draw_arc(
		_p(box, 47.0, 39.0),
		32.0 * unit,
		PI * -0.95,
		PI * -0.05,
		40,
		red,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 20.0, 19.0), _p(box, 27.0, 27.0), gold, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 72.0, 19.0), _p(box, 65.0, 27.0), gold, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 96.0),
			Vector2(19.0, 71.0),
			Vector2(32.0, 58.0),
			Vector2(59.0, 58.0),
			Vector2(75.0, 73.0),
			Vector2(82.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(19.0, 94.0),
			Vector2(25.0, 74.0),
			Vector2(34.0, 63.0),
			Vector2(57.0, 63.0),
			Vector2(69.0, 75.0),
			Vector2(76.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(25.0, 75.0),
			Vector2(36.0, 66.0),
			Vector2(45.0, 77.0),
			Vector2(40.0, 94.0),
			Vector2(20.0, 94.0)
		],
		purple
	)
	_fill(
		canvas,
		box,
		[
			Vector2(52.0, 77.0),
			Vector2(58.0, 66.0),
			Vector2(67.0, 75.0),
			Vector2(73.0, 94.0),
			Vector2(55.0, 94.0)
		],
		red
	)

	# A hooked gold collar, a fire seal and embroidered robe seams.
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 54.0),
			Vector2(38.0, 60.0),
			Vector2(47.0, 72.0),
			Vector2(59.0, 60.0),
			Vector2(66.0, 53.0),
			Vector2(61.0, 68.0),
			Vector2(48.0, 83.0),
			Vector2(33.0, 69.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 60.0),
			Vector2(39.0, 65.0),
			Vector2(47.0, 77.0),
			Vector2(58.0, 65.0),
			Vector2(61.0, 60.0),
			Vector2(58.0, 68.0),
			Vector2(48.0, 79.0),
			Vector2(36.0, 67.0)
		],
		robe
	)
	canvas.draw_circle(_p(box, 48.0, 80.0), 5.0 * unit, ink)
	canvas.draw_circle(_p(box, 48.0, 80.0), 3.0 * unit, fire)
	canvas.draw_circle(_p(box, 48.0, 80.0), 1.2 * unit, light)
	canvas.draw_line(_p(box, 32.0, 86.0), _p(box, 39.0, 91.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 57.0, 91.0), _p(box, 65.0, 86.0), gold, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(25.0, 38.0),
			Vector2(23.0, 14.0),
			Vector2(35.0, 22.0),
			Vector2(44.0, 14.0),
			Vector2(54.0, 17.0),
			Vector2(68.0, 10.0),
			Vector2(66.0, 35.0),
			Vector2(69.0, 48.0),
			Vector2(62.0, 62.0),
			Vector2(35.0, 63.0),
			Vector2(26.0, 52.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 37.0),
			Vector2(28.0, 23.0),
			Vector2(35.0, 28.0),
			Vector2(44.0, 20.0),
			Vector2(54.0, 23.0),
			Vector2(63.0, 18.0),
			Vector2(62.0, 36.0),
			Vector2(64.0, 47.0),
			Vector2(58.0, 57.0),
			Vector2(38.0, 58.0),
			Vector2(31.0, 50.0)
		],
		purple
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 35.0),
			Vector2(40.0, 26.0),
			Vector2(50.0, 25.0),
			Vector2(59.0, 31.0),
			Vector2(61.0, 42.0),
			Vector2(58.0, 45.0),
			Vector2(56.0, 34.0),
			Vector2(49.0, 29.0),
			Vector2(41.0, 30.0),
			Vector2(35.0, 38.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 36.0),
			Vector2(41.0, 30.0),
			Vector2(50.0, 30.0),
			Vector2(57.0, 36.0),
			Vector2(57.0, 47.0),
			Vector2(51.0, 56.0),
			Vector2(43.0, 57.0),
			Vector2(36.0, 49.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(38.0, 37.0),
			Vector2(43.0, 33.0),
			Vector2(49.0, 33.0),
			Vector2(53.0, 37.0),
			Vector2(53.0, 46.0),
			Vector2(49.0, 52.0),
			Vector2(44.0, 53.0),
			Vector2(39.0, 47.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(48.0, 34.0),
			Vector2(53.0, 38.0),
			Vector2(53.0, 46.0),
			Vector2(49.0, 51.0),
			Vector2(46.0, 49.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 39.0, 39.0), _p(box, 44.0, 40.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 40.0), _p(box, 53.0, 38.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 40.0, 42.0), _p(box, 43.0, 42.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 49.0, 42.0), _p(box, 52.0, 41.0), fire, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 46.0, 40.0), _p(box, 45.0, 46.0), skin, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 43.0, 49.0), _p(box, 49.0, 48.0), ink, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 40.0, 44.0), _p(box, 41.0, 48.0), red, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 44.0), _p(box, 50.0, 48.0), red, maxf(1.0 * unit, 1.0), true)

	# A forked staff holds a fire orb; the free hand shapes a small spell spark.
	canvas.draw_line(_p(box, 78.0, 53.0), _p(box, 76.0, 95.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 53.0), _p(box, 76.0, 95.0), gold, maxf(2.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(65.0, 29.0),
			Vector2(71.0, 35.0),
			Vector2(72.0, 47.0),
			Vector2(78.0, 51.0),
			Vector2(84.0, 46.0),
			Vector2(85.0, 35.0),
			Vector2(92.0, 27.0),
			Vector2(90.0, 48.0),
			Vector2(80.0, 59.0),
			Vector2(71.0, 54.0),
			Vector2(65.0, 44.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 35.0),
			Vector2(71.0, 39.0),
			Vector2(74.0, 49.0),
			Vector2(78.0, 54.0),
			Vector2(85.0, 48.0),
			Vector2(88.0, 38.0),
			Vector2(88.0, 46.0),
			Vector2(79.0, 56.0),
			Vector2(73.0, 52.0),
			Vector2(68.0, 43.0)
		],
		gold
	)
	canvas.draw_circle(_p(box, 78.0, 36.0), 11.0 * unit, red)
	canvas.draw_circle(_p(box, 78.0, 36.0), 8.0 * unit, fire)
	canvas.draw_circle(_p(box, 78.0, 36.0), 4.0 * unit, light)
	_fill(
		canvas,
		box,
		[
			Vector2(71.0, 30.0),
			Vector2(69.0, 21.0),
			Vector2(75.0, 26.0),
			Vector2(79.0, 14.0),
			Vector2(84.0, 25.0),
			Vector2(86.0, 31.0),
			Vector2(80.0, 36.0)
		],
		fire
	)
	_fill(
		canvas,
		box,
		[Vector2(77.0, 28.0), Vector2(79.0, 21.0), Vector2(82.0, 28.0), Vector2(80.0, 31.0)],
		light
	)
	canvas.draw_circle(_p(box, 74.0, 80.0), 4.0 * unit, skin)
	canvas.draw_line(_p(box, 72.0, 83.0), _p(box, 78.0, 84.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(20.0, 83.0),
			Vector2(22.0, 74.0),
			Vector2(25.0, 71.0),
			Vector2(27.0, 74.0),
			Vector2(27.0, 80.0),
			Vector2(33.0, 78.0),
			Vector2(35.0, 81.0),
			Vector2(28.0, 87.0)
		],
		skin
	)
	canvas.draw_circle(_p(box, 26.0, 65.0), 5.0 * unit, fire)
	canvas.draw_circle(_p(box, 26.0, 65.0), 2.0 * unit, light)
	canvas.draw_arc(
		_p(box, 26.0, 65.0), 9.0 * unit, PI * 0.1, PI * 1.7, 40, gold, maxf(1.0 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 17.0, 59.0), 1.2 * unit, bone)
	canvas.draw_circle(_p(box, 33.0, 58.0), 1.0 * unit, fire)


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
