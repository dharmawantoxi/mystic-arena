class_name UiThemeComponents
extends RefCounted

## Layout/draw-command port of ui_theme components. The returned `ops` list is
## compared with the pygame oracle; UiThemeDraw renders it on a CanvasItem.


static func panel(
	rect: Rect2i,
	border: Array,
	fill_top: Array,
	fill_bottom: Array,
	ticks := true,
	shadow := true,
	border_w := 1
) -> Dictionary:
	var ops: Array = []
	var cheap := UiTheme.cheap_alpha()
	var radius := UiTheme.integer("panel.radius")
	if shadow:
		if cheap:
			ops.append(
				_shadow(
					rect.size.x,
					rect.size.y,
					radius,
					110,
					4,
					Vector2(rect.position) + _vec("panel.shadow_offset")
				)
			)
		else:
			ops.append(
				_rect(UiTheme.moved(rect, 3, 4), UiTheme.value("panel.shadow_color"), 0, radius)
			)
	if cheap:
		ops.append(
			_gradient(
				rect.size.x, rect.size.y, fill_top, fill_bottom, radius, Vector2(rect.position)
			)
		)
	else:
		ops.append(_rect(rect, UiTheme.palette.get("panel_fill", []), 0, radius))
	ops.append(_rect(rect, border, border_w, radius))
	if ticks:
		ops.append(_ticks(rect, UiTheme.palette.get("gold", [])))
	return _done(ops, {}, null)


static func panel_solid(rect: Rect2i, border: Array) -> Dictionary:
	var radius := UiTheme.integer("panel.radius")
	var ops: Array = [
		_rect(rect, UiTheme.palette.get("panel_fill", []), 0, radius),
		_rect(rect, border, 1, radius),
		_ticks(rect, UiTheme.palette.get("gold", [])),
	]
	return _done(ops, {}, null)


static func button(
	bid: String,
	label: String,
	cx: float,
	cy: float,
	accent: Array,
	font_size: int,
	measure: Callable,
	opts: Dictionary = {}
) -> Dictionary:
	var ops: Array = []
	var btns: Dictionary = {}
	var cheap := UiTheme.cheap_alpha()
	var w := int(opts.get("w", 300))
	var h := int(opts.get("h", 50))
	var hover := bool(opts.get("hover", false))
	var icon: Variant = opts.get("icon")
	var letter_gap := bool(opts.get("letter_gap", true))
	var base := UiTheme.rect(cx - floori(w / 2.0), cy - floori(h / 2.0), w, h)
	var rect := base
	if hover:
		var inflate: Array = UiTheme.value("button.hover_inflate")
		rect = UiTheme.inflate(base, int(inflate[0]), int(inflate[1]))
	if hover:
		if cheap:
			var pad: Array = UiTheme.value("button.glow_pad")
			ops.append(
				_radial(
					rect.size.x + int(pad[0]),
					rect.size.y + int(pad[1]),
					accent,
					UiTheme.integer("button.glow_alpha"),
					Vector2(rect.position) + _vec("button.glow_offset")
				)
			)
		else:
			var cheap_inflate: Array = UiTheme.value("button.cheap_glow_inflate")
			ops.append(
				_rect(
					UiTheme.inflate(rect, int(cheap_inflate[0]), int(cheap_inflate[1])),
					accent,
					UiTheme.integer("button.cheap_glow_width"),
					UiTheme.integer("button.cheap_glow_radius")
				)
			)
	if cheap:
		ops.append(
			_shadow(
				rect.size.x,
				rect.size.y,
				12,
				110,
				4,
				Vector2(rect.position) + _vec("button.shadow_offset")
			)
		)
	var top: Array = (
		UiTheme.value("button.top_hover") if hover else UiTheme.value("button.top_normal")
	)
	var bot: Array = (
		UiTheme.value("button.bot_hover") if hover else UiTheme.value("button.bot_normal")
	)
	if cheap:
		ops.append(_gradient(rect.size.x, rect.size.y, top, bot, 12, Vector2(rect.position)))
	else:
		ops.append(_rect(rect, top, 0, 12))
	var inset := UiTheme.integer("button.highlight_inset")
	ops.append(
		_line(
			Vector2(rect.position.x + inset, rect.position.y + 1),
			Vector2(rect.end.x - inset, rect.position.y + 1),
			UiTheme.value("button.highlight"),
			1
		)
	)
	var ar: Array = UiTheme.value("button.accent_rect")
	ops.append(
		_rect(
			UiTheme.rect(
				rect.position.x + ar[0], rect.position.y + ar[1], ar[2], rect.size.y - ar[3]
			),
			accent,
			0,
			UiTheme.integer("button.accent_radius")
		)
	)
	if cheap:
		var agr: Array = UiTheme.value("button.accent_glow_rect")
		var glow_color := accent.duplicate()
		glow_color.append(UiTheme.integer("button.accent_glow_alpha"))
		ops.append(
			_rect(
				UiTheme.rect(
					rect.position.x + agr[0], rect.position.y + agr[1], agr[2], rect.size.y - agr[3]
				),
				glow_color,
				0,
				UiTheme.integer("button.accent_glow_radius")
			)
		)
	ops.append(
		_rect(
			rect, accent if hover else UiTheme.palette.get("edge_gold", []), 2 if hover else 1, 12
		)
	)
	ops.append(_ticks(rect, UiTheme.palette.get("gold", [])))
	if icon != null:
		var badge := Vector2(
			rect.position.x + UiTheme.integer("button.badge_center_x"), UiTheme.center(rect).y
		)
		var badge_radius := UiTheme.integer("button.badge_radius")
		ops.append(_circle(badge, badge_radius, UiTheme.value("button.badge_bg")))
		ops.append(_circle(badge, badge_radius, accent, UiTheme.integer("button.badge_width")))
		ops.append(_icon(str(icon), badge, accent, UiTheme.number("button.icon_scale")))
	var size := int(opts.get("font_size_override", 0))
	if size <= 0:
		size = font_size
	var text := UiThemeText.letter(label) if letter_gap else label
	var text_cx: float
	if icon != null:
		var tw := float(measure.call(text))
		var left_min := rect.position.x + UiTheme.integer("button.label_left")
		var right_max := rect.end.x - UiTheme.integer("button.label_right")
		text_cx = base.position.x + floori(w / 2.0) + UiTheme.integer("button.label_shift")
		if text_cx - tw / 2.0 < left_min:
			text_cx = left_min + tw / 2.0
		if text_cx + tw / 2.0 > right_max:
			text_cx = right_max - tw / 2.0
		if text_cx - tw / 2.0 < left_min:
			text_cx = (left_min + right_max) / 2.0
	else:
		text_cx = UiTheme.center(rect).x
	ops.append(
		_text(
			text,
			UiTheme.palette.get("text_white", []),
			Vector2(text_cx, UiTheme.center(rect).y),
			null,
			true,
			[2, 2],
			size
		)
	)
	btns[bid] = UiTheme.rect_row(rect)
	return _done(ops, btns, UiTheme.rect_row(rect))


static func pill(
	bid: String,
	label: String,
	rect: Rect2i,
	kind: String,
	font_size: int,
	_measure: Callable,
	opts: Dictionary = {}
) -> Dictionary:
	var ops: Array = []
	var btns: Dictionary = {}
	var cheap := UiTheme.cheap_alpha()
	var hover := bool(opts.get("hover", false))
	var enabled := bool(opts.get("enabled", true))
	var icon: Variant = opts.get("icon")
	var letter_gap := bool(opts.get("letter_gap", true))
	var colors: Dictionary = UiTheme.value("pill.colors")
	var row: Array = colors.get(kind, colors.get("neutral", []))
	var top: Array = row[0].duplicate()
	var bot: Array = row[1].duplicate()
	var edge: Array = row[2]
	var tcol: Array = row[3]
	if hover and enabled:
		top = UiTheme.lighten(top, UiTheme.integer("pill.hover_top"))
		bot = UiTheme.lighten(bot, UiTheme.integer("pill.hover_bot"))
	var radius := UiTheme.integer("pill.radius")
	if cheap:
		ops.append(_gradient(rect.size.x, rect.size.y, top, bot, radius, Vector2(rect.position)))
	else:
		ops.append(_rect(rect, top, 0, radius))
	ops.append(_rect(rect, edge, 2 if enabled else 1, radius))
	if hover and enabled and cheap:
		var pad: Array = UiTheme.value("pill.glow_pad")
		ops.append(
			_radial(
				rect.size.x + int(pad[0]),
				rect.size.y + int(pad[1]),
				edge,
				UiTheme.integer("pill.glow_alpha"),
				Vector2(rect.position) + _vec("pill.glow_offset")
			)
		)
	var cx := UiTheme.center(rect).x
	if icon != null and str(icon) != "":
		var icon_x := rect.position.x + UiTheme.integer("pill.icon_x")
		ops.append(
			_icon(
				str(icon),
				Vector2(icon_x, UiTheme.center(rect).y),
				edge,
				UiTheme.number("pill.icon_scale")
			)
		)
		cx = icon_x + floori((rect.size.x - 22) / 2.0)
	var text := UiThemeText.letter(label) if letter_gap else label
	ops.append(
		_text(
			text,
			tcol if enabled else UiTheme.palette.get("text_faint", []),
			Vector2(cx, UiTheme.center(rect).y),
			null,
			true,
			[2, 2],
			font_size
		)
	)
	if enabled:
		btns[bid] = UiTheme.rect_row(rect)
	return _done(ops, btns, UiTheme.rect_row(rect))


static func chip(
	pos: Vector2,
	text: String,
	accent: Array,
	font_size: int,
	measure: Callable,
	opts: Dictionary = {}
) -> Dictionary:
	var ops: Array = []
	var cheap := UiTheme.cheap_alpha()
	var icon: Variant = opts.get("icon")
	var value: Variant = opts.get("value")
	var align := str(opts.get("align", "left"))
	var spaced := UiThemeText.letter(text)
	var total_w := UiTheme.integer("chip.base_w")
	if icon != null and str(icon) != "":
		total_w += UiTheme.integer("chip.icon_w")
	total_w += int(measure.call(spaced))
	if value != null:
		total_w += UiTheme.integer("chip.value_gap") + int(measure.call(str(value)))
	var h := UiTheme.integer("chip.height")
	var x := pos.x - total_w if align == "right" else pos.x
	var rect := UiTheme.rect(x, pos.y, total_w, h)
	if cheap:
		ops.append(
			_gradient(
				rect.size.x,
				h,
				UiTheme.value("chip.top"),
				UiTheme.value("chip.bottom"),
				floori(h / 2.0),
				Vector2(rect.position)
			)
		)
	else:
		ops.append(_rect(rect, UiTheme.value("chip.cheap_fill"), 0, floori(h / 2.0)))
	ops.append(_rect(rect, accent, 1, floori(h / 2.0)))
	var ix := rect.position.x + UiTheme.integer("chip.icon_x")
	var iy := UiTheme.center(rect).y
	if icon != null and str(icon) != "":
		var icon_color: Array = opts.get("icon_color") if opts.get("icon_color") != null else accent
		ops.append(_icon(str(icon), Vector2(ix, iy), icon_color, UiTheme.number("chip.icon_scale")))
		ix += UiTheme.integer("chip.icon_w")
	ops.append(
		_text(
			spaced,
			UiTheme.palette.get("text_body", []),
			null,
			[ix, rect.position.y + UiTheme.integer("chip.text_y")],
			false,
			[2, 2],
			font_size
		)
	)
	ix += int(measure.call(spaced))
	if value != null:
		ix += UiTheme.integer("chip.value_gap")
		var value_color: Array = (
			opts.get("value_color") if opts.get("value_color") != null else accent
		)
		ops.append(
			_text(
				str(value),
				value_color,
				null,
				[ix, rect.position.y + UiTheme.integer("chip.text_y")],
				false,
				[2, 2],
				font_size
			)
		)
	return _done(ops, {}, UiTheme.rect_row(rect))


static func section_header(
	x: float,
	y: float,
	title: String,
	icon_name: String,
	color: Array,
	font_size: int,
	measure: Callable,
	rule_w := 240
) -> Dictionary:
	var ops: Array = []
	var io: Array = UiTheme.value("header.icon_offset")
	ops.append(
		_icon(icon_name, Vector2(x + io[0], y + io[1]), color, UiTheme.number("header.icon_scale"))
	)
	var text_x := x + UiTheme.integer("header.text_x")
	ops.append(_text(UiThemeText.letter(title), color, null, [text_x, y], false, [2, 2], font_size))
	var tw := int(measure.call(title)) + UiTheme.integer("header.text_x")
	var rule_x := x + tw + UiTheme.integer("header.rule_gap")
	ops.append(
		_line(
			Vector2(rule_x, y + UiTheme.integer("header.rule_y")),
			Vector2(rule_x + rule_w, y + UiTheme.integer("header.rule_y")),
			color,
			1
		)
	)
	ops.append(
		_line(
			Vector2(text_x, y + UiTheme.integer("header.underline_y")),
			Vector2(rule_x, y + UiTheme.integer("header.underline_y")),
			UiTheme.dim(color, UiTheme.number("header.dim_factor")),
			1
		)
	)
	return _done(ops, {}, y + UiTheme.integer("header.return_y"))


static func toggle(
	bid: String, rect: Rect2i, is_on: bool, font_size: int, hover := false
) -> Dictionary:
	var ops: Array = []
	var btns: Dictionary = {}
	var cheap := UiTheme.cheap_alpha()
	var prefix := "on" if is_on else "off"
	var suffix := "_hover" if hover else ""
	var top: Array = UiTheme.value("toggle.%s_top%s" % [prefix, suffix])
	var bot: Array = UiTheme.value("toggle.%s_bot%s" % [prefix, suffix])
	var edge: Array = UiTheme.value("toggle.%s_edge%s" % [prefix, suffix])
	var radius := floori(rect.size.y / 2.0)
	if cheap:
		ops.append(_gradient(rect.size.x, rect.size.y, top, bot, radius, Vector2(rect.position)))
	else:
		ops.append(_rect(rect, top, 0, radius))
	ops.append(_rect(rect, edge, 2, radius))
	var knob := UiTheme.integer("toggle.knob")
	var inset := UiTheme.integer("toggle.knob_inset")
	var kx := rect.end.x - knob - inset if is_on else rect.position.x + inset
	var ky := UiTheme.center(rect).y
	ops.append(
		_circle(Vector2(kx + 1, ky + 2), floori(knob / 2.0), UiTheme.value("toggle.knob_shadow"))
	)
	ops.append(_circle(Vector2(kx, ky), floori(knob / 2.0), UiTheme.value("toggle.knob_fill")))
	ops.append(_circle(Vector2(kx, ky), floori(knob / 2.0), edge, 1))
	var lab := "ON" if is_on else "OFF"
	var lx := (
		UiTheme.center(rect).x
		+ (
			-UiTheme.integer("toggle.label_offset")
			if is_on
			else UiTheme.integer("toggle.label_offset")
		)
	)
	var tcol: Array = (
		UiTheme.value("toggle.on_text") if is_on else UiTheme.palette.get("text_body", [])
	)
	ops.append(_text(lab, tcol, Vector2(lx, ky), null, false, [2, 2], font_size))
	btns[bid] = UiTheme.rect_row(rect)
	return _done(ops, btns, UiTheme.rect_row(rect))


static func slider(x: float, y: float, w: float, value: float, knob_hover := false) -> Dictionary:
	var ops: Array = []
	var cheap := UiTheme.cheap_alpha()
	var track_h := UiTheme.integer("slider.track_h")
	var bar := UiTheme.rect(x, y, w, track_h)
	var radius := UiTheme.integer("slider.radius")
	ops.append(_rect(bar, UiTheme.value("slider.track_color"), 0, radius))
	var fill_w := int(w * clampf(value, 0.0, 1.0))
	if fill_w > UiTheme.integer("slider.min_fill"):
		if cheap:
			ops.append(
				_gradient(
					fill_w,
					track_h,
					UiTheme.palette.get("gold_bright", []),
					UiTheme.value("slider.fill_bottom"),
					radius,
					Vector2(x, y)
				)
			)
		else:
			ops.append(
				_rect(
					UiTheme.rect(x, y, fill_w, track_h), UiTheme.palette.get("gold", []), 0, radius
				)
			)
	ops.append(_rect(bar, UiTheme.value("slider.border_color"), 1, radius))
	var kx := x + fill_w
	var ky := y + floori(track_h / 2.0)
	if knob_hover and cheap:
		var glow := UiTheme.integer("slider.glow_size")
		ops.append(
			_radial(
				glow,
				glow,
				UiTheme.palette.get("gold", []),
				UiTheme.integer("slider.glow_alpha"),
				Vector2(kx - glow / 2.0, ky - glow / 2.0)
			)
		)
	ops.append(
		_circle(
			Vector2(kx, ky),
			UiTheme.integer("slider.knob_outer"),
			UiTheme.value("slider.knob_shadow")
		)
	)
	ops.append(
		_circle(
			Vector2(kx, ky), UiTheme.integer("slider.knob_inner"), UiTheme.value("slider.knob_fill")
		)
	)
	ops.append(
		_circle(
			Vector2(kx, ky),
			UiTheme.integer("slider.knob_inner"),
			UiTheme.palette.get("gold", []),
			2
		)
	)
	return _done(ops, {}, kx)


static func corner_ticks(rect: Rect2i, color: Array, length := 11, width := 2, inset := 2) -> Array:
	var ops: Array = []
	var corners := [
		[rect.position.x + inset, rect.position.y + inset, 1, 1],
		[rect.end.x - inset, rect.position.y + inset, -1, 1],
		[rect.position.x + inset, rect.end.y - inset, 1, -1],
		[rect.end.x - inset, rect.end.y - inset, -1, -1],
	]
	for corner: Array in corners:
		var ax: int = corner[0]
		var ay: int = corner[1]
		var dx: int = corner[2]
		var dy: int = corner[3]
		ops.append(_line(Vector2(ax, ay), Vector2(ax + dx * length, ay), color, width))
		ops.append(_line(Vector2(ax, ay), Vector2(ax, ay + dy * length), color, width))
	return ops


static func _done(ops: Array, btns: Dictionary, result: Variant) -> Dictionary:
	return {"ops": ops, "btns": btns, "result": result}


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


static func _shadow(
	w: int, h: int, radius: int, alpha: int, spread: int, pos: Vector2
) -> Dictionary:
	return {
		"op": "shadow",
		"size": [w + spread * 2, h + spread * 2],
		"radius": radius,
		"alpha": alpha,
		"spread": spread,
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
