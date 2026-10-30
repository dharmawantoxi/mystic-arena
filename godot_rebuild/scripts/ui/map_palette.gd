extends RefCounted
## Source `map_components/palettes.py` colours plus `TILE_SIZE`.
##
## The 52 colours are theme-independent (stone, tree, crystal, fire, outline)
## and were hard-coded into three rasterisers before this loader existed.
## `data/levels/map_palette.json` is generated from the Pygame source by
## `tests/map_components_source_oracle.py`, so the map can no longer drift from
## `palettes.py` without the oracle failing.

const DATA := "res://data/levels/map_palette.json"
static var _cache: Dictionary = {}


static func data() -> Dictionary:
	if _cache.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA))
		if parsed is Dictionary:
			_cache = parsed
	return _cache


static func colors() -> Dictionary:
	return data().get("colors", {})


static func tile_size() -> int:
	return int(data().get("tile_size", 0))


static func color(name: String) -> Color:
	var value: Variant = colors().get(name)
	if not (value is Array):
		return Color(0, 0, 0, 0)
	var rgb: Array = value
	if rgb.size() < 3:
		return Color(0, 0, 0, 0)
	return Color8(int(rgb[0]), int(rgb[1]), int(rgb[2]))


static func palette(names: Array) -> Array[Color]:
	var result: Array[Color] = []
	for name in names:
		result.append(color(String(name)))
	return result
