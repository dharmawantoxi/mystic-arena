# gdlint:disable=max-file-lines, max-public-methods
extends RefCounted
## Layer 9cp: native port of the design system `ui_theme.py` (1011 lines).
##
## The 9br bake already owns the pixels of `panel`, `pill`, `button`, `toggle`, `tab`,
## `slider` and the 30 vector icons (`assets/art/ui/*.png` read through `scripts/ui/ui_skin.gd`).
## What was missing is the *geometry and text* half of the module: every helper below emits
## the same op dictionaries `draw_recorder.py` records from the source, so
## `tests/ui_theme_source_oracle.py` can compare case by case.
##
## Op vocabulary (identical to `scripts/ui/*_layout.gd`):
##   rect {rect, color, width, radius} | line {a, b, color, width}
##   circle {center, radius, color, width} | polygon {points, color, width}
##   text {text, size, style, color, pos} (pos = top-left of the source render)
##   vgrad {rect, top, bottom, radius} | radial {rect, color, alpha}
##   shadow {rect, radius, alpha, spread} | icon {name, center, color, scale}
##   gradtext {text, size, style, top, bottom, width, height}
## `vgrad`, `radial`, `shadow`, `icon` and `gradtext` are the baked primitives: their pixels
## come from the sheets (`GradientTexture2D` for slider fills), their geometry is pinned here.
##
##   * `letter`, `tab_width`, `fit_ellipsis`, `math_hyp`, `dim` are pure helpers;
##   * colours come from the 9br manifest (`UiSkin.palette`), so the palette stays single-source;
##   * inline colours the source spells out (button/toggle/tab/chip fills) are literals here and
##     pinned by `tests/fixtures/ui_theme_source.json`;
##   * `cheap_alpha` is a parameter: every layout already receives the adaptive quality flag.

const UiSkin = preload("res://scripts/ui/ui_skin.gd")
const TICK_LENGTH := 11
const TICK_WIDTH := 2
const TICK_INSET := 2
const PANEL_RADIUS := 12
const PILL_RADIUS := 7
const TAB_RADIUS := 8
const TRACK_RADIUS_SLIDER := 4
const SLIDER_TRACK := 8
const SLIDER_KNOB := 11
const SLIDER_KNOB_CORE := 8
const TOGGLE_KNOB := 18
const CHIP_HEIGHT := 30
const CHIP_PAD := 26
const CHIP_ICON_PAD := 22
const CHIP_VALUE_PAD := 10
const TAB_MIN_WIDTH := 150
const TAB_PAD := 36
const OPTION_MIN_BOX := 110
const OPTION_BOX_PAD := 26
const BACK_BUTTON_WIDTH := 200
const BACK_BUTTON_HEIGHT := 42
const SCROLL_MIN_THUMB := 18
const TITLE_GLOW := [620, 150]
const TITLE_GLOW_ALPHA := 46
const TITLE_GLOW_COLOR := [255, 205, 90]
const ORNAMENT_SPAN := 220
const ORNAMENT_GAP := 18
const ORNAMENT_DROP := 52
const ORNAMENT_DIAMOND := 8
const GRAD_TEXT_CACHE_LIMIT := 400
const OUTLINE_DEFAULT := [8, 9, 18]
const BODY_GRAD_TOP := [255, 233, 158]
const BODY_GRAD_BOTTOM := [196, 138, 40]
const SHADOW_TEXT := [5, 6, 12]
const SHADOW_SPREAD := 4
const SHADOW_ALPHA := 110
const FALLBACK_COLOR := [1, 0, 1]
# `pill()` colours table: kind -> [top, bottom, edge, text].
const PILL_KINDS := {
	"gold": [[86, 66, 22], [52, 40, 14], [255, 205, 85], [255, 220, 110]],
	"success": [[38, 122, 60], [22, 74, 36], [112, 226, 132], [214, 255, 222]],
	"danger": [[122, 42, 42], [74, 26, 26], [255, 108, 108], [255, 214, 214]],
	"locked": [[48, 50, 66], [30, 32, 44], [148, 158, 188], [132, 142, 170]],
	"owned": [[34, 96, 48], [20, 56, 30], [112, 226, 132], [190, 250, 200]],
	"neutral": [[52, 58, 84], [30, 35, 56], [148, 158, 188], [198, 207, 230]],
	"violet": [[74, 48, 118], [44, 28, 78], [196, 150, 255], [226, 205, 255]],
	"cyan": [[36, 84, 110], [22, 52, 72], [140, 214, 255], [205, 240, 255]],
}
const NEUTRAL := "neutral"
static var _gradtext_cache: Dictionary = {}


# ── palette ─────────────────────────────────────────────────────────────
## An RGB array for a `ui_theme.py` colour constant, read from the 9br manifest.
static func rgb(name: String) -> Array:
	var color := UiSkin.palette(name)
	if color == UiSkin.NO_COLOR:
		return FALLBACK_COLOR.duplicate()
	return [
		roundi(color.r * 255.0), roundi(color.g * 255.0), roundi(color.b * 255.0)
	]


## `ui_theme.clear_caches()`: drop the title gradient cache and the 9br sheet cache.
static func clear_caches() -> void:
	_gradtext_cache.clear()
	UiSkin.clear_cache()


# ── pure helpers ────────────────────────────────────────────────────────
## `gap.join(list(text))` - pygame has no letter tracking.
static func letter(text: String, gap: String = " ") -> String:
	var characters := PackedStringArray()
	for character in text:
		characters.append(character)
	return gap.join(characters)


## `(x * x + y * y) ** 0.5`.
static func math_hyp(x: float, y: float) -> float:
	return sqrt(x * x + y * y)


## `tuple(int(c * f) for c in color)`.
static func dim(color: Array, factor: float = 0.55) -> Array:
	var out: Array = []
	for channel in color:
		out.append(int(int(channel) * factor))
	return out


## `ui_theme.fit_ellipsis`: truncate to `max_w`, never leaving a dangling dot.
static func fit_ellipsis(
	measure: Callable, text: String, max_w: int, font_size: int, ellipsis: String = "…"
) -> String:
	var current := text
	if int(measure.call(current, font_size).x) <= max_w:
		return current
	while current.length() > 1:
		var candidate := current.substr(0, current.length() - 1)
		if int(measure.call(candidate + ellipsis, font_size).x) <= max_w:
			return candidate + ellipsis
		current = candidate
	return ellipsis


## `ui_theme.tab_width`: auto width that follows the letter-spaced label.
static func tab_width(
	measure: Callable, label: String, font_size: int, min_w: int = TAB_MIN_WIDTH
) -> int:
	return maxi(min_w, int(measure.call(letter(label), font_size).x) + TAB_PAD)


# ── op primitives ───────────────────────────────────────────────────────
static func _rgba(color: Array) -> Array:
	var out: Array = [int(color[0]), int(color[1]), int(color[2])]
	out.append(int(color[3]) if color.size() > 3 else 255)
	return out


static func rect_op(box: Array, color: Array, width: int = 0, radius: int = 0) -> Dictionary:
	return {
		"kind": "rect",
		"rect": [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
		"color": _rgba(color),
		"mult": 255,
		"width": width,
		"radius": radius,
	}


static func line_op(a: Array, b: Array, color: Array, width: int = 1) -> Dictionary:
	return {
		"kind": "line",
		"a": [int(a[0]), int(a[1])],
		"b": [int(b[0]), int(b[1])],
		"color": _rgba(color),
		"mult": 255,
		"width": width,
	}


static func circle_op(center: Array, radius: int, color: Array, width: int = 0) -> Dictionary:
	return {
		"kind": "circle",
		"center": [int(center[0]), int(center[1])],
		"radius": radius,
		"color": _rgba(color),
		"mult": 255,
		"width": width,
	}


static func polygon_op(points: Array, color: Array, width: int = 0) -> Dictionary:
	var shaped: Array = []
	for point in points:
		shaped.append([int(point[0]), int(point[1])])
	return {"kind": "polygon", "points": shaped, "color": _rgba(color), "mult": 255,
		"width": width}


static func text_op(
	text: String, size: int, style: String, color: Array, pos: Array
) -> Dictionary:
	return {
		"kind": "text",
		"text": text,
		"size": size,
		"style": style,
		"color": _rgba(color),
		"mult": 255,
		"pos": [int(pos[0]), int(pos[1])],
	}


## `_vgrad`: one gradient op (the pixels are a `GradientTexture2D` or a baked sheet).
static func vgrad_op(box: Array, top: Array, bottom: Array, radius: int = 0) -> Dictionary:
	return {
		"kind": "vgrad",
		"rect": [int(box[0]), int(box[1]), maxi(2, int(box[2])), maxi(2, int(box[3]))],
		"top": _rgba(top).slice(0, 3),
		"bottom": _rgba(bottom).slice(0, 3),
		"radius": radius,
		"mult": 255,
	}


## `_radial`: the glow is `assets/art/ui/slider_glow.png`; alpha snaps to multiples of 8.
static func radial_op(box: Array, color: Array, alpha: int) -> Dictionary:
	var graded := maxi(4, mini(120, int(alpha) / 8 * 8))
	return {
		"kind": "radial",
		"rect": [int(box[0]), int(box[1]), maxi(8, int(box[2])), maxi(8, int(box[3]))],
		"color": _rgba(color).slice(0, 3),
		"alpha": graded,
		"mult": 255,
	}


## `_shadow`: soft ring baked into the sheets; `box` is the source rect before the spread.
static func shadow_op(
	box: Array, radius: int = PANEL_RADIUS, alpha: int = SHADOW_ALPHA,
	spread: int = SHADOW_SPREAD
) -> Dictionary:
	return {
		"kind": "shadow",
		"rect": [
			int(box[0]), int(box[1]),
			maxi(2, int(box[2]) + spread * 2), maxi(2, int(box[3]) + spread * 2),
		],
		"radius": radius,
		"alpha": alpha,
		"spread": spread,
		"mult": 255,
	}


## `draw_icon`: placement of one baked vector glyph (`assets/art/ui/icons.png`).
static func icon_op(
	center: Array, name: String, color: Array, scale: float = 1.0
) -> Dictionary:
	return {
		"kind": "icon",
		"name": name,
		"center": [int(center[0]), int(center[1])],
		"color": _rgba(color),
		"scale": scale,
		"mult": 255,
	}


static func _gradtext(
	text: String, size: int, style: String, top: Array, bottom: Array, width: int
) -> Dictionary:
	var key := "%s|%d|%s|%s|%s|%d" % [text, size, style, str(top), str(bottom), width]
	if _gradtext_cache.has(key):
		return (_gradtext_cache[key] as Dictionary).duplicate(true)
	var op := {
		"kind": "gradtext",
		"text": text,
		"size": size,
		"style": style,
		"top": _rgba(top).slice(0, 3),
		"bottom": _rgba(bottom).slice(0, 3),
		"width": width,
		"height": maxi(1, size),
		"mult": 255,
	}
	if _gradtext_cache.size() > GRAD_TEXT_CACHE_LIMIT:
		_gradtext_cache.clear()
	_gradtext_cache[key] = op
	return op.duplicate(true)


static func _center_pos(measure: Callable, text: String, size: int, center: Array) -> Array:
	var span: Vector2i = measure.call(text, size)
	return [int(center[0]) - (span.x >> 1), int(center[1]) - (span.y >> 1)]


# ── text blocks ─────────────────────────────────────────────────────────
## `ui_theme.draw_text`: body render plus an optional `(5, 6, 12)` shadow.
static func draw_text_ops(state: Dictionary, measure: Callable) -> Array:
	var text := String(state.get("text", ""))
	var size := int(state.get("size", 20))
	var style := String(state.get("style", "body"))
	var color: Array = state.get("color", rgb("TEXT_WHITE"))
	var pos: Array = [0, 0]
	if state.has("center"):
		pos = _center_pos(measure, text, size, state["center"])
	else:
		pos = [int(state.topleft[0]), int(state.topleft[1])]
	var ops: Array = []
	if bool(state.get("shadow", true)):
		var offset: Array = state.get("offset", [2, 2])
		var moved := [pos[0] + int(offset[0]), pos[1] + int(offset[1])]
		ops.append(text_op(text, size, style, SHADOW_TEXT, moved))
	ops.append(text_op(text, size, style, color, pos))
	return ops


## `ui_theme.outline_text`: 8 outline blits when `cheap_alpha()`, 4 otherwise, then the body.
static func outline_text_ops(state: Dictionary, measure: Callable) -> Dictionary:
	var text := String(state.get("text", ""))
	var size := int(state.get("size", 64))
	var style := String(state.get("style", "title"))
	var center: Array = state.get("center", [0, 0])
	var outline: Array = state.get("outline", OUTLINE_DEFAULT)
	var width := int(state.get("width", 2))
	var top: Array = state.get("body_top", BODY_GRAD_TOP)
	var bottom: Array = state.get("body_bottom", BODY_GRAD_BOTTOM)
	var pos := _center_pos(measure, text, size, center)
	var span: Vector2i = measure.call(text, size)
	var offsets: Array = [
		[-width, 0], [width, 0], [0, -width], [0, width],
		[-width, -width], [width, width], [-width, width], [width, -width],
	]
	if not bool(state.get("cheap_alpha", true)):
		offsets = offsets.slice(0, 4)
	var ops: Array = []
	for offset in offsets:
		var moved := [pos[0] + int(offset[0]), pos[1] + int(offset[1])]
		ops.append(text_op(text, size, style, outline, moved))
	ops.append(_gradtext(text, size, style, top, bottom, span.x))
	return {"ops": ops, "rect": [pos[0], pos[1], span.x, span.y]}


# ── frames ──────────────────────────────────────────────────────────────
## `ui_theme.corner_ticks`: the gold corner brackets of the whole design system.
static func corner_ticks_ops(
	box: Array, color: Array, length: int = TICK_LENGTH, width: int = TICK_WIDTH,
	inset: int = TICK_INSET
) -> Array:
	var left := int(box[0])
	var top := int(box[1])
	var right := left + int(box[2])
	var bottom := top + int(box[3])
	var corners: Array = [
		[left + inset, top + inset, 1, 1],
		[right - inset, top + inset, -1, 1],
		[left + inset, bottom - inset, 1, -1],
		[right - inset, bottom - inset, -1, -1],
	]
	var ops: Array = []
	for corner in corners:
		var ax := int(corner[0])
		var ay := int(corner[1])
		var dx := int(corner[2])
		var dy := int(corner[3])
		ops.append(line_op([ax, ay], [ax + dx * length, ay], color, width))
		ops.append(line_op([ax, ay], [ax, ay + dy * length], color, width))
	return ops


## `ui_theme.panel`: glass panel with gradient, border, gold ticks and a shadow.
static func panel_ops(state: Dictionary) -> Array:
	var box: Array = state["rect"]
	var border: Array = state.get("border", rgb("EDGE_GOLD"))
	var fill_top: Array = state.get("fill_top", rgb("PANEL_TOP"))
	var fill_bottom: Array = state.get("fill_bottom", rgb("PANEL_BOTTOM"))
	var border_w := int(state.get("border_w", 1))
	var cheap := bool(state.get("cheap_alpha", true))
	var ops: Array = []
	if bool(state.get("shadow", true)):
		var at := [int(box[0]) - SHADOW_SPREAD, int(box[1]) - SHADOW_SPREAD]
		if cheap:
			ops.append(shadow_op([at[0], at[1], box[2], box[3]]))
		else:
			ops.append(rect_op(
				[int(box[0]) + 3, int(box[1]) + 4, box[2], box[3]], [6, 7, 14], 0, PANEL_RADIUS
			))
	if cheap:
		ops.append(vgrad_op(box, fill_top, fill_bottom, PANEL_RADIUS))
	else:
		ops.append(rect_op(box, rgb("PANEL_FILL"), 0, PANEL_RADIUS))
	ops.append(rect_op(box, border, border_w, PANEL_RADIUS))
	if bool(state.get("ticks", true)):
		ops.append_array(corner_ticks_ops(box, rgb("GOLD")))
	return ops


## `ui_theme.panel_solid`: the alpha-free panel of the cheap device path.
static func panel_solid_ops(state: Dictionary) -> Array:
	var box: Array = state["rect"]
	var border: Array = state.get("border", rgb("EDGE_GOLD"))
	var radius := int(state.get("radius", PANEL_RADIUS))
	var ops: Array = [
		rect_op(box, rgb("PANEL_FILL"), 0, radius),
		rect_op(box, border, 1, radius),
	]
	ops.append_array(corner_ticks_ops(box, rgb("GOLD")))
	return ops


# ── interactive components ──────────────────────────────────────────────
static func _component(ops: Array, box: Array, buttons: Dictionary) -> Dictionary:
	return {
		"ops": ops,
		"rect": [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
		"buttons": buttons,
	}


## `ui_theme.pill`: the small action button of eight kinds.
static func pill_ops(state: Dictionary, measure: Callable) -> Dictionary:
	var box: Array = state["rect"]
	var kind := String(state.get("kind", NEUTRAL))
	var bid := String(state.get("id", ""))
	var label := String(state.get("label", ""))
	var size := int(state.get("size", 20))
	var style := String(state.get("style", "body"))
	var hover := bool(state.get("hover", false))
	var enabled := bool(state.get("enabled", true))
	var icon := String(state.get("icon", ""))
	var cheap := bool(state.get("cheap_alpha", true))
	var row: Array = PILL_KINDS.get(kind, PILL_KINDS[NEUTRAL])
	var top: Array = (row[0] as Array).duplicate()
	var bottom: Array = (row[1] as Array).duplicate()
	var edge: Array = row[2]
	var text_color: Array = row[3]
	if hover and enabled:
		top = _brighten(top, 18)
		bottom = _brighten(bottom, 14)
	var radius := int(state.get("radius", PILL_RADIUS))
	var ops: Array = []
	if cheap:
		ops.append(vgrad_op(box, top, bottom, radius))
	else:
		ops.append(rect_op(box, top, 0, radius))
	ops.append(rect_op(box, edge, 2 if enabled else 1, radius))
	if hover and enabled and cheap:
		var at := [int(box[0]) - 15, int(box[1]) - 12]
		ops.append(radial_op(
			[at[0], at[1], int(box[2]) + 30, int(box[3]) + 24], edge, 66
		))
	var center_x := int(box[0]) + (int(box[2]) >> 1)
	var center_y := int(box[1]) + (int(box[3]) >> 1)
	if icon != "":
		var icon_at := [int(box[0]) + CHIP_ICON_PAD, center_y]
		ops.append(icon_op(icon_at, icon, edge, 0.8))
		center_x = int(box[0]) + CHIP_ICON_PAD + ((int(box[2]) - CHIP_ICON_PAD) >> 1)
	var text := letter(label) if bool(state.get("letter_gap", true)) else label
	ops.append_array(draw_text_ops({
		"text": text,
		"size": size,
		"style": style,
		"color": text_color if enabled else rgb("TEXT_FAINT"),
		"center": [center_x, center_y],
	}, measure))
	var buttons: Dictionary = {}
	if enabled:
		buttons[bid] = [int(box[0]), int(box[1]), int(box[2]), int(box[3])]
	return _component(ops, box, buttons)


## `ui_theme.button`: the premium main-menu button with its icon badge.
static func button_ops(state: Dictionary, measure: Callable) -> Dictionary:
	var width := int(state.get("w", 300))
	var height := int(state.get("h", 50))
	var cx := int(state["cx"])
	var cy := int(state["cy"])
	var accent: Array = state["accent"]
	var size := int(state.get("size", 26))
	var style := String(state.get("style", "body_semibold"))
	var hover := bool(state.get("hover", false))
	var icon := String(state.get("icon", ""))
	var cheap := bool(state.get("cheap_alpha", true))
	var base := [cx - (width >> 1), cy - (height >> 1), width, height]
	var box := base.duplicate()
	if hover:
		box = [int(base[0]) - 9, int(base[1]) - 4, width + 18, height + 8]
	var ops: Array = []
	if hover:
		var glow_at := [int(box[0]) - 22, int(box[1]) - 18]
		if cheap:
			ops.append(radial_op(
				[glow_at[0], glow_at[1], int(box[2]) + 44, int(box[3]) + 36], accent, 74
			))
		else:
			ops.append(rect_op(
				[int(box[0]) - 5, int(box[1]) - 5, int(box[2]) + 10, int(box[3]) + 10],
				accent, 2, 14
			))
	if cheap:
		ops.append(shadow_op([int(box[0]) - 2, int(box[1]) - 2, box[2], box[3]]))
	var top: Array = [44, 52, 86] if hover else [34, 41, 70]
	var bottom: Array = [24, 29, 52] if hover else [17, 21, 38]
	if cheap:
		ops.append(vgrad_op(box, top, bottom, PANEL_RADIUS))
	else:
		ops.append(rect_op(box, top, 0, PANEL_RADIUS))
	ops.append(line_op(
		[int(box[0]) + 12, int(box[1]) + 1], [int(box[0]) + int(box[2]) - 12, int(box[1]) + 1],
		[255, 255, 255], 1
	))
	ops.append(rect_op(
		[int(box[0]) + 6, int(box[1]) + 10, 4, int(box[3]) - 20], accent, 0, 2
	))
	if cheap:
		var tint := _rgba(accent)
		tint[3] = 70
		ops.append(rect_op(
			[int(box[0]) + 4, int(box[1]) + 8, 8, int(box[3]) - 16], tint, 0, 3
		))
	ops.append(rect_op(
		box, accent if hover else rgb("EDGE_GOLD"), 2 if hover else 1, PANEL_RADIUS
	))
	ops.append_array(corner_ticks_ops(box, rgb("GOLD")))
	var center_y := int(box[1]) + (int(box[3]) >> 1)
	if icon != "":
		var badge := [int(box[0]) + 34, center_y]
		ops.append(circle_op(badge, 17, [12, 14, 26]))
		ops.append(circle_op(badge, 17, accent, 2))
		ops.append(icon_op(badge, icon, accent, 0.9))
	var text := letter(String(state.get("label", ""))) if bool(
		state.get("letter_gap", true)) else String(state.get("label", ""))
	var text_cx := float(int(box[0]) + (int(box[2]) >> 1))
	if icon != "":
		var text_width := int(measure.call(text, size).x)
		var left_min := int(box[0]) + 56
		var right_max := int(box[0]) + int(box[2]) - 10
		text_cx = float(int(base[0]) + (width >> 1) + 14)
		if text_cx - text_width / 2.0 < float(left_min):
			text_cx = float(left_min) + text_width / 2.0
		if text_cx + text_width / 2.0 > float(right_max):
			text_cx = float(right_max) - text_width / 2.0
		if text_cx - text_width / 2.0 < float(left_min):
			text_cx = float(left_min + right_max) / 2.0
	ops.append_array(draw_text_ops({
		"text": text,
		"size": size,
		"style": String(state.get("text_style", style)),
		"color": rgb("TEXT_WHITE"),
		"center": [int(text_cx), center_y],
	}, measure))
	var buttons: Dictionary = {String(state.get("id", "")): [
		int(box[0]), int(box[1]), int(box[2]), int(box[3])
	]}
	return _component(ops, box, buttons)


## `ui_theme.toggle`: ON/OFF pill with the knob on the opposite side of the label.
static func toggle_ops(state: Dictionary, measure: Callable) -> Dictionary:
	var box: Array = state["rect"]
	var is_on := bool(state.get("on", false))
	var hover := bool(state.get("hover", false))
	var size := int(state.get("size", 20))
	var style := String(state.get("style", "body"))
	var cheap := bool(state.get("cheap_alpha", true))
	var top: Array = []
	var bottom: Array = []
	var edge: Array = []
	if is_on:
		top = [92, 214, 118] if hover else [70, 190, 96]
		bottom = [46, 138, 70] if hover else [34, 116, 58]
		edge = [160, 255, 180] if hover else [120, 235, 145]
	else:
		top = [92, 96, 118] if hover else [74, 78, 100]
		bottom = [56, 60, 80] if hover else [44, 48, 68]
		edge = [150, 156, 180] if hover else [120, 126, 150]
	var radius := int(box[3]) >> 1
	var ops: Array = []
	if cheap:
		ops.append(vgrad_op(box, top, bottom, radius))
	else:
		ops.append(rect_op(box, top, 0, radius))
	ops.append(rect_op(box, edge, 2, radius))
	var knob := TOGGLE_KNOB
	var knob_x := int(box[0]) + 6
	if is_on:
		knob_x = int(box[0]) + int(box[2]) - knob - 6
	var knob_y := int(box[1]) + (int(box[3]) >> 1)
	ops.append(circle_op([knob_x + 1, knob_y + 2], knob / 2, [12, 14, 24]))
	ops.append(circle_op([knob_x, knob_y], knob / 2, [245, 248, 255]))
	ops.append(circle_op([knob_x, knob_y], knob / 2, edge, 1))
	var label_x := int(box[0]) + (int(box[2]) >> 1) + 8
	if is_on:
		label_x = int(box[0]) + (int(box[2]) >> 1) - 8
	ops.append_array(draw_text_ops({
		"text": "ON" if is_on else "OFF",
		"size": size,
		"style": style,
		"color": [210, 255, 220] if is_on else rgb("TEXT_BODY"),
		"center": [label_x, knob_y],
		"shadow": false,
	}, measure))
	var buttons: Dictionary = {String(state.get("id", "")): [
		int(box[0]), int(box[1]), int(box[2]), int(box[3])
	]}
	return _component(ops, box, buttons)


## `ui_theme.tab`: hero-shop category tab.
static func tab_ops(state: Dictionary, measure: Callable) -> Dictionary:
	var box: Array = state["rect"]
	var accent: Array = state["accent"]
	var active := bool(state.get("active", false))
	var hover := bool(state.get("hover", false))
	var size := int(state.get("size", 20))
	var style := String(state.get("style", "body"))
	var cheap := bool(state.get("cheap_alpha", true))
	var ops: Array = []
	var text_color: Array = []
	if active:
		if cheap:
			ops.append(vgrad_op(box, [46, 56, 92], [26, 32, 58], TAB_RADIUS))
		else:
			ops.append(rect_op(box, [46, 56, 92], 0, TAB_RADIUS))
		ops.append(rect_op(box, accent, 2, TAB_RADIUS))
		ops.append(rect_op(
			[int(box[0]) + 8, int(box[1]) + int(box[3]) - 4, int(box[2]) - 16, 3],
			accent, 0, 1
		))
		text_color = accent
	else:
		var top: Array = [34, 39, 62] if hover else [22, 26, 44]
		var bottom: Array = [20, 24, 42] if hover else [15, 18, 32]
		if cheap:
			ops.append(vgrad_op(box, top, bottom, TAB_RADIUS))
		else:
			ops.append(rect_op(box, top, 0, TAB_RADIUS))
		ops.append(rect_op(
			box, [120, 130, 160] if hover else [72, 80, 106], 1, TAB_RADIUS
		))
		text_color = rgb("TEXT_BODY") if hover else rgb("TEXT_DIM")
	ops.append_array(draw_text_ops({
		"text": letter(String(state.get("label", ""))),
		"size": size,
		"style": style,
		"color": text_color,
		"center": [int(box[0]) + (int(box[2]) >> 1), int(box[1]) + (int(box[3]) >> 1)],
		"shadow": false,
	}, measure))
	var buttons: Dictionary = {String(state.get("id", "")): [
		int(box[0]), int(box[1]), int(box[2]), int(box[3])
	]}
	return _component(ops, box, buttons)


## `ui_theme.slider`: track, gold fill and knob; `result` is the knob x.
static func slider_ops(state: Dictionary) -> Dictionary:
	var x := int(state.get("x", 0))
	var y := int(state.get("y", 0))
	var width := int(state.get("w", 0))
	var value := clampf(float(state.get("value", 0.0)), 0.0, 1.0)
	var knob_hover := bool(state.get("knob_hover", false))
	var cheap := bool(state.get("cheap_alpha", true))
	var track := [x, y, width, SLIDER_TRACK]
	var ops: Array = [rect_op(track, [34, 38, 58], 0, TRACK_RADIUS_SLIDER)]
	var fill_w := int(width * value)
	if fill_w > 4:
		if cheap:
			ops.append(vgrad_op(
				[x, y, fill_w, SLIDER_TRACK], rgb("GOLD_BRIGHT"), [196, 138, 40],
				TRACK_RADIUS_SLIDER
			))
		else:
			ops.append(rect_op(
				[x, y, fill_w, SLIDER_TRACK], rgb("GOLD"), 0, TRACK_RADIUS_SLIDER
			))
	ops.append(rect_op(track, [120, 110, 86], 1, TRACK_RADIUS_SLIDER))
	var knob_x := x + fill_w
	var knob_y := y + (SLIDER_TRACK >> 1)
	if knob_hover and cheap:
		ops.append(radial_op(
			[knob_x - 18, knob_y - 18, 36, 36], rgb("GOLD"), 80
		))
	ops.append(circle_op([knob_x, knob_y], SLIDER_KNOB, [12, 14, 24]))
	ops.append(circle_op([knob_x, knob_y], SLIDER_KNOB_CORE, [245, 248, 255]))
	ops.append(circle_op([knob_x, knob_y], SLIDER_KNOB_CORE, rgb("GOLD"), 2))
	return {"ops": ops, "rect": track, "result": knob_x, "buttons": {}}


## `ui_theme.chip`: auto-sized status chip (icon, label, optional value).
static func chip_ops(state: Dictionary, measure: Callable) -> Dictionary:
	var pos: Array = state["pos"]
	var text := String(state.get("text", ""))
	var accent: Array = state["accent"]
	var size := int(state.get("size", 26))
	var style := String(state.get("style", "body"))
	var icon := String(state.get("icon", ""))
	var value := String(state.get("value", ""))
	var cheap := bool(state.get("cheap_alpha", true))
	var spaced := letter(text)
	var total_w := CHIP_PAD
	if icon != "":
		total_w += CHIP_ICON_PAD
	total_w += int(measure.call(spaced, size).x)
	if value != "":
		total_w += CHIP_VALUE_PAD + int(measure.call(value, size).x)
	var x := int(pos[0])
	if String(state.get("align", "left")) == "right":
		x = int(pos[0]) - total_w
	var box := [x, int(pos[1]), total_w, CHIP_HEIGHT]
	var radius := CHIP_HEIGHT >> 1
	var ops: Array = []
	if cheap:
		ops.append(vgrad_op(box, [32, 38, 64], [18, 22, 40], radius))
	else:
		ops.append(rect_op(box, [22, 26, 46], 0, radius))
	ops.append(rect_op(box, accent, 1, radius))
	var icon_x := x + 14
	var icon_y := int(pos[1]) + radius
	if icon != "":
		ops.append(icon_op(
			[icon_x, icon_y], icon, state.get("icon_color", accent), 0.75
		))
		icon_x += CHIP_ICON_PAD
	ops.append_array(draw_text_ops({
		"text": spaced,
		"size": size,
		"style": style,
		"color": rgb("TEXT_BODY"),
		"topleft": [icon_x, int(pos[1]) + 7],
		"shadow": false,
	}, measure))
	icon_x += int(measure.call(spaced, size).x)
	if value != "":
		icon_x += CHIP_VALUE_PAD
		ops.append_array(draw_text_ops({
			"text": value,
			"size": size,
			"style": style,
			"color": state.get("value_color", accent),
			"topleft": [icon_x, int(pos[1]) + 7],
			"shadow": false,
		}, measure))
	return _component(ops, box, {})


## `ui_theme.section_header`: icon, letter-spaced title, hairline and dim underline.
static func section_header_ops(state: Dictionary, measure: Callable) -> Dictionary:
	var x := int(state.get("x", 0))
	var y := int(state.get("y", 0))
	var title := String(state.get("title", ""))
	var color: Array = state["color"]
	var size := int(state.get("size", 26))
	var style := String(state.get("style", "body"))
	var icon := String(state.get("icon", ""))
	var rule_w := int(state.get("rule_w", 240))
	var ops: Array = []
	if icon != "":
		ops.append(icon_op([x + 10, y + 11], icon, color, 0.9))
	ops.append_array(draw_text_ops({
		"text": letter(title),
		"size": size,
		"style": style,
		"color": color,
		"topleft": [x + 28, y],
		"shadow": false,
	}, measure))
	var text_w := int(measure.call(title, size).x) + 28
	ops.append(line_op([x + text_w + 14, y + 14], [x + text_w + 14 + rule_w, y + 14], color, 1))
	ops.append(line_op(
		[x + 28, y + 26], [x + text_w + 14, y + 26], dim(color), 1
	))
	return {"ops": ops, "rect": [x, y, 0, 0], "result": y + 34, "buttons": {}}


## `ui_theme.option_cycler`: label plus a value box with chevron buttons.
static func option_cycler_ops(state: Dictionary, measure: Callable) -> Dictionary:
	var x := int(state.get("x", 0))
	var y := int(state.get("y", 0))
	var width := int(state.get("width", 0))
	var id_base := String(state.get("id", ""))
	var label := String(state.get("label", ""))
	var value := String(state.get("value", ""))
	var label_size := int(state.get("label_size", 26))
	var label_style := String(state.get("label_style", "body"))
	var value_size := int(state.get("value_size", 22))
	var value_style := String(state.get("value_style", "body_medium"))
	var hover := String(state.get("hover", ""))
	var cheap := bool(state.get("cheap_alpha", true))
	var ops: Array = draw_text_ops({
		"text": label,
		"size": label_size,
		"style": label_style,
		"color": rgb("TEXT_BODY"),
		"topleft": [x, y + 10],
		"shadow": false,
	}, measure)
	var box_w := maxi(OPTION_MIN_BOX, int(measure.call(value, value_size).x) + OPTION_BOX_PAD)
	box_w = mini(box_w, width - 66)
	var box := [x + width - box_w - 56, y + 7, box_w, CHIP_HEIGHT]
	var box_hover := hover == id_base + "_prev" or hover == id_base + "_next"
	if cheap:
		ops.append(vgrad_op(box, [40, 48, 80], [20, 24, 44], 6))
	else:
		ops.append(rect_op(box, [28, 34, 58], 0, 6))
	ops.append(rect_op(box, rgb("EDGE_GOLD") if box_hover else [96, 106, 138], 1, 6))
	ops.append_array(draw_text_ops({
		"text": value,
		"size": value_size,
		"style": value_style,
		"color": rgb("GOLD_TEXT"),
		"center": [int(box[0]) + (int(box[2]) >> 1), int(box[1]) + (int(box[3]) >> 1)],
		"shadow": false,
	}, measure))
	var buttons: Dictionary = {}
	for side in ["l", "r"]:
		var bid := id_base + ("_prev" if side == "l" else "_next")
		var button_w := 24
		var button_x := int(box[0]) - button_w - 6
		if side == "r":
			button_x = int(box[0]) + int(box[2]) + 6
		var button := [button_x, int(box[1]), button_w, int(box[3])]
		var button_hover := hover == bid
		if cheap:
			ops.append(vgrad_op(
				button, [64, 74, 110] if button_hover else [42, 48, 74], [26, 30, 52], 6
			))
		else:
			ops.append(rect_op(
				button, [64, 74, 110] if button_hover else [42, 48, 74], 0, 6
			))
		ops.append(rect_op(
			button, [150, 160, 196] if button_hover else [96, 106, 138], 1, 6
		))
		ops.append(icon_op(
			[button_x + (button_w >> 1), int(box[1]) + (int(box[3]) >> 1)],
			"chevron_" + side, [200, 210, 240], 0.6
		))
		buttons[bid] = button
	return {
		"ops": ops,
		"rect": box,
		"result": int(box[1]) + int(box[3]),
		"buttons": buttons,
	}


## `ui_theme.screen_title`: gold gradient title, glow, ornament and subtitle plate.
static func screen_title_ops(state: Dictionary, measure: Callable) -> Dictionary:
	var cx := int(state.get("cx", 0))
	var y := int(state.get("y", 0))
	var text := String(state.get("text", ""))
	var size := int(state.get("size", 64))
	var style := String(state.get("style", "title"))
	var sub := String(state.get("sub", ""))
	var cheap := bool(state.get("cheap_alpha", true))
	var ops: Array = []
	if bool(state.get("glow", true)) and cheap:
		ops.append(radial_op(
			[cx - 310, y - 62, TITLE_GLOW[0], TITLE_GLOW[1]], TITLE_GLOW_COLOR,
			TITLE_GLOW_ALPHA
		))
	ops.append_array(outline_text_ops({
		"text": text,
		"size": size,
		"style": style,
		"center": [cx, y],
		"cheap_alpha": cheap,
	}, measure)["ops"])
	var line_y := y + ORNAMENT_DROP
	if bool(state.get("ornament", true)):
		ops.append(line_op(
			[cx - ORNAMENT_SPAN, line_y], [cx - ORNAMENT_GAP, line_y], rgb("EDGE_GOLD"), 2
		))
		ops.append(line_op(
			[cx + ORNAMENT_GAP, line_y], [cx + ORNAMENT_SPAN, line_y], rgb("EDGE_GOLD"), 2
		))
		ops.append(polygon_op([
			[cx - ORNAMENT_DIAMOND, line_y],
			[cx, line_y - 7],
			[cx + ORNAMENT_DIAMOND, line_y],
			[cx, line_y + 7],
		], rgb("GOLD")))
		ops.append(circle_op([cx - 230, line_y], 3, rgb("GOLD_BRIGHT")))
		ops.append(circle_op([cx + 230, line_y], 3, rgb("GOLD_BRIGHT")))
	if sub != "":
		var sub_size := int(state.get("sub_size", 30))
		var sub_style := String(state.get("sub_style", "body_semibold"))
		var spaced := letter(sub)
		var span: Vector2i = measure.call(spaced, sub_size)
		var plate := [
			cx - ((span.x + 56) >> 1), line_y + 12, span.x + 56, 44,
		]
		if cheap:
			ops.append(vgrad_op(plate, [26, 32, 58], [14, 18, 34], 10))
		else:
			ops.append(rect_op(plate, [16, 20, 38], 0, 10))
		ops.append(rect_op(plate, rgb("EDGE_GOLD"), 1, 10))
		ops.append_array(corner_ticks_ops(plate, rgb("GOLD"), 8, 1, 3))
		ops.append(text_op(
			spaced, sub_size, sub_style, state.get("sub_color", rgb("CYAN_SOFT")),
			[
				int(plate[0]) + (int(plate[2]) >> 1) - (span.x >> 1),
				int(plate[1]) + 22 - (span.y >> 1),
			]
		))
	return {"ops": ops, "rect": [cx, y, 0, 0], "buttons": {}}


## `ui_theme.back_button`: the uniform 200x42 BACK pill.
static func back_button_ops(state: Dictionary, measure: Callable) -> Dictionary:
	var cx := int(state.get("cx", 0))
	var y := int(state.get("y", 0))
	var box := [
		cx - (BACK_BUTTON_WIDTH >> 1), y - (BACK_BUTTON_HEIGHT >> 1),
		BACK_BUTTON_WIDTH, BACK_BUTTON_HEIGHT,
	]
	return pill_ops({
		"rect": box,
		"id": String(state.get("id", "")),
		"label": "BACK",
		"kind": NEUTRAL,
		"size": int(state.get("size", 26)),
		"style": String(state.get("style", "body_semibold")),
		"hover": bool(state.get("hover", false)),
		"icon": "back",
		"cheap_alpha": bool(state.get("cheap_alpha", true)),
	}, measure)


## `ui_theme.scroll_indicator`: slim track with a gold thumb.
static func scroll_indicator_ops(state: Dictionary) -> Dictionary:
	var x := int(state.get("x", 0))
	var y := int(state.get("y", 0))
	var height := int(state.get("height", 0))
	var width := int(state.get("width", 6))
	var scroll_pos := int(state.get("scroll_pos", 0))
	var max_scroll := int(state.get("max_scroll", 0))
	var cheap := bool(state.get("cheap_alpha", true))
	var track := [x, y, width, height]
	var ops: Array = [rect_op(track, [28, 32, 52], 0, 3)]
	if max_scroll > 0:
		var ratio := float(height) / float(height + max_scroll)
		var thumb_h := maxi(SCROLL_MIN_THUMB, int(float(height) * ratio))
		var thumb_y := y + int(float(height - thumb_h) * (float(scroll_pos) / float(max_scroll)))
		if cheap:
			ops.append(vgrad_op(
				[x, thumb_y, width, thumb_h], rgb("GOLD_BRIGHT"), [196, 138, 40], 3
			))
		else:
			ops.append(rect_op([x, thumb_y, width, thumb_h], rgb("GOLD"), 0, 3))
	return {"ops": ops, "rect": track, "buttons": {}}


## `ui_theme.hp_bar`: dark track, lightened fill and a slate border.
static func hp_bar_ops(state: Dictionary) -> Array:
	var x := int(state.get("x", 0))
	var y := int(state.get("y", 0))
	var width := int(state.get("w", 0))
	var height := int(state.get("h", 0))
	var ratio := clampf(float(state.get("ratio", 0.0)), 0.0, 1.0)
	var color: Array = state.get("color", rgb("GREEN"))
	var cheap := bool(state.get("cheap_alpha", true))
	var radius := height >> 1
	var track := [x, y, width, height]
	var ops: Array = [rect_op(track, [16, 18, 30], 0, radius)]
	var fill_w := int(float(width) * ratio)
	if fill_w > 3:
		if cheap:
			ops.append(vgrad_op(
				[x, y, fill_w, height], _brighten(color, 50), color, radius
			))
		else:
			ops.append(rect_op([x, y, fill_w, height], color, 0, radius))
	ops.append(rect_op(track, [86, 92, 120], 1, radius))
	return ops


## `ui_theme.progress_bar`: gold progress track.
static func progress_bar_ops(state: Dictionary) -> Array:
	var x := int(state.get("x", 0))
	var y := int(state.get("y", 0))
	var width := int(state.get("w", 0))
	var height := int(state.get("h", 8))
	var frac := clampf(float(state.get("frac", 0.0)), 0.0, 1.0)
	var color: Array = state.get("color", rgb("GOLD"))
	var cheap := bool(state.get("cheap_alpha", true))
	var radius := height >> 1
	var track := [x, y, width, height]
	var ops: Array = [rect_op(track, [30, 34, 54], 0, radius)]
	var fill_w := int(float(width) * frac)
	if fill_w > 3:
		if cheap:
			ops.append(vgrad_op([x, y, fill_w, height], _brighten(color, 40), color, radius))
		else:
			ops.append(rect_op([x, y, fill_w, height], color, 0, radius))
	ops.append(rect_op(track, [96, 96, 126], 1, radius))
	return ops


static func _brighten(color: Array, step: int) -> Array:
	var out: Array = []
	for channel in color:
		out.append(mini(255, int(channel) + step))
	return out
