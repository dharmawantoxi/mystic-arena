extends RefCounted
## Native port of `ui_components/_bundle.py::BaseUIComponent` (the shared toolbox) plus
## `_popup_di_panel` / `mobile.platform_utils.panel_popup_pos`.
##
## Every component in the folder inherits these four helpers, so they live in one place
## instead of being re-derived per popup:
##
##   * `shadow_ops`   - `_draw_shadow_rect`: one black rect, alpha-blended. The source
##     builds a `w + 2*offset` surface, draws the rect inset by `offset` and blits it back
##     at `rect - offset`; both offsets cancel, so the net op is the rect itself.
##   * `hp_bar_ops`   - `_draw_hp_bar`: dark red track, GREEN > 50 %, YELLOW > 25 %,
##     RED otherwise, `int(w * ratio)` wide (can overflow the track), white 1 px border.
##   * `close_button_ops` - `_draw_close_button`: rect and circle variants, hover glow.
##   * `panel_position`   - `_popup_di_panel` -> `panel_popup_pos`: move a popup into the
##     right dock panel when it fits (`w <= panel_w - 8`), else return `{}` and let the
##     caller anchor on the map.
##
## Colours are `[r, g, b, a]` int arrays like every other `scripts/ui/*_layout.gd`.

const GREEN := [50, 200, 50, 255]
const YELLOW := [255, 220, 0, 255]
const RED := [220, 50, 50, 255]
const WHITE := [255, 255, 255, 255]
const HP_TRACK := [40, 0, 0, 255]
const HOVER_FILL := [255, 60, 60, 255]
const CIRCLE_FILL := [150, 30, 30, 255]
const CIRCLE_HOVER := [200, 40, 40, 255]
const CIRCLE_GLOW := [255, 80, 80, 100]
const SHADOW := [0, 0, 0, 255]
const CLOSE_TEXT_SIZE := 28
const CLOSE_TEXT := "X"


## `_draw_shadow_rect(rect, alpha=150, border_radius=8, offset=(5, 5))`.
static func shadow_ops(box: Rect2i, alpha: int = 150, radius: int = 8) -> Array:
	return [{
		"kind": "rect",
		"rect": _rect_array(box),
		"color": [SHADOW[0], SHADOW[1], SHADOW[2], alpha],
		"width": 0,
		"radius": radius,
	}]


## `_draw_hp_bar(x, y, w, h, ratio, show_bg=True)`.
static func hp_bar_ops(box: Rect2i, ratio: float, show_bg: bool = true) -> Array:
	var ops: Array = []
	if show_bg:
		ops.append(_rect_op(box, HP_TRACK, 0, 0))
	var fill := int(box.size.x * ratio)
	if fill > 0:
		ops.append(_rect_op(Rect2i(box.position, Vector2i(fill, box.size.y)), _hp_color(ratio), 0, 0))
	ops.append(_rect_op(box, WHITE, 1, 0))
	return ops


## Threshold chain of `_draw_hp_bar`: `> 0.5` green, `> 0.25` yellow, else red.
static func _hp_color(ratio: float) -> Array:
	if ratio > 0.5:
		return GREEN
	if ratio > 0.25:
		return YELLOW
	return RED


## `_draw_close_button(x, y, size=44, button_id='close', style='rect')` with the hover
## already resolved by the caller (the source reads `pygame.mouse.get_pos()`).
static func close_button_ops(
	box: Rect2i, hover: bool = false, style: String = "rect", measure: Callable = Callable()
) -> Array:
	if style == "circle":
		return _circle_close_ops(box, hover)
	return _rect_close_ops(box, hover, measure)


static func _rect_close_ops(box: Rect2i, hover: bool, measure: Callable) -> Array:
	var border := 2 if hover else 1
	var ops: Array = [
		_rect_op(box, HOVER_FILL if hover else RED, 0, 3),
		_rect_op(box, WHITE, border, 3),
	]
	var metrics: Vector2 = measure.call(CLOSE_TEXT, CLOSE_TEXT_SIZE)
	ops.append({
		"kind": "text",
		"text": CLOSE_TEXT,
		"size": CLOSE_TEXT_SIZE,
		"style": "body_semibold",
		"color": WHITE,
		"pos": [
			box.position.x + box.size.x / 2 - int(metrics.x) / 2,
			box.position.y + box.size.y / 2 - int(metrics.y) / 2,
		],
	})
	return ops


static func _circle_close_ops(box: Rect2i, hover: bool) -> Array:
	var size := box.size.x
	var center := box.position + Vector2i(size / 2, size / 2)
	var ops: Array = []
	if hover:
		var glow := box.position - Vector2i(5, 5) + Vector2i((size + 10) / 2, (size + 10) / 2)
		ops.append({
			"kind": "circle",
			"center": [glow.x, glow.y],
			"radius": size / 2 + 3,
			"color": CIRCLE_GLOW,
			"width": 0,
		})
	ops.append({
		"kind": "circle",
		"center": [center.x, center.y],
		"radius": size / 2,
		"color": CIRCLE_HOVER if hover else CIRCLE_FILL,
		"width": 0,
	})
	ops.append({
		"kind": "circle",
		"center": [center.x, center.y],
		"radius": size / 2,
		"color": WHITE,
		"width": 2,
	})
	var offset := size / 4
	ops.append(_line(center + Vector2i(-offset, -offset), center + Vector2i(offset, offset), 3))
	ops.append(_line(center + Vector2i(offset, -offset), center + Vector2i(-offset, offset), 3))
	return ops


static func _line(from: Vector2i, to: Vector2i, width: int) -> Dictionary:
	return {
		"kind": "line",
		"a": [from.x, from.y],
		"b": [to.x, to.y],
		"color": WHITE,
		"width": width,
	}


## `_popup_di_panel` -> `platform_utils.panel_popup_pos(w, h, atas=12)`.
## Returns `{}` when the popup cannot fit the dock panel (`w > panel_w - 8`).
static func panel_position(w: int, h: int, panel: Rect2i, top_margin: int = 12) -> Dictionary:
	if panel.size.x <= 0 or panel.size.y <= 0 or w > panel.size.x - 8:
		return {}
	var x := panel.position.x + (panel.size.x - w) / 2
	var y := maxi(top_margin, mini(panel.size.y - h - 12, _floor_half(panel.size.y - h)))
	return {"x": x, "y": y}


static func _floor_half(value: int) -> int:
	return int(floor(float(value) / 2.0))


static func _rect_array(box: Rect2i) -> Array:
	return [box.position.x, box.position.y, box.size.x, box.size.y]


static func _rect_op(box: Rect2i, color: Array, width: int, radius: int) -> Dictionary:
	return {"kind": "rect", "rect": _rect_array(box), "color": color, "width": width, "radius": radius}
