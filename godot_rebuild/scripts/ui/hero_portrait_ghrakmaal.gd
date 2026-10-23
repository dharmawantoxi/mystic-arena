extends RefCounted
## Native canvas portrait: Ghrakmaal, The Colossus of Sundered Earth / Earth Colossus.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(35, 31, 26)
	var rock := Color8(108, 99, 81)
	var shade := Color8(69, 66, 56)
	var light := Color8(178, 166, 132)
	var earth := Color8(137, 104, 65)
	var glow := Color8(244, 188, 79)
	var core := Color8(255, 227, 132)
	var moss := Color8(81, 101, 61)
	_backdrop(canvas, box, Color8(81, 75, 49), Color8(29, 31, 26))

	# Dislocated pillars and fault lines suggest a sundered landscape.
	_fill(
		canvas,
		box,
		[
			Vector2(3.0, 65.0),
			Vector2(6.0, 34.0),
			Vector2(15.0, 27.0),
			Vector2(21.0, 33.0),
			Vector2(19.0, 65.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 60.0),
			Vector2(10.0, 37.0),
			Vector2(14.0, 34.0),
			Vector2(16.0, 38.0),
			Vector2(14.0, 60.0)
		],
		rock
	)
	_fill(
		canvas,
		box,
		[
			Vector2(75.0, 64.0),
			Vector2(77.0, 32.0),
			Vector2(87.0, 24.0),
			Vector2(93.0, 31.0),
			Vector2(91.0, 64.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 80.0, 43.0), _p(box, 85.0, 47.0), glow, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 85.0, 47.0), _p(box, 82.0, 56.0), glow, maxf(1.5 * unit, 1.0), true)

	# A towering asymmetrical slab body has no human armour, hair or weapon.
	_fill(
		canvas,
		box,
		[
			Vector2(3.0, 96.0),
			Vector2(5.0, 64.0),
			Vector2(17.0, 48.0),
			Vector2(31.0, 52.0),
			Vector2(36.0, 43.0),
			Vector2(58.0, 42.0),
			Vector2(67.0, 51.0),
			Vector2(81.0, 47.0),
			Vector2(91.0, 63.0),
			Vector2(94.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 94.0),
			Vector2(11.0, 67.0),
			Vector2(20.0, 54.0),
			Vector2(31.0, 58.0),
			Vector2(39.0, 48.0),
			Vector2(55.0, 47.0),
			Vector2(64.0, 57.0),
			Vector2(78.0, 53.0),
			Vector2(85.0, 66.0),
			Vector2(88.0, 94.0)
		],
		rock
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 49.0),
			Vector2(59.0, 53.0),
			Vector2(65.0, 61.0),
			Vector2(79.0, 57.0),
			Vector2(85.0, 70.0),
			Vector2(87.0, 94.0),
			Vector2(50.0, 94.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 65.0),
			Vector2(21.0, 56.0),
			Vector2(29.0, 60.0),
			Vector2(25.0, 64.0),
			Vector2(19.0, 63.0),
			Vector2(15.0, 73.0)
		],
		light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 60.0),
			Vector2(77.0, 56.0),
			Vector2(82.0, 65.0),
			Vector2(75.0, 68.0),
			Vector2(69.0, 65.0)
		],
		earth
	)
	canvas.draw_line(_p(box, 13.0, 77.0), _p(box, 26.0, 75.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 68.0, 75.0), _p(box, 84.0, 77.0), ink, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 67.0),
			Vector2(47.0, 59.0),
			Vector2(65.0, 68.0),
			Vector2(64.0, 92.0),
			Vector2(49.0, 96.0),
			Vector2(30.0, 91.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 69.0),
			Vector2(47.0, 64.0),
			Vector2(60.0, 70.0),
			Vector2(59.0, 89.0),
			Vector2(49.0, 93.0),
			Vector2(35.0, 88.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(38.0, 72.0),
			Vector2(47.0, 67.0),
			Vector2(57.0, 73.0),
			Vector2(55.0, 86.0),
			Vector2(48.0, 91.0),
			Vector2(38.0, 85.0)
		],
		earth
	)

	# A deep jagged chest fault glows amber between separated rock plates.
	_fill(
		canvas,
		box,
		[
			Vector2(45.0, 66.0),
			Vector2(53.0, 69.0),
			Vector2(50.0, 75.0),
			Vector2(55.0, 80.0),
			Vector2(48.0, 90.0),
			Vector2(42.0, 86.0),
			Vector2(45.0, 79.0),
			Vector2(40.0, 75.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(46.0, 70.0),
			Vector2(49.0, 71.0),
			Vector2(46.0, 76.0),
			Vector2(51.0, 80.0),
			Vector2(47.0, 86.0),
			Vector2(46.0, 84.0),
			Vector2(48.0, 79.0),
			Vector2(44.0, 75.0)
		],
		glow
	)
	canvas.draw_line(_p(box, 47.0, 74.0), _p(box, 47.0, 78.0), core, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 35.0, 77.0), _p(box, 39.0, 78.0), glow, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 55.0, 82.0), _p(box, 60.0, 83.0), glow, maxf(1.0 * unit, 1.0), true)

	# An offset basalt head has a broken crown ridge and narrow mineral eyes.
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 26.0),
			Vector2(31.0, 15.0),
			Vector2(40.0, 18.0),
			Vector2(44.0, 8.0),
			Vector2(53.0, 15.0),
			Vector2(63.0, 13.0),
			Vector2(69.0, 25.0),
			Vector2(66.0, 48.0),
			Vector2(58.0, 59.0),
			Vector2(39.0, 60.0),
			Vector2(28.0, 49.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 28.0),
			Vector2(35.0, 21.0),
			Vector2(41.0, 23.0),
			Vector2(46.0, 15.0),
			Vector2(52.0, 21.0),
			Vector2(60.0, 19.0),
			Vector2(64.0, 27.0),
			Vector2(61.0, 46.0),
			Vector2(55.0, 54.0),
			Vector2(41.0, 55.0),
			Vector2(33.0, 46.0)
		],
		rock
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 20.0),
			Vector2(59.0, 21.0),
			Vector2(64.0, 28.0),
			Vector2(61.0, 45.0),
			Vector2(54.0, 53.0),
			Vector2(49.0, 48.0),
			Vector2(51.0, 38.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 25.0),
			Vector2(41.0, 27.0),
			Vector2(46.0, 19.0),
			Vector2(49.0, 24.0),
			Vector2(44.0, 31.0),
			Vector2(34.0, 32.0)
		],
		light
	)
	_fill(
		canvas,
		box,
		[Vector2(53.0, 25.0), Vector2(59.0, 24.0), Vector2(61.0, 29.0), Vector2(56.0, 32.0)],
		earth
	)
	_fill(
		canvas,
		box,
		[Vector2(31.0, 35.0), Vector2(44.0, 34.0), Vector2(45.0, 42.0), Vector2(33.0, 41.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(51.0, 34.0), Vector2(64.0, 33.0), Vector2(62.0, 41.0), Vector2(51.0, 42.0)],
		ink
	)
	canvas.draw_line(_p(box, 35.0, 38.0), _p(box, 42.0, 38.0), glow, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 38.0), _p(box, 60.0, 37.0), core, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(46.0, 32.0),
			Vector2(50.0, 32.0),
			Vector2(53.0, 44.0),
			Vector2(47.0, 48.0),
			Vector2(42.0, 44.0)
		],
		light
	)
	canvas.draw_line(_p(box, 40.0, 51.0), _p(box, 56.0, 50.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 42.0, 21.0), _p(box, 44.0, 27.0), glow, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 44.0, 27.0), _p(box, 42.0, 32.0), glow, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 58.0, 43.0), _p(box, 55.0, 47.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 36.0, 44.0), _p(box, 38.0, 48.0), earth, maxf(1.5 * unit, 1.0), true)

	# Unequal boulder fists and moss seams finish the colossal silhouette.
	_fill(
		canvas,
		box,
		[
			Vector2(4.0, 82.0),
			Vector2(16.0, 77.0),
			Vector2(29.0, 82.0),
			Vector2(32.0, 92.0),
			Vector2(26.0, 96.0),
			Vector2(4.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 85.0),
			Vector2(17.0, 82.0),
			Vector2(25.0, 85.0),
			Vector2(27.0, 91.0),
			Vector2(23.0, 93.0),
			Vector2(9.0, 93.0)
		],
		rock
	)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 85.0),
			Vector2(17.0, 84.0),
			Vector2(21.0, 86.0),
			Vector2(17.0, 89.0),
			Vector2(11.0, 90.0)
		],
		light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 81.0),
			Vector2(81.0, 76.0),
			Vector2(93.0, 83.0),
			Vector2(94.0, 96.0),
			Vector2(66.0, 96.0),
			Vector2(62.0, 90.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(69.0, 85.0),
			Vector2(81.0, 81.0),
			Vector2(88.0, 86.0),
			Vector2(89.0, 93.0),
			Vector2(69.0, 93.0),
			Vector2(67.0, 90.0)
		],
		rock
	)
	canvas.draw_line(_p(box, 14.0, 85.0), _p(box, 15.0, 92.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 21.0, 85.0), _p(box, 22.0, 92.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 76.0, 84.0), _p(box, 78.0, 88.0), glow, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 88.0), _p(box, 84.0, 87.0), glow, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 20.0, 69.0), _p(box, 26.0, 68.0), moss, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 71.0, 71.0), _p(box, 78.0, 72.0), moss, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(22.0, 26.0), Vector2(26.0, 21.0), Vector2(28.0, 27.0), Vector2(25.0, 31.0)],
		earth
	)
	_fill(
		canvas,
		box,
		[Vector2(70.0, 18.0), Vector2(75.0, 15.0), Vector2(77.0, 21.0), Vector2(73.0, 24.0)],
		rock
	)


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
