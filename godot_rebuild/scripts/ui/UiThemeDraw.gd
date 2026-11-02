class_name UiThemeDraw
extends RefCounted

## Renders ui_theme draw commands on any CanvasItem. Geometry/parameters are
## parity-tested; primitive rasterization is native Godot, not pixel-exact pygame.


static func render(canvas: CanvasItem, ops: Array, font: Font, default_size := 24) -> void:
	if not UiTheme.ensure_loaded():
		return
	for op: Dictionary in ops:
		match str(op.op):
			"gradient":
				var size: Array = op.size
				var texture := UiThemeTextures.gradient(
					int(size[0]), int(size[1]), op.top, op.bottom, int(op.radius)
				)
				canvas.draw_texture_rect(
					texture, Rect2(_v2(op.pos), Vector2(float(size[0]), float(size[1]))), false
				)
			"radial":
				var size: Array = op.size
				var texture := UiThemeTextures.radial(
					int(size[0]), int(size[1]), op.color, int(op.alpha)
				)
				canvas.draw_texture_rect(
					texture, Rect2(_v2(op.pos), Vector2(float(size[0]), float(size[1]))), false
				)
			"shadow":
				var size: Array = op.size
				var texture := UiThemeTextures.shadow(
					int(size[0]) - int(op.spread) * 2,
					int(size[1]) - int(op.spread) * 2,
					int(op.radius),
					int(op.alpha),
					int(op.spread)
				)
				canvas.draw_texture_rect(
					texture, Rect2(_v2(op.pos), Vector2(float(size[0]), float(size[1]))), false
				)
			"rect":
				_rect(canvas, _rect2(op.rect), op.color, int(op.width), int(op.radius))
			"line":
				canvas.draw_line(_v2(op.start), _v2(op.end), UiTheme.rgb(op.color), float(op.width))
			"circle":
				canvas.draw_circle(
					_v2(op.center),
					float(op.radius),
					UiTheme.rgb(op.color),
					int(op.width) == 0,
					float(op.width)
				)
			"polygon":
				var points := PackedVector2Array()
				for point: Array in op.points:
					points.append(_v2(point))
				canvas.draw_colored_polygon(points, UiTheme.rgb(op.color))
			"arc":
				_arc(canvas, op)
			"icon":
				render(
					canvas,
					UiThemeIcons.draw_data(str(op.name), _v2(op.center), op.color, float(op.scale)),
					font,
					default_size
				)
			"ticks":
				render(
					canvas,
					UiThemeComponents.corner_ticks(
						_rect2(op.rect), op.color, int(op.length), int(op.width), int(op.inset)
					),
					font,
					default_size
				)
			"text":
				_text(canvas, op, font, default_size)
			"outline":
				_outline(canvas, op, font, default_size)


static func _rect(canvas: CanvasItem, rect: Rect2, color: Array, width: int, radius: int) -> void:
	var style := StyleBoxFlat.new()
	style.bg_color = UiTheme.rgb(color) if width == 0 else Color.TRANSPARENT
	style.border_color = UiTheme.rgb(color)
	style.set_border_width_all(width)
	style.set_corner_radius_all(radius)
	canvas.draw_style_box(style, rect)


static func _text(canvas: CanvasItem, op: Dictionary, font: Font, default_size: int) -> void:
	var size := int(op.get("font_size", default_size))
	var text := str(op.text)
	var metrics := Vector2(
		font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x, font.get_height(size)
	)
	var offset: Array = op.get("offset", [2, 2])
	var blits := UiThemeText.layout(
		metrics, op.get("center"), op.get("topleft"), bool(op.get("shadow", false)), offset
	)
	for blit: Dictionary in blits:
		var color: Array = UiTheme.value("text.shadow_color") if bool(blit.shadow) else op.color
		var pos: Vector2 = blit.pos + Vector2(0, font.get_ascent(size))
		canvas.draw_string(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, UiTheme.rgb(color))


static func _outline(canvas: CanvasItem, op: Dictionary, font: Font, default_size: int) -> void:
	var size := int(op.get("font_size", default_size))
	var text := str(op.text)
	var metrics := Vector2(
		font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x, font.get_height(size)
	)
	var pos := Vector2(float(op.center[0]) - metrics.x / 2.0, float(op.center[1]) - metrics.y / 2.0)
	var baseline := pos + Vector2(0, font.get_ascent(size))
	var width := int(op.get("width", 2))
	for pair: Array in UiThemeText.outline_offsets(width, UiTheme.cheap_alpha()):
		canvas.draw_string(
			font,
			baseline + Vector2(float(pair[0]), float(pair[1])),
			text,
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			size,
			UiTheme.rgb(op.outline)
		)
	var top: Array = (
		op.get("body_top") if op.get("body_top") != null else UiTheme.palette.get("gold_bright", [])
	)
	var bottom: Array = (
		op.get("body_bottom")
		if op.get("body_bottom") != null
		else UiTheme.value("text.outline_body_bottom")
	)
	var body := UiTheme.rgb(top).lerp(UiTheme.rgb(bottom), 0.5)
	canvas.draw_string(font, baseline, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, body)


static func _arc(canvas: CanvasItem, op: Dictionary) -> void:
	var rect := _rect2(op.rect)
	var center := rect.get_center()
	var radii := rect.size / 2.0
	if radii.x <= 0 or radii.y <= 0:
		return
	canvas.draw_set_transform(center, 0.0, radii)
	canvas.draw_arc(
		Vector2.ZERO,
		1.0,
		48,
		-float(op.end),
		-float(op.start),
		UiTheme.rgb(op.color),
		float(op.width) / maxf(radii.x, radii.y)
	)
	canvas.draw_set_transform(Vector2.ZERO)


static func _v2(row: Array) -> Vector2:
	return Vector2(float(row[0]), float(row[1]))


static func _rect2(row: Array) -> Rect2:
	return Rect2(float(row[0]), float(row[1]), float(row[2]), float(row[3]))
