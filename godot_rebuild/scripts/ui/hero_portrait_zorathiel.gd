extends RefCounted
## Native canvas portrait: Zorathiel, The Arcane Mage.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(28, 23, 49)
	var robe := Color8(66, 48, 110)
	var purple := Color8(115, 71, 158)
	var blue := Color8(66, 133, 175)
	var cyan := Color8(102, 222, 222)
	var light := Color8(220, 250, 230)
	var gold := Color8(207, 174, 100)
	var skin := Color8(186, 158, 181)
	var shade := Color8(120, 99, 147)
	var hair := Color8(211, 214, 224)
	_backdrop(canvas, box, Color8(75, 52, 112), Color8(24, 25, 51))

	# Arcane orbitals, runic spokes and small prism satellites fill the back field.
	canvas.draw_arc(
		_p(box, 47.0, 40.0), 35.0 * unit, PI * 0.1, PI * 1.75, 64, cyan, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 47.0, 40.0), 29.0 * unit, PI * 0.85, PI * 2.3, 64, gold, maxf(1.2 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 47.0, 5.0), _p(box, 47.0, 13.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 12.0, 40.0), _p(box, 20.0, 40.0), cyan, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 74.0, 40.0), _p(box, 82.0, 40.0), gold, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[Vector2(15.0, 19.0), Vector2(19.0, 14.0), Vector2(22.0, 20.0), Vector2(18.0, 25.0)],
		purple
	)
	_fill(
		canvas,
		box,
		[Vector2(16.0, 19.0), Vector2(19.0, 16.0), Vector2(20.0, 20.0), Vector2(18.0, 22.0)],
		light
	)
	_fill(
		canvas,
		box,
		[Vector2(77.0, 18.0), Vector2(82.0, 13.0), Vector2(85.0, 20.0), Vector2(80.0, 25.0)],
		blue
	)
	canvas.draw_circle(_p(box, 81.0, 19.0), 1.5 * unit, cyan)

	# A narrow embroidered robe and split high collar keep the mage silhouette tall.
	_fill(
		canvas,
		box,
		[
			Vector2(10.0, 96.0),
			Vector2(16.0, 73.0),
			Vector2(31.0, 58.0),
			Vector2(61.0, 58.0),
			Vector2(78.0, 73.0),
			Vector2(85.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(17.0, 94.0),
			Vector2(23.0, 75.0),
			Vector2(34.0, 64.0),
			Vector2(58.0, 64.0),
			Vector2(71.0, 75.0),
			Vector2(78.0, 94.0)
		],
		robe
	)
	_fill(
		canvas,
		box,
		[
			Vector2(18.0, 94.0),
			Vector2(24.0, 76.0),
			Vector2(35.0, 66.0),
			Vector2(43.0, 79.0),
			Vector2(38.0, 94.0)
		],
		purple
	)
	_fill(
		canvas,
		box,
		[
			Vector2(53.0, 78.0),
			Vector2(59.0, 66.0),
			Vector2(70.0, 76.0),
			Vector2(76.0, 94.0),
			Vector2(58.0, 94.0)
		],
		blue
	)
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 67.0),
			Vector2(19.0, 42.0),
			Vector2(32.0, 50.0),
			Vector2(41.0, 67.0),
			Vector2(34.0, 76.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 64.0),
			Vector2(24.0, 51.0),
			Vector2(32.0, 56.0),
			Vector2(36.0, 67.0),
			Vector2(33.0, 69.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(54.0, 67.0),
			Vector2(64.0, 49.0),
			Vector2(76.0, 41.0),
			Vector2(71.0, 68.0),
			Vector2(62.0, 76.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(60.0, 66.0),
			Vector2(65.0, 56.0),
			Vector2(71.0, 50.0),
			Vector2(67.0, 65.0),
			Vector2(63.0, 69.0)
		],
		gold
	)

	# Geometric embroidery converges on a floating arcane chest prism.
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 70.0),
			Vector2(46.0, 77.0),
			Vector2(59.0, 69.0),
			Vector2(56.0, 82.0),
			Vector2(47.0, 89.0),
			Vector2(37.0, 82.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(47.0, 71.0), Vector2(54.0, 79.0), Vector2(47.0, 86.0), Vector2(40.0, 79.0)],
		cyan
	)
	_fill(canvas, box, [Vector2(47.0, 71.0), Vector2(47.0, 81.0), Vector2(40.0, 79.0)], light)
	canvas.draw_line(_p(box, 30.0, 86.0), _p(box, 39.0, 91.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 56.0, 91.0), _p(box, 65.0, 85.0), cyan, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 88.0), _p(box, 47.0, 94.0), gold, maxf(1.5 * unit, 1.0), true)

	# Silver hair, long ears and a three-point circlet frame the angular face.
	_fill(
		canvas,
		box,
		[Vector2(33.0, 34.0), Vector2(20.0, 27.0), Vector2(27.0, 43.0), Vector2(36.0, 46.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(31.0, 35.0), Vector2(24.0, 31.0), Vector2(29.0, 40.0), Vector2(34.0, 42.0)],
		skin
	)
	_fill(
		canvas,
		box,
		[Vector2(61.0, 34.0), Vector2(75.0, 26.0), Vector2(68.0, 43.0), Vector2(59.0, 46.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(63.0, 35.0), Vector2(71.0, 30.0), Vector2(66.0, 40.0), Vector2(61.0, 42.0)],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 44.0),
			Vector2(26.0, 24.0),
			Vector2(34.0, 12.0),
			Vector2(47.0, 6.0),
			Vector2(61.0, 12.0),
			Vector2(69.0, 26.0),
			Vector2(66.0, 50.0),
			Vector2(58.0, 60.0),
			Vector2(36.0, 59.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 42.0),
			Vector2(31.0, 26.0),
			Vector2(37.0, 17.0),
			Vector2(47.0, 12.0),
			Vector2(58.0, 17.0),
			Vector2(64.0, 27.0),
			Vector2(62.0, 46.0),
			Vector2(56.0, 54.0),
			Vector2(38.0, 54.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 32.0),
			Vector2(38.0, 23.0),
			Vector2(55.0, 22.0),
			Vector2(63.0, 31.0),
			Vector2(61.0, 47.0),
			Vector2(54.0, 57.0),
			Vector2(41.0, 57.0),
			Vector2(34.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 33.0),
			Vector2(42.0, 27.0),
			Vector2(54.0, 27.0),
			Vector2(59.0, 32.0),
			Vector2(58.0, 44.0),
			Vector2(53.0, 52.0),
			Vector2(43.0, 52.0),
			Vector2(38.0, 45.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(52.0, 28.0),
			Vector2(58.0, 32.0),
			Vector2(59.0, 39.0),
			Vector2(55.0, 47.0),
			Vector2(51.0, 51.0),
			Vector2(48.0, 47.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 31.0),
			Vector2(36.0, 20.0),
			Vector2(47.0, 15.0),
			Vector2(60.0, 20.0),
			Vector2(65.0, 32.0),
			Vector2(56.0, 27.0),
			Vector2(48.0, 30.0),
			Vector2(39.0, 26.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 28.0),
			Vector2(41.0, 23.0),
			Vector2(47.0, 27.0),
			Vector2(54.0, 22.0),
			Vector2(61.0, 28.0)
		],
		gold
	)
	_fill(
		canvas,
		box,
		[Vector2(44.0, 25.0), Vector2(47.0, 20.0), Vector2(51.0, 25.0), Vector2(47.0, 30.0)],
		cyan
	)
	canvas.draw_circle(_p(box, 47.0, 25.0), 1.0 * unit, light)
	canvas.draw_line(_p(box, 37.0, 35.0), _p(box, 44.0, 36.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 36.0), _p(box, 58.0, 34.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 39.0, 39.0), _p(box, 44.0, 39.0), cyan, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 39.0), _p(box, 57.0, 38.0), light, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 38.0), _p(box, 45.0, 44.0), skin, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 42.0, 48.0), _p(box, 51.0, 48.0), ink, maxf(1.2 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 34.0),
			Vector2(36.0, 31.0),
			Vector2(35.0, 49.0),
			Vector2(39.0, 57.0),
			Vector2(32.0, 51.0)
		],
		hair
	)
	_fill(
		canvas,
		box,
		[
			Vector2(59.0, 30.0),
			Vector2(63.0, 34.0),
			Vector2(62.0, 50.0),
			Vector2(56.0, 58.0),
			Vector2(59.0, 45.0)
		],
		hair
	)

	# An open hand levitates a faceted focus; no conventional weapon is needed.
	_fill(
		canvas,
		box,
		[
			Vector2(66.0, 94.0),
			Vector2(65.0, 82.0),
			Vector2(70.0, 76.0),
			Vector2(72.0, 67.0),
			Vector2(76.0, 67.0),
			Vector2(78.0, 76.0),
			Vector2(83.0, 70.0),
			Vector2(87.0, 72.0),
			Vector2(84.0, 83.0),
			Vector2(88.0, 91.0),
			Vector2(84.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(71.0, 91.0),
			Vector2(70.0, 83.0),
			Vector2(75.0, 79.0),
			Vector2(81.0, 80.0),
			Vector2(83.0, 88.0),
			Vector2(80.0, 92.0)
		],
		skin
	)
	canvas.draw_line(_p(box, 74.0, 79.0), _p(box, 74.0, 70.0), skin, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 79.0, 79.0), _p(box, 84.0, 73.0), skin, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 68.0), _p(box, 80.0, 59.0), cyan, maxf(1.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(73.0, 52.0),
			Vector2(80.0, 45.0),
			Vector2(88.0, 52.0),
			Vector2(85.0, 61.0),
			Vector2(78.0, 65.0),
			Vector2(72.0, 59.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 53.0),
			Vector2(80.0, 49.0),
			Vector2(84.0, 53.0),
			Vector2(82.0, 59.0),
			Vector2(78.0, 61.0)
		],
		cyan
	)
	_fill(canvas, box, [Vector2(80.0, 49.0), Vector2(80.0, 57.0), Vector2(77.0, 53.0)], light)
	canvas.draw_arc(
		_p(box, 80.0, 55.0), 12.0 * unit, PI * -0.8, PI * 0.8, 32, gold, maxf(1.0 * unit, 1.0), true
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


static func _backdrop(canvas: CanvasItem, box: Rect2, top: Color, bottom: Color) -> void:
	var bands := 18
	var height := box.size.y / float(bands)
	for index in bands:
		var band := Rect2(
			box.position.x, box.position.y + height * float(index), box.size.x, height + 1.0
		)
		canvas.draw_rect(band, top.lerp(bottom, float(index) / float(bands - 1)))
