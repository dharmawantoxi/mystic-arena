extends RefCounted
## Native canvas painter for Aureth'zar, the True Boss/Solar Archer.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(10, 17, 31)
	var mantle := Color8(24, 39, 68)
	var mantle_light := Color8(45, 77, 117)
	var blue := Color8(51, 111, 151)
	var gold := Color8(225, 170, 66)
	var gold_light := Color8(255, 219, 119)
	var sun := Color8(255, 239, 177)
	var skin := Color8(219, 171, 131)
	var skin_light := Color8(242, 202, 158)
	var hair := Color8(218, 174, 99)
	var hair_light := Color8(255, 224, 142)
	var glow := Color8(255, 248, 208)

	_backdrop(canvas, box, Color8(112, 95, 160), Color8(12, 20, 40))
	canvas.draw_arc(
		_p(box, 48.0, 45.0),
		39.0 * unit,
		-PI * 0.88,
		-PI * 0.12,
		32,
		Color(gold_light.r, gold_light.g, gold_light.b, 0.32),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 45.0),
		30.0 * unit,
		PI * 0.13,
		PI * 0.87,
		28,
		Color(glow.r, glow.g, glow.b, 0.20),
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 13.0, 37.0), 1.8 * unit, glow)
	canvas.draw_circle(_p(box, 81.0, 35.0), 2.2 * unit, gold_light)
	canvas.draw_circle(_p(box, 17.0, 56.0), 1.5 * unit, gold)
	canvas.draw_circle(_p(box, 78.0, 63.0), 1.8 * unit, glow)

	# A tall recurve bow and sunlit arrow frame the archer's right side.
	canvas.draw_arc(
		_p(box, 61.0, 47.0),
		28.0 * unit,
		-PI * 0.40,
		PI * 0.40,
		28,
		outline,
		maxf(7.0 * unit, 2.0),
		true
	)
	canvas.draw_arc(
		_p(box, 61.0, 47.0),
		28.0 * unit,
		-PI * 0.40,
		PI * 0.40,
		28,
		gold,
		maxf(3.0 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 82.0, 28.0), _p(box, 67.0, 67.0), outline, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 82.0, 28.0), _p(box, 67.0, 67.0), glow, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 69.0, 49.0), _p(box, 89.0, 25.0), outline, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 70.0, 48.0), _p(box, 87.0, 28.0), gold_light, maxf(1.5 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[Vector2(88.0, 27.0), Vector2(92.0, 20.0), Vector2(91.0, 29.0), Vector2(86.0, 33.0)],
		sun
	)
	canvas.draw_line(_p(box, 70.0, 49.0), _p(box, 74.0, 45.0), gold, maxf(2.0 * unit, 1.0), true)

	# A midnight-blue mantle and fitted gold-trimmed shoulders.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 96.0),
			Vector2(12.0, 77.0),
			Vector2(21.0, 66.0),
			Vector2(34.0, 59.0),
			Vector2(61.0, 59.0),
			Vector2(75.0, 65.0),
			Vector2(85.0, 78.0),
			Vector2(89.0, 96.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 94.0),
			Vector2(19.0, 79.0),
			Vector2(29.0, 70.0),
			Vector2(41.0, 64.0),
			Vector2(56.0, 64.0),
			Vector2(68.0, 70.0),
			Vector2(78.0, 81.0),
			Vector2(81.0, 94.0),
		],
		mantle
	)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 71.0),
			Vector2(14.0, 61.0),
			Vector2(26.0, 58.0),
			Vector2(38.0, 64.0),
			Vector2(35.0, 76.0),
			Vector2(24.0, 82.0),
			Vector2(13.0, 79.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 69.0),
			Vector2(18.0, 64.0),
			Vector2(27.0, 62.0),
			Vector2(33.0, 66.0),
			Vector2(31.0, 73.0),
			Vector2(24.0, 78.0),
			Vector2(17.0, 76.0),
		],
		mantle_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(59.0, 64.0),
			Vector2(69.0, 58.0),
			Vector2(82.0, 62.0),
			Vector2(86.0, 72.0),
			Vector2(82.0, 81.0),
			Vector2(70.0, 83.0),
			Vector2(60.0, 77.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(64.0, 66.0),
			Vector2(71.0, 62.0),
			Vector2(80.0, 65.0),
			Vector2(82.0, 72.0),
			Vector2(79.0, 77.0),
			Vector2(71.0, 79.0),
			Vector2(64.0, 75.0),
		],
		mantle_light
	)
	canvas.draw_line(_p(box, 18.0, 68.0), _p(box, 31.0, 67.0), gold, maxf(2.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 66.0, 67.0), _p(box, 80.0, 67.0), gold, maxf(2.2 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 25.0, 72.0), 2.0 * unit, gold_light)
	canvas.draw_circle(_p(box, 73.0, 72.0), 2.0 * unit, gold_light)

	# Ivory collar and a dawn-colored sash lead to the sunstone insignia.
	_fill(
		canvas,
		box,
		[Vector2(37.0, 51.0), Vector2(48.0, 60.0), Vector2(42.0, 69.0), Vector2(33.0, 57.0)],
		outline
	)
	_fill(
		canvas,
		box,
		[Vector2(58.0, 51.0), Vector2(49.0, 60.0), Vector2(55.0, 69.0), Vector2(63.0, 57.0)],
		outline
	)
	_fill(
		canvas,
		box,
		[Vector2(39.0, 53.0), Vector2(47.0, 60.0), Vector2(42.0, 65.0), Vector2(36.0, 57.0)],
		glow
	)
	_fill(
		canvas,
		box,
		[Vector2(56.0, 53.0), Vector2(50.0, 60.0), Vector2(54.0, 65.0), Vector2(60.0, 57.0)],
		glow
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 60.0),
			Vector2(36.0, 59.0),
			Vector2(69.0, 91.0),
			Vector2(65.0, 96.0),
			Vector2(58.0, 96.0),
			Vector2(26.0, 68.0),
		],
		blue
	)
	canvas.draw_line(
		_p(box, 32.0, 61.0), _p(box, 66.0, 93.0), gold_light, maxf(1.4 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 48.0, 75.0), 8.0 * unit, outline)
	canvas.draw_circle(_p(box, 48.0, 75.0), 5.5 * unit, gold)
	canvas.draw_circle(_p(box, 48.0, 75.0), 2.5 * unit, glow)
	canvas.draw_line(
		_p(box, 48.0, 65.0), _p(box, 48.0, 68.0), gold_light, maxf(1.3 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 48.0, 82.0), _p(box, 48.0, 85.0), gold_light, maxf(1.3 * unit, 1.0), true
	)

	# Long sun-gold hair streams from beneath the circlet.
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 28.0),
			Vector2(27.0, 20.0),
			Vector2(25.0, 31.0),
			Vector2(21.0, 40.0),
			Vector2(27.0, 44.0),
			Vector2(24.0, 55.0),
			Vector2(34.0, 52.0),
			Vector2(39.0, 43.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 30.0),
			Vector2(29.0, 24.0),
			Vector2(28.0, 34.0),
			Vector2(25.0, 40.0),
			Vector2(30.0, 43.0),
			Vector2(28.0, 50.0),
			Vector2(34.0, 48.0),
			Vector2(37.0, 42.0),
		],
		hair
	)
	canvas.draw_line(
		_p(box, 29.0, 34.0), _p(box, 32.0, 43.0), hair_light, maxf(1.5 * unit, 1.0), true
	)

	# A calm, radiant face framed by a fine solar circlet.
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 31.0),
			Vector2(32.0, 22.0),
			Vector2(40.0, 16.0),
			Vector2(52.0, 16.0),
			Vector2(62.0, 23.0),
			Vector2(66.0, 33.0),
			Vector2(63.0, 43.0),
			Vector2(57.0, 51.0),
			Vector2(48.0, 56.0),
			Vector2(39.0, 52.0),
			Vector2(33.0, 45.0),
			Vector2(29.0, 37.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 31.0),
			Vector2(37.0, 24.0),
			Vector2(43.0, 20.0),
			Vector2(52.0, 20.0),
			Vector2(59.0, 26.0),
			Vector2(62.0, 34.0),
			Vector2(59.0, 42.0),
			Vector2(54.0, 48.0),
			Vector2(48.0, 51.0),
			Vector2(41.0, 48.0),
			Vector2(36.0, 42.0),
			Vector2(33.0, 36.0),
		],
		skin
	)
	canvas.draw_circle(_p(box, 31.0, 36.0), 3.8 * unit, outline)
	canvas.draw_circle(_p(box, 31.0, 36.0), 2.0 * unit, skin)
	canvas.draw_circle(_p(box, 65.0, 36.0), 3.8 * unit, outline)
	canvas.draw_circle(_p(box, 65.0, 36.0), 2.0 * unit, skin)
	canvas.draw_line(_p(box, 37.0, 33.0), _p(box, 44.0, 34.0), mantle, maxf(2.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 34.0), _p(box, 59.0, 33.0), mantle, maxf(2.2 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 38.0, 36.0), _p(box, 43.0, 36.0), gold_light, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 53.0, 36.0), _p(box, 58.0, 36.0), gold_light, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 48.0, 35.0), _p(box, 47.0, 41.0), skin_light, maxf(1.4 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 44.0, 46.0), _p(box, 52.0, 46.0), mantle, maxf(1.4 * unit, 1.0), true)
	canvas.draw_line(_p(box, 32.0, 26.0), _p(box, 64.0, 26.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 23.0), 3.0 * unit, gold_light)
	canvas.draw_circle(_p(box, 48.0, 23.0), 1.3 * unit, glow)

	# Three fine rays crown the dawn-bright circlet.
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 25.0),
			Vector2(34.0, 15.0),
			Vector2(42.0, 22.0),
			Vector2(48.0, 9.0),
			Vector2(53.0, 22.0),
			Vector2(62.0, 14.0),
			Vector2(58.0, 26.0),
			Vector2(48.0, 29.0),
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(40.0, 22.0),
			Vector2(37.0, 18.0),
			Vector2(45.0, 23.0),
			Vector2(48.0, 14.0),
			Vector2(51.0, 23.0),
			Vector2(59.0, 17.0),
			Vector2(55.0, 24.0),
			Vector2(48.0, 26.0),
		],
		hair_light
	)
	canvas.draw_circle(_p(box, 48.0, 19.0), 1.5 * unit, glow)


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
