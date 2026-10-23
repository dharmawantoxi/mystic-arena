extends RefCounted
## Native creature portrait families; draw bodies moved without geometry changes.

const SIZE := 96.0


static func paint(
	family: String, canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	match family:
		"beast":
			_beast(canvas, box, unit, spec, ink)
		"golem":
			_golem(canvas, box, unit, spec, ink)
		"serpent":
			_serpent(canvas, box, unit, spec, ink)
		"wraith":
			_wraith(canvas, box, unit, spec, ink)
		"reaper":
			_reaper(canvas, box, unit, spec, ink)
		"treant":
			_treant(canvas, box, unit, spec, ink)
		"elemental":
			_elemental(canvas, box, unit, spec, ink)
		_:
			_beast(canvas, box, unit, spec, ink)


static func _beast(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_armor_body(canvas, box, spec, ink)
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 35.0),
			Vector2(25.0, 14.0),
			Vector2(38.0, 23.0),
			Vector2(47.0, 17.0),
			Vector2(58.0, 23.0),
			Vector2(70.0, 13.0),
			Vector2(67.0, 37.0),
			Vector2(60.0, 55.0),
			Vector2(47.0, 64.0),
			Vector2(34.0, 55.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 35.0),
			Vector2(32.0, 24.0),
			Vector2(40.0, 29.0),
			Vector2(47.0, 24.0),
			Vector2(55.0, 29.0),
			Vector2(63.0, 23.0),
			Vector2(62.0, 37.0),
			Vector2(56.0, 51.0),
			Vector2(47.0, 57.0),
			Vector2(38.0, 51.0)
		],
		spec["primary"]
	)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 41.0),
			Vector2(47.0, 36.0),
			Vector2(58.0, 41.0),
			Vector2(55.0, 51.0),
			Vector2(47.0, 56.0),
			Vector2(39.0, 51.0)
		],
		spec["skin"]
	)
	canvas.draw_circle(_p(box, 40.0, 36.0), 2.0 * unit, spec["light"])
	canvas.draw_circle(_p(box, 55.0, 36.0), 2.0 * unit, spec["accent"])
	_fill(
		canvas,
		box,
		[Vector2(43.0, 43.0), Vector2(47.0, 41.0), Vector2(52.0, 43.0), Vector2(47.0, 47.0)],
		ink
	)
	canvas.draw_line(_p(box, 41.0, 50.0), _p(box, 47.0, 52.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 52.0), _p(box, 54.0, 49.0), ink, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas, box, [Vector2(40.0, 51.0), Vector2(44.0, 52.0), Vector2(42.0, 58.0)], spec["light"]
	)
	_fill(
		canvas, box, [Vector2(51.0, 52.0), Vector2(55.0, 50.0), Vector2(53.0, 58.0)], spec["light"]
	)


static func _golem(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_armor_body(canvas, box, spec, ink)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 26.0),
			Vector2(38.0, 16.0),
			Vector2(58.0, 16.0),
			Vector2(68.0, 27.0),
			Vector2(64.0, 50.0),
			Vector2(55.0, 60.0),
			Vector2(38.0, 58.0),
			Vector2(30.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 29.0),
			Vector2(41.0, 22.0),
			Vector2(55.0, 22.0),
			Vector2(62.0, 29.0),
			Vector2(59.0, 46.0),
			Vector2(52.0, 53.0),
			Vector2(41.0, 52.0),
			Vector2(36.0, 44.0)
		],
		spec["skin"]
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 30.0),
			Vector2(41.0, 25.0),
			Vector2(61.0, 27.0),
			Vector2(57.0, 35.0),
			Vector2(39.0, 34.0)
		],
		spec["primary"]
	)
	canvas.draw_circle(_p(box, 41.0, 38.0), 2.0 * unit, spec["light"])
	canvas.draw_circle(_p(box, 54.0, 38.0), 2.0 * unit, spec["accent"])
	canvas.draw_line(_p(box, 41.0, 48.0), _p(box, 54.0, 48.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 47.0, 76.0), 7.0 * unit, spec["accent"])
	canvas.draw_circle(_p(box, 47.0, 76.0), 2.5 * unit, spec["light"])
	canvas.draw_line(
		_p(box, 37.0, 22.0), _p(box, 40.0, 30.0), spec["accent"], maxf(1.5 * unit, 1.0), true
	)


static func _serpent(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_robe_body(canvas, box, spec, ink)
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 43.0),
			Vector2(27.0, 23.0),
			Vector2(38.0, 14.0),
			Vector2(47.0, 20.0),
			Vector2(57.0, 14.0),
			Vector2(69.0, 24.0),
			Vector2(72.0, 43.0),
			Vector2(59.0, 56.0),
			Vector2(36.0, 56.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 38.0),
			Vector2(35.0, 25.0),
			Vector2(47.0, 21.0),
			Vector2(60.0, 25.0),
			Vector2(64.0, 38.0),
			Vector2(55.0, 51.0),
			Vector2(47.0, 57.0),
			Vector2(39.0, 51.0)
		],
		spec["skin"]
	)
	_fill(
		canvas,
		box,
		[Vector2(35.0, 36.0), Vector2(44.0, 33.0), Vector2(43.0, 40.0), Vector2(36.0, 41.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(51.0, 33.0), Vector2(60.0, 36.0), Vector2(59.0, 41.0), Vector2(52.0, 40.0)],
		ink
	)
	canvas.draw_circle(_p(box, 40.0, 37.0), 1.5 * unit, spec["light"])
	canvas.draw_circle(_p(box, 55.0, 37.0), 1.5 * unit, spec["accent"])
	_fill(
		canvas,
		box,
		[
			Vector2(41.0, 46.0),
			Vector2(47.0, 49.0),
			Vector2(54.0, 46.0),
			Vector2(51.0, 54.0),
			Vector2(44.0, 54.0)
		],
		ink
	)
	_fill(
		canvas, box, [Vector2(42.0, 48.0), Vector2(45.0, 49.0), Vector2(44.0, 56.0)], spec["light"]
	)
	_fill(
		canvas, box, [Vector2(50.0, 49.0), Vector2(53.0, 48.0), Vector2(52.0, 56.0)], spec["light"]
	)
	canvas.draw_arc(
		_p(box, 77.0, 76.0),
		15.0 * unit,
		PI * -0.7,
		PI * 0.8,
		32,
		spec["accent"],
		maxf(5.0 * unit, 1.0),
		true
	)


static func _wraith(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_robe_body(canvas, box, spec, ink)
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 50.0),
			Vector2(23.0, 28.0),
			Vector2(32.0, 13.0),
			Vector2(47.0, 6.0),
			Vector2(63.0, 14.0),
			Vector2(71.0, 31.0),
			Vector2(65.0, 50.0),
			Vector2(56.0, 58.0),
			Vector2(38.0, 57.0)
		],
		spec["primary"]
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 32.0),
			Vector2(40.0, 24.0),
			Vector2(55.0, 24.0),
			Vector2(63.0, 33.0),
			Vector2(58.0, 51.0),
			Vector2(47.0, 58.0),
			Vector2(37.0, 50.0)
		],
		spec["skin"]
	)
	_fill(
		canvas,
		box,
		[Vector2(35.0, 35.0), Vector2(44.0, 32.0), Vector2(45.0, 41.0), Vector2(37.0, 42.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(51.0, 32.0), Vector2(60.0, 35.0), Vector2(58.0, 42.0), Vector2(50.0, 41.0)],
		ink
	)
	canvas.draw_circle(_p(box, 41.0, 37.0), 1.5 * unit, spec["light"])
	canvas.draw_circle(_p(box, 55.0, 37.0), 1.5 * unit, spec["accent"])
	_fill(
		canvas,
		box,
		[
			Vector2(40.0, 47.0),
			Vector2(47.0, 50.0),
			Vector2(55.0, 46.0),
			Vector2(52.0, 54.0),
			Vector2(43.0, 54.0)
		],
		ink
	)
	canvas.draw_arc(
		_p(box, 17.0, 63.0),
		9.0 * unit,
		PI * 0.4,
		PI * 1.8,
		28,
		spec["accent"],
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 79.0, 57.0),
		10.0 * unit,
		PI * -0.7,
		PI * 0.7,
		28,
		spec["light"],
		maxf(1.5 * unit, 1.0),
		true
	)


static func _reaper(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_wraith(canvas, box, unit, spec, ink)
	canvas.draw_line(_p(box, 74.0, 96.0), _p(box, 82.0, 29.0), ink, maxf(8.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 74.0, 96.0), _p(box, 82.0, 29.0), spec["accent"], maxf(3.0 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[
			Vector2(83.0, 31.0),
			Vector2(66.0, 14.0),
			Vector2(45.0, 5.0),
			Vector2(28.0, 4.0),
			Vector2(40.0, 13.0),
			Vector2(57.0, 25.0),
			Vector2(75.0, 37.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 29.0),
			Vector2(64.0, 18.0),
			Vector2(46.0, 10.0),
			Vector2(38.0, 9.0),
			Vector2(49.0, 17.0),
			Vector2(62.0, 26.0),
			Vector2(74.0, 33.0)
		],
		spec["light"]
	)


static func _treant(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_golem(canvas, box, unit, spec, ink)
	canvas.draw_line(_p(box, 37.0, 24.0), _p(box, 27.0, 10.0), ink, maxf(7.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 28.0, 12.0), _p(box, 19.0, 8.0), spec["accent"], maxf(3.0 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 58.0, 24.0), _p(box, 68.0, 9.0), ink, maxf(7.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 67.0, 12.0), _p(box, 77.0, 7.0), spec["accent"], maxf(3.0 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 20.0, 9.0), 4.0 * unit, spec["primary"])
	canvas.draw_circle(_p(box, 77.0, 8.0), 4.0 * unit, spec["primary"])
	canvas.draw_line(
		_p(box, 47.0, 40.0), _p(box, 44.0, 49.0), spec["accent"], maxf(1.5 * unit, 1.0), true
	)


static func _elemental(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 96.0),
			Vector2(20.0, 72.0),
			Vector2(33.0, 61.0),
			Vector2(47.0, 68.0),
			Vector2(61.0, 59.0),
			Vector2(77.0, 73.0),
			Vector2(84.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(22.0, 94.0),
			Vector2(27.0, 75.0),
			Vector2(39.0, 68.0),
			Vector2(47.0, 77.0),
			Vector2(58.0, 67.0),
			Vector2(70.0, 77.0),
			Vector2(75.0, 94.0)
		],
		spec["primary"]
	)
	canvas.draw_circle(_p(box, 47.0, 39.0), 25.0 * unit, ink)
	canvas.draw_circle(_p(box, 47.0, 39.0), 20.0 * unit, spec["primary"])
	_fill(
		canvas,
		box,
		[
			Vector2(47.0, 18.0),
			Vector2(59.0, 30.0),
			Vector2(55.0, 48.0),
			Vector2(47.0, 59.0),
			Vector2(37.0, 47.0),
			Vector2(34.0, 30.0)
		],
		spec["accent"]
	)
	canvas.draw_circle(_p(box, 41.0, 37.0), 2.5 * unit, spec["light"])
	canvas.draw_circle(_p(box, 54.0, 37.0), 2.5 * unit, spec["light"])
	canvas.draw_arc(
		_p(box, 47.0, 39.0),
		31.0 * unit,
		PI * -0.8,
		PI * 0.8,
		40,
		spec["light"],
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 18.0, 72.0), 8.0 * unit, spec["accent"])
	canvas.draw_circle(_p(box, 78.0, 72.0), 8.0 * unit, spec["accent"])


static func _robe_body(canvas: CanvasItem, box: Rect2, spec: Dictionary, ink: Color) -> void:
	_fill(
		canvas,
		box,
		[
			Vector2(7.0, 96.0),
			Vector2(13.0, 71.0),
			Vector2(31.0, 57.0),
			Vector2(62.0, 57.0),
			Vector2(82.0, 72.0),
			Vector2(89.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 94.0),
			Vector2(20.0, 74.0),
			Vector2(33.0, 63.0),
			Vector2(60.0, 63.0),
			Vector2(75.0, 74.0),
			Vector2(82.0, 94.0)
		],
		spec["primary"]
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 94.0),
			Vector2(25.0, 75.0),
			Vector2(37.0, 68.0),
			Vector2(44.0, 80.0),
			Vector2(38.0, 94.0)
		],
		spec["accent"]
	)
	_fill(
		canvas,
		box,
		[
			Vector2(53.0, 79.0),
			Vector2(60.0, 67.0),
			Vector2(72.0, 76.0),
			Vector2(77.0, 94.0),
			Vector2(59.0, 94.0)
		],
		spec["bottom"]
	)


static func _armor_body(canvas: CanvasItem, box: Rect2, spec: Dictionary, ink: Color) -> void:
	_fill(
		canvas,
		box,
		[
			Vector2(4.0, 96.0),
			Vector2(10.0, 70.0),
			Vector2(29.0, 54.0),
			Vector2(65.0, 54.0),
			Vector2(86.0, 70.0),
			Vector2(93.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 94.0),
			Vector2(18.0, 73.0),
			Vector2(32.0, 62.0),
			Vector2(61.0, 62.0),
			Vector2(78.0, 73.0),
			Vector2(85.0, 94.0)
		],
		spec["primary"]
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 65.0),
			Vector2(46.0, 58.0),
			Vector2(63.0, 65.0),
			Vector2(59.0, 82.0),
			Vector2(47.0, 89.0),
			Vector2(34.0, 82.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 68.0),
			Vector2(46.0, 64.0),
			Vector2(57.0, 68.0),
			Vector2(54.0, 77.0),
			Vector2(47.0, 82.0),
			Vector2(39.0, 77.0)
		],
		spec["accent"]
	)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 70.0),
			Vector2(17.0, 55.0),
			Vector2(28.0, 53.0),
			Vector2(36.0, 65.0),
			Vector2(28.0, 77.0),
			Vector2(15.0, 79.0)
		],
		spec["primary"]
	)
	_fill(
		canvas,
		box,
		[
			Vector2(59.0, 65.0),
			Vector2(68.0, 53.0),
			Vector2(80.0, 55.0),
			Vector2(87.0, 70.0),
			Vector2(80.0, 79.0),
			Vector2(66.0, 77.0)
		],
		spec["primary"]
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
