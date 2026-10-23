extends RefCounted
## Native canvas portrait: Gravewake, The Tidehunter / Kraken Tidehunter.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(19, 34, 42)
	var skin := Color8(64, 121, 123)
	var shade := Color8(35, 76, 88)
	var light := Color8(156, 214, 198)
	var sea := Color8(83, 177, 169)
	var fin := Color8(109, 75, 112)
	var sucker := Color8(197, 162, 163)
	var shell := Color8(202, 193, 148)
	var iron := Color8(109, 137, 138)
	var rust := Color8(142, 99, 67)
	_backdrop(canvas, box, Color8(32, 77, 96), Color8(14, 29, 43))

	# Curling tentacles and a low wave ring surround a broad kraken silhouette.
	canvas.draw_arc(
		_p(box, 47.0, 47.0), 37.0 * unit, PI * -0.9, PI * -0.1, 40, sea, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 16.0, 46.0), 11.0 * unit, PI * 0.45, PI * 1.95, 40, ink, maxf(9.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 16.0, 46.0),
		10.0 * unit,
		PI * 0.45,
		PI * 1.95,
		40,
		skin,
		maxf(5.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 79.0, 44.0), 11.0 * unit, PI * 1.05, PI * 2.55, 40, ink, maxf(9.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 79.0, 44.0),
		10.0 * unit,
		PI * 1.05,
		PI * 2.55,
		40,
		skin,
		maxf(5.0 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 8.0, 42.0), 1.4 * unit, sucker)
	canvas.draw_circle(_p(box, 10.0, 36.0), 1.4 * unit, sucker)
	canvas.draw_circle(_p(box, 18.0, 36.0), 1.4 * unit, sucker)
	canvas.draw_circle(_p(box, 86.0, 40.0), 1.4 * unit, sucker)
	canvas.draw_circle(_p(box, 84.0, 34.0), 1.4 * unit, sucker)
	canvas.draw_circle(_p(box, 77.0, 34.0), 1.4 * unit, sucker)
	_fill(
		canvas,
		box,
		[
			Vector2(3.0, 96.0),
			Vector2(8.0, 69.0),
			Vector2(24.0, 55.0),
			Vector2(64.0, 54.0),
			Vector2(84.0, 68.0),
			Vector2(93.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 94.0),
			Vector2(14.0, 72.0),
			Vector2(27.0, 61.0),
			Vector2(63.0, 60.0),
			Vector2(78.0, 72.0),
			Vector2(86.0, 94.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(49.0, 61.0),
			Vector2(63.0, 63.0),
			Vector2(78.0, 75.0),
			Vector2(84.0, 94.0),
			Vector2(50.0, 94.0)
		],
		shade
	)

	# Fanned fins, shell plates and barnacles retain a distinctly marine anatomy.
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 67.0),
			Vector2(8.0, 49.0),
			Vector2(18.0, 55.0),
			Vector2(21.0, 44.0),
			Vector2(29.0, 57.0),
			Vector2(34.0, 53.0),
			Vector2(41.0, 68.0),
			Vector2(30.0, 80.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(16.0, 65.0),
			Vector2(14.0, 57.0),
			Vector2(20.0, 61.0),
			Vector2(23.0, 52.0),
			Vector2(28.0, 63.0),
			Vector2(32.0, 59.0),
			Vector2(35.0, 67.0),
			Vector2(28.0, 74.0)
		],
		fin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(55.0, 67.0),
			Vector2(63.0, 53.0),
			Vector2(68.0, 57.0),
			Vector2(77.0, 44.0),
			Vector2(80.0, 55.0),
			Vector2(89.0, 49.0),
			Vector2(86.0, 68.0),
			Vector2(68.0, 80.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(61.0, 67.0),
			Vector2(66.0, 59.0),
			Vector2(70.0, 63.0),
			Vector2(75.0, 52.0),
			Vector2(77.0, 61.0),
			Vector2(83.0, 57.0),
			Vector2(81.0, 65.0),
			Vector2(70.0, 74.0)
		],
		fin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 69.0),
			Vector2(19.0, 61.0),
			Vector2(28.0, 65.0),
			Vector2(33.0, 73.0),
			Vector2(26.0, 79.0),
			Vector2(16.0, 77.0)
		],
		shell
	)
	_fill(
		canvas,
		box,
		[
			Vector2(64.0, 72.0),
			Vector2(70.0, 64.0),
			Vector2(80.0, 63.0),
			Vector2(85.0, 70.0),
			Vector2(79.0, 78.0),
			Vector2(68.0, 78.0)
		],
		iron
	)
	canvas.draw_circle(_p(box, 18.0, 70.0), 2.3 * unit, shell)
	canvas.draw_circle(_p(box, 18.0, 70.0), 1.0 * unit, shade)
	canvas.draw_circle(_p(box, 23.0, 72.0), 2.3 * unit, shell)
	canvas.draw_circle(_p(box, 23.0, 72.0), 1.0 * unit, shade)
	canvas.draw_circle(_p(box, 74.0, 69.0), 2.3 * unit, shell)
	canvas.draw_circle(_p(box, 74.0, 69.0), 1.0 * unit, shade)
	canvas.draw_circle(_p(box, 79.0, 72.0), 2.3 * unit, shell)
	canvas.draw_circle(_p(box, 79.0, 72.0), 1.0 * unit, shade)
	canvas.draw_line(_p(box, 29.0, 69.0), _p(box, 65.0, 94.0), rust, maxf(5.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(43.0, 80.0), Vector2(48.0, 75.0), Vector2(56.0, 81.0), Vector2(51.0, 86.0)],
		iron
	)
	_fill(
		canvas,
		box,
		[Vector2(46.0, 80.0), Vector2(48.0, 78.0), Vector2(53.0, 81.0), Vector2(51.0, 83.0)],
		shade
	)

	# A domed brow and paired cheek tentacles replace human hair and beard.
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 32.0),
			Vector2(28.0, 22.0),
			Vector2(39.0, 15.0),
			Vector2(55.0, 16.0),
			Vector2(65.0, 24.0),
			Vector2(69.0, 36.0),
			Vector2(64.0, 51.0),
			Vector2(56.0, 59.0),
			Vector2(39.0, 61.0),
			Vector2(28.0, 52.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 33.0),
			Vector2(33.0, 25.0),
			Vector2(41.0, 21.0),
			Vector2(53.0, 22.0),
			Vector2(60.0, 28.0),
			Vector2(63.0, 36.0),
			Vector2(59.0, 48.0),
			Vector2(53.0, 54.0),
			Vector2(41.0, 55.0),
			Vector2(33.0, 48.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 23.0),
			Vector2(59.0, 28.0),
			Vector2(63.0, 36.0),
			Vector2(59.0, 47.0),
			Vector2(53.0, 52.0),
			Vector2(48.0, 49.0),
			Vector2(51.0, 40.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 30.0),
			Vector2(33.0, 21.0),
			Vector2(38.0, 25.0),
			Vector2(43.0, 14.0),
			Vector2(48.0, 23.0),
			Vector2(55.0, 17.0),
			Vector2(62.0, 26.0),
			Vector2(64.0, 33.0),
			Vector2(56.0, 30.0),
			Vector2(42.0, 31.0)
		],
		fin
	)
	canvas.draw_line(_p(box, 35.0, 29.0), _p(box, 42.0, 27.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 28.0), _p(box, 57.0, 29.0), light, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(31.0, 35.0), Vector2(43.0, 34.0), Vector2(45.0, 41.0), Vector2(34.0, 42.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(50.0, 34.0), Vector2(63.0, 35.0), Vector2(59.0, 42.0), Vector2(49.0, 41.0)],
		ink
	)
	canvas.draw_line(_p(box, 35.0, 38.0), _p(box, 41.0, 38.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 38.0), _p(box, 58.0, 38.0), light, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(39.0, 46.0),
			Vector2(46.0, 43.0),
			Vector2(54.0, 46.0),
			Vector2(57.0, 53.0),
			Vector2(51.0, 58.0),
			Vector2(41.0, 57.0),
			Vector2(36.0, 52.0)
		],
		ink
	)
	_fill(canvas, box, [Vector2(41.0, 47.0), Vector2(44.0, 47.0), Vector2(43.0, 52.0)], shell)
	_fill(canvas, box, [Vector2(50.0, 47.0), Vector2(53.0, 47.0), Vector2(51.0, 52.0)], shell)
	canvas.draw_arc(
		_p(box, 33.0, 54.0), 8.0 * unit, PI * -0.5, PI * 1.15, 40, ink, maxf(7.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 33.0, 54.0), 7.0 * unit, PI * -0.5, PI * 1.15, 40, sea, maxf(4.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 61.0, 54.0), 8.0 * unit, PI * -0.15, PI * 1.5, 40, ink, maxf(7.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 61.0, 54.0), 7.0 * unit, PI * -0.15, PI * 1.5, 40, sea, maxf(4.0 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 28.0, 53.0), 1.0 * unit, sucker)
	canvas.draw_circle(_p(box, 28.0, 58.0), 1.0 * unit, sucker)
	canvas.draw_circle(_p(box, 36.0, 59.0), 1.0 * unit, sucker)
	canvas.draw_circle(_p(box, 66.0, 53.0), 1.0 * unit, sucker)
	canvas.draw_circle(_p(box, 66.0, 58.0), 1.0 * unit, sucker)
	canvas.draw_circle(_p(box, 58.0, 59.0), 1.0 * unit, sucker)

	# A salvaged anchor and a gripping webbed hand establish the tidehunter kit.
	canvas.draw_line(_p(box, 78.0, 63.0), _p(box, 75.0, 94.0), ink, maxf(7.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 63.0), _p(box, 75.0, 94.0), rust, maxf(3.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 80.0, 24.0), 8.0 * unit, ink)
	canvas.draw_circle(_p(box, 80.0, 24.0), 6.0 * unit, iron)
	canvas.draw_circle(_p(box, 80.0, 24.0), 3.0 * unit, shade)
	canvas.draw_line(_p(box, 80.0, 31.0), _p(box, 78.0, 57.0), ink, maxf(7.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 80.0, 31.0), _p(box, 78.0, 57.0), iron, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 68.0, 38.0), _p(box, 90.0, 40.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 68.0, 38.0), _p(box, 90.0, 40.0), iron, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(60.0, 44.0),
			Vector2(69.0, 48.0),
			Vector2(65.0, 49.0),
			Vector2(71.0, 55.0),
			Vector2(78.0, 57.0),
			Vector2(85.0, 53.0),
			Vector2(87.0, 48.0),
			Vector2(84.0, 47.0),
			Vector2(93.0, 42.0),
			Vector2(92.0, 55.0),
			Vector2(84.0, 63.0),
			Vector2(77.0, 66.0),
			Vector2(66.0, 61.0),
			Vector2(60.0, 54.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(63.0, 49.0),
			Vector2(68.0, 54.0),
			Vector2(72.0, 58.0),
			Vector2(78.0, 61.0),
			Vector2(84.0, 57.0),
			Vector2(89.0, 52.0),
			Vector2(89.0, 49.0),
			Vector2(90.0, 54.0),
			Vector2(82.0, 61.0),
			Vector2(77.0, 63.0),
			Vector2(68.0, 59.0),
			Vector2(63.0, 53.0)
		],
		iron
	)
	canvas.draw_circle(_p(box, 73.0, 80.0), 5.0 * unit, skin)
	canvas.draw_line(_p(box, 71.0, 83.0), _p(box, 77.0, 83.0), sea, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 36.0, 84.0), _p(box, 42.0, 86.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 91.0), _p(box, 59.0, 87.0), sea, maxf(2.0 * unit, 1.0), true)


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
