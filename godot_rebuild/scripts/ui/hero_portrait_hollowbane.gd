extends RefCounted
## Native canvas portrait: Kurosaki Hollowbane, The Substitute Shinigami.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(23, 26, 38)
	var robe := Color8(41, 44, 58)
	var shade := Color8(28, 33, 49)
	var light := Color8(234, 231, 212)
	var skin := Color8(209, 168, 137)
	var face_shade := Color8(152, 112, 105)
	var hair := Color8(222, 125, 48)
	var gold := Color8(253, 178, 66)
	var steel := Color8(163, 185, 196)
	var red := Color8(165, 48, 54)
	var spirit := Color8(101, 191, 221)
	_backdrop(canvas, box, Color8(43, 67, 91), Color8(17, 23, 38))

	# Blue spirit arcs and a broad dark sword frame a substitute soul reaper.
	canvas.draw_arc(
		_p(box, 45.0, 41.0),
		35.0 * unit,
		PI * -0.95,
		PI * -0.18,
		40,
		spirit,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 46.0, 45.0),
		39.0 * unit,
		PI * 0.06,
		PI * 0.6,
		40,
		steel,
		maxf(1.0 * unit, 1.0),
		true
	)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 11.0),
			Vector2(78.0, 7.0),
			Vector2(84.0, 15.0),
			Vector2(78.0, 67.0),
			Vector2(66.0, 68.0),
			Vector2(63.0, 61.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(70.0, 16.0),
			Vector2(76.0, 12.0),
			Vector2(79.0, 17.0),
			Vector2(75.0, 61.0),
			Vector2(69.0, 63.0),
			Vector2(67.0, 58.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(76.0, 12.0),
			Vector2(79.0, 17.0),
			Vector2(75.0, 61.0),
			Vector2(72.0, 64.0),
			Vector2(74.0, 19.0)
		],
		steel
	)

	# A black wrap robe, white crossed collar and a diagonal fabric harness.
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 96.0),
			Vector2(19.0, 69.0),
			Vector2(32.0, 56.0),
			Vector2(59.0, 56.0),
			Vector2(76.0, 70.0),
			Vector2(86.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(16.0, 94.0),
			Vector2(25.0, 72.0),
			Vector2(34.0, 61.0),
			Vector2(57.0, 61.0),
			Vector2(70.0, 73.0),
			Vector2(80.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 63.0),
			Vector2(58.0, 65.0),
			Vector2(69.0, 76.0),
			Vector2(77.0, 94.0),
			Vector2(51.0, 94.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 34.0, 61.0), _p(box, 53.0, 81.0), light, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 59.0, 61.0), _p(box, 44.0, 79.0), light, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 62.0), _p(box, 52.0, 78.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 56.0, 63.0), _p(box, 46.0, 77.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 28.0, 69.0), _p(box, 61.0, 94.0), steel, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 28.0, 69.0), _p(box, 61.0, 94.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 30.0, 90.0), _p(box, 63.0, 90.0), light, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 45.0, 90.0), _p(box, 51.0, 90.0), ink, maxf(2.0 * unit, 1.0), true)

	# Spiky orange hair leaves a severe face and a broken ivory half-mask exposed.
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 29.0),
			Vector2(36.0, 19.0),
			Vector2(55.0, 19.0),
			Vector2(65.0, 29.0),
			Vector2(63.0, 45.0),
			Vector2(55.0, 58.0),
			Vector2(41.0, 59.0),
			Vector2(31.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 31.0),
			Vector2(39.0, 24.0),
			Vector2(53.0, 24.0),
			Vector2(59.0, 31.0),
			Vector2(58.0, 44.0),
			Vector2(52.0, 54.0),
			Vector2(42.0, 54.0),
			Vector2(36.0, 46.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 26.0),
			Vector2(58.0, 31.0),
			Vector2(58.0, 43.0),
			Vector2(52.0, 52.0),
			Vector2(48.0, 49.0),
			Vector2(50.0, 41.0)
		],
		face_shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 35.0),
			Vector2(25.0, 25.0),
			Vector2(31.0, 26.0),
			Vector2(31.0, 17.0),
			Vector2(39.0, 21.0),
			Vector2(41.0, 11.0),
			Vector2(47.0, 18.0),
			Vector2(54.0, 11.0),
			Vector2(58.0, 20.0),
			Vector2(66.0, 18.0),
			Vector2(64.0, 28.0),
			Vector2(69.0, 32.0),
			Vector2(61.0, 38.0),
			Vector2(56.0, 29.0),
			Vector2(50.0, 34.0),
			Vector2(46.0, 27.0),
			Vector2(40.0, 34.0),
			Vector2(37.0, 29.0),
			Vector2(32.0, 41.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 28.0),
			Vector2(35.0, 22.0),
			Vector2(40.0, 25.0),
			Vector2(42.0, 18.0),
			Vector2(46.0, 23.0),
			Vector2(43.0, 28.0),
			Vector2(38.0, 26.0)
		],
		gold
	)
	canvas.draw_line(_p(box, 37.0, 36.0), _p(box, 43.0, 37.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 37.0), _p(box, 57.0, 35.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 40.0), _p(box, 42.0, 40.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 40.0), _p(box, 56.0, 39.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 38.0), _p(box, 45.0, 44.0), skin, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 43.0, 50.0), _p(box, 51.0, 49.0), ink, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(56.0, 28.0),
			Vector2(64.0, 31.0),
			Vector2(66.0, 43.0),
			Vector2(61.0, 54.0),
			Vector2(54.0, 56.0),
			Vector2(52.0, 49.0),
			Vector2(56.0, 42.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 31.0),
			Vector2(62.0, 33.0),
			Vector2(63.0, 43.0),
			Vector2(59.0, 50.0),
			Vector2(55.0, 52.0),
			Vector2(55.0, 49.0),
			Vector2(58.0, 41.0)
		],
		light
	)
	_fill(
		canvas,
		box,
		[Vector2(57.0, 36.0), Vector2(63.0, 36.0), Vector2(62.0, 42.0), Vector2(57.0, 43.0)],
		ink
	)
	canvas.draw_line(_p(box, 58.0, 39.0), _p(box, 61.0, 38.0), red, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 60.0, 32.0), _p(box, 60.0, 35.0), red, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 58.0, 44.0), _p(box, 57.0, 48.0), red, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 57.0, 49.0), _p(box, 60.0, 47.0), ink, maxf(1.0 * unit, 1.0), true)

	# Frayed white grip bindings and a loose cloth tail emphasize the oversized blade.
	_fill(
		canvas,
		box,
		[Vector2(64.0, 65.0), Vector2(80.0, 64.0), Vector2(83.0, 70.0), Vector2(68.0, 74.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(68.0, 67.0), Vector2(78.0, 67.0), Vector2(79.0, 69.0), Vector2(69.0, 71.0)],
		steel
	)
	canvas.draw_line(_p(box, 72.0, 74.0), _p(box, 69.0, 93.0), ink, maxf(7.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 72.0, 75.0), _p(box, 69.0, 92.0), light, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 69.0, 78.0), _p(box, 73.0, 79.0), shade, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 69.0, 84.0), _p(box, 73.0, 85.0), shade, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 69.0, 90.0), _p(box, 73.0, 91.0), shade, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 91.0),
			Vector2(72.0, 92.0),
			Vector2(76.0, 86.0),
			Vector2(81.0, 85.0),
			Vector2(78.0, 90.0),
			Vector2(75.0, 91.0),
			Vector2(73.0, 96.0),
			Vector2(68.0, 96.0)
		],
		light
	)
	canvas.draw_circle(_p(box, 65.0, 82.0), 4.0 * unit, skin)
	canvas.draw_line(
		_p(box, 63.0, 85.0), _p(box, 68.0, 85.0), face_shade, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 23.0, 83.0), _p(box, 30.0, 90.0), steel, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 57.0, 77.0), _p(box, 62.0, 71.0), steel, maxf(1.0 * unit, 1.0), true)


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
