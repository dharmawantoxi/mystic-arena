extends RefCounted
## Layer 9bv11: `HoverIndicators._draw_tower_range_hover` and
## `_draw_tower_tooltip` (`ui_components/_bundle.py`). This is a view-only op builder;
## it never changes selection, commands, or simulation state.

const RANGE_FILL := [100, 200, 255]
const RANGE_EDGE := [150, 220, 255]
const WHITE := [255, 255, 255]
const TOOLTIP_BG := [20, 25, 40]
const TOOLTIP_SHADOW := [0, 0, 0]
const FONT_SIZE := 24
const FONT_STYLE := "body_medium"
const DASH_COUNT := 24


## `state` contains x/y, range, animation_time, tower name/level/damage/kills/color.
## `measure` returns a Vector2i for (text, size), matching the view's font metrics.
static func ops(state: Dictionary, measure: Callable) -> Array:
	var result: Array = []
	var x := float(state.get("x", 0.0))
	var y := float(state.get("y", 0.0))
	var radius := int(state.get("range", 0))
	var animation_time := float(state.get("animation_time", 0.0))
	var pulse := sin(animation_time * 0.1) * 0.2 + 0.8
	var center_x := int(x)
	var center_y := int(y)
	result.append(_circle(center_x, center_y, radius, RANGE_FILL + [int(30 * pulse)], 0))
	result.append(_circle(center_x, center_y, radius, RANGE_EDGE + [int(180 * pulse)], 2))
	var local_center := radius + 4
	var surface_x := int(x) - radius - 4
	var surface_y := int(y) - radius - 4
	for i in range(0, DASH_COUNT, 2):
		var start_angle := float(i) / DASH_COUNT * TAU + animation_time * 0.02
		var end_angle := float(i + 1) / DASH_COUNT * TAU + animation_time * 0.02
		for angle in [start_angle, end_angle]:
			var dx := cos(angle) * (radius - 3)
			var dy := sin(angle) * (radius - 3)
			var dash_x := surface_x + int(local_center + dx)
			var dash_y := surface_y + int(local_center + dy)
			result.append(_circle(dash_x, dash_y, 2, WHITE + [200], 0))
	result.append_array(_tooltip_ops(state, measure, center_x, center_y))
	return result


static func _tooltip_ops(
	state: Dictionary, measure: Callable, tooltip_x: int, tower_y: int
) -> Array:
	var lines := [
		"%s Lv.%d" % [String(state.get("name", "")), int(state.get("level", 1))],
		"DMG: %d  RNG: %d" % [int(state.get("damage", 0)), int(state.get("range", 0))],
		"Kills: %d" % int(state.get("kills", 0)),
	]
	var sizes: Array[Vector2i] = []
	var max_width := 0
	var total_height := 0
	for line in lines:
		var size: Vector2i = measure.call(String(line), FONT_SIZE)
		sizes.append(size)
		max_width = maxi(max_width, size.x)
		total_height += size.y + 2
	var bg_width := max_width + 12
	var bg_height := total_height + 6
	var bg_x := tooltip_x - int(bg_width / 2)
	var bg_y := tower_y - 60 - bg_height
	var bg_rect := [bg_x, bg_y, bg_width, bg_height]
	var result: Array = [
		{
			"kind": "rect",
			"rect": bg_rect.duplicate(),
			"color": TOOLTIP_SHADOW + [100],
			"mult": 255,
			"width": 0,
			"radius": 4,
		},
		{
			"kind": "rect",
			"rect": bg_rect.duplicate(),
			"color": TOOLTIP_BG + [255],
			"mult": 255,
			"width": 0,
			"radius": 4,
		},
		{
			"kind": "rect",
			"rect": bg_rect.duplicate(),
			"color": _rgba(state.get("color", [255, 255, 255])),
			"mult": 255,
			"width": 2,
			"radius": 4,
		},
	]
	var text_y := bg_y + 4
	for index in range(lines.size()):
		var text_width: int = sizes[index].x
		(
			result
			. append(
				{
					"kind": "text",
					"text": String(lines[index]),
					"size": FONT_SIZE,
					"style": FONT_STYLE,
					"color": [255, 255, 255, 255],
					"mult": 255,
					"pos": [tooltip_x - int(text_width / 2), text_y],
				}
			)
		)
		text_y += sizes[index].y + 2
	(
		result
		. append(
			{
				"kind": "polygon",
				"points":
				[
					[tooltip_x - 4, bg_y + bg_height],
					[tooltip_x, bg_y + bg_height + 5],
					[tooltip_x + 4, bg_y + bg_height],
				],
				"color": _rgba(state.get("color", [255, 255, 255])),
				"mult": 255,
				"width": 0,
			}
		)
	)
	return result


static func _circle(
	center_x: int, center_y: int, radius: int, rgb: Array, width: int
) -> Dictionary:
	return {
		"kind": "circle",
		"center": [center_x, center_y],
		"radius": radius,
		"color": rgb.duplicate(),
		"mult": 255,
		"width": width,
	}


static func _rgba(value: Variant) -> Array:
	var color: Array = value.duplicate() if value is Array else [255, 255, 255]
	if color.size() == 3:
		color.append(255)
	return color
