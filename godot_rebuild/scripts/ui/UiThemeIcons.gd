class_name UiThemeIcons
extends RefCounted

## Vector icon geometry from ui_theme.draw_icon. Coordinates stay in the
## source's float space; the pygame oracle records the same primitive calls.


static func draw_data(name: String, center: Vector2, color: Array, s := 1.0) -> Array:
	var ops: Array = []
	var cx := center.x
	var cy := center.y
	if _basic(name, cx, cy, color, s, ops):
		return ops
	if _system(name, cx, cy, color, s, ops):
		return ops
	if _status(name, cx, cy, color, s, ops):
		return ops
	if _navigation(name, cx, cy, color, s, ops):
		return ops
	_misc(name, cx, cy, color, s, ops)
	return ops


static func _basic(name: String, cx: float, cy: float, color: Array, s: float, ops: Array) -> bool:
	match name:
		"play":
			ops.append(
				_polygon(
					[
						Vector2(cx - 6 * s, cy - 10 * s),
						Vector2(cx - 6 * s, cy + 10 * s),
						Vector2(cx + 11 * s, cy)
					],
					color
				)
			)
		"continue":
			ops.append(
				_polygon(
					[
						Vector2(cx - 11 * s, cy - 9 * s),
						Vector2(cx - 11 * s, cy + 9 * s),
						Vector2(cx - 1 * s, cy)
					],
					color
				)
			)
			ops.append(
				_polygon(
					[Vector2(cx, cy - 9 * s), Vector2(cx, cy + 9 * s), Vector2(cx + 11 * s, cy)],
					color
				)
			)
		"coin":
			ops.append(_circle(Vector2(cx, cy), 9 * s, [255, 205, 66]))
			ops.append(_circle(Vector2(cx, cy), 9 * s, [190, 140, 32], 2))
			ops.append(_circle(Vector2(cx, cy), 5 * s, [230, 175, 50]))
			ops.append(
				_line(Vector2(cx, cy - 3.5 * s), Vector2(cx, cy + 3.5 * s), [190, 140, 32], 2)
			)
		"pad":
			ops.append(
				_rect(UiTheme.rect(cx - 12 * s, cy - 7 * s, 24 * s, 15 * s), color, 0, int(7 * s))
			)
			ops.append(_circle(Vector2(cx - 6 * s, cy), 2 * s, [10, 12, 22]))
			ops.append(_circle(Vector2(cx + 5 * s, cy + 2 * s), 2 * s, [10, 12, 22]))
		"help":
			var r := 5.5 * s
			ops.append(_arc(UiTheme.rect(cx - r, cy - 9 * s, 2 * r, 2 * r), color, 3.4, 6.9, 2))
			ops.append(
				_line(Vector2(cx + 4.5 * s, cy - 0.3 * s), Vector2(cx, cy + 2.5 * s), color, 2)
			)
			ops.append(_circle(Vector2(cx, cy + 6.5 * s), 1.6 * s, color))
		"gear":
			ops.append(_circle(Vector2(cx, cy), 7 * s, color, 2))
			for index in range(6):
				var a := index * PI / 3.0
				ops.append(
					_line(
						Vector2(cx + cos(a) * 7 * s, cy + sin(a) * 7 * s),
						Vector2(cx + cos(a) * 11 * s, cy + sin(a) * 11 * s),
						color,
						2
					)
				)
		"star":
			for pair: Array in [[1, 0], [0, 1], [1, 1], [1, -1]]:
				var dx: int = pair[0]
				var dy: int = pair[1]
				ops.append(
					_line(
						Vector2(cx - dx * 8 * s, cy - dy * 8 * s),
						Vector2(cx + dx * 8 * s, cy + dy * 8 * s),
						color,
						2
					)
				)
			ops.append(_circle(Vector2(cx, cy), 3 * s, color))
		_:
			return false
	return true


static func _system(name: String, cx: float, cy: float, color: Array, s: float, ops: Array) -> bool:
	match name:
		"quit":
			ops.append(
				_line(Vector2(cx - 7 * s, cy - 7 * s), Vector2(cx + 7 * s, cy + 7 * s), color, 3)
			)
			ops.append(
				_line(Vector2(cx + 7 * s, cy - 7 * s), Vector2(cx - 7 * s, cy + 7 * s), color, 3)
			)
		"lock":
			var bw := 14 * s
			var bh := 11 * s
			var bx := cx - bw / 2.0
			var by := cy - bh / 2.0 + 2 * s
			ops.append(_rect(UiTheme.rect(bx, by, bw, bh), color, 0, int(3 * s)))
			ops.append(
				_arc(
					UiTheme.rect(bx + bw * 0.2, by - 8 * s, bw * 0.6, 12 * s), color, 3.14, 6.28, 2
				)
			)
			ops.append(_circle(Vector2(cx, by + bh * 0.45), 2 * s, [10, 12, 22]))
		"speaker":
			ops.append(_rect(UiTheme.rect(cx - 9 * s, cy - 3 * s, 5 * s, 6 * s), color))
			ops.append(
				_polygon(
					[
						Vector2(cx - 4 * s, cy - 3 * s),
						Vector2(cx + 1 * s, cy - 8 * s),
						Vector2(cx + 1 * s, cy + 8 * s),
						Vector2(cx - 4 * s, cy + 3 * s)
					],
					color
				)
			)
			ops.append(
				_arc(UiTheme.rect(cx + 1 * s, cy - 7 * s, 12 * s, 14 * s), color, -1.0, 1.0, 2)
			)
			ops.append(
				_arc(UiTheme.rect(cx + 2 * s, cy - 10 * s, 16 * s, 20 * s), color, -0.9, 0.9, 2)
			)
		"swords":
			ops.append(
				_line(Vector2(cx - 8 * s, cy - 8 * s), Vector2(cx + 8 * s, cy + 8 * s), color, 3)
			)
			ops.append(
				_line(Vector2(cx + 8 * s, cy - 8 * s), Vector2(cx - 8 * s, cy + 8 * s), color, 3)
			)
			ops.append(
				_line(
					Vector2(cx - 9 * s, cy + 5 * s),
					Vector2(cx - 5 * s, cy + 9 * s),
					[10, 12, 22],
					3
				)
			)
			ops.append(
				_line(
					Vector2(cx + 9 * s, cy + 5 * s),
					Vector2(cx + 5 * s, cy + 9 * s),
					[10, 12, 22],
					3
				)
			)
			ops.append(_circle(Vector2(cx, cy), 2.5 * s, color))
		"monitor":
			ops.append(_rect(UiTheme.rect(cx - 9 * s, cy - 7 * s, 18 * s, 12 * s), color, 2))
			ops.append(_line(Vector2(cx, cy + 5 * s), Vector2(cx, cy + 9 * s), color, 2))
			ops.append(
				_line(Vector2(cx - 5 * s, cy + 9 * s), Vector2(cx + 5 * s, cy + 9 * s), color, 2)
			)
		_:
			return false
	return true


static func _status(name: String, cx: float, cy: float, color: Array, s: float, ops: Array) -> bool:
	match name:
		"cloud":
			ops.append(_circle(Vector2(cx - 5 * s, cy + 2 * s), 5 * s, color))
			ops.append(_circle(Vector2(cx, cy - 3 * s), 6 * s, color))
			ops.append(_circle(Vector2(cx + 6 * s, cy + 2 * s), 5 * s, color))
			ops.append(_rect(UiTheme.rect(cx - 5 * s, cy + 2 * s, 11 * s, 4 * s), color))
		"warn":
			ops.append(
				_polygon(
					[
						Vector2(cx, cy - 9 * s),
						Vector2(cx + 10 * s, cy + 8 * s),
						Vector2(cx - 10 * s, cy + 8 * s)
					],
					color
				)
			)
			ops.append(_line(Vector2(cx, cy - 4 * s), Vector2(cx, cy + 2 * s), [10, 12, 22], 2))
			ops.append(_circle(Vector2(cx, cy + 5 * s), 1.5 * s, [10, 12, 22]))
		"heart":
			var r := 4.2 * s
			ops.append(_circle(Vector2(cx - r, cy - r * 0.4), r, color))
			ops.append(_circle(Vector2(cx + r, cy - r * 0.4), r, color))
			ops.append(
				_polygon(
					[
						Vector2(cx - r * 1.85, cy),
						Vector2(cx + r * 1.85, cy),
						Vector2(cx, cy + r * 2.1)
					],
					color
				)
			)
		"skull":
			ops.append(_circle(Vector2(cx, cy - 2.5 * s), 6.5 * s, color))
			ops.append(_rect(UiTheme.rect(cx - 3.5 * s, cy + 2.5 * s, 7 * s, 5 * s), color, 0, 2))
			ops.append(_circle(Vector2(cx - 2.6 * s, cy - 3.5 * s), 2 * s, [10, 12, 22]))
			ops.append(_circle(Vector2(cx + 2.6 * s, cy - 3.5 * s), 2 * s, [10, 12, 22]))
		"bolt":
			ops.append(
				_polygon(
					[
						Vector2(cx + 2 * s, cy - 10 * s),
						Vector2(cx - 6 * s, cy + 1 * s),
						Vector2(cx - 1 * s, cy + 1 * s),
						Vector2(cx - 3 * s, cy + 10 * s),
						Vector2(cx + 6 * s, cy - 1 * s),
						Vector2(cx + 1 * s, cy - 1 * s)
					],
					color
				)
			)
		_:
			return false
	return true


static func _navigation(
	name: String, cx: float, cy: float, color: Array, s: float, ops: Array
) -> bool:
	match name:
		"check":
			ops.append(_line(Vector2(cx - 7 * s, cy), Vector2(cx - 2 * s, cy + 5 * s), color, 3))
			ops.append(
				_line(Vector2(cx - 2 * s, cy + 5 * s), Vector2(cx + 7 * s, cy - 5 * s), color, 3)
			)
		"back":
			ops.append(_line(Vector2(cx + 4 * s, cy - 7 * s), Vector2(cx - 5 * s, cy), color, 3))
			ops.append(_line(Vector2(cx - 5 * s, cy), Vector2(cx + 4 * s, cy + 7 * s), color, 3))
		"chevron_l", "chevron_r":
			var d := -1 if name == "chevron_l" else 1
			ops.append(
				_line(Vector2(cx + 4 * s * d, cy - 6 * s), Vector2(cx - 4 * s * d, cy), color, 3)
			)
			ops.append(
				_line(Vector2(cx - 4 * s * d, cy), Vector2(cx + 4 * s * d, cy + 6 * s), color, 3)
			)
		"plus":
			ops.append(_line(Vector2(cx - 6 * s, cy), Vector2(cx + 6 * s, cy), color, 3))
			ops.append(_line(Vector2(cx, cy - 6 * s), Vector2(cx, cy + 6 * s), color, 3))
		"minus":
			ops.append(_line(Vector2(cx - 6 * s, cy), Vector2(cx + 6 * s, cy), color, 3))
		_:
			return false
	return true


static func _misc(name: String, cx: float, cy: float, color: Array, s: float, ops: Array) -> void:
	match name:
		"crown":
			ops.append(
				_polygon(
					[
						Vector2(cx - 9 * s, cy + 6 * s),
						Vector2(cx - 9 * s, cy - 4 * s),
						Vector2(cx - 4 * s, cy + 1 * s),
						Vector2(cx, cy - 7 * s),
						Vector2(cx + 4 * s, cy + 1 * s),
						Vector2(cx + 9 * s, cy - 4 * s),
						Vector2(cx + 9 * s, cy + 6 * s)
					],
					color
				)
			)
		"gem":
			ops.append(
				_polygon(
					[
						Vector2(cx, cy - 8 * s),
						Vector2(cx + 7 * s, cy - 2 * s),
						Vector2(cx, cy + 8 * s),
						Vector2(cx - 7 * s, cy - 2 * s)
					],
					color
				)
			)
			ops.append(
				_line(
					Vector2(cx - 7 * s, cy - 2 * s),
					Vector2(cx + 7 * s, cy - 2 * s),
					[255, 255, 255],
					1
				)
			)
		"trophy":
			ops.append(
				_polygon(
					[
						Vector2(cx - 7 * s, cy - 8 * s),
						Vector2(cx + 7 * s, cy - 8 * s),
						Vector2(cx + 5 * s, cy),
						Vector2(cx, cy + 4 * s),
						Vector2(cx - 5 * s, cy)
					],
					color
				)
			)
			ops.append(_line(Vector2(cx, cy + 4 * s), Vector2(cx, cy + 7 * s), color, 2))
			ops.append(
				_line(Vector2(cx - 5 * s, cy + 9 * s), Vector2(cx + 5 * s, cy + 9 * s), color, 2)
			)
			ops.append(
				_arc(UiTheme.rect(cx - 10 * s, cy - 8 * s, 5 * s, 7 * s), color, 1.4, 4.6, 2)
			)
			ops.append(
				_arc(UiTheme.rect(cx + 5 * s, cy - 8 * s, 5 * s, 7 * s), color, -1.4, 1.6, 2)
			)
		"shield":
			ops.append(
				_polygon(
					[
						Vector2(cx, cy - 9 * s),
						Vector2(cx + 8 * s, cy - 5 * s),
						Vector2(cx + 8 * s, cy + 3 * s),
						Vector2(cx, cy + 9 * s),
						Vector2(cx - 8 * s, cy + 3 * s),
						Vector2(cx - 8 * s, cy - 5 * s)
					],
					color
				)
			)
		"upload":
			ops.append(_line(Vector2(cx, cy + 8 * s), Vector2(cx, cy - 6 * s), color, 2))
			ops.append(
				_polygon(
					[
						Vector2(cx - 5 * s, cy - 2 * s),
						Vector2(cx + 5 * s, cy - 2 * s),
						Vector2(cx, cy - 8 * s)
					],
					color
				)
			)
			ops.append(
				_line(Vector2(cx - 7 * s, cy + 8 * s), Vector2(cx + 7 * s, cy + 8 * s), color, 2)
			)
		"download":
			ops.append(_line(Vector2(cx, cy - 8 * s), Vector2(cx, cy + 6 * s), color, 2))
			ops.append(
				_polygon(
					[
						Vector2(cx - 5 * s, cy + 2 * s),
						Vector2(cx + 5 * s, cy + 2 * s),
						Vector2(cx, cy + 8 * s)
					],
					color
				)
			)
			ops.append(
				_line(Vector2(cx - 7 * s, cy + 8 * s), Vector2(cx + 7 * s, cy + 8 * s), color, 2)
			)


static func _polygon(points: Array, color: Array) -> Dictionary:
	var rows: Array = []
	for point: Vector2 in points:
		rows.append([point.x, point.y])
	return {"op": "polygon", "color": color, "points": rows, "width": 0}


static func _circle(center: Vector2, radius: float, color: Array, width := 0) -> Dictionary:
	return {
		"op": "circle",
		"color": color,
		"center": [center.x, center.y],
		"radius": radius,
		"width": width
	}


static func _rect(rect: Rect2i, color: Array, width := 0, radius := 0) -> Dictionary:
	return {
		"op": "rect",
		"color": color,
		"rect": UiTheme.rect_row(rect),
		"width": width,
		"radius": radius
	}


static func _line(start: Vector2, end: Vector2, color: Array, width := 1) -> Dictionary:
	return {
		"op": "line",
		"color": color,
		"start": [start.x, start.y],
		"end": [end.x, end.y],
		"width": width
	}


static func _arc(rect: Rect2i, color: Array, start: float, end: float, width := 1) -> Dictionary:
	return {
		"op": "arc",
		"color": color,
		"rect": UiTheme.rect_row(rect),
		"start": start,
		"end": end,
		"width": width
	}
