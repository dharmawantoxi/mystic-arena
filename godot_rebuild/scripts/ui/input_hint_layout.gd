extends RefCounted
## Layer 9bv4: `ControllerManager.draw_hint_bar` (`_core.py`) with the defaults
## `Game._draw_input_hints` uses (`get_font(19)`, y = SCREEN_HEIGHT - 30, centred). Pure op
## builder; the ops use the `draw_recorder.py` shapes so
## `tests/input_hint_draw_source_oracle.py` can pin them.
##
##   * every (label, desc) item is `label_w + 2 * KEY_PAD + 5 + desc_w` wide, `GAP` apart;
##     the row starts at `(1280 - total_w) // 2` (floor, also when the row overflows);
##   * a (0, 0, 0, 140) strip `total_w + 2 * PAD_X` x `font_h + 8` at (x - PAD_X, y - 4);
##   * per item a radius-4 key box (48, 52, 70) at (x, y - 1), `label_w + 2 * KEY_PAD` x
##     `font_h + 2`, edged 1 px (120, 130, 165), the label (255, 235, 140) at (x + KEY_PAD, y)
##     and the description (205, 210, 225) at (x + key_w + 5, y).

const SCREEN_WIDTH := 1280
const BAR_Y := 690
const FONT_SIZE := 19
const PAD_X := 7
const GAP := 16
const KEY_PAD := 5
const STRIP := [0, 0, 0, 140]
const KEY_FILL := [48, 52, 70]
const KEY_EDGE := [120, 130, 165]
const LABEL_COLOR := [255, 235, 140]
const DESC_COLOR := [205, 210, 225]


## `hints` is `get_hints(context)`: `[label, desc]` pairs. An empty list paints nothing.
static func ops(hints: Array, measure: Callable) -> Array:
	var out: Array = []
	if hints.is_empty():
		return out
	var font_height: int = measure.call("", FONT_SIZE).y
	var items: Array = []
	var total_w := 0
	for hint in hints:
		var label := String(hint[0])
		var desc := String(hint[1])
		var label_w: int = measure.call(label, FONT_SIZE).x
		var width: int = label_w + KEY_PAD * 2 + 5 + measure.call(desc, FONT_SIZE).x
		items.append([label, desc, label_w, width])
		total_w += width + GAP
	total_w = maxi(0, total_w - GAP)
	var x := (SCREEN_WIDTH - total_w) >> 1
	var strip := {
		"kind": "fill",
		"rect": [x - PAD_X, BAR_Y - 4, total_w + PAD_X * 2, font_height + 8],
		"color": STRIP.duplicate(),
		"mult": 255,
		"blend": 0,
	}
	out.append(strip)
	for item in items:
		var key_w: int = int(item[2]) + KEY_PAD * 2
		var key := [x, BAR_Y - 1, key_w, font_height + 2]
		out.append(_rect(key, KEY_FILL, 0))
		out.append(_rect(key, KEY_EDGE, 1))
		out.append(_text(String(item[0]), LABEL_COLOR, x + KEY_PAD))
		out.append(_text(String(item[1]), DESC_COLOR, x + key_w + 5))
		x += int(item[3]) + GAP
	return out


static func _rect(box: Array, color: Array, width: int) -> Dictionary:
	return {
		"kind": "rect",
		"rect": box.duplicate(),
		"color": [int(color[0]), int(color[1]), int(color[2]), 255],
		"mult": 255,
		"width": width,
		"radius": 4,
	}


static func _text(words: String, color: Array, x: int) -> Dictionary:
	return {
		"kind": "text",
		"text": words,
		"size": FONT_SIZE,
		"style": "body",
		"color": [int(color[0]), int(color[1]), int(color[2]), 255],
		"mult": 255,
		"pos": [x, BAR_Y],
	}
