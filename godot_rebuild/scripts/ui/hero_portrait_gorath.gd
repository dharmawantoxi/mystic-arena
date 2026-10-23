extends RefCounted
## Native canvas portrait: Gorath, The Bloodwarden / Blood Hunter.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(33, 23, 30)
	var cloth := Color8(73, 35, 46)
	var red := Color8(161, 45, 54)
	var light := Color8(225, 206, 161)
	var skin := Color8(157, 109, 91)
	var shade := Color8(99, 66, 65)
	var steel := Color8(130, 146, 148)
	var bone := Color8(193, 177, 137)
	var hair := Color8(40, 30, 35)
	var blood := Color8(228, 80, 65)
	_backdrop(canvas, box, Color8(86, 38, 49), Color8(26, 23, 32))

	# An incomplete blood ring and crossed hooked blades frame a lean hunter.
	canvas.draw_arc(
		_p(box, 47.0, 39.0),
		33.0 * unit,
		PI * -0.94,
		PI * -0.12,
		40,
		red,
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 12.0, 45.0), _p(box, 17.0, 40.0), blood, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 77.0, 17.0), _p(box, 84.0, 21.0), red, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 20.0),
			Vector2(21.0, 25.0),
			Vector2(31.0, 45.0),
			Vector2(67.0, 89.0),
			Vector2(61.0, 94.0),
			Vector2(23.0, 49.0),
			Vector2(16.0, 32.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(16.0, 25.0),
			Vector2(20.0, 28.0),
			Vector2(29.0, 46.0),
			Vector2(64.0, 89.0),
			Vector2(62.0, 90.0),
			Vector2(25.0, 48.0),
			Vector2(20.0, 33.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(84.0, 18.0),
			Vector2(81.0, 33.0),
			Vector2(72.0, 49.0),
			Vector2(35.0, 94.0),
			Vector2(29.0, 89.0),
			Vector2(66.0, 44.0),
			Vector2(76.0, 25.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(80.0, 25.0),
			Vector2(78.0, 33.0),
			Vector2(69.0, 48.0),
			Vector2(33.0, 90.0),
			Vector2(32.0, 89.0),
			Vector2(69.0, 44.0),
			Vector2(77.0, 28.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 96.0),
			Vector2(20.0, 70.0),
			Vector2(33.0, 59.0),
			Vector2(58.0, 59.0),
			Vector2(74.0, 71.0),
			Vector2(82.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 94.0),
			Vector2(25.0, 73.0),
			Vector2(35.0, 64.0),
			Vector2(56.0, 64.0),
			Vector2(68.0, 74.0),
			Vector2(76.0, 94.0)
		],
		cloth
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 68.0),
			Vector2(41.0, 62.0),
			Vector2(52.0, 63.0),
			Vector2(61.0, 70.0),
			Vector2(60.0, 94.0),
			Vector2(32.0, 94.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(49.0, 65.0),
			Vector2(56.0, 68.0),
			Vector2(60.0, 73.0),
			Vector2(58.0, 94.0),
			Vector2(49.0, 94.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 35.0, 77.0), _p(box, 44.0, 80.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 80.0), _p(box, 58.0, 76.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 71.0), _p(box, 43.0, 75.0), red, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 75.0), _p(box, 56.0, 70.0), red, maxf(2.0 * unit, 1.0), true)

	# A ragged cowl, bone brow and tooth necklace leave the face exposed.
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 33.0),
			Vector2(28.0, 23.0),
			Vector2(37.0, 14.0),
			Vector2(54.0, 13.0),
			Vector2(65.0, 24.0),
			Vector2(67.0, 43.0),
			Vector2(62.0, 57.0),
			Vector2(56.0, 64.0),
			Vector2(36.0, 64.0),
			Vector2(27.0, 51.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 34.0),
			Vector2(33.0, 25.0),
			Vector2(39.0, 19.0),
			Vector2(53.0, 18.0),
			Vector2(60.0, 27.0),
			Vector2(62.0, 42.0),
			Vector2(58.0, 54.0),
			Vector2(54.0, 59.0),
			Vector2(38.0, 59.0),
			Vector2(31.0, 49.0)
		],
		cloth
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 32.0),
			Vector2(39.0, 24.0),
			Vector2(54.0, 24.0),
			Vector2(61.0, 32.0),
			Vector2(60.0, 45.0),
			Vector2(53.0, 56.0),
			Vector2(42.0, 57.0),
			Vector2(34.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 33.0),
			Vector2(41.0, 28.0),
			Vector2(52.0, 28.0),
			Vector2(57.0, 34.0),
			Vector2(56.0, 44.0),
			Vector2(51.0, 52.0),
			Vector2(43.0, 53.0),
			Vector2(38.0, 45.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 30.0),
			Vector2(56.0, 34.0),
			Vector2(56.0, 43.0),
			Vector2(51.0, 50.0),
			Vector2(48.0, 48.0),
			Vector2(49.0, 40.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 34.0),
			Vector2(35.0, 27.0),
			Vector2(42.0, 23.0),
			Vector2(54.0, 24.0),
			Vector2(60.0, 31.0),
			Vector2(59.0, 39.0),
			Vector2(54.0, 34.0),
			Vector2(49.0, 29.0),
			Vector2(43.0, 34.0),
			Vector2(40.0, 31.0),
			Vector2(36.0, 38.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 31.0),
			Vector2(36.0, 24.0),
			Vector2(44.0, 27.0),
			Vector2(48.0, 20.0),
			Vector2(52.0, 27.0),
			Vector2(59.0, 24.0),
			Vector2(64.0, 31.0),
			Vector2(57.0, 33.0),
			Vector2(49.0, 30.0),
			Vector2(39.0, 33.0)
		],
		bone
	)
	_fill(
		canvas,
		box,
		[Vector2(45.0, 27.0), Vector2(48.0, 24.0), Vector2(51.0, 28.0), Vector2(48.0, 32.0)],
		ink
	)
	canvas.draw_line(_p(box, 38.0, 36.0), _p(box, 44.0, 38.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 38.0), _p(box, 56.0, 35.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 40.0), _p(box, 43.0, 40.0), blood, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 40.0), _p(box, 55.0, 39.0), blood, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 42.0), _p(box, 40.0, 48.0), red, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 54.0, 42.0), _p(box, 53.0, 48.0), red, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 37.0), _p(box, 45.0, 44.0), skin, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 43.0, 49.0), _p(box, 51.0, 48.0), ink, maxf(1.2 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 53.0),
			Vector2(41.0, 61.0),
			Vector2(48.0, 69.0),
			Vector2(60.0, 58.0),
			Vector2(64.0, 52.0),
			Vector2(62.0, 65.0),
			Vector2(49.0, 76.0),
			Vector2(34.0, 66.0)
		],
		red
	)
	canvas.draw_line(_p(box, 36.0, 65.0), _p(box, 48.0, 72.0), bone, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 72.0), _p(box, 60.0, 64.0), bone, maxf(1.5 * unit, 1.0), true)
	_fill(canvas, box, [Vector2(38.0, 68.0), Vector2(41.0, 68.0), Vector2(39.0, 73.0)], light)
	_fill(canvas, box, [Vector2(44.0, 72.0), Vector2(47.0, 72.0), Vector2(45.0, 77.0)], light)
	_fill(canvas, box, [Vector2(51.0, 71.0), Vector2(54.0, 71.0), Vector2(52.0, 76.0)], light)
	_fill(canvas, box, [Vector2(56.0, 67.0), Vector2(59.0, 67.0), Vector2(57.0, 72.0)], light)

	# Leather arm wraps and hooked wrist guards carry small blood-red inlays.
	_fill(
		canvas,
		box,
		[Vector2(17.0, 79.0), Vector2(29.0, 76.0), Vector2(37.0, 94.0), Vector2(18.0, 96.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(21.0, 81.0), Vector2(27.0, 80.0), Vector2(32.0, 92.0), Vector2(21.0, 93.0)],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 81.0),
			Vector2(17.0, 72.0),
			Vector2(22.0, 77.0),
			Vector2(28.0, 79.0),
			Vector2(26.0, 85.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 22.0, 86.0), _p(box, 29.0, 84.0), bone, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 23.0, 90.0), _p(box, 31.0, 88.0), bone, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(63.0, 77.0), Vector2(75.0, 80.0), Vector2(77.0, 96.0), Vector2(57.0, 94.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(65.0, 81.0), Vector2(72.0, 83.0), Vector2(73.0, 93.0), Vector2(62.0, 92.0)],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 80.0),
			Vector2(73.0, 77.0),
			Vector2(78.0, 71.0),
			Vector2(77.0, 83.0),
			Vector2(70.0, 86.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 64.0, 85.0), _p(box, 71.0, 87.0), bone, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 63.0, 89.0), _p(box, 72.0, 91.0), bone, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 25.0, 82.0), 1.5 * unit, blood)
	canvas.draw_circle(_p(box, 69.0, 82.0), 1.5 * unit, blood)


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
