extends RefCounted
## Native canvas painter for Abaddon, the True Boss/Knight Hero Shop portrait.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(10, 15, 27)
	var armor := Color8(29, 40, 62)
	var armor_light := Color8(58, 79, 111)
	var steel := Color8(137, 164, 188)
	var silver := Color8(216, 232, 237)
	var frost := Color8(71, 213, 222)
	var glow := Color8(179, 255, 250)

	_backdrop(canvas, box, Color8(37, 69, 113), Color8(12, 17, 29))
	canvas.draw_arc(
		_p(box, 48.0, 44.0),
		39.0 * unit,
		-PI * 0.88,
		-PI * 0.10,
		32,
		Color(frost.r, frost.g, frost.b, 0.26),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 44.0),
		31.0 * unit,
		PI * 0.12,
		PI * 0.82,
		28,
		Color(glow.r, glow.g, glow.b, 0.18),
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 16.0, 36.0), 2.2 * unit, frost)
	canvas.draw_circle(_p(box, 79.0, 29.0), 1.8 * unit, glow)
	canvas.draw_circle(_p(box, 18.0, 55.0), 1.4 * unit, glow)
	canvas.draw_circle(_p(box, 80.0, 61.0), 2.0 * unit, frost)

	# The ghost-lit sword rises behind the right shoulder.
	_fill(
		canvas,
		box,
		[
			Vector2(66.0, 47.0),
			Vector2(72.0, 25.0),
			Vector2(82.0, 9.0),
			Vector2(83.0, 24.0),
			Vector2(75.0, 48.0),
			Vector2(70.0, 55.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(70.0, 43.0),
			Vector2(75.0, 25.0),
			Vector2(80.0, 16.0),
			Vector2(79.0, 26.0),
			Vector2(73.0, 45.0),
			Vector2(70.0, 49.0),
		],
		steel
	)
	canvas.draw_line(_p(box, 74.0, 30.0), _p(box, 79.0, 21.0), glow, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 68.0, 48.0), _p(box, 79.0, 52.0), outline, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 69.0, 48.0), _p(box, 78.0, 51.0), silver, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 73.0, 50.0), _p(box, 62.0, 77.0), outline, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 73.0, 51.0), _p(box, 64.0, 74.0), armor_light, maxf(1.8 * unit, 1.0), true
	)

	# Armored body, shield, and layered pauldrons.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 92.0),
			Vector2(13.0, 72.0),
			Vector2(24.0, 63.0),
			Vector2(37.0, 57.0),
			Vector2(59.0, 57.0),
			Vector2(74.0, 64.0),
			Vector2(87.0, 92.0),
			Vector2(83.0, 96.0),
			Vector2(12.0, 96.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(16.0, 92.0),
			Vector2(21.0, 74.0),
			Vector2(31.0, 67.0),
			Vector2(43.0, 63.0),
			Vector2(57.0, 63.0),
			Vector2(69.0, 70.0),
			Vector2(78.0, 92.0),
		],
		armor
	)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 69.0),
			Vector2(17.0, 59.0),
			Vector2(30.0, 62.0),
			Vector2(37.0, 72.0),
			Vector2(32.0, 85.0),
			Vector2(19.0, 90.0),
			Vector2(11.0, 82.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 70.0),
			Vector2(18.0, 63.0),
			Vector2(28.0, 66.0),
			Vector2(33.0, 73.0),
			Vector2(29.0, 82.0),
			Vector2(20.0, 86.0),
			Vector2(14.0, 80.0),
		],
		armor_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(61.0, 69.0),
			Vector2(69.0, 61.0),
			Vector2(81.0, 63.0),
			Vector2(86.0, 73.0),
			Vector2(82.0, 86.0),
			Vector2(70.0, 89.0),
			Vector2(62.0, 82.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(65.0, 71.0),
			Vector2(71.0, 66.0),
			Vector2(79.0, 67.0),
			Vector2(82.0, 74.0),
			Vector2(79.0, 81.0),
			Vector2(71.0, 84.0),
			Vector2(65.0, 79.0),
		],
		armor_light
	)
	canvas.draw_line(_p(box, 17.0, 74.0), _p(box, 29.0, 71.0), silver, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 69.0, 73.0), _p(box, 80.0, 71.0), silver, maxf(2.0 * unit, 1.0), true)

	# A warding kite shield anchors the left side of the silhouette.
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 66.0),
			Vector2(4.0, 59.0),
			Vector2(11.0, 54.0),
			Vector2(25.0, 56.0),
			Vector2(34.0, 66.0),
			Vector2(31.0, 81.0),
			Vector2(20.0, 90.0),
			Vector2(10.0, 82.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 65.0),
			Vector2(8.0, 60.0),
			Vector2(13.0, 57.0),
			Vector2(23.0, 59.0),
			Vector2(30.0, 67.0),
			Vector2(28.0, 79.0),
			Vector2(20.0, 86.0),
			Vector2(13.0, 80.0),
		],
		steel
	)
	canvas.draw_line(_p(box, 13.0, 67.0), _p(box, 25.0, 69.0), glow, maxf(1.6 * unit, 1.0), true)
	canvas.draw_line(_p(box, 21.0, 62.0), _p(box, 20.0, 81.0), frost, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 20.0, 71.0), 3.4 * unit, outline)
	canvas.draw_circle(_p(box, 20.0, 71.0), 1.7 * unit, glow)

	# High-crested helm and shadowed spectral visor.
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 37.0),
			Vector2(28.0, 25.0),
			Vector2(35.0, 16.0),
			Vector2(47.0, 11.0),
			Vector2(59.0, 16.0),
			Vector2(68.0, 25.0),
			Vector2(67.0, 39.0),
			Vector2(62.0, 51.0),
			Vector2(54.0, 57.0),
			Vector2(40.0, 56.0),
			Vector2(32.0, 50.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 35.0),
			Vector2(33.0, 26.0),
			Vector2(39.0, 19.0),
			Vector2(47.0, 16.0),
			Vector2(57.0, 19.0),
			Vector2(63.0, 27.0),
			Vector2(62.0, 39.0),
			Vector2(57.0, 48.0),
			Vector2(51.0, 52.0),
			Vector2(42.0, 51.0),
			Vector2(36.0, 46.0),
		],
		armor_light
	)
	_fill(
		canvas,
		box,
		[Vector2(42.0, 18.0), Vector2(47.0, 6.0), Vector2(51.0, 19.0), Vector2(48.0, 25.0)],
		outline
	)
	_fill(
		canvas,
		box,
		[Vector2(46.0, 17.0), Vector2(47.0, 11.0), Vector2(49.0, 18.0), Vector2(48.0, 21.0)],
		silver
	)
	canvas.draw_line(_p(box, 34.0, 27.0), _p(box, 40.0, 21.0), silver, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 60.0, 21.0), _p(box, 65.0, 28.0), silver, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 31.0),
			Vector2(43.0, 27.0),
			Vector2(52.0, 27.0),
			Vector2(61.0, 32.0),
			Vector2(59.0, 42.0),
			Vector2(51.0, 48.0),
			Vector2(43.0, 47.0),
			Vector2(36.0, 42.0),
		],
		outline
	)
	canvas.draw_line(_p(box, 37.0, 35.0), _p(box, 44.0, 34.0), frost, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 34.0), _p(box, 59.0, 35.0), frost, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 38.0), _p(box, 44.0, 38.0), glow, maxf(unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 38.0), _p(box, 58.0, 38.0), glow, maxf(unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 34.0), _p(box, 48.0, 43.0), steel, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 42.0, 45.0), _p(box, 54.0, 45.0), silver, maxf(1.5 * unit, 1.0), true)

	# The split breastplate frames a luminous crescent sigil.
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 65.0),
			Vector2(39.0, 59.0),
			Vector2(48.0, 62.0),
			Vector2(57.0, 59.0),
			Vector2(65.0, 65.0),
			Vector2(61.0, 84.0),
			Vector2(49.0, 90.0),
			Vector2(36.0, 84.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 66.0),
			Vector2(41.0, 63.0),
			Vector2(48.0, 66.0),
			Vector2(55.0, 63.0),
			Vector2(61.0, 67.0),
			Vector2(57.0, 81.0),
			Vector2(49.0, 85.0),
			Vector2(40.0, 81.0),
		],
		armor_light
	)
	canvas.draw_line(_p(box, 40.0, 70.0), _p(box, 49.0, 75.0), silver, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 57.0, 70.0), _p(box, 49.0, 75.0), silver, maxf(2.0 * unit, 1.0), true)
	canvas.draw_arc(
		_p(box, 49.0, 76.0),
		6.0 * unit,
		-PI * 0.85,
		PI * 0.55,
		20,
		glow,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 49.0, 76.0), 1.5 * unit, frost)
	canvas.draw_line(_p(box, 36.0, 85.0), _p(box, 42.0, 88.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 56.0, 88.0), _p(box, 62.0, 84.0), silver, maxf(1.5 * unit, 1.0), true)


static func _fill(canvas: CanvasItem, box: Rect2, points: Array[Vector2], color: Color) -> void:
	canvas.draw_colored_polygon(_poly(box, points), color)


static func _p(box: Rect2, x: float, y: float) -> Vector2:
	return box.position + Vector2(x, y) * (box.size.x / SIZE)


static func _poly(box: Rect2, points: Array[Vector2]) -> PackedVector2Array:
	var result := PackedVector2Array()
	for point in points:
		result.append(box.position + point * (box.size.x / SIZE))
	return result


static func _backdrop(canvas: CanvasItem, box: Rect2, top: Color, bottom: Color) -> void:
	var bands := 18
	var height := box.size.y / float(bands)
	for index in bands:
		var band := Rect2(
			box.position.x, box.position.y + height * float(index), box.size.x, height + 1.0
		)
		canvas.draw_rect(band, top.lerp(bottom, float(index) / float(bands - 1)))
