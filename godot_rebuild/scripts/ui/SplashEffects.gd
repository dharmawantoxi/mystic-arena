class_name SplashEffects
extends RefCounted

## Cached textures for the splash. Background/logo glow are rebuilt only when
## size/radius changes; logo frames are cached by quantized size.
const MAX_BACKGROUNDS := 4
const MAX_GLOWS := 16
const MAX_LOGO_FRAMES := 32
static var backgrounds: Dictionary = {}
static var logo_glows: Dictionary = {}
static var logo_frames: Dictionary = {}


static func clear_cache() -> void:
	backgrounds.clear()
	logo_glows.clear()
	logo_frames.clear()


static func background(model: SplashModel, size: Vector2i) -> Texture2D:
	if not model.valid() or size.x <= 0 or size.y <= 0:
		return null
	var key := "%s:%d:%d" % [model.source_sha, size.x, size.y]
	if backgrounds.has(key):
		return backgrounds[key]
	var image := Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
	var step := maxi(1, size.y / model.i("band_target"))
	var split := model.f("grad_split")
	var top: Array = model.config.grad_top
	var mid: Array = model.config.grad_mid
	var bottom: Array = model.config.grad_bot
	for y in range(0, size.y, step):
		var f := float(y) / float(size.y)
		var row := Color(0, 0, 0, 1)
		if f < split:
			var ratio := f / split
			row = Color8(
				int(top[0] + (mid[0] - top[0]) * ratio),
				int(top[1] + (mid[1] - top[1]) * ratio),
				int(top[2] + (mid[2] - top[2]) * ratio),
				255
			)
		else:
			var ratio := (f - split) / (1.0 - split)
			row = Color8(
				int(mid[0] + (bottom[0] - mid[0]) * ratio),
				int(mid[1] + (bottom[1] - mid[1]) * ratio),
				int(mid[2] + (bottom[2] - mid[2]) * ratio),
				255
			)
		image.fill_rect(Rect2i(0, y, size.x, mini(step, size.y - y)), row)
	_vignette(image, model)
	var texture := ImageTexture.create_from_image(image)
	if backgrounds.size() >= MAX_BACKGROUNDS:
		backgrounds.clear()
	backgrounds[key] = texture
	return texture


static func _vignette(image: Image, model: SplashModel) -> void:
	var start := model.i("vig_start")
	var step := absi(model.i("vig_step"))
	var slope := model.f("vig_slope")
	var inset := start % step
	if inset == 0:
		inset = step
	var final_alpha := mini(255, int(slope * (start - inset)))
	var size := image.get_size()
	if final_alpha >= 255 and size.x > 2 * inset and size.y > 2 * inset:
		image.fill_rect(Rect2i(inset, inset, size.x - 2 * inset, size.y - 2 * inset), Color.BLACK)
		return
	for value in range(start, 0, -step):
		var alpha := mini(255, int(slope * (start - value))) / 255.0
		var pos := value
		var rect := Rect2i(pos, pos, size.x - 2 * pos, size.y - 2 * pos)
		if rect.size.x <= 0 or rect.size.y <= 0:
			continue
		for y in range(rect.position.y, rect.end.y):
			for x in range(rect.position.x, rect.end.x):
				var old := image.get_pixel(x, y)
				image.set_pixel(x, y, old.lerp(Color.BLACK, alpha))


static func logo_glow(model: SplashModel, radius: int) -> Texture2D:
	if not model.valid() or radius <= 0:
		return null
	var key := "%s:%d" % [model.source_sha, radius]
	if logo_glows.has(key):
		return logo_glows[key]
	var image := Image.create(radius * 2, radius * 2, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	var step := absi(model.i("glow_step"))
	var peak := model.f("glow_alpha")
	var accent: Array = model.config.accent
	var col := Color8(int(accent[0]), int(accent[1]), int(accent[2]), 0)
	var profile := PackedInt32Array()
	profile.resize(radius)
	for distance in range(radius):
		var ring := radius
		while ring - step > 0 and ring - step > distance:
			ring -= step
		profile[distance] = int(peak * (1.0 - float(ring) / float(radius)))
	for y in range(radius * 2):
		for x in range(radius * 2):
			var distance := ceili(
				sqrt(float((x - radius) * (x - radius) + (y - radius) * (y - radius)))
			)
			if distance >= radius:
				continue
			col.a8 = profile[distance]
			image.set_pixel(x, y, col)
	var texture := ImageTexture.create_from_image(image)
	if logo_glows.size() >= MAX_GLOWS:
		logo_glows.clear()
	logo_glows[key] = texture
	return texture


static func logo_frame(source: Image, target: Vector2i) -> Texture2D:
	if source == null or target.x <= 0 or target.y <= 0:
		return null
	var key := "%d:%d:%d" % [source.get_instance_id(), target.x, target.y]
	if logo_frames.has(key):
		return logo_frames[key]
	var frame := source.duplicate() as Image
	frame.resize(target.x, target.y, Image.INTERPOLATE_LANCZOS)
	var texture := ImageTexture.create_from_image(frame)
	if logo_frames.size() >= MAX_LOGO_FRAMES:
		logo_frames.clear()
	logo_frames[key] = texture
	return texture
