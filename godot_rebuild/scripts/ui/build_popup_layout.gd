extends RefCounted
## Layer 9bv7: `BuildPopup.draw` (`ui_components/_bundle.py`, cheap-alpha branch), the
## build-tower popup pygame paints while an empty build slot is selected. Pure op builder;
## the ops use the `draw_recorder.py` shapes (plus one op per cached surface) so
## `tests/build_popup_draw_source_oracle.py` can pin them.
##
##   * the 400 x 300 card sits at the slot, clamped into the frame (`origin`);
##   * a gold connector line runs from the card's bottom-centre to the slot;
##   * shadow + vertical gradient card, 2 px gold border and gold corner ticks;
##   * the Cinzel "BUILD TOWER" title, the `Gold: n (Cost: 100)` line;
##   * the X close button (hover red);
##   * a 2x2 grid of four tower cards (archer, cannon, ice, mage) with a coin icon, cost
##     and hover glow; a card is hovered only while the gold covers the 100 cost.
##
## `state`: x, y (slot), gold and mouse (Vector2i), with optional panel_pos and popup_w for the
## wide-screen side panel. `cheap_alpha` mirrors `mobile.perf.Quality.cheap_alpha`: true draws the
## gradient card and the card glow, false draws the flat `(25, 30, 45)` panel and flat card fills.

const POPUP_W := 400
const POPUP_H := 300
const SCREEN_W := 1280
const SCREEN_H := 720
const COST := 100
const BTN_H := 78
const SHADOW_SPREAD := 4
## `_core.GOLD`: the connector line.
const GOLD := [255, 200, 50]
## `ui_theme.GOLD`: the panel border and the card corner ticks.
const UI_GOLD := [255, 205, 85]
const GOLD_BRIGHT := [255, 233, 158]
const GOLD_TEXT := [255, 220, 110]
const RED := [220, 50, 50]
const WHITE := [255, 255, 255]
const GRAY := [150, 150, 150]
const DESC_TEXT := [215, 222, 240]
const PANEL_TOP := [34, 40, 68]
const PANEL_BOTTOM := [16, 19, 36]
const PANEL_SOLID := [25, 30, 45]
const TOWER_TYPES := [
	["archer", "Archer", "Fast single", [100, 220, 120]],
	["cannon", "Cannon", "AOE + Burn", [200, 100, 60]],
	["ice", "Ice", "Slow move+atk", [120, 200, 255]],
	["mage", "Mage", "Chain + Debuff", [180, 80, 220]],
]

var _ops: Array = []
var _measure: Callable


## `state`: x, y, gold and mouse; `measure` measures the Cinzel title and the X glyph.
static func ops(state: Dictionary, measure: Callable, cheap_alpha: bool = true) -> Array:
	var layout := new()
	layout._measure = measure
	layout._draw(state, cheap_alpha)
	return layout._ops


## `BuildPopup.draw`'s fallback position: centred on the slot, 30 px above it, clamped to
## the frame with the source's exact order of checks.
static func origin(slot_x: int, slot_y: int) -> Vector2i:
	return origin_for_width(slot_x, slot_y, POPUP_W)


static func origin_for_width(slot_x: int, slot_y: int, popup_width: int) -> Vector2i:
	var px := slot_x - (popup_width >> 1)
	var py := slot_y - POPUP_H - 30
	if px < 10:
		px = 10
	if px + popup_width > SCREEN_W - 10:
		px = SCREEN_W - popup_width - 10
	if py < 10:
		py = slot_y + 30
	if py + POPUP_H > SCREEN_H - 10:
		py = SCREEN_H - POPUP_H - 10
	if py < 10:
		py = 10
	return Vector2i(px, py)


## Mirrors BuildPopup's compact width and `platform_utils.panel_popup_pos` on the full surface.
static func mobile_geometry(panel: Rect2i) -> Dictionary:
	if panel.size.x <= 0:
		return {}
	var popup_width := mini(POPUP_W, maxi(1, panel.size.x - 16))
	if popup_width > panel.size.x - 8:
		return {}
	var centered_y := floori(float(panel.size.y - POPUP_H) / 2.0)
	var py := maxi(12, mini(panel.size.y - POPUP_H - 12, centered_y))
	var px := panel.position.x + int((panel.size.x - popup_width) / 2)
	return {"panel_pos": [px, py], "popup_w": popup_width}


static func state_width(state: Dictionary) -> int:
	return clampi(int(state.get("popup_w", POPUP_W)), 1, POPUP_W)


static func state_origin(state: Dictionary) -> Vector2i:
	var supplied: Variant = state.get("panel_pos", null)
	if supplied is Array and supplied.size() >= 2:
		return Vector2i(int(supplied[0]), int(supplied[1]))
	if supplied is Vector2i:
		return supplied
	return origin_for_width(int(state.get("x", 0)), int(state.get("y", 0)), state_width(state))


## `g.ui_buttons['build_<type>']`: the card rect the source registers.
static func button_rect(slot_x: int, slot_y: int, index: int) -> Rect2i:
	return state_button_rect({"x": slot_x, "y": slot_y}, index)


static func state_button_rect(state: Dictionary, index: int) -> Rect2i:
	var origin_at := state_origin(state)
	var popup_width := state_width(state)
	var btn_w := (popup_width - 50) >> 1
	var col := index % 2
	var row := index >> 1
	var bx := origin_at.x + 15 + col * (btn_w + 12)
	var by := origin_at.y + 62 + row * (BTN_H + 10)
	return Rect2i(bx, by, btn_w, BTN_H)


## `g.ui_buttons['build_close']`: the X button rect the source registers.
static func close_rect(slot_x: int, slot_y: int) -> Rect2i:
	return state_close_rect({"x": slot_x, "y": slot_y})


static func state_close_rect(state: Dictionary) -> Rect2i:
	var origin_at := state_origin(state)
	return Rect2i(origin_at.x + state_width(state) - 26, origin_at.y + 6, 22, 22)


func _draw(state: Dictionary, cheap_alpha: bool) -> void:
	var slot_x := int(state.get("x", 0))
	var slot_y := int(state.get("y", 0))
	var gold := int(state.get("gold", 0))
	var mouse: Vector2i = state.get("mouse", Vector2i())
	var popup_width := state_width(state)
	var origin_at := state_origin(state)
	var px := origin_at.x
	var py := origin_at.y
	if not state.has("panel_pos"):
		_ops.append(
			_line(
				[px + (popup_width >> 1), py + POPUP_H], [slot_x, slot_y - 10], _rgba(GOLD, 255), 2
			)
		)
	_panel(px, py, popup_width, cheap_alpha)
	_title(px, py, popup_width)
	_gold_info(px, py, gold)
	_section("_draw_close_button")
	_close_button(px, py, mouse, popup_width)
	_section("_draw_tower_buttons")
	_tower_buttons(px, py, gold, mouse, popup_width, cheap_alpha)


## Shadow + gradient card (or the flat panel), 2 px gold border and the gold corner ticks.
func _panel(px: int, py: int, popup_width: int, cheap_alpha: bool) -> void:
	if cheap_alpha:
		_ops.append(_shadow(popup_width, POPUP_H, 10, 150, px - 3, py - 3))
		_ops.append(_vgrad([px, py, popup_width, POPUP_H], PANEL_TOP, PANEL_BOTTOM, 10))
	else:
		_ops.append(_rect([px, py, popup_width, POPUP_H], _rgba(PANEL_SOLID, 255), 0, 10))
	_ops.append(_rect([px, py, popup_width, POPUP_H], _rgba(UI_GOLD, 255), 2, 10))
	_corner_ticks([px, py, popup_width, POPUP_H], GOLD_BRIGHT, 12)


## `ui_theme.outline_text` with the default gold gradient body (`GOLD_BRIGHT` -> deep gold).
func _title(px: int, py: int, popup_width: int) -> void:
	var cx_t := px + (popup_width >> 1)
	var metrics: Vector2i = _measure.call("BUILD TOWER", 30)
	var op := {
		"kind": "outline_text",
		"text": "BUILD TOWER",
		"size": 30,
		"style": "title",
		"pos": [(cx_t - 10) - (metrics.x >> 1), (py + 22) - (metrics.y >> 1)],
		"outline": [8, 9, 18],
		"width": 2,
		"top": GOLD_BRIGHT,
		"bottom": [196, 138, 40],
		"mult": 255,
	}
	_ops.append(op)


func _gold_info(px: int, py: int, gold: int) -> void:
	var label := "Gold: %s  (Cost: %d)" % [_thousands(gold), COST]
	_ops.append(_text(label, 18, GOLD_TEXT, [px + 15, py + 40], "body_semibold"))


## `BaseUIComponent._draw_close_button(..., size=22, style='rect')`.
func _close_button(px: int, py: int, mouse: Vector2i, popup_width: int) -> void:
	var size := 22
	var x := px + popup_width - 26
	var y := py + 6
	var hover := Rect2i(x, y, size, size).has_point(mouse)
	if hover:
		_ops.append(_rect([x, y, size, size], _rgba([255, 60, 60], 255), 0, 3))
		_ops.append(_rect([x, y, size, size], _rgba(WHITE, 255), 2, 3))
	else:
		_ops.append(_rect([x, y, size, size], _rgba(RED, 255), 0, 3))
		_ops.append(_rect([x, y, size, size], _rgba(WHITE, 255), 1, 3))
	var metrics: Vector2i = _measure.call("X", 28)
	var cx := x + (size >> 1)
	var cy := y + (size >> 1)
	_ops.append(
		_text("X", 28, WHITE, [cx - (metrics.x >> 1), cy - (metrics.y >> 1)], "body_semibold")
	)


## `BuildPopup._draw_tower_buttons`: the 2x2 grid of premium tower cards.
func _tower_buttons(
	px: int, py: int, gold: int, mouse: Vector2i, popup_width: int, cheap_alpha: bool
) -> void:
	var can_afford := gold >= COST
	var btn_w := (popup_width - 50) >> 1
	var start_y := py + 62
	for index in range(TOWER_TYPES.size()):
		var col := index % 2
		var row := index >> 1
		var bx := px + 15 + col * (btn_w + 12)
		var by := start_y + row * (BTN_H + 10)
		var hover := can_afford and Rect2i(bx, by, btn_w, BTN_H).has_point(mouse)
		var color: Array = TOWER_TYPES[index][3]
		var dark := _tint(color, 0.30, 18)
		var lighter := _tint(color, 0.45, 40, true)
		var bottom := _tint(color, 0.22, 12)
		if cheap_alpha:
			_ops.append(_vgrad([bx, by, btn_w, BTN_H], lighter if hover else dark, bottom, 8))
			if hover:
				_ops.append(_radial([bx - 8, by - 8, btn_w + 16, BTN_H + 16], color, 40))
		else:
			_ops.append(_rect([bx, by, btn_w, BTN_H], _rgba(dark, 255), 0, 8))
		_ops.append(
			_rect([bx, by, btn_w, BTN_H], _rgba(color if can_afford else [70, 70, 80], 255), 2, 8)
		)
		if can_afford:
			_corner_ticks([bx, by, btn_w, BTN_H], UI_GOLD, 8)
		_ops.append(
			_text(
				TOWER_TYPES[index][1],
				22,
				WHITE if can_afford else GRAY,
				[bx + 10, by + 7],
				"body_bold"
			)
		)
		_ops.append(
			_text(
				TOWER_TYPES[index][2],
				17,
				DESC_TEXT if can_afford else GRAY,
				[bx + 10, by + 32],
				"body_medium"
			)
		)
		_coin(bx + 16, by + 62, 0.5)
		_ops.append(
			_text(
				"%d Gold" % COST,
				18,
				GOLD_TEXT if can_afford else GRAY,
				[bx + 28, by + 53],
				"body_bold"
			)
		)


## `ui_theme.draw_icon(surf, "coin", cx, cy, color, s=0.5)`; the coin ignores `color`.
func _coin(cx: int, cy: int, s: float) -> void:
	var r := 9.0 * s
	_ops.append(_circle([cx, cy], r, _rgba([255, 205, 66], 255), 0))
	_ops.append(_circle([cx, cy], r, _rgba([190, 140, 32], 255), 2))
	_ops.append(_circle([cx, cy], 5.0 * s, _rgba([230, 175, 50], 255), 0))
	_ops.append(_line([cx, cy - 3.5 * s], [cx, cy + 3.5 * s], _rgba([190, 140, 32], 255), 2))


## `ui_theme.corner_ticks(rect, color, length)` with width 2 and inset 2.
func _corner_ticks(box: Array, color: Array, length: int) -> void:
	var left: int = int(box[0])
	var top: int = int(box[1])
	var right: int = left + int(box[2])
	var bottom: int = top + int(box[3])
	var corners: Array = [
		[left + 2, top + 2, 1, 1],
		[right - 2, top + 2, -1, 1],
		[left + 2, bottom - 2, 1, -1],
		[right - 2, bottom - 2, -1, -1],
	]
	for index in range(corners.size()):
		var cx: int = int(corners[index][0])
		var cy: int = int(corners[index][1])
		var sx: int = int(corners[index][2])
		var sy: int = int(corners[index][3])
		_ops.append(_line([cx, cy], [cx + sx * length, cy], _rgba(color, 255), 2))
		_ops.append(_line([cx, cy], [cx, cy + sy * length], _rgba(color, 255), 2))


## `int(channel * factor) + bias`, the source's dark / lighter / bottom tints; `clamp`
## applies the `min(255, ...)` the source puts on the lighter tint only.
static func _tint(color: Array, factor: float, bias: int, clamp := false) -> Array:
	var out := [
		int(int(color[0]) * factor) + bias,
		int(int(color[1]) * factor) + bias,
		int(int(color[2]) * factor) + bias,
	]
	if clamp:
		for index in range(out.size()):
			out[index] = mini(255, int(out[index]))
	return out


## Python's `f"{gold:,}"`: thousands separators, no decimals.
static func _thousands(value: int) -> String:
	if value < 0:
		return "-" + _thousands(-value)
	var digits := str(value)
	var parts: Array = []
	while digits.length() > 3:
		parts.insert(0, digits.right(3))
		digits = digits.left(digits.length() - 3)
	parts.insert(0, digits)
	return ",".join(parts)


func _section(name: String) -> void:
	_ops.append({"kind": "section", "name": name})


static func _rgba(color: Array, alpha: int) -> Array:
	return [int(color[0]), int(color[1]), int(color[2]), alpha]


static func _circle(center: Array, radius: float, rgba: Array, width: int) -> Dictionary:
	return {
		"kind": "circle",
		"center": center,
		"radius": radius,
		"color": rgba,
		"mult": 255,
		"width": width,
	}


static func _line(a: Array, b: Array, rgba: Array, width: int) -> Dictionary:
	return {"kind": "line", "a": a, "b": b, "color": rgba, "mult": 255, "width": width}


static func _rect(box: Array, rgba: Array, width: int, radius: int) -> Dictionary:
	return {
		"kind": "rect",
		"rect": box.duplicate(),
		"color": rgba,
		"mult": 255,
		"width": width,
		"radius": radius,
	}


static func _vgrad(box: Array, top: Array, bottom: Array, radius: int) -> Dictionary:
	return {
		"kind": "vgrad",
		"rect": box.duplicate(),
		"top": top,
		"bottom": bottom,
		"radius": radius,
		"mult": 255,
	}


static func _shadow(w: int, h: int, radius: int, alpha: int, dx: int, dy: int) -> Dictionary:
	return {
		"kind": "shadow",
		"rect": [dx, dy, w + SHADOW_SPREAD * 2, h + SHADOW_SPREAD * 2],
		"radius": radius,
		"alpha": alpha,
		"mult": 255,
	}


static func _radial(box: Array, color: Array, alpha: int) -> Dictionary:
	return {"kind": "radial", "rect": box.duplicate(), "color": color, "alpha": alpha, "mult": 255}


static func _text(words: String, size: int, color: Array, pos: Array, style: String) -> Dictionary:
	return {
		"kind": "text",
		"text": words,
		"size": size,
		"style": style,
		"color": _rgba(color, 255),
		"mult": 255,
		"pos": pos,
	}
