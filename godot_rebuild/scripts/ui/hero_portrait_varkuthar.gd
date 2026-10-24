extends RefCounted
## Native canvas portrait: Varkuthar, The Bloodfire Zealot.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(35, 23, 29)
	var robe := Color8(83, 34, 43)
	var crimson := Color8(151, 44, 46)
	var orange := Color8(235, 100, 39)
	var gold := Color8(213, 157, 65)
	var light := Color8(255, 220, 125)
	var skin := Color8(181, 126, 107)
	var shade := Color8(112, 70, 73)
	var bone := Color8(218, 190, 145)
	_backdrop(canvas, box, Color8(104, 43, 39), Color8(30, 23, 31))

	# A bloodfire halo and ritual sparks backlight the flame-shaped mitre.
	canvas.draw_circle(_p(box, 47.0, 38.0), 32.0 * unit, crimson)
	canvas.draw_arc(
		_p(box, 47.0, 38.0),
		34.0 * unit,
		PI * 0.2,
		PI * 1.8,
		56,
		orange,
		maxf(2.0 * unit, 1.0),
		true
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 45.0),
			Vector2(9.0, 32.0),
			Vector2(16.0, 20.0),
			Vector2(17.0, 35.0),
			Vector2(23.0, 42.0)
		],
		orange
	)
	_fill(
		canvas,
		box,
		[
			Vector2(75.0, 42.0),
			Vector2(81.0, 31.0),
			Vector2(80.0, 18.0),
			Vector2(88.0, 32.0),
			Vector2(85.0, 46.0)
		],
		crimson
	)
	canvas.draw_circle(_p(box, 15.0, 16.0), 1.3 * unit, light)
	canvas.draw_circle(_p(box, 85.0, 13.0), 1.0 * unit, orange)
	canvas.draw_circle(_p(box, 10.0, 54.0), 1.2 * unit, gold)

	# Ceremonial robes use broad crimson panels, gold hems and prayer beads.
	_fill(
		canvas,
		box,
		[
			Vector2(7.0, 96.0),
			Vector2(12.0, 72.0),
			Vector2(30.0, 56.0),
			Vector2(63.0, 56.0),
			Vector2(83.0, 72.0),
			Vector2(90.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 94.0),
			Vector2(19.0, 74.0),
			Vector2(32.0, 63.0),
			Vector2(60.0, 63.0),
			Vector2(76.0, 74.0),
			Vector2(83.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 94.0),
			Vector2(20.0, 75.0),
			Vector2(32.0, 66.0),
			Vector2(41.0, 79.0),
			Vector2(35.0, 94.0)
		],
		crimson
	)
	_fill(
		canvas,
		box,
		[
			Vector2(54.0, 79.0),
			Vector2(61.0, 66.0),
			Vector2(75.0, 75.0),
			Vector2(81.0, 94.0),
			Vector2(61.0, 94.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 61.0),
			Vector2(38.0, 58.0),
			Vector2(47.0, 69.0),
			Vector2(57.0, 58.0),
			Vector2(68.0, 62.0),
			Vector2(57.0, 77.0),
			Vector2(47.0, 83.0),
			Vector2(36.0, 76.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 65.0),
			Vector2(39.0, 64.0),
			Vector2(47.0, 74.0),
			Vector2(56.0, 64.0),
			Vector2(62.0, 65.0),
			Vector2(54.0, 74.0),
			Vector2(47.0, 79.0),
			Vector2(40.0, 73.0)
		],
		robe
	)
	canvas.draw_arc(
		_p(box, 47.0, 61.0),
		24.0 * unit,
		PI * 0.18,
		PI * 0.82,
		36,
		bone,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 30.0, 78.0), 2.0 * unit, bone)
	canvas.draw_circle(_p(box, 64.0, 78.0), 2.0 * unit, bone)

	# The central bloodfire seal is a stylized flame rather than a martial emblem.
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 79.0),
			Vector2(42.0, 71.0),
			Vector2(47.0, 75.0),
			Vector2(53.0, 69.0),
			Vector2(58.0, 80.0),
			Vector2(54.0, 90.0),
			Vector2(47.0, 94.0),
			Vector2(40.0, 89.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(42.0, 81.0),
			Vector2(45.0, 76.0),
			Vector2(48.0, 80.0),
			Vector2(52.0, 75.0),
			Vector2(54.0, 82.0),
			Vector2(51.0, 88.0),
			Vector2(47.0, 90.0),
			Vector2(44.0, 87.0)
		],
		orange
	)
	_fill(
		canvas,
		box,
		[Vector2(46.0, 82.0), Vector2(49.0, 79.0), Vector2(51.0, 84.0), Vector2(48.0, 88.0)],
		light
	)

	# A severe face sits beneath the tall ceremonial flame-mitre.
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 32.0),
			Vector2(37.0, 22.0),
			Vector2(56.0, 21.0),
			Vector2(65.0, 31.0),
			Vector2(62.0, 48.0),
			Vector2(55.0, 58.0),
			Vector2(41.0, 58.0),
			Vector2(32.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 33.0),
			Vector2(41.0, 27.0),
			Vector2(54.0, 26.0),
			Vector2(60.0, 32.0),
			Vector2(58.0, 45.0),
			Vector2(53.0, 53.0),
			Vector2(43.0, 53.0),
			Vector2(37.0, 45.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 27.0),
			Vector2(59.0, 32.0),
			Vector2(59.0, 40.0),
			Vector2(55.0, 48.0),
			Vector2(50.0, 52.0),
			Vector2(47.0, 47.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 34.0),
			Vector2(31.0, 20.0),
			Vector2(39.0, 13.0),
			Vector2(46.0, 3.0),
			Vector2(51.0, 15.0),
			Vector2(61.0, 20.0),
			Vector2(66.0, 34.0),
			Vector2(58.0, 38.0),
			Vector2(37.0, 38.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 31.0),
			Vector2(36.0, 22.0),
			Vector2(42.0, 18.0),
			Vector2(46.0, 10.0),
			Vector2(50.0, 20.0),
			Vector2(57.0, 23.0),
			Vector2(61.0, 31.0),
			Vector2(55.0, 34.0),
			Vector2(39.0, 34.0)
		],
		crimson
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 29.0),
			Vector2(43.0, 26.0),
			Vector2(47.0, 29.0),
			Vector2(53.0, 25.0),
			Vector2(62.0, 29.0),
			Vector2(58.0, 34.0),
			Vector2(37.0, 34.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[Vector2(44.0, 25.0), Vector2(47.0, 20.0), Vector2(51.0, 25.0), Vector2(47.0, 30.0)],
		orange
	)
	canvas.draw_line(_p(box, 36.0, 38.0), _p(box, 43.0, 39.0), ink, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 39.0), _p(box, 59.0, 37.0), ink, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 41.0), _p(box, 43.0, 41.0), light, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 41.0), _p(box, 57.0, 40.0), orange, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 40.0), _p(box, 45.0, 46.0), skin, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 42.0, 50.0), _p(box, 51.0, 49.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 57.0, 42.0), _p(box, 55.0, 48.0), crimson, maxf(1.5 * unit, 1.0), true)

	# A chained censer releases bloodfire; the zealot carries no conventional weapon.
	canvas.draw_circle(_p(box, 75.0, 62.0), 4.0 * unit, skin)
	canvas.draw_line(_p(box, 75.0, 65.0), _p(box, 73.0, 82.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 75.0, 65.0), _p(box, 84.0, 82.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 75.0, 65.0), _p(box, 79.0, 81.0), bone, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(70.0, 82.0),
			Vector2(86.0, 82.0),
			Vector2(84.0, 91.0),
			Vector2(79.0, 96.0),
			Vector2(73.0, 91.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(74.0, 85.0),
			Vector2(82.0, 85.0),
			Vector2(81.0, 90.0),
			Vector2(78.0, 92.0),
			Vector2(75.0, 89.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(73.0, 80.0),
			Vector2(75.0, 70.0),
			Vector2(79.0, 75.0),
			Vector2(83.0, 66.0),
			Vector2(85.0, 79.0),
			Vector2(79.0, 84.0)
		],
		orange
	)
	_fill(
		canvas,
		box,
		[Vector2(77.0, 79.0), Vector2(79.0, 73.0), Vector2(82.0, 78.0), Vector2(79.0, 82.0)],
		light
	)
	canvas.draw_circle(_p(box, 87.0, 65.0), 1.2 * unit, light)


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
