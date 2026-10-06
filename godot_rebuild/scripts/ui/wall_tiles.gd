extends RefCounted
## Source border-wall block/spike commands. Rectangles match source geometry;
## triangle edge pixels use Godot rasterization instead of pygame scanlines.

const DATA := "res://data/levels/wall_tiles.json"
const BOUNDS := Rect2i(0, 0, 1280, 720)
static var _commands: Array = []


static func commands() -> Array:
	if _commands.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA))
		if parsed is Array:
			_commands = parsed
	return _commands.duplicate(true)


static func raster() -> Image:
	var image := Image.create(1280, 720, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	var colors: Array[Color] = [
		Color8(12, 8, 12),
		Color8(55, 55, 65),
		Color8(95, 95, 105),
		Color8(135, 135, 145),
		Color8(175, 175, 185)
	]
	for row in commands():
		var ink: Color = colors[int(row[1])]
		match int(row[0]):
			0:
				_fill(image, Rect2i(int(row[2]), int(row[3]), int(row[4]), int(row[5])), ink)
			1:
				_triangle(
					image,
					Vector2i(int(row[2]), int(row[3])),
					Vector2i(int(row[4]), int(row[5])),
					Vector2i(int(row[6]), int(row[7])),
					ink
				)
			2:
				var start := Vector2i(int(row[2]), int(row[3]))
				var end := Vector2i(int(row[4]), int(row[5]))
				_fill(image, Rect2i(start, Vector2i(1, end.y - start.y + 1)), ink)
	return image


static func _fill(image: Image, rect: Rect2i, color: Color) -> void:
	var clipped := rect.intersection(BOUNDS)
	if clipped.has_area():
		image.fill_rect(clipped, color)


static func _edge(a: Vector2i, b: Vector2i, p: Vector2i) -> int:
	return (p.x - a.x) * (b.y - a.y) - (p.y - a.y) * (b.x - a.x)


static func _triangle(image: Image, a: Vector2i, b: Vector2i, c: Vector2i, ink: Color) -> void:
	var min_x := maxi(0, mini(a.x, mini(b.x, c.x)))
	var max_x := mini(1279, maxi(a.x, maxi(b.x, c.x)))
	var min_y := maxi(0, mini(a.y, mini(b.y, c.y)))
	var max_y := mini(719, maxi(a.y, maxi(b.y, c.y)))
	for y in range(min_y, max_y + 1):
		for x in range(min_x, max_x + 1):
			var p := Vector2i(x, y)
			var ab := _edge(a, b, p)
			var bc := _edge(b, c, p)
			var ca := _edge(c, a, p)
			if (ab >= 0 and bc >= 0 and ca >= 0) or (ab <= 0 and bc <= 0 and ca <= 0):
				image.set_pixelv(p, ink)
