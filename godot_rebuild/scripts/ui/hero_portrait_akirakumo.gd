extends RefCounted
## Native canvas portrait: Akirakumo, The Moonfang Prince / Moon Demon Prince.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(14, 20, 39)
	var robe := Color8(35, 41, 77)
	var purple := Color8(74, 65, 122)
	var silver := Color8(175, 192, 222)
	var moon := Color8(229, 240, 251)
	var skin := Color8(159, 174, 205)
	var hair := Color8(217, 225, 239)
	var shade := Color8(95, 113, 152)
	var blue := Color8(101, 179, 231)
	var gold := Color8(201, 177, 130)
	_backdrop(canvas, box, Color8(39, 48, 94), Color8(12, 18, 38))

	# A crescent moon and silver points crown an angular demon-prince silhouette.
	canvas.draw_arc(
		_p(box, 48.0, 36.0),
		31.0 * unit,
		PI * -0.94,
		PI * -0.06,
		32,
		blue,
		maxf(3.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 36.0),
		34.0 * unit,
		PI * -0.8,
		PI * -0.2,
		32,
		moon,
		maxf(1.3 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 9.0, 24.0), _p(box, 13.0, 24.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 11.0, 22.0), _p(box, 11.0, 26.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 80.0, 38.0), _p(box, 84.0, 38.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 82.0, 36.0), _p(box, 82.0, 40.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 18.0, 49.0), _p(box, 22.0, 49.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 20.0, 47.0), _p(box, 20.0, 51.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 71.0, 12.0), _p(box, 75.0, 12.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 73.0, 10.0), _p(box, 73.0, 14.0), silver, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 96.0),
			Vector2(17.0, 66.0),
			Vector2(30.0, 53.0),
			Vector2(65.0, 53.0),
			Vector2(80.0, 65.0),
			Vector2(87.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 94.0),
			Vector2(21.0, 68.0),
			Vector2(33.0, 58.0),
			Vector2(62.0, 58.0),
			Vector2(76.0, 68.0),
			Vector2(82.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(22.0, 72.0),
			Vector2(35.0, 64.0),
			Vector2(48.0, 72.0),
			Vector2(61.0, 64.0),
			Vector2(74.0, 72.0),
			Vector2(67.0, 94.0),
			Vector2(29.0, 94.0)
		],
		purple
	)

	# Layered shoulder armour flares like folded lunar wings.
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 61.0),
			Vector2(24.0, 50.0),
			Vector2(37.0, 59.0),
			Vector2(40.0, 74.0),
			Vector2(26.0, 81.0),
			Vector2(14.0, 73.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(19.0, 62.0),
			Vector2(25.0, 55.0),
			Vector2(33.0, 61.0),
			Vector2(35.0, 70.0),
			Vector2(26.0, 76.0),
			Vector2(18.0, 71.0)
		],
		silver
	)
	_fill(
		canvas,
		box,
		[
			Vector2(81.0, 61.0),
			Vector2(72.0, 50.0),
			Vector2(59.0, 59.0),
			Vector2(56.0, 74.0),
			Vector2(70.0, 81.0),
			Vector2(82.0, 73.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 62.0),
			Vector2(71.0, 55.0),
			Vector2(63.0, 61.0),
			Vector2(61.0, 70.0),
			Vector2(70.0, 76.0),
			Vector2(78.0, 71.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 21.0, 63.0), _p(box, 30.0, 66.0), moon, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 75.0, 63.0), _p(box, 66.0, 66.0), silver, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 28.0),
			Vector2(36.0, 17.0),
			Vector2(50.0, 13.0),
			Vector2(63.0, 19.0),
			Vector2(68.0, 31.0),
			Vector2(66.0, 55.0),
			Vector2(58.0, 64.0),
			Vector2(35.0, 62.0),
			Vector2(27.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 29.0),
			Vector2(39.0, 20.0),
			Vector2(50.0, 17.0),
			Vector2(60.0, 22.0),
			Vector2(64.0, 32.0),
			Vector2(62.0, 52.0),
			Vector2(57.0, 58.0),
			Vector2(38.0, 57.0),
			Vector2(31.0, 47.0)
		],
		hair
	)

	# Tapered ears, pale face and paired fangs below the moon-blue eyes.
	_fill(
		canvas,
		box,
		[Vector2(33.0, 33.0), Vector2(20.0, 26.0), Vector2(26.0, 42.0), Vector2(36.0, 47.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(32.0, 35.0), Vector2(24.0, 30.0), Vector2(28.0, 40.0), Vector2(35.0, 43.0)],
		skin
	)
	_fill(
		canvas,
		box,
		[Vector2(62.0, 33.0), Vector2(76.0, 26.0), Vector2(70.0, 42.0), Vector2(60.0, 47.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(63.0, 35.0), Vector2(72.0, 30.0), Vector2(68.0, 40.0), Vector2(61.0, 43.0)],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 27.0),
			Vector2(44.0, 22.0),
			Vector2(56.0, 24.0),
			Vector2(62.0, 32.0),
			Vector2(59.0, 46.0),
			Vector2(49.0, 56.0),
			Vector2(39.0, 50.0),
			Vector2(33.0, 40.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 29.0),
			Vector2(45.0, 25.0),
			Vector2(54.0, 27.0),
			Vector2(59.0, 33.0),
			Vector2(56.0, 44.0),
			Vector2(49.0, 52.0),
			Vector2(41.0, 47.0),
			Vector2(36.0, 39.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 28.0),
			Vector2(56.0, 30.0),
			Vector2(59.0, 34.0),
			Vector2(55.0, 44.0),
			Vector2(49.0, 50.0),
			Vector2(47.0, 45.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 30.0),
			Vector2(35.0, 20.0),
			Vector2(47.0, 15.0),
			Vector2(60.0, 21.0),
			Vector2(65.0, 31.0),
			Vector2(58.0, 29.0),
			Vector2(51.0, 23.0),
			Vector2(46.0, 35.0),
			Vector2(43.0, 27.0),
			Vector2(37.0, 37.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 38.0, 36.0), _p(box, 44.0, 38.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 38.0), _p(box, 57.0, 35.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 39.0), _p(box, 44.0, 39.0), blue, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 39.0), _p(box, 57.0, 38.0), blue, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 37.0), _p(box, 45.0, 43.0), moon, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 42.0, 46.0), _p(box, 53.0, 46.0), ink, maxf(2.0 * unit, 1.0), true)
	_fill(canvas, box, [Vector2(42.0, 46.0), Vector2(45.0, 46.0), Vector2(44.0, 50.0)], moon)
	_fill(canvas, box, [Vector2(50.0, 46.0), Vector2(53.0, 46.0), Vector2(51.0, 50.0)], moon)

	# Forked silver horns and a crescent brow jewel show princely rank.
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 27.0),
			Vector2(25.0, 16.0),
			Vector2(27.0, 5.0),
			Vector2(31.0, 13.0),
			Vector2(37.0, 19.0),
			Vector2(42.0, 22.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 24.0),
			Vector2(28.0, 15.0),
			Vector2(28.0, 10.0),
			Vector2(31.0, 16.0),
			Vector2(38.0, 22.0)
		],
		silver
	)
	_fill(
		canvas,
		box,
		[
			Vector2(54.0, 22.0),
			Vector2(61.0, 16.0),
			Vector2(67.0, 5.0),
			Vector2(70.0, 15.0),
			Vector2(64.0, 27.0),
			Vector2(59.0, 29.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(59.0, 24.0),
			Vector2(64.0, 16.0),
			Vector2(67.0, 10.0),
			Vector2(67.0, 16.0),
			Vector2(62.0, 25.0)
		],
		silver
	)
	canvas.draw_line(_p(box, 36.0, 29.0), _p(box, 58.0, 29.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_arc(
		_p(box, 48.0, 29.0), 3.0 * unit, PI * 0.0, PI * 1.5, 32, moon, maxf(1.5 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 51.0),
			Vector2(48.0, 59.0),
			Vector2(64.0, 50.0),
			Vector2(61.0, 64.0),
			Vector2(48.0, 71.0),
			Vector2(35.0, 64.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 56.0),
			Vector2(48.0, 63.0),
			Vector2(60.0, 55.0),
			Vector2(58.0, 62.0),
			Vector2(48.0, 67.0),
			Vector2(38.0, 62.0)
		],
		silver
	)
	_fill(
		canvas,
		box,
		[
			Vector2(45.0, 70.0),
			Vector2(51.0, 70.0),
			Vector2(55.0, 78.0),
			Vector2(48.0, 84.0),
			Vector2(41.0, 78.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(47.0, 72.0),
			Vector2(50.0, 73.0),
			Vector2(52.0, 78.0),
			Vector2(48.0, 81.0),
			Vector2(44.0, 78.0)
		],
		blue
	)
	canvas.draw_line(_p(box, 48.0, 84.0), _p(box, 48.0, 94.0), gold, maxf(2.0 * unit, 1.0), true)

	# A curved moon blade crosses the lower frame, with a dark wrapped grip.
	_fill(
		canvas,
		box,
		[
			Vector2(16.0, 92.0),
			Vector2(30.0, 86.0),
			Vector2(51.0, 76.0),
			Vector2(72.0, 60.0),
			Vector2(86.0, 43.0),
			Vector2(81.0, 62.0),
			Vector2(62.0, 80.0),
			Vector2(40.0, 92.0),
			Vector2(25.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 91.0),
			Vector2(51.0, 79.0),
			Vector2(73.0, 63.0),
			Vector2(82.0, 51.0),
			Vector2(78.0, 62.0),
			Vector2(60.0, 78.0),
			Vector2(38.0, 90.0),
			Vector2(26.0, 94.0)
		],
		silver
	)
	canvas.draw_line(_p(box, 36.0, 90.0), _p(box, 60.0, 79.0), moon, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 25.0, 85.0), _p(box, 32.0, 96.0), gold, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 14.0, 95.0), _p(box, 25.0, 90.0), ink, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 15.0, 94.0), _p(box, 24.0, 90.0), purple, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 14.0, 94.0), 2.0 * unit, gold)


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
