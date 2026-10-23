extends RefCounted
## Native canvas portrait: Ignakhor, The Furnace-Wrought Berserker.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(31, 27, 29)
	var iron := Color8(77, 77, 78)
	var shade := Color8(45, 47, 53)
	var rust := Color8(139, 77, 45)
	var steel := Color8(150, 155, 149)
	var ember := Color8(244, 122, 47)
	var core := Color8(255, 221, 112)
	var skin := Color8(158, 113, 84)
	var darkskin := Color8(102, 73, 65)
	var leather := Color8(84, 55, 40)
	_backdrop(canvas, box, Color8(90, 51, 40), Color8(26, 26, 33))

	# Two smoking furnace vents rise behind a broad, armoured berserker.
	canvas.draw_line(_p(box, 16.0, 53.0), _p(box, 16.0, 20.0), ink, maxf(10.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 16.0, 53.0), _p(box, 16.0, 20.0), iron, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 12.0, 24.0), _p(box, 20.0, 24.0), rust, maxf(3.0 * unit, 1.0), true)
	canvas.draw_arc(
		_p(box, 16.0, 15.0), 7.0 * unit, PI * -0.8, PI * 0.5, 40, shade, maxf(4.0 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 19.0, 10.0), 1.2 * unit, ember)
	canvas.draw_line(_p(box, 78.0, 53.0), _p(box, 78.0, 20.0), ink, maxf(10.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 53.0), _p(box, 78.0, 20.0), iron, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 74.0, 24.0), _p(box, 82.0, 24.0), rust, maxf(3.0 * unit, 1.0), true)
	canvas.draw_arc(
		_p(box, 78.0, 15.0), 7.0 * unit, PI * -0.8, PI * 0.5, 40, shade, maxf(4.0 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 81.0, 10.0), 1.2 * unit, ember)
	_fill(
		canvas,
		box,
		[
			Vector2(4.0, 96.0),
			Vector2(10.0, 67.0),
			Vector2(26.0, 53.0),
			Vector2(63.0, 53.0),
			Vector2(85.0, 69.0),
			Vector2(92.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 94.0),
			Vector2(16.0, 70.0),
			Vector2(29.0, 60.0),
			Vector2(61.0, 60.0),
			Vector2(78.0, 72.0),
			Vector2(85.0, 94.0)
		],
		leather
	)

	# Riveted pauldrons and a glowing grated chest furnace carry the wrought-metal theme.
	_fill(
		canvas,
		box,
		[
			Vector2(7.0, 68.0),
			Vector2(13.0, 50.0),
			Vector2(26.0, 48.0),
			Vector2(38.0, 63.0),
			Vector2(34.0, 81.0),
			Vector2(15.0, 81.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 67.0),
			Vector2(18.0, 56.0),
			Vector2(25.0, 54.0),
			Vector2(32.0, 64.0),
			Vector2(29.0, 76.0),
			Vector2(18.0, 76.0)
		],
		iron
	)
	_fill(
		canvas,
		box,
		[Vector2(15.0, 69.0), Vector2(29.0, 66.0), Vector2(29.0, 72.0), Vector2(18.0, 76.0)],
		rust
	)
	_fill(
		canvas,
		box,
		[
			Vector2(56.0, 63.0),
			Vector2(65.0, 48.0),
			Vector2(80.0, 52.0),
			Vector2(88.0, 68.0),
			Vector2(79.0, 82.0),
			Vector2(62.0, 79.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 64.0),
			Vector2(68.0, 55.0),
			Vector2(76.0, 57.0),
			Vector2(82.0, 68.0),
			Vector2(76.0, 77.0),
			Vector2(66.0, 74.0)
		],
		iron
	)
	canvas.draw_circle(_p(box, 19.0, 61.0), 1.5 * unit, steel)
	canvas.draw_circle(_p(box, 27.0, 65.0), 1.5 * unit, steel)
	canvas.draw_circle(_p(box, 69.0, 61.0), 1.5 * unit, steel)
	canvas.draw_circle(_p(box, 76.0, 67.0), 1.5 * unit, steel)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 65.0),
			Vector2(45.0, 59.0),
			Vector2(59.0, 65.0),
			Vector2(66.0, 94.0),
			Vector2(26.0, 94.0)
		],
		iron
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 63.0), Vector2(58.0, 67.0), Vector2(63.0, 94.0), Vector2(48.0, 94.0)],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 72.0),
			Vector2(47.0, 67.0),
			Vector2(60.0, 73.0),
			Vector2(59.0, 88.0),
			Vector2(47.0, 94.0),
			Vector2(34.0, 88.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(38.0, 74.0),
			Vector2(47.0, 71.0),
			Vector2(56.0, 75.0),
			Vector2(55.0, 86.0),
			Vector2(47.0, 90.0),
			Vector2(38.0, 86.0)
		],
		rust
	)
	_fill(
		canvas,
		box,
		[
			Vector2(41.0, 75.0),
			Vector2(47.0, 73.0),
			Vector2(53.0, 76.0),
			Vector2(52.0, 85.0),
			Vector2(47.0, 87.0),
			Vector2(41.0, 84.0)
		],
		ember
	)
	_fill(
		canvas,
		box,
		[
			Vector2(45.0, 76.0),
			Vector2(49.0, 76.0),
			Vector2(50.0, 83.0),
			Vector2(46.0, 86.0),
			Vector2(44.0, 82.0)
		],
		core
	)
	canvas.draw_line(_p(box, 41.0, 74.0), _p(box, 42.0, 87.0), iron, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 46.0, 74.0), _p(box, 47.0, 87.0), iron, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 74.0), _p(box, 52.0, 87.0), iron, maxf(2.0 * unit, 1.0), true)

	# A scarred exposed lower face sits beneath a heavy angular half-helm.
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 29.0),
			Vector2(35.0, 19.0),
			Vector2(56.0, 18.0),
			Vector2(66.0, 29.0),
			Vector2(64.0, 46.0),
			Vector2(56.0, 58.0),
			Vector2(39.0, 59.0),
			Vector2(29.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 31.0),
			Vector2(39.0, 24.0),
			Vector2(54.0, 24.0),
			Vector2(60.0, 32.0),
			Vector2(59.0, 44.0),
			Vector2(53.0, 53.0),
			Vector2(41.0, 54.0),
			Vector2(35.0, 46.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 26.0),
			Vector2(58.0, 31.0),
			Vector2(60.0, 36.0),
			Vector2(57.0, 46.0),
			Vector2(52.0, 52.0),
			Vector2(48.0, 49.0)
		],
		darkskin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 32.0),
			Vector2(27.0, 22.0),
			Vector2(34.0, 21.0),
			Vector2(37.0, 11.0),
			Vector2(46.0, 17.0),
			Vector2(55.0, 10.0),
			Vector2(60.0, 21.0),
			Vector2(67.0, 22.0),
			Vector2(67.0, 34.0),
			Vector2(57.0, 30.0),
			Vector2(38.0, 31.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 28.0),
			Vector2(32.0, 25.0),
			Vector2(38.0, 24.0),
			Vector2(40.0, 17.0),
			Vector2(46.0, 23.0),
			Vector2(53.0, 16.0),
			Vector2(57.0, 25.0),
			Vector2(62.0, 26.0),
			Vector2(62.0, 29.0),
			Vector2(55.0, 27.0),
			Vector2(39.0, 28.0)
		],
		iron
	)
	canvas.draw_line(_p(box, 37.0, 26.0), _p(box, 44.0, 25.0), steel, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 25.0), _p(box, 59.0, 27.0), rust, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 35.0, 36.0), _p(box, 43.0, 38.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 38.0), _p(box, 59.0, 35.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 40.0), _p(box, 42.0, 40.0), ember, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 40.0), _p(box, 57.0, 39.0), core, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 38.0), _p(box, 45.0, 44.0), skin, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 49.0), _p(box, 55.0, 48.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 54.0, 30.0), _p(box, 52.0, 45.0), steel, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 43.0, 53.0), _p(box, 51.0, 52.0), darkskin, maxf(2.0 * unit, 1.0), true
	)

	# A notched forge axe, wrapped grip and iron gauntlet establish the melee role.
	canvas.draw_line(_p(box, 78.0, 39.0), _p(box, 75.0, 95.0), ink, maxf(7.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 39.0), _p(box, 75.0, 95.0), rust, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 12.0),
			Vector2(79.0, 18.0),
			Vector2(90.0, 13.0),
			Vector2(89.0, 31.0),
			Vector2(82.0, 38.0),
			Vector2(70.0, 34.0),
			Vector2(63.0, 22.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(69.0, 18.0),
			Vector2(78.0, 23.0),
			Vector2(86.0, 19.0),
			Vector2(85.0, 29.0),
			Vector2(80.0, 33.0),
			Vector2(73.0, 30.0),
			Vector2(68.0, 23.0)
		],
		iron
	)
	_fill(
		canvas,
		box,
		[
			Vector2(86.0, 19.0),
			Vector2(85.0, 29.0),
			Vector2(80.0, 33.0),
			Vector2(83.0, 33.0),
			Vector2(88.0, 29.0),
			Vector2(88.0, 22.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 71.0, 23.0), _p(box, 77.0, 27.0), ember, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 77.0, 27.0), _p(box, 79.0, 32.0), ember, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 79.0),
			Vector2(77.0, 75.0),
			Vector2(84.0, 81.0),
			Vector2(81.0, 91.0),
			Vector2(70.0, 92.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 81.0),
			Vector2(77.0, 79.0),
			Vector2(80.0, 83.0),
			Vector2(78.0, 88.0),
			Vector2(73.0, 88.0)
		],
		iron
	)
	canvas.draw_line(_p(box, 72.0, 84.0), _p(box, 79.0, 84.0), steel, maxf(1.5 * unit, 1.0), true)


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
