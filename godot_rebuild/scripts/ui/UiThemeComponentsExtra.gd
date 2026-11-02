class_name UiThemeComponentsExtra
extends RefCounted

## Remaining ui_theme components: settings cycler, tabs, screen title, back
## button, scroll indicator, and HP/progress bars.


static func option_cycler(
	id_base: String,
	label: String,
	value: String,
	x: float,
	y: float,
	width: float,
	label_size: int,
	value_size: int,
	measure: Callable,
	hover: Variant = null
) -> Dictionary:
	var ops: Array = []
	var btns: Dictionary = {}
	var cheap := UiTheme.cheap_alpha()
	ops.append(
		_text(
			label,
			UiTheme.palette.get("text_body", []),
			null,
			[x, y + UiTheme.integer("cycler.label_y")],
			false,
			[2, 2],
			label_size
		)
	)
	var vw := maxi(
		UiTheme.integer("cycler.min_vw"),
		int(measure.call(value)) + UiTheme.integer("cycler.value_pad")
	)
	vw = mini(vw, int(width) - UiTheme.integer("cycler.width_reserve"))
	var vh := UiTheme.integer("cycler.vh")
	var vx := x + width - vw - UiTheme.integer("cycler.right_reserve")
	var vy := y + UiTheme.integer("cycler.vy")
	var box := UiTheme.rect(vx, vy, vw, vh)
	var box_hover: bool = hover == id_base + "_prev" or hover == id_base + "_next"
	var radius := UiTheme.integer("cycler.radius")
	if cheap:
		ops.append(
			_gradient(
				box.size.x,
				box.size.y,
				UiTheme.value("cycler.top"),
				UiTheme.value("cycler.bottom"),
				radius,
				Vector2(box.position)
			)
		)
	else:
		ops.append(_rect(box, UiTheme.value("cycler.cheap_fill"), 0, radius))
	ops.append(
		_rect(
			box,
			UiTheme.palette.get("edge_gold", []) if box_hover else UiTheme.value("cycler.edge"),
			1,
			radius
		)
	)
	ops.append(
		_text(
			value,
			UiTheme.palette.get("gold_text", []),
			UiTheme.center(box),
			null,
			false,
			[2, 2],
			value_size
		)
	)
	for side: String in ["l", "r"]:
		var bid := id_base + ("_prev" if side == "l" else "_next")
		var icon := "chevron_l" if side == "l" else "chevron_r"
		var bw := UiTheme.integer("cycler.chevron_w")
		var gap := UiTheme.integer("cycler.chevron_gap")
		var bx := box.position.x - bw - gap if side == "l" else box.end.x + gap
		var b := UiTheme.rect(bx, vy, bw, vh)
		var bh: bool = hover == bid
		var top: Array = (
			UiTheme.value("cycler.chevron_top_hover") if bh else UiTheme.value("cycler.chevron_top")
		)
		if cheap:
			ops.append(
				_gradient(
					bw, vh, top, UiTheme.value("cycler.chevron_bottom"), radius, Vector2(b.position)
				)
			)
		else:
			ops.append(_rect(b, top, 0, radius))
		ops.append(
			_rect(
				b,
				UiTheme.value("cycler.chevron_edge_hover") if bh else UiTheme.value("cycler.edge"),
				1,
				radius
			)
		)
		ops.append(
			_icon(
				icon,
				UiTheme.center(b),
				UiTheme.value("cycler.chevron_icon"),
				UiTheme.number("cycler.icon_scale")
			)
		)
		btns[bid] = UiTheme.rect_row(b)
	return {"ops": ops, "btns": btns, "result": vy + vh}


static func tab_width(label: String, measure: Callable, min_w := 150) -> int:
	return maxi(
		min_w, int(measure.call(UiThemeText.letter(label))) + UiTheme.integer("tab.padding")
	)


static func tab(
	bid: String,
	rect: Rect2i,
	label: String,
	accent: Array,
	font_size: int,
	active: bool,
	hover := false
) -> Dictionary:
	var ops: Array = []
	var btns: Dictionary = {}
	var cheap := UiTheme.cheap_alpha()
	var radius := UiTheme.integer("tab.radius")
	var tcol: Array
	if active:
		var top: Array = UiTheme.value("tab.active_top")
		var bot: Array = UiTheme.value("tab.active_bot")
		if cheap:
			ops.append(
				_gradient(rect.size.x, rect.size.y, top, bot, radius, Vector2(rect.position))
			)
		else:
			ops.append(_rect(rect, top, 0, radius))
		ops.append(_rect(rect, accent, 2, radius))
		var u: Array = UiTheme.value("tab.underline")
		ops.append(
			_rect(
				UiTheme.rect(rect.position.x + u[0], rect.end.y - u[1], rect.size.x - u[2], u[3]),
				accent,
				0,
				UiTheme.integer("tab.underline_radius")
			)
		)
		tcol = accent
	else:
		var top: Array = (
			UiTheme.value("tab.hover_top") if hover else UiTheme.value("tab.normal_top")
		)
		var bot: Array = (
			UiTheme.value("tab.hover_bot") if hover else UiTheme.value("tab.normal_bot")
		)
		if cheap:
			ops.append(
				_gradient(rect.size.x, rect.size.y, top, bot, radius, Vector2(rect.position))
			)
		else:
			ops.append(_rect(rect, top, 0, radius))
		ops.append(
			_rect(
				rect,
				UiTheme.value("tab.hover_edge") if hover else UiTheme.value("tab.normal_edge"),
				1,
				radius
			)
		)
		tcol = (
			UiTheme.palette.get("text_body", []) if hover else UiTheme.palette.get("text_dim", [])
		)
	ops.append(
		_text(UiThemeText.letter(label), tcol, UiTheme.center(rect), null, false, [2, 2], font_size)
	)
	btns[bid] = UiTheme.rect_row(rect)
	return {"ops": ops, "btns": btns, "result": UiTheme.rect_row(rect)}


static func screen_title(
	text: String,
	cx: float,
	y: float,
	glow := true,
	sub: Variant = null,
	sub_color: Variant = null,
	ornament := true,
	measure: Callable = Callable()
) -> Dictionary:
	var ops: Array = []
	var cheap := UiTheme.cheap_alpha()
	var font_size := UiTheme.integer("title.font_size")
	if glow and cheap:
		var size: Array = UiTheme.value("title.glow_size")
		ops.append(
			_radial(
				int(size[0]),
				int(size[1]),
				UiTheme.value("title.glow_color"),
				UiTheme.integer("title.glow_alpha"),
				Vector2(cx, y) + _vec("title.glow_offset")
			)
		)
	ops.append(
		{
			"op": "outline",
			"text": text,
			"center": [cx, y],
			"outline": UiTheme.value("text.outline_color"),
			"width": 2,
			"body_top": null,
			"body_bottom": null,
			"font_size": font_size
		}
	)
	var fy := y + UiTheme.integer("title.ornament_y")
	if ornament:
		var outer := UiTheme.integer("title.line_outer")
		var inner := UiTheme.integer("title.line_inner")
		var edge: Array = UiTheme.palette.get("edge_gold", [])
		ops.append(_line(Vector2(cx - outer, fy), Vector2(cx - inner, fy), edge, 2))
		ops.append(_line(Vector2(cx + inner, fy), Vector2(cx + outer, fy), edge, 2))
		var dx := UiTheme.integer("title.diamond_x")
		var dy := UiTheme.integer("title.diamond_y")
		ops.append(
			_polygon(
				[
					Vector2(cx - dx, fy),
					Vector2(cx, fy - dy),
					Vector2(cx + dx, fy),
					Vector2(cx, fy + dy)
				],
				UiTheme.palette.get("gold", [])
			)
		)
		var dot_x := UiTheme.integer("title.dot_x")
		var dot_r := UiTheme.integer("title.dot_radius")
		ops.append(_circle(Vector2(cx - dot_x, fy), dot_r, UiTheme.palette.get("gold_bright", [])))
		ops.append(_circle(Vector2(cx + dot_x, fy), dot_r, UiTheme.palette.get("gold_bright", [])))
	if sub != null and str(sub) != "":
		var sub_size := UiTheme.integer("title.sub_font_size")
		var spaced := UiThemeText.letter(str(sub))
		var sub_w := (
			int(measure.call(spaced)) if measure.is_valid() else spaced.length() * sub_size / 2
		)
		var pad := UiTheme.integer("title.sub_pad")
		var plate := UiTheme.rect(
			cx - floori((sub_w + pad) / 2.0),
			fy + UiTheme.integer("title.sub_y"),
			sub_w + pad,
			UiTheme.integer("title.sub_h")
		)
		var radius := UiTheme.integer("title.sub_radius")
		if cheap:
			ops.append(
				_gradient(
					plate.size.x,
					plate.size.y,
					UiTheme.value("title.sub_top"),
					UiTheme.value("title.sub_bottom"),
					radius,
					Vector2(plate.position)
				)
			)
		else:
			ops.append(_rect(plate, UiTheme.value("title.sub_cheap"), 0, radius))
		ops.append(_rect(plate, UiTheme.palette.get("edge_gold", []), 1, radius))
		var ticks: Array = UiTheme.value("title.sub_ticks")
		ops.append(
			_ticks(
				plate, UiTheme.palette.get("gold", []), int(ticks[0]), int(ticks[1]), int(ticks[2])
			)
		)
		var color: Array = sub_color if sub_color != null else UiTheme.palette.get("cyan_soft", [])
		ops.append(
			{
				"op": "text",
				"text": spaced,
				"color": color,
				"shadow": false,
				"center": [UiTheme.center(plate).x, UiTheme.center(plate).y]
			}
		)
	return {"ops": ops, "btns": {}, "result": null}


static func back_button(
	bid: String, cx: float, y: float, hover := false, font_size := 0, measure: Callable = Callable()
) -> Dictionary:
	var size := font_size if font_size > 0 else UiTheme.integer("back.font_size")
	var w := UiTheme.integer("back.width")
	var h := UiTheme.integer("back.height")
	var rect := UiTheme.rect(cx - floori(w / 2.0), y - floori(h / 2.0), w, h)
	return UiThemeComponents.pill(
		bid, "BACK", rect, "neutral", size, measure, {"hover": hover, "icon": "back"}
	)


static func scroll_indicator(
	x: float, y: float, height: float, scroll_pos: float, max_scroll: float, width := 6
) -> Dictionary:
	var ops: Array = []
	var cheap := UiTheme.cheap_alpha()
	var radius := UiTheme.integer("scroll.radius")
	var track := UiTheme.rect(x, y, width, height)
	ops.append(_rect(track, UiTheme.value("scroll.track_color"), 0, radius))
	if max_scroll > 0:
		var ratio := height / (height + max_scroll)
		var thumb_h := maxi(UiTheme.integer("scroll.min_thumb"), int(height * ratio))
		var thumb_y := y + int((height - thumb_h) * (scroll_pos / max_scroll))
		if cheap:
			ops.append(
				_gradient(
					width,
					thumb_h,
					UiTheme.palette.get("gold_bright", []),
					UiTheme.value("scroll.fill_bottom"),
					radius,
					Vector2(x, thumb_y)
				)
			)
		else:
			ops.append(
				_rect(
					UiTheme.rect(x, thumb_y, width, thumb_h),
					UiTheme.palette.get("gold", []),
					0,
					radius
				)
			)
	return {"ops": ops, "btns": {}, "result": UiTheme.rect_row(track)}


static func hp_bar(
	x: float, y: float, w: float, h: float, ratio: float, color: Variant = null
) -> Dictionary:
	var ops: Array = []
	var cheap := UiTheme.cheap_alpha()
	var fill: Array = color if color != null else UiTheme.palette.get("green", [])
	var r := UiTheme.rect(x, y, w, h)
	var radius := floori(h / 2.0)
	ops.append(_rect(r, UiTheme.value("hp.track_color"), 0, radius))
	var fw := int(w * clampf(ratio, 0.0, 1.0))
	if fw > UiTheme.integer("hp.min_fill"):
		var light := UiTheme.lighten(fill, UiTheme.integer("hp.lighten"))
		if cheap:
			ops.append(_gradient(fw, int(h), light, fill, radius, Vector2(x, y)))
		else:
			ops.append(_rect(UiTheme.rect(x, y, fw, h), fill, 0, radius))
	ops.append(_rect(r, UiTheme.value("hp.border_color"), 1, radius))
	return {"ops": ops, "btns": {}, "result": null}


static func progress_bar(
	x: float, y: float, w: float, frac: float, color: Variant = null, h := 8
) -> Dictionary:
	var ops: Array = []
	var cheap := UiTheme.cheap_alpha()
	var fill: Array = color if color != null else UiTheme.palette.get("gold", [])
	var r := UiTheme.rect(x, y, w, h)
	var radius := floori(h / 2.0)
	ops.append(_rect(r, UiTheme.value("progress.track_color"), 0, radius))
	var fw := int(w * clampf(frac, 0.0, 1.0))
	if fw > UiTheme.integer("progress.min_fill"):
		var light := UiTheme.lighten(fill, UiTheme.integer("progress.lighten"))
		if cheap:
			ops.append(_gradient(fw, h, light, fill, radius, Vector2(x, y)))
		else:
			ops.append(_rect(UiTheme.rect(x, y, fw, h), fill, 0, radius))
	ops.append(_rect(r, UiTheme.value("progress.border_color"), 1, radius))
	return {"ops": ops, "btns": {}, "result": null}


static func _vec(path: String) -> Vector2:
	var row: Array = UiTheme.value(path)
	return Vector2(float(row[0]), float(row[1]))


static func _gradient(
	w: int, h: int, top: Array, bottom: Array, radius: int, pos: Vector2
) -> Dictionary:
	return {
		"op": "gradient",
		"size": [maxi(2, w), maxi(2, h)],
		"top": top,
		"bottom": bottom,
		"radius": radius,
		"pos": [pos.x, pos.y]
	}


static func _radial(w: int, h: int, color: Array, alpha: int, pos: Vector2) -> Dictionary:
	return {
		"op": "radial",
		"size": [maxi(8, w), maxi(8, h)],
		"color": color,
		"alpha": alpha,
		"pos": [pos.x, pos.y]
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


static func _circle(center: Vector2, radius: float, color: Array, width := 0) -> Dictionary:
	return {
		"op": "circle",
		"color": color,
		"center": [center.x, center.y],
		"radius": radius,
		"width": width
	}


static func _polygon(points: Array, color: Array) -> Dictionary:
	var rows: Array = []
	for point: Vector2 in points:
		rows.append([point.x, point.y])
	return {"op": "polygon", "color": color, "points": rows, "width": 0}


static func _icon(name: String, center: Vector2, color: Array, scale: float) -> Dictionary:
	return {
		"op": "icon", "name": name, "center": [center.x, center.y], "color": color, "scale": scale
	}


static func _ticks(rect: Rect2i, color: Array, length := 11, width := 2, inset := 2) -> Dictionary:
	return {
		"op": "ticks",
		"rect": UiTheme.rect_row(rect),
		"color": color,
		"length": length,
		"width": width,
		"inset": inset
	}


static func _text(
	text: String,
	color: Array,
	center: Variant,
	topleft: Variant,
	shadow: bool,
	offset: Array,
	font_size: int
) -> Dictionary:
	return {
		"op": "text",
		"text": text,
		"color": color,
		"center": [center.x, center.y] if center != null else null,
		"topleft": topleft,
		"shadow": shadow,
		"offset": offset,
		"font_size": font_size
	}
