extends RefCounted
## Native canvas portrait: Aurelix, The Time Sovereign / Time Mage.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(21, 31, 37)
	var robe := Color8(34, 74, 80)
	var teal := Color8(51, 121, 125)
	var gold := Color8(191, 152, 77)
	var light := Color8(250, 226, 157)
	var bronze := Color8(105, 85, 50)
	var skin := Color8(180, 166, 143)
	var shade := Color8(117, 122, 115)
	var hair := Color8(212, 220, 210)
	var magic := Color8(116, 236, 211)
	_backdrop(canvas, box, Color8(30, 72, 76), Color8(15, 27, 36))

	# A segmented clock halo with offset hands encodes the time-mage identity.
	canvas.draw_arc(
		_p(box, 46.0, 40.0),
		33.0 * unit,
		PI * -0.95,
		PI * 0.25,
		48,
		gold,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 46.0, 40.0),
		37.0 * unit,
		PI * 0.33,
		PI * 0.95,
		48,
		bronze,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 46.0, 40.0),
		29.0 * unit,
		PI * -0.93,
		PI * -0.05,
		48,
		teal,
		maxf(1.0 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 46.0, 7.0), _p(box, 46.0, 12.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 62.0, 12.0), _p(box, 60.0, 16.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 74.0, 24.0), _p(box, 70.0, 26.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 79.0, 40.0), _p(box, 74.0, 40.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 18.0, 24.0), _p(box, 22.0, 26.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 30.0, 12.0), _p(box, 32.0, 16.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 13.0, 40.0), _p(box, 18.0, 40.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 46.0, 40.0), _p(box, 59.0, 19.0), magic, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 46.0, 40.0), _p(box, 25.0, 33.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 96.0),
			Vector2(19.0, 69.0),
			Vector2(31.0, 60.0),
			Vector2(60.0, 60.0),
			Vector2(74.0, 72.0),
			Vector2(83.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 94.0),
			Vector2(23.0, 72.0),
			Vector2(33.0, 64.0),
			Vector2(58.0, 64.0),
			Vector2(70.0, 74.0),
			Vector2(77.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[Vector2(26.0, 72.0), Vector2(39.0, 69.0), Vector2(44.0, 94.0), Vector2(20.0, 94.0)],
		teal
	)
	_fill(
		canvas,
		box,
		[Vector2(56.0, 67.0), Vector2(64.0, 73.0), Vector2(69.0, 94.0), Vector2(52.0, 94.0)],
		bronze
	)

	# High forked collar, silver swept hair and a monocle over one tired eye.
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 50.0),
			Vector2(40.0, 58.0),
			Vector2(48.0, 69.0),
			Vector2(60.0, 59.0),
			Vector2(67.0, 49.0),
			Vector2(65.0, 68.0),
			Vector2(50.0, 80.0),
			Vector2(34.0, 71.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 56.0),
			Vector2(39.0, 62.0),
			Vector2(48.0, 73.0),
			Vector2(61.0, 63.0),
			Vector2(63.0, 56.0),
			Vector2(62.0, 67.0),
			Vector2(50.0, 76.0),
			Vector2(36.0, 68.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 28.0),
			Vector2(38.0, 19.0),
			Vector2(55.0, 20.0),
			Vector2(63.0, 28.0),
			Vector2(62.0, 44.0),
			Vector2(55.0, 56.0),
			Vector2(41.0, 58.0),
			Vector2(32.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 29.0),
			Vector2(39.0, 24.0),
			Vector2(53.0, 24.0),
			Vector2(59.0, 30.0),
			Vector2(58.0, 44.0),
			Vector2(52.0, 52.0),
			Vector2(42.0, 53.0),
			Vector2(36.0, 45.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 26.0),
			Vector2(58.0, 30.0),
			Vector2(59.0, 40.0),
			Vector2(54.0, 48.0),
			Vector2(48.0, 51.0),
			Vector2(50.0, 43.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 33.0),
			Vector2(28.0, 23.0),
			Vector2(34.0, 24.0),
			Vector2(37.0, 14.0),
			Vector2(43.0, 18.0),
			Vector2(50.0, 12.0),
			Vector2(58.0, 18.0),
			Vector2(64.0, 24.0),
			Vector2(65.0, 35.0),
			Vector2(57.0, 29.0),
			Vector2(54.0, 23.0),
			Vector2(47.0, 28.0),
			Vector2(43.0, 24.0),
			Vector2(36.0, 31.0),
			Vector2(35.0, 44.0),
			Vector2(30.0, 42.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 35.0, 24.0), _p(box, 40.0, 20.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 43.0, 17.0), _p(box, 50.0, 16.0), hair, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 35.0), _p(box, 43.0, 36.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 36.0), _p(box, 57.0, 34.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 54.0, 39.0), 5.0 * unit, bronze)
	canvas.draw_circle(_p(box, 54.0, 39.0), 3.5 * unit, magic)
	canvas.draw_line(_p(box, 52.0, 37.0), _p(box, 55.0, 40.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 58.0, 42.0), _p(box, 60.0, 54.0), gold, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 39.0), _p(box, 42.0, 39.0), magic, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 36.0), _p(box, 45.0, 43.0), skin, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 42.0, 48.0), _p(box, 52.0, 47.0), ink, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(40.0, 50.0),
			Vector2(46.0, 53.0),
			Vector2(52.0, 50.0),
			Vector2(50.0, 58.0),
			Vector2(46.0, 62.0),
			Vector2(42.0, 58.0)
		],
		hair
	)

	# An hourglass chest seal and orbiting sand motes replace a martial harness.
	canvas.draw_line(_p(box, 39.0, 77.0), _p(box, 56.0, 77.0), gold, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 92.0), _p(box, 56.0, 92.0), gold, maxf(2.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(41.0, 79.0),
			Vector2(54.0, 79.0),
			Vector2(51.0, 85.0),
			Vector2(54.0, 90.0),
			Vector2(41.0, 90.0),
			Vector2(44.0, 85.0)
		],
		ink
	)
	_fill(canvas, box, [Vector2(44.0, 80.0), Vector2(51.0, 80.0), Vector2(48.0, 84.0)], magic)
	_fill(canvas, box, [Vector2(48.0, 86.0), Vector2(52.0, 90.0), Vector2(44.0, 90.0)], light)
	canvas.draw_line(_p(box, 40.0, 79.0), _p(box, 40.0, 90.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 55.0, 79.0), _p(box, 55.0, 90.0), gold, maxf(1.5 * unit, 1.0), true)

	# Clock-headed staff with eccentric inner rings and a suspended crystal.
	canvas.draw_line(_p(box, 78.0, 56.0), _p(box, 78.0, 94.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 56.0), _p(box, 78.0, 94.0), gold, maxf(2.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 78.0, 48.0), 13.0 * unit, ink)
	canvas.draw_circle(_p(box, 78.0, 48.0), 10.5 * unit, gold)
	canvas.draw_circle(_p(box, 78.0, 48.0), 8.0 * unit, robe)
	canvas.draw_arc(
		_p(box, 78.0, 48.0),
		6.0 * unit,
		PI * -0.85,
		PI * 0.65,
		48,
		magic,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 78.0, 42.0), _p(box, 78.0, 48.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 48.0), _p(box, 83.0, 50.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 78.0, 48.0), 1.5 * unit, magic)
	_fill(
		canvas,
		box,
		[Vector2(78.0, 29.0), Vector2(81.0, 34.0), Vector2(78.0, 38.0), Vector2(75.0, 34.0)],
		gold
	)
	canvas.draw_circle(_p(box, 75.0, 78.0), 4.0 * unit, skin)
	canvas.draw_line(_p(box, 73.0, 81.0), _p(box, 78.0, 81.0), bronze, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 16.0, 51.0), 1.2 * unit, magic)
	canvas.draw_circle(_p(box, 21.0, 58.0), 1.2 * unit, magic)
	canvas.draw_circle(_p(box, 13.0, 65.0), 1.2 * unit, magic)


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
