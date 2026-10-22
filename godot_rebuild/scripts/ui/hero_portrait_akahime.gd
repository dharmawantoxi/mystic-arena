extends RefCounted
## Native canvas portrait: Akahime, The Scarlet Blossom / Scarlet Kunoichi.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(28, 15, 34)
	var cloth := Color8(56, 33, 58)
	var scarlet := Color8(168, 37, 68)
	var rose := Color8(236, 91, 124)
	var petal := Color8(255, 183, 196)
	var skin := Color8(232, 181, 165)
	var hair := Color8(35, 27, 46)
	var steel := Color8(175, 185, 211)
	var gold := Color8(221, 174, 113)
	_backdrop(canvas, box, Color8(99, 37, 65), Color8(28, 17, 39))

	# Scarlet moon, airborne petals, and crossed kunai behind the shoulders.
	canvas.draw_circle(_p(box, 48.0, 32.0), 26.0 * unit, scarlet)
	canvas.draw_arc(
		_p(box, 48.0, 32.0),
		29.0 * unit,
		PI * -0.93,
		PI * -0.12,
		32,
		rose,
		maxf(1.0 * unit, 1.0),
		true
	)
	_fill(
		canvas,
		box,
		[Vector2(12.0, 24.0), Vector2(18.0, 20.0), Vector2(20.0, 25.0), Vector2(15.0, 29.0)],
		petal
	)
	_fill(
		canvas,
		box,
		[Vector2(77.0, 15.0), Vector2(82.0, 12.0), Vector2(85.0, 17.0), Vector2(80.0, 21.0)],
		petal
	)
	_fill(
		canvas,
		box,
		[Vector2(81.0, 45.0), Vector2(87.0, 42.0), Vector2(89.0, 46.0), Vector2(85.0, 51.0)],
		petal
	)
	_fill(
		canvas,
		box,
		[Vector2(10.0, 57.0), Vector2(15.0, 54.0), Vector2(18.0, 58.0), Vector2(14.0, 62.0)],
		petal
	)
	canvas.draw_line(_p(box, 17.0, 35.0), _p(box, 70.0, 87.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 17.0, 35.0), _p(box, 70.0, 87.0), steel, maxf(2.0 * unit, 1.0), true)
	_fill(canvas, box, [Vector2(10.0, 26.0), Vector2(23.0, 32.0), Vector2(21.0, 40.0)], steel)
	canvas.draw_line(_p(box, 78.0, 32.0), _p(box, 25.0, 87.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 32.0), _p(box, 25.0, 87.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(canvas, box, [Vector2(86.0, 22.0), Vector2(82.0, 37.0), Vector2(74.0, 31.0)], steel)

	# High tied hair and a loose side lock give the kunoichi an asymmetric silhouette.
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 25.0),
			Vector2(57.0, 10.0),
			Vector2(70.0, 7.0),
			Vector2(78.0, 15.0),
			Vector2(77.0, 27.0),
			Vector2(68.0, 40.0),
			Vector2(71.0, 50.0),
			Vector2(62.0, 45.0),
			Vector2(61.0, 30.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(55.0, 25.0),
			Vector2(60.0, 13.0),
			Vector2(69.0, 11.0),
			Vector2(74.0, 17.0),
			Vector2(72.0, 28.0),
			Vector2(65.0, 37.0),
			Vector2(66.0, 27.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 60.0, 15.0), _p(box, 72.0, 19.0), rose, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 96.0),
			Vector2(19.0, 73.0),
			Vector2(32.0, 61.0),
			Vector2(61.0, 59.0),
			Vector2(76.0, 72.0),
			Vector2(84.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 94.0),
			Vector2(23.0, 75.0),
			Vector2(34.0, 65.0),
			Vector2(59.0, 63.0),
			Vector2(72.0, 75.0),
			Vector2(79.0, 94.0)
		],
		cloth
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 65.0),
			Vector2(44.0, 69.0),
			Vector2(38.0, 94.0),
			Vector2(23.0, 94.0),
			Vector2(25.0, 76.0)
		],
		scarlet
	)
	_fill(
		canvas,
		box,
		[
			Vector2(60.0, 64.0),
			Vector2(68.0, 73.0),
			Vector2(72.0, 94.0),
			Vector2(57.0, 94.0),
			Vector2(48.0, 73.0)
		],
		scarlet
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 28.0),
			Vector2(39.0, 19.0),
			Vector2(53.0, 18.0),
			Vector2(64.0, 26.0),
			Vector2(65.0, 42.0),
			Vector2(58.0, 55.0),
			Vector2(42.0, 58.0),
			Vector2(31.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 30.0),
			Vector2(42.0, 24.0),
			Vector2(53.0, 23.0),
			Vector2(60.0, 29.0),
			Vector2(61.0, 41.0),
			Vector2(55.0, 50.0),
			Vector2(45.0, 53.0),
			Vector2(36.0, 44.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 32.0),
			Vector2(33.0, 23.0),
			Vector2(42.0, 17.0),
			Vector2(55.0, 18.0),
			Vector2(64.0, 26.0),
			Vector2(64.0, 38.0),
			Vector2(56.0, 30.0),
			Vector2(48.0, 26.0),
			Vector2(44.0, 36.0),
			Vector2(42.0, 28.0),
			Vector2(34.0, 39.0),
			Vector2(35.0, 54.0),
			Vector2(29.0, 48.0)
		],
		hair
	)

	# Ruby brow ribbon, keen eyes and a folded face veil.
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 30.0),
			Vector2(44.0, 28.0),
			Vector2(58.0, 29.0),
			Vector2(62.0, 33.0),
			Vector2(59.0, 36.0),
			Vector2(44.0, 32.0),
			Vector2(34.0, 35.0)
		],
		scarlet
	)
	canvas.draw_line(_p(box, 37.0, 38.0), _p(box, 44.0, 39.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 39.0), _p(box, 58.0, 37.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 39.0), _p(box, 43.0, 39.0), petal, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 39.0), _p(box, 57.0, 38.0), petal, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 43.0),
			Vector2(46.0, 45.0),
			Vector2(61.0, 41.0),
			Vector2(58.0, 51.0),
			Vector2(48.0, 57.0),
			Vector2(38.0, 51.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(38.0, 45.0),
			Vector2(47.0, 48.0),
			Vector2(58.0, 44.0),
			Vector2(55.0, 50.0),
			Vector2(48.0, 54.0),
			Vector2(40.0, 50.0)
		],
		cloth
	)
	canvas.draw_line(_p(box, 41.0, 48.0), _p(box, 51.0, 51.0), rose, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 54.0),
			Vector2(46.0, 60.0),
			Vector2(61.0, 53.0),
			Vector2(63.0, 62.0),
			Vector2(48.0, 70.0),
			Vector2(32.0, 63.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 57.0),
			Vector2(46.0, 63.0),
			Vector2(59.0, 57.0),
			Vector2(59.0, 61.0),
			Vector2(48.0, 66.0),
			Vector2(35.0, 61.0)
		],
		scarlet
	)
	_fill(
		canvas,
		box,
		[
			Vector2(61.0, 58.0),
			Vector2(77.0, 55.0),
			Vector2(88.0, 62.0),
			Vector2(77.0, 62.0),
			Vector2(87.0, 73.0),
			Vector2(71.0, 68.0),
			Vector2(59.0, 62.0)
		],
		rose
	)
	canvas.draw_line(_p(box, 66.0, 60.0), _p(box, 76.0, 60.0), petal, maxf(1.5 * unit, 1.0), true)

	# Five-petal hair ornament and layered forearm guards finish the silhouette.
	canvas.draw_circle(_p(box, 32.0, 26.0), 3.0 * unit, rose)
	canvas.draw_circle(_p(box, 36.0, 28.0), 3.0 * unit, rose)
	canvas.draw_circle(_p(box, 35.0, 33.0), 3.0 * unit, rose)
	canvas.draw_circle(_p(box, 30.0, 33.0), 3.0 * unit, rose)
	canvas.draw_circle(_p(box, 28.0, 29.0), 3.0 * unit, rose)
	canvas.draw_circle(_p(box, 32.0, 30.0), 2.0 * unit, gold)
	_fill(
		canvas,
		box,
		[
			Vector2(22.0, 77.0),
			Vector2(32.0, 74.0),
			Vector2(39.0, 90.0),
			Vector2(33.0, 96.0),
			Vector2(20.0, 94.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 80.0),
			Vector2(30.0, 78.0),
			Vector2(35.0, 90.0),
			Vector2(31.0, 93.0),
			Vector2(23.0, 91.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(70.0, 76.0),
			Vector2(78.0, 81.0),
			Vector2(79.0, 94.0),
			Vector2(64.0, 96.0),
			Vector2(61.0, 88.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(71.0, 80.0),
			Vector2(75.0, 83.0),
			Vector2(76.0, 91.0),
			Vector2(66.0, 93.0),
			Vector2(65.0, 88.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 24.0, 83.0), _p(box, 32.0, 85.0), cloth, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 68.0, 83.0), _p(box, 75.0, 85.0), cloth, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 24.0, 88.0), _p(box, 32.0, 90.0), cloth, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 68.0, 88.0), _p(box, 75.0, 90.0), cloth, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 73.0), _p(box, 57.0, 88.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 57.0, 73.0), _p(box, 40.0, 88.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 81.0), 4.0 * unit, ink)
	canvas.draw_circle(_p(box, 48.0, 81.0), 2.0 * unit, rose)


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
