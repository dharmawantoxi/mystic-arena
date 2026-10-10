class_name RenderCache
extends RefCounted
## State-only port of `_render.py::RenderCache`.
##
## Pygame Font and Surface objects, plus their pixel drawing, are intentionally
## not ported. Cached resources are Dictionary state with the source dimensions,
## colours and draw-local metadata exposed through getters.

const FONT_MIN := 8
const FONT_MAX := 220

static var _shared: RenderCache

var _fonts: Array = []
var _circles: Array = []
var _surfaces: Array = []
var _font_creations := 0
var _surface_creations := 0
var _serial := 0


static func get_shared() -> RenderCache:
	if _shared == null:
		_shared = RenderCache.new()
	return _shared


static func reset_shared() -> void:
	_shared = null


static func get_cached_font(size: int, style: String = "body", bold: bool = false) -> Variant:
	return get_shared().get_font(size, style, bold)


static func get_cached_circle(radius: int, color: Array, width: int = 0) -> Variant:
	return get_shared().get_circle_surface(radius, color, width)


static func get_cached_glow(radius: int, color: Array, layers: int = 5) -> Variant:
	return get_shared().get_glow_surface(radius, color, layers)


static func clear_shared_cache() -> void:
	get_shared().clear()


func get_font(size: int, style: String = "body", bold: bool = false) -> Variant:
	var clamped_size: int = clampi(size, FONT_MIN, FONT_MAX)
	var key: Array = [clamped_size, style, bold]
	var cache_index: int = _find_entry(_fonts, key)
	if cache_index >= 0:
		var cached_entry: Dictionary = _fonts[cache_index]
		return cached_entry["value"]

	_font_creations += 1
	var font: Dictionary = {
		"kind": "font",
		"size": clamped_size,
		"style": style,
		"bold": bold,
		"serial": _next_serial(),
	}
	_fonts.append({"key": key, "value": font})
	return font


func get_circle_surface(radius: int, color: Array, width: int = 0) -> Variant:
	var clamped_color: Array = _clamp_color(color)
	var key: Array = [radius, clamped_color, width]
	var cache_index: int = _find_entry(_circles, key)
	if cache_index >= 0:
		var cached_entry: Dictionary = _circles[cache_index]
		return cached_entry["value"]

	_surface_creations += 1
	var size: int = radius * 2 + 4
	var surface: Dictionary = _new_surface(size, size)
	surface["color"] = clamped_color.duplicate()
	surface["draw_calls"] = [
		{
			"color": clamped_color.duplicate(),
			"center": [int(size / 2), int(size / 2)],
			"radius": radius,
			"width": width,
		}
	]
	_circles.append({"key": key, "value": surface})
	return surface


func get_glow_surface(radius: int, color: Array, layers: int = 5) -> Variant:
	var color_rgb: Array = color.slice(0, 3)
	var key: Array = ["glow", radius, color_rgb, layers]
	var cache_index: int = _find_entry(_surfaces, key)
	if cache_index >= 0:
		var cached_entry: Dictionary = _surfaces[cache_index]
		return cached_entry["value"]

	_surface_creations += 1
	var size: int = radius * 2 + 4
	var surface: Dictionary = _new_surface(size, size)
	var draws: Array = []
	var cx: int = int(size / 2)
	var cy: int = int(size / 2)
	var radius_step: int = int(radius / layers)
	var alpha_step: int = int(200 / layers)
	for index in range(layers):
		var layer_radius: int = radius - index * radius_step
		if layer_radius <= 0:
			continue
		var alpha: int = (layers - index) * alpha_step
		alpha = clampi(alpha, 0, 255)
		(
			draws
			. append(
				{
					"color": [int(color_rgb[0]), int(color_rgb[1]), int(color_rgb[2]), alpha],
					"center": [cx, cy],
					"radius": layer_radius,
					"width": 0,
				}
			)
		)
	surface["color"] = color_rgb.duplicate()
	surface["layers"] = layers
	surface["draw_calls"] = draws
	_surfaces.append({"key": key, "value": surface})
	return surface


func clear() -> void:
	_circles.clear()
	_surfaces.clear()


func get_stats() -> Dictionary:
	return {
		"fonts": _fonts.size(),
		"circles": _circles.size(),
		"surfaces": _surfaces.size(),
	}


func get_state() -> Dictionary:
	var stats: Dictionary = get_stats()
	return {
		"fonts": stats["fonts"],
		"circles": stats["circles"],
		"surfaces": stats["surfaces"],
		"font_creations": _font_creations,
		"surface_creations": _surface_creations,
	}


func get_font_snapshot(font: Variant) -> Dictionary:
	if not (font is Dictionary):
		return {}
	var value: Dictionary = font
	return {
		"size": int(value.get("size", 0)),
		"style": String(value.get("style", "")),
		"bold": bool(value.get("bold", false)),
	}


func get_surface_snapshot(surface: Variant) -> Dictionary:
	if not (surface is Dictionary):
		return {}
	var value: Dictionary = surface
	return {
		"width": int(value.get("width", 0)),
		"height": int(value.get("height", 0)),
		"draw_calls": (value.get("draw_calls", []) as Array).duplicate(true),
	}


func _new_surface(width: int, height: int) -> Dictionary:
	return {
		"kind": "surface",
		"width": width,
		"height": height,
		"serial": _next_serial(),
		"draw_calls": [],
	}


func _next_serial() -> int:
	_serial += 1
	return _serial


func _clamp_color(color: Array) -> Array:
	var count: int = 4 if color.size() == 4 else 3
	var result: Array = []
	for index in range(count):
		result.append(clampi(int(color[index]), 0, 255))
	return result


func _find_entry(entries: Array, key: Array) -> int:
	for index in range(entries.size()):
		var entry: Dictionary = entries[index]
		if _keys_equal(entry["key"], key):
			return index
	return -1


func _keys_equal(left: Variant, right: Variant) -> bool:
	if typeof(left) != typeof(right):
		return false
	if left is Array:
		var left_array: Array = left
		var right_array: Array = right
		if left_array.size() != right_array.size():
			return false
		for index in range(left_array.size()):
			if not _keys_equal(left_array[index], right_array[index]):
				return false
		return true
	return left == right
