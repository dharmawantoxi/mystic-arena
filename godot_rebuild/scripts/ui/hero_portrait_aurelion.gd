extends RefCounted
## Native canvas portrait: Aurelion, The Golden Sovereign / Royal King.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(34, 23, 31)
	var robe := Color8(83, 30, 65)
	var purple := Color8(131, 53, 104)
	var gold := Color8(213, 161, 59)
	var light := Color8(255, 225, 144)
	var bronze := Color8(125, 84, 38)
	var fur := Color8(225, 216, 193)
	var skin := Color8(207, 158, 112)
	var shade := Color8(151, 99, 72)
	var hair := Color8(235, 212, 158)
	var gem := Color8(111, 216, 215)
	_backdrop(canvas, box, Color8(83, 51, 67), Color8(29, 24, 37))

	# Throne finials and an ornate halo distinguish a magical king from a fighter.
	canvas.draw_arc(
		_p(box, 46.0, 39.0),
		32.0 * unit,
		PI * -0.94,
		PI * -0.06,
		48,
		bronze,
		maxf(3.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 46.0, 39.0),
		29.0 * unit,
		PI * -0.9,
		PI * -0.1,
		48,
		gold,
		maxf(1.0 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 15.0, 28.0), _p(box, 15.0, 92.0), ink, maxf(7.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 15.0, 28.0), _p(box, 15.0, 92.0), gold, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(15.0, 17.0), Vector2(19.0, 25.0), Vector2(15.0, 31.0), Vector2(11.0, 25.0)],
		gold
	)
	canvas.draw_line(_p(box, 78.0, 28.0), _p(box, 78.0, 92.0), ink, maxf(7.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 28.0), _p(box, 78.0, 92.0), gold, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(78.0, 17.0), Vector2(82.0, 25.0), Vector2(78.0, 31.0), Vector2(74.0, 25.0)],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 96.0),
			Vector2(15.0, 70.0),
			Vector2(28.0, 59.0),
			Vector2(61.0, 59.0),
			Vector2(75.0, 69.0),
			Vector2(83.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 94.0),
			Vector2(20.0, 72.0),
			Vector2(30.0, 63.0),
			Vector2(59.0, 63.0),
			Vector2(70.0, 72.0),
			Vector2(77.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[Vector2(22.0, 73.0), Vector2(34.0, 69.0), Vector2(38.0, 94.0), Vector2(18.0, 94.0)],
		purple
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 67.0),
			Vector2(47.0, 63.0),
			Vector2(59.0, 68.0),
			Vector2(62.0, 95.0),
			Vector2(32.0, 95.0)
		],
		bronze
	)
	_fill(
		canvas,
		box,
		[
			Vector2(38.0, 70.0),
			Vector2(47.0, 74.0),
			Vector2(56.0, 70.0),
			Vector2(55.0, 89.0),
			Vector2(48.0, 94.0),
			Vector2(39.0, 89.0)
		],
		gold
	)
	canvas.draw_line(_p(box, 41.0, 77.0), _p(box, 53.0, 77.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 42.0, 84.0), _p(box, 53.0, 84.0), light, maxf(1.5 * unit, 1.0), true)

	# Ermine mantle with dark spots, a heavy chain and a square emerald seal.
	_fill(
		canvas,
		box,
		[
			Vector2(16.0, 67.0),
			Vector2(29.0, 55.0),
			Vector2(43.0, 63.0),
			Vector2(47.0, 72.0),
			Vector2(39.0, 81.0),
			Vector2(25.0, 78.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(20.0, 67.0),
			Vector2(30.0, 59.0),
			Vector2(39.0, 65.0),
			Vector2(42.0, 72.0),
			Vector2(37.0, 77.0),
			Vector2(26.0, 74.0)
		],
		fur
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 67.0),
			Vector2(64.0, 55.0),
			Vector2(50.0, 63.0),
			Vector2(46.0, 72.0),
			Vector2(54.0, 81.0),
			Vector2(68.0, 78.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(73.0, 67.0),
			Vector2(63.0, 59.0),
			Vector2(54.0, 65.0),
			Vector2(51.0, 72.0),
			Vector2(56.0, 77.0),
			Vector2(67.0, 74.0)
		],
		fur
	)
	canvas.draw_circle(_p(box, 26.0, 66.0), 1.2 * unit, ink)
	canvas.draw_circle(_p(box, 32.0, 70.0), 1.2 * unit, ink)
	canvas.draw_circle(_p(box, 37.0, 73.0), 1.2 * unit, ink)
	canvas.draw_circle(_p(box, 67.0, 66.0), 1.2 * unit, ink)
	canvas.draw_circle(_p(box, 61.0, 70.0), 1.2 * unit, ink)
	canvas.draw_circle(_p(box, 56.0, 73.0), 1.2 * unit, ink)
	canvas.draw_line(_p(box, 32.0, 72.0), _p(box, 47.0, 81.0), gold, maxf(2.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 62.0, 72.0), _p(box, 47.0, 81.0), gold, maxf(2.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(47.0, 76.0), Vector2(53.0, 81.0), Vector2(47.0, 87.0), Vector2(41.0, 81.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(47.0, 78.0), Vector2(51.0, 81.0), Vector2(47.0, 85.0), Vector2(43.0, 81.0)],
		gem
	)

	# Tall open crown, silver-gold side hair and a forked royal beard.
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 29.0),
			Vector2(37.0, 20.0),
			Vector2(55.0, 20.0),
			Vector2(63.0, 29.0),
			Vector2(63.0, 45.0),
			Vector2(55.0, 57.0),
			Vector2(40.0, 58.0),
			Vector2(30.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 29.0),
			Vector2(39.0, 25.0),
			Vector2(53.0, 25.0),
			Vector2(58.0, 31.0),
			Vector2(58.0, 44.0),
			Vector2(52.0, 52.0),
			Vector2(42.0, 53.0),
			Vector2(35.0, 44.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 27.0),
			Vector2(58.0, 31.0),
			Vector2(58.0, 43.0),
			Vector2(52.0, 51.0),
			Vector2(47.0, 48.0),
			Vector2(50.0, 40.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 29.0),
			Vector2(36.0, 27.0),
			Vector2(35.0, 41.0),
			Vector2(38.0, 48.0),
			Vector2(33.0, 49.0),
			Vector2(28.0, 41.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(57.0, 27.0),
			Vector2(63.0, 29.0),
			Vector2(65.0, 41.0),
			Vector2(60.0, 49.0),
			Vector2(56.0, 47.0),
			Vector2(59.0, 40.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 29.0),
			Vector2(25.0, 12.0),
			Vector2(35.0, 18.0),
			Vector2(39.0, 6.0),
			Vector2(47.0, 17.0),
			Vector2(55.0, 6.0),
			Vector2(59.0, 18.0),
			Vector2(68.0, 12.0),
			Vector2(64.0, 29.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 26.0),
			Vector2(30.0, 18.0),
			Vector2(36.0, 23.0),
			Vector2(40.0, 13.0),
			Vector2(47.0, 23.0),
			Vector2(54.0, 13.0),
			Vector2(58.0, 23.0),
			Vector2(63.0, 18.0),
			Vector2(61.0, 26.0)
		],
		gold
	)
	canvas.draw_line(_p(box, 33.0, 25.0), _p(box, 60.0, 25.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 47.0, 24.0), 2.5 * unit, gem)
	canvas.draw_line(_p(box, 37.0, 34.0), _p(box, 43.0, 35.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 35.0), _p(box, 57.0, 34.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 37.0), _p(box, 42.0, 37.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 37.0), _p(box, 56.0, 37.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 36.0), _p(box, 45.0, 43.0), skin, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 43.0),
			Vector2(42.0, 46.0),
			Vector2(47.0, 44.0),
			Vector2(53.0, 46.0),
			Vector2(58.0, 42.0),
			Vector2(56.0, 52.0),
			Vector2(51.0, 60.0),
			Vector2(47.0, 56.0),
			Vector2(43.0, 61.0),
			Vector2(38.0, 53.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 42.0, 49.0), _p(box, 51.0, 49.0), shade, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 42.0, 53.0), _p(box, 43.0, 57.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 52.0), _p(box, 50.0, 56.0), light, maxf(1.5 * unit, 1.0), true)

	# Orb-topped sceptre radiates the ranged magical role; no spear or shield.
	canvas.draw_line(_p(box, 80.0, 46.0), _p(box, 76.0, 94.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 80.0, 46.0), _p(box, 76.0, 94.0), gold, maxf(2.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 81.0, 42.0), 10.0 * unit, ink)
	canvas.draw_circle(_p(box, 81.0, 42.0), 8.0 * unit, gold)
	canvas.draw_circle(_p(box, 81.0, 42.0), 5.0 * unit, gem)
	canvas.draw_arc(
		_p(box, 81.0, 42.0), 6.0 * unit, PI * 0.95, PI * 1.8, 48, light, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 72.0, 42.0), _p(box, 90.0, 42.0), gold, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 81.0, 30.0), _p(box, 81.0, 35.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 77.0, 79.0), 4.0 * unit, skin)
	canvas.draw_line(_p(box, 74.0, 82.0), _p(box, 80.0, 82.0), bronze, maxf(2.0 * unit, 1.0), true)


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
