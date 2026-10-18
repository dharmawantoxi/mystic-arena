extends RefCounted
## Layer 9bb: the DRAW of `_render.py::KillFeed` as a pure op list.
##
## `ops()` replays `KillFeed.draw()` and returns dictionaries in source order,
## three per visible entry (backing box, team-colour border, text):
##   fill {rect, color, mult}; rect {rect, color, mult, width, radius};
##   text {text, size, style, color, mult, pos, w, h}.
## `color` is RGBA 0..255 and `mult` the pygame surface alpha the op was
## blitted with (255 = opaque). Text metrics come from the `measure` callable
## (`text, size -> Vector2i`) so the oracle's fake font and the real font share
## the same layout code. `kill_feed_draw_source_oracle.py` pins every op.

const BASE_INSET_X := 20
const BASE_Y := 250
const FONT_SIZE := 22
const FONT_STYLE := "body_medium"
const FADE_IN_TICKS := 15
const FADE_OUT_TICKS := 45
const SLIDE_DISTANCE := 100.0
## `text_rect.inflate(12, 4)` keeps the centre: 6 px left and 2 px up.
const BOX_INSET_X := 6
const BOX_INSET_Y := 2
const BORDER_WIDTH := 1
const BORDER_RADIUS := 3


## Source alpha: fade in over the first 15 ticks of life, hold, then fade out
## over the last 45. A fresh entry (lifetime == max) is fully transparent.
static func fade_alpha(lifetime: int, max_lifetime: int) -> int:
	if lifetime > FADE_OUT_TICKS:
		if lifetime > max_lifetime - FADE_IN_TICKS:
			return int(255.0 * (float(max_lifetime - lifetime) / float(FADE_IN_TICKS)))
		return 255
	return int(255.0 * (float(lifetime) / float(FADE_OUT_TICKS)))


## Source slide-in: the entry starts 100 px right of the anchor and settles
## over the same 15 ticks as the fade-in.
static func slide_x(lifetime: int, max_lifetime: int) -> int:
	if lifetime > max_lifetime - FADE_IN_TICKS:
		var progress := float(max_lifetime - lifetime) / float(FADE_IN_TICKS)
		return int((1.0 - progress) * SLIDE_DISTANCE)
	return 0


## Every visible entry in list order. `entries` is `KillFeed.entries`.
static func ops(entries: Array, screen_w: int, measure: Callable) -> Array:
	var result: Array = []
	for entry_value in entries:
		var entry: Dictionary = entry_value
		var life: int = int(entry.get("lifetime", 0))
		var max_life: int = int(entry.get("max_lifetime", 0))
		var alpha := fade_alpha(life, max_life)
		if alpha > 0:
			result.append_array(
				_entry_ops(entry, alpha, slide_x(life, max_life), screen_w, measure)
			)
	return result


static func _entry_ops(
	entry: Dictionary, alpha: int, slide: int, screen_w: int, measure: Callable
) -> Array:
	var text: String = String(entry.get("text", ""))
	var ink := _rgb(entry.get("color", [255, 255, 255]))
	var extent: Vector2i = measure.call(text, FONT_SIZE)
	var left := screen_w - BASE_INSET_X + slide - extent.x
	var top := BASE_Y + int(float(entry.get("y_offset", 0.0)))
	var box := [
		left - BOX_INSET_X,
		top - BOX_INSET_Y,
		extent.x + 2 * BOX_INSET_X,
		extent.y + 2 * BOX_INSET_Y
	]
	var half := alpha >> 1
	return [
		{"kind": "fill", "rect": box, "color": [0, 0, 0, half], "mult": 255},
		{
			"kind": "rect",
			"rect": box.duplicate(),
			"color": [ink[0], ink[1], ink[2], half],
			"mult": 255,
			"width": BORDER_WIDTH,
			"radius": BORDER_RADIUS,
		},
		{
			"kind": "text",
			"text": text,
			"size": FONT_SIZE,
			"style": FONT_STYLE,
			"color": [ink[0], ink[1], ink[2], 255],
			"mult": alpha,
			"pos": [left, top],
			"w": extent.x,
			"h": extent.y,
		},
	]


## `KillFeed.entries` carry a `Color`; the oracle fixture carries `[r, g, b]`.
static func _rgb(value: Variant) -> Array:
	if value is Color:
		var tint: Color = value
		return [tint.r8, tint.g8, tint.b8]
	var parts: Array = value
	return [int(parts[0]), int(parts[1]), int(parts[2])]
