extends RefCounted
## Native canvas portrait: Zhyrakaan, The Phantom Lancer.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(20, 28, 43)
	var armor := Color8(59, 91, 111)
	var shade := Color8(38, 57, 79)
	var steel := Color8(142, 181, 190)
	var cloth := Color8(42, 68, 91)
	var echo := Color8(36, 91, 105)
	var teal := Color8(70, 205, 197)
	var light := Color8(190, 255, 236)
	var violet := Color8(100, 99, 153)
	_backdrop(canvas, box, Color8(36, 71, 91), Color8(18, 24, 43))

	# Offset spectral silhouettes and broken halos suggest a phantom mirror-line.
	_fill(
		canvas,
		box,
		[
			Vector2(3.0, 84.0),
			Vector2(8.0, 55.0),
			Vector2(20.0, 45.0),
			Vector2(29.0, 53.0),
			Vector2(24.0, 75.0),
			Vector2(19.0, 94.0)
		],
		echo
	)
	_fill(
		canvas,
		box,
		[
			Vector2(73.0, 53.0),
			Vector2(82.0, 45.0),
			Vector2(92.0, 57.0),
			Vector2(95.0, 85.0),
			Vector2(84.0, 95.0),
			Vector2(77.0, 75.0)
		],
		echo
	)
	canvas.draw_arc(
		_p(box, 47.0, 42.0),
		36.0 * unit,
		PI * 0.75,
		PI * 1.55,
		40,
		teal,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 47.0, 42.0),
		36.0 * unit,
		PI * 1.72,
		PI * 2.35,
		40,
		violet,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 11.0, 30.0), _p(box, 22.0, 38.0), echo, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 74.0, 38.0), _p(box, 88.0, 27.0), echo, maxf(5.0 * unit, 1.0), true)

	# A split riding cloak sits beneath layered, blue-silver lancer armour.
	_fill(
		canvas,
		box,
		[
			Vector2(4.0, 96.0),
			Vector2(10.0, 69.0),
			Vector2(29.0, 54.0),
			Vector2(64.0, 55.0),
			Vector2(84.0, 70.0),
			Vector2(92.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 94.0),
			Vector2(16.0, 72.0),
			Vector2(29.0, 61.0),
			Vector2(36.0, 69.0),
			Vector2(29.0, 94.0)
		],
		cloth
	)
	_fill(
		canvas,
		box,
		[
			Vector2(63.0, 68.0),
			Vector2(72.0, 61.0),
			Vector2(82.0, 74.0),
			Vector2(87.0, 94.0),
			Vector2(67.0, 94.0)
		],
		violet
	)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 94.0),
			Vector2(17.0, 83.0),
			Vector2(20.0, 94.0),
			Vector2(25.0, 82.0),
			Vector2(29.0, 94.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 94.0),
			Vector2(73.0, 82.0),
			Vector2(78.0, 94.0),
			Vector2(83.0, 84.0),
			Vector2(87.0, 94.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 64.0),
			Vector2(42.0, 57.0),
			Vector2(57.0, 63.0),
			Vector2(66.0, 94.0),
			Vector2(26.0, 94.0)
		],
		armor
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 61.0), Vector2(57.0, 66.0), Vector2(62.0, 94.0), Vector2(48.0, 94.0)],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 65.0),
			Vector2(46.0, 75.0),
			Vector2(61.0, 65.0),
			Vector2(57.0, 79.0),
			Vector2(47.0, 87.0),
			Vector2(35.0, 79.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 69.0),
			Vector2(46.0, 77.0),
			Vector2(56.0, 70.0),
			Vector2(53.0, 77.0),
			Vector2(47.0, 82.0),
			Vector2(39.0, 77.0)
		],
		steel
	)
	canvas.draw_circle(_p(box, 47.0, 77.0), 3.0 * unit, teal)
	canvas.draw_circle(_p(box, 47.0, 77.0), 1.2 * unit, light)
	canvas.draw_line(_p(box, 35.0, 87.0), _p(box, 43.0, 91.0), steel, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 91.0), _p(box, 59.0, 86.0), violet, maxf(1.5 * unit, 1.0), true)

	# Broad pauldrons carry spectral rims rather than conventional spikes.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 69.0),
			Vector2(14.0, 54.0),
			Vector2(27.0, 50.0),
			Vector2(38.0, 63.0),
			Vector2(32.0, 77.0),
			Vector2(16.0, 80.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 68.0),
			Vector2(19.0, 58.0),
			Vector2(27.0, 56.0),
			Vector2(32.0, 64.0),
			Vector2(28.0, 72.0),
			Vector2(19.0, 74.0)
		],
		armor
	)
	canvas.draw_arc(
		_p(box, 24.0, 64.0), 10.0 * unit, PI * 0.85, PI * 1.8, 24, teal, maxf(1.5 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 63.0),
			Vector2(68.0, 50.0),
			Vector2(81.0, 54.0),
			Vector2(88.0, 69.0),
			Vector2(80.0, 80.0),
			Vector2(64.0, 77.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(64.0, 64.0),
			Vector2(70.0, 56.0),
			Vector2(78.0, 58.0),
			Vector2(82.0, 68.0),
			Vector2(77.0, 74.0),
			Vector2(68.0, 72.0)
		],
		armor
	)
	canvas.draw_line(_p(box, 70.0, 57.0), _p(box, 79.0, 64.0), teal, maxf(1.5 * unit, 1.0), true)

	# A closed helm and tall spectral crest conceal all but the luminous eyes.
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 32.0),
			Vector2(34.0, 18.0),
			Vector2(47.0, 11.0),
			Vector2(61.0, 18.0),
			Vector2(67.0, 32.0),
			Vector2(62.0, 50.0),
			Vector2(54.0, 59.0),
			Vector2(39.0, 57.0),
			Vector2(30.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 32.0),
			Vector2(38.0, 22.0),
			Vector2(47.0, 17.0),
			Vector2(57.0, 22.0),
			Vector2(62.0, 33.0),
			Vector2(58.0, 47.0),
			Vector2(52.0, 53.0),
			Vector2(41.0, 52.0),
			Vector2(35.0, 45.0)
		],
		armor
	)
	_fill(
		canvas,
		box,
		[
			Vector2(38.0, 18.0),
			Vector2(35.0, 5.0),
			Vector2(46.0, 11.0),
			Vector2(53.0, 3.0),
			Vector2(58.0, 18.0),
			Vector2(48.0, 23.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(42.0, 16.0),
			Vector2(40.0, 10.0),
			Vector2(47.0, 15.0),
			Vector2(52.0, 9.0),
			Vector2(54.0, 17.0),
			Vector2(48.0, 19.0)
		],
		violet
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 33.0),
			Vector2(43.0, 27.0),
			Vector2(57.0, 29.0),
			Vector2(62.0, 35.0),
			Vector2(57.0, 45.0),
			Vector2(39.0, 45.0),
			Vector2(34.0, 40.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(39.0, 34.0),
			Vector2(45.0, 31.0),
			Vector2(54.0, 32.0),
			Vector2(57.0, 36.0),
			Vector2(53.0, 40.0),
			Vector2(42.0, 40.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 38.0, 35.0), _p(box, 44.0, 37.0), light, maxf(2.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 37.0), _p(box, 57.0, 35.0), teal, maxf(2.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 29.0), _p(box, 47.0, 45.0), steel, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 40.0, 48.0), _p(box, 47.0, 52.0), steel, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 52.0), _p(box, 55.0, 47.0), steel, maxf(1.5 * unit, 1.0), true)

	# The long lance and its diamond head stay clear of the face silhouette.
	canvas.draw_line(_p(box, 72.0, 96.0), _p(box, 84.0, 27.0), ink, maxf(8.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 72.0, 96.0), _p(box, 84.0, 27.0), steel, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(80.0, 29.0),
			Vector2(83.0, 14.0),
			Vector2(89.0, 3.0),
			Vector2(92.0, 15.0),
			Vector2(88.0, 29.0),
			Vector2(85.0, 34.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(84.0, 26.0),
			Vector2(86.0, 15.0),
			Vector2(89.0, 9.0),
			Vector2(89.0, 17.0),
			Vector2(87.0, 26.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[Vector2(87.0, 15.0), Vector2(89.0, 9.0), Vector2(89.0, 18.0), Vector2(87.0, 25.0)],
		light
	)
	canvas.draw_line(_p(box, 78.0, 33.0), _p(box, 91.0, 29.0), ink, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 79.0, 32.0), _p(box, 90.0, 29.0), violet, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 80.0),
			Vector2(75.0, 75.0),
			Vector2(82.0, 80.0),
			Vector2(80.0, 90.0),
			Vector2(71.0, 92.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 81.0),
			Vector2(76.0, 79.0),
			Vector2(79.0, 82.0),
			Vector2(77.0, 87.0),
			Vector2(73.0, 88.0)
		],
		armor
	)
	canvas.draw_line(_p(box, 73.0, 83.0), _p(box, 79.0, 82.0), teal, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 16.0, 21.0), 1.2 * unit, light)
	canvas.draw_circle(_p(box, 70.0, 12.0), 1.0 * unit, teal)


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
