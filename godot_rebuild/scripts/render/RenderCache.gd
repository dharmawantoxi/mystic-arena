class_name RenderCache
extends RefCounted

## Native _render.py font system + RenderCache (circles/glow) + SpriteCache stats.
## Font files are shared; Godot rasterizes glyphs at draw time with the requested
## size, so no per-frame Surface allocation is needed.
const FONT_FILES := {
	"title": "res://assets/fonts/Cinzel.ttf",
	"body": "res://assets/fonts/Barlow-Regular.ttf",
	"body_medium": "res://assets/fonts/Barlow-Medium.ttf",
	"body_semibold": "res://assets/fonts/Barlow-SemiBold.ttf",
	"body_bold": "res://assets/fonts/Barlow-Bold.ttf",
}
static var _fonts: Dictionary = {}
static var _textures: Dictionary = {}
static var stats := {"font_hits": 0, "font_loads": 0, "texture_hits": 0, "texture_builds": 0}


static func font(style := "body") -> Font:
	var key := style if FONT_FILES.has(style) else "body"
	if _fonts.has(key):
		stats.font_hits += 1
		return _fonts[key]
	var path: String = FONT_FILES[key]
	var loaded: Font = null
	if ResourceLoader.exists(path):
		loaded = load(path) as Font
	if loaded == null:
		loaded = ThemeDB.fallback_font
	_fonts[key] = loaded
	stats.font_loads += 1
	return loaded


static func get_font(_size: int, style := "body") -> Font:
	# _render.get_font(size, style) compatibility; size is passed to draw_string.
	return font(style)


static func title_font(_size: int) -> Font:
	return font("title")


static func text(
	canvas: CanvasItem,
	pos: Vector2,
	value: String,
	font_size: int,
	color: Color,
	style := "body",
	align := HORIZONTAL_ALIGNMENT_LEFT,
	width := -1.0
) -> void:
	canvas.draw_string(font(style), pos, value, align, width, font_size, color)


static func centered(
	canvas: CanvasItem, pos: Vector2, value: String, font_size: int, color: Color, style := "body"
) -> void:
	var f := font(style)
	var extent := f.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
	canvas.draw_string(
		f,
		pos - Vector2(extent.x * 0.5, -extent.y * 0.25),
		value,
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		font_size,
		color
	)


static func circle_texture() -> Texture2D:
	return _radial_texture("circle", false)


static func glow_texture() -> Texture2D:
	return _radial_texture("glow", true)


static func _radial_texture(key: String, soft: bool) -> Texture2D:
	if _textures.has(key):
		stats.texture_hits += 1
		return _textures[key]
	var side := 64
	var image := Image.create(side, side, false, Image.FORMAT_RGBA8)
	var center := Vector2(side * 0.5, side * 0.5)
	var radius := side * 0.5 - 1.0
	for y in range(side):
		for x in range(side):
			var dist := center.distance_to(Vector2(x + 0.5, y + 0.5)) / radius
			var alpha := 0.0
			if dist <= 1.0:
				alpha = (1.0 - dist) if soft else clampf((1.0 - dist) * 8.0, 0.0, 1.0)
			image.set_pixel(x, y, Color(1, 1, 1, alpha))
	var texture := ImageTexture.create_from_image(image)
	_textures[key] = texture
	stats.texture_builds += 1
	return texture


static func draw_glow(canvas: CanvasItem, pos: Vector2, radius: float, color: Color) -> void:
	var texture := glow_texture()
	canvas.draw_texture_rect(
		texture, Rect2(pos - Vector2.ONE * radius, Vector2.ONE * radius * 2), false, color
	)


static func draw_circle_sprite(
	canvas: CanvasItem, pos: Vector2, radius: float, color: Color
) -> void:
	var texture := circle_texture()
	canvas.draw_texture_rect(
		texture, Rect2(pos - Vector2.ONE * radius, Vector2.ONE * radius * 2), false, color
	)


static func get_circle(_radius: int, color: Color) -> Texture2D:
	# _render.get_circle compatibility: tint is applied at draw time.
	_textures["tint_%s" % color.to_html()] = color
	return circle_texture()


static func get_glow(_radius: int, _color: Color) -> Texture2D:
	return glow_texture()


static func clear_cache() -> void:
	_fonts.clear()
	_textures.clear()
	stats = {"font_hits": 0, "font_loads": 0, "texture_hits": 0, "texture_builds": 0}
