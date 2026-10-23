extends RefCounted
## Native canvas portrait: Akiraze, The Golden Tempest / Golden Ninja.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(29, 26, 24)
	var cloth := Color8(49, 51, 48)
	var shadow := Color8(91, 66, 31)
	var gold := Color8(210, 158, 45)
	var light := Color8(255, 225, 136)
	var skin := Color8(210, 164, 117)
	var steel := Color8(181, 197, 182)
	_backdrop(canvas, box, Color8(94, 79, 32), Color8(23, 30, 29))

	# Golden gusts and a swept scarf imply the tempest without animation.
	canvas.draw_arc(
		_p(box, 47.0, 46.0),
		37.0 * unit,
		PI * -0.93,
		PI * -0.15,
		32,
		gold,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 49.0),
		41.0 * unit,
		PI * 0.12,
		PI * 0.83,
		32,
		shadow,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 9.0, 40.0), _p(box, 25.0, 34.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 8.0, 48.0), _p(box, 20.0, 44.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 70.0, 16.0), _p(box, 86.0, 13.0), light, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(60.0, 42.0),
			Vector2(72.0, 35.0),
			Vector2(88.0, 37.0),
			Vector2(81.0, 44.0),
			Vector2(91.0, 49.0),
			Vector2(76.0, 53.0),
			Vector2(59.0, 50.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(64.0, 43.0),
			Vector2(74.0, 39.0),
			Vector2(83.0, 39.0),
			Vector2(77.0, 44.0),
			Vector2(85.0, 47.0),
			Vector2(75.0, 49.0),
			Vector2(64.0, 47.0)
		],
		gold
	)

	# Short crossed blades behind a narrow, layered ninja silhouette.
	canvas.draw_line(_p(box, 20.0, 25.0), _p(box, 71.0, 88.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 20.0, 25.0), _p(box, 71.0, 88.0), steel, maxf(2.0 * unit, 1.0), true)
	_fill(canvas, box, [Vector2(15.0, 18.0), Vector2(23.0, 22.0), Vector2(24.0, 31.0)], light)
	canvas.draw_line(_p(box, 76.0, 24.0), _p(box, 29.0, 87.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 76.0, 24.0), _p(box, 29.0, 87.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(canvas, box, [Vector2(81.0, 17.0), Vector2(79.0, 30.0), Vector2(72.0, 26.0)], steel)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 96.0),
			Vector2(19.0, 73.0),
			Vector2(32.0, 61.0),
			Vector2(61.0, 60.0),
			Vector2(76.0, 73.0),
			Vector2(83.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 94.0),
			Vector2(24.0, 74.0),
			Vector2(34.0, 65.0),
			Vector2(59.0, 64.0),
			Vector2(71.0, 75.0),
			Vector2(78.0, 94.0)
		],
		cloth
	)
	_fill(
		canvas,
		box,
		[
			Vector2(23.0, 74.0),
			Vector2(34.0, 65.0),
			Vector2(43.0, 68.0),
			Vector2(34.0, 81.0),
			Vector2(23.0, 84.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 74.0),
			Vector2(61.0, 65.0),
			Vector2(52.0, 68.0),
			Vector2(61.0, 81.0),
			Vector2(73.0, 84.0)
		],
		shadow
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 26.0),
			Vector2(37.0, 18.0),
			Vector2(55.0, 16.0),
			Vector2(65.0, 26.0),
			Vector2(67.0, 43.0),
			Vector2(58.0, 58.0),
			Vector2(42.0, 61.0),
			Vector2(31.0, 49.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 28.0),
			Vector2(39.0, 22.0),
			Vector2(54.0, 20.0),
			Vector2(61.0, 28.0),
			Vector2(63.0, 42.0),
			Vector2(55.0, 54.0),
			Vector2(43.0, 57.0),
			Vector2(35.0, 47.0)
		],
		cloth
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 29.0),
			Vector2(31.0, 20.0),
			Vector2(38.0, 22.0),
			Vector2(41.0, 11.0),
			Vector2(47.0, 18.0),
			Vector2(55.0, 10.0),
			Vector2(57.0, 20.0),
			Vector2(66.0, 19.0),
			Vector2(63.0, 31.0),
			Vector2(53.0, 26.0),
			Vector2(41.0, 29.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(39.0, 24.0),
			Vector2(43.0, 17.0),
			Vector2(47.0, 23.0),
			Vector2(54.0, 16.0),
			Vector2(54.0, 24.0),
			Vector2(47.0, 27.0)
		],
		light
	)

	# A gold brow plate leaves only a sharp diagonal eye opening exposed.
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 30.0),
			Vector2(46.0, 27.0),
			Vector2(63.0, 30.0),
			Vector2(62.0, 36.0),
			Vector2(47.0, 33.0),
			Vector2(34.0, 36.0)
		],
		shadow
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 31.0),
			Vector2(47.0, 29.0),
			Vector2(60.0, 31.0),
			Vector2(59.0, 33.0),
			Vector2(47.0, 31.0),
			Vector2(36.0, 34.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 37.0),
			Vector2(46.0, 35.0),
			Vector2(61.0, 37.0),
			Vector2(58.0, 43.0),
			Vector2(47.0, 45.0),
			Vector2(37.0, 42.0)
		],
		skin
	)
	canvas.draw_line(_p(box, 38.0, 38.0), _p(box, 44.0, 39.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 39.0), _p(box, 58.0, 37.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 40.0), _p(box, 43.0, 40.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 40.0), _p(box, 57.0, 39.0), light, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 43.0),
			Vector2(47.0, 46.0),
			Vector2(61.0, 42.0),
			Vector2(57.0, 53.0),
			Vector2(47.0, 58.0),
			Vector2(38.0, 52.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(38.0, 45.0),
			Vector2(47.0, 49.0),
			Vector2(58.0, 45.0),
			Vector2(54.0, 52.0),
			Vector2(47.0, 55.0),
			Vector2(40.0, 50.0)
		],
		cloth
	)
	canvas.draw_line(_p(box, 41.0, 49.0), _p(box, 51.0, 52.0), gold, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 53.0),
			Vector2(45.0, 60.0),
			Vector2(62.0, 53.0),
			Vector2(64.0, 62.0),
			Vector2(48.0, 70.0),
			Vector2(33.0, 63.0)
		],
		shadow
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 57.0),
			Vector2(46.0, 64.0),
			Vector2(60.0, 57.0),
			Vector2(60.0, 61.0),
			Vector2(48.0, 67.0),
			Vector2(36.0, 61.0)
		],
		gold
	)
	canvas.draw_line(_p(box, 37.0, 59.0), _p(box, 47.0, 64.0), light, maxf(1.5 * unit, 1.0), true)

	# Diagonal harness, shuriken clasp and plated forearms complete the kit.
	canvas.draw_line(_p(box, 31.0, 69.0), _p(box, 63.0, 94.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 31.0, 69.0), _p(box, 63.0, 94.0), gold, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(48.0, 72.0),
			Vector2(51.0, 78.0),
			Vector2(58.0, 80.0),
			Vector2(51.0, 82.0),
			Vector2(48.0, 89.0),
			Vector2(46.0, 82.0),
			Vector2(39.0, 80.0),
			Vector2(46.0, 78.0)
		],
		steel
	)
	canvas.draw_circle(_p(box, 48.0, 80.0), 2.0 * unit, ink)
	_fill(
		canvas,
		box,
		[Vector2(21.0, 82.0), Vector2(32.0, 78.0), Vector2(39.0, 94.0), Vector2(22.0, 96.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(24.0, 84.0), Vector2(30.0, 82.0), Vector2(35.0, 92.0), Vector2(25.0, 93.0)],
		gold
	)
	canvas.draw_line(_p(box, 25.0, 86.0), _p(box, 31.0, 85.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 26.0, 90.0), _p(box, 33.0, 88.0), shadow, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(65.0, 79.0), Vector2(76.0, 83.0), Vector2(76.0, 96.0), Vector2(59.0, 94.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(67.0, 83.0), Vector2(73.0, 85.0), Vector2(73.0, 93.0), Vector2(63.0, 91.0)],
		gold
	)
	canvas.draw_line(_p(box, 66.0, 86.0), _p(box, 72.0, 88.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 65.0, 89.0), _p(box, 72.0, 91.0), shadow, maxf(1.5 * unit, 1.0), true)


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
