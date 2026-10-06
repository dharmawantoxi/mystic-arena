extends RefCounted
## 54 source theme palettes: gameplay palette lookup, not visual GPU parity.

const Palette = preload("res://scripts/ui/terrain_palette.gd")
const Catalog = preload("res://scripts/match/level_catalog.gd")
const DATA := "res://data/levels/theme_palette.json"
const RIVER := "res://data/levels/river_path.json"


func run(check: Callable) -> void:
	var fixture: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA))
	check.call(fixture is Dictionary and fixture.size() == 54, "All 54 source terrain themes")
	if not (fixture is Dictionary):
		return
	for number in range(1, Catalog.COUNT + 1):
		var config := Catalog.get_level_config(number)
		var theme: String = String(config.map_theme)
		var row: Dictionary = fixture[theme]
		var colors := Palette.for_level(config)
		check.call(colors.size() == row.size(), "Complete terrain theme level %d" % number)
		for key in row:
			var rgb: Array = row[key]
			check.call(
				colors[key] == Color8(int(rgb[0]), int(rgb[1]), int(rgb[2])),
				"Source color %s L%d" % [key, number]
			)
	var forest := Palette.for_theme("forest")
	check.call(Palette.for_theme("unknown") == forest, "Unknown theme falls back to forest")
	var rows: Array = JSON.parse_string(FileAccess.get_file_as_string(RIVER))
	var path := Palette.river_path()
	check.call(rows.size() == 61 and path.size() == rows.size(), "Source river spline length")
	for index in range(rows.size()):
		check.call(
			path[index] == Vector2(int(rows[index][0]), int(rows[index][1])),
			"Source river point %d" % index
		)
	path[0] = Vector2(-99, -99)
	check.call(
		Palette.river_path()[0] == Vector2(0, 200), "River path cache is immutable to callers"
	)
