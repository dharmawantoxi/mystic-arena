extends RefCounted
## Native canvas painter for Drakar, the Boss/Berserker Hero Shop portrait.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(22, 16, 21)
	var armor := Color8(74, 36, 43)
	var armor_light := Color8(143, 52, 47)
	var steel := Color8(125, 128, 128)
	var steel_light := Color8(222, 190, 142)
	var skin := Color8(163, 91, 64)
	var ember := Color8(245, 91, 38)
	var hot := Color8(255, 190, 70)

	_backdrop(canvas, box, Color8(94, 40, 37), Color8(18, 15, 21))
	canvas.draw_arc(
		_p(box, 48.0, 47.0),
		39.0 * unit,
		-PI * 0.88,
		-PI * 0.12,
		32,
		Color(ember.r, ember.g, ember.b, 0.28),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 47.0),
		32.0 * unit,
		PI * 0.14,
		PI * 0.82,
		28,
		Color(hot.r, hot.g, hot.b, 0.18),
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 13.0, 39.0), 2.2 * unit, ember)
	canvas.draw_circle(_p(box, 82.0, 31.0), 2.5 * unit, hot)
	canvas.draw_circle(_p(box, 20.0, 56.0), 1.5 * unit, hot)
	canvas.draw_circle(_p(box, 78.0, 69.0), 1.8 * unit, ember)

	# A heavy split-blade axe sits behind the shoulder.
	_fill(
		canvas,
		box,
		[Vector2(74.0, 49.0), Vector2(80.0, 51.0), Vector2(61.0, 91.0), Vector2(55.0, 88.0)],
		outline
	)
	_fill(
		canvas,
		box,
		[Vector2(76.0, 51.0), Vector2(78.0, 52.0), Vector2(60.0, 87.0), Vector2(58.0, 86.0)],
		steel_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 43.0),
			Vector2(77.0, 32.0),
			Vector2(88.0, 35.0),
			Vector2(91.0, 45.0),
			Vector2(86.0, 57.0),
			Vector2(75.0, 59.0),
			Vector2(68.0, 53.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(75.0, 42.0),
			Vector2(79.0, 36.0),
			Vector2(86.0, 38.0),
			Vector2(88.0, 45.0),
			Vector2(84.0, 53.0),
			Vector2(76.0, 55.0),
			Vector2(72.0, 51.0),
		],
		steel
	)
	canvas.draw_line(_p(box, 78.0, 40.0), _p(box, 86.0, 43.0), hot, maxf(1.5 * unit, 1.0), true)

	# Broad armored silhouette and spiked shoulders.
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 91.0),
			Vector2(14.0, 72.0),
			Vector2(24.0, 62.0),
			Vector2(37.0, 56.0),
			Vector2(59.0, 56.0),
			Vector2(73.0, 64.0),
			Vector2(85.0, 90.0),
			Vector2(82.0, 96.0),
			Vector2(13.0, 96.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(16.0, 91.0),
			Vector2(21.0, 72.0),
			Vector2(31.0, 64.0),
			Vector2(43.0, 60.0),
			Vector2(56.0, 60.0),
			Vector2(68.0, 68.0),
			Vector2(78.0, 91.0),
		],
		armor
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 70.0),
			Vector2(9.0, 58.0),
			Vector2(18.0, 62.0),
			Vector2(23.0, 53.0),
			Vector2(28.0, 61.0),
			Vector2(38.0, 64.0),
			Vector2(37.0, 78.0),
			Vector2(25.0, 86.0),
			Vector2(13.0, 82.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 70.0),
			Vector2(14.0, 64.0),
			Vector2(20.0, 68.0),
			Vector2(24.0, 60.0),
			Vector2(28.0, 67.0),
			Vector2(34.0, 68.0),
			Vector2(33.0, 77.0),
			Vector2(24.0, 82.0),
			Vector2(16.0, 79.0),
		],
		armor_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 64.0),
			Vector2(68.0, 61.0),
			Vector2(74.0, 54.0),
			Vector2(76.0, 64.0),
			Vector2(86.0, 61.0),
			Vector2(82.0, 71.0),
			Vector2(84.0, 82.0),
			Vector2(72.0, 86.0),
			Vector2(61.0, 79.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 67.0),
			Vector2(70.0, 65.0),
			Vector2(74.0, 60.0),
			Vector2(76.0, 67.0),
			Vector2(82.0, 65.0),
			Vector2(79.0, 72.0),
			Vector2(80.0, 78.0),
			Vector2(72.0, 81.0),
			Vector2(64.0, 76.0),
		],
		armor_light
	)
	canvas.draw_line(
		_p(box, 18.0, 74.0), _p(box, 31.0, 70.0), steel_light, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 67.0, 72.0), _p(box, 78.0, 68.0), steel_light, maxf(2.0 * unit, 1.0), true
	)

	# Curved horns, mane, and the strong jaw frame the face.
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 28.0),
			Vector2(28.0, 22.0),
			Vector2(17.0, 13.0),
			Vector2(21.0, 28.0),
			Vector2(27.0, 37.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 28.0),
			Vector2(27.0, 23.0),
			Vector2(22.0, 18.0),
			Vector2(25.0, 29.0),
			Vector2(29.0, 34.0),
		],
		steel_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(61.0, 28.0),
			Vector2(68.0, 22.0),
			Vector2(79.0, 13.0),
			Vector2(75.0, 28.0),
			Vector2(69.0, 37.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 28.0),
			Vector2(69.0, 23.0),
			Vector2(74.0, 18.0),
			Vector2(71.0, 29.0),
			Vector2(67.0, 34.0),
		],
		steel_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 31.0),
			Vector2(29.0, 19.0),
			Vector2(39.0, 11.0),
			Vector2(49.0, 8.0),
			Vector2(57.0, 12.0),
			Vector2(66.0, 12.0),
			Vector2(70.0, 22.0),
			Vector2(66.0, 34.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 27.0),
			Vector2(34.0, 19.0),
			Vector2(42.0, 13.0),
			Vector2(49.0, 12.0),
			Vector2(56.0, 16.0),
			Vector2(63.0, 15.0),
			Vector2(65.0, 25.0),
			Vector2(59.0, 31.0),
		],
		armor_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 27.0),
			Vector2(32.0, 24.0),
			Vector2(36.0, 21.0),
			Vector2(38.0, 28.0),
			Vector2(35.0, 34.0),
		],
		ember
	)
	_fill(
		canvas,
		box,
		[
			Vector2(63.0, 25.0),
			Vector2(67.0, 22.0),
			Vector2(68.0, 29.0),
			Vector2(65.0, 35.0),
		],
		ember
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 26.0),
			Vector2(36.0, 19.0),
			Vector2(43.0, 16.0),
			Vector2(56.0, 17.0),
			Vector2(63.0, 24.0),
			Vector2(65.0, 38.0),
			Vector2(61.0, 48.0),
			Vector2(54.0, 55.0),
			Vector2(43.0, 55.0),
			Vector2(35.0, 48.0),
			Vector2(31.0, 38.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 28.0),
			Vector2(40.0, 23.0),
			Vector2(53.0, 22.0),
			Vector2(59.0, 28.0),
			Vector2(60.0, 39.0),
			Vector2(56.0, 46.0),
			Vector2(49.0, 51.0),
			Vector2(42.0, 49.0),
			Vector2(36.0, 42.0),
		],
		skin
	)
	canvas.draw_line(_p(box, 34.0, 32.0), _p(box, 44.0, 29.0), outline, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 29.0), _p(box, 63.0, 32.0), outline, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 34.0), _p(box, 43.0, 35.0), hot, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 35.0), _p(box, 59.0, 34.0), hot, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 35.0), _p(box, 47.0, 42.0), outline, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 39.0, 39.0), _p(box, 44.0, 40.0), Color8(255, 213, 164), maxf(unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 56.0, 39.0), _p(box, 52.0, 40.0), Color8(255, 213, 164), maxf(unit, 1.0), true
	)

	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 43.0),
			Vector2(42.0, 46.0),
			Vector2(48.0, 44.0),
			Vector2(54.0, 46.0),
			Vector2(59.0, 42.0),
			Vector2(57.0, 51.0),
			Vector2(50.0, 56.0),
			Vector2(42.0, 54.0),
			Vector2(37.0, 49.0),
		],
		armor
	)
	canvas.draw_line(_p(box, 42.0, 47.0), _p(box, 44.0, 51.0), steel_light, maxf(unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 47.0), _p(box, 52.0, 51.0), steel_light, maxf(unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 47.0), _p(box, 48.0, 51.0), ember, maxf(1.5 * unit, 1.0), true)

	# The split breastplate carries a molten-red crest.
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 64.0),
			Vector2(39.0, 59.0),
			Vector2(48.0, 62.0),
			Vector2(57.0, 59.0),
			Vector2(66.0, 65.0),
			Vector2(61.0, 83.0),
			Vector2(49.0, 89.0),
			Vector2(36.0, 83.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 66.0),
			Vector2(41.0, 63.0),
			Vector2(48.0, 66.0),
			Vector2(55.0, 63.0),
			Vector2(62.0, 67.0),
			Vector2(58.0, 80.0),
			Vector2(49.0, 84.0),
			Vector2(40.0, 80.0),
		],
		steel
	)
	canvas.draw_line(
		_p(box, 38.0, 68.0), _p(box, 48.0, 75.0), steel_light, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 58.0, 68.0), _p(box, 49.0, 75.0), steel_light, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 48.0, 75.0), 6.0 * unit, outline)
	canvas.draw_circle(_p(box, 48.0, 75.0), 3.8 * unit, ember)
	canvas.draw_circle(_p(box, 48.0, 75.0), 1.8 * unit, hot)
	canvas.draw_line(
		_p(box, 34.0, 83.0), _p(box, 41.0, 86.0), armor_light, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 56.0, 86.0), _p(box, 63.0, 82.0), armor_light, maxf(2.0 * unit, 1.0), true
	)


static func _fill(canvas: CanvasItem, box: Rect2, points: Array[Vector2], color: Color) -> void:
	canvas.draw_colored_polygon(_poly(box, points), color)


static func _p(box: Rect2, x: float, y: float) -> Vector2:
	return box.position + Vector2(x, y) * (box.size.x / SIZE)


static func _poly(box: Rect2, points: Array[Vector2]) -> PackedVector2Array:
	var result := PackedVector2Array()
	for point in points:
		result.append(box.position + point * (box.size.x / SIZE))
	return result


static func _backdrop(canvas: CanvasItem, box: Rect2, top: Color, bottom: Color) -> void:
	var bands := 18
	var height := box.size.y / float(bands)
	for index in bands:
		var band := Rect2(
			box.position.x, box.position.y + height * float(index), box.size.x, height + 1.0
		)
		canvas.draw_rect(band, top.lerp(bottom, float(index) / float(bands - 1)))
