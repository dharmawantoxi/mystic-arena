extends RefCounted
## Native canvas portrait: Auroth, The Celestial Bastion / Bastion Titan.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(24, 31, 44)
	var stone := Color8(105, 123, 141)
	var shade := Color8(58, 74, 96)
	var light := Color8(203, 222, 225)
	var gold := Color8(199, 168, 97)
	var bronze := Color8(119, 100, 65)
	var core := Color8(135, 234, 249)
	var night := Color8(28, 43, 69)
	_backdrop(canvas, box, Color8(42, 66, 88), Color8(17, 27, 44))

	# A celestial disc and tiny stars surround a fortress-like stone titan.
	canvas.draw_circle(_p(box, 48.0, 34.0), 28.0 * unit, bronze)
	canvas.draw_circle(_p(box, 48.0, 34.0), 25.0 * unit, night)
	canvas.draw_arc(
		_p(box, 48.0, 34.0),
		30.0 * unit,
		PI * -0.85,
		PI * -0.15,
		48,
		gold,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 10.0, 24.0), _p(box, 14.0, 24.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 12.0, 22.0), _p(box, 12.0, 26.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 82.0, 25.0), _p(box, 86.0, 25.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 84.0, 23.0), _p(box, 84.0, 27.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 17.0, 46.0), _p(box, 21.0, 46.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 19.0, 44.0), _p(box, 19.0, 48.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 76.0, 48.0), _p(box, 80.0, 48.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 46.0), _p(box, 78.0, 50.0), light, maxf(1.0 * unit, 1.0), true)

	# Massive crenellated pauldrons provide the bastion silhouette, not a human cape.
	_fill(
		canvas,
		box,
		[
			Vector2(4.0, 94.0),
			Vector2(5.0, 50.0),
			Vector2(11.0, 50.0),
			Vector2(11.0, 39.0),
			Vector2(20.0, 39.0),
			Vector2(20.0, 49.0),
			Vector2(25.0, 49.0),
			Vector2(25.0, 40.0),
			Vector2(34.0, 40.0),
			Vector2(34.0, 61.0),
			Vector2(62.0, 61.0),
			Vector2(62.0, 40.0),
			Vector2(71.0, 40.0),
			Vector2(71.0, 49.0),
			Vector2(76.0, 49.0),
			Vector2(76.0, 39.0),
			Vector2(85.0, 39.0),
			Vector2(85.0, 50.0),
			Vector2(91.0, 50.0),
			Vector2(92.0, 94.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 91.0),
			Vector2(10.0, 55.0),
			Vector2(15.0, 55.0),
			Vector2(15.0, 44.0),
			Vector2(17.0, 44.0),
			Vector2(17.0, 54.0),
			Vector2(29.0, 54.0),
			Vector2(29.0, 48.0),
			Vector2(30.0, 65.0),
			Vector2(66.0, 65.0),
			Vector2(67.0, 48.0),
			Vector2(67.0, 54.0),
			Vector2(80.0, 54.0),
			Vector2(80.0, 44.0),
			Vector2(82.0, 44.0),
			Vector2(82.0, 55.0),
			Vector2(86.0, 55.0),
			Vector2(87.0, 91.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 57.0),
			Vector2(28.0, 57.0),
			Vector2(32.0, 67.0),
			Vector2(29.0, 78.0),
			Vector2(11.0, 78.0)
		],
		stone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 57.0),
			Vector2(86.0, 57.0),
			Vector2(85.0, 78.0),
			Vector2(67.0, 78.0),
			Vector2(64.0, 67.0)
		],
		stone
	)
	canvas.draw_line(_p(box, 12.0, 59.0), _p(box, 27.0, 59.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 69.0, 59.0), _p(box, 84.0, 59.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 12.0, 73.0), _p(box, 28.0, 73.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 68.0, 73.0), _p(box, 84.0, 73.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(25.0, 63.0),
			Vector2(37.0, 55.0),
			Vector2(59.0, 55.0),
			Vector2(71.0, 64.0),
			Vector2(74.0, 96.0),
			Vector2(22.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 66.0),
			Vector2(39.0, 60.0),
			Vector2(57.0, 60.0),
			Vector2(66.0, 67.0),
			Vector2(69.0, 94.0),
			Vector2(27.0, 94.0)
		],
		stone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(48.0, 63.0),
			Vector2(58.0, 64.0),
			Vector2(65.0, 70.0),
			Vector2(68.0, 93.0),
			Vector2(49.0, 92.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 67.0),
			Vector2(41.0, 63.0),
			Vector2(44.0, 68.0),
			Vector2(36.0, 73.0),
			Vector2(31.0, 79.0)
		],
		light
	)
	canvas.draw_line(_p(box, 31.0, 87.0), _p(box, 42.0, 92.0), bronze, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 54.0, 92.0), _p(box, 66.0, 87.0), gold, maxf(2.0 * unit, 1.0), true)

	# An inset crystalline core lights the chest through concentric stone plates.
	_fill(
		canvas,
		box,
		[Vector2(48.0, 65.0), Vector2(61.0, 77.0), Vector2(48.0, 91.0), Vector2(35.0, 77.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 68.0), Vector2(57.0, 77.0), Vector2(48.0, 87.0), Vector2(39.0, 77.0)],
		gold
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 71.0), Vector2(54.0, 77.0), Vector2(48.0, 84.0), Vector2(42.0, 77.0)],
		night
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 73.0), Vector2(52.0, 77.0), Vector2(48.0, 81.0), Vector2(44.0, 77.0)],
		core
	)
	canvas.draw_line(_p(box, 31.0, 83.0), _p(box, 37.0, 81.0), core, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 59.0, 81.0), _p(box, 65.0, 83.0), core, maxf(1.5 * unit, 1.0), true)

	# A monolithic face, squared cheek blocks and an astronomical crown.
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 25.0),
			Vector2(35.0, 17.0),
			Vector2(61.0, 17.0),
			Vector2(67.0, 25.0),
			Vector2(65.0, 49.0),
			Vector2(57.0, 58.0),
			Vector2(39.0, 58.0),
			Vector2(31.0, 49.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 27.0),
			Vector2(39.0, 22.0),
			Vector2(57.0, 22.0),
			Vector2(62.0, 27.0),
			Vector2(60.0, 47.0),
			Vector2(54.0, 53.0),
			Vector2(42.0, 53.0),
			Vector2(36.0, 47.0)
		],
		stone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(49.0, 23.0),
			Vector2(57.0, 23.0),
			Vector2(62.0, 28.0),
			Vector2(59.0, 47.0),
			Vector2(53.0, 52.0),
			Vector2(49.0, 47.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 26.0),
			Vector2(30.0, 13.0),
			Vector2(38.0, 19.0),
			Vector2(43.0, 9.0),
			Vector2(48.0, 17.0),
			Vector2(53.0, 9.0),
			Vector2(58.0, 19.0),
			Vector2(66.0, 13.0),
			Vector2(66.0, 26.0),
			Vector2(58.0, 29.0),
			Vector2(38.0, 29.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 24.0),
			Vector2(35.0, 21.0),
			Vector2(39.0, 24.0),
			Vector2(43.0, 16.0),
			Vector2(48.0, 23.0),
			Vector2(53.0, 16.0),
			Vector2(57.0, 24.0),
			Vector2(61.0, 21.0),
			Vector2(61.0, 24.0),
			Vector2(57.0, 26.0),
			Vector2(39.0, 26.0)
		],
		light
	)
	_fill(
		canvas,
		box,
		[Vector2(34.0, 33.0), Vector2(44.0, 33.0), Vector2(44.0, 40.0), Vector2(35.0, 39.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(52.0, 33.0), Vector2(62.0, 33.0), Vector2(61.0, 39.0), Vector2(52.0, 40.0)],
		ink
	)
	canvas.draw_line(_p(box, 36.0, 36.0), _p(box, 42.0, 37.0), core, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 54.0, 37.0), _p(box, 60.0, 36.0), core, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(46.0, 31.0),
			Vector2(50.0, 31.0),
			Vector2(53.0, 43.0),
			Vector2(48.0, 47.0),
			Vector2(43.0, 43.0)
		],
		light
	)
	canvas.draw_line(_p(box, 41.0, 49.0), _p(box, 55.0, 49.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 45.0), _p(box, 41.0, 46.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 55.0, 46.0), _p(box, 58.0, 45.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 24.0), _p(box, 40.0, 30.0), shade, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 56.0, 44.0), _p(box, 55.0, 48.0), ink, maxf(1.0 * unit, 1.0), true)

	# Heavy articulated fists and engraved star rivets finish the stone armour.
	_fill(
		canvas,
		box,
		[
			Vector2(5.0, 81.0),
			Vector2(19.0, 79.0),
			Vector2(27.0, 86.0),
			Vector2(24.0, 96.0),
			Vector2(5.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 84.0),
			Vector2(18.0, 83.0),
			Vector2(22.0, 88.0),
			Vector2(21.0, 93.0),
			Vector2(9.0, 93.0)
		],
		stone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 79.0),
			Vector2(91.0, 81.0),
			Vector2(91.0, 96.0),
			Vector2(72.0, 96.0),
			Vector2(69.0, 86.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(78.0, 83.0),
			Vector2(87.0, 84.0),
			Vector2(87.0, 93.0),
			Vector2(75.0, 93.0),
			Vector2(74.0, 88.0)
		],
		stone
	)
	canvas.draw_line(_p(box, 12.0, 87.0), _p(box, 12.0, 91.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 17.0, 87.0), _p(box, 17.0, 91.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 79.0, 87.0), _p(box, 79.0, 91.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 84.0, 87.0), _p(box, 84.0, 91.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 20.0, 65.0), 3.0 * unit, bronze)
	canvas.draw_circle(_p(box, 20.0, 65.0), 1.3 * unit, core)
	canvas.draw_circle(_p(box, 76.0, 65.0), 3.0 * unit, bronze)
	canvas.draw_circle(_p(box, 76.0, 65.0), 1.3 * unit, core)


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
