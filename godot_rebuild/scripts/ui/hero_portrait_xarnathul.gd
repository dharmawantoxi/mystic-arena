extends RefCounted
## Native canvas portrait: Xarnathul, The Deathsinger.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(25, 22, 38)
	var robe := Color8(55, 45, 76)
	var violet := Color8(102, 65, 119)
	var shade := Color8(68, 79, 94)
	var skin := Color8(139, 157, 151)
	var bone := Color8(204, 216, 190)
	var teal := Color8(79, 196, 181)
	var light := Color8(197, 248, 218)
	var silver := Color8(137, 157, 169)
	var mouth := Color8(43, 25, 48)
	_backdrop(canvas, box, Color8(50, 57, 77), Color8(20, 23, 40))

	# Concentric song-waves and two spectral notes surround the deathly choir.
	canvas.draw_arc(
		_p(box, 47.0, 41.0),
		36.0 * unit,
		PI * 0.55,
		PI * 2.45,
		64,
		violet,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 47.0, 41.0),
		30.0 * unit,
		PI * 0.62,
		PI * 2.38,
		64,
		teal,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 12.0, 34.0), 3.0 * unit, teal)
	canvas.draw_line(_p(box, 14.0, 33.0), _p(box, 14.0, 18.0), bone, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 14.0, 18.0), _p(box, 22.0, 15.0), bone, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 83.0, 43.0), 2.5 * unit, light)
	canvas.draw_line(_p(box, 85.0, 42.0), _p(box, 85.0, 29.0), teal, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 85.0, 29.0), _p(box, 90.0, 27.0), teal, maxf(2.0 * unit, 1.0), true)

	# A long torn robe and split funerary collar frame the singer's exposed throat.
	_fill(
		canvas,
		box,
		[
			Vector2(5.0, 96.0),
			Vector2(11.0, 71.0),
			Vector2(29.0, 56.0),
			Vector2(63.0, 56.0),
			Vector2(82.0, 71.0),
			Vector2(91.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 94.0),
			Vector2(18.0, 73.0),
			Vector2(32.0, 62.0),
			Vector2(60.0, 62.0),
			Vector2(76.0, 74.0),
			Vector2(84.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 94.0),
			Vector2(20.0, 75.0),
			Vector2(34.0, 65.0),
			Vector2(42.0, 78.0),
			Vector2(35.0, 94.0)
		],
		violet
	)
	_fill(
		canvas,
		box,
		[
			Vector2(54.0, 77.0),
			Vector2(61.0, 65.0),
			Vector2(75.0, 75.0),
			Vector2(82.0, 94.0),
			Vector2(60.0, 94.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(22.0, 67.0),
			Vector2(18.0, 40.0),
			Vector2(30.0, 47.0),
			Vector2(40.0, 65.0),
			Vector2(34.0, 75.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(25.0, 63.0),
			Vector2(23.0, 49.0),
			Vector2(30.0, 54.0),
			Vector2(35.0, 66.0),
			Vector2(32.0, 69.0)
		],
		silver
	)
	_fill(
		canvas,
		box,
		[
			Vector2(56.0, 65.0),
			Vector2(66.0, 47.0),
			Vector2(78.0, 39.0),
			Vector2(73.0, 67.0),
			Vector2(62.0, 75.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(61.0, 65.0),
			Vector2(67.0, 54.0),
			Vector2(73.0, 48.0),
			Vector2(69.0, 64.0),
			Vector2(63.0, 69.0)
		],
		silver
	)

	# Rib-like jewellery and a glowing throat seal make the silhouette ceremonial.
	canvas.draw_circle(_p(box, 47.0, 66.0), 6.0 * unit, ink)
	canvas.draw_circle(_p(box, 47.0, 66.0), 3.5 * unit, teal)
	canvas.draw_circle(_p(box, 47.0, 66.0), 1.3 * unit, light)
	canvas.draw_line(_p(box, 34.0, 72.0), _p(box, 42.0, 77.0), silver, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 31.0, 78.0), _p(box, 41.0, 83.0), silver, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 60.0, 72.0), _p(box, 52.0, 77.0), silver, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 63.0, 78.0), _p(box, 53.0, 83.0), silver, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 73.0), _p(box, 47.0, 93.0), teal, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 87.0),
			Vector2(42.0, 84.0),
			Vector2(47.0, 89.0),
			Vector2(53.0, 84.0),
			Vector2(60.0, 87.0),
			Vector2(57.0, 94.0),
			Vector2(38.0, 94.0)
		],
		ink
	)

	# The peaked veil is drawn behind a gaunt face with a visibly singing mouth.
	_fill(
		canvas,
		box,
		[
			Vector2(23.0, 51.0),
			Vector2(20.0, 29.0),
			Vector2(27.0, 13.0),
			Vector2(40.0, 6.0),
			Vector2(47.0, 13.0),
			Vector2(55.0, 6.0),
			Vector2(69.0, 14.0),
			Vector2(75.0, 30.0),
			Vector2(69.0, 51.0),
			Vector2(61.0, 59.0),
			Vector2(33.0, 59.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 45.0),
			Vector2(27.0, 29.0),
			Vector2(33.0, 18.0),
			Vector2(41.0, 14.0),
			Vector2(47.0, 20.0),
			Vector2(54.0, 14.0),
			Vector2(64.0, 19.0),
			Vector2(69.0, 31.0),
			Vector2(64.0, 47.0),
			Vector2(58.0, 53.0),
			Vector2(36.0, 53.0)
		],
		violet
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 31.0),
			Vector2(36.0, 21.0),
			Vector2(54.0, 20.0),
			Vector2(64.0, 30.0),
			Vector2(62.0, 46.0),
			Vector2(55.0, 57.0),
			Vector2(40.0, 58.0),
			Vector2(31.0, 46.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 32.0),
			Vector2(40.0, 26.0),
			Vector2(53.0, 25.0),
			Vector2(59.0, 31.0),
			Vector2(58.0, 43.0),
			Vector2(53.0, 51.0),
			Vector2(42.0, 52.0),
			Vector2(36.0, 44.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 26.0),
			Vector2(58.0, 31.0),
			Vector2(59.0, 37.0),
			Vector2(56.0, 46.0),
			Vector2(51.0, 51.0),
			Vector2(48.0, 47.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 31.0),
			Vector2(35.0, 20.0),
			Vector2(47.0, 16.0),
			Vector2(60.0, 21.0),
			Vector2(66.0, 32.0),
			Vector2(57.0, 28.0),
			Vector2(47.0, 25.0),
			Vector2(37.0, 28.0)
		],
		ink
	)
	canvas.draw_line(_p(box, 36.0, 34.0), _p(box, 43.0, 36.0), ink, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 36.0), _p(box, 58.0, 33.0), ink, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 38.0), _p(box, 43.0, 38.0), light, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 38.0), _p(box, 56.0, 37.0), teal, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 36.0), _p(box, 45.0, 42.0), bone, maxf(1.2 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(41.0, 43.0),
			Vector2(47.0, 41.0),
			Vector2(53.0, 43.0),
			Vector2(52.0, 51.0),
			Vector2(47.0, 55.0),
			Vector2(42.0, 51.0)
		],
		mouth
	)
	canvas.draw_line(_p(box, 43.0, 45.0), _p(box, 51.0, 45.0), bone, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(44.0, 50.0), Vector2(47.0, 48.0), Vector2(50.0, 50.0), Vector2(47.0, 52.0)],
		teal
	)
	canvas.draw_arc(
		_p(box, 47.0, 47.0),
		15.0 * unit,
		PI * -0.32,
		PI * 0.32,
		24,
		light,
		maxf(1.2 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 47.0, 47.0),
		20.0 * unit,
		PI * -0.28,
		PI * 0.28,
		24,
		teal,
		maxf(1.0 * unit, 1.0),
		true
	)

	# One raised bony hand conducts the refrain; no weapon is carried.
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 96.0),
			Vector2(10.0, 82.0),
			Vector2(15.0, 76.0),
			Vector2(16.0, 63.0),
			Vector2(20.0, 62.0),
			Vector2(22.0, 74.0),
			Vector2(26.0, 66.0),
			Vector2(30.0, 67.0),
			Vector2(28.0, 79.0),
			Vector2(34.0, 76.0),
			Vector2(37.0, 80.0),
			Vector2(29.0, 91.0),
			Vector2(24.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 91.0),
			Vector2(15.0, 82.0),
			Vector2(20.0, 77.0),
			Vector2(26.0, 79.0),
			Vector2(31.0, 81.0),
			Vector2(26.0, 89.0),
			Vector2(22.0, 93.0)
		],
		skin
	)
	canvas.draw_line(_p(box, 18.0, 78.0), _p(box, 18.0, 66.0), bone, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 23.0, 78.0), _p(box, 28.0, 70.0), bone, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 27.0, 82.0), _p(box, 33.0, 79.0), bone, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 14.0, 57.0), 1.2 * unit, light)
	canvas.draw_circle(_p(box, 79.0, 59.0), 1.0 * unit, teal)


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
