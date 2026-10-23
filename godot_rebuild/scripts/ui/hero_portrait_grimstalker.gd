extends RefCounted
## Native canvas portrait: Grimstalker, The Chembeast of the Depths / Toxic Werewolf.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(23, 32, 35)
	var fur := Color8(63, 88, 89)
	var shade := Color8(37, 58, 65)
	var light := Color8(159, 183, 163)
	var muzzle := Color8(119, 141, 130)
	var toxic := Color8(169, 231, 82)
	var core := Color8(225, 255, 142)
	var steel := Color8(104, 127, 131)
	var rust := Color8(125, 89, 58)
	var bone := Color8(221, 219, 172)
	var vial := Color8(69, 113, 76)
	_backdrop(canvas, box, Color8(49, 80, 58), Color8(18, 29, 36))

	# Toxic vapor curls and a chemical reservoir frame a hunched werewolf.
	canvas.draw_arc(
		_p(box, 15.0, 33.0), 9.0 * unit, PI * -0.5, PI * 0.9, 40, vial, maxf(4.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 16.0, 32.0), 7.0 * unit, PI * -0.5, PI * 0.8, 40, toxic, maxf(1.5 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 81.0, 27.0), 8.0 * unit, PI * 0.2, PI * 1.7, 40, vial, maxf(4.0 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 10.0, 19.0), 1.5 * unit, toxic)
	canvas.draw_circle(_p(box, 84.0, 43.0), 1.2 * unit, core)
	_fill(
		canvas,
		box,
		[
			Vector2(7.0, 96.0),
			Vector2(8.0, 66.0),
			Vector2(22.0, 51.0),
			Vector2(34.0, 55.0),
			Vector2(44.0, 48.0),
			Vector2(62.0, 52.0),
			Vector2(83.0, 66.0),
			Vector2(92.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(13.0, 94.0),
			Vector2(14.0, 69.0),
			Vector2(25.0, 57.0),
			Vector2(35.0, 61.0),
			Vector2(45.0, 54.0),
			Vector2(60.0, 58.0),
			Vector2(77.0, 70.0),
			Vector2(85.0, 94.0)
		],
		fur
	)
	_fill(
		canvas,
		box,
		[
			Vector2(49.0, 56.0),
			Vector2(62.0, 60.0),
			Vector2(77.0, 73.0),
			Vector2(83.0, 94.0),
			Vector2(50.0, 94.0)
		],
		shade
	)

	# Ragged fur, strapped chemical tanks and a glowing collar replace armour.
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 59.0),
			Vector2(19.0, 54.0),
			Vector2(25.0, 59.0),
			Vector2(25.0, 78.0),
			Vector2(16.0, 80.0),
			Vector2(11.0, 74.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(15.0, 61.0),
			Vector2(19.0, 58.0),
			Vector2(22.0, 61.0),
			Vector2(22.0, 73.0),
			Vector2(17.0, 76.0),
			Vector2(15.0, 72.0)
		],
		vial
	)
	_fill(
		canvas,
		box,
		[
			Vector2(16.0, 65.0),
			Vector2(21.0, 64.0),
			Vector2(21.0, 72.0),
			Vector2(17.0, 74.0),
			Vector2(16.0, 72.0)
		],
		toxic
	)
	canvas.draw_line(_p(box, 13.0, 61.0), _p(box, 23.0, 60.0), rust, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 14.0, 74.0), _p(box, 23.0, 73.0), rust, maxf(3.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(69.0, 58.0),
			Vector2(77.0, 55.0),
			Vector2(84.0, 61.0),
			Vector2(83.0, 77.0),
			Vector2(74.0, 80.0),
			Vector2(68.0, 72.0)
		],
		steel
	)
	_fill(
		canvas,
		box,
		[
			Vector2(72.0, 61.0),
			Vector2(77.0, 59.0),
			Vector2(80.0, 63.0),
			Vector2(79.0, 73.0),
			Vector2(74.0, 76.0),
			Vector2(72.0, 71.0)
		],
		vial
	)
	_fill(
		canvas,
		box,
		[
			Vector2(73.0, 65.0),
			Vector2(79.0, 65.0),
			Vector2(78.0, 72.0),
			Vector2(75.0, 74.0),
			Vector2(73.0, 70.0)
		],
		toxic
	)
	canvas.draw_line(_p(box, 71.0, 62.0), _p(box, 81.0, 63.0), rust, maxf(3.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 72.0, 73.0), _p(box, 80.0, 75.0), rust, maxf(3.0 * unit, 1.0), true)
	canvas.draw_arc(
		_p(box, 47.0, 54.0),
		17.0 * unit,
		PI * 0.05,
		PI * 0.95,
		40,
		steel,
		maxf(4.0 * unit, 1.0),
		true
	)
	canvas.draw_circle(_p(box, 47.0, 72.0), 6.0 * unit, ink)
	canvas.draw_circle(_p(box, 47.0, 72.0), 4.0 * unit, toxic)
	canvas.draw_circle(_p(box, 47.0, 72.0), 1.8 * unit, core)
	canvas.draw_line(_p(box, 32.0, 73.0), _p(box, 58.0, 94.0), rust, maxf(5.0 * unit, 1.0), true)

	# Tall wolf ears, angular brow, a long muzzle and exposed fangs define the head.
	_fill(
		canvas,
		box,
		[
			Vector2(24.0, 36.0),
			Vector2(21.0, 12.0),
			Vector2(34.0, 20.0),
			Vector2(42.0, 18.0),
			Vector2(53.0, 18.0),
			Vector2(66.0, 10.0),
			Vector2(68.0, 34.0),
			Vector2(73.0, 41.0),
			Vector2(65.0, 54.0),
			Vector2(58.0, 63.0),
			Vector2(39.0, 64.0),
			Vector2(28.0, 54.0),
			Vector2(22.0, 46.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(29.0, 35.0),
			Vector2(26.0, 20.0),
			Vector2(34.0, 26.0),
			Vector2(42.0, 23.0),
			Vector2(53.0, 23.0),
			Vector2(62.0, 19.0),
			Vector2(63.0, 35.0),
			Vector2(67.0, 42.0),
			Vector2(61.0, 52.0),
			Vector2(55.0, 58.0),
			Vector2(41.0, 59.0),
			Vector2(32.0, 51.0),
			Vector2(27.0, 44.0)
		],
		fur
	)
	_fill(
		canvas,
		box,
		[
			Vector2(50.0, 25.0),
			Vector2(59.0, 24.0),
			Vector2(63.0, 36.0),
			Vector2(66.0, 42.0),
			Vector2(59.0, 52.0),
			Vector2(53.0, 56.0),
			Vector2(48.0, 49.0)
		],
		shade
	)
	_fill(canvas, box, [Vector2(26.0, 19.0), Vector2(30.0, 32.0), Vector2(34.0, 29.0)], muzzle)
	_fill(canvas, box, [Vector2(61.0, 18.0), Vector2(57.0, 29.0), Vector2(62.0, 32.0)], muzzle)
	_fill(
		canvas,
		box,
		[Vector2(31.0, 32.0), Vector2(38.0, 28.0), Vector2(43.0, 31.0), Vector2(39.0, 35.0)],
		light
	)
	_fill(
		canvas,
		box,
		[Vector2(50.0, 31.0), Vector2(56.0, 27.0), Vector2(61.0, 31.0), Vector2(56.0, 35.0)],
		fur
	)
	_fill(
		canvas,
		box,
		[Vector2(29.0, 36.0), Vector2(41.0, 35.0), Vector2(45.0, 43.0), Vector2(34.0, 43.0)],
		ink
	)
	_fill(
		canvas,
		box,
		[Vector2(49.0, 36.0), Vector2(63.0, 35.0), Vector2(58.0, 43.0), Vector2(49.0, 43.0)],
		ink
	)
	canvas.draw_line(_p(box, 33.0, 39.0), _p(box, 40.0, 40.0), toxic, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 52.0, 40.0), _p(box, 58.0, 38.0), core, maxf(2.0 * unit, 1.0), true)
	_fill(
		canvas,
		box,
		[
			Vector2(39.0, 43.0),
			Vector2(48.0, 39.0),
			Vector2(57.0, 44.0),
			Vector2(61.0, 51.0),
			Vector2(54.0, 58.0),
			Vector2(41.0, 58.0),
			Vector2(34.0, 51.0)
		],
		muzzle
	)
	_fill(
		canvas,
		box,
		[
			Vector2(43.0, 43.0),
			Vector2(50.0, 42.0),
			Vector2(54.0, 46.0),
			Vector2(48.0, 49.0),
			Vector2(42.0, 47.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 51.0),
			Vector2(44.0, 53.0),
			Vector2(52.0, 52.0),
			Vector2(60.0, 48.0),
			Vector2(57.0, 57.0),
			Vector2(50.0, 62.0),
			Vector2(40.0, 59.0)
		],
		ink
	)
	_fill(canvas, box, [Vector2(37.0, 52.0), Vector2(42.0, 53.0), Vector2(41.0, 58.0)], bone)
	_fill(canvas, box, [Vector2(53.0, 53.0), Vector2(58.0, 50.0), Vector2(55.0, 58.0)], bone)
	_fill(canvas, box, [Vector2(45.0, 60.0), Vector2(47.0, 55.0), Vector2(49.0, 61.0)], bone)
	canvas.draw_line(_p(box, 31.0, 45.0), _p(box, 33.0, 49.0), toxic, maxf(1.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 60.0, 45.0), _p(box, 59.0, 49.0), toxic, maxf(1.0 * unit, 1.0), true)

	# Long clawed hands and leaking hoses emphasize the chembeast rather than a human hunter.
	_fill(
		canvas,
		box,
		[
			Vector2(7.0, 82.0),
			Vector2(18.0, 77.0),
			Vector2(30.0, 83.0),
			Vector2(34.0, 93.0),
			Vector2(28.0, 96.0),
			Vector2(5.0, 96.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(12.0, 85.0),
			Vector2(19.0, 82.0),
			Vector2(26.0, 86.0),
			Vector2(28.0, 92.0),
			Vector2(25.0, 93.0),
			Vector2(11.0, 93.0)
		],
		fur
	)
	_fill(
		canvas,
		box,
		[
			Vector2(67.0, 83.0),
			Vector2(79.0, 77.0),
			Vector2(90.0, 83.0),
			Vector2(92.0, 96.0),
			Vector2(66.0, 96.0),
			Vector2(61.0, 92.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(68.0, 86.0),
			Vector2(79.0, 82.0),
			Vector2(85.0, 86.0),
			Vector2(87.0, 93.0),
			Vector2(69.0, 93.0),
			Vector2(66.0, 91.0)
		],
		fur
	)
	_fill(
		canvas,
		box,
		[Vector2(12.0, 87.0), Vector2(16.0, 86.0), Vector2(17.0, 93.0), Vector2(14.0, 96.0)],
		bone
	)
	_fill(
		canvas,
		box,
		[Vector2(19.0, 87.0), Vector2(23.0, 86.0), Vector2(24.0, 93.0), Vector2(21.0, 96.0)],
		bone
	)
	_fill(
		canvas,
		box,
		[Vector2(73.0, 87.0), Vector2(77.0, 86.0), Vector2(78.0, 93.0), Vector2(75.0, 96.0)],
		bone
	)
	_fill(
		canvas,
		box,
		[Vector2(80.0, 87.0), Vector2(84.0, 86.0), Vector2(85.0, 93.0), Vector2(82.0, 96.0)],
		bone
	)
	canvas.draw_arc(
		_p(box, 27.0, 78.0), 8.0 * unit, PI * 0.4, PI * 1.7, 40, steel, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_arc(
		_p(box, 66.0, 80.0), 8.0 * unit, PI * -0.7, PI * 0.6, 40, steel, maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_circle(_p(box, 30.0, 84.0), 1.5 * unit, toxic)
	canvas.draw_circle(_p(box, 65.0, 88.0), 1.3 * unit, toxic)
	canvas.draw_line(_p(box, 37.0, 81.0), _p(box, 42.0, 84.0), light, maxf(1.5 * unit, 1.0), true)
	canvas.draw_line(_p(box, 54.0, 84.0), _p(box, 60.0, 80.0), light, maxf(1.5 * unit, 1.0), true)


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
