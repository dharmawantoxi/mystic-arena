extends RefCounted
## Native canvas portrait: Brumhar, The Glacier Reaver / Glacier Warrior.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(22, 32, 43)
	var steel := Color8(71, 99, 117)
	var shade := Color8(42, 63, 82)
	var ice := Color8(128, 205, 225)
	var light := Color8(220, 247, 244)
	var fur := Color8(169, 180, 174)
	var skin := Color8(167, 165, 158)
	var darkskin := Color8(110, 129, 137)
	var hair := Color8(204, 218, 212)
	var leather := Color8(89, 68, 52)
	_backdrop(canvas, box, Color8(48, 90, 116), Color8(20, 32, 48))

	# Glacier shards and diagonal snow streaks frame a fur-clad reaver.
	_fill(
		canvas,
		box,
		[
			Vector2(4.0, 62.0),
			Vector2(12.0, 27.0),
			Vector2(21.0, 47.0),
			Vector2(28.0, 36.0),
			Vector2(32.0, 64.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[Vector2(9.0, 55.0), Vector2(13.0, 36.0), Vector2(16.0, 49.0), Vector2(14.0, 59.0)],
		ice
	)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 60.0),
			Vector2(74.0, 32.0),
			Vector2(81.0, 43.0),
			Vector2(89.0, 22.0),
			Vector2(93.0, 63.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 7.0, 17.0), _p(box, 17.0, 13.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 20.0, 32.0), _p(box, 28.0, 28.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 70.0, 16.0), _p(box, 80.0, 12.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 82.0, 52.0), _p(box, 91.0, 48.0), light, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(5.0, 96.0),
			Vector2(12.0, 68.0),
			Vector2(28.0, 54.0),
			Vector2(62.0, 54.0),
			Vector2(83.0, 68.0),
			Vector2(91.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 94.0),
			Vector2(18.0, 71.0),
			Vector2(30.0, 60.0),
			Vector2(61.0, 60.0),
			Vector2(77.0, 72.0),
			Vector2(84.0, 94.0)
		],
		leather
	)

	# Heavy frost armour has irregular ice caps over a thick wolf-fur collar.
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 66.0),
			Vector2(25.0, 52.0),
			Vector2(36.0, 58.0),
			Vector2(46.0, 67.0),
			Vector2(59.0, 57.0),
			Vector2(70.0, 54.0),
			Vector2(81.0, 67.0),
			Vector2(70.0, 79.0),
			Vector2(56.0, 72.0),
			Vector2(46.0, 78.0),
			Vector2(34.0, 72.0),
			Vector2(22.0, 78.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(17.0, 66.0),
			Vector2(26.0, 57.0),
			Vector2(35.0, 63.0),
			Vector2(44.0, 71.0),
			Vector2(46.0, 67.0),
			Vector2(55.0, 65.0),
			Vector2(62.0, 60.0),
			Vector2(69.0, 59.0),
			Vector2(75.0, 67.0),
			Vector2(68.0, 72.0),
			Vector2(58.0, 68.0),
			Vector2(46.0, 74.0),
			Vector2(34.0, 68.0),
			Vector2(24.0, 72.0)
		],
		fur
	)
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 72.0),
			Vector2(15.0, 58.0),
			Vector2(29.0, 59.0),
			Vector2(37.0, 70.0),
			Vector2(31.0, 86.0),
			Vector2(12.0, 85.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 73.0),
			Vector2(18.0, 63.0),
			Vector2(27.0, 64.0),
			Vector2(32.0, 71.0),
			Vector2(28.0, 81.0),
			Vector2(16.0, 81.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 70.0),
			Vector2(17.0, 60.0),
			Vector2(22.0, 66.0),
			Vector2(26.0, 61.0),
			Vector2(29.0, 68.0),
			Vector2(25.0, 72.0),
			Vector2(18.0, 74.0)
		],
		ice
	)
	_fill(
		canvas,
		box,
		[
			Vector2(57.0, 70.0),
			Vector2(65.0, 59.0),
			Vector2(79.0, 58.0),
			Vector2(87.0, 72.0),
			Vector2(83.0, 85.0),
			Vector2(64.0, 86.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 71.0),
			Vector2(67.0, 64.0),
			Vector2(77.0, 63.0),
			Vector2(82.0, 73.0),
			Vector2(79.0, 81.0),
			Vector2(66.0, 81.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(64.0, 68.0),
			Vector2(69.0, 61.0),
			Vector2(73.0, 66.0),
			Vector2(78.0, 60.0),
			Vector2(81.0, 70.0),
			Vector2(76.0, 74.0),
			Vector2(68.0, 72.0)
		],
		ice
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 74.0),
			Vector2(45.0, 79.0),
			Vector2(58.0, 73.0),
			Vector2(64.0, 94.0),
			Vector2(28.0, 94.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 45.0, 81.0), _p(box, 45.0, 94.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 34.0, 81.0), _p(box, 41.0, 84.0), ice, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 84.0), _p(box, 58.0, 80.0), ice, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 29.0, 75.0), _p(box, 61.0, 94.0), leather, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 31.0, 77.0), _p(box, 59.0, 94.0), fur, maxf(1.0 * unit, 1.0), true)

	# A scarred open face, ice-grey beard and stout horned iron helm.
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 28.0),
			Vector2(34.0, 18.0),
			Vector2(56.0, 18.0),
			Vector2(66.0, 29.0),
			Vector2(64.0, 45.0),
			Vector2(56.0, 58.0),
			Vector2(39.0, 60.0),
			Vector2(29.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 30.0),
			Vector2(38.0, 23.0),
			Vector2(54.0, 23.0),
			Vector2(60.0, 31.0),
			Vector2(59.0, 44.0),
			Vector2(53.0, 53.0),
			Vector2(41.0, 54.0),
			Vector2(35.0, 45.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 25.0),
			Vector2(57.0, 29.0),
			Vector2(60.0, 32.0),
			Vector2(57.0, 45.0),
			Vector2(53.0, 52.0),
			Vector2(48.0, 48.0)
		],
		darkskin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 29.0),
			Vector2(21.0, 23.0),
			Vector2(18.0, 11.0),
			Vector2(26.0, 16.0),
			Vector2(29.0, 21.0),
			Vector2(35.0, 17.0),
			Vector2(55.0, 16.0),
			Vector2(63.0, 22.0),
			Vector2(70.0, 16.0),
			Vector2(75.0, 10.0),
			Vector2(72.0, 25.0),
			Vector2(64.0, 31.0),
			Vector2(57.0, 28.0),
			Vector2(36.0, 29.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 22.0),
			Vector2(22.0, 17.0),
			Vector2(26.0, 21.0),
			Vector2(30.0, 26.0),
			Vector2(34.0, 23.0),
			Vector2(34.0, 27.0),
			Vector2(29.0, 28.0)
		],
		fur
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 27.0),
			Vector2(66.0, 24.0),
			Vector2(70.0, 20.0),
			Vector2(69.0, 24.0),
			Vector2(64.0, 28.0)
		],
		fur
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 26.0),
			Vector2(37.0, 21.0),
			Vector2(53.0, 20.0),
			Vector2(59.0, 25.0),
			Vector2(60.0, 30.0),
			Vector2(53.0, 27.0),
			Vector2(38.0, 28.0),
			Vector2(33.0, 31.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 37.0, 24.0), _p(box, 53.0, 23.0), ice, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 36.0, 35.0), _p(box, 42.0, 36.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 36.0), _p(box, 57.0, 34.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 39.0), _p(box, 41.0, 39.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 39.0), _p(box, 56.0, 38.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 54.0, 31.0), _p(box, 52.0, 44.0), ice, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 36.0), _p(box, 45.0, 43.0), skin, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 43.0),
			Vector2(40.0, 46.0),
			Vector2(46.0, 44.0),
			Vector2(53.0, 46.0),
			Vector2(60.0, 41.0),
			Vector2(57.0, 53.0),
			Vector2(50.0, 64.0),
			Vector2(46.0, 60.0),
			Vector2(41.0, 64.0),
			Vector2(36.0, 54.0)
		],
		hair
	)
	canvas.draw_line(
		_p(box, 41.0, 49.0), _p(box, 51.0, 49.0), darkskin, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 41.0, 54.0), _p(box, 43.0, 58.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 53.0), _p(box, 50.0, 58.0), light, maxf(1.5 * unit, 1.0), true)

	# A chipped frost cleaver and a strapped gauntlet finish the melee silhouette.
	canvas.draw_line(_p(box, 79.0, 36.0), _p(box, 75.0, 95.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 79.0, 36.0), _p(box, 75.0, 95.0), leather, maxf(2.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(71.0, 12.0),
			Vector2(85.0, 9.0),
			Vector2(90.0, 19.0),
			Vector2(87.0, 26.0),
			Vector2(89.0, 32.0),
			Vector2(81.0, 39.0),
			Vector2(71.0, 34.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(74.0, 16.0),
			Vector2(83.0, 13.0),
			Vector2(86.0, 19.0),
			Vector2(83.0, 26.0),
			Vector2(85.0, 31.0),
			Vector2(80.0, 35.0),
			Vector2(74.0, 31.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(83.0, 13.0),
			Vector2(86.0, 19.0),
			Vector2(83.0, 26.0),
			Vector2(85.0, 31.0),
			Vector2(80.0, 35.0),
			Vector2(78.0, 32.0),
			Vector2(81.0, 25.0),
			Vector2(81.0, 17.0)
		],
		ice
	)
	canvas.draw_line(_p(box, 83.0, 17.0), _p(box, 83.0, 21.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 81.0, 28.0), _p(box, 80.0, 31.0), light, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 79.0),
			Vector2(77.0, 76.0),
			Vector2(83.0, 81.0),
			Vector2(80.0, 90.0),
			Vector2(70.0, 90.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 81.0),
			Vector2(77.0, 80.0),
			Vector2(79.0, 82.0),
			Vector2(77.0, 87.0),
			Vector2(73.0, 87.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 72.0, 84.0), _p(box, 78.0, 84.0), fur, maxf(2.0 * unit, 1.0), true)


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
