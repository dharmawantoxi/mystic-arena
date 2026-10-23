extends RefCounted
## Native canvas portrait: Gravefang, The Bone Devourer / Earth Guardian.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(34, 32, 27)
	var hide := Color8(95, 104, 73)
	var shade := Color8(59, 69, 50)
	var earth := Color8(127, 104, 67)
	var bone := Color8(185, 179, 139)
	var light := Color8(231, 222, 176)
	var darkbone := Color8(124, 126, 99)
	var moss := Color8(81, 121, 65)
	var eye := Color8(179, 218, 105)
	_backdrop(canvas, box, Color8(72, 82, 53), Color8(26, 32, 26))

	# Root tangles and broken ribs frame a hunched earth-bound bone guardian.
	canvas.draw_line(_p(box, 10.0, 72.0), _p(box, 14.0, 37.0), earth, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 14.0, 37.0), _p(box, 7.0, 23.0), earth, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 84.0, 69.0), _p(box, 80.0, 36.0), shade, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 80.0, 36.0), _p(box, 89.0, 22.0), earth, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(5.0, 96.0),
			Vector2(9.0, 66.0),
			Vector2(24.0, 51.0),
			Vector2(35.0, 54.0),
			Vector2(44.0, 47.0),
			Vector2(62.0, 51.0),
			Vector2(81.0, 61.0),
			Vector2(91.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 94.0),
			Vector2(15.0, 69.0),
			Vector2(26.0, 57.0),
			Vector2(36.0, 60.0),
			Vector2(45.0, 53.0),
			Vector2(60.0, 57.0),
			Vector2(75.0, 66.0),
			Vector2(85.0, 94.0)
		],
		hide
	)
	_fill(
		canvas,
		box,
		[
			Vector2(49.0, 56.0),
			Vector2(62.0, 59.0),
			Vector2(76.0, 70.0),
			Vector2(83.0, 94.0),
			Vector2(49.0, 94.0)
		],
		shade
	)

	# Uneven fossil plates and rib-like arcs wrap the broad shoulders and chest.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 66.0),
			Vector2(13.0, 48.0),
			Vector2(22.0, 42.0),
			Vector2(33.0, 49.0),
			Vector2(39.0, 65.0),
			Vector2(31.0, 81.0),
			Vector2(15.0, 81.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 65.0),
			Vector2(18.0, 52.0),
			Vector2(23.0, 48.0),
			Vector2(29.0, 53.0),
			Vector2(33.0, 65.0),
			Vector2(28.0, 76.0),
			Vector2(18.0, 76.0)
		],
		bone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 51.0),
			Vector2(29.0, 55.0),
			Vector2(32.0, 65.0),
			Vector2(27.0, 73.0),
			Vector2(24.0, 67.0)
		],
		darkbone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(59.0, 64.0),
			Vector2(65.0, 47.0),
			Vector2(74.0, 44.0),
			Vector2(85.0, 53.0),
			Vector2(88.0, 69.0),
			Vector2(80.0, 81.0),
			Vector2(65.0, 79.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(64.0, 65.0),
			Vector2(69.0, 52.0),
			Vector2(74.0, 50.0),
			Vector2(81.0, 56.0),
			Vector2(83.0, 68.0),
			Vector2(77.0, 76.0),
			Vector2(68.0, 74.0)
		],
		bone
	)
	canvas.draw_line(_p(box, 17.0, 61.0), _p(box, 22.0, 53.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 70.0, 58.0), _p(box, 74.0, 54.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 34.0, 71.0), _p(box, 38.0, 93.0), earth, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 60.0, 70.0), _p(box, 57.0, 94.0), earth, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 36.0, 74.0), _p(box, 44.0, 78.0), bone, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 36.0, 81.0), _p(box, 44.0, 84.0), bone, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 88.0), _p(box, 44.0, 90.0), bone, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 78.0), _p(box, 59.0, 73.0), bone, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 84.0), _p(box, 58.0, 80.0), bone, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 90.0), _p(box, 57.0, 87.0), bone, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(45.0, 71.0), Vector2(50.0, 70.0), Vector2(50.0, 94.0), Vector2(45.0, 94.0)],
		earth
	)

	# A heavy skull muzzle and a jagged fossil crest make the nonhuman face.
	_fill(
		canvas,
		box,
		[
			Vector2(23.0, 33.0),
			Vector2(28.0, 20.0),
			Vector2(40.0, 17.0),
			Vector2(46.0, 10.0),
			Vector2(57.0, 17.0),
			Vector2(67.0, 23.0),
			Vector2(70.0, 38.0),
			Vector2(65.0, 54.0),
			Vector2(56.0, 63.0),
			Vector2(38.0, 63.0),
			Vector2(27.0, 53.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 34.0),
			Vector2(33.0, 25.0),
			Vector2(42.0, 22.0),
			Vector2(47.0, 16.0),
			Vector2(54.0, 22.0),
			Vector2(62.0, 27.0),
			Vector2(64.0, 38.0),
			Vector2(60.0, 51.0),
			Vector2(53.0, 57.0),
			Vector2(40.0, 58.0),
			Vector2(32.0, 49.0)
		],
		bone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 23.0),
			Vector2(61.0, 28.0),
			Vector2(64.0, 38.0),
			Vector2(59.0, 50.0),
			Vector2(53.0, 56.0),
			Vector2(49.0, 49.0),
			Vector2(53.0, 39.0)
		],
		darkbone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 32.0),
			Vector2(36.0, 27.0),
			Vector2(42.0, 25.0),
			Vector2(44.0, 30.0),
			Vector2(38.0, 34.0)
		],
		light
	)
	_fill(
		canvas,
		box,
		[Vector2(30.0, 37.0), Vector2(41.0, 35.0), Vector2(44.0, 43.0), Vector2(33.0, 44.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(51.0, 35.0), Vector2(64.0, 36.0), Vector2(60.0, 44.0), Vector2(50.0, 43.0)],
		ink
	)
	canvas.draw_line(_p(box, 34.0, 40.0), _p(box, 40.0, 40.0), eye, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 40.0), _p(box, 59.0, 40.0), eye, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(45.0, 38.0),
			Vector2(49.0, 38.0),
			Vector2(52.0, 47.0),
			Vector2(46.0, 49.0),
			Vector2(41.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(43.0, 42.0), Vector2(47.0, 40.0), Vector2(49.0, 46.0), Vector2(45.0, 47.0)],
		darkbone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 47.0),
			Vector2(42.0, 51.0),
			Vector2(52.0, 51.0),
			Vector2(62.0, 46.0),
			Vector2(60.0, 56.0),
			Vector2(52.0, 62.0),
			Vector2(40.0, 61.0),
			Vector2(32.0, 55.0)
		],
		ink
	)
	_fill(canvas, box, [Vector2(34.0, 48.0), Vector2(38.0, 50.0), Vector2(37.0, 57.0)], light)
	_fill(canvas, box, [Vector2(55.0, 51.0), Vector2(60.0, 48.0), Vector2(57.0, 57.0)], light)
	_fill(canvas, box, [Vector2(42.0, 59.0), Vector2(44.0, 53.0), Vector2(46.0, 60.0)], bone)
	_fill(canvas, box, [Vector2(49.0, 60.0), Vector2(51.0, 53.0), Vector2(53.0, 59.0)], bone)
	canvas.draw_line(_p(box, 47.0, 19.0), _p(box, 44.0, 27.0), earth, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 44.0, 27.0), _p(box, 48.0, 32.0), earth, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 28.0, 29.0), _p(box, 32.0, 25.0), moss, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 62.0, 48.0), _p(box, 59.0, 53.0), moss, maxf(2.0 * unit, 1.0), true)

	# Root-bound fists, fossil claws and moss patches complete the guardian.
	_fill(
		canvas,
		box,
		[
			Vector2(6.0, 81.0),
			Vector2(17.0, 76.0),
			Vector2(28.0, 81.0),
			Vector2(34.0, 91.0),
			Vector2(29.0, 96.0),
			Vector2(5.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 84.0),
			Vector2(18.0, 81.0),
			Vector2(25.0, 85.0),
			Vector2(28.0, 91.0),
			Vector2(25.0, 93.0),
			Vector2(10.0, 93.0)
		],
		hide
	)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 81.0),
			Vector2(79.0, 76.0),
			Vector2(90.0, 82.0),
			Vector2(92.0, 96.0),
			Vector2(67.0, 96.0),
			Vector2(62.0, 90.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(69.0, 85.0),
			Vector2(79.0, 81.0),
			Vector2(85.0, 85.0),
			Vector2(87.0, 93.0),
			Vector2(70.0, 93.0),
			Vector2(67.0, 90.0)
		],
		hide
	)
	_fill(
		canvas,
		box,
		[Vector2(12.0, 86.0), Vector2(16.0, 85.0), Vector2(15.0, 94.0), Vector2(12.0, 96.0)],
		bone
	)
	_fill(
		canvas,
		box,
		[Vector2(19.0, 86.0), Vector2(23.0, 85.0), Vector2(22.0, 94.0), Vector2(19.0, 96.0)],
		bone
	)
	_fill(
		canvas,
		box,
		[Vector2(73.0, 86.0), Vector2(77.0, 85.0), Vector2(76.0, 94.0), Vector2(73.0, 96.0)],
		bone
	)
	_fill(
		canvas,
		box,
		[Vector2(80.0, 86.0), Vector2(84.0, 85.0), Vector2(83.0, 94.0), Vector2(80.0, 96.0)],
		bone
	)
	canvas.draw_line(_p(box, 12.0, 82.0), _p(box, 24.0, 90.0), earth, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 72.0, 90.0), _p(box, 85.0, 82.0), earth, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 22.0, 69.0), 3.0 * unit, moss)
	canvas.draw_circle(_p(box, 74.0, 68.0), 2.5 * unit, moss)


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
