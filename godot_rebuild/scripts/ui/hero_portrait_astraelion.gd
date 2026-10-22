extends RefCounted
## Native canvas portrait: Astraelion, The Starlight Swordmaster / Starlight Assassin.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(15, 19, 40)
	var cloak := Color8(42, 38, 88)
	var violet := Color8(102, 78, 160)
	var blue := Color8(93, 163, 223)
	var star := Color8(218, 240, 255)
	var skin := Color8(187, 174, 204)
	var shade := Color8(116, 111, 155)
	var hair := Color8(174, 194, 228)
	var silver := Color8(151, 178, 211)
	_backdrop(canvas, box, Color8(39, 41, 95), Color8(13, 19, 40))

	# Constellation lines and offset stars frame an unhooded swordmaster.
	canvas.draw_line(_p(box, 13.0, 31.0), _p(box, 24.0, 16.0), violet, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 24.0, 16.0), _p(box, 49.0, 10.0), violet, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 49.0, 10.0), _p(box, 76.0, 20.0), violet, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 76.0, 20.0), _p(box, 84.0, 38.0), violet, maxf(1.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 13.0, 31.0), 2.0 * unit, blue)
	canvas.draw_circle(_p(box, 13.0, 31.0), 0.8 * unit, star)
	canvas.draw_circle(_p(box, 24.0, 16.0), 2.0 * unit, blue)
	canvas.draw_circle(_p(box, 24.0, 16.0), 0.8 * unit, star)
	canvas.draw_circle(_p(box, 49.0, 10.0), 2.0 * unit, blue)
	canvas.draw_circle(_p(box, 49.0, 10.0), 0.8 * unit, star)
	canvas.draw_circle(_p(box, 76.0, 20.0), 2.0 * unit, blue)
	canvas.draw_circle(_p(box, 76.0, 20.0), 0.8 * unit, star)
	canvas.draw_circle(_p(box, 84.0, 38.0), 2.0 * unit, blue)
	canvas.draw_circle(_p(box, 84.0, 38.0), 0.8 * unit, star)
	canvas.draw_arc(
		_p(box, 47.0, 43.0),
		34.0 * unit,
		PI * -0.8,
		PI * -0.18,
		32,
		blue,
		maxf(1.0 * unit, 1.0),
		true
	)

	# Flowing asymmetric cape and slim armour contrast with tank silhouettes.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 95.0),
			Vector2(19.0, 63.0),
			Vector2(33.0, 54.0),
			Vector2(58.0, 54.0),
			Vector2(77.0, 66.0),
			Vector2(88.0, 94.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 93.0),
			Vector2(23.0, 65.0),
			Vector2(34.0, 58.0),
			Vector2(57.0, 58.0),
			Vector2(73.0, 69.0),
			Vector2(83.0, 92.0)
		],
		cloak
	)
	_fill(
		canvas,
		box,
		[
			Vector2(19.0, 71.0),
			Vector2(30.0, 60.0),
			Vector2(41.0, 65.0),
			Vector2(32.0, 78.0),
			Vector2(20.0, 90.0)
		],
		violet
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 62.0),
			Vector2(47.0, 58.0),
			Vector2(61.0, 64.0),
			Vector2(67.0, 94.0),
			Vector2(28.0, 94.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 65.0),
			Vector2(47.0, 62.0),
			Vector2(58.0, 67.0),
			Vector2(62.0, 92.0),
			Vector2(33.0, 92.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[Vector2(36.0, 66.0), Vector2(46.0, 70.0), Vector2(48.0, 82.0), Vector2(37.0, 78.0)],
		silver
	)
	_fill(
		canvas,
		box,
		[Vector2(50.0, 70.0), Vector2(58.0, 68.0), Vector2(60.0, 78.0), Vector2(51.0, 82.0)],
		blue
	)
	canvas.draw_line(_p(box, 48.0, 84.0), _p(box, 48.0, 94.0), ink, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 28.0),
			Vector2(37.0, 19.0),
			Vector2(54.0, 18.0),
			Vector2(64.0, 27.0),
			Vector2(65.0, 41.0),
			Vector2(58.0, 53.0),
			Vector2(45.0, 59.0),
			Vector2(34.0, 51.0),
			Vector2(29.0, 40.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 30.0),
			Vector2(40.0, 23.0),
			Vector2(53.0, 22.0),
			Vector2(60.0, 29.0),
			Vector2(61.0, 40.0),
			Vector2(55.0, 49.0),
			Vector2(45.0, 55.0),
			Vector2(37.0, 48.0),
			Vector2(33.0, 39.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 25.0),
			Vector2(59.0, 29.0),
			Vector2(61.0, 39.0),
			Vector2(54.0, 48.0),
			Vector2(47.0, 51.0),
			Vector2(49.0, 43.0)
		],
		shade
	)

	# Swept silver fringe, star-blue eyes and a narrow cheek mark.
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 32.0),
			Vector2(29.0, 21.0),
			Vector2(37.0, 22.0),
			Vector2(41.0, 12.0),
			Vector2(48.0, 18.0),
			Vector2(58.0, 16.0),
			Vector2(65.0, 24.0),
			Vector2(67.0, 35.0),
			Vector2(59.0, 30.0),
			Vector2(53.0, 23.0),
			Vector2(47.0, 32.0),
			Vector2(43.0, 26.0),
			Vector2(36.0, 36.0),
			Vector2(35.0, 49.0),
			Vector2(29.0, 43.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[Vector2(34.0, 26.0), Vector2(41.0, 18.0), Vector2(45.0, 23.0), Vector2(39.0, 29.0)],
		star
	)
	canvas.draw_line(_p(box, 37.0, 36.0), _p(box, 44.0, 37.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 37.0), _p(box, 58.0, 35.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 39.0), _p(box, 43.0, 39.0), blue, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 39.0), _p(box, 57.0, 38.0), blue, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 37.0), _p(box, 45.0, 43.0), star, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 43.0, 48.0), _p(box, 52.0, 47.0), ink, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 57.0, 41.0), _p(box, 54.0, 46.0), violet, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 49.0),
			Vector2(43.0, 59.0),
			Vector2(61.0, 50.0),
			Vector2(64.0, 60.0),
			Vector2(49.0, 70.0),
			Vector2(34.0, 63.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 54.0),
			Vector2(44.0, 63.0),
			Vector2(60.0, 55.0),
			Vector2(60.0, 60.0),
			Vector2(49.0, 66.0),
			Vector2(37.0, 61.0)
		],
		cloak
	)
	canvas.draw_line(_p(box, 37.0, 58.0), _p(box, 46.0, 64.0), silver, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(48.0, 62.0),
			Vector2(50.0, 67.0),
			Vector2(55.0, 69.0),
			Vector2(50.0, 71.0),
			Vector2(48.0, 76.0),
			Vector2(46.0, 71.0),
			Vector2(41.0, 69.0),
			Vector2(46.0, 67.0)
		],
		star
	)
	canvas.draw_circle(_p(box, 48.0, 69.0), 1.8 * unit, blue)

	# A slender luminous sword stands upright, paired with a reverse-grip blade.
	_fill(
		canvas,
		box,
		[
			Vector2(73.0, 77.0),
			Vector2(70.0, 23.0),
			Vector2(74.0, 9.0),
			Vector2(79.0, 23.0),
			Vector2(77.0, 77.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(74.0, 73.0),
			Vector2(73.0, 24.0),
			Vector2(74.0, 15.0),
			Vector2(76.0, 24.0),
			Vector2(76.0, 73.0)
		],
		silver
	)
	canvas.draw_line(_p(box, 74.0, 20.0), _p(box, 75.0, 70.0), star, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 66.0, 77.0), _p(box, 84.0, 77.0), ink, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 67.0, 77.0), _p(box, 83.0, 77.0), blue, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 75.0, 80.0), _p(box, 75.0, 93.0), ink, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 75.0, 81.0), _p(box, 75.0, 91.0), violet, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 75.0, 92.0), 2.0 * unit, star)
	_fill(
		canvas,
		box,
		[
			Vector2(19.0, 65.0),
			Vector2(24.0, 72.0),
			Vector2(34.0, 90.0),
			Vector2(29.0, 94.0),
			Vector2(20.0, 75.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(21.0, 69.0),
			Vector2(24.0, 74.0),
			Vector2(31.0, 88.0),
			Vector2(29.0, 90.0),
			Vector2(22.0, 75.0)
		],
		silver
	)
	canvas.draw_line(_p(box, 24.0, 91.0), _p(box, 36.0, 86.0), blue, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 70.0, 82.0), 4.0 * unit, skin)
	canvas.draw_line(_p(box, 68.0, 84.0), _p(box, 73.0, 85.0), cloak, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 21.0, 53.0), 1.5 * unit, blue)
	canvas.draw_circle(_p(box, 83.0, 55.0), 1.1 * unit, star)


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
