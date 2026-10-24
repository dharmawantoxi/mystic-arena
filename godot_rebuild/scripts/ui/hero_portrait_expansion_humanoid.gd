extends RefCounted
## Native humanoid portrait families; draw bodies moved without geometry changes.

const SIZE := 96.0


static func paint(
	family: String, canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	match family:
		"mage":
			_mage(canvas, box, unit, spec, ink)
		"warrior":
			_warrior(canvas, box, unit, spec, ink)
		"assassin":
			_assassin(canvas, box, unit, spec, ink)
		"archer":
			_archer(canvas, box, unit, spec, ink)
		"gunner":
			_gunner(canvas, box, unit, spec, ink)
		"fighter":
			_fighter(canvas, box, unit, spec, ink)
		"rider":
			_rider(canvas, box, unit, spec, ink)
		_:
			_warrior(canvas, box, unit, spec, ink)


static func _mage(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_robe_body(canvas, box, spec, ink)
	var lift := float(spec["variant"] % 3) * 2.0
	_fill(
		canvas,
		box,
		[
			Vector2(20.0, 32.0),
			Vector2(31.0, 23.0),
			Vector2(37.0, 12.0 - lift),
			Vector2(47.0, 4.0 - lift),
			Vector2(53.0, 17.0),
			Vector2(66.0, 23.0),
			Vector2(76.0, 32.0),
			Vector2(62.0, 36.0),
			Vector2(32.0, 36.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 29.0),
			Vector2(39.0, 23.0),
			Vector2(59.0, 23.0),
			Vector2(67.0, 29.0),
			Vector2(58.0, 32.0),
			Vector2(37.0, 32.0)
		],
		spec["primary"]
	)
	_human_head(canvas, box, unit, spec, ink)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 28.0),
			Vector2(44.0, 25.0),
			Vector2(48.0, 28.0),
			Vector2(54.0, 24.0),
			Vector2(63.0, 28.0)
		],
		spec["accent"]
	)
	if spec["variant"] % 2 == 0:
		canvas.draw_line(_p(box, 76.0, 47.0), _p(box, 73.0, 96.0), ink, maxf(7.0 * unit, 1.0), true)
		canvas.draw_line(
			_p(box, 76.0, 47.0), _p(box, 73.0, 96.0), spec["accent"], maxf(2.5 * unit, 1.0), true
		)
		canvas.draw_circle(_p(box, 77.0, 36.0), 10.0 * unit, ink)
		canvas.draw_circle(_p(box, 77.0, 36.0), 7.0 * unit, spec["accent"])
		canvas.draw_circle(_p(box, 77.0, 36.0), 2.5 * unit, spec["light"])
	else:
		canvas.draw_circle(_p(box, 77.0, 65.0), 10.0 * unit, ink)
		canvas.draw_circle(_p(box, 77.0, 65.0), 7.0 * unit, spec["accent"])
		canvas.draw_arc(
			_p(box, 77.0, 65.0),
			13.0 * unit,
			PI * -0.7,
			PI * 0.8,
			28,
			spec["light"],
			maxf(1.2 * unit, 1.0),
			true
		)


static func _warrior(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_armor_body(canvas, box, spec, ink)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 31.0),
			Vector2(35.0, 18.0),
			Vector2(47.0, 12.0),
			Vector2(61.0, 18.0),
			Vector2(67.0, 32.0),
			Vector2(58.0, 35.0),
			Vector2(36.0, 35.0)
		],
		spec["primary"]
	)
	_human_head(canvas, box, unit, spec, ink, spec["variant"] % 3 == 0)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 19.0),
			Vector2(40.0, 7.0),
			Vector2(47.0, 13.0),
			Vector2(54.0, 6.0),
			Vector2(58.0, 19.0),
			Vector2(47.0, 23.0)
		],
		spec["accent"]
	)
	canvas.draw_line(_p(box, 76.0, 42.0), _p(box, 72.0, 96.0), ink, maxf(8.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 76.0, 42.0), _p(box, 72.0, 96.0), spec["accent"], maxf(3.0 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[
			Vector2(70.0, 39.0),
			Vector2(75.0, 17.0),
			Vector2(82.0, 6.0),
			Vector2(87.0, 20.0),
			Vector2(84.0, 41.0),
			Vector2(78.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(75.0, 36.0),
			Vector2(78.0, 20.0),
			Vector2(82.0, 13.0),
			Vector2(83.0, 23.0),
			Vector2(81.0, 37.0)
		],
		spec["light"]
	)
	canvas.draw_line(
		_p(box, 69.0, 46.0), _p(box, 85.0, 43.0), spec["accent"], maxf(3.0 * unit, 1.0), true
	)


static func _assassin(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_robe_body(canvas, box, spec, ink)
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 49.0),
			Vector2(23.0, 28.0),
			Vector2(32.0, 13.0),
			Vector2(47.0, 7.0),
			Vector2(63.0, 14.0),
			Vector2(71.0, 31.0),
			Vector2(65.0, 49.0),
			Vector2(57.0, 56.0),
			Vector2(37.0, 55.0)
		],
		spec["primary"]
	)
	_human_head(canvas, box, unit, spec, ink, true)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 31.0),
			Vector2(36.0, 20.0),
			Vector2(47.0, 14.0),
			Vector2(60.0, 20.0),
			Vector2(66.0, 31.0),
			Vector2(56.0, 27.0),
			Vector2(47.0, 30.0),
			Vector2(38.0, 27.0)
		],
		ink
	)
	canvas.draw_line(_p(box, 19.0, 60.0), _p(box, 26.0, 91.0), ink, maxf(7.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 61.0),
			Vector2(7.0, 45.0),
			Vector2(11.0, 31.0),
			Vector2(18.0, 47.0),
			Vector2(21.0, 62.0)
		],
		spec["light"]
	)
	canvas.draw_line(_p(box, 77.0, 60.0), _p(box, 70.0, 91.0), ink, maxf(7.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(75.0, 62.0),
			Vector2(79.0, 47.0),
			Vector2(87.0, 31.0),
			Vector2(90.0, 45.0),
			Vector2(84.0, 61.0)
		],
		spec["accent"]
	)


static func _archer(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_armor_body(canvas, box, spec, ink)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 42.0),
			Vector2(29.0, 23.0),
			Vector2(39.0, 12.0),
			Vector2(54.0, 12.0),
			Vector2(66.0, 25.0),
			Vector2(65.0, 44.0),
			Vector2(57.0, 53.0),
			Vector2(37.0, 53.0)
		],
		spec["primary"]
	)
	_human_head(canvas, box, unit, spec, ink)
	canvas.draw_arc(
		_p(box, 77.0, 52.0),
		30.0 * unit,
		PI * -0.55,
		PI * 0.55,
		40,
		ink,
		maxf(6.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 77.0, 52.0),
		30.0 * unit,
		PI * -0.55,
		PI * 0.55,
		40,
		spec["accent"],
		maxf(2.5 * unit, 1.0),
		true
	)
	canvas.draw_line(
		_p(box, 92.0, 25.0), _p(box, 92.0, 79.0), spec["light"], maxf(1.0 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 61.0, 52.0), _p(box, 94.0, 52.0), ink, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas, box, [Vector2(94.0, 52.0), Vector2(87.0, 48.0), Vector2(87.0, 56.0)], spec["light"]
	)


static func _gunner(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_armor_body(canvas, box, spec, ink)
	_fill(
		canvas,
		box,
		[
			Vector2(23.0, 29.0),
			Vector2(34.0, 21.0),
			Vector2(38.0, 12.0),
			Vector2(57.0, 14.0),
			Vector2(63.0, 23.0),
			Vector2(75.0, 29.0),
			Vector2(61.0, 34.0),
			Vector2(33.0, 34.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 27.0),
			Vector2(42.0, 23.0),
			Vector2(61.0, 25.0),
			Vector2(66.0, 29.0),
			Vector2(57.0, 31.0),
			Vector2(36.0, 31.0)
		],
		spec["primary"]
	)
	_human_head(canvas, box, unit, spec, ink)
	canvas.draw_line(_p(box, 61.0, 70.0), _p(box, 91.0, 55.0), ink, maxf(11.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 64.0, 68.0), _p(box, 90.0, 55.0), spec["accent"], maxf(5.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 84.0, 58.0), _p(box, 94.0, 53.0), spec["light"], maxf(3.0 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[Vector2(65.0, 70.0), Vector2(73.0, 72.0), Vector2(69.0, 86.0), Vector2(62.0, 82.0)],
		ink
	)


static func _fighter(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_armor_body(canvas, box, spec, ink)
	_human_head(canvas, box, unit, spec, ink)
	canvas.draw_line(
		_p(box, 34.0, 29.0), _p(box, 60.0, 28.0), spec["accent"], maxf(5.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 58.0, 29.0), _p(box, 67.0, 36.0), spec["accent"], maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 20.0, 81.0), 12.0 * unit, ink)
	canvas.draw_circle(_p(box, 20.0, 81.0), 8.0 * unit, spec["skin"])
	canvas.draw_circle(_p(box, 75.0, 81.0), 12.0 * unit, ink)
	canvas.draw_circle(_p(box, 75.0, 81.0), 8.0 * unit, spec["skin"])
	canvas.draw_line(
		_p(box, 15.0, 80.0), _p(box, 25.0, 82.0), spec["accent"], maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 70.0, 82.0), _p(box, 80.0, 80.0), spec["accent"], maxf(2.0 * unit, 1.0), true
	)


static func _rider(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 57.0),
			Vector2(8.0, 31.0),
			Vector2(20.0, 17.0),
			Vector2(30.0, 29.0),
			Vector2(34.0, 49.0),
			Vector2(25.0, 61.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 49.0),
			Vector2(14.0, 33.0),
			Vector2(20.0, 25.0),
			Vector2(26.0, 33.0),
			Vector2(28.0, 47.0),
			Vector2(23.0, 53.0)
		],
		spec["accent"]
	)
	canvas.draw_circle(_p(box, 20.0, 35.0), 1.5 * unit, spec["light"])
	_warrior(canvas, box, unit, spec, ink)
	canvas.draw_line(_p(box, 18.0, 90.0), _p(box, 29.0, 38.0), ink, maxf(6.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(25.0, 40.0),
			Vector2(28.0, 24.0),
			Vector2(34.0, 17.0),
			Vector2(34.0, 34.0),
			Vector2(30.0, 43.0)
		],
		spec["light"]
	)


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


static func _human_head(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color, masked: bool = false
) -> void:
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 31.0),
			Vector2(37.0, 21.0),
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
		spec["skin"]
	)
	canvas.draw_line(_p(box, 36.0, 36.0), _p(box, 43.0, 37.0), ink, maxf(2.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 37.0), _p(box, 59.0, 35.0), ink, maxf(2.2 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 38.0, 39.0), _p(box, 43.0, 39.0), spec["light"], maxf(1.7 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 52.0, 39.0), _p(box, 57.0, 38.0), spec["accent"], maxf(1.7 * unit, 1.0), true
	)
	if masked:
		_fill(
			canvas,
			box,
			[
				Vector2(37.0, 43.0),
				Vector2(47.0, 46.0),
				Vector2(58.0, 42.0),
				Vector2(55.0, 53.0),
				Vector2(48.0, 57.0),
				Vector2(40.0, 53.0)
			],
			spec["primary"]
		)
	else:
		canvas.draw_line(
			_p(box, 47.0, 40.0), _p(box, 45.0, 45.0), spec["skin"], maxf(1.2 * unit, 1.0), true
		)
		canvas.draw_line(_p(box, 42.0, 50.0), _p(box, 51.0, 49.0), ink, maxf(1.3 * unit, 1.0), true)


static func _fill(canvas: CanvasItem, box: Rect2, points: Array[Vector2], color: Color) -> void:
	canvas.draw_colored_polygon(_poly(box, points), color)


static func _poly(box: Rect2, points: Array[Vector2]) -> PackedVector2Array:
	var result := PackedVector2Array()
	for point in points:
		result.append(_p(box, point.x, point.y))
	return result


static func _p(box: Rect2, x: float, y: float) -> Vector2:
	return box.position + Vector2(x, y) * box.size.x / SIZE
