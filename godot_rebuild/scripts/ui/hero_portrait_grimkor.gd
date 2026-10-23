extends RefCounted
## Native canvas portrait: Grimkor, The Sawmill Warlord.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(32, 29, 27)
	var steel := Color8(99, 110, 109)
	var shade := Color8(57, 67, 66)
	var light := Color8(206, 209, 179)
	var rust := Color8(145, 87, 47)
	var wood := Color8(109, 73, 42)
	var skin := Color8(151, 154, 115)
	var darkskin := Color8(95, 113, 83)
	var red := Color8(149, 51, 42)
	var brass := Color8(193, 156, 78)
	_backdrop(canvas, box, Color8(82, 69, 48), Color8(27, 30, 29))

	# A toothed mill wheel and splintered beams establish a heavy industrial warlord.
	canvas.draw_circle(_p(box, 21.0, 36.0), 20.0 * unit, ink)
	canvas.draw_circle(_p(box, 21.0, 36.0), 17.0 * unit, steel)
	canvas.draw_circle(_p(box, 21.0, 36.0), 12.0 * unit, shade)
	_fill(canvas, box, [Vector2(6.0, 23.0), Vector2(4.0, 16.0), Vector2(13.0, 19.0)], steel)
	_fill(canvas, box, [Vector2(17.0, 18.0), Vector2(19.0, 10.0), Vector2(24.0, 18.0)], steel)
	_fill(canvas, box, [Vector2(32.0, 22.0), Vector2(39.0, 19.0), Vector2(36.0, 28.0)], steel)
	_fill(canvas, box, [Vector2(37.0, 36.0), Vector2(44.0, 39.0), Vector2(36.0, 43.0)], steel)
	_fill(canvas, box, [Vector2(25.0, 51.0), Vector2(24.0, 59.0), Vector2(18.0, 52.0)], steel)
	_fill(canvas, box, [Vector2(7.0, 44.0), Vector2(1.0, 45.0), Vector2(4.0, 36.0)], steel)
	canvas.draw_circle(_p(box, 21.0, 36.0), 4.0 * unit, brass)
	canvas.draw_circle(_p(box, 21.0, 36.0), 1.5 * unit, ink)
	canvas.draw_line(_p(box, 75.0, 19.0), _p(box, 88.0, 53.0), wood, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 75.0, 19.0), _p(box, 88.0, 53.0), rust, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(5.0, 96.0),
			Vector2(12.0, 67.0),
			Vector2(29.0, 55.0),
			Vector2(62.0, 55.0),
			Vector2(82.0, 68.0),
			Vector2(91.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 94.0),
			Vector2(18.0, 71.0),
			Vector2(31.0, 61.0),
			Vector2(60.0, 61.0),
			Vector2(76.0, 72.0),
			Vector2(84.0, 94.0)
		],
		wood
	)

	# Bolted steel shoulder plates, saw-tooth trim and a leather apron.
	_fill(
		canvas,
		box,
		[
			Vector2(7.0, 68.0),
			Vector2(13.0, 51.0),
			Vector2(26.0, 49.0),
			Vector2(37.0, 62.0),
			Vector2(35.0, 79.0),
			Vector2(16.0, 83.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 67.0),
			Vector2(18.0, 57.0),
			Vector2(25.0, 55.0),
			Vector2(32.0, 64.0),
			Vector2(29.0, 74.0),
			Vector2(18.0, 77.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[Vector2(14.0, 70.0), Vector2(29.0, 67.0), Vector2(30.0, 72.0), Vector2(18.0, 76.0)],
		rust
	)
	_fill(
		canvas,
		box,
		[
			Vector2(57.0, 62.0),
			Vector2(66.0, 49.0),
			Vector2(79.0, 52.0),
			Vector2(87.0, 68.0),
			Vector2(78.0, 83.0),
			Vector2(60.0, 78.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 64.0),
			Vector2(68.0, 55.0),
			Vector2(76.0, 58.0),
			Vector2(81.0, 68.0),
			Vector2(75.0, 77.0),
			Vector2(65.0, 73.0)
		],
		steel
	)
	canvas.draw_circle(_p(box, 18.0, 62.0), 2.0 * unit, ink)
	canvas.draw_circle(_p(box, 18.0, 62.0), 1.0 * unit, brass)
	canvas.draw_circle(_p(box, 26.0, 65.0), 2.0 * unit, ink)
	canvas.draw_circle(_p(box, 26.0, 65.0), 1.0 * unit, brass)
	canvas.draw_circle(_p(box, 69.0, 61.0), 2.0 * unit, ink)
	canvas.draw_circle(_p(box, 69.0, 61.0), 1.0 * unit, brass)
	canvas.draw_circle(_p(box, 76.0, 67.0), 2.0 * unit, ink)
	canvas.draw_circle(_p(box, 76.0, 67.0), 1.0 * unit, brass)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 64.0),
			Vector2(47.0, 59.0),
			Vector2(60.0, 65.0),
			Vector2(66.0, 94.0),
			Vector2(27.0, 94.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 68.0),
			Vector2(46.0, 65.0),
			Vector2(55.0, 69.0),
			Vector2(60.0, 94.0),
			Vector2(33.0, 94.0)
		],
		wood
	)
	canvas.draw_line(_p(box, 34.0, 70.0), _p(box, 58.0, 92.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 34.0, 70.0), _p(box, 58.0, 92.0), red, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(43.0, 79.0), Vector2(47.0, 75.0), Vector2(53.0, 80.0), Vector2(49.0, 85.0)],
		brass
	)

	# A riveted half-helm with work goggles exposes a square jaw and tusks.
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 30.0),
			Vector2(34.0, 20.0),
			Vector2(56.0, 18.0),
			Vector2(66.0, 29.0),
			Vector2(64.0, 46.0),
			Vector2(56.0, 59.0),
			Vector2(39.0, 61.0),
			Vector2(29.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 32.0),
			Vector2(38.0, 25.0),
			Vector2(54.0, 24.0),
			Vector2(60.0, 31.0),
			Vector2(59.0, 44.0),
			Vector2(53.0, 54.0),
			Vector2(41.0, 55.0),
			Vector2(35.0, 46.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 26.0),
			Vector2(58.0, 31.0),
			Vector2(60.0, 35.0),
			Vector2(57.0, 46.0),
			Vector2(52.0, 53.0),
			Vector2(48.0, 49.0)
		],
		darkskin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 31.0),
			Vector2(27.0, 22.0),
			Vector2(35.0, 15.0),
			Vector2(55.0, 13.0),
			Vector2(66.0, 22.0),
			Vector2(67.0, 33.0),
			Vector2(58.0, 29.0),
			Vector2(37.0, 31.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 27.0),
			Vector2(32.0, 23.0),
			Vector2(38.0, 19.0),
			Vector2(54.0, 18.0),
			Vector2(61.0, 24.0),
			Vector2(62.0, 28.0),
			Vector2(55.0, 25.0),
			Vector2(38.0, 27.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 35.0, 24.0), _p(box, 55.0, 22.0), rust, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 31.0, 33.0), _p(box, 62.0, 32.0), ink, maxf(5.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 39.0, 34.0), 6.0 * unit, ink)
	canvas.draw_circle(_p(box, 39.0, 34.0), 4.5 * unit, brass)
	canvas.draw_circle(_p(box, 39.0, 34.0), 3.0 * unit, shade)
	canvas.draw_circle(_p(box, 55.0, 34.0), 6.0 * unit, ink)
	canvas.draw_circle(_p(box, 55.0, 34.0), 4.5 * unit, brass)
	canvas.draw_circle(_p(box, 55.0, 34.0), 3.0 * unit, red)
	canvas.draw_line(_p(box, 37.0, 32.0), _p(box, 40.0, 35.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 32.0), _p(box, 56.0, 35.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 36.0), _p(box, 45.0, 43.0), skin, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 49.0), _p(box, 55.0, 48.0), ink, maxf(2.0 * unit, 1.0), true)
	_fill(canvas, box, [Vector2(37.0, 46.0), Vector2(39.0, 42.0), Vector2(43.0, 49.0)], light)
	_fill(canvas, box, [Vector2(51.0, 49.0), Vector2(56.0, 42.0), Vector2(56.0, 47.0)], light)
	_fill(
		canvas,
		box,
		[
			Vector2(39.0, 53.0),
			Vector2(47.0, 56.0),
			Vector2(55.0, 51.0),
			Vector2(53.0, 58.0),
			Vector2(42.0, 59.0)
		],
		darkskin
	)

	# A long mechanical saw rises at the right, with teeth separated from its bar.
	_fill(
		canvas,
		box,
		[
			Vector2(75.0, 13.0),
			Vector2(83.0, 10.0),
			Vector2(87.0, 19.0),
			Vector2(84.0, 68.0),
			Vector2(72.0, 68.0),
			Vector2(72.0, 21.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 17.0),
			Vector2(81.0, 15.0),
			Vector2(83.0, 21.0),
			Vector2(81.0, 62.0),
			Vector2(76.0, 62.0),
			Vector2(76.0, 23.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 79.0, 22.0), _p(box, 78.0, 58.0), shade, maxf(2.0 * unit, 1.0), true)
	_fill(canvas, box, [Vector2(84.0, 23.0), Vector2(90.0, 25.0), Vector2(84.0, 29.0)], light)
	_fill(canvas, box, [Vector2(84.0, 32.0), Vector2(90.0, 34.0), Vector2(84.0, 38.0)], light)
	_fill(canvas, box, [Vector2(84.0, 41.0), Vector2(90.0, 43.0), Vector2(84.0, 47.0)], light)
	_fill(canvas, box, [Vector2(84.0, 50.0), Vector2(90.0, 52.0), Vector2(84.0, 56.0)], light)
	_fill(canvas, box, [Vector2(84.0, 59.0), Vector2(90.0, 61.0), Vector2(84.0, 65.0)], light)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 65.0),
			Vector2(85.0, 65.0),
			Vector2(87.0, 79.0),
			Vector2(80.0, 87.0),
			Vector2(68.0, 82.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 69.0),
			Vector2(81.0, 69.0),
			Vector2(82.0, 77.0),
			Vector2(78.0, 82.0),
			Vector2(72.0, 79.0)
		],
		rust
	)
	canvas.draw_circle(_p(box, 77.0, 74.0), 3.0 * unit, ink)
	canvas.draw_circle(_p(box, 77.0, 74.0), 1.5 * unit, brass)
	canvas.draw_line(_p(box, 74.0, 84.0), _p(box, 74.0, 94.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 74.0, 85.0), _p(box, 74.0, 93.0), steel, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 69.0, 83.0), 4.0 * unit, skin)
	canvas.draw_line(_p(box, 67.0, 86.0), _p(box, 72.0, 86.0), shade, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 82.0),
			Vector2(22.0, 78.0),
			Vector2(31.0, 86.0),
			Vector2(29.0, 96.0),
			Vector2(9.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 85.0),
			Vector2(21.0, 83.0),
			Vector2(26.0, 88.0),
			Vector2(25.0, 93.0),
			Vector2(14.0, 93.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 16.0, 88.0), _p(box, 24.0, 88.0), brass, maxf(1.5 * unit, 1.0), true)


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
