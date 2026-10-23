extends RefCounted
## Native canvas portrait: Emberwick, The Blazing Matron / Fire Matron.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(42, 25, 34)
	var robe := Color8(110, 41, 52)
	var red := Color8(177, 65, 54)
	var gold := Color8(218, 161, 66)
	var light := Color8(255, 231, 158)
	var flame := Color8(249, 137, 59)
	var skin := Color8(198, 146, 122)
	var shade := Color8(139, 88, 88)
	var hair := Color8(90, 44, 47)
	var silver := Color8(190, 173, 156)
	_backdrop(canvas, box, Color8(108, 53, 44), Color8(34, 23, 36))

	# A flame-shaped aura and ember motes frame the poised fire matron.
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 63.0),
			Vector2(9.0, 43.0),
			Vector2(18.0, 27.0),
			Vector2(19.0, 42.0),
			Vector2(29.0, 24.0),
			Vector2(32.0, 12.0),
			Vector2(44.0, 27.0),
			Vector2(48.0, 9.0),
			Vector2(58.0, 28.0),
			Vector2(67.0, 16.0),
			Vector2(68.0, 35.0),
			Vector2(80.0, 27.0),
			Vector2(77.0, 45.0),
			Vector2(87.0, 38.0),
			Vector2(81.0, 62.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(20.0, 61.0),
			Vector2(17.0, 44.0),
			Vector2(24.0, 33.0),
			Vector2(24.0, 45.0),
			Vector2(34.0, 30.0),
			Vector2(35.0, 23.0),
			Vector2(44.0, 35.0),
			Vector2(49.0, 21.0),
			Vector2(56.0, 36.0),
			Vector2(64.0, 28.0),
			Vector2(65.0, 45.0),
			Vector2(76.0, 37.0),
			Vector2(72.0, 54.0),
			Vector2(78.0, 49.0),
			Vector2(76.0, 62.0)
		],
		robe
	)
	canvas.draw_circle(_p(box, 10.0, 21.0), 1.3 * unit, flame)
	canvas.draw_circle(_p(box, 82.0, 18.0), 1.3 * unit, flame)
	canvas.draw_circle(_p(box, 18.0, 66.0), 1.3 * unit, flame)
	canvas.draw_circle(_p(box, 85.0, 59.0), 1.3 * unit, flame)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 96.0),
			Vector2(19.0, 70.0),
			Vector2(32.0, 58.0),
			Vector2(59.0, 58.0),
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
			Vector2(24.0, 73.0),
			Vector2(34.0, 63.0),
			Vector2(57.0, 63.0),
			Vector2(70.0, 75.0),
			Vector2(78.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(25.0, 73.0),
			Vector2(37.0, 68.0),
			Vector2(44.0, 78.0),
			Vector2(39.0, 94.0),
			Vector2(19.0, 94.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 77.0),
			Vector2(59.0, 67.0),
			Vector2(69.0, 75.0),
			Vector2(76.0, 94.0),
			Vector2(56.0, 94.0)
		],
		shade
	)

	# A tall sculpted collar, a gold fire clasp and engraved robe piping.
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 51.0),
			Vector2(38.0, 57.0),
			Vector2(47.0, 68.0),
			Vector2(58.0, 58.0),
			Vector2(69.0, 50.0),
			Vector2(65.0, 68.0),
			Vector2(48.0, 82.0),
			Vector2(32.0, 68.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 57.0),
			Vector2(39.0, 62.0),
			Vector2(47.0, 74.0),
			Vector2(58.0, 63.0),
			Vector2(64.0, 56.0),
			Vector2(61.0, 67.0),
			Vector2(48.0, 78.0),
			Vector2(36.0, 66.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 32.0),
			Vector2(29.0, 22.0),
			Vector2(36.0, 19.0),
			Vector2(38.0, 11.0),
			Vector2(48.0, 9.0),
			Vector2(57.0, 14.0),
			Vector2(61.0, 23.0),
			Vector2(67.0, 28.0),
			Vector2(66.0, 46.0),
			Vector2(61.0, 60.0),
			Vector2(54.0, 63.0),
			Vector2(37.0, 62.0),
			Vector2(28.0, 49.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 31.0),
			Vector2(37.0, 23.0),
			Vector2(55.0, 23.0),
			Vector2(63.0, 31.0),
			Vector2(61.0, 46.0),
			Vector2(54.0, 57.0),
			Vector2(42.0, 58.0),
			Vector2(33.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 32.0),
			Vector2(40.0, 27.0),
			Vector2(53.0, 27.0),
			Vector2(58.0, 33.0),
			Vector2(57.0, 44.0),
			Vector2(52.0, 53.0),
			Vector2(43.0, 54.0),
			Vector2(37.0, 46.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 29.0),
			Vector2(58.0, 34.0),
			Vector2(57.0, 44.0),
			Vector2(52.0, 51.0),
			Vector2(48.0, 49.0),
			Vector2(50.0, 41.0)
		],
		shade
	)

	# Swept auburn hair in a silver-streaked bun and a flame diadem.
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 34.0),
			Vector2(32.0, 25.0),
			Vector2(41.0, 21.0),
			Vector2(53.0, 22.0),
			Vector2(61.0, 28.0),
			Vector2(64.0, 40.0),
			Vector2(58.0, 35.0),
			Vector2(54.0, 28.0),
			Vector2(46.0, 33.0),
			Vector2(42.0, 28.0),
			Vector2(36.0, 36.0),
			Vector2(35.0, 49.0),
			Vector2(30.0, 43.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 34.0, 28.0), _p(box, 40.0, 25.0), silver, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 54.0, 25.0), _p(box, 59.0, 30.0), silver, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 27.0),
			Vector2(38.0, 22.0),
			Vector2(44.0, 25.0),
			Vector2(48.0, 18.0),
			Vector2(52.0, 25.0),
			Vector2(58.0, 22.0),
			Vector2(60.0, 28.0),
			Vector2(52.0, 28.0),
			Vector2(48.0, 33.0),
			Vector2(44.0, 28.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 23.0), Vector2(50.0, 27.0), Vector2(48.0, 30.0), Vector2(46.0, 27.0)],
		light
	)
	canvas.draw_line(_p(box, 38.0, 36.0), _p(box, 44.0, 37.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 37.0), _p(box, 57.0, 35.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 40.0), _p(box, 43.0, 40.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 40.0), _p(box, 56.0, 39.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 38.0), _p(box, 46.0, 44.0), skin, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 44.0, 49.0), _p(box, 51.0, 48.0), robe, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 43.0), _p(box, 41.0, 44.0), shade, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 54.0, 44.0), _p(box, 57.0, 42.0), shade, maxf(1.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 35.0, 45.0), 2.0 * unit, gold)
	canvas.draw_circle(_p(box, 35.0, 49.0), 1.3 * unit, light)
	canvas.draw_circle(_p(box, 60.0, 44.0), 2.0 * unit, gold)
	canvas.draw_circle(_p(box, 60.0, 48.0), 1.3 * unit, light)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 72.0), Vector2(54.0, 80.0), Vector2(48.0, 87.0), Vector2(42.0, 80.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 75.0), Vector2(51.0, 80.0), Vector2(48.0, 84.0), Vector2(45.0, 80.0)],
		flame
	)
	canvas.draw_line(_p(box, 34.0, 83.0), _p(box, 41.0, 87.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 55.0, 87.0), _p(box, 63.0, 83.0), gold, maxf(1.5 * unit, 1.0), true)

	# A raised casting palm holds a clean layered flame, not a weapon.
	_fill(
		canvas,
		box,
		[
			Vector2(65.0, 90.0),
			Vector2(64.0, 80.0),
			Vector2(67.0, 76.0),
			Vector2(66.0, 70.0),
			Vector2(70.0, 68.0),
			Vector2(73.0, 75.0),
			Vector2(75.0, 70.0),
			Vector2(79.0, 71.0),
			Vector2(79.0, 79.0),
			Vector2(84.0, 78.0),
			Vector2(86.0, 81.0),
			Vector2(79.0, 88.0),
			Vector2(75.0, 94.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 87.0),
			Vector2(68.0, 80.0),
			Vector2(71.0, 79.0),
			Vector2(69.0, 72.0),
			Vector2(70.0, 72.0),
			Vector2(74.0, 79.0),
			Vector2(77.0, 74.0),
			Vector2(77.0, 81.0),
			Vector2(82.0, 81.0),
			Vector2(77.0, 85.0),
			Vector2(74.0, 90.0)
		],
		skin
	)
	canvas.draw_line(_p(box, 68.0, 90.0), _p(box, 76.0, 92.0), gold, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 68.0),
			Vector2(62.0, 59.0),
			Vector2(66.0, 48.0),
			Vector2(71.0, 54.0),
			Vector2(77.0, 39.0),
			Vector2(81.0, 50.0),
			Vector2(87.0, 55.0),
			Vector2(85.0, 65.0),
			Vector2(78.0, 71.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(70.0, 66.0),
			Vector2(66.0, 59.0),
			Vector2(68.0, 53.0),
			Vector2(72.0, 58.0),
			Vector2(77.0, 46.0),
			Vector2(79.0, 54.0),
			Vector2(84.0, 58.0),
			Vector2(82.0, 64.0),
			Vector2(77.0, 68.0)
		],
		flame
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 64.0),
			Vector2(71.0, 59.0),
			Vector2(75.0, 60.0),
			Vector2(78.0, 53.0),
			Vector2(80.0, 60.0),
			Vector2(78.0, 65.0),
			Vector2(75.0, 67.0)
		],
		light
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
