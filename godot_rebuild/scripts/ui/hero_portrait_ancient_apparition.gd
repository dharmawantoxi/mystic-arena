extends RefCounted
## Native canvas painter for Ancient Apparition, the True Boss/Ice Mage.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(8, 17, 33)
	var robe := Color8(23, 43, 76)
	var robe_light := Color8(42, 79, 119)
	var ice := Color8(106, 198, 227)
	var pale := Color8(195, 236, 246)
	var frost := Color8(88, 227, 241)
	var glow := Color8(231, 255, 255)

	_backdrop(canvas, box, Color8(44, 72, 127), Color8(11, 17, 33))
	canvas.draw_arc(
		_p(box, 47.0, 43.0),
		38.0 * unit,
		-PI * 0.90,
		-PI * 0.10,
		32,
		Color(frost.r, frost.g, frost.b, 0.25),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 47.0, 43.0),
		29.0 * unit,
		PI * 0.12,
		PI * 0.84,
		28,
		Color(glow.r, glow.g, glow.b, 0.18),
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 14.0, 34.0), 2.0 * unit, frost)
	canvas.draw_circle(_p(box, 80.0, 34.0), 1.8 * unit, glow)
	canvas.draw_circle(_p(box, 18.0, 55.0), 1.5 * unit, glow)
	canvas.draw_circle(_p(box, 77.0, 63.0), 2.0 * unit, frost)

	# A crystal-tipped staff floats behind the right side of the mantle.
	canvas.draw_line(_p(box, 82.0, 41.0), _p(box, 72.0, 93.0), outline, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 82.0, 41.0), _p(box, 73.0, 91.0), ice, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(76.0, 43.0),
			Vector2(77.0, 27.0),
			Vector2(82.0, 11.0),
			Vector2(87.0, 24.0),
			Vector2(87.0, 39.0),
			Vector2(82.0, 47.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(79.0, 39.0),
			Vector2(80.0, 27.0),
			Vector2(82.0, 17.0),
			Vector2(85.0, 27.0),
			Vector2(84.0, 38.0),
			Vector2(82.0, 42.0),
		],
		pale
	)
	_fill(
		canvas,
		box,
		[Vector2(81.0, 21.0), Vector2(75.0, 17.0), Vector2(77.0, 29.0), Vector2(81.0, 34.0)],
		ice
	)
	canvas.draw_line(_p(box, 82.0, 19.0), _p(box, 82.0, 38.0), glow, maxf(1.5 * unit, 1.0), true)

	# A flowing midnight robe widens into an icy mantle.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 93.0),
			Vector2(13.0, 73.0),
			Vector2(23.0, 64.0),
			Vector2(36.0, 58.0),
			Vector2(58.0, 58.0),
			Vector2(73.0, 66.0),
			Vector2(87.0, 93.0),
			Vector2(82.0, 96.0),
			Vector2(12.0, 96.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 92.0),
			Vector2(20.0, 75.0),
			Vector2(30.0, 68.0),
			Vector2(42.0, 63.0),
			Vector2(56.0, 63.0),
			Vector2(68.0, 70.0),
			Vector2(79.0, 92.0),
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 72.0),
			Vector2(17.0, 62.0),
			Vector2(29.0, 59.0),
			Vector2(39.0, 66.0),
			Vector2(34.0, 82.0),
			Vector2(22.0, 88.0),
			Vector2(13.0, 83.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(17.0, 71.0),
			Vector2(20.0, 65.0),
			Vector2(28.0, 63.0),
			Vector2(34.0, 68.0),
			Vector2(30.0, 79.0),
			Vector2(22.0, 83.0),
			Vector2(17.0, 80.0),
		],
		robe_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 66.0),
			Vector2(68.0, 60.0),
			Vector2(78.0, 64.0),
			Vector2(85.0, 75.0),
			Vector2(82.0, 85.0),
			Vector2(71.0, 89.0),
			Vector2(61.0, 81.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(63.0, 68.0),
			Vector2(70.0, 64.0),
			Vector2(77.0, 67.0),
			Vector2(81.0, 75.0),
			Vector2(78.0, 81.0),
			Vector2(71.0, 84.0),
			Vector2(65.0, 79.0),
		],
		robe_light
	)
	canvas.draw_line(_p(box, 19.0, 74.0), _p(box, 31.0, 70.0), ice, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 67.0, 73.0), _p(box, 78.0, 75.0), ice, maxf(2.0 * unit, 1.0), true)

	# Ice-crystal prongs rise from the hood like a frozen crown.
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 22.0),
			Vector2(30.0, 10.0),
			Vector2(40.0, 17.0),
			Vector2(47.0, 5.0),
			Vector2(51.0, 18.0),
			Vector2(61.0, 9.0),
			Vector2(60.0, 23.0),
			Vector2(54.0, 29.0),
			Vector2(39.0, 29.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 20.0),
			Vector2(34.0, 14.0),
			Vector2(42.0, 20.0),
			Vector2(47.0, 10.0),
			Vector2(50.0, 21.0),
			Vector2(58.0, 14.0),
			Vector2(57.0, 23.0),
			Vector2(52.0, 26.0),
			Vector2(40.0, 26.0),
		],
		pale
	)

	# The deep hood frames a calm, spectral face.
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 39.0),
			Vector2(26.0, 26.0),
			Vector2(33.0, 16.0),
			Vector2(45.0, 12.0),
			Vector2(58.0, 16.0),
			Vector2(68.0, 27.0),
			Vector2(67.0, 42.0),
			Vector2(61.0, 51.0),
			Vector2(55.0, 57.0),
			Vector2(39.0, 57.0),
			Vector2(31.0, 50.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 36.0),
			Vector2(32.0, 27.0),
			Vector2(38.0, 19.0),
			Vector2(46.0, 16.0),
			Vector2(55.0, 19.0),
			Vector2(62.0, 28.0),
			Vector2(61.0, 39.0),
			Vector2(56.0, 47.0),
			Vector2(49.0, 52.0),
			Vector2(41.0, 50.0),
			Vector2(35.0, 45.0),
		],
		robe_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 31.0),
			Vector2(43.0, 27.0),
			Vector2(52.0, 27.0),
			Vector2(59.0, 32.0),
			Vector2(57.0, 41.0),
			Vector2(52.0, 46.0),
			Vector2(45.0, 48.0),
			Vector2(39.0, 44.0),
		],
		Color8(124, 183, 204)
	)
	canvas.draw_line(_p(box, 36.0, 33.0), _p(box, 44.0, 34.0), outline, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 34.0), _p(box, 60.0, 33.0), outline, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 36.0), _p(box, 44.0, 36.0), glow, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 36.0), _p(box, 58.0, 36.0), glow, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 35.0), _p(box, 47.0, 42.0), ice, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 42.0, 45.0), _p(box, 53.0, 45.0), pale, maxf(1.5 * unit, 1.0), true)

	# Frosted collar, runic clasp, and a floating ice focus.
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 53.0),
			Vector2(39.0, 49.0),
			Vector2(47.0, 55.0),
			Vector2(55.0, 49.0),
			Vector2(65.0, 55.0),
			Vector2(61.0, 65.0),
			Vector2(49.0, 70.0),
			Vector2(36.0, 65.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 55.0),
			Vector2(40.0, 53.0),
			Vector2(47.0, 59.0),
			Vector2(54.0, 53.0),
			Vector2(60.0, 56.0),
			Vector2(57.0, 63.0),
			Vector2(49.0, 67.0),
			Vector2(39.0, 63.0),
		],
		ice
	)
	canvas.draw_line(_p(box, 41.0, 59.0), _p(box, 48.0, 64.0), glow, maxf(1.6 * unit, 1.0), true)
	canvas.draw_line(_p(box, 56.0, 59.0), _p(box, 49.0, 64.0), pale, maxf(1.6 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 49.0, 64.0), 3.0 * unit, outline)
	canvas.draw_circle(_p(box, 49.0, 64.0), 1.6 * unit, glow)

	_fill(
		canvas,
		box,
		[
			Vector2(46.0, 70.0),
			Vector2(50.0, 66.0),
			Vector2(55.0, 70.0),
			Vector2(56.0, 78.0),
			Vector2(51.0, 84.0),
			Vector2(44.0, 78.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(49.0, 70.0),
			Vector2(52.0, 73.0),
			Vector2(53.0, 78.0),
			Vector2(50.0, 81.0),
			Vector2(47.0, 78.0),
			Vector2(47.0, 73.0),
		],
		pale
	)
	canvas.draw_line(_p(box, 50.0, 72.0), _p(box, 50.0, 78.0), frost, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 39.0, 77.0), 1.7 * unit, glow)
	canvas.draw_circle(_p(box, 61.0, 81.0), 1.4 * unit, frost)


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
