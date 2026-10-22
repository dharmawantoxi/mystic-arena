extends RefCounted
## Native canvas painter for Kaizen, the Wind Blade.

const SIZE := 96.0


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var unit := box.size.x / SIZE
	var outline := Color8(24, 26, 40)
	var shadow := Color8(16, 40, 82)
	var dark := Color8(30, 60, 110)
	var body := Color8(55, 80, 145)
	var mid := Color8(110, 175, 230)
	var light := Color8(175, 220, 250)
	var weapon := Color8(210, 220, 235)
	var fx := Color8(245, 252, 255)
	_backdrop(canvas, box, shadow, dark)
	for index in 3:
		var radius := (20.0 + 9.0 * float(index)) * unit
		canvas.draw_arc(
			_p(box, 48.0, 44.0),
			radius,
			-PI * 0.35,
			PI * 0.75,
			24,
			Color(mid.r, mid.g, mid.b, 0.34 - 0.09 * float(index)),
			maxf(2.0 * unit, 1.0),
			true
		)
	canvas.draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(40.0, 26.0),
				Vector2(12.0, 34.0),
				Vector2(4.0, 46.0),
				Vector2(16.0, 45.0),
				Vector2(38.0, 34.0)
			]
		),
		light
	)
	canvas.draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(38.0, 32.0),
				Vector2(58.0, 32.0),
				Vector2(66.0, 58.0),
				Vector2(58.0, 86.0),
				Vector2(38.0, 86.0),
				Vector2(30.0, 58.0)
			]
		),
		dark
	)
	canvas.draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(42.0, 34.0),
				Vector2(54.0, 34.0),
				Vector2(60.0, 58.0),
				Vector2(54.0, 84.0),
				Vector2(42.0, 84.0),
				Vector2(36.0, 58.0)
			]
		),
		body
	)
	canvas.draw_colored_polygon(
		_poly(
			box,
			[Vector2(46.0, 36.0), Vector2(50.0, 36.0), Vector2(52.0, 58.0), Vector2(44.0, 58.0)]
		),
		mid
	)
	canvas.draw_circle(_p(box, 48.0, 24.0), 10.0 * unit, mid)
	canvas.draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(36.0, 26.0),
				Vector2(48.0, 9.0),
				Vector2(60.0, 26.0),
				Vector2(56.0, 30.0),
				Vector2(40.0, 30.0)
			]
		),
		dark
	)
	canvas.draw_line(_p(box, 42.0, 24.0), _p(box, 46.0, 24.0), outline, maxf(2.0 * unit, 1.0))
	canvas.draw_line(_p(box, 51.0, 24.0), _p(box, 55.0, 24.0), outline, maxf(2.0 * unit, 1.0))
	canvas.draw_line(_p(box, 66.0, 82.0), _p(box, 22.0, 20.0), weapon, maxf(5.0 * unit, 1.5), true)
	canvas.draw_line(_p(box, 66.0, 82.0), _p(box, 22.0, 20.0), light, maxf(2.0 * unit, 1.0), true)
	canvas.draw_line(_p(box, 64.0, 78.0), _p(box, 70.0, 84.0), outline, maxf(3.0 * unit, 1.0))
	canvas.draw_circle(_p(box, 76.0, 20.0), 3.0 * unit, fx)


static func _p(box: Rect2, x: float, y: float) -> Vector2:
	return box.position + Vector2(x, y) * (box.size.x / SIZE)


static func _poly(box: Rect2, points: Array[Vector2]) -> PackedVector2Array:
	var result := PackedVector2Array()
	for point in points:
		result.append(box.position + point * (box.size.x / SIZE))
	return result


static func _backdrop(canvas: CanvasItem, box: Rect2, top: Color, bottom: Color) -> void:
	var bands := 18
	var height := box.size.y / float(bands)
	for index in bands:
		var band := Rect2(
			box.position.x, box.position.y + height * float(index), box.size.x, height + 1.0
		)
		canvas.draw_rect(band, top.lerp(bottom, float(index) / float(bands - 1)))
