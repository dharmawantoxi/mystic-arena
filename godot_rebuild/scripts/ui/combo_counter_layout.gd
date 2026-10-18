extends RefCounted
## Layer 9bc: the DRAW of `_render.py::ComboCounter` as a pure op list.
##
## `ops()` replays `ComboCounter.draw()` and returns dictionaries in source
## order: the timer bar (two rects, from two kills on), the `x{count}` shadows
## and text, then the tier label shadow and text (from five kills on):
##   rect {rect, color, mult, width, radius};
##   text {text, size, style, color, mult, pos, w, h}.
## `color` is RGBA 0..255 and `mult` the pygame surface alpha (255 = opaque).
## Text metrics come from the `measure` callable (`text, size -> Vector2i`) so
## the oracle's fake font and the real font share the same layout code.
## `cheap_alpha` mirrors `mobile.perf.Quality.cheap_alpha`: true draws the 8-way
## count shadow, false the single (2, 2) one.
## `combo_counter_draw_source_oracle.py` pins every op.

const RIGHT_INSET := 100
const CENTER_Y := 100
const LABEL_RISE := 30
const BAR_DROP := 40
const BAR_WIDTH := 80
const BAR_HEIGHT := 4
const BAR_BACK := [40, 40, 40]
const COUNT_FONT := 48.0
const MIN_COUNT_SIZE := 8
const MIN_VISIBLE_SCALE := 0.1
const LABEL_SIZE := 24
const LABEL_MIN_COUNT := 5
const FLASH_TICKS := 20.0
const COUNT_STYLE := "body_bold"
const LABEL_STYLE := "body"
const SHADOW_RING := [[-2, -2], [-2, 0], [-2, 2], [0, -2], [0, 2], [2, -2], [2, 0], [2, 2]]
const SHADOW_SINGLE := [[2, 2]]
## `[minimum count, label, colour]`, highest tier first like the source `elif` chain.
const TIERS := [
	[20, "GODLIKE!", [255, 50, 50]],
	[15, "UNSTOPPABLE!", [255, 100, 50]],
	[10, "RAMPAGE!", [255, 200, 50]],
	[5, "KILLING SPREE!", [100, 255, 100]],
]
const BASE_TIER := [0, "COMBO", [255, 255, 255]]


## The fields `draw()` reads off a `ComboCounter` port.
static func state_of(counter) -> Dictionary:
	return {
		"count": counter.count,
		"timer": counter.timer,
		"max_timer": counter.max_timer,
		"display_scale": counter.display_scale,
		"color_flash": counter.color_flash,
	}


## Source tier ladder for `count`: the first `>=` match wins, else white COMBO.
static func tier(count: int) -> Array:
	for entry in TIERS:
		if count >= int(entry[0]):
			return entry
	return BASE_TIER


## Source flash: lerp the tier colour toward white by `color_flash / 20`.
static func flash_color(color: Array, color_flash: int) -> Array:
	if color_flash <= 0:
		return color.duplicate()
	var ratio := float(color_flash) / FLASH_TICKS
	var mixed: Array = []
	for channel in color:
		mixed.append(int(float(channel) + float(255 - int(channel)) * ratio))
	return mixed


## One frame of `draw()` for `state` (see `state_of`).
static func ops(
	state: Dictionary, screen_w: int, measure: Callable, cheap_alpha: bool = true
) -> Array:
	var count: int = int(state.get("count", 0))
	var display_scale: float = float(state.get("display_scale", 0.0))
	var result: Array = []
	if count < 2 and display_scale < MIN_VISIBLE_SCALE:
		return result
	var center_x := screen_w - RIGHT_INSET
	var entry := tier(count)
	var ink: Array = entry[2]
	if count >= 2:
		result.append_array(
			_bar_ops(center_x, ink, int(state.get("timer", 0)), int(state.get("max_timer", 1)))
		)
	var count_size := int(COUNT_FONT * display_scale)
	if count_size < MIN_COUNT_SIZE:
		return result
	var shown := flash_color(ink, int(state.get("color_flash", 0)))
	result.append_array(_count_ops(count, count_size, shown, center_x, measure, cheap_alpha))
	if count >= LABEL_MIN_COUNT:
		result.append_array(_label_ops(String(entry[1]), shown, center_x, measure))
	return result


static func _bar_ops(center_x: int, ink: Array, timer: int, max_timer: int) -> Array:
	var left := center_x - (BAR_WIDTH >> 1)
	var top := CENTER_Y + BAR_DROP
	var fill := int(float(BAR_WIDTH) * (float(timer) / float(max_timer)))
	return [
		_rect_op([left, top, BAR_WIDTH, BAR_HEIGHT], BAR_BACK),
		_rect_op([left, top, fill, BAR_HEIGHT], ink),
	]


static func _count_ops(
	count: int, size: int, shown: Array, center_x: int, measure: Callable, cheap_alpha: bool
) -> Array:
	var text: String = "x%d" % count
	var extent: Vector2i = measure.call(text, size)
	var left := center_x - (extent.x >> 1)
	var top := CENTER_Y - (extent.y >> 1)
	var offsets: Array = SHADOW_RING if cheap_alpha else SHADOW_SINGLE
	var result: Array = []
	for offset in offsets:
		var at := [left + int(offset[0]), top + int(offset[1])]
		result.append(_text_op(text, size, COUNT_STYLE, [0, 0, 0], at, extent))
	result.append(_text_op(text, size, COUNT_STYLE, shown, [left, top], extent))
	return result


static func _label_ops(label: String, shown: Array, center_x: int, measure: Callable) -> Array:
	var extent: Vector2i = measure.call(label, LABEL_SIZE)
	var left := center_x - (extent.x >> 1)
	var top := CENTER_Y - LABEL_RISE - (extent.y >> 1)
	return [
		_text_op(label, LABEL_SIZE, LABEL_STYLE, [0, 0, 0], [left + 1, top + 1], extent),
		_text_op(label, LABEL_SIZE, LABEL_STYLE, shown, [left, top], extent),
	]


static func _rect_op(box: Array, color: Array) -> Dictionary:
	return {
		"kind": "rect",
		"rect": box,
		"color": [color[0], color[1], color[2], 255],
		"mult": 255,
		"width": 0,
		"radius": 0,
	}


static func _text_op(
	text: String, size: int, style: String, color: Array, at: Array, extent: Vector2i
) -> Dictionary:
	return {
		"kind": "text",
		"text": text,
		"size": size,
		"style": style,
		"color": [color[0], color[1], color[2], 255],
		"mult": 255,
		"pos": at,
		"w": extent.x,
		"h": extent.y,
	}
