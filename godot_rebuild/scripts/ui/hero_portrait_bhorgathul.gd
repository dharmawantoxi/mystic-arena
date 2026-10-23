extends RefCounted
## Native canvas portrait: Bhor'gathul, The Earth Render.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(36, 29, 23)
	var rock := Color8(114, 93, 67)
	var shade := Color8(71, 60, 46)
	var light := Color8(177, 153, 106)
	var earth := Color8(139, 104, 57)
	var skin := Color8(139, 124, 87)
	var dark := Color8(91, 83, 57)
	var crystal := Color8(230, 180, 66)
	var glow := Color8(255, 225, 127)
	var moss := Color8(83, 105, 57)
	_backdrop(canvas, box, Color8(84, 69, 43), Color8(30, 30, 24))

	# Suspended fractured slabs surround a broad earth-shaping giant.
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 22.0),
			Vector2(18.0, 17.0),
			Vector2(22.0, 26.0),
			Vector2(15.0, 34.0),
			Vector2(8.0, 30.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 14.0),
			Vector2(87.0, 20.0),
			Vector2(85.0, 31.0),
			Vector2(76.0, 29.0),
			Vector2(72.0, 22.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(6.0, 48.0), Vector2(12.0, 41.0), Vector2(19.0, 45.0), Vector2(16.0, 55.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(81.0, 45.0), Vector2(90.0, 42.0), Vector2(88.0, 54.0), Vector2(82.0, 57.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 23.0),
			Vector2(17.0, 21.0),
			Vector2(19.0, 26.0),
			Vector2(14.0, 30.0),
			Vector2(11.0, 28.0)
		],
		rock
	)
	_fill(
		canvas,
		box,
		[Vector2(78.0, 19.0), Vector2(84.0, 22.0), Vector2(82.0, 28.0), Vector2(77.0, 26.0)],
		earth
	)
	canvas.draw_line(_p(box, 12.0, 25.0), _p(box, 16.0, 26.0), crystal, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 77.0, 23.0), _p(box, 81.0, 24.0), light, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(4.0, 96.0),
			Vector2(10.0, 65.0),
			Vector2(27.0, 53.0),
			Vector2(63.0, 53.0),
			Vector2(84.0, 65.0),
			Vector2(92.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 94.0),
			Vector2(15.0, 68.0),
			Vector2(29.0, 58.0),
			Vector2(62.0, 58.0),
			Vector2(79.0, 68.0),
			Vector2(86.0, 94.0)
		],
		shade
	)

	# Cragged shoulders and an earthy hide carry irregular mineral seams.
	_fill(
		canvas,
		box,
		[
			Vector2(7.0, 66.0),
			Vector2(15.0, 50.0),
			Vector2(29.0, 45.0),
			Vector2(38.0, 61.0),
			Vector2(34.0, 77.0),
			Vector2(16.0, 82.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 66.0),
			Vector2(19.0, 54.0),
			Vector2(27.0, 51.0),
			Vector2(33.0, 62.0),
			Vector2(29.0, 73.0),
			Vector2(18.0, 77.0)
		],
		rock
	)
	_fill(
		canvas,
		box,
		[
			Vector2(19.0, 55.0),
			Vector2(25.0, 53.0),
			Vector2(29.0, 59.0),
			Vector2(23.0, 62.0),
			Vector2(15.0, 65.0)
		],
		light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 61.0),
			Vector2(66.0, 45.0),
			Vector2(80.0, 51.0),
			Vector2(89.0, 65.0),
			Vector2(81.0, 82.0),
			Vector2(62.0, 77.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(63.0, 62.0),
			Vector2(69.0, 51.0),
			Vector2(77.0, 55.0),
			Vector2(84.0, 66.0),
			Vector2(78.0, 77.0),
			Vector2(67.0, 73.0)
		],
		rock
	)
	_fill(
		canvas,
		box,
		[Vector2(69.0, 53.0), Vector2(76.0, 57.0), Vector2(80.0, 64.0), Vector2(71.0, 61.0)],
		earth
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 66.0),
			Vector2(38.0, 56.0),
			Vector2(56.0, 57.0),
			Vector2(66.0, 68.0),
			Vector2(70.0, 96.0),
			Vector2(25.0, 96.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(49.0, 61.0),
			Vector2(57.0, 61.0),
			Vector2(63.0, 69.0),
			Vector2(66.0, 94.0),
			Vector2(50.0, 94.0)
		],
		dark
	)
	canvas.draw_line(_p(box, 32.0, 72.0), _p(box, 42.0, 76.0), earth, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 76.0), _p(box, 61.0, 71.0), earth, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(39.0, 76.0),
			Vector2(48.0, 71.0),
			Vector2(57.0, 78.0),
			Vector2(54.0, 88.0),
			Vector2(43.0, 90.0),
			Vector2(36.0, 84.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(42.0, 78.0),
			Vector2(48.0, 75.0),
			Vector2(53.0, 79.0),
			Vector2(51.0, 85.0),
			Vector2(44.0, 86.0),
			Vector2(40.0, 83.0)
		],
		rock
	)
	canvas.draw_line(_p(box, 47.0, 77.0), _p(box, 45.0, 81.0), glow, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 45.0, 81.0), _p(box, 49.0, 85.0), crystal, maxf(1.5 * unit, 1.0), true)

	# Stone brow, blunt tusks and thick braided side locks form an exposed face.
	_fill(
		canvas,
		box,
		[
			Vector2(25.0, 30.0),
			Vector2(33.0, 19.0),
			Vector2(57.0, 18.0),
			Vector2(68.0, 30.0),
			Vector2(65.0, 47.0),
			Vector2(56.0, 59.0),
			Vector2(39.0, 60.0),
			Vector2(28.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 31.0),
			Vector2(37.0, 24.0),
			Vector2(55.0, 23.0),
			Vector2(62.0, 32.0),
			Vector2(59.0, 45.0),
			Vector2(53.0, 54.0),
			Vector2(41.0, 55.0),
			Vector2(34.0, 46.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 25.0),
			Vector2(57.0, 26.0),
			Vector2(62.0, 32.0),
			Vector2(58.0, 46.0),
			Vector2(53.0, 53.0),
			Vector2(49.0, 48.0)
		],
		dark
	)
	_fill(
		canvas,
		box,
		[
			Vector2(25.0, 30.0),
			Vector2(28.0, 19.0),
			Vector2(36.0, 21.0),
			Vector2(42.0, 12.0),
			Vector2(48.0, 19.0),
			Vector2(57.0, 13.0),
			Vector2(62.0, 23.0),
			Vector2(68.0, 22.0),
			Vector2(67.0, 33.0),
			Vector2(55.0, 29.0),
			Vector2(39.0, 31.0)
		],
		rock
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 26.0),
			Vector2(36.0, 25.0),
			Vector2(42.0, 18.0),
			Vector2(46.0, 23.0),
			Vector2(42.0, 27.0)
		],
		light
	)
	_fill(
		canvas,
		box,
		[Vector2(51.0, 23.0), Vector2(57.0, 19.0), Vector2(60.0, 26.0), Vector2(56.0, 27.0)],
		earth
	)
	canvas.draw_line(_p(box, 34.0, 35.0), _p(box, 42.0, 37.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 37.0), _p(box, 59.0, 34.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 36.0, 39.0), _p(box, 41.0, 39.0), glow, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 39.0), _p(box, 57.0, 38.0), glow, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(43.0, 37.0),
			Vector2(49.0, 37.0),
			Vector2(52.0, 45.0),
			Vector2(46.0, 48.0),
			Vector2(40.0, 45.0)
		],
		dark
	)
	canvas.draw_line(_p(box, 40.0, 50.0), _p(box, 54.0, 49.0), ink, maxf(2.0 * unit, 1.0), true)
	_fill(canvas, box, [Vector2(37.0, 48.0), Vector2(39.0, 42.0), Vector2(43.0, 50.0)], light)
	_fill(canvas, box, [Vector2(52.0, 50.0), Vector2(57.0, 42.0), Vector2(57.0, 48.0)], light)
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 35.0),
			Vector2(32.0, 36.0),
			Vector2(34.0, 51.0),
			Vector2(32.0, 61.0),
			Vector2(26.0, 56.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 35.0),
			Vector2(67.0, 34.0),
			Vector2(69.0, 56.0),
			Vector2(63.0, 61.0),
			Vector2(60.0, 51.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 27.0, 44.0), _p(box, 32.0, 45.0), earth, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 28.0, 50.0), _p(box, 33.0, 51.0), earth, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 62.0, 44.0), _p(box, 67.0, 43.0), earth, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 62.0, 51.0), _p(box, 68.0, 50.0), earth, maxf(2.0 * unit, 1.0), true)

	# Oversized rock gauntlets channel earth magic, with no melee weapon prop.
	_fill(
		canvas,
		box,
		[
			Vector2(6.0, 81.0),
			Vector2(17.0, 75.0),
			Vector2(30.0, 80.0),
			Vector2(34.0, 91.0),
			Vector2(27.0, 96.0),
			Vector2(6.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 84.0),
			Vector2(18.0, 80.0),
			Vector2(26.0, 83.0),
			Vector2(29.0, 90.0),
			Vector2(25.0, 93.0),
			Vector2(11.0, 93.0)
		],
		rock
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 84.0),
			Vector2(18.0, 82.0),
			Vector2(23.0, 85.0),
			Vector2(19.0, 88.0),
			Vector2(12.0, 89.0)
		],
		light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(66.0, 81.0),
			Vector2(78.0, 75.0),
			Vector2(90.0, 81.0),
			Vector2(91.0, 96.0),
			Vector2(68.0, 96.0),
			Vector2(61.0, 91.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 85.0),
			Vector2(78.0, 80.0),
			Vector2(86.0, 84.0),
			Vector2(87.0, 93.0),
			Vector2(70.0, 93.0),
			Vector2(66.0, 90.0)
		],
		rock
	)
	canvas.draw_line(_p(box, 16.0, 86.0), _p(box, 20.0, 90.0), crystal, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 20.0, 90.0), _p(box, 25.0, 89.0), glow, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 74.0, 84.0), _p(box, 77.0, 89.0), crystal, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 77.0, 89.0), _p(box, 83.0, 88.0), glow, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 18.0, 70.0), _p(box, 24.0, 69.0), moss, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 70.0, 66.0), _p(box, 77.0, 68.0), moss, maxf(2.0 * unit, 1.0), true)


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
