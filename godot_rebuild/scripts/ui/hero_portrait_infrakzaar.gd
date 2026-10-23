extends RefCounted
## Native canvas portrait: Infrakzaar, The Emberflesh Pyromancer.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(39, 27, 29)
	var flesh := Color8(128, 64, 51)
	var shade := Color8(78, 44, 44)
	var plate := Color8(68, 59, 57)
	var ash := Color8(155, 130, 104)
	var ember := Color8(239, 112, 45)
	var light := Color8(255, 217, 116)
	var red := Color8(178, 53, 37)
	var bone := Color8(203, 177, 127)
	_backdrop(canvas, box, Color8(101, 45, 34), Color8(30, 24, 30))

	# Rising flame tongues silhouette an exposed ember-cracked spellcaster.
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 62.0),
			Vector2(7.0, 44.0),
			Vector2(15.0, 27.0),
			Vector2(18.0, 43.0),
			Vector2(27.0, 21.0),
			Vector2(29.0, 12.0),
			Vector2(39.0, 29.0),
			Vector2(47.0, 10.0),
			Vector2(56.0, 28.0),
			Vector2(66.0, 15.0),
			Vector2(68.0, 36.0),
			Vector2(78.0, 25.0),
			Vector2(76.0, 42.0),
			Vector2(89.0, 34.0),
			Vector2(87.0, 61.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 61.0),
			Vector2(13.0, 45.0),
			Vector2(16.0, 38.0),
			Vector2(19.0, 49.0),
			Vector2(30.0, 30.0),
			Vector2(32.0, 24.0),
			Vector2(41.0, 37.0),
			Vector2(47.0, 24.0),
			Vector2(55.0, 39.0),
			Vector2(63.0, 28.0),
			Vector2(64.0, 46.0),
			Vector2(74.0, 36.0),
			Vector2(71.0, 51.0),
			Vector2(82.0, 43.0),
			Vector2(81.0, 61.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(6.0, 96.0),
			Vector2(11.0, 69.0),
			Vector2(29.0, 54.0),
			Vector2(61.0, 54.0),
			Vector2(82.0, 69.0),
			Vector2(91.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 94.0),
			Vector2(17.0, 72.0),
			Vector2(31.0, 60.0),
			Vector2(59.0, 60.0),
			Vector2(76.0, 72.0),
			Vector2(85.0, 94.0)
		],
		flesh
	)
	_fill(
		canvas,
		box,
		[
			Vector2(49.0, 61.0),
			Vector2(61.0, 64.0),
			Vector2(75.0, 75.0),
			Vector2(82.0, 94.0),
			Vector2(50.0, 94.0)
		],
		shade
	)

	# Charred shoulder crusts break around glowing seams, leaving the torso bare.
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 68.0),
			Vector2(14.0, 54.0),
			Vector2(23.0, 48.0),
			Vector2(35.0, 57.0),
			Vector2(39.0, 70.0),
			Vector2(30.0, 82.0),
			Vector2(15.0, 79.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 68.0),
			Vector2(19.0, 58.0),
			Vector2(24.0, 54.0),
			Vector2(31.0, 61.0),
			Vector2(34.0, 69.0),
			Vector2(28.0, 76.0),
			Vector2(18.0, 75.0)
		],
		plate
	)
	canvas.draw_line(_p(box, 20.0, 57.0), _p(box, 23.0, 64.0), ember, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 23.0, 64.0), _p(box, 29.0, 66.0), light, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(57.0, 69.0),
			Vector2(63.0, 56.0),
			Vector2(73.0, 49.0),
			Vector2(82.0, 55.0),
			Vector2(88.0, 69.0),
			Vector2(81.0, 80.0),
			Vector2(65.0, 81.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 69.0),
			Vector2(67.0, 60.0),
			Vector2(74.0, 55.0),
			Vector2(78.0, 60.0),
			Vector2(82.0, 69.0),
			Vector2(77.0, 76.0),
			Vector2(67.0, 76.0)
		],
		plate
	)
	canvas.draw_line(_p(box, 74.0, 57.0), _p(box, 72.0, 65.0), ember, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 72.0, 65.0), _p(box, 77.0, 69.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 33.0, 72.0), _p(box, 44.0, 77.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 77.0), _p(box, 63.0, 72.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 65.0), _p(box, 41.0, 71.0), ember, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 41.0, 71.0), _p(box, 37.0, 80.0), ember, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 58.0, 66.0), _p(box, 53.0, 72.0), ember, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 72.0), _p(box, 56.0, 78.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 45.0, 80.0), _p(box, 48.0, 85.0), red, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 85.0), _p(box, 46.0, 93.0), ember, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 88.0),
			Vector2(38.0, 85.0),
			Vector2(46.0, 89.0),
			Vector2(57.0, 85.0),
			Vector2(67.0, 89.0),
			Vector2(70.0, 96.0),
			Vector2(24.0, 96.0)
		],
		plate
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 29.0),
			Vector2(35.0, 19.0),
			Vector2(56.0, 18.0),
			Vector2(66.0, 29.0),
			Vector2(64.0, 46.0),
			Vector2(56.0, 58.0),
			Vector2(40.0, 60.0),
			Vector2(30.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 31.0),
			Vector2(39.0, 24.0),
			Vector2(54.0, 23.0),
			Vector2(60.0, 31.0),
			Vector2(58.0, 45.0),
			Vector2(53.0, 54.0),
			Vector2(42.0, 54.0),
			Vector2(36.0, 46.0)
		],
		flesh
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 25.0),
			Vector2(58.0, 31.0),
			Vector2(60.0, 36.0),
			Vector2(57.0, 46.0),
			Vector2(52.0, 52.0),
			Vector2(48.0, 48.0)
		],
		shade
	)

	# A bald volcanic brow, blunt basalt horns and ember eyes replace robe and cowl.
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 30.0),
			Vector2(24.0, 12.0),
			Vector2(34.0, 18.0),
			Vector2(39.0, 24.0),
			Vector2(54.0, 23.0),
			Vector2(62.0, 16.0),
			Vector2(69.0, 11.0),
			Vector2(64.0, 32.0),
			Vector2(55.0, 30.0),
			Vector2(39.0, 31.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 27.0),
			Vector2(28.0, 19.0),
			Vector2(33.0, 22.0),
			Vector2(38.0, 28.0),
			Vector2(44.0, 26.0),
			Vector2(52.0, 27.0),
			Vector2(60.0, 23.0),
			Vector2(64.0, 18.0),
			Vector2(61.0, 28.0),
			Vector2(54.0, 28.0),
			Vector2(40.0, 29.0)
		],
		plate
	)
	canvas.draw_line(_p(box, 31.0, 24.0), _p(box, 34.0, 26.0), ash, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 58.0, 26.0), _p(box, 62.0, 22.0), ash, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 35.0, 36.0), _p(box, 43.0, 38.0), ink, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 38.0), _p(box, 59.0, 35.0), ink, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 40.0), _p(box, 42.0, 40.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 40.0), _p(box, 57.0, 39.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 43.0, 27.0), _p(box, 45.0, 33.0), ember, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 45.0, 33.0), _p(box, 42.0, 38.0), ember, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 55.0, 43.0), _p(box, 52.0, 48.0), ember, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 43.0), _p(box, 40.0, 48.0), red, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 38.0), _p(box, 45.0, 45.0), flesh, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 40.0, 50.0), _p(box, 54.0, 49.0), ink, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(39.0, 53.0),
			Vector2(46.0, 55.0),
			Vector2(55.0, 51.0),
			Vector2(53.0, 57.0),
			Vector2(43.0, 59.0)
		],
		plate
	)

	# Two open hands conjure cinders without a staff or martial weapon.
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 92.0),
			Vector2(9.0, 79.0),
			Vector2(14.0, 75.0),
			Vector2(15.0, 66.0),
			Vector2(19.0, 64.0),
			Vector2(22.0, 75.0),
			Vector2(26.0, 68.0),
			Vector2(30.0, 69.0),
			Vector2(29.0, 80.0),
			Vector2(35.0, 78.0),
			Vector2(37.0, 82.0),
			Vector2(29.0, 91.0),
			Vector2(23.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 90.0),
			Vector2(14.0, 81.0),
			Vector2(18.0, 79.0),
			Vector2(18.0, 69.0),
			Vector2(19.0, 69.0),
			Vector2(21.0, 81.0),
			Vector2(25.0, 78.0),
			Vector2(28.0, 72.0),
			Vector2(26.0, 82.0),
			Vector2(32.0, 82.0),
			Vector2(26.0, 88.0),
			Vector2(21.0, 92.0)
		],
		flesh
	)
	_fill(
		canvas,
		box,
		[
			Vector2(60.0, 82.0),
			Vector2(67.0, 79.0),
			Vector2(65.0, 69.0),
			Vector2(69.0, 67.0),
			Vector2(74.0, 75.0),
			Vector2(76.0, 64.0),
			Vector2(80.0, 64.0),
			Vector2(81.0, 75.0),
			Vector2(87.0, 78.0),
			Vector2(88.0, 92.0),
			Vector2(77.0, 96.0),
			Vector2(67.0, 91.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(65.0, 83.0),
			Vector2(71.0, 82.0),
			Vector2(69.0, 72.0),
			Vector2(73.0, 80.0),
			Vector2(78.0, 79.0),
			Vector2(78.0, 69.0),
			Vector2(79.0, 69.0),
			Vector2(79.0, 82.0),
			Vector2(83.0, 83.0),
			Vector2(83.0, 90.0),
			Vector2(77.0, 92.0),
			Vector2(70.0, 88.0)
		],
		flesh
	)
	canvas.draw_circle(_p(box, 21.0, 56.0), 8.0 * unit, red)
	canvas.draw_circle(_p(box, 21.0, 56.0), 5.0 * unit, ember)
	canvas.draw_circle(_p(box, 21.0, 56.0), 2.5 * unit, light)
	canvas.draw_circle(_p(box, 77.0, 55.0), 8.0 * unit, red)
	canvas.draw_circle(_p(box, 77.0, 55.0), 5.0 * unit, ember)
	canvas.draw_circle(_p(box, 77.0, 55.0), 2.5 * unit, light)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 51.0),
			Vector2(17.0, 42.0),
			Vector2(22.0, 47.0),
			Vector2(26.0, 39.0),
			Vector2(26.0, 49.0),
			Vector2(23.0, 54.0)
		],
		ember
	)
	_fill(
		canvas,
		box,
		[
			Vector2(73.0, 50.0),
			Vector2(71.0, 43.0),
			Vector2(77.0, 46.0),
			Vector2(80.0, 37.0),
			Vector2(82.0, 48.0),
			Vector2(79.0, 52.0)
		],
		ember
	)
	canvas.draw_line(_p(box, 14.0, 89.0), _p(box, 23.0, 93.0), bone, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 73.0, 93.0), _p(box, 83.0, 90.0), bone, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 11.0, 40.0), 1.0 * unit, light)
	canvas.draw_circle(_p(box, 87.0, 28.0), 1.3 * unit, ember)


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
