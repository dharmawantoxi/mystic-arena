class_name UiThemeTextures
extends RefCounted

## Cached native textures for the pygame surface helpers. Rounded masking and
## smoothscale are native approximations; numeric formulas live in UiThemeSurfaces.
static var _cache: Dictionary = {}


static func clear_caches() -> void:
	_cache.clear()
	UiThemeSurfaces.clear_caches()


static func gradient(w: int, h: int, top: Array, bottom: Array, radius := 0) -> ImageTexture:
	w = maxi(2, w)
	h = maxi(2, h)
	var key := "g:%d:%d:%s:%s:%d" % [w, h, str(top), str(bottom), radius]
	if _cache.has(key):
		return _cache[key]
	var data := UiThemeSurfaces.gradient_data(w, h, top, bottom, radius)
	var image := Image.create(w, h, false, Image.FORMAT_RGBA8)
	for row: Array in data.rows:
		var color := Color(float(row[1]) / 255.0, float(row[2]) / 255.0, float(row[3]) / 255.0)
		for x in range(w):
			image.set_pixel(
				x, int(row[0]), Color(color, _rounded_alpha(x, int(row[0]), w, h, radius))
			)
	var texture := ImageTexture.create_from_image(image)
	_cache[key] = texture
	return texture


static func radial(w: int, h: int, color: Array, alpha: int) -> ImageTexture:
	var data := UiThemeSurfaces.radial_data(w, h, color, alpha)
	var key := "r:%s" % str(data.size) + ":%s:%d" % [str(color), alpha]
	if _cache.has(key):
		return _cache[key]
	var image := Image.create(int(data.size[0]), int(data.size[1]), false, Image.FORMAT_RGBA8)
	image.fill(Color.TRANSPARENT)
	for block: Dictionary in data.blocks:
		var c := UiTheme.rgb(block.color)
		var rect: Array = block.rect
		for y in range(int(rect[1]), int(rect[1]) + int(rect[3])):
			for x in range(int(rect[0]), int(rect[0]) + int(rect[2])):
				if x < image.get_width() and y < image.get_height():
					image.set_pixel(x, y, c)
	var texture := ImageTexture.create_from_image(image)
	_cache[key] = texture
	return texture


static func shadow(w: int, h: int, radius := 12, alpha := 110, spread := 4) -> ImageTexture:
	var data := UiThemeSurfaces.shadow_data(w, h, radius, alpha, spread)
	var key := "s:%d:%d:%d:%d:%d" % [w, h, radius, alpha, spread]
	if _cache.has(key):
		return _cache[key]
	var small: Dictionary = data.small_ops[0]
	var rect: Array = small.rect
	var sw := int(rect[2])
	var sh := int(rect[3])
	var image := Image.create(sw, sh, false, Image.FORMAT_RGBA8)
	var color := UiTheme.rgb(small.color)
	for y in range(sh):
		for x in range(sw):
			image.set_pixel(x, y, Color(color, _rounded_alpha(x, y, sw, sh, int(small.radius))))
	image.resize(int(data.size[0]), int(data.size[1]), Image.INTERPOLATE_BILINEAR)
	var texture := ImageTexture.create_from_image(image)
	_cache[key] = texture
	return texture


static func _rounded_alpha(x: int, y: int, w: int, h: int, radius: int) -> float:
	if radius <= 0:
		return 1.0
	var r := minf(float(radius), minf(w, h) / 2.0)
	var px := x + 0.5
	var py := y + 0.5
	var dx := maxf(absf(px - w / 2.0) - (w / 2.0 - r), 0.0)
	var dy := maxf(absf(py - h / 2.0) - (h / 2.0 - r), 0.0)
	return 1.0 if dx * dx + dy * dy <= r * r else 0.0
