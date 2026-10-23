extends RefCounted
## Native canvas portrait: Kazreth, The Blood Reaver.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(31, 24, 28)
	var armor := Color8(85, 48, 51)
	var red := Color8(136, 36, 44)
	var blood := Color8(197, 47, 48)
	var steel := Color8(145, 133, 127)
	var bright := Color8(207, 190, 165)
	var skin := Color8(153, 100, 80)
	var shade := Color8(94, 61, 57)
	var bone := Color8(211, 190, 151)
	var leather := Color8(66, 46, 40)
	_backdrop(canvas, box, Color8(91, 40, 43), Color8(28, 24, 29))

	# Slashing warpaint marks and ember-red sparks frame the heavy reaver.
	canvas.draw_line(_p(box, 9.0, 22.0), _p(box, 24.0, 35.0), red, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 14.0, 15.0), _p(box, 28.0, 27.0), blood, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 73.0, 18.0), _p(box, 88.0, 29.0), red, maxf(5.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 12.0, 43.0), 1.2 * unit, bright)
	canvas.draw_circle(_p(box, 87.0, 43.0), 1.4 * unit, blood)
	canvas.draw_circle(_p(box, 20.0, 10.0), 1.0 * unit, blood)

	# Broad red plate, leather underlayers and a trophies chain dominate the bust.
	_fill(
		canvas,
		box,
		[
			Vector2(3.0, 96.0),
			Vector2(9.0, 70.0),
			Vector2(28.0, 54.0),
			Vector2(65.0, 54.0),
			Vector2(86.0, 70.0),
			Vector2(94.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 94.0),
			Vector2(16.0, 73.0),
			Vector2(31.0, 61.0),
			Vector2(61.0, 61.0),
			Vector2(79.0, 73.0),
			Vector2(87.0, 94.0)
		],
		leather
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 64.0),
			Vector2(43.0, 58.0),
			Vector2(58.0, 64.0),
			Vector2(67.0, 94.0),
			Vector2(25.0, 94.0)
		],
		armor
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 61.0), Vector2(58.0, 66.0), Vector2(63.0, 94.0), Vector2(48.0, 94.0)],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 67.0),
			Vector2(46.0, 75.0),
			Vector2(62.0, 67.0),
			Vector2(58.0, 82.0),
			Vector2(47.0, 89.0),
			Vector2(35.0, 82.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 71.0),
			Vector2(46.0, 77.0),
			Vector2(56.0, 71.0),
			Vector2(53.0, 79.0),
			Vector2(47.0, 83.0),
			Vector2(40.0, 79.0)
		],
		blood
	)
	canvas.draw_arc(
		_p(box, 47.0, 65.0),
		25.0 * unit,
		PI * 0.15,
		PI * 0.85,
		40,
		steel,
		maxf(2.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 30.0, 79.0), 2.5 * unit, bone)
	canvas.draw_circle(_p(box, 64.0, 79.0), 2.5 * unit, bone)
	canvas.draw_line(_p(box, 43.0, 89.0), _p(box, 47.0, 94.0), steel, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 89.0), _p(box, 48.0, 94.0), steel, maxf(2.0 * unit, 1.0), true)

	# Spiked pauldrons and bare forearms keep the silhouette brutal rather than roguish.
	_fill(
		canvas,
		box,
		[
			Vector2(6.0, 70.0),
			Vector2(11.0, 54.0),
			Vector2(18.0, 58.0),
			Vector2(23.0, 46.0),
			Vector2(29.0, 55.0),
			Vector2(38.0, 64.0),
			Vector2(32.0, 79.0),
			Vector2(15.0, 82.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 68.0),
			Vector2(17.0, 60.0),
			Vector2(24.0, 57.0),
			Vector2(32.0, 65.0),
			Vector2(28.0, 73.0),
			Vector2(19.0, 76.0)
		],
		armor
	)
	canvas.draw_line(_p(box, 17.0, 62.0), _p(box, 29.0, 67.0), blood, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 64.0),
			Vector2(67.0, 54.0),
			Vector2(73.0, 46.0),
			Vector2(78.0, 58.0),
			Vector2(85.0, 54.0),
			Vector2(90.0, 70.0),
			Vector2(81.0, 82.0),
			Vector2(64.0, 79.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(64.0, 65.0),
			Vector2(70.0, 57.0),
			Vector2(77.0, 60.0),
			Vector2(83.0, 68.0),
			Vector2(77.0, 76.0),
			Vector2(68.0, 73.0)
		],
		armor
	)
	canvas.draw_line(_p(box, 68.0, 66.0), _p(box, 80.0, 62.0), blood, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 82.0),
			Vector2(20.0, 77.0),
			Vector2(31.0, 83.0),
			Vector2(29.0, 96.0),
			Vector2(12.0, 96.0)
		],
		skin
	)
	canvas.draw_line(_p(box, 16.0, 83.0), _p(box, 25.0, 88.0), red, maxf(3.0 * unit, 1.0), true)

	# A bald scarred head, metal jaw guard and single tusk distinguish the reaver.
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 30.0),
			Vector2(35.0, 18.0),
			Vector2(48.0, 13.0),
			Vector2(61.0, 20.0),
			Vector2(67.0, 32.0),
			Vector2(63.0, 49.0),
			Vector2(55.0, 59.0),
			Vector2(39.0, 58.0),
			Vector2(30.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 31.0),
			Vector2(39.0, 23.0),
			Vector2(48.0, 19.0),
			Vector2(57.0, 24.0),
			Vector2(62.0, 32.0),
			Vector2(59.0, 45.0),
			Vector2(53.0, 53.0),
			Vector2(41.0, 53.0),
			Vector2(35.0, 45.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 21.0),
			Vector2(58.0, 25.0),
			Vector2(62.0, 33.0),
			Vector2(59.0, 45.0),
			Vector2(53.0, 52.0),
			Vector2(48.0, 47.0)
		],
		shade
	)
	canvas.draw_line(_p(box, 40.0, 22.0), _p(box, 44.0, 30.0), red, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 44.0, 30.0), _p(box, 41.0, 36.0), blood, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 34.0, 34.0), _p(box, 43.0, 37.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 37.0), _p(box, 60.0, 33.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 39.0), _p(box, 43.0, 39.0), blood, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 39.0), _p(box, 58.0, 38.0), bright, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 43.0),
			Vector2(46.0, 47.0),
			Vector2(59.0, 42.0),
			Vector2(57.0, 53.0),
			Vector2(50.0, 59.0),
			Vector2(40.0, 55.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(41.0, 47.0),
			Vector2(47.0, 50.0),
			Vector2(54.0, 46.0),
			Vector2(52.0, 52.0),
			Vector2(47.0, 55.0),
			Vector2(43.0, 52.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 43.0, 48.0), _p(box, 52.0, 48.0), bone, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(55.0, 48.0), Vector2(61.0, 46.0), Vector2(58.0, 55.0), Vector2(54.0, 57.0)],
		bone
	)
	canvas.draw_circle(_p(box, 38.0, 49.0), 1.3 * unit, blood)

	# The long-hafted double reaver axe has opposing crescent blades and red edges.
	canvas.draw_line(_p(box, 80.0, 27.0), _p(box, 74.0, 96.0), ink, maxf(8.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 80.0, 27.0), _p(box, 74.0, 96.0), leather, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 34.0),
			Vector2(64.0, 37.0),
			Vector2(57.0, 28.0),
			Vector2(60.0, 14.0),
			Vector2(70.0, 20.0),
			Vector2(78.0, 20.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(73.0, 30.0),
			Vector2(65.0, 32.0),
			Vector2(62.0, 27.0),
			Vector2(64.0, 21.0),
			Vector2(70.0, 25.0),
			Vector2(75.0, 24.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(83.0, 20.0),
			Vector2(91.0, 14.0),
			Vector2(95.0, 25.0),
			Vector2(91.0, 37.0),
			Vector2(82.0, 34.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(85.0, 24.0),
			Vector2(90.0, 21.0),
			Vector2(92.0, 26.0),
			Vector2(89.0, 32.0),
			Vector2(85.0, 30.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[Vector2(74.0, 18.0), Vector2(85.0, 18.0), Vector2(87.0, 35.0), Vector2(75.0, 36.0)],
		armor
	)
	canvas.draw_line(_p(box, 61.0, 19.0), _p(box, 59.0, 28.0), blood, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 93.0, 22.0), _p(box, 92.0, 31.0), blood, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 75.0, 39.0), _p(box, 86.0, 38.0), bright, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 80.0),
			Vector2(74.0, 75.0),
			Vector2(82.0, 79.0),
			Vector2(82.0, 89.0),
			Vector2(74.0, 93.0),
			Vector2(68.0, 89.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 81.0),
			Vector2(75.0, 79.0),
			Vector2(79.0, 81.0),
			Vector2(78.0, 87.0),
			Vector2(73.0, 88.0)
		],
		skin
	)
	canvas.draw_line(_p(box, 70.0, 76.0), _p(box, 80.0, 75.0), steel, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 69.0, 83.0), _p(box, 79.0, 82.0), steel, maxf(1.5 * unit, 1.0), true)


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
