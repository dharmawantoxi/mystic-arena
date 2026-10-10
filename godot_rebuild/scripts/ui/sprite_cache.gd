class_name SpriteCache
extends RefCounted
## State-only port of `_render.py::SpriteCache`.
##
## Pygame surfaces and pixel drawing are intentionally not ported. A cached
## surface is represented by a small Dictionary carrying its dimensions and
## callback-owned metadata, so callers can replay cache state and draw their
## own Godot representation. `render_func` receives that Dictionary and may
## populate its metadata just as the source callback populates a Surface.

const DEFAULT_MAX_CACHE := 2000

static var _shared: SpriteCache

var max_cache := DEFAULT_MAX_CACHE
var _cache: Array = []
var _cropped: Array = []
var _hits := 0
var _misses := 0
var _surface_serial := 0


## Godot cannot replace Python's __new__ singleton hook, so this is the
## equivalent shared instance used by the source module-level shortcuts.
static func get_shared() -> SpriteCache:
	if _shared == null:
		_shared = SpriteCache.new()
	return _shared


static func reset_shared() -> void:
	_shared = null


static func get_cached_sprite(
	cache_key: Variant, width: int, height: int, render_func: Callable
) -> Variant:
	return get_shared().get_or_render(cache_key, width, height, render_func)


static func get_cached_sprite_cropped(
	cache_key: Variant, width: int, height: int, render_func: Callable, anchor: Variant = null
) -> Variant:
	return get_shared().get_or_render_cropped(cache_key, width, height, render_func, anchor)


static func clear_sprite_cache() -> void:
	get_shared().clear()


func set_max_cache(limit: int) -> void:
	max_cache = limit


func get_or_render(cache_key: Variant, width: int, height: int, render_func: Callable) -> Variant:
	var cache_index: int = _find_entry(_cache, cache_key)
	if cache_index >= 0:
		_hits += 1
		var cached_entry: Dictionary = _cache[cache_index]
		return cached_entry["surface"]

	_misses += 1
	var surface: Dictionary = _new_surface(width, height)
	render_func.call(surface)
	_cache.append({"key": cache_key, "surface": surface})
	_evict_oldest(_cache)
	return surface


func get_or_render_cropped(
	cache_key: Variant, width: int, height: int, render_func: Callable, anchor: Variant = null
) -> Variant:
	var cache_index: int = _find_entry(_cropped, cache_key)
	if cache_index >= 0:
		_hits += 1
		var cached_entry: Dictionary = _cropped[cache_index]
		return cached_entry["value"]

	_misses += 1
	var anchor_value: Array
	if anchor == null:
		anchor_value = [width / 2, height / 2]
	else:
		anchor_value = (anchor as Array).duplicate()
	var anchor_x: int = int(anchor_value[0])
	var anchor_y: int = int(anchor_value[1])
	var surface: Dictionary = _new_surface(width, height)
	render_func.call(surface)
	var bounds: Dictionary = _get_surface_bounds(surface)
	var entry: Array
	if int(bounds["width"]) <= 0 or int(bounds["height"]) <= 0:
		entry = [surface, anchor_x, anchor_y]
	else:
		var cropped: Dictionary = _copy_surface_region(surface, bounds)
		entry = [cropped, anchor_x - int(bounds["x"]), anchor_y - int(bounds["y"])]

	_cropped.append({"key": cache_key, "value": entry})
	_evict_oldest(_cropped)
	return entry


func invalidate(prefix: Variant = null) -> void:
	if prefix == null:
		_cache.clear()
		_cropped.clear()
		return

	var keys_to_remove: Array = []
	for entry_value in _cache:
		var entry: Dictionary = entry_value
		var key: Variant = entry["key"]
		if _has_prefix(key, prefix):
			keys_to_remove.append(key)
	for key in keys_to_remove:
		_remove_key(_cache, key)
		_remove_key(_cropped, key)


func clear() -> void:
	_cache.clear()
	_cropped.clear()


func get_stats() -> Dictionary:
	var total: int = _hits + _misses
	var hit_rate := 0.0
	if total > 0:
		hit_rate = float(_hits) / float(total) * 100.0
	return {
		"cached": _cache.size() + _cropped.size(),
		"hits": _hits,
		"misses": _misses,
		"hit_rate": "%.1f%%" % hit_rate,
	}


## State getter for callers that need cache lifecycle without exposing entries.
func get_state() -> Dictionary:
	var stats: Dictionary = get_stats()
	return {
		"cached": stats["cached"],
		"hits": stats["hits"],
		"misses": stats["misses"],
		"hit_rate": stats["hit_rate"],
		"max_cache": max_cache,
		"full_entries": _cache.size(),
		"cropped_entries": _cropped.size(),
	}


## Presentation-safe view of the state-only surface placeholder.
func get_surface_snapshot(surface: Variant) -> Dictionary:
	if not (surface is Dictionary):
		return {}
	var value: Dictionary = surface
	return {
		"width": int(value.get("width", 0)),
		"height": int(value.get("height", 0)),
		"marker": value.get("marker", null),
	}


func _new_surface(width: int, height: int) -> Dictionary:
	_surface_serial += 1
	return {
		"width": width,
		"height": height,
		"bounds": [0, 0, 0, 0],
		"marker": null,
		"serial": _surface_serial,
	}


func _get_surface_bounds(surface: Dictionary) -> Dictionary:
	var value: Variant = surface.get("bounds", [0, 0, 0, 0])
	if value is Array and (value as Array).size() >= 4:
		var bounds: Array = value
		return {
			"x": int(bounds[0]),
			"y": int(bounds[1]),
			"width": int(bounds[2]),
			"height": int(bounds[3]),
		}
	return {"x": 0, "y": 0, "width": 0, "height": 0}


func _copy_surface_region(surface: Dictionary, bounds: Dictionary) -> Dictionary:
	var cropped := _new_surface(int(bounds["width"]), int(bounds["height"]))
	cropped["bounds"] = [0, 0, int(bounds["width"]), int(bounds["height"])]
	cropped["marker"] = surface.get("marker", null)
	return cropped


func _find_entry(entries: Array, cache_key: Variant) -> int:
	for index in range(entries.size()):
		var entry: Dictionary = entries[index]
		if entry["key"] == cache_key:
			return index
	return -1


func _remove_key(entries: Array, cache_key: Variant) -> void:
	var index: int = _find_entry(entries, cache_key)
	if index >= 0:
		entries.remove_at(index)


func _evict_oldest(entries: Array) -> void:
	if entries.size() > max_cache:
		entries.remove_at(0)


func _has_prefix(cache_key: Variant, prefix: Variant) -> bool:
	if not (cache_key is Array):
		return false
	var key: Array = cache_key
	return key.size() > 0 and key[0] == prefix
