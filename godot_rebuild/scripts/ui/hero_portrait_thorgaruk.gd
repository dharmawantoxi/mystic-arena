extends RefCounted
## Native canvas portrait: Thorgaruk, The Skyhorn Warrior.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(25, 31, 43)
	var skin := Color8(91, 125, 140)
	var skin_shade := Color8(57, 82, 103)
	var armor := Color8(74, 96, 116)
	var steel := Color8(154, 181, 190)
	var gold := Color8(205, 162, 80)
	var ivory := Color8(224, 222, 186)
	var fur := Color8(177, 195, 194)
	var sky := Color8(99, 195, 218)
	var light := Color8(230, 250, 230)
	var leather := Color8(72, 57, 52)
	_backdrop(canvas, box, Color8(67, 121, 150), Color8(27, 38, 56))

	# Storm clouds and angular lightning sit behind the enormous skyward horns.
	canvas.draw_circle(_p(box, 14.0, 37.0), 11.0 * unit, armor)
	canvas.draw_circle(_p(box, 25.0, 39.0), 9.0 * unit, armor)
	canvas.draw_circle(_p(box, 82.0, 43.0), 12.0 * unit, armor)
	canvas.draw_line(_p(box, 13.0, 19.0), _p(box, 18.0, 28.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 18.0, 28.0), _p(box, 14.0, 34.0), sky, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 14.0, 34.0), _p(box, 21.0, 43.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 80.0, 17.0), _p(box, 75.0, 27.0), sky, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 75.0, 27.0), _p(box, 79.0, 33.0), light, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 31.0),
			Vector2(21.0, 28.0),
			Vector2(10.0, 19.0),
			Vector2(8.0, 6.0),
			Vector2(16.0, 13.0),
			Vector2(27.0, 16.0),
			Vector2(39.0, 21.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(32.0, 26.0),
			Vector2(22.0, 23.0),
			Vector2(14.0, 17.0),
			Vector2(12.0, 12.0),
			Vector2(18.0, 17.0),
			Vector2(28.0, 20.0),
			Vector2(36.0, 23.0)
		],
		ivory
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 21.0),
			Vector2(74.0, 16.0),
			Vector2(85.0, 12.0),
			Vector2(90.0, 5.0),
			Vector2(88.0, 19.0),
			Vector2(77.0, 28.0),
			Vector2(63.0, 31.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(65.0, 23.0),
			Vector2(75.0, 20.0),
			Vector2(83.0, 16.0),
			Vector2(86.0, 12.0),
			Vector2(84.0, 19.0),
			Vector2(75.0, 24.0),
			Vector2(65.0, 27.0)
		],
		ivory
	)
	canvas.draw_line(_p(box, 18.0, 19.0), _p(box, 22.0, 23.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 20.0), _p(box, 82.0, 17.0), gold, maxf(2.0 * unit, 1.0), true)

	# A cloud-fur mantle wraps a broad breastplate with a stormbird chevron.
	_fill(
		canvas,
		box,
		[
			Vector2(4.0, 96.0),
			Vector2(10.0, 72.0),
			Vector2(28.0, 55.0),
			Vector2(65.0, 55.0),
			Vector2(85.0, 71.0),
			Vector2(93.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(11.0, 94.0),
			Vector2(17.0, 74.0),
			Vector2(31.0, 62.0),
			Vector2(61.0, 62.0),
			Vector2(78.0, 74.0),
			Vector2(86.0, 94.0)
		],
		leather
	)
	canvas.draw_circle(_p(box, 19.0, 66.0), 13.0 * unit, fur)
	canvas.draw_circle(_p(box, 30.0, 61.0), 11.0 * unit, fur)
	canvas.draw_circle(_p(box, 66.0, 61.0), 11.0 * unit, fur)
	canvas.draw_circle(_p(box, 77.0, 67.0), 13.0 * unit, fur)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 64.0),
			Vector2(43.0, 58.0),
			Vector2(58.0, 64.0),
			Vector2(66.0, 94.0),
			Vector2(26.0, 94.0)
		],
		armor
	)
	_fill(
		canvas,
		box,
		[Vector2(48.0, 61.0), Vector2(58.0, 66.0), Vector2(62.0, 94.0), Vector2(48.0, 94.0)],
		skin_shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 68.0),
			Vector2(46.0, 76.0),
			Vector2(62.0, 67.0),
			Vector2(57.0, 80.0),
			Vector2(47.0, 87.0),
			Vector2(36.0, 80.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 71.0),
			Vector2(46.0, 78.0),
			Vector2(57.0, 71.0),
			Vector2(53.0, 78.0),
			Vector2(47.0, 82.0),
			Vector2(40.0, 78.0)
		],
		gold
	)
	_fill(canvas, box, [Vector2(44.0, 75.0), Vector2(49.0, 75.0), Vector2(47.0, 84.0)], sky)
	canvas.draw_line(_p(box, 34.0, 88.0), _p(box, 42.0, 92.0), steel, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 92.0), _p(box, 60.0, 87.0), gold, maxf(2.0 * unit, 1.0), true)

	# The blue-grey face has a blunt muzzle, stern eyes and a braided storm beard.
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 31.0),
			Vector2(36.0, 21.0),
			Vector2(56.0, 20.0),
			Vector2(65.0, 30.0),
			Vector2(64.0, 48.0),
			Vector2(56.0, 60.0),
			Vector2(39.0, 60.0),
			Vector2(30.0, 48.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 32.0),
			Vector2(40.0, 26.0),
			Vector2(54.0, 25.0),
			Vector2(60.0, 31.0),
			Vector2(59.0, 45.0),
			Vector2(53.0, 54.0),
			Vector2(41.0, 55.0),
			Vector2(35.0, 46.0)
		],
		skin
	)
	_fill(
		canvas,
		box,
		[
			Vector2(52.0, 26.0),
			Vector2(59.0, 31.0),
			Vector2(60.0, 38.0),
			Vector2(56.0, 48.0),
			Vector2(51.0, 53.0),
			Vector2(48.0, 48.0)
		],
		skin_shade
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 31.0),
			Vector2(37.0, 22.0),
			Vector2(47.0, 18.0),
			Vector2(58.0, 22.0),
			Vector2(64.0, 31.0),
			Vector2(55.0, 28.0),
			Vector2(47.0, 30.0),
			Vector2(38.0, 27.0)
		],
		gold
	)
	canvas.draw_circle(_p(box, 47.0, 24.0), 3.0 * unit, sky)
	canvas.draw_circle(_p(box, 47.0, 24.0), 1.2 * unit, light)
	canvas.draw_line(_p(box, 35.0, 35.0), _p(box, 43.0, 37.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 51.0, 37.0), _p(box, 59.0, 34.0), ink, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 38.0, 39.0), _p(box, 43.0, 39.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 39.0), _p(box, 57.0, 38.0), sky, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(41.0, 40.0),
			Vector2(47.0, 37.0),
			Vector2(53.0, 40.0),
			Vector2(55.0, 47.0),
			Vector2(48.0, 50.0),
			Vector2(40.0, 47.0)
		],
		skin_shade
	)
	canvas.draw_line(_p(box, 43.0, 45.0), _p(box, 51.0, 45.0), ink, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 49.0),
			Vector2(43.0, 53.0),
			Vector2(52.0, 51.0),
			Vector2(59.0, 48.0),
			Vector2(56.0, 63.0),
			Vector2(50.0, 78.0),
			Vector2(44.0, 70.0),
			Vector2(38.0, 62.0)
		],
		fur
	)
	_fill(
		canvas,
		box,
		[
			Vector2(43.0, 55.0),
			Vector2(49.0, 57.0),
			Vector2(54.0, 54.0),
			Vector2(52.0, 66.0),
			Vector2(49.0, 72.0),
			Vector2(46.0, 65.0)
		],
		ivory
	)
	canvas.draw_line(_p(box, 42.0, 60.0), _p(box, 54.0, 61.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 45.0, 68.0), _p(box, 51.0, 69.0), gold, maxf(2.0 * unit, 1.0), true)

	# A compact storm hammer and wrapped grip establish the melee silhouette.
	canvas.draw_line(_p(box, 78.0, 46.0), _p(box, 75.0, 96.0), ink, maxf(8.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 46.0), _p(box, 75.0, 96.0), leather, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 40.0),
			Vector2(74.0, 32.0),
			Vector2(90.0, 35.0),
			Vector2(94.0, 45.0),
			Vector2(88.0, 53.0),
			Vector2(73.0, 52.0),
			Vector2(67.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 41.0),
			Vector2(77.0, 37.0),
			Vector2(87.0, 39.0),
			Vector2(89.0, 45.0),
			Vector2(85.0, 48.0),
			Vector2(75.0, 47.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(79.0, 38.0),
			Vector2(83.0, 39.0),
			Vector2(80.0, 43.0),
			Vector2(84.0, 44.0),
			Vector2(78.0, 47.0)
		],
		sky
	)
	canvas.draw_line(_p(box, 73.0, 76.0), _p(box, 79.0, 76.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 73.0, 83.0), _p(box, 78.0, 83.0), gold, maxf(2.0 * unit, 1.0), true)


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
