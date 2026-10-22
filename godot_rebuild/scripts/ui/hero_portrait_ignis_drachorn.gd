extends RefCounted
## Native canvas painter for Ignis Drachorn, the True Boss/Dragon Knight.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(19, 11, 18)
	var shadow := Color8(47, 19, 25)
	var armor := Color8(70, 28, 35)
	var armor_light := Color8(126, 39, 37)
	var scale_red := Color8(171, 53, 39)
	var steel := Color8(145, 143, 146)
	var steel_light := Color8(219, 198, 160)
	var horn := Color8(221, 187, 127)
	var gold := Color8(237, 151, 51)
	var ember := Color8(244, 76, 29)
	var hot := Color8(255, 190, 64)
	var core := Color8(255, 225, 124)

	_backdrop(canvas, box, Color8(130, 47, 27), Color8(17, 12, 20))
	canvas.draw_arc(
		_p(box, 48.0, 47.0),
		39.0 * unit,
		-PI * 0.88,
		-PI * 0.12,
		32,
		Color(ember.r, ember.g, ember.b, 0.30),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 47.0),
		31.0 * unit,
		PI * 0.14,
		PI * 0.86,
		28,
		Color(hot.r, hot.g, hot.b, 0.17),
		maxf(1.5 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 13.0, 35.0), 2.0 * unit, hot)
	canvas.draw_circle(_p(box, 81.0, 34.0), 2.2 * unit, ember)
	canvas.draw_circle(_p(box, 17.0, 57.0), 1.5 * unit, gold)
	canvas.draw_circle(_p(box, 78.0, 63.0), 1.8 * unit, hot)

	# A blackened greatsword with a molten fuller rises behind the right pauldron.
	_fill(
		canvas,
		box,
		[
			Vector2(73.0, 60.0),
			Vector2(78.0, 43.0),
			Vector2(84.0, 28.0),
			Vector2(91.0, 18.0),
			Vector2(90.0, 35.0),
			Vector2(86.0, 53.0),
			Vector2(79.0, 66.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 56.0),
			Vector2(81.0, 42.0),
			Vector2(87.0, 28.0),
			Vector2(88.0, 25.0),
			Vector2(87.0, 39.0),
			Vector2(83.0, 53.0),
			Vector2(79.0, 60.0),
		],
		steel
	)
	canvas.draw_line(_p(box, 81.0, 42.0), _p(box, 86.0, 31.0), ember, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 75.0, 56.0), _p(box, 84.0, 60.0), outline, maxf(5.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 76.0, 56.0), _p(box, 83.0, 59.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 78.0, 59.0), _p(box, 67.0, 79.0), outline, maxf(4.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 78.0, 59.0), _p(box, 68.0, 77.0), steel_light, maxf(1.6 * unit, 1.0), true
	)

	# A ragged fire-wyrm mantle frames the armored silhouette.
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 53.0),
			Vector2(18.0, 39.0),
			Vector2(9.0, 38.0),
			Vector2(14.0, 48.0),
			Vector2(6.0, 47.0),
			Vector2(15.0, 59.0),
			Vector2(10.0, 70.0),
			Vector2(27.0, 69.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(26.0, 55.0),
			Vector2(18.0, 45.0),
			Vector2(13.0, 43.0),
			Vector2(19.0, 53.0),
			Vector2(12.0, 52.0),
			Vector2(22.0, 62.0),
			Vector2(18.0, 66.0),
			Vector2(28.0, 65.0),
		],
		armor_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(66.0, 53.0),
			Vector2(78.0, 39.0),
			Vector2(87.0, 38.0),
			Vector2(82.0, 48.0),
			Vector2(90.0, 47.0),
			Vector2(81.0, 59.0),
			Vector2(86.0, 70.0),
			Vector2(69.0, 69.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(70.0, 55.0),
			Vector2(79.0, 45.0),
			Vector2(84.0, 43.0),
			Vector2(78.0, 53.0),
			Vector2(85.0, 52.0),
			Vector2(75.0, 62.0),
			Vector2(78.0, 67.0),
			Vector2(68.0, 65.0),
		],
		armor_light
	)

	# Heavy plates and raised pauldrons carry the molten sovereign's colors.
	_fill(
		canvas,
		box,
		[
			Vector2(8.0, 96.0),
			Vector2(12.0, 77.0),
			Vector2(21.0, 65.0),
			Vector2(34.0, 58.0),
			Vector2(60.0, 58.0),
			Vector2(75.0, 65.0),
			Vector2(85.0, 78.0),
			Vector2(89.0, 96.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 94.0),
			Vector2(19.0, 79.0),
			Vector2(29.0, 69.0),
			Vector2(41.0, 64.0),
			Vector2(56.0, 64.0),
			Vector2(68.0, 70.0),
			Vector2(78.0, 81.0),
			Vector2(81.0, 94.0),
		],
		armor
	)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 69.0),
			Vector2(12.0, 59.0),
			Vector2(20.0, 60.0),
			Vector2(22.0, 51.0),
			Vector2(29.0, 59.0),
			Vector2(38.0, 62.0),
			Vector2(36.0, 76.0),
			Vector2(25.0, 84.0),
			Vector2(13.0, 81.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 69.0),
			Vector2(16.0, 63.0),
			Vector2(21.0, 65.0),
			Vector2(23.0, 57.0),
			Vector2(28.0, 64.0),
			Vector2(34.0, 66.0),
			Vector2(32.0, 75.0),
			Vector2(24.0, 80.0),
			Vector2(16.0, 78.0),
		],
		armor_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(58.0, 62.0),
			Vector2(68.0, 58.0),
			Vector2(76.0, 51.0),
			Vector2(79.0, 61.0),
			Vector2(88.0, 60.0),
			Vector2(83.0, 71.0),
			Vector2(85.0, 82.0),
			Vector2(72.0, 85.0),
			Vector2(61.0, 78.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(63.0, 65.0),
			Vector2(70.0, 62.0),
			Vector2(76.0, 57.0),
			Vector2(78.0, 65.0),
			Vector2(83.0, 64.0),
			Vector2(80.0, 72.0),
			Vector2(81.0, 78.0),
			Vector2(72.0, 81.0),
			Vector2(64.0, 75.0),
		],
		armor_light
	)
	canvas.draw_line(_p(box, 17.0, 70.0), _p(box, 31.0, 68.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 66.0, 68.0), _p(box, 80.0, 67.0), gold, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 25.0, 73.0), 2.0 * unit, hot)
	canvas.draw_circle(_p(box, 73.0, 72.0), 2.0 * unit, hot)

	# A split red tabard and the glowing heart sit beneath the dragon helm.
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 57.0),
			Vector2(48.0, 63.0),
			Vector2(61.0, 57.0),
			Vector2(68.0, 93.0),
			Vector2(53.0, 96.0),
			Vector2(48.0, 76.0),
			Vector2(42.0, 96.0),
			Vector2(28.0, 93.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(38.0, 61.0),
			Vector2(48.0, 66.0),
			Vector2(58.0, 61.0),
			Vector2(62.0, 91.0),
			Vector2(53.0, 94.0),
			Vector2(48.0, 75.0),
			Vector2(43.0, 94.0),
			Vector2(34.0, 91.0),
		],
		scale_red
	)
	canvas.draw_line(_p(box, 35.0, 68.0), _p(box, 43.0, 79.0), gold, maxf(1.8 * unit, 1.0), true)
	canvas.draw_line(_p(box, 61.0, 68.0), _p(box, 54.0, 79.0), gold, maxf(1.8 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 48.0, 74.0), 9.0 * unit, outline)
	canvas.draw_circle(_p(box, 48.0, 74.0), 6.0 * unit, ember)
	canvas.draw_circle(_p(box, 48.0, 74.0), 3.0 * unit, core)
	canvas.draw_line(_p(box, 48.0, 83.0), _p(box, 48.0, 92.0), gold, maxf(2.0 * unit, 1.0), true)

	# Curved horns and a flame crest frame the dragon-shaped helm.
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 28.0),
			Vector2(29.0, 18.0),
			Vector2(20.0, 7.0),
			Vector2(22.0, 19.0),
			Vector2(15.0, 16.0),
			Vector2(20.0, 26.0),
			Vector2(29.0, 34.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 27.0),
			Vector2(31.0, 19.0),
			Vector2(23.0, 11.0),
			Vector2(26.0, 22.0),
			Vector2(20.0, 20.0),
			Vector2(24.0, 27.0),
			Vector2(31.0, 31.0),
		],
		horn
	)
	_fill(
		canvas,
		box,
		[
			Vector2(61.0, 28.0),
			Vector2(67.0, 18.0),
			Vector2(76.0, 7.0),
			Vector2(74.0, 19.0),
			Vector2(81.0, 16.0),
			Vector2(76.0, 26.0),
			Vector2(67.0, 34.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(59.0, 27.0),
			Vector2(65.0, 19.0),
			Vector2(73.0, 11.0),
			Vector2(70.0, 22.0),
			Vector2(76.0, 20.0),
			Vector2(72.0, 27.0),
			Vector2(65.0, 31.0),
		],
		horn
	)

	# The armored brow, snout, and eye slits are built as bold readable planes.
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 34.0),
			Vector2(31.0, 26.0),
			Vector2(39.0, 20.0),
			Vector2(49.0, 18.0),
			Vector2(59.0, 22.0),
			Vector2(66.0, 31.0),
			Vector2(68.0, 41.0),
			Vector2(63.0, 51.0),
			Vector2(55.0, 57.0),
			Vector2(48.0, 60.0),
			Vector2(40.0, 56.0),
			Vector2(32.0, 50.0),
			Vector2(28.0, 42.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(33.0, 34.0),
			Vector2(35.0, 29.0),
			Vector2(41.0, 24.0),
			Vector2(49.0, 22.0),
			Vector2(57.0, 25.0),
			Vector2(62.0, 32.0),
			Vector2(64.0, 40.0),
			Vector2(60.0, 47.0),
			Vector2(54.0, 52.0),
			Vector2(48.0, 55.0),
			Vector2(42.0, 52.0),
			Vector2(36.0, 47.0),
			Vector2(33.0, 40.0),
		],
		armor_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 35.0),
			Vector2(42.0, 31.0),
			Vector2(48.0, 34.0),
			Vector2(47.0, 39.0),
			Vector2(40.0, 38.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 34.0),
			Vector2(56.0, 31.0),
			Vector2(63.0, 35.0),
			Vector2(57.0, 38.0),
			Vector2(50.0, 39.0),
		],
		outline
	)
	canvas.draw_line(_p(box, 38.0, 36.0), _p(box, 43.0, 36.0), hot, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 54.0, 36.0), _p(box, 59.0, 36.0), hot, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 41.0, 36.0), 1.2 * unit, core)
	canvas.draw_circle(_p(box, 56.0, 36.0), 1.2 * unit, core)
	_fill(
		canvas,
		box,
		[
			Vector2(37.0, 40.0),
			Vector2(45.0, 39.0),
			Vector2(49.0, 42.0),
			Vector2(55.0, 39.0),
			Vector2(61.0, 42.0),
			Vector2(57.0, 48.0),
			Vector2(49.0, 51.0),
			Vector2(41.0, 48.0),
		],
		shadow
	)
	canvas.draw_line(_p(box, 44.0, 46.0), _p(box, 54.0, 46.0), ember, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 46.0, 48.0), _p(box, 52.0, 48.0), hot, maxf(1.2 * unit, 1.0), true)

	# Crown ridges and scale marks give the helm its dragon silhouette.
	_fill(
		canvas,
		box,
		[
			Vector2(40.0, 24.0),
			Vector2(43.0, 13.0),
			Vector2(48.0, 4.0),
			Vector2(52.0, 14.0),
			Vector2(58.0, 9.0),
			Vector2(56.0, 23.0),
			Vector2(49.0, 28.0),
		],
		gold
	)
	_fill(
		canvas,
		box,
		[
			Vector2(45.0, 19.0),
			Vector2(48.0, 10.0),
			Vector2(51.0, 19.0),
			Vector2(49.0, 24.0),
		],
		core
	)
	canvas.draw_line(
		_p(box, 34.0, 29.0), _p(box, 40.0, 25.0), steel_light, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 57.0, 25.0), _p(box, 63.0, 30.0), steel_light, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 35.0, 45.0), _p(box, 40.0, 48.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 61.0, 44.0), _p(box, 56.0, 48.0), gold, maxf(1.5 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 33.0, 54.0), 1.5 * unit, ember)
	canvas.draw_circle(_p(box, 64.0, 54.0), 1.5 * unit, ember)


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
