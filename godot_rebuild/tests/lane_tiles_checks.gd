extends RefCounted
## Source command order and a few image pixels; GPU presentation is separate.

const Palette = preload("res://scripts/ui/terrain_palette.gd")
const LaneTiles = preload("res://scripts/ui/lane_tiles.gd")
const FIXTURE := "res://data/levels/lane_tiles.json"


func run(check: Callable) -> void:
	var fixture: Array = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var commands := LaneTiles.commands()
	check.call(
		fixture.size() == 6654 and commands.size() == fixture.size(), "Source lane command count"
	)
	for index in range(fixture.size()):
		for field in range(6):
			check.call(
				int(commands[index][field]) == int(fixture[index][field]),
				"Lane rect %d/%d" % [index, field]
			)
	commands[0][0] = -1
	check.call(int(LaneTiles.commands()[0][0]) >= 0, "Lane command cache cannot be mutated")
	for name in ["forest", "desert"]:
		var colors := Palette.for_theme(name)
		var image := LaneTiles.raster(colors)
		check.call(image.get_width() == 1280 and image.get_height() == 720, "Lane layer size")
		check.call(
			image.get_pixel(90, 600) == colors["path_stone_1"], "Source stone base %s" % name
		)
		check.call(image.get_pixel(0, 0).a == 0.0, "Terrain outside lanes stays transparent")
