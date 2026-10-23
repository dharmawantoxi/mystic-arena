extends RefCounted
## Native canvas portrait: Hitokage, The Sunfire Blade Master / Sun Swordsman.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(37, 24, 29)
	var cloth := Color8(61, 40, 46)
	var red := Color8(158, 47, 43)
	var flame := Color8(239, 116, 48)
	var gold := Color8(232, 175, 63)
	var light := Color8(255, 233, 163)
	var skin := Color8(209, 159, 124)
	var shade := Color8(153, 96, 81)
	var hair := Color8(77, 33, 36)
	var steel := Color8(190, 196, 186)
	_backdrop(canvas, box, Color8(102, 52, 43), Color8(30, 24, 34))

	# A broad sun disc and separated flame rays distinguish the sun swordsman.
	canvas.draw_circle(_p(box, 47.0, 37.0), 28.0 * unit, red)
	canvas.draw_circle(_p(box, 47.0, 37.0), 24.0 * unit, flame)
	canvas.draw_circle(_p(box, 47.0, 37.0), 19.0 * unit, gold)
	canvas.draw_line(_p(box, 15.0, 20.0), _p(box, 22.0, 24.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 29.0, 7.0), _p(box, 33.0, 14.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 49.0, 3.0), _p(box, 49.0, 9.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 69.0, 10.0), _p(box, 65.0, 16.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 82.0, 26.0), _p(box, 74.0, 29.0), gold, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 96.0),
			Vector2(20.0, 71.0),
			Vector2(32.0, 58.0),
			Vector2(60.0, 58.0),
			Vector2(75.0, 72.0),
			Vector2(83.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 94.0),
			Vector2(26.0, 73.0),
			Vector2(34.0, 63.0),
			Vector2(58.0, 63.0),
			Vector2(69.0, 74.0),
			Vector2(77.0, 94.0)
		],
		cloth
	)

	# A split pale haori with flame tips surrounds a dark uniform and crossed collar.
	_fill(
		canvas,
		box,
		[
			Vector2(21.0, 70.0),
			Vector2(32.0, 61.0),
			Vector2(41.0, 69.0),
			Vector2(36.0, 94.0),
			Vector2(16.0, 94.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(54.0, 69.0),
			Vector2(61.0, 61.0),
			Vector2(71.0, 72.0),
			Vector2(79.0, 94.0),
			Vector2(59.0, 94.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(17.0, 94.0),
			Vector2(20.0, 84.0),
			Vector2(24.0, 89.0),
			Vector2(27.0, 80.0),
			Vector2(30.0, 88.0),
			Vector2(34.0, 84.0),
			Vector2(35.0, 94.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(20.0, 94.0),
			Vector2(22.0, 89.0),
			Vector2(24.0, 92.0),
			Vector2(27.0, 86.0),
			Vector2(29.0, 92.0),
			Vector2(32.0, 90.0),
			Vector2(33.0, 94.0)
		],
		flame
	)
	_fill(
		canvas,
		box,
		[
			Vector2(60.0, 94.0),
			Vector2(60.0, 85.0),
			Vector2(65.0, 89.0),
			Vector2(67.0, 80.0),
			Vector2(70.0, 88.0),
			Vector2(74.0, 85.0),
			Vector2(78.0, 94.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(63.0, 94.0),
			Vector2(64.0, 90.0),
			Vector2(66.0, 92.0),
			Vector2(68.0, 86.0),
			Vector2(70.0, 93.0),
			Vector2(73.0, 90.0),
			Vector2(75.0, 94.0)
		],
		flame
	)
	canvas.draw_line(_p(box, 35.0, 64.0), _p(box, 52.0, 83.0), light, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 58.0, 64.0), _p(box, 44.0, 79.0), light, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 65.0), _p(box, 51.0, 81.0), ink, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 56.0, 65.0), _p(box, 46.0, 77.0), ink, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 88.0), _p(box, 59.0, 88.0), steel, maxf(3.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 83.0), 1.8 * unit, gold)

	# Wild dark-red hair, tied trailing locks, a brow flame mark and long earrings.
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 28.0),
			Vector2(67.0, 20.0),
			Vector2(76.0, 23.0),
			Vector2(81.0, 35.0),
			Vector2(76.0, 49.0),
			Vector2(81.0, 60.0),
			Vector2(69.0, 53.0),
			Vector2(68.0, 39.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 28.0),
			Vector2(68.0, 24.0),
			Vector2(73.0, 27.0),
			Vector2(76.0, 35.0),
			Vector2(72.0, 48.0),
			Vector2(76.0, 54.0),
			Vector2(71.0, 50.0),
			Vector2(72.0, 36.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 30.0),
			Vector2(35.0, 20.0),
			Vector2(55.0, 19.0),
			Vector2(65.0, 29.0),
			Vector2(63.0, 45.0),
			Vector2(55.0, 58.0),
			Vector2(41.0, 59.0),
			Vector2(31.0, 49.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 32.0),
			Vector2(39.0, 25.0),
			Vector2(53.0, 24.0),
			Vector2(59.0, 31.0),
			Vector2(58.0, 44.0),
			Vector2(52.0, 54.0),
			Vector2(42.0, 54.0),
			Vector2(36.0, 47.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 26.0),
			Vector2(58.0, 31.0),
			Vector2(58.0, 43.0),
			Vector2(52.0, 52.0),
			Vector2(48.0, 49.0),
			Vector2(50.0, 41.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 35.0),
			Vector2(25.0, 25.0),
			Vector2(32.0, 26.0),
			Vector2(34.0, 16.0),
			Vector2(42.0, 20.0),
			Vector2(47.0, 11.0),
			Vector2(54.0, 18.0),
			Vector2(61.0, 17.0),
			Vector2(66.0, 28.0),
			Vector2(65.0, 39.0),
			Vector2(58.0, 34.0),
			Vector2(55.0, 26.0),
			Vector2(48.0, 31.0),
			Vector2(44.0, 26.0),
			Vector2(37.0, 36.0),
			Vector2(35.0, 49.0),
			Vector2(29.0, 44.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 34.0, 26.0), _p(box, 39.0, 23.0), red, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 20.0), _p(box, 57.0, 23.0), red, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 32.0),
			Vector2(39.0, 27.0),
			Vector2(43.0, 30.0),
			Vector2(43.0, 35.0),
			Vector2(40.0, 34.0),
			Vector2(39.0, 39.0),
			Vector2(37.0, 36.0)
		],
		red
	)
	canvas.draw_line(_p(box, 37.0, 37.0), _p(box, 43.0, 38.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 38.0), _p(box, 57.0, 36.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 40.0), _p(box, 42.0, 40.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 40.0), _p(box, 56.0, 39.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 38.0), _p(box, 45.0, 45.0), skin, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 43.0, 50.0), _p(box, 51.0, 49.0), ink, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 34.0, 43.0), _p(box, 34.0, 49.0), gold, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 60.0, 43.0), _p(box, 61.0, 49.0), gold, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(31.0, 49.0), Vector2(36.0, 49.0), Vector2(36.0, 58.0), Vector2(31.0, 58.0)],
		light
	)
	_fill(
		canvas,
		box,
		[Vector2(59.0, 49.0), Vector2(64.0, 49.0), Vector2(64.0, 58.0), Vector2(59.0, 58.0)],
		light
	)
	canvas.draw_circle(_p(box, 33.5, 51.5), 1.0 * unit, red)
	canvas.draw_circle(_p(box, 61.5, 51.5), 1.0 * unit, red)
	canvas.draw_line(_p(box, 32.0, 55.0), _p(box, 35.0, 55.0), red, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 60.0, 55.0), _p(box, 63.0, 55.0), red, maxf(1.0 * unit, 1.0), true)

	# A narrow sunfire katana rises at the side, with flame guard and wrapped grip.
	_fill(
		canvas,
		box,
		[
			Vector2(78.0, 10.0),
			Vector2(82.0, 17.0),
			Vector2(81.0, 66.0),
			Vector2(75.0, 66.0),
			Vector2(75.0, 22.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(78.0, 16.0),
			Vector2(79.0, 20.0),
			Vector2(78.0, 62.0),
			Vector2(77.0, 62.0),
			Vector2(77.0, 23.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 80.0, 24.0), _p(box, 79.0, 60.0), flame, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 69.0),
			Vector2(73.0, 62.0),
			Vector2(77.0, 65.0),
			Vector2(82.0, 61.0),
			Vector2(83.0, 66.0),
			Vector2(89.0, 69.0),
			Vector2(83.0, 73.0),
			Vector2(77.0, 71.0),
			Vector2(73.0, 75.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(73.0, 69.0),
			Vector2(76.0, 66.0),
			Vector2(78.0, 68.0),
			Vector2(82.0, 66.0),
			Vector2(84.0, 69.0),
			Vector2(81.0, 70.0),
			Vector2(77.0, 69.0),
			Vector2(75.0, 71.0)
		],
		gold
	)
	canvas.draw_line(_p(box, 78.0, 73.0), _p(box, 78.0, 94.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 74.0), _p(box, 78.0, 93.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 76.0, 77.0), _p(box, 80.0, 79.0), red, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 76.0, 83.0), _p(box, 80.0, 85.0), red, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 76.0, 89.0), _p(box, 80.0, 91.0), red, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 73.0, 83.0), 4.0 * unit, skin)
	canvas.draw_line(_p(box, 71.0, 86.0), _p(box, 76.0, 86.0), shade, maxf(1.5 * unit, 1.0), true)


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
