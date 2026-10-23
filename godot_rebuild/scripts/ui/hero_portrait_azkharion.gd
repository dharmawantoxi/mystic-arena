extends RefCounted
## Native canvas portrait: Azkharion, The Ashen Warlord.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(30, 25, 25)
	var plate := Color8(75, 70, 67)
	var shade := Color8(47, 43, 43)
	var ash := Color8(155, 145, 131)
	var edge := Color8(199, 183, 153)
	var ember := Color8(245, 127, 56)
	var red := Color8(116, 43, 37)
	var skin := Color8(157, 128, 109)
	var scar := Color8(102, 65, 55)
	_backdrop(canvas, box, Color8(90, 54, 43), Color8(27, 26, 29))

	# Jagged smoke and drifting cinders identify the ash theme without animation.
	_fill(
		canvas,
		box,
		[
			Vector2(7.0, 56.0),
			Vector2(13.0, 39.0),
			Vector2(10.0, 30.0),
			Vector2(19.0, 22.0),
			Vector2(17.0, 12.0),
			Vector2(28.0, 23.0),
			Vector2(25.0, 38.0),
			Vector2(30.0, 49.0),
			Vector2(24.0, 62.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(71.0, 54.0),
			Vector2(76.0, 40.0),
			Vector2(72.0, 31.0),
			Vector2(81.0, 21.0),
			Vector2(78.0, 12.0),
			Vector2(89.0, 25.0),
			Vector2(85.0, 39.0),
			Vector2(89.0, 53.0),
			Vector2(83.0, 64.0)
		],
		shade
	)
	canvas.draw_circle(_p(box, 12.0, 19.0), 1.1 * unit, ember)
	canvas.draw_circle(_p(box, 23.0, 42.0), 1.1 * unit, ember)
	canvas.draw_circle(_p(box, 82.0, 17.0), 1.1 * unit, ember)
	canvas.draw_circle(_p(box, 87.0, 59.0), 1.1 * unit, ember)
	canvas.draw_circle(_p(box, 18.0, 65.0), 1.1 * unit, ember)

	# A tattered red mantle hangs beneath soot-black, serrated armour.
	_fill(
		canvas,
		box,
		[
			Vector2(6.0, 96.0),
			Vector2(15.0, 66.0),
			Vector2(31.0, 54.0),
			Vector2(61.0, 54.0),
			Vector2(79.0, 66.0),
			Vector2(90.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 94.0),
			Vector2(20.0, 69.0),
			Vector2(32.0, 60.0),
			Vector2(61.0, 60.0),
			Vector2(74.0, 69.0),
			Vector2(83.0, 93.0),
			Vector2(72.0, 90.0),
			Vector2(66.0, 96.0),
			Vector2(56.0, 91.0),
			Vector2(49.0, 95.0),
			Vector2(36.0, 90.0),
			Vector2(23.0, 96.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 62.0),
			Vector2(40.0, 56.0),
			Vector2(55.0, 57.0),
			Vector2(66.0, 65.0),
			Vector2(68.0, 96.0),
			Vector2(26.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 65.0),
			Vector2(42.0, 61.0),
			Vector2(54.0, 62.0),
			Vector2(61.0, 67.0),
			Vector2(63.0, 94.0),
			Vector2(31.0, 94.0)
		],
		plate
	)
	_fill(
		canvas,
		box,
		[Vector2(34.0, 65.0), Vector2(43.0, 67.0), Vector2(44.0, 76.0), Vector2(35.0, 72.0)],
		ash
	)
	_fill(
		canvas,
		box,
		[
			Vector2(48.0, 67.0),
			Vector2(55.0, 65.0),
			Vector2(60.0, 71.0),
			Vector2(62.0, 93.0),
			Vector2(49.0, 92.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 34.0, 81.0), _p(box, 42.0, 84.0), edge, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 84.0), _p(box, 60.0, 80.0), ash, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 72.0), _p(box, 45.0, 79.0), ember, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 45.0, 79.0), _p(box, 49.0, 83.0), ember, maxf(1.0 * unit, 1.0), true)

	# Uneven spiked pauldrons and riveted plates suggest a battle-worn commander.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 66.0),
			Vector2(10.0, 50.0),
			Vector2(18.0, 55.0),
			Vector2(21.0, 44.0),
			Vector2(28.0, 55.0),
			Vector2(34.0, 53.0),
			Vector2(40.0, 68.0),
			Vector2(31.0, 81.0),
			Vector2(14.0, 77.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 64.0),
			Vector2(17.0, 59.0),
			Vector2(22.0, 61.0),
			Vector2(24.0, 53.0),
			Vector2(28.0, 61.0),
			Vector2(32.0, 59.0),
			Vector2(35.0, 67.0),
			Vector2(29.0, 75.0),
			Vector2(18.0, 73.0)
		],
		plate
	)
	_fill(
		canvas,
		box,
		[
			Vector2(16.0, 63.0),
			Vector2(21.0, 65.0),
			Vector2(28.0, 62.0),
			Vector2(31.0, 65.0),
			Vector2(28.0, 68.0),
			Vector2(19.0, 68.0)
		],
		ash
	)
	_fill(
		canvas,
		box,
		[
			Vector2(56.0, 68.0),
			Vector2(62.0, 54.0),
			Vector2(69.0, 55.0),
			Vector2(76.0, 44.0),
			Vector2(78.0, 56.0),
			Vector2(86.0, 50.0),
			Vector2(87.0, 67.0),
			Vector2(81.0, 78.0),
			Vector2(66.0, 81.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(61.0, 68.0),
			Vector2(66.0, 59.0),
			Vector2(71.0, 61.0),
			Vector2(75.0, 53.0),
			Vector2(75.0, 62.0),
			Vector2(81.0, 59.0),
			Vector2(82.0, 67.0),
			Vector2(77.0, 74.0),
			Vector2(68.0, 76.0)
		],
		plate
	)
	canvas.draw_line(_p(box, 65.0, 64.0), _p(box, 70.0, 66.0), edge, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 73.0, 65.0), _p(box, 79.0, 64.0), ash, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 20.0, 71.0), 1.3 * unit, edge)
	canvas.draw_circle(_p(box, 29.0, 69.0), 1.3 * unit, edge)
	canvas.draw_circle(_p(box, 67.0, 70.0), 1.3 * unit, edge)
	canvas.draw_circle(_p(box, 77.0, 71.0), 1.3 * unit, edge)

	# An open iron war-helm exposes an ashen face, brow scar and short beard.
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 28.0),
			Vector2(36.0, 18.0),
			Vector2(56.0, 18.0),
			Vector2(65.0, 28.0),
			Vector2(64.0, 45.0),
			Vector2(57.0, 56.0),
			Vector2(41.0, 58.0),
			Vector2(31.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 30.0),
			Vector2(39.0, 23.0),
			Vector2(54.0, 23.0),
			Vector2(59.0, 30.0),
			Vector2(59.0, 43.0),
			Vector2(53.0, 52.0),
			Vector2(43.0, 53.0),
			Vector2(36.0, 45.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 25.0),
			Vector2(58.0, 30.0),
			Vector2(59.0, 41.0),
			Vector2(53.0, 50.0),
			Vector2(48.0, 48.0),
			Vector2(50.0, 40.0)
		],
		scar
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 33.0),
			Vector2(24.0, 17.0),
			Vector2(31.0, 20.0),
			Vector2(36.0, 11.0),
			Vector2(47.0, 18.0),
			Vector2(57.0, 11.0),
			Vector2(62.0, 21.0),
			Vector2(69.0, 17.0),
			Vector2(65.0, 34.0),
			Vector2(58.0, 29.0),
			Vector2(37.0, 29.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 28.0),
			Vector2(30.0, 23.0),
			Vector2(34.0, 24.0),
			Vector2(38.0, 17.0),
			Vector2(47.0, 23.0),
			Vector2(56.0, 17.0),
			Vector2(60.0, 25.0),
			Vector2(63.0, 23.0),
			Vector2(62.0, 28.0),
			Vector2(55.0, 25.0),
			Vector2(39.0, 26.0)
		],
		plate
	)
	canvas.draw_line(_p(box, 35.0, 26.0), _p(box, 44.0, 24.0), ash, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 24.0), _p(box, 59.0, 27.0), edge, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 30.0),
			Vector2(35.0, 29.0),
			Vector2(35.0, 40.0),
			Vector2(39.0, 46.0),
			Vector2(35.0, 48.0),
			Vector2(30.0, 42.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(59.0, 29.0),
			Vector2(65.0, 31.0),
			Vector2(64.0, 42.0),
			Vector2(59.0, 48.0),
			Vector2(56.0, 45.0),
			Vector2(60.0, 39.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 37.0, 34.0), _p(box, 43.0, 36.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 36.0), _p(box, 57.0, 34.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 38.0), _p(box, 42.0, 38.0), ember, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 38.0), _p(box, 56.0, 37.0), ember, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 54.0, 30.0), _p(box, 52.0, 41.0), edge, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 36.0), _p(box, 45.0, 43.0), skin, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 44.0),
			Vector2(43.0, 46.0),
			Vector2(48.0, 44.0),
			Vector2(54.0, 45.0),
			Vector2(59.0, 41.0),
			Vector2(56.0, 51.0),
			Vector2(49.0, 57.0),
			Vector2(41.0, 53.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 43.0, 49.0), _p(box, 52.0, 48.0), skin, maxf(1.5 * unit, 1.0), true)

	# A notched executioner axe occupies the right edge, crossed by ember seams.
	canvas.draw_line(_p(box, 79.0, 36.0), _p(box, 74.0, 95.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 79.0, 36.0), _p(box, 74.0, 95.0), ash, maxf(2.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(66.0, 15.0),
			Vector2(78.0, 20.0),
			Vector2(90.0, 15.0),
			Vector2(88.0, 30.0),
			Vector2(82.0, 31.0),
			Vector2(84.0, 37.0),
			Vector2(73.0, 35.0),
			Vector2(66.0, 29.0),
			Vector2(61.0, 19.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 20.0),
			Vector2(78.0, 24.0),
			Vector2(86.0, 21.0),
			Vector2(85.0, 27.0),
			Vector2(78.0, 28.0),
			Vector2(79.0, 32.0),
			Vector2(74.0, 31.0),
			Vector2(68.0, 27.0)
		],
		plate
	)
	_fill(
		canvas,
		box,
		[
			Vector2(86.0, 21.0),
			Vector2(85.0, 27.0),
			Vector2(80.0, 29.0),
			Vector2(79.0, 32.0),
			Vector2(83.0, 33.0),
			Vector2(85.0, 29.0),
			Vector2(87.0, 28.0)
		],
		edge
	)
	canvas.draw_line(_p(box, 68.0, 23.0), _p(box, 76.0, 27.0), ember, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 76.0, 27.0), _p(box, 76.0, 31.0), ember, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 74.0, 43.0), _p(box, 83.0, 45.0), red, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 74.0, 47.0), _p(box, 82.0, 49.0), red, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 78.0),
			Vector2(77.0, 75.0),
			Vector2(83.0, 80.0),
			Vector2(80.0, 89.0),
			Vector2(70.0, 90.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 80.0),
			Vector2(77.0, 79.0),
			Vector2(79.0, 81.0),
			Vector2(77.0, 86.0),
			Vector2(73.0, 86.0)
		],
		plate
	)
	canvas.draw_line(_p(box, 72.0, 82.0), _p(box, 77.0, 82.0), edge, maxf(1.5 * unit, 1.0), true)


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
