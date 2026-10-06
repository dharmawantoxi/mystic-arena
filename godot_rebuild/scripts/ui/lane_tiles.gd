extends RefCounted
## Source StaticRenderer.draw_lane commands for top/mid/bot. Static tile
## colors/positions are source-derived; thin crack line pixels are a Godot
## Bresenham approximation, not Pygame's rasterizer.

const DATA := "res://data/levels/lane_tiles.json"
const BOUNDS := Rect2i(0, 0, 1280, 720)
static var _commands: Array = []


static func commands() -> Array:
	if _commands.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA))
		if parsed is Array:
			_commands = parsed
	return _commands.duplicate(true)


static func raster(palette: Dictionary) -> Image:
	var image := Image.create(1280, 720, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	var colors: Array[Color] = [
		palette["path_stone_1"],
		palette["path_stone_2"],
		palette["path_stone_3"],
		palette["path_stone_4"],
		palette["path_moss"],
		palette["path_crack"],
		palette["radiant_moss"],
		Color8(12, 8, 12),
		Color8(55, 55, 65),
		Color8(95, 95, 105),
		Color8(135, 135, 145),
		Color8(175, 175, 185)
	]
	for row in commands():
		var ink: Color = colors[int(row[0])]
		if int(row[5]) == -1:
			_line(
				image, Vector2i(int(row[1]), int(row[2])), Vector2i(int(row[3]), int(row[4])), ink
			)
		else:
			var rect := Rect2i(int(row[1]), int(row[2]), int(row[3]), int(row[4]))
			var clipped := rect.intersection(BOUNDS)
			if clipped.has_area():
				image.fill_rect(clipped, ink)
	return image


static func _line(image: Image, start: Vector2i, end: Vector2i, ink: Color) -> void:
	var at := start
	var dx := absi(end.x - start.x)
	var dy := absi(end.y - start.y)
	var sx := 1 if start.x < end.x else -1
	var sy := 1 if start.y < end.y else -1
	var error := dx - dy
	while true:
		if BOUNDS.has_point(at):
			image.set_pixelv(at, ink)
		if at == end:
			break
		var twice := error * 2
		if twice > -dy:
			error -= dy
			at.x += sx
		if twice < dx:
			error += dx
			at.y += sy
