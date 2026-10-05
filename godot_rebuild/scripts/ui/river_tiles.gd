extends RefCounted
## Static river layer from source StaticRenderer.draw_river rectangles. Source
## coordinates/order and theme colors; no animation or terrain decorations.

const DATA := "res://data/levels/river_tiles.json"
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
		palette["river_deep"],
		palette["river_mid"],
		palette["river_glow"],
		palette["river_foam"],
		Color8(55, 55, 65),
		Color8(95, 95, 105),
		Color8(135, 135, 145),
		Color8(12, 8, 12)
	]
	for row in commands():
		var rect := Rect2i(int(row[1]), int(row[2]), int(row[3]), int(row[4]))
		var ink: Color = colors[int(row[0])]
		if int(row[5]) == 0:
			_fill(image, rect, ink)
		else:
			_fill(image, Rect2i(rect.position, Vector2i(rect.size.x, 1)), ink)
			_fill(
				image,
				Rect2i(rect.position + Vector2i(0, rect.size.y - 1), Vector2i(rect.size.x, 1)),
				ink
			)
			_fill(image, Rect2i(rect.position, Vector2i(1, rect.size.y)), ink)
			_fill(
				image,
				Rect2i(rect.position + Vector2i(rect.size.x - 1, 0), Vector2i(1, rect.size.y)),
				ink
			)
	return image


static func _fill(image: Image, rect: Rect2i, color: Color) -> void:
	var clipped := rect.intersection(BOUNDS)
	if clipped.has_area():
		image.fill_rect(clipped, color)
