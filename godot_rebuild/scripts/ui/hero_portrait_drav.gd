extends RefCounted
## Native canvas portrait: Drav, The Tideforged Warden.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(19, 35, 43)
	var steel := Color8(55, 103, 116)
	var shade := Color8(33, 65, 81)
	var light := Color8(193, 230, 223)
	var bronze := Color8(154, 130, 75)
	var gold := Color8(215, 189, 118)
	var skin := Color8(123, 157, 155)
	var hair := Color8(168, 198, 190)
	var sea := Color8(76, 187, 185)
	var coral := Color8(186, 118, 89)
	var shell := Color8(214, 205, 168)
	_backdrop(canvas, box, Color8(32, 89, 108), Color8(15, 31, 46))

	# Wave arcs, bubbles and a reef crest frame a weathered sea warden.
	canvas.draw_arc(
		_p(box, 44.0, 45.0),
		34.0 * unit,
		PI * -0.9,
		PI * -0.15,
		40,
		sea,
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 47.0, 49.0), 39.0 * unit, PI * 0.1, PI * 0.8, 40, steel, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 13.0, 28.0), 2.0 * unit, PI * 0, PI * 2, 40, light, maxf(1.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 20.0, 17.0), 1.3 * unit, PI * 0, PI * 2, 40, light, maxf(1.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 78.0, 21.0), 2.0 * unit, PI * 0, PI * 2, 40, light, maxf(1.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 86.0, 47.0), 1.5 * unit, PI * 0, PI * 2, 40, light, maxf(1.0 * unit, 1.0), true
	)
	_fill(
		canvas,
		box,
		[
			Vector2(7.0, 96.0),
			Vector2(13.0, 67.0),
			Vector2(29.0, 55.0),
			Vector2(61.0, 55.0),
			Vector2(80.0, 68.0),
			Vector2(89.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 94.0),
			Vector2(19.0, 70.0),
			Vector2(31.0, 61.0),
			Vector2(59.0, 61.0),
			Vector2(74.0, 71.0),
			Vector2(83.0, 94.0)
		],
		shade
	)

	# Barnacle-studded scallop pauldrons and overlapping tide-forged plates.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 68.0),
			Vector2(17.0, 53.0),
			Vector2(29.0, 52.0),
			Vector2(38.0, 66.0),
			Vector2(33.0, 81.0),
			Vector2(15.0, 81.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 68.0),
			Vector2(20.0, 58.0),
			Vector2(27.0, 57.0),
			Vector2(33.0, 67.0),
			Vector2(29.0, 76.0),
			Vector2(18.0, 76.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 15.0, 70.0), _p(box, 30.0, 70.0), bronze, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 20.0, 61.0), _p(box, 20.0, 67.0), sea, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 25.0, 60.0), _p(box, 26.0, 67.0), sea, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(56.0, 66.0),
			Vector2(64.0, 52.0),
			Vector2(76.0, 53.0),
			Vector2(85.0, 68.0),
			Vector2(78.0, 81.0),
			Vector2(61.0, 81.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(61.0, 67.0),
			Vector2(66.0, 57.0),
			Vector2(73.0, 58.0),
			Vector2(80.0, 68.0),
			Vector2(75.0, 76.0),
			Vector2(65.0, 76.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 64.0, 70.0), _p(box, 79.0, 70.0), bronze, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 68.0, 60.0), _p(box, 67.0, 67.0), sea, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 73.0, 61.0), _p(box, 73.0, 67.0), sea, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 16.0, 72.0), 2.0 * unit, shell)
	canvas.draw_circle(_p(box, 16.0, 72.0), 0.8 * unit, shade)
	canvas.draw_circle(_p(box, 21.0, 74.0), 2.0 * unit, shell)
	canvas.draw_circle(_p(box, 21.0, 74.0), 0.8 * unit, shade)
	canvas.draw_circle(_p(box, 76.0, 72.0), 2.0 * unit, shell)
	canvas.draw_circle(_p(box, 76.0, 72.0), 0.8 * unit, shade)
	canvas.draw_circle(_p(box, 71.0, 74.0), 2.0 * unit, shell)
	canvas.draw_circle(_p(box, 71.0, 74.0), 0.8 * unit, shade)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 65.0),
			Vector2(46.0, 60.0),
			Vector2(59.0, 66.0),
			Vector2(65.0, 94.0),
			Vector2(28.0, 94.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 64.0), Vector2(58.0, 68.0), Vector2(63.0, 93.0), Vector2(49.0, 93.0)],
		shade
	)
	canvas.draw_line(_p(box, 34.0, 72.0), _p(box, 46.0, 77.0), bronze, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 49.0, 77.0), _p(box, 59.0, 72.0), bronze, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 33.0, 82.0), _p(box, 45.0, 86.0), sea, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 86.0), _p(box, 61.0, 82.0), sea, maxf(2.0 * unit, 1.0), true)

	# An open ridged helm, coral branches and a split sea-grey beard.
	_fill(
		canvas,
		box,
		[
			Vector2(27.0, 28.0),
			Vector2(35.0, 18.0),
			Vector2(56.0, 18.0),
			Vector2(65.0, 29.0),
			Vector2(63.0, 46.0),
			Vector2(56.0, 58.0),
			Vector2(40.0, 60.0),
			Vector2(30.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 30.0),
			Vector2(38.0, 24.0),
			Vector2(54.0, 24.0),
			Vector2(59.0, 31.0),
			Vector2(58.0, 44.0),
			Vector2(52.0, 54.0),
			Vector2(42.0, 54.0),
			Vector2(36.0, 46.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(51.0, 26.0),
			Vector2(58.0, 31.0),
			Vector2(58.0, 43.0),
			Vector2(52.0, 52.0),
			Vector2(48.0, 49.0)
		],
		shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 31.0),
			Vector2(28.0, 24.0),
			Vector2(36.0, 18.0),
			Vector2(46.0, 13.0),
			Vector2(56.0, 18.0),
			Vector2(64.0, 25.0),
			Vector2(64.0, 33.0),
			Vector2(56.0, 29.0),
			Vector2(38.0, 29.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 27.0),
			Vector2(38.0, 22.0),
			Vector2(46.0, 18.0),
			Vector2(55.0, 22.0),
			Vector2(61.0, 28.0),
			Vector2(55.0, 26.0),
			Vector2(46.0, 22.0),
			Vector2(38.0, 26.0)
		],
		bronze
	)
	_fill(
		canvas,
		box,
		[
			Vector2(43.0, 18.0),
			Vector2(46.0, 8.0),
			Vector2(50.0, 18.0),
			Vector2(48.0, 26.0),
			Vector2(45.0, 26.0)
		],
		gold
	)
	canvas.draw_line(_p(box, 30.0, 25.0), _p(box, 23.0, 17.0), coral, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 23.0, 17.0), _p(box, 23.0, 11.0), coral, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 25.0, 20.0), _p(box, 19.0, 19.0), coral, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 61.0, 25.0), _p(box, 69.0, 17.0), coral, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 69.0, 17.0), _p(box, 70.0, 10.0), coral, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 67.0, 20.0), _p(box, 75.0, 19.0), coral, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 36.0, 35.0), _p(box, 43.0, 36.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 50.0, 36.0), _p(box, 57.0, 34.0), ink, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 37.0, 39.0), _p(box, 42.0, 39.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 39.0), _p(box, 56.0, 38.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 47.0, 37.0), _p(box, 45.0, 44.0), skin, maxf(1.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 43.0),
			Vector2(40.0, 46.0),
			Vector2(46.0, 44.0),
			Vector2(53.0, 46.0),
			Vector2(59.0, 42.0),
			Vector2(57.0, 53.0),
			Vector2(51.0, 63.0),
			Vector2(46.0, 59.0),
			Vector2(41.0, 64.0),
			Vector2(36.0, 54.0)
		],
		hair
	)
	canvas.draw_line(_p(box, 41.0, 50.0), _p(box, 51.0, 49.0), shade, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 41.0, 54.0), _p(box, 43.0, 59.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 54.0), _p(box, 50.0, 59.0), light, maxf(1.5 * unit, 1.0), true)

	# An anchor-sealed shield and a tall hooked trident complete the warden kit.
	_fill(
		canvas,
		box,
		[
			Vector2(7.0, 83.0),
			Vector2(19.0, 76.0),
			Vector2(33.0, 82.0),
			Vector2(31.0, 92.0),
			Vector2(22.0, 96.0),
			Vector2(10.0, 93.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 84.0),
			Vector2(20.0, 80.0),
			Vector2(28.0, 84.0),
			Vector2(27.0, 90.0),
			Vector2(22.0, 93.0),
			Vector2(14.0, 90.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 21.0, 83.0), _p(box, 21.0, 90.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 17.0, 88.0), _p(box, 21.0, 91.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 21.0, 91.0), _p(box, 25.0, 88.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 21.0, 83.0), 1.5 * unit, gold)
	canvas.draw_line(_p(box, 79.0, 39.0), _p(box, 76.0, 95.0), ink, maxf(6.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 79.0, 39.0), _p(box, 76.0, 95.0), bronze, maxf(2.5 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 16.0),
			Vector2(73.0, 20.0),
			Vector2(74.0, 30.0),
			Vector2(77.0, 32.0),
			Vector2(79.0, 10.0),
			Vector2(82.0, 7.0),
			Vector2(84.0, 31.0),
			Vector2(87.0, 28.0),
			Vector2(87.0, 18.0),
			Vector2(93.0, 14.0),
			Vector2(92.0, 33.0),
			Vector2(84.0, 42.0),
			Vector2(74.0, 41.0),
			Vector2(67.0, 33.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(70.0, 23.0),
			Vector2(72.0, 25.0),
			Vector2(73.0, 31.0),
			Vector2(77.0, 35.0),
			Vector2(75.0, 38.0),
			Vector2(70.0, 32.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[Vector2(81.0, 17.0), Vector2(83.0, 34.0), Vector2(80.0, 38.0), Vector2(78.0, 35.0)],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(90.0, 22.0),
			Vector2(89.0, 32.0),
			Vector2(83.0, 39.0),
			Vector2(80.0, 38.0),
			Vector2(85.0, 33.0),
			Vector2(88.0, 29.0)
		],
		steel
	)
	canvas.draw_line(_p(box, 81.0, 18.0), _p(box, 81.0, 31.0), light, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 74.0, 38.0), _p(box, 83.0, 38.0), sea, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 75.0, 80.0), 4.0 * unit, skin)
	canvas.draw_line(_p(box, 73.0, 83.0), _p(box, 78.0, 83.0), bronze, maxf(2.0 * unit, 1.0), true)


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
