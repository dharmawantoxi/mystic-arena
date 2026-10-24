extends RefCounted
## Layer 9bv2: `Game._draw_gold_hud` (`_core.py`), the gold chip and mode badge pygame paints
## at the top-left while the wide-screen side panel is off. Pure op builder; the ops use the
## `draw_recorder.py` shapes so `tests/gold_hud_draw_source_oracle.py` can pin them.
##
## Chip at (18, 22), 40 px high, `max(150, val_w + inc_w + 78)` wide, radius 20:
##   * fill: `_vgrad` (44, 38, 18) -> (24, 20, 9) when `cheap_alpha()`, else solid (26, 22, 10);
##   * 2 px border in `ui_theme.GOLD`;
##   * `draw_icon("coin")` at (x + 24, centre y), s = 0.9;
##   * `f"{gold:,}"`, 24 px body_bold, (255, 236, 160), top-left (x + 44, y + 5);
##   * hairline (140, 110, 50) at gx - 6 from y + 10 to y + 30, gx = x + 44 + val_w + 12;
##   * `"+" + format_gold_rate(rate) + "/s"`, 17 px body_medium, (196, 241, 168), at (gx, y + 11).
## Badge at (x, y + 46), 24 px high, label width + 24 wide, radius 12:
##   * fill: `_vgrad` (24, 28, 48) -> (14, 17, 32) when `cheap_alpha()`, else (16, 19, 34);
##   * 1 px border in the mode colour * 0.6 (truncated);
##   * `draw_icon("swords")` at (x + 15, centre y), s = 0.55;
##   * EASY / NORMAL / HARD, 18 px body_semibold, at (x + 27, y + 4). Any other difficulty
##     shows NORMAL, like the source `else` branch.

const Economy = preload("res://scripts/match/match_economy.gd")

const ORIGIN := Vector2i(18, 22)
const CHIP_HEIGHT := 40
const CHIP_MIN_WIDTH := 150
const BADGE_HEIGHT := 24
## `height // 2` in the source (radius and icon centre), kept as constants.
const CHIP_HALF := 20
const BADGE_HALF := 12
const GOLD := [255, 205, 85]
const CHIP_TOP := [44, 38, 18]
const CHIP_BOTTOM := [24, 20, 9]
const CHIP_SOLID := [26, 22, 10]
const GOLD_TEXT := [255, 236, 160]
const HAIRLINE := [140, 110, 50]
const INCOME_TEXT := [196, 241, 168]
const BADGE_TOP := [24, 28, 48]
const BADGE_BOTTOM := [14, 17, 32]
const BADGE_SOLID := [16, 19, 34]
const COIN_FILL := [255, 205, 66]
const COIN_EDGE := [190, 140, 32]
const COIN_INNER := [230, 175, 50]
const ICON_DARK := [10, 12, 22]
const MODES := {
	"easy": ["EASY", [100, 210, 255]],
	"hard": ["HARD", [255, 120, 120]],
}
const NORMAL_MODE := ["NORMAL", [120, 230, 150]]

var _ops: Array = []


## `f"{gold:,}"`: thousands separated by commas.
static func gold_text(gold: int) -> String:
	var digits := str(absi(gold))
	var grouped := ""
	while digits.length() > 3:
		grouped = "," + digits.right(3) + grouped
		digits = digits.left(digits.length() - 3)
	return ("-" if gold < 0 else "") + digits + grouped


static func income_text(rate: float) -> String:
	return "+" + Economy.format_gold_rate(rate) + "/s"


static func mode(difficulty: String) -> Array:
	return MODES.get(difficulty, NORMAL_MODE)


## The chip's rect, `[x, y, w, h]`, for a given font measure (the HUD keeps clear of it).
static func chip_rect(gold: int, rate: float, measure: Callable) -> Array:
	var val_w: int = measure.call(gold_text(gold), 24).x
	var inc_w: int = measure.call(income_text(rate), 17).x
	return [ORIGIN.x, ORIGIN.y, maxi(CHIP_MIN_WIDTH, val_w + inc_w + 78), CHIP_HEIGHT]


static func ops(
	gold: int, rate: float, difficulty: String, measure: Callable, cheap_alpha: bool = true
) -> Array:
	var layout := new()
	layout._chip(gold, rate, measure, cheap_alpha)
	layout._badge(difficulty, measure, cheap_alpha)
	return layout._ops


func _chip(gold: int, rate: float, measure: Callable, cheap_alpha: bool) -> void:
	var x := ORIGIN.x
	var y := ORIGIN.y
	var chip := chip_rect(gold, rate, measure)
	var radius := CHIP_HALF
	_fill(chip, CHIP_TOP, CHIP_BOTTOM, CHIP_SOLID, radius, cheap_alpha)
	_ops.append(_rect(chip, GOLD, 2, radius))
	_coin(x + 24, y + CHIP_HALF, 0.9)
	var val_w: int = measure.call(gold_text(gold), 24).x
	_ops.append(_text(gold_text(gold), 24, "body_bold", GOLD_TEXT, x + 44, y + 5))
	var gx := x + 44 + val_w + 12
	_ops.append(_line([gx - 6, y + 10], [gx - 6, y + CHIP_HEIGHT - 10], HAIRLINE, 1))
	_ops.append(_text(income_text(rate), 17, "body_medium", INCOME_TEXT, gx, y + 11))


func _badge(difficulty: String, measure: Callable, cheap_alpha: bool) -> void:
	var picked := mode(difficulty)
	var label := String(picked[0])
	var color: Array = picked[1]
	var width: int = measure.call(label, 18).x + 24
	var box := [ORIGIN.x, ORIGIN.y + CHIP_HEIGHT + 6, width, BADGE_HEIGHT]
	var radius := BADGE_HALF
	_fill(box, BADGE_TOP, BADGE_BOTTOM, BADGE_SOLID, radius, cheap_alpha)
	var edge := [int(color[0] * 0.6), int(color[1] * 0.6), int(color[2] * 0.6)]
	_ops.append(_rect(box, edge, 1, radius))
	_swords(int(box[0]) + 15, int(box[1]) + BADGE_HALF, 0.55, color)
	_ops.append(_text(label, 18, "body_semibold", color, int(box[0]) + 27, int(box[1]) + 4))


func _fill(
	box: Array, top: Array, bottom: Array, solid: Array, radius: int, cheap_alpha: bool
) -> void:
	if cheap_alpha:
		var gradient := {
			"kind": "vgrad",
			"rect": box.duplicate(),
			"top": top.duplicate(),
			"bottom": bottom.duplicate(),
			"radius": radius,
			"mult": 255,
		}
		_ops.append(gradient)
	else:
		_ops.append(_rect(box, solid, 0, radius))


## `ui_theme.draw_icon(surf, "coin", cx, cy, color, s)`; the coin ignores `color`.
func _coin(cx: int, cy: int, s: float) -> void:
	_ops.append(_circle([cx, cy], 9 * s, COIN_FILL, 0))
	_ops.append(_circle([cx, cy], 9 * s, COIN_EDGE, 2))
	_ops.append(_circle([cx, cy], 5 * s, COIN_INNER, 0))
	_ops.append(_line([cx, cy - 3.5 * s], [cx, cy + 3.5 * s], COIN_EDGE, 2))


## `ui_theme.draw_icon(surf, "swords", cx, cy, color, s)`.
func _swords(cx: int, cy: int, s: float, color: Array) -> void:
	_ops.append(_line([cx - 8 * s, cy - 8 * s], [cx + 8 * s, cy + 8 * s], color, 3))
	_ops.append(_line([cx + 8 * s, cy - 8 * s], [cx - 8 * s, cy + 8 * s], color, 3))
	_ops.append(_line([cx - 9 * s, cy + 5 * s], [cx - 5 * s, cy + 9 * s], ICON_DARK, 3))
	_ops.append(_line([cx + 9 * s, cy + 5 * s], [cx + 5 * s, cy + 9 * s], ICON_DARK, 3))
	_ops.append(_circle([cx, cy], 2.5 * s, color, 0))


static func _rgba(color: Array) -> Array:
	return [int(color[0]), int(color[1]), int(color[2]), 255]


static func _rect(box: Array, color: Array, width: int, radius: int) -> Dictionary:
	return {
		"kind": "rect",
		"rect": box.duplicate(),
		"color": _rgba(color),
		"mult": 255,
		"width": width,
		"radius": radius,
	}


static func _circle(center: Array, radius: float, color: Array, width: int) -> Dictionary:
	return {
		"kind": "circle",
		"center": center.duplicate(),
		"radius": radius,
		"color": _rgba(color),
		"mult": 255,
		"width": width,
	}


static func _line(a: Array, b: Array, color: Array, width: int) -> Dictionary:
	return {"kind": "line", "a": a, "b": b, "color": _rgba(color), "mult": 255, "width": width}


static func _text(
	words: String, size: int, style: String, color: Array, x: int, y: int
) -> Dictionary:
	return {
		"kind": "text",
		"text": words,
		"size": size,
		"style": style,
		"color": _rgba(color),
		"mult": 255,
		"pos": [x, y],
	}
