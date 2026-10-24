extends RefCounted
## Native canvas portrait: Zhyvrek, The Void Reaper.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(18, 20, 34)
	var cloak := Color8(43, 43, 72)
	var shade := Color8(31, 34, 57)
	var violet := Color8(91, 62, 126)
	var rift := Color8(153, 88, 193)
	var wisp := Color8(84, 196, 196)
	var bone := Color8(177, 187, 183)
	var steel := Color8(133, 157, 174)
	var light := Color8(213, 245, 224)
	_backdrop(canvas, box, Color8(43, 42, 73), Color8(15, 20, 34))

	# A huge crescent scythe sits behind the reaper, its haft clear of the face.
	canvas.draw_line(_p(box, 73.0, 96.0), _p(box, 82.0, 28.0), ink, maxf(9.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 73.0, 96.0), _p(box, 82.0, 28.0), steel, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(83.0, 31.0),
			Vector2(66.0, 14.0),
			Vector2(45.0, 5.0),
			Vector2(27.0, 4.0),
			Vector2(39.0, 13.0),
			Vector2(56.0, 25.0),
			Vector2(75.0, 37.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 29.0),
			Vector2(64.0, 18.0),
			Vector2(46.0, 10.0),
			Vector2(38.0, 9.0),
			Vector2(48.0, 17.0),
			Vector2(61.0, 26.0),
			Vector2(74.0, 33.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[Vector2(39.0, 9.0), Vector2(47.0, 11.0), Vector2(61.0, 21.0), Vector2(52.0, 18.0)],
		light
	)
	canvas.draw_line(_p(box, 76.0, 34.0), _p(box, 87.0, 31.0), rift, maxf(3.0 * unit, 1.0), true)

	# Ragged cloak panels and spectral seams create a lean melee silhouette.
	_fill(
		canvas,
		box,
		[
			Vector2(5.0, 96.0),
			Vector2(10.0, 72.0),
			Vector2(28.0, 55.0),
			Vector2(63.0, 55.0),
			Vector2(83.0, 71.0),
			Vector2(91.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 94.0),
			Vector2(17.0, 74.0),
			Vector2(31.0, 62.0),
			Vector2(60.0, 62.0),
			Vector2(77.0, 74.0),
			Vector2(84.0, 94.0)
		],
		cloak
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 94.0),
			Vector2(18.0, 75.0),
			Vector2(31.0, 65.0),
			Vector2(40.0, 79.0),
			Vector2(32.0, 88.0),
			Vector2(35.0, 96.0)
		],
		violet
	)
	_fill(
		canvas,
		box,
		[
			Vector2(54.0, 78.0),
			Vector2(61.0, 65.0),
			Vector2(76.0, 75.0),
			Vector2(83.0, 94.0),
			Vector2(65.0, 96.0),
			Vector2(66.0, 85.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(16.0, 94.0),
			Vector2(23.0, 83.0),
			Vector2(28.0, 94.0),
			Vector2(34.0, 85.0),
			Vector2(38.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(54.0, 96.0),
			Vector2(60.0, 84.0),
			Vector2(66.0, 94.0),
			Vector2(73.0, 83.0),
			Vector2(78.0, 96.0)
		],
		violet
	)
	canvas.draw_line(_p(box, 28.0, 73.0), _p(box, 37.0, 85.0), wisp, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 65.0, 73.0), _p(box, 58.0, 85.0), rift, maxf(1.5 * unit, 1.0), true)

	# Tattered shoulder wings and a narrow chest seal avoid heavy warrior armour.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 70.0),
			Vector2(14.0, 54.0),
			Vector2(26.0, 50.0),
			Vector2(37.0, 63.0),
			Vector2(30.0, 72.0),
			Vector2(23.0, 67.0),
			Vector2(18.0, 79.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 67.0),
			Vector2(19.0, 58.0),
			Vector2(26.0, 56.0),
			Vector2(31.0, 63.0),
			Vector2(26.0, 66.0),
			Vector2(21.0, 63.0),
			Vector2(19.0, 71.0)
		],
		violet
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 63.0),
			Vector2(69.0, 50.0),
			Vector2(81.0, 54.0),
			Vector2(88.0, 70.0),
			Vector2(78.0, 79.0),
			Vector2(72.0, 67.0),
			Vector2(65.0, 73.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(65.0, 63.0),
			Vector2(71.0, 56.0),
			Vector2(77.0, 58.0),
			Vector2(82.0, 67.0),
			Vector2(76.0, 71.0),
			Vector2(72.0, 63.0),
			Vector2(68.0, 67.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 68.0),
			Vector2(47.0, 61.0),
			Vector2(59.0, 68.0),
			Vector2(55.0, 82.0),
			Vector2(47.0, 88.0),
			Vector2(39.0, 82.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(47.0, 67.0), Vector2(53.0, 75.0), Vector2(47.0, 83.0), Vector2(41.0, 75.0)],
		rift
	)
	canvas.draw_circle(_p(box, 47.0, 75.0), 2.0 * unit, light)

	# The pointed cowl conceals a skull-like mask with luminous empty sockets.
	_fill(
		canvas,
		box,
		[
			Vector2(25.0, 51.0),
			Vector2(22.0, 31.0),
			Vector2(30.0, 15.0),
			Vector2(45.0, 7.0),
			Vector2(60.0, 13.0),
			Vector2(70.0, 29.0),
			Vector2(68.0, 51.0),
			Vector2(58.0, 62.0),
			Vector2(36.0, 61.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 47.0),
			Vector2(28.0, 32.0),
			Vector2(35.0, 20.0),
			Vector2(46.0, 13.0),
			Vector2(57.0, 18.0),
			Vector2(65.0, 31.0),
			Vector2(63.0, 47.0),
			Vector2(56.0, 56.0),
			Vector2(38.0, 55.0)
		],
		violet
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 33.0),
			Vector2(38.0, 24.0),
			Vector2(55.0, 23.0),
			Vector2(64.0, 32.0),
			Vector2(61.0, 48.0),
			Vector2(54.0, 57.0),
			Vector2(41.0, 57.0),
			Vector2(33.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 34.0),
			Vector2(41.0, 29.0),
			Vector2(54.0, 28.0),
			Vector2(59.0, 33.0),
			Vector2(57.0, 45.0),
			Vector2(52.0, 52.0),
			Vector2(43.0, 52.0),
			Vector2(38.0, 45.0)
		],
		bone
	)
	_fill(
		canvas,
		box,
		[Vector2(36.0, 35.0), Vector2(44.0, 33.0), Vector2(45.0, 41.0), Vector2(38.0, 42.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(51.0, 33.0), Vector2(59.0, 35.0), Vector2(57.0, 42.0), Vector2(50.0, 41.0)],
		ink
	)
	canvas.draw_circle(_p(box, 41.0, 38.0), 1.5 * unit, wisp)
	canvas.draw_circle(_p(box, 54.0, 38.0), 1.5 * unit, rift)
	_fill(
		canvas,
		box,
		[Vector2(45.0, 41.0), Vector2(48.0, 38.0), Vector2(51.0, 42.0), Vector2(48.0, 46.0)],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(39.0, 47.0),
			Vector2(47.0, 50.0),
			Vector2(56.0, 46.0),
			Vector2(52.0, 54.0),
			Vector2(43.0, 54.0)
		],
		ink
	)
	canvas.draw_line(_p(box, 43.0, 49.0), _p(box, 43.0, 53.0), bone, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 50.0), _p(box, 48.0, 54.0), bone, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 49.0), _p(box, 52.0, 53.0), bone, maxf(1.2 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 32.0),
			Vector2(35.0, 20.0),
			Vector2(46.0, 13.0),
			Vector2(58.0, 18.0),
			Vector2(65.0, 31.0),
			Vector2(56.0, 27.0),
			Vector2(47.0, 30.0),
			Vector2(38.0, 27.0)
		],
		shade
	)

	# One gauntlet wraps the scythe while the free hand ends in spectral claws.
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 81.0),
			Vector2(74.0, 75.0),
			Vector2(82.0, 79.0),
			Vector2(81.0, 90.0),
			Vector2(73.0, 93.0),
			Vector2(68.0, 89.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 82.0),
			Vector2(75.0, 79.0),
			Vector2(79.0, 81.0),
			Vector2(78.0, 87.0),
			Vector2(73.0, 88.0)
		],
		cloak
	)
	canvas.draw_line(_p(box, 71.0, 77.0), _p(box, 80.0, 75.0), rift, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 69.0, 84.0), _p(box, 79.0, 82.0), steel, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 93.0),
			Vector2(10.0, 81.0),
			Vector2(15.0, 75.0),
			Vector2(17.0, 65.0),
			Vector2(21.0, 66.0),
			Vector2(22.0, 76.0),
			Vector2(28.0, 70.0),
			Vector2(31.0, 73.0),
			Vector2(27.0, 85.0),
			Vector2(29.0, 94.0)
		],
		ink
	)
	canvas.draw_line(_p(box, 17.0, 79.0), _p(box, 19.0, 69.0), bone, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 21.0, 81.0), _p(box, 28.0, 74.0), bone, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 13.0, 58.0), 1.2 * unit, wisp)


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
