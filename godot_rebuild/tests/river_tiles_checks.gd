extends RefCounted
## Source command order and selected pixels, headless (not GPU screenshot parity).

const Palette = preload("res://scripts/ui/terrain_palette.gd")
const RiverTiles = preload("res://scripts/ui/river_tiles.gd")
const FIXTURE := "res://data/levels/river_tiles.json"


func run(check: Callable) -> void:
	var fixture: Array = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var commands := RiverTiles.commands()
	check.call(
		fixture.size() == 1878 and commands.size() == fixture.size(), "Source tile command count"
	)
	for index in range(fixture.size()):
		for field in range(6):
			check.call(
				int(commands[index][field]) == int(fixture[index][field]),
				"River rect %d/%d" % [index, field]
			)
	commands[0][0] = -1
	check.call(int(RiverTiles.commands()[0][0]) >= 0, "Command cache cannot be mutated")
	for name in ["forest", "desert"]:
		var colors := Palette.for_theme(name)
		var image := RiverTiles.raster(colors)
		check.call(image.get_width() == 1280 and image.get_height() == 720, "River texture size")
		check.call(image.get_pixel(0, 192) == colors["river_mid"], "River mid tile %s" % name)
		check.call(image.get_pixel(10, 195) == colors["river_deep"], "River deep tile %s" % name)
		check.call(image.get_pixel(7, 175) == Color8(12, 8, 12), "Source bank outline")
		check.call(image.get_pixel(8, 176) == Color8(135, 135, 145), "Source bank highlight")
		check.call(image.get_pixel(0, 0).a == 0.0, "Terrain outside river stays transparent")
