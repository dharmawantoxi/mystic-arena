extends RefCounted
## Native canvas painter for Grondmauris, the True Boss/Earth Colossus.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(11, 15, 12)
	var stone_shadow := Color8(28, 34, 27)
	var stone := Color8(63, 74, 52)
	var stone_mid := Color8(98, 119, 70)
	var stone_light := Color8(147, 165, 96)
	var moss := Color8(70, 103, 50)
	var fissure := Color8(140, 190, 70)
	var glow := Color8(200, 255, 180)
	var deep_glow := Color8(64, 121, 45)

	_backdrop(canvas, box, Color8(69, 94, 54), Color8(15, 22, 18))
	canvas.draw_arc(
		_p(box, 48.0, 46.0),
		39.0 * unit,
		-PI * 0.88,
		-PI * 0.12,
		32,
		Color(fissure.r, fissure.g, fissure.b, 0.22),
		maxf(2.0 * unit, 1.0),
		true
	)
	canvas.draw_arc(
		_p(box, 48.0, 46.0),
		30.0 * unit,
		PI * 0.14,
		PI * 0.86,
		28,
		Color(glow.r, glow.g, glow.b, 0.12),
		maxf(1.4 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 13.0, 41.0), 1.7 * unit, stone_light)
	canvas.draw_circle(_p(box, 82.0, 38.0), 1.9 * unit, glow)
	canvas.draw_circle(_p(box, 17.0, 60.0), 1.3 * unit, fissure)
	canvas.draw_circle(_p(box, 78.0, 64.0), 1.6 * unit, stone_light)

	# A broken ring of floating shale frames the ancient colossus.
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 51.0),
			Vector2(5.0, 43.0),
			Vector2(10.0, 35.0),
			Vector2(17.0, 43.0),
			Vector2(26.0, 49.0),
			Vector2(25.0, 57.0),
		],
		stone_shadow
	)
	_fill(
		canvas,
		box,
		[
			Vector2(82.0, 50.0),
			Vector2(91.0, 42.0),
			Vector2(86.0, 34.0),
			Vector2(79.0, 43.0),
			Vector2(70.0, 49.0),
			Vector2(71.0, 57.0),
		],
		stone_shadow
	)
	_fill(
		canvas,
		box,
		[
			Vector2(19.0, 34.0),
			Vector2(14.0, 25.0),
			Vector2(23.0, 29.0),
		],
		stone_mid
	)
	_fill(
		canvas,
		box,
		[
			Vector2(77.0, 32.0),
			Vector2(84.0, 23.0),
			Vector2(82.0, 35.0),
		],
		stone_mid
	)

	# Broad shoulders and fractured basalt plates form the chest silhouette.
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 96.0),
			Vector2(13.0, 78.0),
			Vector2(20.0, 65.0),
			Vector2(31.0, 58.0),
			Vector2(65.0, 57.0),
			Vector2(77.0, 65.0),
			Vector2(84.0, 79.0),
			Vector2(88.0, 96.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 94.0),
			Vector2(19.0, 79.0),
			Vector2(25.0, 68.0),
			Vector2(34.0, 62.0),
			Vector2(62.0, 61.0),
			Vector2(72.0, 68.0),
			Vector2(78.0, 80.0),
			Vector2(82.0, 94.0),
		],
		stone_shadow
	)
	_fill(
		canvas,
		box,
		[
			Vector2(9.0, 73.0),
			Vector2(15.0, 61.0),
			Vector2(27.0, 56.0),
			Vector2(39.0, 64.0),
			Vector2(35.0, 81.0),
			Vector2(24.0, 87.0),
			Vector2(11.0, 83.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(14.0, 72.0),
			Vector2(19.0, 64.0),
			Vector2(27.0, 60.0),
			Vector2(34.0, 66.0),
			Vector2(31.0, 77.0),
			Vector2(24.0, 82.0),
			Vector2(16.0, 79.0),
		],
		stone_mid
	)
	_fill(
		canvas,
		box,
		[
			Vector2(57.0, 64.0),
			Vector2(69.0, 56.0),
			Vector2(82.0, 61.0),
			Vector2(88.0, 73.0),
			Vector2(85.0, 84.0),
			Vector2(72.0, 87.0),
			Vector2(61.0, 80.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(62.0, 66.0),
			Vector2(70.0, 60.0),
			Vector2(79.0, 64.0),
			Vector2(83.0, 72.0),
			Vector2(80.0, 79.0),
			Vector2(72.0, 82.0),
			Vector2(65.0, 77.0),
		],
		stone_mid
	)
	canvas.draw_line(
		_p(box, 18.0, 68.0), _p(box, 31.0, 70.0), stone_light, maxf(1.8 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 78.0, 68.0), _p(box, 65.0, 70.0), stone_light, maxf(1.8 * unit, 1.0), true
	)

	# Layered chest rocks cradle a radiant moss-green earthstone.
	_fill(
		canvas,
		box,
		[
			Vector2(30.0, 61.0),
			Vector2(39.0, 56.0),
			Vector2(57.0, 56.0),
			Vector2(66.0, 62.0),
			Vector2(70.0, 94.0),
			Vector2(26.0, 94.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 63.0),
			Vector2(41.0, 59.0),
			Vector2(55.0, 59.0),
			Vector2(61.0, 63.0),
			Vector2(64.0, 91.0),
			Vector2(32.0, 91.0),
		],
		stone
	)
	_fill(
		canvas,
		box,
		[
			Vector2(36.0, 63.0),
			Vector2(43.0, 60.0),
			Vector2(47.0, 66.0),
			Vector2(43.0, 73.0),
			Vector2(34.0, 75.0),
		],
		stone_mid
	)
	_fill(
		canvas,
		box,
		[
			Vector2(60.0, 64.0),
			Vector2(55.0, 60.0),
			Vector2(50.0, 66.0),
			Vector2(54.0, 74.0),
			Vector2(63.0, 76.0),
		],
		stone_light
	)

	# Moss and luminous fractures streak across the stone armor.
	canvas.draw_line(_p(box, 17.0, 76.0), _p(box, 24.0, 73.0), moss, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 74.0, 76.0), _p(box, 80.0, 79.0), moss, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 28.0, 83.0), _p(box, 35.0, 78.0), deep_glow, maxf(2.5 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 68.0, 84.0), _p(box, 61.0, 78.0), deep_glow, maxf(2.5 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 28.0, 83.0), _p(box, 35.0, 78.0), fissure, maxf(1.1 * unit, 1.0), true)
	canvas.draw_line(_p(box, 68.0, 84.0), _p(box, 61.0, 78.0), fissure, maxf(1.1 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 20.0, 69.0), 1.4 * unit, glow)
	canvas.draw_circle(_p(box, 76.0, 70.0), 1.4 * unit, glow)

	canvas.draw_circle(_p(box, 48.0, 78.0), 13.0 * unit, outline)
	canvas.draw_circle(_p(box, 48.0, 78.0), 10.0 * unit, stone_mid)
	canvas.draw_circle(_p(box, 48.0, 78.0), 6.4 * unit, deep_glow)
	canvas.draw_circle(_p(box, 48.0, 78.0), 3.6 * unit, fissure)
	canvas.draw_circle(_p(box, 48.0, 78.0), 1.5 * unit, glow)
	canvas.draw_arc(
		_p(box, 48.0, 78.0),
		11.0 * unit,
		-PI * 0.82,
		PI * 0.78,
		24,
		stone_light,
		maxf(1.2 * unit, 1.0),
		true
	)
	canvas.draw_line(_p(box, 39.0, 62.0), _p(box, 44.0, 68.0), fissure, maxf(1.3 * unit, 1.0), true)
	canvas.draw_line(_p(box, 57.0, 62.0), _p(box, 52.0, 68.0), fissure, maxf(1.3 * unit, 1.0), true)

	# A craggy head with basalt horns and deep-set green eyes.
	_fill(
		canvas,
		box,
		[
			Vector2(28.0, 35.0),
			Vector2(22.0, 23.0),
			Vector2(34.0, 27.0),
			Vector2(39.0, 17.0),
			Vector2(47.0, 23.0),
			Vector2(56.0, 15.0),
			Vector2(62.0, 27.0),
			Vector2(74.0, 22.0),
			Vector2(68.0, 38.0),
			Vector2(70.0, 47.0),
			Vector2(62.0, 58.0),
			Vector2(48.0, 63.0),
			Vector2(34.0, 58.0),
			Vector2(27.0, 48.0),
		],
		outline
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 36.0),
			Vector2(27.0, 27.0),
			Vector2(36.0, 31.0),
			Vector2(40.0, 22.0),
			Vector2(47.0, 28.0),
			Vector2(56.0, 20.0),
			Vector2(61.0, 31.0),
			Vector2(69.0, 27.0),
			Vector2(65.0, 39.0),
			Vector2(66.0, 46.0),
			Vector2(60.0, 54.0),
			Vector2(48.0, 59.0),
			Vector2(36.0, 54.0),
			Vector2(31.0, 46.0),
		],
		stone_mid
	)
	_fill(
		canvas,
		box,
		[
			Vector2(31.0, 36.0),
			Vector2(27.0, 27.0),
			Vector2(36.0, 31.0),
			Vector2(40.0, 22.0),
			Vector2(45.0, 29.0),
			Vector2(38.0, 37.0),
			Vector2(35.0, 50.0),
			Vector2(31.0, 46.0),
		],
		stone_light
	)
	_fill(
		canvas,
		box,
		[
			Vector2(56.0, 21.0),
			Vector2(61.0, 31.0),
			Vector2(69.0, 27.0),
			Vector2(65.0, 39.0),
			Vector2(60.0, 36.0),
		],
		stone
	)
	canvas.draw_line(_p(box, 25.0, 29.0), _p(box, 35.0, 34.0), outline, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 71.0, 29.0), _p(box, 61.0, 34.0), outline, maxf(2.0 * unit, 1.0), true)

	# Moss-dark sockets and emerald light define the colossus's gaze.
	canvas.draw_line(_p(box, 34.0, 39.0), _p(box, 44.0, 40.0), outline, maxf(3.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 40.0), _p(box, 62.0, 39.0), outline, maxf(3.2 * unit, 1.0), true)
	canvas.draw_line(_p(box, 36.0, 40.0), _p(box, 43.0, 40.0), fissure, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 53.0, 40.0), _p(box, 60.0, 39.0), fissure, maxf(2.0 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 39.0, 40.0), 1.1 * unit, glow)
	canvas.draw_circle(_p(box, 57.0, 39.0), 1.1 * unit, glow)
	canvas.draw_line(
		_p(box, 48.0, 40.0), _p(box, 46.0, 48.0), stone_shadow, maxf(2.2 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 40.0, 51.0), _p(box, 56.0, 51.0), outline, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 42.0, 53.0), _p(box, 54.0, 53.0), stone_light, maxf(1.1 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 35.0, 32.0), _p(box, 43.0, 35.0), stone_light, maxf(1.2 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 61.0, 32.0), _p(box, 54.0, 35.0), stone_light, maxf(1.2 * unit, 1.0), true
	)

	# Bright fissures climb the brow and split the cheek plates.
	canvas.draw_line(
		_p(box, 48.0, 24.0), _p(box, 47.0, 31.0), deep_glow, maxf(3.0 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 48.0, 24.0), _p(box, 47.0, 31.0), glow, maxf(1.2 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 35.0, 44.0), _p(box, 39.0, 49.0), deep_glow, maxf(2.5 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 35.0, 44.0), _p(box, 39.0, 49.0), fissure, maxf(1.1 * unit, 1.0), true)
	canvas.draw_line(
		_p(box, 61.0, 44.0), _p(box, 57.0, 49.0), deep_glow, maxf(2.5 * unit, 1.0), true
	)
	canvas.draw_line(_p(box, 61.0, 44.0), _p(box, 57.0, 49.0), fissure, maxf(1.1 * unit, 1.0), true)
	canvas.draw_circle(_p(box, 34.0, 59.0), 1.5 * unit, moss)
	canvas.draw_circle(_p(box, 62.0, 59.0), 1.5 * unit, moss)
	canvas.draw_circle(_p(box, 48.0, 61.0), 2.0 * unit, glow)


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
