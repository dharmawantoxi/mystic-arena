extends RefCounted
## Layer 9bv12: `HoverIndicators._draw_slot_hover` (`ui_components/_bundle.py`).
## This is a view-only op builder; it never changes selection, commands, or simulation state.

const GLOW_RGB := [100, 200, 255]
const BLACK := [0, 0, 0]
const WHITE := [255, 255, 255]
const HINT_TEXT := "TAP TO BUILD"
const HINT_FONT_SIZE := 20
const HINT_FONT_STYLE := "body"
const HINT_WIDTH := 100
const HINT_HEIGHT := 18


## `state` contains x/y and animation_time. `measure` returns a Vector2i for (text, size),
## matching the view's font metrics; the source uses `font_tiny` = `get_font(20, "body")`.
static func ops(state: Dictionary, measure: Callable) -> Array:
	var result: Array = []
	var center_x := int(state.get("x", 0.0))
	var center_y := int(state.get("y", 0.0))
	var animation_time := float(state.get("animation_time", 0.0))
	var pulse := sin(animation_time * 0.15) * 0.3 + 0.7
	for radius in range(35, 15, -3):
		var alpha := int((35 - radius) * 6 * pulse)
		if alpha > 0:
			result.append(_circle(center_x, center_y, radius, GLOW_RGB + [alpha]))
	var hint_rect := [center_x - 50, center_y - 36, HINT_WIDTH, HINT_HEIGHT]
	(
		result
		. append(
			{
				"kind": "rect",
				"rect": hint_rect.duplicate(),
				"color": BLACK + [200],
				"mult": 255,
				"width": 0,
				"radius": 3,
			}
		)
	)
	(
		result
		. append(
			{
				"kind": "rect",
				"rect": hint_rect.duplicate(),
				"color": GLOW_RGB + [255],
				"mult": 255,
				"width": 1,
				"radius": 3,
			}
		)
	)
	var text_size: Vector2i = measure.call(HINT_TEXT, HINT_FONT_SIZE)
	(
		result
		. append(
			{
				"kind": "text",
				"text": HINT_TEXT,
				"size": HINT_FONT_SIZE,
				"style": HINT_FONT_STYLE,
				"color": WHITE + [255],
				"mult": 255,
				"pos":
				[
					center_x - int(text_size.x / 2),
					center_y - 27 - int(text_size.y / 2),
				],
			}
		)
	)
	return result


static func _circle(center_x: int, center_y: int, radius: int, rgb: Array) -> Dictionary:
	return {
		"kind": "circle",
		"center": [center_x, center_y],
		"radius": radius,
		"color": rgb.duplicate(),
		"mult": 255,
		"width": 0,
	}
