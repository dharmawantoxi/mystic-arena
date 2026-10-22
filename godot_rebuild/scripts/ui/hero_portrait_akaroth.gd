extends RefCounted
## Native canvas portrait: Akaroth, The Crimson Fist / Crimson Brawler.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(34, 17, 23)
	var skin := Color8(176, 99, 74)
	var light := Color8(225, 151, 104)
	var shade := Color8(113, 54, 48)
	var hair := Color8(46, 27, 30)
	var red := Color8(169, 34, 44)
	var fire := Color8(247, 103, 61)
	var wrap := Color8(229, 199, 150)
	var iron := Color8(74, 67, 68)
	var gold := Color8(216, 153, 73)
	_backdrop(canvas, box, Color8(105, 37, 36), Color8(27, 18, 24))

	# Broken impact rays behind a bare-shouldered, square-jawed brawler.
	canvas.draw_line(_p(box, 12.0, 21.0), _p(box, 25.0, 32.0), fire, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 9.0, 42.0), _p(box, 21.0, 45.0), fire, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 76.0, 30.0), _p(box, 86.0, 17.0), fire, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 47.0), _p(box, 89.0, 41.0), fire, maxf(2.0 * unit, 1.0), true)
	canvas.draw_arc(
		_p(box, 48.0, 48.0),
		38.0 * unit,
		PI * -0.89,
		PI * -0.11,
		32,
		red,
		maxf(2.0 * unit, 1.0),
		true
	)
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 96.0),
			Vector2(9.0, 71.0),
			Vector2(19.0, 58.0),
			Vector2(35.0, 53.0),
			Vector2(60.0, 52.0),
			Vector2(78.0, 59.0),
			Vector2(87.0, 74.0),
			Vector2(88.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 94.0),
			Vector2(13.0, 73.0),
			Vector2(23.0, 62.0),
			Vector2(36.0, 57.0),
			Vector2(59.0, 57.0),
			Vector2(74.0, 63.0),
			Vector2(82.0, 76.0),
			Vector2(83.0, 94.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 64.0),
			Vector2(37.0, 59.0),
			Vector2(46.0, 65.0),
			Vector2(44.0, 76.0),
			Vector2(27.0, 73.0),
			Vector2(19.0, 77.0)
		],
		light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 65.0),
			Vector2(59.0, 59.0),
			Vector2(72.0, 65.0),
			Vector2(78.0, 77.0),
			Vector2(62.0, 73.0),
			Vector2(52.0, 77.0)
		],
		light
	)
	canvas.draw_line(_p(box, 48.0, 67.0), _p(box, 48.0, 89.0), shade, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 29.0, 78.0), _p(box, 42.0, 81.0), shade, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 55.0, 81.0), _p(box, 67.0, 77.0), shade, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(31.0, 89.0), Vector2(65.0, 89.0), Vector2(67.0, 96.0), Vector2(29.0, 96.0)],
		iron
	)
	_fill(
		canvas,
		box,
		[Vector2(43.0, 89.0), Vector2(53.0, 89.0), Vector2(55.0, 96.0), Vector2(41.0, 96.0)],
		gold
	)

	# A cropped black crest, split eyebrow and broad nose mark the fighter.
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 25.0),
			Vector2(36.0, 16.0),
			Vector2(58.0, 16.0),
			Vector2(67.0, 27.0),
			Vector2(64.0, 47.0),
			Vector2(56.0, 58.0),
			Vector2(40.0, 59.0),
			Vector2(31.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 27.0),
			Vector2(39.0, 21.0),
			Vector2(56.0, 21.0),
			Vector2(62.0, 28.0),
			Vector2(60.0, 45.0),
			Vector2(53.0, 54.0),
			Vector2(42.0, 54.0),
			Vector2(35.0, 45.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(49.0, 25.0),
			Vector2(59.0, 25.0),
			Vector2(62.0, 30.0),
			Vector2(59.0, 45.0),
			Vector2(53.0, 52.0),
			Vector2(48.0, 49.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 30.0),
			Vector2(28.0, 21.0),
			Vector2(35.0, 22.0),
			Vector2(37.0, 12.0),
			Vector2(43.0, 17.0),
			Vector2(49.0, 10.0),
			Vector2(53.0, 17.0),
			Vector2(60.0, 14.0),
			Vector2(66.0, 24.0),
			Vector2(64.0, 33.0),
			Vector2(55.0, 26.0),
			Vector2(40.0, 26.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 36.0, 34.0), _p(box, 44.0, 36.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 36.0), _p(box, 60.0, 33.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 38.0), _p(box, 43.0, 38.0), wrap, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 38.0), _p(box, 58.0, 37.0), wrap, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 36.0), _p(box, 44.0, 44.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 44.0, 45.0), _p(box, 51.0, 45.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 40.0, 49.0), _p(box, 55.0, 49.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 42.0, 49.0), _p(box, 52.0, 49.0), wrap, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 57.0, 28.0), _p(box, 54.0, 43.0), fire, maxf(1.5 * unit, 1.0), true)

	# Raised crimson gauntlets dominate the foreground, with wrapped wrists.
	_fill(
		canvas,
		box,
		[
			Vector2(6.0, 64.0),
			Vector2(10.0, 54.0),
			Vector2(20.0, 50.0),
			Vector2(30.0, 54.0),
			Vector2(35.0, 66.0),
			Vector2(32.0, 80.0),
			Vector2(18.0, 85.0),
			Vector2(8.0, 78.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 64.0),
			Vector2(13.0, 57.0),
			Vector2(20.0, 54.0),
			Vector2(27.0, 57.0),
			Vector2(31.0, 67.0),
			Vector2(28.0, 77.0),
			Vector2(18.0, 81.0),
			Vector2(12.0, 76.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 61.0),
			Vector2(16.0, 56.0),
			Vector2(23.0, 56.0),
			Vector2(28.0, 62.0),
			Vector2(26.0, 67.0),
			Vector2(14.0, 66.0)
		],
		fire
	)
	canvas.draw_line(_p(box, 16.0, 58.0), _p(box, 17.0, 64.0), ink, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 21.0, 58.0), _p(box, 22.0, 64.0), ink, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 26.0, 58.0), _p(box, 27.0, 64.0), ink, maxf(1.2 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 70.0),
			Vector2(22.0, 68.0),
			Vector2(28.0, 72.0),
			Vector2(26.0, 77.0),
			Vector2(18.0, 79.0),
			Vector2(13.0, 76.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(17.0, 82.0),
			Vector2(29.0, 78.0),
			Vector2(37.0, 89.0),
			Vector2(34.0, 96.0),
			Vector2(21.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(20.0, 84.0),
			Vector2(28.0, 81.0),
			Vector2(33.0, 90.0),
			Vector2(31.0, 94.0),
			Vector2(24.0, 94.0)
		],
		wrap
	)
	canvas.draw_line(_p(box, 22.0, 87.0), _p(box, 30.0, 85.0), shade, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 24.0, 92.0), _p(box, 32.0, 89.0), shade, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 65.0),
			Vector2(67.0, 51.0),
			Vector2(79.0, 47.0),
			Vector2(89.0, 55.0),
			Vector2(91.0, 68.0),
			Vector2(87.0, 79.0),
			Vector2(73.0, 83.0),
			Vector2(65.0, 77.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(66.0, 65.0),
			Vector2(70.0, 54.0),
			Vector2(78.0, 51.0),
			Vector2(86.0, 57.0),
			Vector2(87.0, 67.0),
			Vector2(84.0, 76.0),
			Vector2(74.0, 79.0),
			Vector2(69.0, 74.0)
		],
		red
	)
	_fill(
		canvas,
		box,
		[
			Vector2(70.0, 57.0),
			Vector2(76.0, 53.0),
			Vector2(83.0, 56.0),
			Vector2(86.0, 62.0),
			Vector2(82.0, 66.0),
			Vector2(69.0, 63.0)
		],
		fire
	)
	canvas.draw_line(_p(box, 73.0, 56.0), _p(box, 72.0, 62.0), ink, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 56.0), _p(box, 77.0, 62.0), ink, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 83.0, 56.0), _p(box, 82.0, 62.0), ink, maxf(1.2 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(70.0, 69.0),
			Vector2(78.0, 66.0),
			Vector2(85.0, 69.0),
			Vector2(82.0, 75.0),
			Vector2(74.0, 76.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 80.0),
			Vector2(81.0, 82.0),
			Vector2(76.0, 96.0),
			Vector2(61.0, 96.0),
			Vector2(60.0, 88.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(69.0, 83.0),
			Vector2(77.0, 85.0),
			Vector2(73.0, 94.0),
			Vector2(65.0, 94.0),
			Vector2(64.0, 89.0)
		],
		wrap
	)
	canvas.draw_line(_p(box, 67.0, 87.0), _p(box, 76.0, 89.0), shade, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 65.0, 91.0), _p(box, 74.0, 93.0), shade, maxf(1.5 * unit, 1.0), true)

	# Small sparks and rivets finish the heavy fist silhouette.
	canvas.draw_circle(_p(box, 12.0, 69.0), 1.3 * unit, gold)
	canvas.draw_circle(_p(box, 28.0, 68.0), 1.3 * unit, gold)
	canvas.draw_circle(_p(box, 68.0, 67.0), 1.3 * unit, gold)
	canvas.draw_circle(_p(box, 86.0, 67.0), 1.3 * unit, gold)
	canvas.draw_circle(_p(box, 9.0, 48.0), 1.5 * unit, fire)
	canvas.draw_circle(_p(box, 86.0, 34.0), 1.2 * unit, wrap)


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
