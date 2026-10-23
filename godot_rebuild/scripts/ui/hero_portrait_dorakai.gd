extends RefCounted
## Native canvas portrait: Dorakai, The Blood-Drum Oni / Area Demon.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(39, 23, 34)
	var skin := Color8(175, 56, 66)
	var shade := Color8(108, 35, 53)
	var red := Color8(220, 85, 76)
	var hair := Color8(47, 28, 45)
	var horn := Color8(218, 189, 141)
	var light := Color8(248, 224, 178)
	var gold := Color8(192, 145, 65)
	var wood := Color8(112, 53, 41)
	var hide := Color8(194, 149, 104)
	var rope := Color8(227, 188, 133)
	var cloth := Color8(63, 43, 72)
	_backdrop(canvas, box, Color8(99, 37, 57), Color8(34, 23, 42))

	# Paired taiko drums and concentric sound arcs establish the area demon.
	canvas.draw_arc(
		_p(box, 20.0, 40.0), 18.0 * unit, PI * -0.9, PI * -0.1, 40, red, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 20.0, 40.0),
		22.0 * unit,
		PI * -0.85,
		PI * -0.15,
		40,
		shade,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 77.0, 40.0), 17.0 * unit, PI * -0.9, PI * -0.1, 40, red, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 19.0, 43.0), 16.0 * unit, ink)
	canvas.draw_circle(_p(box, 19.0, 43.0), 13.0 * unit, wood)
	canvas.draw_circle(_p(box, 19.0, 41.0), 12.0 * unit, gold)
	canvas.draw_circle(_p(box, 19.0, 41.0), 10.0 * unit, hide)
	canvas.draw_arc(
		_p(box, 19.0, 41.0), 5.0 * unit, PI * 0.2, PI * 1.7, 40, shade, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 21.0, 39.0), 2.0 * unit, red)
	canvas.draw_circle(_p(box, 11.0, 36.0), 1.0 * unit, rope)
	canvas.draw_circle(_p(box, 19.0, 32.0), 1.0 * unit, rope)
	canvas.draw_circle(_p(box, 27.0, 36.0), 1.0 * unit, rope)
	canvas.draw_circle(_p(box, 27.0, 46.0), 1.0 * unit, rope)
	canvas.draw_circle(_p(box, 19.0, 50.0), 1.0 * unit, rope)
	canvas.draw_circle(_p(box, 11.0, 46.0), 1.0 * unit, rope)
	canvas.draw_circle(_p(box, 77.0, 43.0), 16.0 * unit, ink)
	canvas.draw_circle(_p(box, 77.0, 43.0), 13.0 * unit, wood)
	canvas.draw_circle(_p(box, 77.0, 41.0), 12.0 * unit, gold)
	canvas.draw_circle(_p(box, 77.0, 41.0), 10.0 * unit, hide)
	canvas.draw_arc(
		_p(box, 77.0, 41.0), 5.0 * unit, PI * 0.2, PI * 1.7, 40, shade, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 79.0, 39.0), 2.0 * unit, red)
	canvas.draw_circle(_p(box, 69.0, 36.0), 1.0 * unit, rope)
	canvas.draw_circle(_p(box, 77.0, 32.0), 1.0 * unit, rope)
	canvas.draw_circle(_p(box, 85.0, 36.0), 1.0 * unit, rope)
	canvas.draw_circle(_p(box, 85.0, 46.0), 1.0 * unit, rope)
	canvas.draw_circle(_p(box, 77.0, 50.0), 1.0 * unit, rope)
	canvas.draw_circle(_p(box, 69.0, 46.0), 1.0 * unit, rope)
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 96.0),
			Vector2(16.0, 70.0),
			Vector2(32.0, 58.0),
			Vector2(61.0, 58.0),
			Vector2(79.0, 71.0),
			Vector2(88.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 94.0),
			Vector2(21.0, 73.0),
			Vector2(34.0, 62.0),
			Vector2(59.0, 62.0),
			Vector2(74.0, 74.0),
			Vector2(82.0, 94.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 63.0),
			Vector2(61.0, 65.0),
			Vector2(74.0, 76.0),
			Vector2(79.0, 94.0),
			Vector2(51.0, 94.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 78.0),
			Vector2(42.0, 83.0),
			Vector2(60.0, 77.0),
			Vector2(66.0, 94.0),
			Vector2(23.0, 94.0)
		],
		cloth
	)
	canvas.draw_line(_p(box, 31.0, 83.0), _p(box, 59.0, 83.0), gold, maxf(2.0 * unit, 1.0), true)

	# An unruly black mane surrounds an open crimson face and curved ivory horns.
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 46.0),
			Vector2(22.0, 27.0),
			Vector2(28.0, 29.0),
			Vector2(28.0, 17.0),
			Vector2(38.0, 21.0),
			Vector2(43.0, 13.0),
			Vector2(50.0, 18.0),
			Vector2(58.0, 13.0),
			Vector2(63.0, 24.0),
			Vector2(71.0, 22.0),
			Vector2(69.0, 44.0),
			Vector2(73.0, 56.0),
			Vector2(62.0, 60.0),
			Vector2(32.0, 61.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 44.0),
			Vector2(27.0, 33.0),
			Vector2(32.0, 34.0),
			Vector2(32.0, 24.0),
			Vector2(40.0, 26.0),
			Vector2(44.0, 19.0),
			Vector2(50.0, 23.0),
			Vector2(57.0, 20.0),
			Vector2(60.0, 28.0),
			Vector2(65.0, 27.0),
			Vector2(65.0, 43.0),
			Vector2(68.0, 53.0),
			Vector2(60.0, 55.0),
			Vector2(35.0, 55.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 29.0),
			Vector2(19.0, 23.0),
			Vector2(18.0, 10.0),
			Vector2(25.0, 15.0),
			Vector2(29.0, 24.0),
			Vector2(36.0, 27.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 28.0),
			Vector2(23.0, 22.0),
			Vector2(21.0, 15.0),
			Vector2(24.0, 18.0),
			Vector2(27.0, 25.0),
			Vector2(33.0, 28.0)
		],
		horn
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 27.0),
			Vector2(65.0, 24.0),
			Vector2(70.0, 14.0),
			Vector2(78.0, 9.0),
			Vector2(76.0, 24.0),
			Vector2(67.0, 31.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 28.0),
			Vector2(68.0, 25.0),
			Vector2(73.0, 16.0),
			Vector2(72.0, 23.0),
			Vector2(66.0, 29.0)
		],
		horn
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 32.0),
			Vector2(37.0, 24.0),
			Vector2(55.0, 24.0),
			Vector2(64.0, 33.0),
			Vector2(62.0, 47.0),
			Vector2(55.0, 58.0),
			Vector2(41.0, 59.0),
			Vector2(32.0, 49.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 33.0),
			Vector2(40.0, 28.0),
			Vector2(53.0, 28.0),
			Vector2(59.0, 34.0),
			Vector2(58.0, 46.0),
			Vector2(52.0, 54.0),
			Vector2(42.0, 54.0),
			Vector2(37.0, 46.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 30.0),
			Vector2(57.0, 34.0),
			Vector2(58.0, 44.0),
			Vector2(52.0, 52.0),
			Vector2(48.0, 49.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[Vector2(37.0, 34.0), Vector2(42.0, 31.0), Vector2(45.0, 35.0), Vector2(40.0, 38.0)],
		red
	)
	_fill(
		canvas,
		box,
		[Vector2(50.0, 35.0), Vector2(54.0, 31.0), Vector2(57.0, 34.0), Vector2(54.0, 38.0)],
		red
	)
	canvas.draw_line(_p(box, 36.0, 37.0), _p(box, 43.0, 39.0), ink, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 39.0), _p(box, 58.0, 36.0), ink, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 41.0), _p(box, 42.0, 41.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 41.0), _p(box, 56.0, 40.0), light, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(45.0, 38.0),
			Vector2(49.0, 38.0),
			Vector2(52.0, 45.0),
			Vector2(46.0, 47.0),
			Vector2(41.0, 45.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 39.0, 50.0), _p(box, 55.0, 49.0), ink, maxf(2.0 * unit, 1.0), true)
	_fill(canvas, box, [Vector2(39.0, 48.0), Vector2(40.0, 43.0), Vector2(44.0, 50.0)], horn)
	_fill(canvas, box, [Vector2(51.0, 50.0), Vector2(56.0, 43.0), Vector2(55.0, 49.0)], horn)
	canvas.draw_line(_p(box, 44.0, 53.0), _p(box, 51.0, 53.0), red, maxf(1.0 * unit, 1.0), true)

	# A rope necklace and a belly drum sit between two raised beaters.
	canvas.draw_arc(
		_p(box, 47.0, 58.0),
		13.0 * unit,
		PI * 0.03,
		PI * 0.97,
		40,
		rope,
		maxf(3.0 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 35.0, 61.0), 2.0 * unit, gold)
	canvas.draw_circle(_p(box, 40.0, 67.0), 2.0 * unit, gold)
	canvas.draw_circle(_p(box, 47.0, 70.0), 2.0 * unit, gold)
	canvas.draw_circle(_p(box, 54.0, 67.0), 2.0 * unit, gold)
	canvas.draw_circle(_p(box, 59.0, 61.0), 2.0 * unit, gold)
	canvas.draw_circle(_p(box, 47.0, 86.0), 16.0 * unit, ink)
	canvas.draw_circle(_p(box, 47.0, 86.0), 13.0 * unit, wood)
	canvas.draw_circle(_p(box, 47.0, 84.0), 12.0 * unit, gold)
	canvas.draw_circle(_p(box, 47.0, 84.0), 10.0 * unit, hide)
	canvas.draw_arc(
		_p(box, 47.0, 84.0),
		6.0 * unit,
		PI * -0.2,
		PI * 1.35,
		40,
		shade,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 49.0, 82.0), 2.5 * unit, red)
	canvas.draw_line(_p(box, 20.0, 81.0), _p(box, 12.0, 61.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 20.0, 81.0), _p(box, 12.0, 61.0), rope, maxf(2.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 12.0, 60.0), 3.0 * unit, horn)
	canvas.draw_line(_p(box, 75.0, 81.0), _p(box, 85.0, 60.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 75.0, 81.0), _p(box, 85.0, 60.0), rope, maxf(2.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 85.0, 59.0), 3.0 * unit, horn)
	canvas.draw_circle(_p(box, 20.0, 80.0), 5.0 * unit, skin)
	canvas.draw_circle(_p(box, 75.0, 80.0), 5.0 * unit, skin)
	canvas.draw_line(_p(box, 17.0, 84.0), _p(box, 23.0, 84.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 72.0, 84.0), _p(box, 78.0, 84.0), gold, maxf(2.0 * unit, 1.0), true)


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
