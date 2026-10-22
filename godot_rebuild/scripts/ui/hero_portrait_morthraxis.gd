extends RefCounted
## Native canvas painter for Morthraxis, the True Boss/Vampire Lord.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(12, 7, 17)
	var cloak := Color8(54, 10, 28)
	var cloak_light := Color8(97, 14, 38)
	var crimson := Color8(145, 18, 48)
	var blood := Color8(220, 50, 90)
	var rose := Color8(255, 119, 151)
	var silver := Color8(158, 169, 186)
	var silver_light := Color8(228, 230, 237)
	var skin := Color8(218, 190, 178)
	var skin_light := Color8(246, 220, 202)
	var hair := Color8(23, 19, 29)
	var hair_glint := Color8(102, 31, 51)
	var ruby := Color8(255, 70, 104)

	_backdrop(canvas, box, Color8(104, 35, 62), Color8(16, 8, 20))
	canvas.draw_arc(
		_p(box, 48.0, 42.0),
		39.0 * unit,
		-PI * 0.9,
		-PI * 0.1,
		32,
		Color(blood.r, blood.g, blood.b, 0.28),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 42.0),
		30.0 * unit,
		PI * 0.14,
		PI * 0.86,
		28,
		Color(rose.r, rose.g, rose.b, 0.16),
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 14.0, 37.0), 1.7 * unit, rose)
	canvas.draw_circle(_p(box, 82.0, 36.0), 1.5 * unit, blood)
	canvas.draw_circle(_p(box, 17.0, 57.0), 1.8 * unit, blood)
	canvas.draw_circle(_p(box, 78.0, 61.0), 1.6 * unit, rose)

	# Pointed crimson mantle fans out like a pair of folded bat wings.
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 96.0),
			Vector2(7.0, 78.0),
			Vector2(11.0, 63.0),
			Vector2(6.0, 49.0),
			Vector2(18.0, 53.0),
			Vector2(22.0, 42.0),
			Vector2(31.0, 52.0),
			Vector2(39.0, 57.0),
			Vector2(36.0, 75.0),
			Vector2(31.0, 96.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(17.0, 94.0),
			Vector2(12.0, 78.0),
			Vector2(15.0, 64.0),
			Vector2(11.0, 54.0),
			Vector2(20.0, 58.0),
			Vector2(24.0, 48.0),
			Vector2(31.0, 56.0),
			Vector2(35.0, 61.0),
			Vector2(32.0, 76.0),
			Vector2(28.0, 94.0),
		],
		cloak_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(83.0, 96.0),
			Vector2(89.0, 78.0),
			Vector2(85.0, 63.0),
			Vector2(90.0, 49.0),
			Vector2(78.0, 53.0),
			Vector2(74.0, 42.0),
			Vector2(65.0, 52.0),
			Vector2(57.0, 57.0),
			Vector2(60.0, 75.0),
			Vector2(65.0, 96.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(79.0, 94.0),
			Vector2(84.0, 78.0),
			Vector2(81.0, 64.0),
			Vector2(85.0, 54.0),
			Vector2(76.0, 58.0),
			Vector2(72.0, 48.0),
			Vector2(65.0, 56.0),
			Vector2(61.0, 61.0),
			Vector2(64.0, 76.0),
			Vector2(68.0, 94.0),
		],
		cloak_light
	)
	canvas.draw_line(_p(box, 14.0, 62.0), _p(box, 30.0, 73.0), blood, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 82.0, 62.0), _p(box, 66.0, 73.0), blood, maxf(1.5 * unit, 1.0), true)

	# Dark doublet, angular shoulders, and tall blood-red collar.
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 96.0),
			Vector2(19.0, 76.0),
			Vector2(26.0, 63.0),
			Vector2(37.0, 56.0),
			Vector2(59.0, 56.0),
			Vector2(70.0, 63.0),
			Vector2(77.0, 76.0),
			Vector2(81.0, 96.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(21.0, 94.0),
			Vector2(24.0, 78.0),
			Vector2(30.0, 67.0),
			Vector2(39.0, 61.0),
			Vector2(57.0, 61.0),
			Vector2(66.0, 67.0),
			Vector2(72.0, 78.0),
			Vector2(75.0, 94.0),
		],
		cloak
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 75.0),
			Vector2(19.0, 63.0),
			Vector2(31.0, 59.0),
			Vector2(41.0, 66.0),
			Vector2(36.0, 79.0),
			Vector2(25.0, 84.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(17.0, 72.0),
			Vector2(21.0, 66.0),
			Vector2(30.0, 63.0),
			Vector2(36.0, 67.0),
			Vector2(32.0, 76.0),
			Vector2(24.0, 80.0),
		],
		crimson
	)
	_fill(
		canvas,
		box,
		[
			Vector2(83.0, 75.0),
			Vector2(77.0, 63.0),
			Vector2(65.0, 59.0),
			Vector2(55.0, 66.0),
			Vector2(60.0, 79.0),
			Vector2(71.0, 84.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(79.0, 72.0),
			Vector2(75.0, 66.0),
			Vector2(66.0, 63.0),
			Vector2(60.0, 67.0),
			Vector2(64.0, 76.0),
			Vector2(72.0, 80.0),
		],
		crimson
	)
	canvas.draw_line(_p(box, 21.0, 68.0), _p(box, 33.0, 70.0), silver, maxf(1.6 * unit, 1.0), true)
	canvas.draw_line(_p(box, 75.0, 68.0), _p(box, 63.0, 70.0), silver, maxf(1.6 * unit, 1.0), true)

	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 59.0),
			Vector2(32.0, 43.0),
			Vector2(43.0, 54.0),
			Vector2(45.0, 72.0),
			Vector2(36.0, 78.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 61.0),
			Vector2(35.0, 49.0),
			Vector2(41.0, 56.0),
			Vector2(42.0, 69.0),
			Vector2(36.0, 74.0),
		],
		crimson
	)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 59.0),
			Vector2(64.0, 43.0),
			Vector2(53.0, 54.0),
			Vector2(51.0, 72.0),
			Vector2(60.0, 78.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(63.0, 61.0),
			Vector2(61.0, 49.0),
			Vector2(55.0, 56.0),
			Vector2(54.0, 69.0),
			Vector2(60.0, 74.0),
		],
		crimson
	)
	canvas.draw_line(_p(box, 35.0, 58.0), _p(box, 41.0, 65.0), rose, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 61.0, 58.0), _p(box, 55.0, 65.0), rose, maxf(1.2 * unit, 1.0), true)

	# A long swept mane frames the pale face from behind.
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 31.0),
			Vector2(27.0, 23.0),
			Vector2(31.0, 16.0),
			Vector2(41.0, 12.0),
			Vector2(55.0, 13.0),
			Vector2(66.0, 20.0),
			Vector2(69.0, 32.0),
			Vector2(66.0, 47.0),
			Vector2(62.0, 55.0),
			Vector2(56.0, 50.0),
			Vector2(59.0, 34.0),
			Vector2(49.0, 25.0),
			Vector2(39.0, 28.0),
			Vector2(36.0, 49.0),
			Vector2(30.0, 56.0),
			Vector2(26.0, 43.0),
		],
		hair
	)
	canvas.draw_line(
		_p(box, 31.0, 30.0), _p(box, 36.0, 45.0), hair_glint, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 63.0, 27.0), _p(box, 62.0, 44.0), hair_glint, maxf(1.8 * unit, 1.0), true
	)

	# Ears and a sharp, aristocratic face.
	_fill(
		canvas,
		box,
		[Vector2(31.0, 31.0), Vector2(23.0, 25.0), Vector2(27.0, 41.0), Vector2(35.0, 43.0)],
		outline
	)
	_fill(
		canvas,
		box,
		[Vector2(30.0, 32.0), Vector2(26.0, 29.0), Vector2(29.0, 38.0), Vector2(34.0, 40.0)],
		skin
	)
	_fill(
		canvas,
		box,
		[Vector2(65.0, 31.0), Vector2(73.0, 25.0), Vector2(69.0, 41.0), Vector2(61.0, 43.0)],
		outline
	)
	_fill(
		canvas,
		box,
		[Vector2(66.0, 32.0), Vector2(70.0, 29.0), Vector2(67.0, 38.0), Vector2(62.0, 40.0)],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 29.0),
			Vector2(36.0, 22.0),
			Vector2(43.0, 18.0),
			Vector2(54.0, 19.0),
			Vector2(61.0, 25.0),
			Vector2(65.0, 34.0),
			Vector2(62.0, 43.0),
			Vector2(56.0, 51.0),
			Vector2(48.0, 55.0),
			Vector2(40.0, 51.0),
			Vector2(34.0, 43.0),
			Vector2(30.0, 35.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 30.0),
			Vector2(38.0, 24.0),
			Vector2(44.0, 21.0),
			Vector2(53.0, 22.0),
			Vector2(59.0, 27.0),
			Vector2(62.0, 35.0),
			Vector2(60.0, 42.0),
			Vector2(55.0, 48.0),
			Vector2(48.0, 52.0),
			Vector2(42.0, 48.0),
			Vector2(37.0, 42.0),
			Vector2(34.0, 35.0),
		],
		skin
	)

	# A swept widow's peak, lacquer-black with narrow red enamel streaks.
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 31.0),
			Vector2(28.0, 21.0),
			Vector2(36.0, 15.0),
			Vector2(48.0, 13.0),
			Vector2(61.0, 17.0),
			Vector2(68.0, 25.0),
			Vector2(64.0, 31.0),
			Vector2(57.0, 26.0),
			Vector2(50.0, 23.0),
			Vector2(43.0, 26.0),
			Vector2(39.0, 34.0),
			Vector2(34.0, 29.0),
		],
		hair
	)
	canvas.draw_line(
		_p(box, 35.0, 21.0), _p(box, 47.0, 18.0), hair_glint, maxf(1.7 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 52.0, 19.0), _p(box, 63.0, 23.0), hair_glint, maxf(1.4 * unit, 1.0), true
	)

	# Ruby eyes, fine nose, and a restrained flash of fangs.
	canvas.draw_line(_p(box, 36.0, 34.0), _p(box, 45.0, 35.0), outline, maxf(2.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 35.0), _p(box, 60.0, 34.0), outline, maxf(2.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 37.0), _p(box, 44.0, 37.0), ruby, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 37.0), _p(box, 58.0, 37.0), ruby, maxf(1.8 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 41.0, 36.5), 0.8 * unit, rose)
	canvas.draw_circle(_p(box, 55.0, 36.5), 0.8 * unit, rose)
	canvas.draw_line(
		_p(box, 48.0, 36.0), _p(box, 46.0, 42.0), Color8(174, 134, 129), maxf(1.3 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 43.0, 45.0), _p(box, 53.0, 45.0), outline, maxf(1.4 * unit, 1.0), true)
	_fill(
		canvas, box, [Vector2(44.0, 45.0), Vector2(47.0, 45.0), Vector2(46.5, 48.0)], silver_light
	)
	_fill(
		canvas, box, [Vector2(49.0, 45.0), Vector2(52.0, 45.0), Vector2(49.5, 48.0)], silver_light
	)
	canvas.draw_line(
		_p(box, 36.0, 41.0), _p(box, 39.0, 43.0), skin_light, maxf(1.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 58.0, 41.0), _p(box, 61.0, 39.0), skin_light, maxf(1.0 * unit, 1.0), true
	)

	# A silver brow ornament and a cut-crystal blood sigil anchor the armor.
	_fill(
		canvas,
		box,
		[
			Vector2(39.0, 24.0),
			Vector2(43.0, 20.0),
			Vector2(48.0, 23.0),
			Vector2(53.0, 20.0),
			Vector2(57.0, 25.0),
			Vector2(48.0, 28.0),
		],
		silver
	)
	canvas.draw_circle(_p(box, 48.0, 25.0), 2.0 * unit, blood)
	canvas.draw_line(_p(box, 28.0, 81.0), _p(box, 39.0, 91.0), silver, maxf(1.4 * unit, 1.0), true)
	canvas.draw_line(_p(box, 68.0, 81.0), _p(box, 57.0, 91.0), silver, maxf(1.4 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 76.0), 9.0 * unit, outline)
	_fill(
		canvas,
		box,
		[
			Vector2(48.0, 66.0),
			Vector2(55.0, 73.0),
			Vector2(52.0, 84.0),
			Vector2(48.0, 88.0),
			Vector2(44.0, 84.0),
			Vector2(41.0, 73.0),
		],
		blood
	)
	_fill(canvas, box, [Vector2(48.0, 68.0), Vector2(53.0, 74.0), Vector2(49.0, 77.0)], rose)
	canvas.draw_circle(_p(box, 30.0, 64.0), 1.5 * unit, silver_light)
	canvas.draw_circle(_p(box, 66.0, 64.0), 1.5 * unit, silver_light)
	canvas.draw_circle(_p(box, 48.0, 59.0), 1.5 * unit, ruby)


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
