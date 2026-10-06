extends RefCounted
## Source map_components.themes colors, data only; no decorations/FX ported.

const DATA := "res://data/levels/theme_palette.json"
const RIVER := "res://data/levels/river_path.json"
static var _palettes: Dictionary = {}
static var _river: PackedVector2Array = PackedVector2Array()


static func for_theme(name: String) -> Dictionary:
	if _palettes.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA))
		if parsed is Dictionary:
			_palettes = parsed
	var row: Dictionary = _palettes.get(name, _palettes.get("forest", {}))
	var colors := {}
	for key in row:
		var rgb: Array = row[key]
		colors[key] = Color8(int(rgb[0]), int(rgb[1]), int(rgb[2]))
	return colors


static func for_level(config: Dictionary) -> Dictionary:
	return for_theme(String(config.get("map_theme", "forest")))


static func river_path() -> PackedVector2Array:
	if _river.is_empty():
		var rows: Variant = JSON.parse_string(FileAccess.get_file_as_string(RIVER))
		if rows is Array:
			for point in rows:
				_river.append(Vector2(int(point[0]), int(point[1])))
	return _river.duplicate()
