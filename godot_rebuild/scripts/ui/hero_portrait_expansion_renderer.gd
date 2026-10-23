extends RefCounted
## Shared native canvas renderer for explicitly catalogued Hero Shop portrait specs.

const SIZE := 96.0
const HUMANOID = preload("res://scripts/ui/hero_portrait_expansion_humanoid.gd")
const CREATURE = preload("res://scripts/ui/hero_portrait_expansion_creature.gd")


static func paint(canvas: CanvasItem, box: Rect2, spec: Dictionary) -> void:
	var unit := box.size.x / SIZE
	var ink := Color8(20, 22, 32)
	_backdrop(canvas, box, spec["top"], spec["bottom"])
	_theme(canvas, box, unit, spec)
	var family: String = spec["family"]
	if family in ["mage", "warrior", "assassin", "archer", "gunner", "fighter", "rider"]:
		HUMANOID.paint(family, canvas, box, unit, spec, ink)
	elif family in ["beast", "golem", "serpent", "wraith", "reaper", "treant", "elemental"]:
		CREATURE.paint(family, canvas, box, unit, spec, ink)
	else:
		HUMANOID.paint("warrior", canvas, box, unit, spec, ink)
	if spec["crowned"]:
		_crown(canvas, box, unit, spec, ink)
	if spec["horned"]:
		_horns(canvas, box, unit, spec, ink)
	_sigil(canvas, box, unit, spec)


static func _theme(canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary) -> void:
	var accent: Color = spec["accent"]
	var light: Color = spec["light"]
	var feature: String = spec["feature"]
	match feature:
		"fire":
			_fill(
				canvas,
				box,
				[
					Vector2(10.0, 53.0),
					Vector2(8.0, 35.0),
					Vector2(16.0, 20.0),
					Vector2(17.0, 38.0),
					Vector2(23.0, 48.0)
				],
				accent
			)
			_fill(
				canvas,
				box,
				[
					Vector2(76.0, 48.0),
					Vector2(82.0, 32.0),
					Vector2(80.0, 18.0),
					Vector2(89.0, 36.0),
					Vector2(86.0, 53.0)
				],
				light
			)
		"frost", "crystal":
			_fill(
				canvas,
				box,
				[
					Vector2(12.0, 45.0),
					Vector2(18.0, 19.0),
					Vector2(24.0, 43.0),
					Vector2(19.0, 55.0)
				],
				accent
			)
			_fill(
				canvas,
				box,
				[
					Vector2(74.0, 42.0),
					Vector2(82.0, 16.0),
					Vector2(88.0, 43.0),
					Vector2(82.0, 54.0)
				],
				light
			)
		"nature":
			canvas.draw_arc(
				_p(box, 17.0, 32.0),
				10.0 * unit,
				PI * 0.7,
				PI * 1.8,
				24,
				accent,
				maxf(4.0 * unit, 1.0),
				true
			)
			canvas.draw_arc(
				_p(box, 79.0, 29.0),
				11.0 * unit,
				PI * -0.8,
				PI * 0.3,
				24,
				light,
				maxf(4.0 * unit, 1.0),
				true
			)
		"storm":
			canvas.draw_line(
				_p(box, 13.0, 16.0), _p(box, 19.0, 29.0), light, maxf(2.0 * unit, 1.0), true
			)
			canvas.draw_line(
				_p(box, 19.0, 29.0), _p(box, 14.0, 38.0), accent, maxf(2.0 * unit, 1.0), true
			)
			canvas.draw_line(
				_p(box, 82.0, 17.0), _p(box, 76.0, 30.0), light, maxf(2.0 * unit, 1.0), true
			)
			canvas.draw_line(
				_p(box, 76.0, 30.0), _p(box, 81.0, 40.0), accent, maxf(2.0 * unit, 1.0), true
			)
		"holy":
			canvas.draw_arc(
				_p(box, 47.0, 35.0),
				34.0 * unit,
				PI * 0.75,
				PI * 2.25,
				56,
				light,
				maxf(2.0 * unit, 1.0),
				true
			)
			canvas.draw_line(
				_p(box, 47.0, 2.0), _p(box, 47.0, 11.0), accent, maxf(2.0 * unit, 1.0), true
			)
			canvas.draw_line(
				_p(box, 9.0, 35.0), _p(box, 18.0, 35.0), accent, maxf(2.0 * unit, 1.0), true
			)
		"moon":
			canvas.draw_arc(
				_p(box, 47.0, 37.0),
				33.0 * unit,
				PI * 0.45,
				PI * 1.55,
				48,
				light,
				maxf(5.0 * unit, 1.0),
				true
			)
			canvas.draw_circle(_p(box, 82.0, 18.0), 1.5 * unit, accent)
		"water":
			canvas.draw_arc(
				_p(box, 17.0, 42.0),
				12.0 * unit,
				PI * 0.9,
				PI * 1.9,
				28,
				accent,
				maxf(3.0 * unit, 1.0),
				true
			)
			canvas.draw_arc(
				_p(box, 79.0, 37.0),
				12.0 * unit,
				PI * -0.1,
				PI * 0.9,
				28,
				light,
				maxf(3.0 * unit, 1.0),
				true
			)
		"venom":
			canvas.draw_circle(_p(box, 15.0, 31.0), 6.0 * unit, accent)
			canvas.draw_circle(_p(box, 24.0, 20.0), 3.0 * unit, light)
			canvas.draw_circle(_p(box, 83.0, 35.0), 5.0 * unit, accent)
		"sand":
			canvas.draw_arc(
				_p(box, 19.0, 59.0),
				22.0 * unit,
				PI * 1.1,
				PI * 1.9,
				32,
				accent,
				maxf(4.0 * unit, 1.0),
				true
			)
			canvas.draw_arc(
				_p(box, 78.0, 58.0),
				20.0 * unit,
				PI * 1.1,
				PI * 1.9,
				32,
				light,
				maxf(3.0 * unit, 1.0),
				true
			)
		"blood":
			_fill(
				canvas,
				box,
				[
					Vector2(11.0, 33.0),
					Vector2(16.0, 21.0),
					Vector2(20.0, 35.0),
					Vector2(16.0, 42.0)
				],
				accent
			)
			_fill(
				canvas,
				box,
				[
					Vector2(79.0, 29.0),
					Vector2(84.0, 17.0),
					Vector2(88.0, 31.0),
					Vector2(84.0, 37.0)
				],
				light
			)
		"void", "shadow":
			canvas.draw_arc(
				_p(box, 47.0, 39.0),
				34.0 * unit,
				PI * 0.2,
				PI * 1.45,
				48,
				accent,
				maxf(3.0 * unit, 1.0),
				true
			)
			canvas.draw_arc(
				_p(box, 47.0, 39.0),
				29.0 * unit,
				PI * 1.3,
				PI * 2.35,
				48,
				light,
				maxf(1.5 * unit, 1.0),
				true
			)
		_:
			canvas.draw_arc(
				_p(box, 47.0, 39.0),
				33.0 * unit,
				PI * 0.1,
				PI * 1.7,
				48,
				accent,
				maxf(1.5 * unit, 1.0),
				true
			)
			canvas.draw_circle(_p(box, 82.0, 19.0), 1.5 * unit, light)
			canvas.draw_circle(_p(box, 14.0, 23.0), 1.0 * unit, accent)


static func _crown(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_fill(
		canvas,
		box,
		[
			Vector2(34.0, 25.0),
			Vector2(32.0, 13.0),
			Vector2(42.0, 19.0),
			Vector2(47.0, 9.0),
			Vector2(53.0, 19.0),
			Vector2(62.0, 13.0),
			Vector2(60.0, 26.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(38.0, 23.0),
			Vector2(37.0, 18.0),
			Vector2(43.0, 22.0),
			Vector2(47.0, 16.0),
			Vector2(52.0, 22.0),
			Vector2(57.0, 18.0),
			Vector2(56.0, 23.0)
		],
		spec["accent"]
	)
	canvas.draw_circle(_p(box, 47.0, 22.0), 1.5 * unit, spec["light"])


static func _horns(
	canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary, ink: Color
) -> void:
	_fill(
		canvas,
		box,
		[
			Vector2(35.0, 30.0),
			Vector2(24.0, 25.0),
			Vector2(18.0, 11.0),
			Vector2(28.0, 18.0),
			Vector2(39.0, 23.0)
		],
		ink
	)
	_fill(
		canvas,
		box,
		[
			Vector2(59.0, 23.0),
			Vector2(70.0, 18.0),
			Vector2(79.0, 10.0),
			Vector2(73.0, 25.0),
			Vector2(61.0, 30.0)
		],
		ink
	)
	canvas.draw_line(
		_p(box, 24.0, 20.0), _p(box, 30.0, 24.0), spec["accent"], maxf(2.0 * unit, 1.0), true
	)
	canvas.draw_line(
		_p(box, 66.0, 24.0), _p(box, 72.0, 19.0), spec["accent"], maxf(2.0 * unit, 1.0), true
	)


static func _sigil(canvas: CanvasItem, box: Rect2, unit: float, spec: Dictionary) -> void:
	var accent: Color = spec["light"]
	var sigil: int = spec["sigil"]
	match sigil:
		0:
			_fill(
				canvas,
				box,
				[
					Vector2(47.0, 70.0),
					Vector2(52.0, 76.0),
					Vector2(47.0, 82.0),
					Vector2(42.0, 76.0)
				],
				accent
			)
		1:
			canvas.draw_line(
				_p(box, 42.0, 73.0), _p(box, 52.0, 79.0), accent, maxf(2.0 * unit, 1.0), true
			)
			canvas.draw_line(
				_p(box, 52.0, 73.0), _p(box, 42.0, 79.0), accent, maxf(2.0 * unit, 1.0), true
			)
		2:
			canvas.draw_line(
				_p(box, 41.0, 73.0), _p(box, 47.0, 80.0), accent, maxf(2.0 * unit, 1.0), true
			)
			canvas.draw_line(
				_p(box, 47.0, 80.0), _p(box, 53.0, 73.0), accent, maxf(2.0 * unit, 1.0), true
			)
		3:
			canvas.draw_circle(_p(box, 47.0, 76.0), 4.0 * unit, accent)
			canvas.draw_circle(_p(box, 47.0, 76.0), 1.5 * unit, spec["primary"])
		4:
			_fill(
				canvas, box, [Vector2(47.0, 70.0), Vector2(53.0, 81.0), Vector2(41.0, 81.0)], accent
			)
		5:
			canvas.draw_line(
				_p(box, 42.0, 72.0), _p(box, 42.0, 81.0), accent, maxf(1.5 * unit, 1.0), true
			)
			canvas.draw_line(
				_p(box, 47.0, 71.0), _p(box, 47.0, 82.0), accent, maxf(1.5 * unit, 1.0), true
			)
			canvas.draw_line(
				_p(box, 52.0, 72.0), _p(box, 52.0, 81.0), accent, maxf(1.5 * unit, 1.0), true
			)
		6:
			canvas.draw_arc(
				_p(box, 47.0, 76.0),
				6.0 * unit,
				PI * 0.4,
				PI * 1.7,
				24,
				accent,
				maxf(2.0 * unit, 1.0),
				true
			)
		_:
			canvas.draw_line(
				_p(box, 47.0, 70.0), _p(box, 47.0, 82.0), accent, maxf(1.5 * unit, 1.0), true
			)
			canvas.draw_line(
				_p(box, 41.0, 76.0), _p(box, 53.0, 76.0), accent, maxf(1.5 * unit, 1.0), true
			)
			canvas.draw_circle(_p(box, 47.0, 76.0), 2.0 * unit, accent)


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
