extends Control
## Procedural Hero Shop portrait. Kaizen and Thorne carry a hand-authored
## canvas; every other hero id falls back to a deterministic generic bust
## derived from the id hash, so a shared card never renders an empty slot.
## Presentation only: no roster state, no input, no gameplay dependencies.

const SIZE := 96.0
const KAIZEN := "kaizen"
const THORNE := "thorne"

var hero_type := ""

var _definition: Variant = null


static func custom_ids() -> Array[String]:
	return [KAIZEN, THORNE]


static func has_custom(id: String) -> bool:
	return id == KAIZEN or id == THORNE


## Stable HSV hue in [0, 1) used by the generic fallback bust.
static func hue_for(id: String) -> float:
	var total := 0
	for byte in id.to_utf8_buffer():
		total = (total * 31 + int(byte)) % 360
	return float(total) / 360.0


func setup(id: String, definition: Variant = null, pixel_size: float = SIZE) -> void:
	hero_type = id
	_definition = definition
	custom_minimum_size = Vector2(pixel_size, pixel_size)
	queue_redraw()


func _draw() -> void:
	var box := Rect2(Vector2.ZERO, size)
	if box.size.x < 8.0 or box.size.y < 8.0:
		return
	match hero_type:
		KAIZEN:
			_draw_kaizen(box)
		THORNE:
			_draw_thorne(box)
		_:
			_draw_generic(box)
	draw_rect(box.grow(-1.0), Color8(10, 16, 24), false, 2.0)


func _draw_kaizen(box: Rect2) -> void:
	var unit := _scale(box)
	var outline := Color8(24, 26, 40)
	var shadow := Color8(16, 40, 82)
	var dark := Color8(30, 60, 110)
	var body := Color8(55, 80, 145)
	var mid := Color8(110, 175, 230)
	var light := Color8(175, 220, 250)
	var weapon := Color8(210, 220, 235)
	var fx := Color8(245, 252, 255)

	_backdrop(box, shadow, dark)
	for index in 3:
		var radius := (20.0 + 9.0 * float(index)) * unit
		draw_arc(
			_p(box, 48.0, 44.0),
			radius,
			-PI * 0.35,
			PI * 0.75,
			24,
			Color(mid.r, mid.g, mid.b, 0.34 - 0.09 * float(index)),
			maxf(2.0 * unit, 1.0),
			true
		)
	draw_colored_polygon(
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
	draw_colored_polygon(
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
	draw_colored_polygon(
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
	draw_colored_polygon(
		_poly(
			box,
			[Vector2(46.0, 36.0), Vector2(50.0, 36.0), Vector2(52.0, 58.0), Vector2(44.0, 58.0)]
		),
		mid
	)
	draw_circle(_p(box, 48.0, 24.0), 10.0 * unit, mid)
	draw_colored_polygon(
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
	draw_line(_p(box, 42.0, 24.0), _p(box, 46.0, 24.0), outline, maxf(2.0 * unit, 1.0))
	draw_line(_p(box, 51.0, 24.0), _p(box, 55.0, 24.0), outline, maxf(2.0 * unit, 1.0))
	draw_line(_p(box, 66.0, 82.0), _p(box, 22.0, 20.0), weapon, maxf(5.0 * unit, 1.5), true)
	draw_line(_p(box, 66.0, 82.0), _p(box, 22.0, 20.0), light, maxf(2.0 * unit, 1.0), true)
	draw_line(_p(box, 64.0, 78.0), _p(box, 70.0, 84.0), outline, maxf(3.0 * unit, 1.0))
	draw_circle(_p(box, 76.0, 20.0), 3.0 * unit, fx)


func _draw_thorne(box: Rect2) -> void:
	var unit := _scale(box)
	var outline := Color8(38, 26, 10)
	var dark := Color8(96, 60, 14)
	var body := Color8(215, 155, 30)
	var shade := Color8(150, 95, 20)
	var light := Color8(245, 205, 110)
	var goop := Color8(120, 190, 90)

	_backdrop(box, Color8(58, 40, 18), Color8(26, 20, 12))
	var base := _p(box, 48.0, 52.0)
	for index in 7:
		var angle := -PI * 0.92 + PI * 0.84 * (float(index) / 6.0)
		var direction := Vector2(cos(angle), sin(angle))
		var tip := base + direction * 40.0 * unit
		var side := Vector2(-direction.y, direction.x) * 3.5 * unit
		draw_colored_polygon(PackedVector2Array([base - side, base + side, tip]), shade)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(30.0, 38.0),
				Vector2(66.0, 38.0),
				Vector2(72.0, 62.0),
				Vector2(66.0, 86.0),
				Vector2(30.0, 86.0),
				Vector2(24.0, 62.0)
			]
		),
		dark
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(34.0, 42.0),
				Vector2(62.0, 42.0),
				Vector2(67.0, 62.0),
				Vector2(62.0, 84.0),
				Vector2(34.0, 84.0),
				Vector2(29.0, 62.0)
			]
		),
		body
	)
	draw_colored_polygon(
		_poly(
			box,
			[Vector2(40.0, 50.0), Vector2(56.0, 50.0), Vector2(58.0, 66.0), Vector2(38.0, 66.0)]
		),
		light
	)
	draw_circle(_p(box, 48.0, 30.0), 11.0 * unit, body)
	draw_colored_polygon(
		_poly(box, [Vector2(54.0, 30.0), Vector2(72.0, 34.0), Vector2(54.0, 40.0)]), shade
	)
	draw_circle(_p(box, 43.0, 27.0), 2.2 * unit, outline)
	draw_circle(_p(box, 51.0, 27.0), 2.2 * unit, outline)
	draw_circle(_p(box, 77.0, 38.0), 3.0 * unit, goop)
	draw_circle(_p(box, 85.0, 45.0), 2.0 * unit, goop)


func _draw_generic(box: Rect2) -> void:
	var unit := _scale(box)
	var hue := hue_for(hero_type)
	var dark := Color.from_hsv(hue, 0.55, 0.22)
	var body := Color.from_hsv(hue, 0.42, 0.62)
	var light := Color.from_hsv(hue, 0.30, 0.86)

	_backdrop(box, dark, Color.from_hsv(hue, 0.45, 0.10))
	draw_circle(_p(box, 48.0, 44.0), 27.0 * unit, Color.from_hsv(hue, 0.40, 0.30))
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(26.0, 88.0),
				Vector2(32.0, 58.0),
				Vector2(48.0, 50.0),
				Vector2(64.0, 58.0),
				Vector2(70.0, 88.0)
			]
		),
		body
	)
	draw_circle(_p(box, 48.0, 34.0), 12.0 * unit, light)
	draw_rect(Rect2(_p(box, 40.0, 31.0), Vector2(16.0, 4.0) * unit), dark)
	draw_rect(Rect2(_p(box, 26.0, 88.0), Vector2(44.0, 4.0) * unit), _accent())


func _accent() -> Color:
	var role := ""
	if _definition is Dictionary:
		role = String((_definition as Dictionary).get("role", ""))
	elif _definition != null and "role" in _definition:
		role = String(_definition.role)
	match role:
		"Assassin":
			return Color8(120, 220, 200)
		"Bruiser":
			return Color8(230, 170, 70)
		"Mage":
			return Color8(170, 140, 240)
		"Marksman":
			return Color8(230, 130, 120)
		_:
			return Color8(150, 170, 175)


func _scale(box: Rect2) -> float:
	return box.size.x / SIZE


func _p(box: Rect2, x: float, y: float) -> Vector2:
	return box.position + Vector2(x, y) * _scale(box)


func _poly(box: Rect2, points: Array[Vector2]) -> PackedVector2Array:
	var result := PackedVector2Array()
	for point in points:
		result.append(box.position + point * _scale(box))
	return result


func _backdrop(box: Rect2, top: Color, bottom: Color) -> void:
	var bands := 18
	var height := box.size.y / float(bands)
	for index in bands:
		var band := Rect2(
			box.position.x, box.position.y + height * float(index), box.size.x, height + 1.0
		)
		draw_rect(band, top.lerp(bottom, float(index) / float(bands - 1)))
