extends RefCounted
## Source command order and stable inner block pixels (not GPU parity).

const WallTiles = preload("res://scripts/ui/wall_tiles.gd")
const FIXTURE := "res://data/levels/wall_tiles.json"


func run(check: Callable) -> void:
	var fixture: Array = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var commands := WallTiles.commands()
	check.call(fixture.size() == 1323 and commands.size() == fixture.size(), "Source wall commands")
	for index in range(fixture.size()):
		check.call(commands[index].size() == fixture[index].size(), "Wall shape %d" % index)
		for field in range(fixture[index].size()):
			check.call(
				int(commands[index][field]) == int(fixture[index][field]),
				"Wall %d/%d" % [index, field]
			)
	commands[0][0] = -1
	check.call(int(WallTiles.commands()[0][0]) == 0, "Wall commands cannot be mutated")
	var image := WallTiles.raster()
	check.call(image.get_width() == 1280 and image.get_height() == 720, "Wall image size")
	check.call(image.get_pixel(0, 0) == Color8(12, 8, 12), "Wall outer outline")
	check.call(image.get_pixel(2, 2) == Color8(175, 175, 185), "Wall highlight")
	check.call(image.get_pixel(5, 10) == Color8(95, 95, 105), "Wall middle stone")
	check.call(image.get_pixel(640, 350).a == 0.0, "Wall layer center transparent")
