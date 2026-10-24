extends RefCounted
## Layer 9bv3: `ShopHints.draw` (`ui_components/_bundle.py`), the two floating gold pills that
## open pygame's unshaken UI pass (`ui.draw_shop_hints`, before the gold HUD). Pure op
## builder; the ops use the `draw_recorder.py` shapes so `tests/shop_hint_draw_source_oracle.py`
## can pin them.
##
##   * `pulse = int(sin(animation_time * 0.06) * 2)` (truncated toward zero) bobs both pills;
##   * ITEM FORGE over the radiant shop (340, 540), centre (+82, -30); HERO SHOP over the dire
##     shop (940, 180), centre (-82, +44);
##   * the label is `ui_theme.letter(label)` (one space between characters), 14 px body_bold
##     `GOLD_TEXT` (255, 220, 110), its rect centred on the hint point (`x = cx - w // 2`);
##   * the pill is that rect inflated by (16, 8), radius `h // 2`, filled with `_vgrad`
##     (48, 42, 20) -> (24, 20, 9) when `cheap_alpha()` (solid (30, 24, 10) otherwise) and
##     edged 1 px in `GOLD` (255, 205, 85).

const HINTS := [
	[[340, 540], "ITEM FORGE", [82, -30]],
	[[940, 180], "HERO SHOP", [-82, 44]],
]
const FONT_SIZE := 14
const GOLD := [255, 205, 85]
const GOLD_TEXT := [255, 220, 110]
const PILL_TOP := [48, 42, 20]
const PILL_BOTTOM := [24, 20, 9]
const PILL_SOLID := [30, 24, 10]


static func pulse(animation_time: int) -> int:
	return int(sin(float(animation_time) * 0.06) * 2.0)


## `ui_theme.letter`: `gap.join(list(text))`.
static func letter(text: String, gap: String = " ") -> String:
	var characters := PackedStringArray()
	for index in range(text.length()):
		characters.append(text[index])
	return gap.join(characters)


static func ops(animation_time: int, measure: Callable, cheap_alpha: bool = true) -> Array:
	var out: Array = []
	var bob := pulse(animation_time)
	for hint in HINTS:
		var shop: Array = hint[0]
		var anchor: Array = hint[2]
		var label := letter(String(hint[1]))
		var size: Vector2i = measure.call(label, FONT_SIZE)
		var text_x := int(shop[0]) + int(anchor[0]) - (size.x >> 1)
		var text_y := int(shop[1]) + int(anchor[1]) + bob - (size.y >> 1)
		var pill := [text_x - 8, text_y - 4, size.x + 16, size.y + 8]
		var radius: int = int(pill[3]) >> 1
		if cheap_alpha:
			var gradient := {
				"kind": "vgrad",
				"rect": pill.duplicate(),
				"top": PILL_TOP.duplicate(),
				"bottom": PILL_BOTTOM.duplicate(),
				"radius": radius,
				"mult": 255,
			}
			out.append(gradient)
		else:
			out.append(_rect(pill, PILL_SOLID, 0, radius))
		out.append(_rect(pill, GOLD, 1, radius))
		var text := {
			"kind": "text",
			"text": label,
			"size": FONT_SIZE,
			"style": "body_bold",
			"color": _rgba(GOLD_TEXT),
			"mult": 255,
			"pos": [text_x, text_y],
		}
		out.append(text)
	return out


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
