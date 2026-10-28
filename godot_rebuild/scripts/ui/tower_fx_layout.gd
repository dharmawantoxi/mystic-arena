extends RefCounted
## Layer 9bv14: the three `Tower.draw` blocks that 9bl left behind (selected range,
## upgrade flash, and archer muzzle glow). View-only ops: no simulation or input writes.

const RANGE_FILL_ALPHA := 40
const RANGE_BORDER_ALPHA := 150
const UPGRADE_FLASH_TICKS := 30
const UPGRADE_FLASH_MAX_ALPHA := 200
const UPGRADE_RGB := [255, 255, 200]
const MUZZLE_OUTER_RGB := [255, 240, 150]
const MUZZLE_INNER_RGB := [255, 255, 200]
const MUZZLE_TICKS := 8
const BOW_SCALE := 0.7
const BOW_CANVAS_CENTER_X := 70.0
const BOW_CANVAS_BASE_Y := 153.0
const BOW_FINAL_Y_OFFSET := -94.0
## `_NS_archer_tower.LEVEL_CONFIGS[1..6]['tower_h']`; also `bow_platform_height` in .tres.
const BOW_HEIGHTS := [38, 42, 46, 52, 56, 62]


static func color_for(tower_path: String) -> Array:
	match tower_path:
		"archer":
			return [100, 220, 120]
		"cannon":
			return [200, 100, 60]
		"ice":
			return [120, 200, 255]
		"mage":
			return [180, 80, 220]
		_:
			return [255, 255, 255]


## Fixture replay: source `Tower.draw` order is range, upgrade flash, body, muzzle glow.
static func ops(state: Dictionary) -> Array:
	var result := before_ops(state)
	result.append_array(after_ops(state))
	return result


## Painted before the baked tower body (`Tower.draw` puts both here).
static func before_ops(state: Dictionary) -> Array:
	var result: Array = []
	var x := int(state.get("x", 0.0))
	var y := int(state.get("y", 0.0))
	var center := [x, y]
	if bool(state.get("selected", false)):
		var radius := int(state.get("range", 0))
		var rgb: Array = state.get("color", [255, 255, 255])
		result.append(_circle(center, radius, _rgba(rgb, RANGE_FILL_ALPHA), 0))
		result.append(_circle(center, radius, _rgba(rgb, RANGE_BORDER_ALPHA), 2))
	var upgrade_flash := int(state.get("upgrade_flash", 0))
	if upgrade_flash > 0:
		var alpha := int(float(upgrade_flash) / UPGRADE_FLASH_TICKS * UPGRADE_FLASH_MAX_ALPHA)
		result.append(_circle(center, 30, UPGRADE_RGB + [alpha], 0))
	return result


## Painted after the baked tower body, before its HP/shield bars.
static func after_ops(state: Dictionary) -> Array:
	if (
		String(state.get("tower_type", "")) != "archer"
		or int(state.get("shoot_flash_timer", 0)) <= 0
	):
		return []
	var timer := int(state.get("shoot_flash_timer", 0))
	var intensity := float(timer) / float(MUZZLE_TICKS)
	var size := int(5.0 * intensity)
	if size <= 0:
		return []
	var point := bow_position(state)
	var center := [point.x, point.y]
	return [
		_circle(center, size * 2, MUZZLE_OUTER_RGB + [int(120.0 * intensity)], 0),
		_circle(center, size, MUZZLE_INNER_RGB + [int(200.0 * intensity)], 0),
	]


## `towers/_bundle.py::_NS_archer_tower.get_archer_bow_position`, with the source's
## clamped level and `bow_platform_height` standing in for `LEVEL_CONFIGS[level]['tower_h']`.
static func bow_position(state: Dictionary) -> Vector2i:
	var x := float(state.get("x", 0.0))
	var y := float(state.get("y", 0.0))
	var level := clampi(int(state.get("level", 1)), 1, BOW_HEIGHTS.size())
	var height := float(state.get("bow_platform_height", BOW_HEIGHTS[level - 1]))
	var face := 1
	var target_x: Variant = state.get("target_x")
	if target_x != null and float(target_x) <= x:
		face = -1
	var archer_y := BOW_CANVAS_BASE_Y - height - 10.0
	var bow_x_canvas := 77.0 if face > 0 else 63.0
	var bow_y_canvas := archer_y - 1.0
	var world_x := int(x + (bow_x_canvas - BOW_CANVAS_CENTER_X) * BOW_SCALE)
	var world_y := int(y + BOW_FINAL_Y_OFFSET + bow_y_canvas * BOW_SCALE)
	return Vector2i(world_x, world_y)


static func _rgba(rgb: Array, alpha: int) -> Array:
	var color: Array = rgb.duplicate()
	while color.size() < 3:
		color.append(255)
	return [color[0], color[1], color[2], alpha]


static func _circle(center: Array, radius: int, rgb: Array, width: int) -> Dictionary:
	return {
		"kind": "circle",
		"center": center.duplicate(),
		"radius": radius,
		"color": rgb.duplicate(),
		"mult": 255,
		"width": width,
	}
