extends RefCounted
## Source draw command parity; terrain visual RNG is independent of gameplay.

const Palette = preload("res://scripts/ui/terrain_palette.gd")
const TerrainTiles = preload("res://scripts/ui/terrain_tiles.gd")
const FIXTURE := "res://data/levels/terrain_tiles.json"


func run(check: Callable) -> void:
	var fixture: Array = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var commands := TerrainTiles.commands()
	check.call(
		fixture.size() == 8091 and commands.size() == fixture.size(), "Source terrain commands"
	)
	for index in range(fixture.size()):
		check.call(commands[index].size() == fixture[index].size(), "Terrain shape %d" % index)
		for field in range(fixture[index].size()):
			check.call(
				int(commands[index][field]) == int(fixture[index][field]),
				"Terrain %d/%d" % [index, field]
			)
	commands[0][0] = -1
	check.call(int(TerrainTiles.commands()[0][0]) == 0, "Terrain commands cannot be mutated")
	for name in ["forest", "desert"]:
		var colors := Palette.for_theme(name)
		var image := TerrainTiles.raster(colors)
		check.call(image.get_width() == 1280 and image.get_height() == 720, "Terrain image size")
		check.call(image.get_pixel(0, 0) == colors["dire_earth_2"], "Source dire terrain %s" % name)
		check.call(
			image.get_pixel(0, 719) == colors["radiant_grass_2"], "Source radiant terrain %s" % name
		)
		check.call(
			image.get_pixel(640, 352) == colors["transition_1"], "Source transition %s" % name
		)
