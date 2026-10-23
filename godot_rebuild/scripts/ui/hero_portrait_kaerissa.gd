extends RefCounted
## Native canvas portrait: Kaerissa, The Blood Assassin.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(30, 22, 32)
	var leather := Color8(65, 42, 52)
	var shade := Color8(45, 35, 48)
	var crimson := Color8(145, 39, 57)
	var blood := Color8(206, 49, 65)
	var darkred := Color8(91, 31, 48)
	var skin := Color8(190, 139, 132)
	var steel := Color8(183, 188, 198)
	var silver := Color8(117, 130, 145)
	var light := Color8(255, 210, 180)
	_backdrop(canvas, box, Color8(92, 36, 54), Color8(27, 23, 35))

	# A muted blood-moon and falling red motes frame the close-quarters killer.
	canvas.draw_circle(_p(box, 47.0, 38.0), 34.0 * unit, darkred)
	canvas.draw_arc(
		_p(box, 47.0, 38.0),
		34.0 * unit,
		PI * 0.7,
		PI * 1.8,
		48,
		crimson,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 15.0, 26.0), 1.5 * unit, blood)
	canvas.draw_circle(_p(box, 81.0, 20.0), 1.0 * unit, light)
	_fill(
		canvas,
		box,
		[Vector2(84.0, 36.0), Vector2(87.0, 30.0), Vector2(88.0, 38.0), Vector2(86.0, 41.0)],
		blood
	)

	# Fitted dark leathers and a split crimson scarf replace a heavy armour silhouette.
	_fill(
		canvas,
		box,
		[
			Vector2(5.0, 96.0),
			Vector2(11.0, 70.0),
			Vector2(30.0, 56.0),
			Vector2(63.0, 56.0),
			Vector2(83.0, 70.0),
			Vector2(92.0, 96.0)
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
			Vector2(61.0, 62.0),
			Vector2(77.0, 73.0),
			Vector2(85.0, 94.0)
		],
		leather
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 94.0),
			Vector2(19.0, 74.0),
			Vector2(31.0, 65.0),
			Vector2(42.0, 77.0),
			Vector2(34.0, 94.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(52.0, 76.0),
			Vector2(62.0, 64.0),
			Vector2(76.0, 74.0),
			Vector2(83.0, 94.0),
			Vector2(60.0, 94.0)
		],
		darkred
	)
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 58.0),
			Vector2(38.0, 57.0),
			Vector2(48.0, 67.0),
			Vector2(60.0, 57.0),
			Vector2(69.0, 60.0),
			Vector2(57.0, 77.0),
			Vector2(45.0, 82.0),
			Vector2(34.0, 73.0)
		],
		crimson
	)
	_fill(
		canvas,
		box,
		[
			Vector2(45.0, 76.0),
			Vector2(57.0, 70.0),
			Vector2(65.0, 92.0),
			Vector2(55.0, 88.0),
			Vector2(52.0, 96.0),
			Vector2(43.0, 96.0)
		],
		blood
	)
	canvas.draw_line(_p(box, 27.0, 74.0), _p(box, 41.0, 88.0), silver, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 65.0, 75.0), _p(box, 56.0, 86.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 40.0, 87.0), 2.0 * unit, steel)
	canvas.draw_circle(_p(box, 57.0, 86.0), 2.0 * unit, steel)

	# Small layered shoulder guards preserve the assassin's narrow, agile outline.
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 70.0),
			Vector2(15.0, 56.0),
			Vector2(26.0, 53.0),
			Vector2(36.0, 64.0),
			Vector2(30.0, 75.0),
			Vector2(16.0, 79.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 68.0),
			Vector2(20.0, 60.0),
			Vector2(26.0, 59.0),
			Vector2(31.0, 65.0),
			Vector2(27.0, 70.0),
			Vector2(19.0, 73.0)
		],
		leather
	)
	canvas.draw_line(_p(box, 18.0, 63.0), _p(box, 28.0, 66.0), crimson, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(59.0, 64.0),
			Vector2(69.0, 53.0),
			Vector2(80.0, 57.0),
			Vector2(87.0, 70.0),
			Vector2(80.0, 79.0),
			Vector2(65.0, 75.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(65.0, 65.0),
			Vector2(70.0, 59.0),
			Vector2(77.0, 60.0),
			Vector2(82.0, 68.0),
			Vector2(77.0, 73.0),
			Vector2(69.0, 70.0)
		],
		leather
	)
	canvas.draw_line(_p(box, 69.0, 65.0), _p(box, 79.0, 62.0), crimson, maxf(2.0 * unit, 1.0), true)

	# A pointed hood, loose side locks and a red half-mask conceal the face.
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 50.0),
			Vector2(22.0, 29.0),
			Vector2(30.0, 13.0),
			Vector2(46.0, 6.0),
			Vector2(63.0, 13.0),
			Vector2(73.0, 29.0),
			Vector2(69.0, 51.0),
			Vector2(59.0, 61.0),
			Vector2(35.0, 60.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 46.0),
			Vector2(28.0, 30.0),
			Vector2(35.0, 19.0),
			Vector2(47.0, 13.0),
			Vector2(59.0, 19.0),
			Vector2(67.0, 31.0),
			Vector2(64.0, 47.0),
			Vector2(57.0, 54.0),
			Vector2(38.0, 54.0)
		],
		crimson
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 31.0),
			Vector2(39.0, 22.0),
			Vector2(55.0, 22.0),
			Vector2(63.0, 31.0),
			Vector2(61.0, 46.0),
			Vector2(54.0, 56.0),
			Vector2(42.0, 56.0),
			Vector2(34.0, 46.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 32.0),
			Vector2(42.0, 27.0),
			Vector2(54.0, 26.0),
			Vector2(59.0, 32.0),
			Vector2(58.0, 43.0),
			Vector2(53.0, 49.0),
			Vector2(43.0, 50.0),
			Vector2(38.0, 44.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 29.0),
			Vector2(39.0, 24.0),
			Vector2(38.0, 43.0),
			Vector2(42.0, 53.0),
			Vector2(35.0, 49.0),
			Vector2(31.0, 39.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 25.0),
			Vector2(63.0, 32.0),
			Vector2(62.0, 45.0),
			Vector2(55.0, 54.0),
			Vector2(58.0, 42.0)
		],
		darkred
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 31.0),
			Vector2(35.0, 18.0),
			Vector2(47.0, 12.0),
			Vector2(60.0, 18.0),
			Vector2(67.0, 31.0),
			Vector2(57.0, 26.0),
			Vector2(47.0, 23.0),
			Vector2(37.0, 27.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(44.0, 24.0), Vector2(48.0, 19.0), Vector2(52.0, 24.0), Vector2(48.0, 29.0)],
		blood
	)
	canvas.draw_circle(_p(box, 48.0, 23.0), 1.2 * unit, light)
	canvas.draw_line(_p(box, 37.0, 34.0), _p(box, 44.0, 36.0), ink, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 36.0), _p(box, 59.0, 33.0), ink, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 37.0), _p(box, 44.0, 38.0), light, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 38.0), _p(box, 57.0, 36.0), blood, maxf(1.8 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 41.0),
			Vector2(46.0, 44.0),
			Vector2(58.0, 40.0),
			Vector2(57.0, 50.0),
			Vector2(51.0, 56.0),
			Vector2(42.0, 54.0),
			Vector2(38.0, 49.0)
		],
		darkred
	)
	_fill(
		canvas,
		box,
		[
			Vector2(41.0, 45.0),
			Vector2(47.0, 47.0),
			Vector2(54.0, 44.0),
			Vector2(52.0, 50.0),
			Vector2(47.0, 53.0),
			Vector2(43.0, 50.0)
		],
		crimson
	)
	canvas.draw_line(_p(box, 43.0, 49.0), _p(box, 51.0, 49.0), ink, maxf(1.2 * unit, 1.0), true)

	# Twin outward-curved daggers and wrapped grips identify the melee role.
	canvas.draw_line(_p(box, 16.0, 60.0), _p(box, 23.0, 87.0), ink, maxf(8.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 16.0, 60.0), _p(box, 23.0, 87.0), leather, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 81.0, 60.0), _p(box, 73.0, 87.0), ink, maxf(8.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 81.0, 60.0), _p(box, 73.0, 87.0), leather, maxf(4.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 64.0),
			Vector2(5.0, 48.0),
			Vector2(8.0, 34.0),
			Vector2(15.0, 47.0),
			Vector2(19.0, 62.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 57.0),
			Vector2(9.0, 47.0),
			Vector2(9.0, 41.0),
			Vector2(13.0, 49.0),
			Vector2(15.0, 58.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[Vector2(9.0, 42.0), Vector2(11.0, 48.0), Vector2(13.0, 54.0), Vector2(10.0, 48.0)],
		light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(78.0, 62.0),
			Vector2(82.0, 47.0),
			Vector2(90.0, 34.0),
			Vector2(92.0, 48.0),
			Vector2(85.0, 64.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(82.0, 58.0),
			Vector2(85.0, 48.0),
			Vector2(89.0, 41.0),
			Vector2(89.0, 49.0),
			Vector2(85.0, 58.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[Vector2(88.0, 43.0), Vector2(89.0, 40.0), Vector2(89.0, 49.0), Vector2(86.0, 55.0)],
		light
	)
	canvas.draw_line(_p(box, 9.0, 64.0), _p(box, 23.0, 58.0), ink, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 10.0, 63.0), _p(box, 22.0, 58.0), crimson, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 74.0, 58.0), _p(box, 88.0, 64.0), ink, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 75.0, 58.0), _p(box, 87.0, 63.0), crimson, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 18.0, 71.0), _p(box, 23.0, 70.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 20.0, 77.0), _p(box, 25.0, 76.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 74.0, 70.0), _p(box, 79.0, 71.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 72.0, 76.0), _p(box, 77.0, 77.0), silver, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(6.0, 30.0), Vector2(8.0, 25.0), Vector2(10.0, 31.0), Vector2(8.0, 33.0)],
		blood
	)
	canvas.draw_circle(_p(box, 91.0, 72.0), 1.2 * unit, blood)


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
