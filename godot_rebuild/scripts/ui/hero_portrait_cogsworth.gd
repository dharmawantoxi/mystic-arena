extends RefCounted
## Native canvas painter for Cogsworth, the True Boss/Steampunk Sky Machine.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(12, 19, 25)
	var iron := Color8(43, 62, 72)
	var iron_light := Color8(81, 105, 113)
	var iron_pale := Color8(133, 154, 153)
	var brass := Color8(174, 103, 43)
	var brass_light := Color8(230, 155, 75)
	var brass_pale := Color8(255, 211, 136)
	var copper := Color8(133, 68, 43)
	var glass := Color8(7, 31, 43)
	var teal := Color8(89, 214, 219)
	var glow := Color8(203, 255, 239)

	_backdrop(canvas, box, Color8(77, 116, 139), Color8(15, 24, 39))
	canvas.draw_arc(
		_p(box, 48.0, 46.0),
		39.0 * unit,
		-PI * 0.92,
		-PI * 0.12,
		32,
		Color(brass_light.r, brass_light.g, brass_light.b, 0.28),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 46.0),
		31.0 * unit,
		PI * 0.12,
		PI * 0.83,
		28,
		Color(teal.r, teal.g, teal.b, 0.18),
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 12.0, 39.0), 1.8 * unit, brass_pale)
	canvas.draw_circle(_p(box, 82.0, 37.0), 2.0 * unit, glow)
	canvas.draw_circle(_p(box, 15.0, 57.0), 1.4 * unit, teal)
	canvas.draw_circle(_p(box, 80.0, 61.0), 1.8 * unit, brass_light)

	# Swept stabilizer vanes and the compact top rotor silhouette.
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 37.0),
			Vector2(18.0, 30.0),
			Vector2(7.0, 25.0),
			Vector2(12.0, 39.0),
			Vector2(8.0, 49.0),
			Vector2(25.0, 47.0),
			Vector2(35.0, 51.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 38.0),
			Vector2(17.0, 33.0),
			Vector2(11.0, 29.0),
			Vector2(15.0, 39.0),
			Vector2(12.0, 45.0),
			Vector2(25.0, 44.0),
			Vector2(33.0, 47.0),
		],
		iron_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 37.0),
			Vector2(78.0, 30.0),
			Vector2(89.0, 25.0),
			Vector2(84.0, 39.0),
			Vector2(88.0, 49.0),
			Vector2(71.0, 47.0),
			Vector2(61.0, 51.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(69.0, 38.0),
			Vector2(79.0, 33.0),
			Vector2(85.0, 29.0),
			Vector2(81.0, 39.0),
			Vector2(84.0, 45.0),
			Vector2(71.0, 44.0),
			Vector2(63.0, 47.0),
		],
		iron_light
	)
	canvas.draw_line(
		_p(box, 15.0, 39.0), _p(box, 30.0, 41.0), brass_light, maxf(1.8 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 81.0, 39.0), _p(box, 66.0, 41.0), brass_light, maxf(1.8 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 48.0, 10.0), _p(box, 48.0, 19.0), outline, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 48.0, 10.0), _p(box, 48.0, 19.0), brass_light, maxf(2.0 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[
			Vector2(45.0, 8.0),
			Vector2(34.0, 4.0),
			Vector2(21.0, 7.0),
			Vector2(41.0, 11.0),
		],
		brass
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 8.0),
			Vector2(62.0, 4.0),
			Vector2(75.0, 7.0),
			Vector2(55.0, 11.0),
		],
		brass
	)
	canvas.draw_circle(_p(box, 48.0, 9.0), 3.4 * unit, outline)
	canvas.draw_circle(_p(box, 48.0, 9.0), 1.8 * unit, brass_pale)

	# Heavy shoulder housing and a faceted iron chest plate.
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 95.0),
			Vector2(17.0, 75.0),
			Vector2(23.0, 62.0),
			Vector2(35.0, 54.0),
			Vector2(61.0, 54.0),
			Vector2(73.0, 62.0),
			Vector2(79.0, 75.0),
			Vector2(81.0, 95.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(21.0, 94.0),
			Vector2(23.0, 77.0),
			Vector2(29.0, 66.0),
			Vector2(38.0, 59.0),
			Vector2(58.0, 59.0),
			Vector2(67.0, 66.0),
			Vector2(73.0, 77.0),
			Vector2(75.0, 94.0),
		],
		iron
	)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 73.0),
			Vector2(15.0, 62.0),
			Vector2(27.0, 57.0),
			Vector2(39.0, 64.0),
			Vector2(35.0, 79.0),
			Vector2(25.0, 85.0),
			Vector2(12.0, 82.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 71.0),
			Vector2(19.0, 64.0),
			Vector2(27.0, 61.0),
			Vector2(34.0, 66.0),
			Vector2(31.0, 76.0),
			Vector2(24.0, 80.0),
			Vector2(16.0, 78.0),
		],
		brass
	)
	_fill(
		canvas,
		box,
		[
			Vector2(57.0, 64.0),
			Vector2(69.0, 57.0),
			Vector2(81.0, 62.0),
			Vector2(87.0, 73.0),
			Vector2(84.0, 82.0),
			Vector2(71.0, 85.0),
			Vector2(61.0, 79.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 66.0),
			Vector2(69.0, 61.0),
			Vector2(77.0, 64.0),
			Vector2(82.0, 71.0),
			Vector2(79.0, 78.0),
			Vector2(71.0, 80.0),
			Vector2(64.0, 76.0),
		],
		brass
	)
	canvas.draw_line(
		_p(box, 19.0, 68.0), _p(box, 31.0, 69.0), brass_pale, maxf(1.7 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 66.0, 69.0), _p(box, 78.0, 68.0), brass_pale, maxf(1.7 * unit, 1.0), true
	)

	# Exposed side turbines carry the skyship's blue-green exhaust glow.
	canvas.draw_circle(_p(box, 23.0, 72.0), 7.0 * unit, outline)
	canvas.draw_circle(_p(box, 23.0, 72.0), 4.8 * unit, iron_pale)
	canvas.draw_circle(_p(box, 23.0, 72.0), 2.4 * unit, teal)
	canvas.draw_circle(_p(box, 23.0, 72.0), 0.9 * unit, glow)
	canvas.draw_circle(_p(box, 73.0, 72.0), 7.0 * unit, outline)
	canvas.draw_circle(_p(box, 73.0, 72.0), 4.8 * unit, iron_pale)
	canvas.draw_circle(_p(box, 73.0, 72.0), 2.4 * unit, teal)
	canvas.draw_circle(_p(box, 73.0, 72.0), 0.9 * unit, glow)

	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 60.0),
			Vector2(40.0, 56.0),
			Vector2(56.0, 56.0),
			Vector2(64.0, 60.0),
			Vector2(68.0, 93.0),
			Vector2(28.0, 93.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 61.0),
			Vector2(42.0, 58.0),
			Vector2(54.0, 58.0),
			Vector2(60.0, 61.0),
			Vector2(64.0, 91.0),
			Vector2(32.0, 91.0),
		],
		iron_light
	)
	canvas.draw_line(
		_p(box, 37.0, 63.0), _p(box, 33.0, 88.0), brass_light, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 59.0, 63.0), _p(box, 63.0, 88.0), brass_light, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 40.0, 88.0), _p(box, 56.0, 88.0), outline, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 42.0, 88.0), _p(box, 54.0, 88.0), brass_pale, maxf(1.3 * unit, 1.0), true
	)

	# Brass-rimmed clockwork core, with radial marks and a luminous turbine hub.
	canvas.draw_circle(_p(box, 48.0, 76.0), 14.0 * unit, outline)
	canvas.draw_circle(_p(box, 48.0, 76.0), 11.0 * unit, brass)
	canvas.draw_circle(_p(box, 48.0, 76.0), 8.0 * unit, glass)
	canvas.draw_arc(
		_p(box, 48.0, 76.0),
		12.0 * unit,
		-PI * 0.88,
		PI * 0.86,
		28,
		brass_pale,
		maxf(1.2 * unit, 1.0),
		true
	)
	for index in 8:
		var angle := TAU * float(index) / 8.0
		var direction := Vector2(cos(angle), sin(angle))
		canvas.draw_line(
			_p(box, 48.0, 76.0) + direction * 8.5 * unit,
			_p(box, 48.0, 76.0) + direction * 10.5 * unit,
			brass_pale,
			maxf(1.0 * unit, 1.0),
			true
		)
	canvas.draw_circle(_p(box, 48.0, 76.0), 5.6 * unit, teal)
	canvas.draw_circle(_p(box, 48.0, 76.0), 2.3 * unit, glow)
	canvas.draw_line(_p(box, 48.0, 76.0), _p(box, 51.0, 73.0), outline, maxf(1.2 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 76.0), 1.1 * unit, brass_pale)
	canvas.draw_line(
		_p(box, 38.0, 59.0), _p(box, 42.0, 63.0), brass_pale, maxf(1.2 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 58.0, 59.0), _p(box, 54.0, 63.0), brass_pale, maxf(1.2 * unit, 1.0), true
	)

	# Squared brass head with twin glass lenses and a ventilated jaw plate.
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 25.0),
			Vector2(35.0, 17.0),
			Vector2(43.0, 14.0),
			Vector2(53.0, 14.0),
			Vector2(62.0, 18.0),
			Vector2(68.0, 26.0),
			Vector2(68.0, 43.0),
			Vector2(61.0, 53.0),
			Vector2(35.0, 53.0),
			Vector2(28.0, 44.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 26.0),
			Vector2(38.0, 20.0),
			Vector2(44.0, 18.0),
			Vector2(52.0, 18.0),
			Vector2(59.0, 21.0),
			Vector2(64.0, 27.0),
			Vector2(64.0, 42.0),
			Vector2(58.0, 49.0),
			Vector2(38.0, 49.0),
			Vector2(32.0, 42.0),
		],
		brass
	)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 20.0),
			Vector2(44.0, 18.0),
			Vector2(52.0, 18.0),
			Vector2(59.0, 21.0),
			Vector2(62.0, 25.0),
			Vector2(47.0, 25.0),
			Vector2(33.0, 25.0),
		],
		brass_light
	)
	canvas.draw_line(
		_p(box, 35.0, 26.0), _p(box, 61.0, 26.0), brass_pale, maxf(1.4 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 33.0, 29.0), 2.1 * unit, iron_pale)
	canvas.draw_circle(_p(box, 63.0, 29.0), 2.1 * unit, iron_pale)
	canvas.draw_circle(_p(box, 33.0, 29.0), 0.8 * unit, outline)
	canvas.draw_circle(_p(box, 63.0, 29.0), 0.8 * unit, outline)

	# Deep-set luminous optical lenses framed by heavy riveted rims.
	canvas.draw_circle(_p(box, 40.0, 34.0), 7.8 * unit, outline)
	canvas.draw_circle(_p(box, 40.0, 34.0), 6.1 * unit, brass_pale)
	canvas.draw_circle(_p(box, 40.0, 34.0), 4.7 * unit, glass)
	canvas.draw_circle(_p(box, 40.0, 34.0), 3.0 * unit, teal)
	canvas.draw_circle(_p(box, 40.0, 34.0), 1.25 * unit, glow)
	canvas.draw_circle(_p(box, 56.0, 34.0), 7.8 * unit, outline)
	canvas.draw_circle(_p(box, 56.0, 34.0), 6.1 * unit, brass_pale)
	canvas.draw_circle(_p(box, 56.0, 34.0), 4.7 * unit, glass)
	canvas.draw_circle(_p(box, 56.0, 34.0), 3.0 * unit, teal)
	canvas.draw_circle(_p(box, 56.0, 34.0), 1.25 * unit, glow)
	canvas.draw_line(_p(box, 46.0, 34.0), _p(box, 50.0, 34.0), outline, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 46.0, 34.0), _p(box, 50.0, 34.0), brass_light, maxf(1.2 * unit, 1.0), true
	)

	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 42.0),
			Vector2(61.0, 42.0),
			Vector2(58.0, 49.0),
			Vector2(38.0, 49.0),
		],
		iron
	)
	canvas.draw_line(_p(box, 40.0, 44.0), _p(box, 56.0, 44.0), copper, maxf(1.4 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 41.0, 47.0), _p(box, 55.0, 47.0), iron_pale, maxf(1.1 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 31.0, 39.0), 1.5 * unit, brass_pale)
	canvas.draw_circle(_p(box, 65.0, 39.0), 1.5 * unit, brass_pale)
	canvas.draw_line(_p(box, 38.0, 52.0), _p(box, 58.0, 52.0), copper, maxf(1.3 * unit, 1.0), true)

	# Steam vents and little amber status lamps finish the flying machine.
	canvas.draw_line(_p(box, 31.0, 18.0), _p(box, 29.0, 13.0), outline, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 31.0, 18.0), _p(box, 29.0, 13.0), iron_pale, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 65.0, 18.0), _p(box, 67.0, 13.0), outline, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 65.0, 18.0), _p(box, 67.0, 13.0), iron_pale, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 27.0, 11.0),
		4.0 * unit,
		-PI * 0.9,
		PI * 0.1,
		16,
		iron_pale,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 69.0, 11.0),
		4.0 * unit,
		PI * 0.9,
		PI * 1.9,
		16,
		iron_pale,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 33.0, 63.0), 1.4 * unit, brass_pale)
	canvas.draw_circle(_p(box, 63.0, 63.0), 1.4 * unit, brass_pale)
	canvas.draw_circle(_p(box, 48.0, 57.0), 2.0 * unit, teal)


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
