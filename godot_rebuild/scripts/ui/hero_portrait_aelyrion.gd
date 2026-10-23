extends RefCounted
## Native canvas portrait: Aelyrion, The Divine Guardian / Steel Maiden Guardian.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(15, 23, 42)
	var steel := Color8(112, 143, 175)
	var silver := Color8(209, 226, 237)
	var light := Color8(248, 242, 204)
	var gold := Color8(213, 178, 91)
	var blue := Color8(36, 66, 109)
	var hair := Color8(220, 211, 165)
	var skin := Color8(227, 179, 148)
	var shade := Color8(156, 107, 96)
	_backdrop(canvas, box, Color8(51, 73, 108), Color8(12, 23, 43))

	# A broken aureole and steel winglets establish the guardian silhouette.
	canvas.draw_arc(
		_p(box, 48.0, 35.0),
		29.0 * unit,
		PI * -0.94,
		PI * -0.06,
		32,
		gold,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 35.0),
		33.0 * unit,
		PI * -0.86,
		PI * -0.14,
		32,
		silver,
		maxf(1.0 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 29.0, 9.0), _p(box, 29.0, 14.0), light, maxf(1.4 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 9.0), _p(box, 48.0, 14.0), light, maxf(1.4 * unit, 1.0), true)
	canvas.draw_line(_p(box, 67.0, 9.0), _p(box, 67.0, 14.0), light, maxf(1.4 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 94.0),
			Vector2(13.0, 63.0),
			Vector2(28.0, 51.0),
			Vector2(68.0, 51.0),
			Vector2(83.0, 63.0),
			Vector2(87.0, 94.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 94.0),
			Vector2(18.0, 66.0),
			Vector2(31.0, 55.0),
			Vector2(65.0, 55.0),
			Vector2(78.0, 66.0),
			Vector2(82.0, 94.0)
		],
		blue
	)
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 58.0),
			Vector2(11.0, 53.0),
			Vector2(6.0, 29.0),
			Vector2(17.0, 39.0),
			Vector2(22.0, 34.0),
			Vector2(29.0, 54.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 58.0),
			Vector2(85.0, 53.0),
			Vector2(90.0, 29.0),
			Vector2(79.0, 39.0),
			Vector2(74.0, 34.0),
			Vector2(67.0, 54.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 54.0),
			Vector2(14.0, 50.0),
			Vector2(10.0, 36.0),
			Vector2(20.0, 47.0),
			Vector2(23.0, 41.0),
			Vector2(27.0, 52.0)
		],
		silver
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 54.0),
			Vector2(82.0, 50.0),
			Vector2(86.0, 36.0),
			Vector2(76.0, 47.0),
			Vector2(73.0, 41.0),
			Vector2(69.0, 52.0)
		],
		silver
	)

	# Long pale hair sits behind a raised gorget and faceted plate armour.
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 21.0),
			Vector2(41.0, 15.0),
			Vector2(56.0, 16.0),
			Vector2(66.0, 25.0),
			Vector2(69.0, 64.0),
			Vector2(58.0, 70.0),
			Vector2(37.0, 67.0),
			Vector2(27.0, 59.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 23.0),
			Vector2(43.0, 18.0),
			Vector2(55.0, 19.0),
			Vector2(63.0, 27.0),
			Vector2(65.0, 62.0),
			Vector2(58.0, 65.0),
			Vector2(38.0, 63.0),
			Vector2(30.0, 57.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 63.0),
			Vector2(38.0, 55.0),
			Vector2(58.0, 55.0),
			Vector2(69.0, 63.0),
			Vector2(65.0, 93.0),
			Vector2(31.0, 93.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 65.0),
			Vector2(40.0, 59.0),
			Vector2(56.0, 59.0),
			Vector2(65.0, 65.0),
			Vector2(61.0, 91.0),
			Vector2(35.0, 91.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 64.0),
			Vector2(43.0, 60.0),
			Vector2(48.0, 74.0),
			Vector2(39.0, 84.0),
			Vector2(32.0, 76.0)
		],
		silver
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 64.0),
			Vector2(53.0, 60.0),
			Vector2(48.0, 74.0),
			Vector2(57.0, 84.0),
			Vector2(64.0, 76.0)
		],
		silver
	)
	canvas.draw_line(_p(box, 48.0, 74.0), _p(box, 48.0, 93.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 65.0),
			Vector2(27.0, 56.0),
			Vector2(38.0, 64.0),
			Vector2(29.0, 78.0),
			Vector2(15.0, 77.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(84.0, 65.0),
			Vector2(69.0, 56.0),
			Vector2(58.0, 64.0),
			Vector2(67.0, 78.0),
			Vector2(81.0, 77.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(16.0, 66.0),
			Vector2(27.0, 60.0),
			Vector2(33.0, 65.0),
			Vector2(27.0, 73.0),
			Vector2(18.0, 73.0)
		],
		silver
	)
	_fill(
		canvas,
		box,
		[
			Vector2(80.0, 66.0),
			Vector2(69.0, 60.0),
			Vector2(63.0, 65.0),
			Vector2(69.0, 73.0),
			Vector2(78.0, 73.0)
		],
		steel
	)

	# Unmasked face, steel brow band and a sunstone clasp.
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 28.0),
			Vector2(41.0, 22.0),
			Vector2(55.0, 23.0),
			Vector2(63.0, 30.0),
			Vector2(60.0, 46.0),
			Vector2(48.0, 56.0),
			Vector2(36.0, 46.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 30.0),
			Vector2(42.0, 25.0),
			Vector2(54.0, 26.0),
			Vector2(60.0, 31.0),
			Vector2(57.0, 44.0),
			Vector2(48.0, 52.0),
			Vector2(39.0, 44.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 30.0),
			Vector2(35.0, 21.0),
			Vector2(47.0, 18.0),
			Vector2(59.0, 22.0),
			Vector2(64.0, 31.0),
			Vector2(53.0, 27.0),
			Vector2(46.0, 23.0),
			Vector2(41.0, 32.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 28.0),
			Vector2(45.0, 25.0),
			Vector2(48.0, 29.0),
			Vector2(51.0, 25.0),
			Vector2(64.0, 28.0),
			Vector2(61.0, 33.0),
			Vector2(48.0, 35.0),
			Vector2(35.0, 33.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 38.0, 37.0), _p(box, 44.0, 38.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 38.0), _p(box, 58.0, 37.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 37.0), _p(box, 43.0, 37.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 37.0), _p(box, 57.0, 37.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 38.0), _p(box, 46.0, 44.0), shade, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 44.0, 47.0), _p(box, 52.0, 47.0), shade, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 50.0),
			Vector2(48.0, 57.0),
			Vector2(62.0, 50.0),
			Vector2(59.0, 61.0),
			Vector2(48.0, 67.0),
			Vector2(37.0, 61.0)
		],
		ink
	)
	canvas.draw_line(_p(box, 37.0, 55.0), _p(box, 48.0, 62.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 59.0, 55.0), _p(box, 48.0, 62.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 69.0), 5.0 * unit, ink)
	canvas.draw_circle(_p(box, 48.0, 69.0), 3.5 * unit, gold)
	canvas.draw_circle(_p(box, 48.0, 69.0), 1.5 * unit, light)

	# Upright sword and compact shield read clearly at card size.
	_fill(
		canvas,
		box,
		[
			Vector2(17.0, 42.0),
			Vector2(22.0, 50.0),
			Vector2(21.0, 81.0),
			Vector2(16.0, 81.0),
			Vector2(15.0, 50.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 46.0),
			Vector2(20.0, 51.0),
			Vector2(19.0, 79.0),
			Vector2(17.0, 79.0),
			Vector2(17.0, 51.0)
		],
		silver
	)
	canvas.draw_line(_p(box, 12.0, 80.0), _p(box, 26.0, 80.0), gold, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 19.0, 83.0), _p(box, 19.0, 91.0), ink, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 19.0, 83.0), _p(box, 19.0, 91.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 75.0),
			Vector2(79.0, 72.0),
			Vector2(89.0, 78.0),
			Vector2(85.0, 89.0),
			Vector2(77.0, 95.0),
			Vector2(67.0, 87.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(70.0, 78.0),
			Vector2(79.0, 75.0),
			Vector2(86.0, 79.0),
			Vector2(82.0, 87.0),
			Vector2(77.0, 92.0),
			Vector2(70.0, 86.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 78.0, 78.0), _p(box, 77.0, 88.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 73.0, 82.0), _p(box, 82.0, 82.0), light, maxf(2.0 * unit, 1.0), true)


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
