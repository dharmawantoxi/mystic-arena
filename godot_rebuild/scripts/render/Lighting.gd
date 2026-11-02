class_name Lighting
extends RefCounted

## Native port of lighting.py. Mutates RGBA RGB channels only; alpha, size and
## anchors are preserved. Python/pygame remains the preparation-time oracle.
const DEFAULT_PATH := "res://data/lighting.json"
const REQUIRED_FIELDS := [
	"light_dir",
	"rim_add",
	"shade_mul",
	"band2_ratio",
	"mask_alpha",
	"gradient_enabled",
	"grad_dark",
	"grad_light",
	"grad_sheen",
	"grad_steps",
	"size_cache_limit",
	"canonical_mul_rgb",
	"canonical_add_rgb"
]

var load_error := ""
var light_dir := Vector2i(-1, -1)
var rim_add := Vector3i(30, 26, 44)
var shade_mul := 168
var band2_ratio := 0.42
var mask_alpha := 170
var gradient_enabled := true
var grad_dark := 205
var grad_light := 255
var grad_sheen := 22
var grad_steps := 28
var size_cache_limit := 65
var _canonical_cache: Dictionary = {}
var _size_cache: Dictionary = {}
var _contract: Dictionary = {}


func _init(path := DEFAULT_PATH) -> void:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		load_error = "Cannot open %s" % path
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary or int(parsed.get("schema", 0)) != 1:
		load_error = "Invalid lighting JSON: %s" % path
		return
	for field: String in REQUIRED_FIELDS:
		if not parsed.has(field):
			load_error = "Missing lighting field: %s" % field
			return
	_contract = parsed
	light_dir = Vector2i(int(parsed.light_dir[0]), int(parsed.light_dir[1]))
	rim_add = Vector3i(int(parsed.rim_add[0]), int(parsed.rim_add[1]), int(parsed.rim_add[2]))
	shade_mul = int(parsed.shade_mul)
	band2_ratio = float(parsed.band2_ratio)
	mask_alpha = int(parsed.mask_alpha)
	gradient_enabled = bool(parsed.gradient_enabled)
	grad_dark = int(parsed.grad_dark)
	grad_light = int(parsed.grad_light)
	grad_sheen = int(parsed.grad_sheen)
	grad_steps = int(parsed.grad_steps)
	size_cache_limit = int(parsed.size_cache_limit)
	var expected := grad_steps * grad_steps * 3
	if grad_steps < 2 or size_cache_limit < 1:
		load_error = "Invalid lighting cache/grid configuration"
	elif parsed.canonical_mul_rgb.size() != expected or parsed.canonical_add_rgb.size() != expected:
		load_error = "Invalid canonical lighting grid payload"
	for value: int in [shade_mul, mask_alpha, grad_dark, grad_light, grad_sheen]:
		if value < 0 or value > 255:
			load_error = "Lighting byte constant out of range"
	if band2_ratio < 0.0 or band2_ratio > 1.0:
		load_error = "Lighting band ratio out of range"


func valid() -> bool:
	return load_error.is_empty() and not _contract.is_empty()


func reset_gradient_cache() -> void:
	_size_cache.clear()


func clear_cache() -> void:
	_canonical_cache.clear()
	_size_cache.clear()


func size_cache_size() -> int:
	return _size_cache.size()


func canonical(config: Dictionary = {}) -> Dictionary:
	var dark := int(config.get("dark", grad_dark))
	var light := int(config.get("light", grad_light))
	var sheen := int(config.get("sheen", grad_sheen))
	var key := "%d:%d:%d:%d:%d" % [dark, light, sheen, light_dir.x, light_dir.y]
	if _canonical_cache.has(key):
		return _canonical_cache[key]
	var mul := PackedByteArray()
	var add := PackedByteArray()
	if dark == grad_dark and light == grad_light and sheen == grad_sheen and valid():
		for value: Variant in _contract.canonical_mul_rgb:
			mul.append(int(value))
		for value: Variant in _contract.canonical_add_rgb:
			add.append(int(value))
	else:
		var axes := Vector2(absi(light_dir.x), absi(light_dir.y))
		var span := maxf(1.0, float(grad_steps - 1) * (axes.x + axes.y))
		for gy in range(grad_steps):
			for gx in range(grad_steps):
				var t := clampf(1.0 - (gx * axes.x + gy * axes.y) / span, 0.0, 1.0)
				var value := clampi(_py_round(dark + (light - dark) * t), 0, 255)
				var glow := clampi(_py_round(sheen * pow(t, 2.2)), 0, 255)
				mul.append_array(PackedByteArray([value, value, value]))
				add.append_array(PackedByteArray([glow, glow, clampi(int(glow * 1.25), 0, 255)]))
	var result := {"mul": mul, "add": add}
	_canonical_cache[key] = result
	return result


func gradient(size: Vector2i, config: Dictionary = {}) -> Dictionary:
	if not valid() or size.x <= 0 or size.y <= 0:
		return {}
	var dark := int(config.get("dark", grad_dark))
	var light := int(config.get("light", grad_light))
	var sheen := int(config.get("sheen", grad_sheen))
	var key := "%d:%d:%d:%d:%d" % [size.x, size.y, dark, light, sheen]
	if _size_cache.has(key):
		return _size_cache[key]
	if _size_cache.size() >= size_cache_limit:
		_size_cache.clear()
	var base := canonical({"dark": dark, "light": light, "sheen": sheen})
	var grid := Vector2i(grad_steps, grad_steps)
	var result := {
		"size": size,
		"mul": LightingResampler.resize(base.mul, grid.x, grid.y, size),
		"add": LightingResampler.resize(base.add, grid.x, grid.y, size),
	}
	_size_cache[key] = result
	return result


func contour_masks(image: Image, alpha := -1, width := 1) -> Dictionary:
	if image == null or image.get_width() <= 2 or image.get_height() <= 2:
		return {}
	var threshold := mask_alpha if alpha < 0 else alpha
	var solid := _solid_bits(image, threshold)
	if int(solid.count) < 24:
		return {}
	var w := image.get_width()
	var h := image.get_height()
	var bits: PackedByteArray = solid.bits
	var sx := absi(light_dir.x) * width
	var sy := absi(light_dir.y) * width
	var rim := PackedByteArray()
	var shade := PackedByteArray()
	rim.resize(w * h)
	shade.resize(w * h)
	var rim_count := 0
	var shade_count := 0
	for y in range(h):
		for x in range(w):
			var index := y * w + x
			if bits[index] == 0:
				continue
			var lit_neighbor := _bit(bits, w, h, x - sx, y - sy)
			var dark_neighbor := _bit(bits, w, h, x + sx, y + sy)
			if lit_neighbor == 0:
				rim[index] = 1
				rim_count += 1
			if dark_neighbor == 0:
				shade[index] = 1
				shade_count += 1
	return {"rim": rim, "shade": shade, "rim_count": rim_count, "shade_count": shade_count}


func bbox_of(image: Image, alpha := -1) -> Rect2i:
	if image == null:
		return Rect2i()
	var threshold := mask_alpha if alpha < 0 else alpha
	var w := image.get_width()
	var h := image.get_height()
	var data := image.get_data()
	var min_x := w
	var min_y := h
	var max_x := -1
	var max_y := -1
	for y in range(h):
		for x in range(w):
			if data[(y * w + x) * 4 + 3] <= threshold:
				continue
			min_x = mini(min_x, x)
			min_y = mini(min_y, y)
			max_x = maxi(max_x, x)
			max_y = maxi(max_y, y)
	if max_x < 0:
		return Rect2i()
	return Rect2i(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)


func apply_to_rig(image: Image, enabled := true, options: Dictionary = {}) -> Image:
	if not enabled:
		return image
	return apply(image, options)


func apply(image: Image, options: Dictionary = {}) -> Image:
	if not valid() or image == null or image.get_width() <= 2 or image.get_height() <= 2:
		return image
	if image.is_compressed():
		image.decompress()
	if image.get_format() != Image.FORMAT_RGBA8:
		image.convert(Image.FORMAT_RGBA8)
	var alpha := int(options.get("alpha", mask_alpha))
	var masks := contour_masks(image, alpha)
	if masks.is_empty():
		return image
	var w := image.get_width()
	var h := image.get_height()
	var box := Rect2i(0, 0, w, h)
	if options.has("box"):
		if not options.box is Rect2i:
			return image
		box = options.box
		if box.position.x < 0 or box.position.y < 0 or box.position.x >= w or box.position.y >= h:
			return image
	box.size.x = maxi(2, mini(box.size.x, w - box.position.x))
	box.size.y = maxi(2, mini(box.size.y, h - box.position.y))
	var data := image.get_data()
	if bool(options.get("gradient", gradient_enabled)) and box.size.x > 2 and box.size.y > 2:
		_apply_gradient(data, w, box)
	var neutral := clampi(int(options.get("shade_mul", shade_mul)), 0, 255)
	var inner_k := clampi(int(255 - (255 - neutral) * band2_ratio), 0, 255)
	var shade: PackedByteArray = masks.shade
	var wide := PackedByteArray()
	wide.resize(w * h)
	var two_band_active := false
	if bool(options.get("two_band", true)):
		var inner := contour_masks(image, alpha, 2)
		if not inner.is_empty():
			two_band_active = true
			for index in range(w * h):
				wide[index] = 1 if inner.shade[index] == 1 and shade[index] == 0 else 0
	var addition := _rgb_option(options.get("rim_add", rim_add), rim_add)
	# pygame raises on out-of-range rim colors; apply_to_rig swallows the error
	# AFTER gradient/terminator already mutated the surface. Match that partial
	# result by skipping only the rim ADD stage for invalid colors.
	var rim_ok := (
		addition.x >= 0
		and addition.x <= 255
		and addition.y >= 0
		and addition.y <= 255
		and addition.z >= 0
		and addition.z <= 255
	)
	var rim: PackedByteArray = masks.rim
	for index in range(w * h):
		# pygame blits the band-2 mask with an OPAQUE white unsetcolor, so when
		# two_band is active it overwrites the deep-shade multiplier everywhere
		# except the band-2 ring. Reproduce that quirk exactly.
		var factor := 255
		if two_band_active:
			if wide[index] == 1:
				factor = inner_k
		elif shade[index] == 1:
			factor = neutral
		var offset := index * 4
		data[offset] = _mul_byte(data[offset], factor)
		data[offset + 1] = _mul_byte(data[offset + 1], factor)
		data[offset + 2] = _mul_byte(data[offset + 2], factor)
		if rim_ok and rim[index] == 1:
			data[offset] = mini(255, data[offset] + addition.x)
			data[offset + 1] = mini(255, data[offset + 1] + addition.y)
			data[offset + 2] = mini(255, data[offset + 2] + addition.z)
	image.set_data(w, h, false, Image.FORMAT_RGBA8, data)
	return image


func _apply_gradient(data: PackedByteArray, stride: int, box: Rect2i) -> void:
	var maps := gradient(box.size)
	if maps.is_empty():
		return
	var mul: PackedByteArray = maps.mul
	var add: PackedByteArray = maps.add
	for y in range(box.size.y):
		for x in range(box.size.x):
			var dst := ((box.position.y + y) * stride + box.position.x + x) * 4
			var src := (y * box.size.x + x) * 3
			for channel in range(3):
				var value := _mul_byte(data[dst + channel], mul[src + channel])
				data[dst + channel] = mini(255, value + add[src + channel])


func _solid_bits(image: Image, threshold: int) -> Dictionary:
	var data := image.get_data()
	var bits := PackedByteArray()
	bits.resize(image.get_width() * image.get_height())
	var count := 0
	for index in range(bits.size()):
		if data[index * 4 + 3] > threshold:
			bits[index] = 1
			count += 1
	return {"bits": bits, "count": count}


static func _bit(bits: PackedByteArray, width: int, height: int, x: int, y: int) -> int:
	if x < 0 or y < 0 or x >= width or y >= height:
		return 0
	return bits[y * width + x]


static func _mul_byte(value: int, factor: int) -> int:
	# pygame BLEND_RGB_MULT uses (dst * src + 255) >> 8 (ceil product/256).
	return (value * factor + 255) >> 8


static func _rgb_option(value: Variant, fallback: Vector3i) -> Vector3i:
	if value is Vector3i:
		return value
	if value is Array and value.size() == 3:
		return Vector3i(int(value[0]), int(value[1]), int(value[2]))
	return fallback


static func _py_round(value: float) -> int:
	var lower := floorf(value)
	var fraction := value - lower
	if is_equal_approx(fraction, 0.5):
		return int(lower) if int(lower) % 2 == 0 else int(lower) + 1
	return int(floorf(value + 0.5))
