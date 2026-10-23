extends RefCounted
## Native canvas portrait: Thargoroth, The Primordial Colossus.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(28, 33, 31)
	var stone := Color8(104, 110, 91)
	var shade := Color8(65, 75, 66)
	var moss := Color8(66, 105, 62)
	var leaf := Color8(113, 143, 71)
	var amber := Color8(224, 160, 65)
	var light := Color8(245, 220, 137)
	var bone := Color8(190, 179, 137)
	var earth := Color8(83, 65, 47)
	_backdrop(canvas, box, Color8(79, 100, 73), Color8(29, 39, 35))

	# Primitive mountains and a held boulder establish the colossus at range.
	canvas.draw_circle(_p(box, 47.0, 36.0), 30.0 * unit, earth)
	_fill(
		canvas,
		box,
		[
			Vector2(0.0, 66.0),
			Vector2(17.0, 35.0),
			Vector2(27.0, 55.0),
			Vector2(40.0, 24.0),
			Vector2(57.0, 59.0),
			Vector2(72.0, 31.0),
			Vector2(96.0, 64.0),
			Vector2(96.0, 96.0),
			Vector2(0.0, 96.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(70.0, 25.0),
			Vector2(73.0, 12.0),
			Vector2(85.0, 5.0),
			Vector2(94.0, 13.0),
			Vector2(92.0, 28.0),
			Vector2(82.0, 35.0),
			Vector2(72.0, 32.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(75.0, 24.0),
			Vector2(77.0, 15.0),
			Vector2(85.0, 10.0),
			Vector2(90.0, 15.0),
			Vector2(88.0, 26.0),
			Vector2(82.0, 30.0),
			Vector2(76.0, 28.0)
		],
		stone
	)
	canvas.draw_line(_p(box, 84.0, 11.0), _p(box, 82.0, 19.0), amber, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 82.0, 19.0), _p(box, 86.0, 24.0), light, maxf(1.2 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 13.0, 18.0), 1.5 * unit, leaf)
	canvas.draw_circle(_p(box, 24.0, 12.0), 1.0 * unit, light)

	# A massive asymmetrical stone torso carries moss, fossil plates and an amber core.
	_fill(
		canvas,
		box,
		[
			Vector2(2.0, 96.0),
			Vector2(5.0, 71.0),
			Vector2(19.0, 55.0),
			Vector2(33.0, 54.0),
			Vector2(47.0, 62.0),
			Vector2(63.0, 53.0),
			Vector2(80.0, 55.0),
			Vector2(94.0, 74.0),
			Vector2(96.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 94.0),
			Vector2(12.0, 74.0),
			Vector2(23.0, 62.0),
			Vector2(34.0, 61.0),
			Vector2(47.0, 69.0),
			Vector2(62.0, 60.0),
			Vector2(76.0, 62.0),
			Vector2(87.0, 76.0),
			Vector2(89.0, 94.0)
		],
		stone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(48.0, 69.0),
			Vector2(62.0, 61.0),
			Vector2(76.0, 64.0),
			Vector2(85.0, 77.0),
			Vector2(87.0, 94.0),
			Vector2(50.0, 94.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 73.0),
			Vector2(22.0, 61.0),
			Vector2(34.0, 62.0),
			Vector2(30.0, 69.0),
			Vector2(19.0, 72.0),
			Vector2(17.0, 80.0)
		],
		moss
	)
	_fill(
		canvas,
		box,
		[
			Vector2(63.0, 61.0),
			Vector2(75.0, 62.0),
			Vector2(82.0, 70.0),
			Vector2(73.0, 69.0),
			Vector2(67.0, 74.0),
			Vector2(60.0, 68.0)
		],
		moss
	)
	canvas.draw_circle(_p(box, 22.0, 62.0), 3.0 * unit, leaf)
	canvas.draw_circle(_p(box, 72.0, 64.0), 2.5 * unit, leaf)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 68.0),
			Vector2(47.0, 62.0),
			Vector2(63.0, 68.0),
			Vector2(60.0, 84.0),
			Vector2(48.0, 91.0),
			Vector2(34.0, 84.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(47.0, 67.0),
			Vector2(56.0, 72.0),
			Vector2(54.0, 82.0),
			Vector2(48.0, 86.0),
			Vector2(40.0, 81.0),
			Vector2(39.0, 72.0)
		],
		earth
	)
	canvas.draw_circle(_p(box, 47.0, 76.0), 6.0 * unit, amber)
	canvas.draw_circle(_p(box, 47.0, 76.0), 2.5 * unit, light)
	canvas.draw_line(_p(box, 33.0, 88.0), _p(box, 40.0, 92.0), bone, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 55.0, 92.0), _p(box, 62.0, 87.0), moss, maxf(2.0 * unit, 1.0), true)

	# A raised stone arm connects the boulder to the huge shoulder silhouette.
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 96.0),
			Vector2(70.0, 70.0),
			Vector2(76.0, 49.0),
			Vector2(73.0, 35.0),
			Vector2(82.0, 31.0),
			Vector2(89.0, 42.0),
			Vector2(88.0, 62.0),
			Vector2(85.0, 79.0),
			Vector2(89.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(74.0, 91.0),
			Vector2(75.0, 70.0),
			Vector2(81.0, 50.0),
			Vector2(78.0, 38.0),
			Vector2(82.0, 36.0),
			Vector2(85.0, 43.0),
			Vector2(83.0, 62.0),
			Vector2(80.0, 79.0),
			Vector2(84.0, 92.0)
		],
		stone
	)
	canvas.draw_line(_p(box, 80.0, 48.0), _p(box, 84.0, 54.0), amber, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 76.0, 71.0), _p(box, 81.0, 75.0), moss, maxf(2.0 * unit, 1.0), true)

	# The small ancient head has a slab brow, amber eyes and fossil-like teeth.
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 32.0),
			Vector2(34.0, 20.0),
			Vector2(47.0, 15.0),
			Vector2(60.0, 20.0),
			Vector2(66.0, 33.0),
			Vector2(62.0, 50.0),
			Vector2(55.0, 59.0),
			Vector2(39.0, 58.0),
			Vector2(31.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 33.0),
			Vector2(39.0, 25.0),
			Vector2(47.0, 21.0),
			Vector2(56.0, 24.0),
			Vector2(61.0, 33.0),
			Vector2(58.0, 46.0),
			Vector2(53.0, 53.0),
			Vector2(41.0, 53.0),
			Vector2(36.0, 46.0)
		],
		stone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 22.0),
			Vector2(57.0, 25.0),
			Vector2(61.0, 34.0),
			Vector2(58.0, 46.0),
			Vector2(52.0, 53.0),
			Vector2(47.0, 47.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 31.0),
			Vector2(36.0, 22.0),
			Vector2(58.0, 21.0),
			Vector2(67.0, 30.0),
			Vector2(59.0, 35.0),
			Vector2(44.0, 32.0),
			Vector2(35.0, 36.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 24.0),
			Vector2(39.0, 16.0),
			Vector2(48.0, 14.0),
			Vector2(55.0, 18.0),
			Vector2(51.0, 23.0),
			Vector2(42.0, 22.0),
			Vector2(39.0, 28.0)
		],
		moss
	)
	canvas.draw_circle(_p(box, 43.0, 18.0), 2.0 * unit, leaf)
	canvas.draw_line(_p(box, 35.0, 36.0), _p(box, 43.0, 37.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 37.0), _p(box, 59.0, 35.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 40.0, 39.0), 1.8 * unit, amber)
	canvas.draw_circle(_p(box, 55.0, 39.0), 1.8 * unit, light)
	_fill(
		canvas,
		box,
		[
			Vector2(41.0, 39.0),
			Vector2(47.0, 37.0),
			Vector2(54.0, 40.0),
			Vector2(52.0, 47.0),
			Vector2(47.0, 49.0),
			Vector2(40.0, 46.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 48.0),
			Vector2(46.0, 51.0),
			Vector2(57.0, 47.0),
			Vector2(54.0, 56.0),
			Vector2(47.0, 59.0),
			Vector2(40.0, 55.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(41.0, 51.0), Vector2(45.0, 52.0), Vector2(44.0, 56.0), Vector2(41.0, 54.0)],
		bone
	)
	_fill(
		canvas,
		box,
		[Vector2(49.0, 52.0), Vector2(53.0, 50.0), Vector2(52.0, 55.0), Vector2(49.0, 57.0)],
		bone
	)
	canvas.draw_line(_p(box, 36.0, 42.0), _p(box, 34.0, 47.0), amber, maxf(1.2 * unit, 1.0), true)

	# The free hand is a heavy cracked stone fist rather than a weapon grip.
	_fill(
		canvas,
		box,
		[
			Vector2(3.0, 96.0),
			Vector2(5.0, 81.0),
			Vector2(14.0, 72.0),
			Vector2(27.0, 77.0),
			Vector2(33.0, 90.0),
			Vector2(29.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 93.0),
			Vector2(10.0, 83.0),
			Vector2(16.0, 78.0),
			Vector2(24.0, 81.0),
			Vector2(28.0, 90.0),
			Vector2(25.0, 94.0)
		],
		stone
	)
	canvas.draw_line(_p(box, 13.0, 82.0), _p(box, 24.0, 85.0), shade, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 18.0, 79.0), _p(box, 19.0, 88.0), amber, maxf(1.2 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 8.0, 70.0), 2.0 * unit, moss)


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
