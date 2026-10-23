extends RefCounted
## Native canvas portrait: Xharokh, The Void Mage.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(15, 16, 29)
	var obsidian := Color8(34, 35, 57)
	var armor := Color8(55, 50, 86)
	var violet := Color8(109, 70, 151)
	var rift := Color8(151, 90, 196)
	var blue := Color8(76, 135, 185)
	var starlight := Color8(202, 225, 239)
	var mask := Color8(117, 124, 153)
	var shade := Color8(67, 65, 102)
	_backdrop(canvas, box, Color8(42, 35, 69), Color8(13, 17, 31))

	# Star points, a fractured event horizon and monoliths establish the cosmic void.
	canvas.draw_circle(_p(box, 47.0, 39.0), 33.0 * unit, obsidian)
	canvas.draw_arc(
		_p(box, 47.0, 39.0),
		35.0 * unit,
		PI * -0.1,
		PI * 0.85,
		48,
		rift,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 47.0, 39.0), 35.0 * unit, PI * 1.05, PI * 1.9, 48, blue, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 13.0, 19.0), 1.2 * unit, starlight)
	canvas.draw_circle(_p(box, 83.0, 12.0), 1.0 * unit, rift)
	canvas.draw_circle(_p(box, 89.0, 41.0), 1.3 * unit, starlight)
	canvas.draw_circle(_p(box, 8.0, 45.0), 0.9 * unit, blue)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 28.0),
			Vector2(21.0, 18.0),
			Vector2(25.0, 31.0),
			Vector2(21.0, 43.0),
			Vector2(16.0, 39.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(19.0, 29.0), Vector2(21.0, 24.0), Vector2(22.0, 31.0), Vector2(20.0, 37.0)],
		violet
	)
	_fill(
		canvas,
		box,
		[
			Vector2(75.0, 25.0),
			Vector2(82.0, 18.0),
			Vector2(87.0, 29.0),
			Vector2(83.0, 42.0),
			Vector2(77.0, 38.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(80.0, 27.0), Vector2(82.0, 23.0), Vector2(84.0, 30.0), Vector2(82.0, 36.0)],
		blue
	)

	# Angular armoured robes descend in separated dark panels.
	_fill(
		canvas,
		box,
		[
			Vector2(6.0, 96.0),
			Vector2(11.0, 71.0),
			Vector2(29.0, 55.0),
			Vector2(64.0, 55.0),
			Vector2(84.0, 71.0),
			Vector2(91.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 94.0),
			Vector2(18.0, 74.0),
			Vector2(32.0, 62.0),
			Vector2(60.0, 62.0),
			Vector2(77.0, 74.0),
			Vector2(84.0, 94.0)
		],
		armor
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 94.0),
			Vector2(20.0, 75.0),
			Vector2(33.0, 66.0),
			Vector2(41.0, 80.0),
			Vector2(34.0, 94.0)
		],
		obsidian
	)
	_fill(
		canvas,
		box,
		[
			Vector2(54.0, 79.0),
			Vector2(61.0, 65.0),
			Vector2(76.0, 75.0),
			Vector2(82.0, 94.0),
			Vector2(61.0, 94.0)
		],
		violet
	)
	_fill(
		canvas,
		box,
		[
			Vector2(21.0, 94.0),
			Vector2(29.0, 80.0),
			Vector2(37.0, 94.0),
			Vector2(45.0, 83.0),
			Vector2(47.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 96.0),
			Vector2(57.0, 82.0),
			Vector2(65.0, 94.0),
			Vector2(72.0, 82.0),
			Vector2(78.0, 96.0)
		],
		obsidian
	)

	# Shoulder monoliths and a chest singularity give the armour its arcane geometry.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 69.0),
			Vector2(16.0, 51.0),
			Vector2(28.0, 48.0),
			Vector2(38.0, 63.0),
			Vector2(31.0, 77.0),
			Vector2(16.0, 80.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 67.0),
			Vector2(20.0, 56.0),
			Vector2(27.0, 54.0),
			Vector2(32.0, 63.0),
			Vector2(28.0, 71.0),
			Vector2(19.0, 74.0)
		],
		obsidian
	)
	canvas.draw_line(_p(box, 20.0, 57.0), _p(box, 27.0, 65.0), rift, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 63.0),
			Vector2(68.0, 48.0),
			Vector2(80.0, 51.0),
			Vector2(88.0, 69.0),
			Vector2(80.0, 80.0),
			Vector2(65.0, 77.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(64.0, 64.0),
			Vector2(70.0, 54.0),
			Vector2(77.0, 56.0),
			Vector2(82.0, 67.0),
			Vector2(77.0, 74.0),
			Vector2(68.0, 71.0)
		],
		obsidian
	)
	canvas.draw_line(_p(box, 70.0, 56.0), _p(box, 77.0, 65.0), blue, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 67.0),
			Vector2(47.0, 60.0),
			Vector2(63.0, 67.0),
			Vector2(59.0, 84.0),
			Vector2(47.0, 91.0),
			Vector2(35.0, 84.0)
		],
		ink
	)
	canvas.draw_circle(_p(box, 47.0, 76.0), 11.0 * unit, violet)
	canvas.draw_circle(_p(box, 47.0, 76.0), 8.0 * unit, ink)
	canvas.draw_arc(
		_p(box, 47.0, 76.0),
		6.0 * unit,
		PI * -0.75,
		PI * 0.65,
		32,
		blue,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 44.0, 73.0), 1.5 * unit, starlight)
	canvas.draw_line(_p(box, 35.0, 89.0), _p(box, 42.0, 93.0), rift, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 93.0), _p(box, 60.0, 89.0), blue, maxf(1.5 * unit, 1.0), true)

	# A faceted mask with a central fracture replaces skin, hair and a mortal crown.
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 30.0),
			Vector2(38.0, 16.0),
			Vector2(54.0, 15.0),
			Vector2(65.0, 28.0),
			Vector2(62.0, 47.0),
			Vector2(53.0, 59.0),
			Vector2(40.0, 57.0),
			Vector2(31.0, 46.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 31.0),
			Vector2(41.0, 22.0),
			Vector2(52.0, 21.0),
			Vector2(60.0, 30.0),
			Vector2(58.0, 44.0),
			Vector2(51.0, 53.0),
			Vector2(42.0, 52.0),
			Vector2(36.0, 44.0)
		],
		mask
	)
	_fill(
		canvas,
		box,
		[
			Vector2(48.0, 21.0),
			Vector2(53.0, 21.0),
			Vector2(60.0, 30.0),
			Vector2(58.0, 44.0),
			Vector2(51.0, 53.0),
			Vector2(47.0, 48.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 32.0),
			Vector2(42.0, 27.0),
			Vector2(47.0, 31.0),
			Vector2(53.0, 26.0),
			Vector2(61.0, 31.0),
			Vector2(56.0, 39.0),
			Vector2(48.0, 36.0),
			Vector2(39.0, 39.0)
		],
		obsidian
	)
	canvas.draw_line(
		_p(box, 37.0, 34.0), _p(box, 44.0, 35.0), starlight, maxf(2.2 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 52.0, 35.0), _p(box, 58.0, 33.0), rift, maxf(2.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 22.0), _p(box, 46.0, 32.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 46.0, 32.0), _p(box, 50.0, 39.0), rift, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 39.0), _p(box, 47.0, 49.0), ink, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(39.0, 46.0),
			Vector2(47.0, 50.0),
			Vector2(55.0, 45.0),
			Vector2(51.0, 54.0),
			Vector2(43.0, 53.0)
		],
		obsidian
	)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 18.0),
			Vector2(39.0, 7.0),
			Vector2(46.0, 15.0),
			Vector2(53.0, 5.0),
			Vector2(57.0, 17.0),
			Vector2(47.0, 21.0)
		],
		ink
	)
	canvas.draw_circle(_p(box, 47.0, 14.0), 2.0 * unit, rift)

	# A long-fingered hand suspends one final shard without a staff or weapon.
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 95.0),
			Vector2(65.0, 83.0),
			Vector2(70.0, 77.0),
			Vector2(71.0, 67.0),
			Vector2(75.0, 66.0),
			Vector2(78.0, 77.0),
			Vector2(83.0, 69.0),
			Vector2(87.0, 71.0),
			Vector2(85.0, 83.0),
			Vector2(90.0, 89.0),
			Vector2(87.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(71.0, 91.0),
			Vector2(70.0, 84.0),
			Vector2(75.0, 80.0),
			Vector2(81.0, 81.0),
			Vector2(85.0, 88.0),
			Vector2(82.0, 93.0)
		],
		mask
	)
	canvas.draw_line(
		_p(box, 74.0, 80.0), _p(box, 74.0, 70.0), starlight, maxf(1.2 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 79.0, 80.0), _p(box, 84.0, 73.0), starlight, maxf(1.2 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[
			Vector2(73.0, 57.0),
			Vector2(79.0, 47.0),
			Vector2(86.0, 54.0),
			Vector2(84.0, 64.0),
			Vector2(77.0, 67.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(78.0, 57.0), Vector2(80.0, 52.0), Vector2(83.0, 55.0), Vector2(81.0, 61.0)],
		rift
	)
	canvas.draw_line(_p(box, 77.0, 67.0), _p(box, 76.0, 72.0), blue, maxf(1.0 * unit, 1.0), true)


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
