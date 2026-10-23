extends RefCounted
## Native canvas portrait: Cryssalia, The Glacial Empress / Ice Empress.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(23, 31, 57)
	var robe := Color8(54, 72, 129)
	var shade := Color8(63, 99, 152)
	var ice := Color8(132, 206, 237)
	var light := Color8(227, 249, 252)
	var skin := Color8(191, 209, 225)
	var face_shade := Color8(127, 155, 189)
	var hair := Color8(198, 231, 243)
	var gem := Color8(83, 183, 235)
	var silver := Color8(166, 193, 221)
	_backdrop(canvas, box, Color8(48, 79, 132), Color8(19, 28, 54))

	# A symmetrical glacial fan and snowflake halo frame the imperial silhouette.
	_fill(
		canvas,
		box,
		[
			Vector2(6.0, 61.0),
			Vector2(11.0, 29.0),
			Vector2(23.0, 48.0),
			Vector2(26.0, 22.0),
			Vector2(38.0, 58.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 58.0),
			Vector2(70.0, 22.0),
			Vector2(73.0, 48.0),
			Vector2(85.0, 29.0),
			Vector2(90.0, 61.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 54.0),
			Vector2(13.0, 38.0),
			Vector2(20.0, 51.0),
			Vector2(25.0, 36.0),
			Vector2(28.0, 57.0)
		],
		ice
	)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 57.0),
			Vector2(71.0, 36.0),
			Vector2(76.0, 51.0),
			Vector2(83.0, 38.0),
			Vector2(85.0, 54.0)
		],
		ice
	)
	canvas.draw_arc(
		_p(box, 48.0, 39.0),
		32.0 * unit,
		PI * -0.92,
		PI * -0.08,
		40,
		silver,
		maxf(1.0 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 48.0, 4.0), _p(box, 48.0, 11.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 29.0, 10.0), _p(box, 33.0, 16.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 67.0, 10.0), _p(box, 63.0, 16.0), light, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 96.0),
			Vector2(17.0, 69.0),
			Vector2(31.0, 57.0),
			Vector2(64.0, 57.0),
			Vector2(79.0, 69.0),
			Vector2(87.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(16.0, 94.0),
			Vector2(22.0, 72.0),
			Vector2(34.0, 62.0),
			Vector2(61.0, 62.0),
			Vector2(73.0, 72.0),
			Vector2(81.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 72.0),
			Vector2(38.0, 65.0),
			Vector2(47.0, 75.0),
			Vector2(43.0, 94.0),
			Vector2(20.0, 94.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(52.0, 75.0),
			Vector2(60.0, 65.0),
			Vector2(70.0, 72.0),
			Vector2(76.0, 94.0),
			Vector2(55.0, 94.0)
		],
		shade
	)

	# A high crystalline collar and a long white mantle replace martial armour.
	_fill(
		canvas,
		box,
		[
			Vector2(22.0, 53.0),
			Vector2(38.0, 60.0),
			Vector2(48.0, 70.0),
			Vector2(58.0, 60.0),
			Vector2(74.0, 53.0),
			Vector2(67.0, 73.0),
			Vector2(49.0, 85.0),
			Vector2(29.0, 73.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 58.0),
			Vector2(38.0, 64.0),
			Vector2(48.0, 76.0),
			Vector2(59.0, 64.0),
			Vector2(69.0, 58.0),
			Vector2(63.0, 71.0),
			Vector2(49.0, 81.0),
			Vector2(33.0, 71.0)
		],
		silver
	)
	_fill(
		canvas,
		box,
		[Vector2(29.0, 62.0), Vector2(36.0, 66.0), Vector2(43.0, 75.0), Vector2(36.0, 72.0)],
		light
	)
	_fill(
		canvas,
		box,
		[Vector2(61.0, 66.0), Vector2(67.0, 62.0), Vector2(60.0, 72.0), Vector2(53.0, 76.0)],
		ice
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 29.0),
			Vector2(34.0, 20.0),
			Vector2(59.0, 20.0),
			Vector2(66.0, 30.0),
			Vector2(65.0, 52.0),
			Vector2(71.0, 68.0),
			Vector2(60.0, 74.0),
			Vector2(54.0, 61.0),
			Vector2(39.0, 63.0),
			Vector2(32.0, 72.0),
			Vector2(26.0, 65.0),
			Vector2(30.0, 49.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 29.0),
			Vector2(38.0, 21.0),
			Vector2(56.0, 21.0),
			Vector2(63.0, 29.0),
			Vector2(62.0, 44.0),
			Vector2(55.0, 56.0),
			Vector2(42.0, 58.0),
			Vector2(33.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 30.0),
			Vector2(40.0, 25.0),
			Vector2(54.0, 25.0),
			Vector2(59.0, 31.0),
			Vector2(58.0, 43.0),
			Vector2(52.0, 52.0),
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
			Vector2(58.0, 31.0),
			Vector2(58.0, 42.0),
			Vector2(52.0, 50.0),
			Vector2(48.0, 49.0),
			Vector2(50.0, 41.0)
		],
		face_shade
	)

	# A tall icicle diadem, pale swept fringe and cool gemstone eyes.
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 31.0),
			Vector2(33.0, 24.0),
			Vector2(41.0, 20.0),
			Vector2(53.0, 20.0),
			Vector2(61.0, 26.0),
			Vector2(64.0, 39.0),
			Vector2(58.0, 34.0),
			Vector2(53.0, 27.0),
			Vector2(46.0, 32.0),
			Vector2(43.0, 28.0),
			Vector2(36.0, 36.0),
			Vector2(35.0, 49.0),
			Vector2(31.0, 44.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 29.0),
			Vector2(27.0, 17.0),
			Vector2(37.0, 22.0),
			Vector2(39.0, 10.0),
			Vector2(46.0, 21.0),
			Vector2(49.0, 5.0),
			Vector2(55.0, 21.0),
			Vector2(61.0, 10.0),
			Vector2(62.0, 22.0),
			Vector2(70.0, 17.0),
			Vector2(65.0, 30.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 26.0),
			Vector2(32.0, 22.0),
			Vector2(39.0, 26.0),
			Vector2(40.0, 17.0),
			Vector2(46.0, 26.0),
			Vector2(49.0, 12.0),
			Vector2(53.0, 26.0),
			Vector2(59.0, 17.0),
			Vector2(59.0, 26.0),
			Vector2(65.0, 22.0),
			Vector2(62.0, 27.0)
		],
		ice
	)
	canvas.draw_line(_p(box, 35.0, 28.0), _p(box, 62.0, 28.0), light, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(49.0, 23.0), Vector2(52.0, 28.0), Vector2(49.0, 33.0), Vector2(46.0, 28.0)],
		gem
	)
	canvas.draw_line(_p(box, 38.0, 35.0), _p(box, 44.0, 36.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 36.0), _p(box, 57.0, 34.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 39.0), _p(box, 43.0, 39.0), gem, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 39.0), _p(box, 56.0, 38.0), gem, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 48.0, 36.0), _p(box, 46.0, 43.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 44.0, 48.0), _p(box, 51.0, 47.0), robe, maxf(1.2 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 35.0, 44.0), 2.0 * unit, silver)
	canvas.draw_circle(_p(box, 35.0, 49.0), 1.5 * unit, gem)
	canvas.draw_circle(_p(box, 60.0, 43.0), 2.0 * unit, silver)
	canvas.draw_circle(_p(box, 60.0, 48.0), 1.5 * unit, gem)

	# Snowflake clasp, filigree and floating crystal sceptre complete the regalia.
	canvas.draw_circle(_p(box, 49.0, 78.0), 5.0 * unit, ink)
	canvas.draw_circle(_p(box, 49.0, 78.0), 3.0 * unit, gem)
	canvas.draw_line(_p(box, 49.0, 71.0), _p(box, 49.0, 85.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 43.0, 74.0), _p(box, 55.0, 82.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 43.0, 82.0), _p(box, 55.0, 74.0), light, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 87.0), _p(box, 43.0, 91.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 55.0, 91.0), _p(box, 62.0, 87.0), silver, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 80.0, 53.0), _p(box, 78.0, 95.0), ink, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 80.0, 53.0), _p(box, 78.0, 95.0), silver, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(81.0, 22.0),
			Vector2(90.0, 38.0),
			Vector2(87.0, 48.0),
			Vector2(80.0, 57.0),
			Vector2(73.0, 48.0),
			Vector2(72.0, 38.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(81.0, 28.0),
			Vector2(86.0, 39.0),
			Vector2(84.0, 47.0),
			Vector2(80.0, 52.0),
			Vector2(77.0, 46.0),
			Vector2(76.0, 39.0)
		],
		ice
	)
	_fill(
		canvas,
		box,
		[Vector2(81.0, 31.0), Vector2(82.0, 40.0), Vector2(80.0, 48.0), Vector2(79.0, 40.0)],
		light
	)
	canvas.draw_arc(
		_p(box, 81.0, 40.0), 12.0 * unit, PI * -0.9, PI * -0.1, 40, gem, maxf(1.0 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 76.0, 79.0), 3.5 * unit, skin)
	canvas.draw_line(_p(box, 75.0, 82.0), _p(box, 80.0, 82.0), silver, maxf(1.5 * unit, 1.0), true)


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
