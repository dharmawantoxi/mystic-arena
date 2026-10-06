extends RefCounted
## Terrain base/detail commands from source StaticRenderer, with a fixed
## visual RNG stream. Circles and 1px lines use Godot pixel rasterization.

const DATA := "res://data/levels/terrain_tiles.json"
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
	image.fill(Color.BLACK)
	var colors: Array[Color] = [
		palette["radiant_grass_1"],
		palette["radiant_grass_2"],
		palette["radiant_grass_3"],
		palette["radiant_grass_4"],
		palette["radiant_grass_high"],
		palette["radiant_moss"],
		palette["dire_earth_1"],
		palette["dire_earth_2"],
		palette["dire_earth_3"],
		palette["dire_earth_4"],
		palette["dire_ash"],
		palette["dire_burnt"],
		palette["transition_1"],
		palette["transition_2"],
		Color8(60, 60, 70)
	]
	for row in commands():
		var ink: Color = colors[int(row[1])]
		match int(row[0]):
			0:
				var rect := Rect2i(int(row[2]), int(row[3]), int(row[4]), int(row[5]))
				var clipped := rect.intersection(BOUNDS)
				if clipped.has_area():
					image.fill_rect(clipped, ink)
			1:
				_line(
					image,
					Vector2i(int(row[2]), int(row[3])),
					Vector2i(int(row[4]), int(row[5])),
					ink
				)
			2:
				_circle(image, Vector2i(int(row[2]), int(row[3])), int(row[4]), ink)
	return image


static func _circle(image: Image, center: Vector2i, radius: int, ink: Color) -> void:
	for y in range(maxi(0, center.y - radius), mini(719, center.y + radius) + 1):
		for x in range(maxi(0, center.x - radius), mini(1279, center.x + radius) + 1):
			var offset := Vector2i(x, y) - center
			if offset.length_squared() <= radius * radius:
				image.set_pixel(x, y, ink)


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
