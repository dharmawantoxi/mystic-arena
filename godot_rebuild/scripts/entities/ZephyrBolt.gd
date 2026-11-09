class_name ZephyrBolt
extends RefCounted

## Native heroes/zephyr_fx.py::draw_bolt. Geometry is tested against the original
## Python function. CanvasItem alpha compositing is NOT Pygame RGB_ADD parity.
static var palette: Dictionary = {}


static func ensure_loaded() -> void:
	if not palette.is_empty():
		return
	var file := FileAccess.open("res://data/zephyr_palette.json", FileAccess.READ)
	if file != null:
		var parsed: Variant = JSON.parse_string(file.get_as_text())
		if parsed is Dictionary:
			palette = parsed


static func _rgba(key: String) -> Array:
	var rgb: Array = palette[key]
	return [rgb[0], rgb[1], rgb[2], 255]


static func _alpha(color: Array, alpha: int) -> Array:
	return [color[0], color[1], color[2], alpha]


static func _point(x: float, y: float) -> Array:
	# Keep calculations in scalar doubles until Python-compatible truncation.
	return [int(x), int(y)]


static func commands(
	position: Vector2, angle := 0.0, age := 0, critical := false, radius := 6.0
) -> Array:
	return commands_at(position.x, position.y, angle, age, critical, radius)


static func commands_at(
	px: float, py: float, angle := 0.0, age := 0, critical := false, radius := 6.0
) -> Array:
	ensure_loaded()
	if palette.is_empty() or radius <= 0.0:
		return []
	var x := int(px)
	var y := int(py)
	var ca := cos(angle)
	var sa := sin(angle)
	var nx := -sa
	var ny := ca
	var r := radius * (1.2 if critical else 1.0)
	var halo := [110, 74, 12, 255] if critical else _rgba("fx_dark")
	var dark := [92, 58, 8, 255] if critical else _rgba("fx_darkest")
	var body := _rgba("gold" if critical else "fx_mid")
	var edge := _rgba("highlight" if critical else "fx_light")
	var tail := r * 4.2
	var result: Array = [
		[
			"polygon",
			_alpha(dark, 120),
			[
				_point(x + nx * r * 0.8, y + ny * r * 0.8),
				_point(x - ca * tail, y - sa * tail),
				_point(x - nx * r * 0.8, y - ny * r * 0.8)
			]
		],
		[
			"polygon",
			_alpha(body, 90),
			[
				_point(x + nx * r * 0.4, y + ny * r * 0.4),
				_point(x - ca * tail * 0.62, y - sa * tail * 0.62),
				_point(x - nx * r * 0.4, y - ny * r * 0.4)
			]
		],
	]
	var gr := int(r * 2.1)
	result.append(["glow", halo, [x - gr, y - gr], gr, 0.42])
	var front := r * 3.1
	var back := r * 1.5
	var width := r * 0.78
	var points: Array = [
		_point(x + ca * front, y + sa * front),
		_point(x + nx * width - ca * r * 0.2, y + ny * width - sa * r * 0.2),
		_point(x - ca * back, y - sa * back),
		_point(x - nx * width - ca * r * 0.2, y - ny * width - sa * r * 0.2),
	]
	var outline_one: Array = []
	var outline_two: Array = []
	for point: Array in points:
		outline_one.append([point[0] + int(ca) - int(nx), point[1] + int(sa) - int(ny)])
		outline_two.append([point[0] + 1, point[1] + 1])
	result.append(["polygon", _rgba("outline"), outline_one])
	result.append(["polygon", _rgba("outline"), outline_two])
	result.append(["polygon", body, points])
	result.append(
		[
			"polygon",
			edge,
			[
				_point(x + ca * front * 0.78, y + sa * front * 0.78),
				_point(x + nx * width * 0.46, y + ny * width * 0.46),
				_point(x - ca * back * 0.5, y - sa * back * 0.5),
				_point(x - nx * width * 0.16, y - ny * width * 0.16)
			]
		]
	)
	for side: int in [-1, 1]:
		var bx := x - ca * r * 0.35 + nx * side * width * 0.9
		var by := y - sa * r * 0.35 + ny * side * width * 0.9
		result.append(
			[
				"line",
				_rgba("thorn_lit"),
				_point(bx, by),
				_point(
					bx + nx * side * r * 0.95 - ca * r * 1.15,
					by + ny * side * r * 0.95 - sa * r * 1.15
				),
				2
			]
		)
	var cx := x + int(ca * r * 0.35)
	var cy := y + int(sa * r * 0.35)
	var size := maxi(2, int(r * 0.6))
	result.append(["rect", _rgba("fx_hot"), [cx - int(size / 2), cy - int(size / 2), size, size]])
	result.append(["rect", _rgba("fx_white"), [cx - 1, cy - 1, 2, 2]])
	result.append(
		[
			"rect",
			_rgba("fx_white"),
			[int(x + ca * front * 0.9) - 1, int(y + sa * front * 0.9) - 1, 2, 2]
		]
	)
	var spin := age * 0.35
	for index in range(3):
		var orbit := spin + index * TAU / 3.0
		result.append(
			[
				"rect",
				_rgba("fx_bright"),
				[x + int(cos(orbit) * r * 1.9), y + int(sin(orbit) * r * 1.9), 2, 2]
			]
		)
	return result


static func draw(
	canvas: CanvasItem, position: Vector2, angle: float, age: int, critical: bool, radius := 6.0
) -> bool:
	var shapes := commands(position, angle, age, critical, radius)
	draw_shapes(canvas, shapes)
	return not shapes.is_empty()


static func draw_shapes(canvas: CanvasItem, shapes: Array) -> void:
	for shape: Array in shapes:
		var rgba: Array = shape[1]
		var color := Color(rgba[0] / 255.0, rgba[1] / 255.0, rgba[2] / 255.0, rgba[3] / 255.0)
		match str(shape[0]):
			"polygon":
				var points := PackedVector2Array()
				for point: Array in shape[2]:
					points.append(Vector2(point[0], point[1]))
				# Repeated sampled staff poses create zero-area quads. Pygame
				# accepts those, but Godot cannot triangulate them.
				var area := 0.0
				for index in points.size():
					area += points[index].cross(points[(index + 1) % points.size()])
				if points.size() >= 3 and absf(area) > 0.0001:
					if not Geometry2D.triangulate_polygon(points).is_empty():
						canvas.draw_colored_polygon(points, color)
			"polygon_outline":
				var points := PackedVector2Array()
				for point: Array in shape[2]:
					points.append(Vector2(point[0], point[1]))
				if points.size() >= 3:
					points.append(points[0])
					canvas.draw_polyline(points, color, float(shape[3]))
			"polyline":
				var points := PackedVector2Array()
				for point: Array in shape[2]:
					points.append(Vector2(point[0], point[1]))
				if points.size() >= 2:
					canvas.draw_polyline(points, color, float(shape[3]))
			"line":
				canvas.draw_line(
					Vector2(shape[2][0], shape[2][1]),
					Vector2(shape[3][0], shape[3][1]),
					color,
					float(shape[4])
				)
			"rect":
				var box: Array = shape[2]
				canvas.draw_rect(Rect2(box[0], box[1], box[2], box[3]), color)
			"oval":
				_draw_oval(canvas, shape, color)
			"glow":
				_draw_glow(canvas, shape, color)
			"circle":
				if shape.size() > 4:
					# Pygame ring strokes extend inward; CanvasItem strokes are centered.
					var width := float(shape[4])
					canvas.draw_arc(
						Vector2(shape[2][0], shape[2][1]),
						maxf(0.0, float(shape[3]) - width * 0.5),
						0.0,
						TAU,
						96,
						color,
						width
					)
				else:
					canvas.draw_circle(Vector2(shape[2][0], shape[2][1]), float(shape[3]), color)
			"spark":
				draw_shapes(canvas, spark_commands(int(shape[3]), rgba, int(rgba[3]), shape[2]))
			"ellipse":
				_draw_ellipse(canvas, shape, color)
			"arc":
				var box: Array = shape[2]
				var center := Vector2(
					float(box[0]) + float(box[2]) * 0.5, float(box[1]) + float(box[3]) * 0.5
				)
				# Pygame angles are counter-clockwise in screen coordinates.
				canvas.draw_arc(
					center,
					float(box[2]) * 0.5,
					-float(shape[4]),
					-float(shape[3]),
					48,
					color,
					float(shape[5])
				)


static func _draw_glow(canvas: CanvasItem, shape: Array, color: Color) -> void:
	# Same concentric geometry/ramp as glow_surface. Native alpha blending
	# intentionally remains a documented difference from Pygame RGB_ADD.
	var radius := maxi(2, int(shape[3]))
	var center := Vector2(shape[2][0] + radius + 1, shape[2][1] + radius + 1)
	var steps := clampi(radius, 4, 14)
	for index in range(steps, 0, -1):
		var t := float(index) / steps
		var strength := float(shape[4]) * pow(1.0 - t, 1.7)
		if strength <= 0.004:
			continue
		var tint := Color(color.r * strength, color.g * strength, color.b * strength, strength)
		canvas.draw_circle(center, maxi(1, int(radius * t)), tint)


static func ellipse_rotation(degrees: float) -> float:
	# Python int(angle_deg) // 10 * 10 floors negative values after truncation.
	return floor(float(int(degrees)) / 10.0) * 10.0


static func _draw_ellipse(canvas: CanvasItem, shape: Array, color: Color) -> void:
	var angle := deg_to_rad(ellipse_rotation(float(shape[6])))
	var ca := cos(angle)
	var sa := sin(angle)
	var center := Vector2(shape[2][0], shape[2][1])
	var points := PackedVector2Array()
	for index in range(65):
		var phase := index * TAU / 64.0
		var x := cos(phase) * float(shape[3])
		var y := sin(phase) * float(shape[4])
		points.append(center + Vector2(x * ca - y * sa, x * sa + y * ca))
	canvas.draw_polyline(points, color, float(shape[5]))


static func spark_commands(size: int, rgb: Array, opacity := 255, offset: Array = [0, 0]) -> Array:
	size = maxi(3, size)
	var x := int(offset[0])
	var y := int(offset[1])
	var vertical := maxi(1, int(size / 3))
	var horizontal := maxi(1, int(size / 4))
	return [
		[
			"polygon",
			[rgb[0], rgb[1], rgb[2], 235.0 * opacity / 255.0],
			[
				[x + size, y],
				[x + size + vertical, y + size],
				[x + size, y + size * 2],
				[x + size - vertical, y + size]
			]
		],
		[
			"polygon",
			[rgb[0], rgb[1], rgb[2], 190.0 * opacity / 255.0],
			[
				[x, y + size],
				[x + size, y + size - horizontal],
				[x + size * 2, y + size],
				[x + size, y + size + horizontal]
			]
		],
		["circle", [255, 255, 255, opacity], [x + size, y + size], maxi(1, int(size / 4))],
	]


static func _draw_oval(canvas: CanvasItem, shape: Array, color: Color) -> void:
	var box: Array = shape[2]
	var width := float(shape[3])
	var center := Vector2(float(box[0]) + float(box[2]) * 0.5, float(box[1]) + float(box[3]) * 0.5)
	var rx := maxf(0.0, (float(box[2]) - width) * 0.5)
	var ry := maxf(0.0, (float(box[3]) - width) * 0.5)
	var points := PackedVector2Array()
	for i in range(65):
		var angle := i * TAU / 64.0
		points.append(center + Vector2(cos(angle) * rx, sin(angle) * ry))
	if width <= 0.0:
		points.resize(64)
		canvas.draw_colored_polygon(points, color)
	else:
		canvas.draw_polyline(points, color, width)
