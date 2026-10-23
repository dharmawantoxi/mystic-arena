extends RefCounted
## Native canvas portrait: Celwynn, The Star Caretaker / Star Mage.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(25, 27, 50)
	var robe := Color8(61, 53, 110)
	var purple := Color8(101, 81, 154)
	var gold := Color8(203, 178, 110)
	var light := Color8(253, 240, 181)
	var skin := Color8(191, 169, 158)
	var shade := Color8(130, 118, 147)
	var hair := Color8(216, 219, 226)
	var magic := Color8(148, 213, 245)
	var night := Color8(32, 43, 76)
	_backdrop(canvas, box, Color8(45, 53, 96), Color8(20, 24, 45))

	# A ring of tiny stars and a crescent veil frame a calm caretaker.
	canvas.draw_arc(
		_p(box, 47.0, 38.0),
		31.0 * unit,
		PI * -0.95,
		PI * -0.05,
		40,
		gold,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 13.0, 27.0), _p(box, 17.0, 27.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 15.0, 25.0), _p(box, 15.0, 29.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 23.0, 14.0), _p(box, 27.0, 14.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 25.0, 12.0), _p(box, 25.0, 16.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 45.0, 7.0), _p(box, 49.0, 7.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 5.0), _p(box, 47.0, 9.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 67.0, 14.0), _p(box, 71.0, 14.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 69.0, 12.0), _p(box, 69.0, 16.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 77.0, 27.0), _p(box, 81.0, 27.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 79.0, 25.0), _p(box, 79.0, 29.0), light, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 96.0),
			Vector2(19.0, 69.0),
			Vector2(31.0, 55.0),
			Vector2(61.0, 55.0),
			Vector2(75.0, 71.0),
			Vector2(82.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(19.0, 94.0),
			Vector2(24.0, 72.0),
			Vector2(33.0, 60.0),
			Vector2(59.0, 60.0),
			Vector2(70.0, 74.0),
			Vector2(77.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 75.0),
			Vector2(34.0, 66.0),
			Vector2(45.0, 75.0),
			Vector2(41.0, 94.0),
			Vector2(20.0, 94.0)
		],
		purple
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 74.0),
			Vector2(61.0, 65.0),
			Vector2(69.0, 76.0),
			Vector2(74.0, 94.0),
			Vector2(53.0, 94.0)
		],
		night
	)
	canvas.draw_line(_p(box, 30.0, 67.0), _p(box, 44.0, 79.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 61.0, 67.0), _p(box, 51.0, 79.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 76.0), 5.0 * unit, gold)
	canvas.draw_circle(_p(box, 48.0, 76.0), 3.0 * unit, magic)

	# A soft hood, silver side locks and a lowered, kindly gaze.
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 34.0),
			Vector2(29.0, 23.0),
			Vector2(38.0, 15.0),
			Vector2(54.0, 14.0),
			Vector2(65.0, 24.0),
			Vector2(69.0, 44.0),
			Vector2(65.0, 59.0),
			Vector2(57.0, 66.0),
			Vector2(36.0, 65.0),
			Vector2(27.0, 54.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 33.0),
			Vector2(34.0, 24.0),
			Vector2(40.0, 20.0),
			Vector2(53.0, 19.0),
			Vector2(61.0, 27.0),
			Vector2(64.0, 44.0),
			Vector2(60.0, 58.0),
			Vector2(55.0, 61.0),
			Vector2(38.0, 60.0),
			Vector2(32.0, 51.0)
		],
		purple
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 32.0),
			Vector2(39.0, 23.0),
			Vector2(51.0, 21.0),
			Vector2(59.0, 28.0),
			Vector2(62.0, 40.0),
			Vector2(59.0, 43.0),
			Vector2(56.0, 30.0),
			Vector2(50.0, 25.0),
			Vector2(40.0, 27.0),
			Vector2(35.0, 35.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 33.0),
			Vector2(41.0, 27.0),
			Vector2(51.0, 27.0),
			Vector2(57.0, 33.0),
			Vector2(57.0, 44.0),
			Vector2(51.0, 53.0),
			Vector2(43.0, 54.0),
			Vector2(37.0, 47.0),
			Vector2(34.0, 40.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 29.0),
			Vector2(56.0, 33.0),
			Vector2(57.0, 43.0),
			Vector2(51.0, 51.0),
			Vector2(47.0, 49.0),
			Vector2(49.0, 41.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 32.0),
			Vector2(39.0, 26.0),
			Vector2(46.0, 25.0),
			Vector2(43.0, 31.0),
			Vector2(37.0, 36.0),
			Vector2(37.0, 49.0),
			Vector2(41.0, 56.0),
			Vector2(36.0, 55.0),
			Vector2(31.0, 45.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(53.0, 27.0),
			Vector2(58.0, 33.0),
			Vector2(61.0, 43.0),
			Vector2(58.0, 55.0),
			Vector2(53.0, 59.0),
			Vector2(55.0, 48.0),
			Vector2(56.0, 38.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 38.0, 37.0), _p(box, 43.0, 38.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 38.0), _p(box, 55.0, 36.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 40.0), _p(box, 43.0, 40.0), magic, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 40.0), _p(box, 55.0, 39.0), magic, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 38.0), _p(box, 45.0, 44.0), skin, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 43.0, 49.0), _p(box, 50.0, 49.0), ink, maxf(1.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 47.0, 27.0), 1.8 * unit, light)

	# Two cupped hands cradle a bright star above a miniature celestial bowl.
	_fill(
		canvas,
		box,
		[
			Vector2(25.0, 77.0),
			Vector2(34.0, 74.0),
			Vector2(45.0, 84.0),
			Vector2(43.0, 90.0),
			Vector2(32.0, 86.0),
			Vector2(25.0, 83.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 78.0),
			Vector2(33.0, 78.0),
			Vector2(42.0, 85.0),
			Vector2(40.0, 87.0),
			Vector2(33.0, 83.0),
			Vector2(29.0, 82.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 84.0),
			Vector2(62.0, 74.0),
			Vector2(71.0, 77.0),
			Vector2(71.0, 83.0),
			Vector2(64.0, 86.0),
			Vector2(53.0, 90.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(55.0, 85.0),
			Vector2(63.0, 78.0),
			Vector2(67.0, 78.0),
			Vector2(67.0, 82.0),
			Vector2(63.0, 83.0),
			Vector2(57.0, 87.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 83.0),
			Vector2(47.0, 89.0),
			Vector2(61.0, 83.0),
			Vector2(58.0, 91.0),
			Vector2(47.0, 95.0),
			Vector2(37.0, 91.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(38.0, 86.0),
			Vector2(47.0, 90.0),
			Vector2(57.0, 86.0),
			Vector2(55.0, 90.0),
			Vector2(47.0, 92.0),
			Vector2(40.0, 90.0)
		],
		night
	)
	canvas.draw_circle(_p(box, 48.0, 67.0), 13.0 * unit, purple)
	canvas.draw_circle(_p(box, 48.0, 67.0), 9.0 * unit, magic)
	_fill(
		canvas,
		box,
		[
			Vector2(48.0, 55.0),
			Vector2(51.0, 63.0),
			Vector2(59.0, 64.0),
			Vector2(53.0, 70.0),
			Vector2(55.0, 78.0),
			Vector2(48.0, 74.0),
			Vector2(41.0, 78.0),
			Vector2(43.0, 70.0),
			Vector2(37.0, 64.0),
			Vector2(45.0, 63.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(48.0, 58.0),
			Vector2(50.0, 65.0),
			Vector2(56.0, 66.0),
			Vector2(51.0, 69.0),
			Vector2(52.0, 74.0),
			Vector2(48.0, 71.0),
			Vector2(44.0, 74.0),
			Vector2(45.0, 69.0),
			Vector2(40.0, 66.0),
			Vector2(46.0, 65.0)
		],
		light
	)
	canvas.draw_circle(_p(box, 27.0, 58.0), 1.2 * unit, light)
	canvas.draw_circle(_p(box, 68.0, 54.0), 1.5 * unit, magic)
	canvas.draw_arc(
		_p(box, 48.0, 67.0),
		16.0 * unit,
		PI * -0.6,
		PI * 0.25,
		40,
		magic,
		maxf(1.0 * unit, 1.0),
		true
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
