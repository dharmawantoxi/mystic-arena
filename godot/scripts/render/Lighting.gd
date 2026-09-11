# Lighting.gd — port GDScript dari lighting.py (pygame) ke Godot 4.
#
# Kenapa modul ini ada (paritas lighting.py):
# Renderer prosedural di proyek ini membangun volume dengan BLOK NILAI yang
# di-author manual (skin_dark -> skin_mid -> skin_light). Itu bertahan di
# ukuran besar, tapi di 720p hasilnya masih terbaca sebagai "tumpukan pita
# datar" - bukan badan yang kena cahaya - karena tidak ada apa pun yang
# menghubungkan nilai-nilai itu dengan SATU arah cahaya yang konsisten, dan
# tidak ada terminator (garis gelap-terang) di sepanjang siluet.
#
# Modul ini menambahkan tahap yang murah dan universal: dari mask alpha
# sprite, turunkan
#   * rim light   : piksel terluar di sisi cahaya  -> RGB di-ADD sedikit
#   * terminator  : piksel terluar di sisi bayangan -> RGB di-MULT darker
#   * band kedua  : 1 px di dalamnya, 40% kekuatan  -> terasa seperti gradien
#
# Semua dihitung dari mask saja, jadi BEBAS dari bentuk karakter: berlaku
# untuk boss yang digambar langsung maupun hero masterwork lewat bake.
# Tidak ada aset eksternal — aturan "100% prosedural" tetap utuh.
#
# Di Godot, implementasi ada 2 jalur:
#   1) CPU Image (port 1:1 lighting.py) — untuk bake offline / tool
#      tools/convert_to_godot.py bisa pakai ini kalau mau re-bake dengan lighting.
#   2) GPU Shader (lighting.gdshader) — untuk runtime real-time, jauh lebih murah
#      (1 draw call vs loop per-piksel). Shader adalah jalur utama di arena.
#
# Paritas konstanta dengan lighting.py:
#   LIGHT_DIR = (-1, -1) kiri-atas
#   RIM_ADD = (30, 26, 44)
#   SHADE_MUL = 168
#   BAND2_RATIO = 0.42
#   MASK_ALPHA = 170
#   GRAD_DARK = 205, GRAD_LIGHT = 255, GRAD_SHEEN = 22, _GRAD_STEPS = 28
extends RefCounted
class_name MysticLighting

# --- Konstanta paritas lighting.py ---
const LIGHT_DIR: Vector2i = Vector2i(-1, -1)
const RIM_ADD: Color = Color(30.0 / 255.0, 26.0 / 255.0, 44.0 / 255.0, 1.0)
const RIM_ADD_INT: Vector3i = Vector3i(30, 26, 44)
const SHADE_MUL: int = 168
const BAND2_RATIO: float = 0.42
const MASK_ALPHA: int = 170
const GRADIENT_ENABLED: bool = true
const GRAD_DARK: int = 205
const GRAD_LIGHT: int = 255
const GRAD_SHEEN: int = 22
const GRAD_STEPS: int = 28

# Cache gradien kanonik 28x28 dan hasil upscale (w,h)
static var _canon_cache: Dictionary = {} # key -> {mul: Image, add: Image}
static var _size_cache: Dictionary = {}  # (w,h,dark,light,sheen) -> {mul: Image, add: Image}

# -------------------------------------------------------------
# Util internal: mask dari Image (alpha > threshold)
# -------------------------------------------------------------
static func _build_solid_mask(img: Image, alpha_threshold: int) -> Array:
	# Return Array[PackedByteArray] bool 2D atau flat bool
	var w := img.get_width()
	var h := img.get_height()
	var mask: Array = []
	mask.resize(h)
	var thresh_f := float(alpha_threshold) / 255.0
	for y in h:
		var row := PackedByteArray()
		row.resize(w)
		for x in w:
			var a := img.get_pixel(x, y).a
			row[x] = 1 if a * 255.0 >= float(alpha_threshold) or a >= thresh_f else 0
		mask[y] = row
	return mask

static func _count_mask(mask: Array) -> int:
	var c := 0
	for row in mask:
		for v in row:
			if v:
				c += 1
	return c

static func _shifted_mask(mask: Array, dx: int, dy: int, w: int, h: int) -> Array:
	var out: Array = []
	out.resize(h)
	for y in h:
		var row := PackedByteArray()
		row.resize(w)
		row.fill(0)
		out[y] = row
	for y in h:
		var sy := y - dy
		if sy < 0 or sy >= h:
			continue
		var src_row: PackedByteArray = mask[sy]
		var dst_row: PackedByteArray = out[y]
		for x in w:
			var sx := x - dx
			if sx < 0 or sx >= w:
				continue
			if src_row[sx]:
				dst_row[x] = 1
	return out

static func _mask_erase(a: Array, b: Array, w: int, h: int) -> void:
	# a = a - b (inplace): hapus piksel yang ada di b
	for y in h:
		var ra: PackedByteArray = a[y]
		var rb: PackedByteArray = b[y]
		for x in w:
			if rb[x] and ra[x]:
				ra[x] = 0

static func _mask_copy(mask: Array, h: int) -> Array:
	var out: Array = []
	out.resize(h)
	for y in h:
		var src: PackedByteArray = mask[y]
		var dst := PackedByteArray()
		dst.resize(src.size())
		for x in src.size():
			dst[x] = src[x]
		out[y] = dst
	return out

# -------------------------------------------------------------
# Gradient kanonik 28x28 (paritas _canonical)
# -------------------------------------------------------------
static func _canonical_key(dark: int, light: int, sheen: int) -> String:
	return "%d_%d_%d_%d_%d" % [dark, light, sheen, LIGHT_DIR.x, LIGHT_DIR.y]

static func _canonical(dark: int = GRAD_DARK, light: int = GRAD_LIGHT, sheen: int = GRAD_SHEEN) -> Dictionary:
	var key := _canonical_key(dark, light, sheen)
	if _canon_cache.has(key):
		return _canon_cache[key]
	var n := GRAD_STEPS
	var mul_img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var add_img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var ax := absi(LIGHT_DIR.x)
	var ay := absi(LIGHT_DIR.y)
	var span := float((n - 1) * (ax + ay))
	if span < 1.0:
		span = 1.0
	for gy in n:
		for gx in n:
			var t := 1.0 - (float(gx * ax + gy * ay) / span)
			t = clampf(t, 0.0, 1.0)
			var v := int(round(float(dark) + float(light - dark) * t))
			v = clampi(v, 0, 255)
			mul_img.set_pixel(gx, gy, Color(float(v) / 255.0, float(v) / 255.0, float(v) / 255.0, 1.0))
			var k := int(round(float(sheen) * pow(t, 2.2)))
			k = clampi(k, 0, 255)
			# add: (k,k,k*1.25) seperti lighting.py
			var kb := int(round(float(k) * 1.25))
			kb = clampi(kb, 0, 255)
			add_img.set_pixel(gx, gy, Color(float(k) / 255.0, float(k) / 255.0, float(kb) / 255.0, 1.0))
	var dict := {"mul": mul_img, "add": add_img}
	_canon_cache[key] = dict
	return dict

static func _sized(w: int, h: int, dark: int = GRAD_DARK, light: int = GRAD_LIGHT, sheen: int = GRAD_SHEEN) -> Dictionary:
	var key := "%d_%d_%d_%d_%d" % [w, h, dark, light, sheen]
	if _size_cache.has(key):
		return _size_cache[key]
	if _size_cache.size() > 64:
		_size_cache.clear()
	var canon := _canonical(dark, light, sheen)
	var mul: Image = canon["mul"]
	var add: Image = canon["add"]
	var mul_sized := mul.duplicate()
	var add_sized := add.duplicate()
	mul_sized.resize(w, h, Image.INTERPOLATE_BILINEAR)
	add_sized.resize(w, h, Image.INTERPOLATE_BILINEAR)
	var out := {"mul": mul_sized, "add": add_sized}
	_size_cache[key] = out
	return out

static func reset_gradient_cache() -> void:
	_size_cache.clear()
	_canon_cache.clear()

# -------------------------------------------------------------
# contour_masks — paritas lighting.py contour_masks()
# rim = mask - shift(mask, +sx,+sy) -> sisi menghadap cahaya
# shade = mask - shift(mask, -sx,-sy) -> sisi membelakangi cahaya
# -------------------------------------------------------------
static func contour_masks(img: Image, alpha: int = MASK_ALPHA, width: int = 1) -> Dictionary:
	var w := img.get_width()
	var h := img.get_height()
	if w <= 2 or h <= 2:
		return {"rim": [], "shade": [], "valid": false}
	var solid := _build_solid_mask(img, alpha)
	if _count_mask(solid) < 24:
		return {"rim": [], "shade": [], "valid": false}
	var sx := absi(LIGHT_DIR.x) * width
	var sy := absi(LIGHT_DIR.y) * width
	# rim: solid - shifted(solid, +sx,+sy)
	var shifted_pos := _shifted_mask(solid, sx, sy, w, h)
	var rim := _mask_copy(solid, h)
	_mask_erase(rim, shifted_pos, w, h)
	# shade: solid - shifted(solid, -sx,-sy)
	var shifted_neg := _shifted_mask(solid, -sx, -sy, w, h)
	var shade := _mask_copy(solid, h)
	_mask_erase(shade, shifted_neg, w, h)
	return {"rim": rim, "shade": shade, "solid": solid, "valid": true, "w": w, "h": h}

# -------------------------------------------------------------
# _bbox_of — paritas lighting.py _bbox_of()
# -------------------------------------------------------------
static func bbox_of(img: Image, alpha: int = MASK_ALPHA) -> Rect2i:
	var w := img.get_width()
	var h := img.get_height()
	var solid := _build_solid_mask(img, alpha)
	var x0 := w
	var y0 := h
	var x1 := -1
	var y1 := -1
	for y in h:
		var row: PackedByteArray = solid[y]
		for x in w:
			if row[x]:
				if x < x0: x0 = x
				if y < y0: y0 = y
				if x > x1: x1 = x
				if y > y1: y1 = y
	if x1 < 0:
		return Rect2i(0, 0, 0, 0)
	return Rect2i(x0, y0, max(1, x1 - x0 + 1), max(1, y1 - y0 + 1))

# -------------------------------------------------------------
# apply — port utama lighting.py apply()
# Beri cahaya IN-PLACE pada Image: gradien arah + rim + terminator
# Hanya RGB disentuh, alpha tetap.
# -------------------------------------------------------------
static func apply(img: Image, rim_add: Color = RIM_ADD, shade_mul: int = SHADE_MUL,
		two_band: bool = true, alpha: int = MASK_ALPHA,
		gradient: bool = GRADIENT_ENABLED, box: Rect2i = Rect2i(-1, -1, -1, -1)) -> Image:
	var w := img.get_width()
	var h := img.get_height()
	if w <= 2 or h <= 2:
		return img
	var cm := contour_masks(img, alpha, 1)
	if not cm["valid"]:
		return img
	var rim: Array = cm["rim"]
	var shade: Array = cm["shade"]
	# ---- gradient ----
	if gradient:
		var bx: int
		var by: int
		var bw: int
		var bh: int
		if box.size.x < 0:
			bx = 0; by = 0; bw = w; bh = h
		else:
			bx = box.position.x; by = box.position.y
			bw = box.size.x; bh = box.size.y
			bw = max(2, min(bw, w - bx))
			bh = max(2, min(bh, h - by))
		if bw > 2 and bh > 2:
			var grad := _sized(bw, bh)
			var mul_img: Image = grad["mul"]
			var add_img: Image = grad["add"]
			# BLEND_RGB_MULT + ADD per piksel di box
			for yy in bh:
				for xx in bw:
					var gx := bx + xx
					var gy := by + yy
					if gx < 0 or gx >= w or gy < 0 or gy >= h:
						continue
					var src := img.get_pixel(gx, gy)
					if src.a <= 0.001:
						continue
					var m := mul_img.get_pixel(xx, yy)
					var a := add_img.get_pixel(xx, yy)
					# mult
					src.r *= m.r
					src.g *= m.g
					src.b *= m.b
					# add
					src.r = min(1.0, src.r + a.r)
					src.g = min(1.0, src.g + a.g)
					src.b = min(1.0, src.b + a.b)
					img.set_pixel(gx, gy, src)
	# ---- terminator (sisi bayangan): band1 gelap, band2 lebih lemah ----
	var wide: Array = []
	var has_wide := false
	if two_band:
		var outer := contour_masks(img, alpha, 2)
		if outer["valid"]:
			var inner_shade: Array = outer["shade"] # width=2 shade = outer band
			# deep = shade (width=1), wide = inner - deep
			# inner_shade contains 2px border, shade is 1px border
			# wide = inner_shade - shade
			wide = _mask_copy(inner_shade, h)
			_mask_erase(wide, shade, w, h)
			has_wide = true
	var neutral := clampi(int(shade_mul), 0, 255)
	var neutral_f := float(neutral) / 255.0
	var k2 := clampi(int(255.0 - (255.0 - float(neutral)) * BAND2_RATIO), 0, 255)
	var k2_f := float(k2) / 255.0
	# MULT pass
	for y in h:
		var shade_row: PackedByteArray = shade[y]
		var wide_row: PackedByteArray = wide[y] if has_wide else PackedByteArray()
		for x in w:
			if not shade_row[x] and (not has_wide or not wide_row[x]):
				continue
			var src := img.get_pixel(x, y)
			if src.a <= 0.001:
				continue
			if shade_row[x]:
				src.r *= neutral_f
				src.g *= neutral_f
				src.b *= neutral_f
			elif has_wide and wide_row[x]:
				src.r *= k2_f
				src.g *= k2_f
				src.b *= k2_f
			img.set_pixel(x, y, src)
	# ---- rim light (sisi cahaya) ----
	var rim_r := rim_add.r
	var rim_g := rim_add.g
	var rim_b := rim_add.b
	for y in h:
		var rim_row: PackedByteArray = rim[y]
		for x in w:
			if not rim_row[x]:
				continue
			var src := img.get_pixel(x, y)
			if src.a <= 0.001:
				continue
			src.r = min(1.0, src.r + rim_r)
			src.g = min(1.0, src.g + rim_g)
			src.b = min(1.0, src.b + rim_b)
			img.set_pixel(x, y, src)
	return img

static func apply_to_rig(img: Image, enabled: bool = true, rim_add: Color = RIM_ADD,
		shade_mul: int = SHADE_MUL, two_band: bool = true, alpha: int = MASK_ALPHA,
		gradient: bool = GRADIENT_ENABLED, box: Rect2i = Rect2i(-1, -1, -1, -1)) -> Image:
	if not enabled:
		return img
	# Aman: jangan pernah crash renderer — telan error dan kembalikan apa adanya
	# (paritas lighting.py apply_to_rig)
	var copy := img.duplicate()
	var ok := true
	# GDScript tidak punya try/catch untuk Image, tapi kita jaga bounds
	# Kalau ada error, kembalikan copy
	# Di Godot 4.4+ ada push_error, tapi kita tetap kembalikan img asli
	var res: Image = apply(copy, rim_add, shade_mul, two_band, alpha, gradient, box)
	if res == null:
		return img
	return res

# -------------------------------------------------------------
# Helper untuk Texture2D -> Image -> apply -> ImageTexture
# -------------------------------------------------------------
static func apply_to_texture(tex: Texture2D, enabled: bool = true, box: Rect2i = Rect2i(-1, -1, -1, -1)) -> ImageTexture:
	if tex == null:
		return null
	var img := tex.get_image()
	if img == null:
		return null
	# Pastikan RGBA8
	if img.get_format() != Image.FORMAT_RGBA8:
		img.convert(Image.FORMAT_RGBA8)
	apply_to_rig(img, enabled, RIM_ADD, SHADE_MUL, true, MASK_ALPHA, GRADIENT_ENABLED, box)
	return ImageTexture.create_from_image(img)

# -------------------------------------------------------------
# API untuk shader: berikan parameter seragam
# -------------------------------------------------------------
static func shader_params() -> Dictionary:
	return {
		"light_dir": Vector2(float(LIGHT_DIR.x), float(LIGHT_DIR.y)),
		"rim_add": RIM_ADD,
		"shade_mul": float(SHADE_MUL) / 255.0,
		"band2_ratio": BAND2_RATIO,
		"grad_dark": float(GRAD_DARK) / 255.0,
		"grad_light": float(GRAD_LIGHT) / 255.0,
		"grad_sheen": float(GRAD_SHEEN) / 255.0,
		"mask_alpha": float(MASK_ALPHA) / 255.0,
	}

# -------------------------------------------------------------
# Utility: buat material shader lighting siap pakai
# -------------------------------------------------------------
static func create_lighting_material() -> ShaderMaterial:
	var shader := load("res://assets/shaders/lighting.gdshader") as Shader
	if shader == null:
		push_warning("[MysticLighting] lighting.gdshader tidak ditemukan, fallback ke outline")
		shader = load("res://assets/shaders/outline.gdshader") as Shader
	var mat := ShaderMaterial.new()
	mat.shader = shader
	var p := shader_params()
	mat.set_shader_parameter("light_dir", p["light_dir"])
	# rim_add sekarang vec4 di shader (source_color), jadi set sebagai Color/Vector4
	var rim_col: Color = p["rim_add"]
	mat.set_shader_parameter("rim_add", rim_col)
	mat.set_shader_parameter("shade_mul", p["shade_mul"])
	mat.set_shader_parameter("band2_ratio", p["band2_ratio"])
	mat.set_shader_parameter("grad_dark", p["grad_dark"])
	mat.set_shader_parameter("grad_light", p["grad_light"])
	mat.set_shader_parameter("grad_sheen", p["grad_sheen"])
	mat.set_shader_parameter("mask_alpha", p["mask_alpha"])
	return mat
