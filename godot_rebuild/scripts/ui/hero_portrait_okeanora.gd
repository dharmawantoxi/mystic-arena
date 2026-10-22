extends RefCounted
## Native canvas painter for Okeanora, the True Boss/Kraken Priestess.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(5, 18, 23)
	var abyss := Color8(7, 34, 43)
	var robe := Color8(13, 63, 70)
	var robe_light := Color8(24, 105, 111)
	var sea := Color8(42, 154, 157)
	var teal := Color8(95, 245, 220)
	var pearl := Color8(207, 255, 242)
	var skin := Color8(136, 203, 188)
	var skin_light := Color8(187, 235, 218)
	var hair := Color8(19, 46, 64)
	var hair_light := Color8(50, 131, 139)
	var coral := Color8(195, 110, 101)
	var gold := Color8(207, 183, 124)

	_backdrop(canvas, box, Color8(41, 116, 126), Color8(5, 24, 35))
	canvas.draw_arc(
		_p(box, 48.0, 44.0),
		39.0 * unit,
		-PI * 0.9,
		-PI * 0.1,
		32,
		Color(teal.r, teal.g, teal.b, 0.24),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 44.0),
		30.0 * unit,
		PI * 0.16,
		PI * 0.84,
		28,
		Color(pearl.r, pearl.g, pearl.b, 0.15),
		maxf(1.4 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 13.0, 39.0), 1.7 * unit, pearl)
	canvas.draw_circle(_p(box, 81.0, 37.0), 1.8 * unit, teal)
	canvas.draw_circle(_p(box, 17.0, 58.0), 1.4 * unit, teal)
	canvas.draw_circle(_p(box, 78.0, 63.0), 1.8 * unit, pearl)

	# A coral trident rises behind the priestess's right shoulder.
	canvas.draw_line(_p(box, 79.0, 87.0), _p(box, 77.0, 20.0), outline, maxf(5.0 * unit, 1.5), true)
	canvas.draw_line(_p(box, 79.0, 87.0), _p(box, 77.0, 20.0), gold, maxf(2.3 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(76.0, 25.0),
			Vector2(69.0, 12.0),
			Vector2(71.0, 26.0),
			Vector2(75.0, 30.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(76.0, 25.0),
			Vector2(69.0, 12.0),
			Vector2(72.0, 25.0),
			Vector2(75.0, 28.0),
		],
		teal
	)
	_fill(
		canvas,
		box,
		[
			Vector2(78.0, 24.0),
			Vector2(84.0, 11.0),
			Vector2(82.0, 26.0),
			Vector2(78.0, 30.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(78.0, 24.0),
			Vector2(84.0, 11.0),
			Vector2(81.0, 25.0),
			Vector2(78.0, 28.0),
		],
		teal
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 23.0),
			Vector2(77.0, 7.0),
			Vector2(80.0, 21.0),
			Vector2(78.0, 26.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 21.0),
			Vector2(77.0, 9.0),
			Vector2(79.0, 21.0),
			Vector2(78.0, 24.0),
		],
		pearl
	)

	# Two curling feelers frame the mantle, dotted with tiny pale suckers.
	var left_feeler: Array[Vector2] = [
		Vector2(32.0, 61.0),
		Vector2(23.0, 57.0),
		Vector2(15.0, 61.0),
		Vector2(13.0, 69.0),
		Vector2(18.0, 74.0),
	]
	canvas.draw_polyline(_poly(box, left_feeler), outline, maxf(7.0 * unit, 2.0), true)
	canvas.draw_polyline(_poly(box, left_feeler), sea, maxf(4.0 * unit, 1.5), true)
	var right_feeler: Array[Vector2] = [
		Vector2(64.0, 61.0),
		Vector2(73.0, 56.0),
		Vector2(82.0, 60.0),
		Vector2(84.0, 68.0),
		Vector2(79.0, 74.0),
	]
	canvas.draw_polyline(_poly(box, right_feeler), outline, maxf(7.0 * unit, 2.0), true)
	canvas.draw_polyline(_poly(box, right_feeler), sea, maxf(4.0 * unit, 1.5), true)
	canvas.draw_circle(_p(box, 15.0, 66.0), 1.1 * unit, pearl)
	canvas.draw_circle(_p(box, 17.0, 71.0), 1.1 * unit, pearl)
	canvas.draw_circle(_p(box, 81.0, 65.0), 1.1 * unit, pearl)
	canvas.draw_circle(_p(box, 80.0, 70.0), 1.1 * unit, pearl)

	# Lower tendrils curl around the heavy ocean-blue robe.
	var left_tendril: Array[Vector2] = [
		Vector2(30.0, 73.0),
		Vector2(22.0, 79.0),
		Vector2(19.0, 87.0),
		Vector2(24.0, 92.0),
		Vector2(31.0, 89.0),
	]
	canvas.draw_polyline(_poly(box, left_tendril), outline, maxf(8.0 * unit, 2.0), true)
	canvas.draw_polyline(_poly(box, left_tendril), robe_light, maxf(5.0 * unit, 1.5), true)
	var right_tendril: Array[Vector2] = [
		Vector2(66.0, 73.0),
		Vector2(74.0, 79.0),
		Vector2(77.0, 87.0),
		Vector2(72.0, 92.0),
		Vector2(65.0, 89.0),
	]
	canvas.draw_polyline(_poly(box, right_tendril), outline, maxf(8.0 * unit, 2.0), true)
	canvas.draw_polyline(_poly(box, right_tendril), robe_light, maxf(5.0 * unit, 1.5), true)
	canvas.draw_circle(_p(box, 21.0, 83.0), 1.2 * unit, pearl)
	canvas.draw_circle(_p(box, 23.0, 89.0), 1.1 * unit, pearl)
	canvas.draw_circle(_p(box, 75.0, 83.0), 1.2 * unit, pearl)
	canvas.draw_circle(_p(box, 73.0, 89.0), 1.1 * unit, pearl)

	# A scalloped mantle and pearl-threaded shoulder plates.
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 96.0),
			Vector2(16.0, 77.0),
			Vector2(23.0, 65.0),
			Vector2(34.0, 57.0),
			Vector2(62.0, 57.0),
			Vector2(73.0, 65.0),
			Vector2(80.0, 77.0),
			Vector2(84.0, 96.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 94.0),
			Vector2(22.0, 78.0),
			Vector2(29.0, 67.0),
			Vector2(38.0, 62.0),
			Vector2(58.0, 62.0),
			Vector2(67.0, 67.0),
			Vector2(74.0, 78.0),
			Vector2(78.0, 94.0),
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 71.0),
			Vector2(19.0, 62.0),
			Vector2(31.0, 58.0),
			Vector2(40.0, 66.0),
			Vector2(35.0, 79.0),
			Vector2(23.0, 84.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 70.0),
			Vector2(22.0, 64.0),
			Vector2(30.0, 62.0),
			Vector2(36.0, 67.0),
			Vector2(32.0, 76.0),
			Vector2(24.0, 80.0),
		],
		sea
	)
	_fill(
		canvas,
		box,
		[
			Vector2(82.0, 71.0),
			Vector2(77.0, 62.0),
			Vector2(65.0, 58.0),
			Vector2(56.0, 66.0),
			Vector2(61.0, 79.0),
			Vector2(73.0, 84.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(78.0, 70.0),
			Vector2(74.0, 64.0),
			Vector2(66.0, 62.0),
			Vector2(60.0, 67.0),
			Vector2(64.0, 76.0),
			Vector2(72.0, 80.0),
		],
		sea
	)
	canvas.draw_line(_p(box, 22.0, 68.0), _p(box, 34.0, 70.0), pearl, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 74.0, 68.0), _p(box, 62.0, 70.0), pearl, maxf(1.5 * unit, 1.0), true)

	# Layered sea-silk breastplate with a shell-shaped pearl focus.
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 61.0),
			Vector2(41.0, 56.0),
			Vector2(55.0, 56.0),
			Vector2(63.0, 61.0),
			Vector2(68.0, 94.0),
			Vector2(28.0, 94.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 63.0),
			Vector2(43.0, 59.0),
			Vector2(53.0, 59.0),
			Vector2(59.0, 63.0),
			Vector2(63.0, 91.0),
			Vector2(33.0, 91.0),
		],
		robe_light
	)
	canvas.draw_line(_p(box, 40.0, 65.0), _p(box, 34.0, 87.0), teal, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 56.0, 65.0), _p(box, 62.0, 87.0), teal, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 77.0), 9.0 * unit, outline)
	canvas.draw_circle(_p(box, 48.0, 77.0), 6.6 * unit, coral)
	canvas.draw_circle(_p(box, 48.0, 77.0), 4.3 * unit, pearl)
	canvas.draw_arc(
		_p(box, 48.0, 77.0),
		8.0 * unit,
		-PI * 0.85,
		PI * 0.85,
		24,
		gold,
		maxf(1.2 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 48.0, 77.0), 1.8 * unit, teal)

	# Long midnight hair, cool skin, and fin-like ears.
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 30.0),
			Vector2(27.0, 21.0),
			Vector2(34.0, 14.0),
			Vector2(46.0, 12.0),
			Vector2(58.0, 15.0),
			Vector2(67.0, 23.0),
			Vector2(68.0, 38.0),
			Vector2(64.0, 52.0),
			Vector2(58.0, 60.0),
			Vector2(54.0, 49.0),
			Vector2(42.0, 53.0),
			Vector2(36.0, 61.0),
			Vector2(29.0, 52.0),
			Vector2(25.0, 39.0),
		],
		hair
	)
	canvas.draw_line(
		_p(box, 31.0, 31.0), _p(box, 34.0, 51.0), hair_light, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 63.0, 27.0), _p(box, 60.0, 47.0), hair_light, maxf(1.7 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[Vector2(33.0, 31.0), Vector2(22.0, 26.0), Vector2(29.0, 39.0), Vector2(35.0, 42.0)],
		outline
	)
	_fill(
		canvas,
		box,
		[Vector2(63.0, 31.0), Vector2(74.0, 26.0), Vector2(67.0, 39.0), Vector2(61.0, 42.0)],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 28.0),
			Vector2(36.0, 21.0),
			Vector2(43.0, 17.0),
			Vector2(53.0, 18.0),
			Vector2(61.0, 24.0),
			Vector2(65.0, 33.0),
			Vector2(63.0, 42.0),
			Vector2(56.0, 50.0),
			Vector2(48.0, 54.0),
			Vector2(40.0, 50.0),
			Vector2(34.0, 42.0),
			Vector2(30.0, 34.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 29.0),
			Vector2(38.0, 23.0),
			Vector2(44.0, 20.0),
			Vector2(53.0, 21.0),
			Vector2(59.0, 26.0),
			Vector2(62.0, 34.0),
			Vector2(60.0, 41.0),
			Vector2(55.0, 47.0),
			Vector2(48.0, 51.0),
			Vector2(42.0, 47.0),
			Vector2(37.0, 41.0),
			Vector2(34.0, 34.0),
		],
		skin
	)
	canvas.draw_line(_p(box, 37.0, 33.0), _p(box, 44.0, 34.0), abyss, maxf(2.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 34.0), _p(box, 59.0, 33.0), abyss, maxf(2.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 36.0), _p(box, 43.0, 36.0), teal, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 36.0), _p(box, 58.0, 36.0), teal, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 41.0, 36.0), 0.9 * unit, pearl)
	canvas.draw_circle(_p(box, 56.0, 36.0), 0.9 * unit, pearl)
	canvas.draw_line(
		_p(box, 48.0, 35.0), _p(box, 47.0, 41.0), skin_light, maxf(1.3 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 43.0, 45.0), _p(box, 53.0, 45.0), abyss, maxf(1.5 * unit, 1.0), true)

	# Crowned coral rises through the hair above a central moon-pearl.
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 28.0),
			Vector2(25.0, 14.0),
			Vector2(37.0, 21.0),
			Vector2(41.0, 9.0),
			Vector2(48.0, 20.0),
			Vector2(55.0, 9.0),
			Vector2(59.0, 21.0),
			Vector2(71.0, 14.0),
			Vector2(66.0, 29.0),
			Vector2(48.0, 33.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 26.0),
			Vector2(28.0, 18.0),
			Vector2(38.0, 23.0),
			Vector2(42.0, 13.0),
			Vector2(48.0, 23.0),
			Vector2(54.0, 13.0),
			Vector2(58.0, 23.0),
			Vector2(68.0, 18.0),
			Vector2(64.0, 26.0),
			Vector2(48.0, 30.0),
		],
		coral
	)
	canvas.draw_line(_p(box, 34.0, 24.0), _p(box, 62.0, 24.0), gold, maxf(1.4 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 28.0, 17.0), 2.0 * unit, pearl)
	canvas.draw_circle(_p(box, 41.0, 12.0), 2.0 * unit, pearl)
	canvas.draw_circle(_p(box, 55.0, 12.0), 2.0 * unit, pearl)
	canvas.draw_circle(_p(box, 68.0, 17.0), 2.0 * unit, pearl)
	canvas.draw_circle(_p(box, 48.0, 26.0), 3.0 * unit, teal)
	canvas.draw_circle(_p(box, 48.0, 26.0), 1.4 * unit, pearl)
	canvas.draw_circle(_p(box, 34.0, 48.0), 2.0 * unit, gold)
	canvas.draw_circle(_p(box, 62.0, 48.0), 2.0 * unit, gold)

	# Foam-bright scale marks finish the sleeves and the tidal sigil.
	canvas.draw_line(_p(box, 24.0, 83.0), _p(box, 31.0, 88.0), teal, maxf(1.3 * unit, 1.0), true)
	canvas.draw_line(_p(box, 72.0, 83.0), _p(box, 65.0, 88.0), teal, maxf(1.3 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 35.0, 62.0), 1.4 * unit, pearl)
	canvas.draw_circle(_p(box, 61.0, 62.0), 1.4 * unit, pearl)
	canvas.draw_circle(_p(box, 48.0, 58.0), 1.8 * unit, pearl)


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
