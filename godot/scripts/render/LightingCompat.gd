# LightingCompat.gd — wrapper kompatibel GDExtension (godot++) + GDScript fallback
# Tujuan: kode game tidak perlu tahu apakah lib C++ sudah dibuild atau belum.
# - Jika ProjectSettings mystic/rendering/use_gdext_lighting = true DAN class MysticLighting ada (GDExtension loaded),
#   pakai C++ (5-10x lebih cepat, <0.5ms per sprite 90x90)
# - Jika tidak, fallback ke Lighting.gd murni GDScript (port 1:1 lighting.py)
# - Untuk runtime real-time, jalur utama tetap shader GPU (lighting.gdshader), bukan CPU Image
#
# Penggunaan:
#   var compat = LightingCompat.new()
#   var tex = compat.apply_to_texture(my_texture)
# Atau static:
#   LightingCompat.apply_image(img)
#   LightingCompat.create_material()

extends RefCounted

const LightingGD = preload("res://scripts/render/Lighting.gd")

static var _has_gdext: bool = false
static var _checked: bool = false

static func _ensure_check() -> void:
	if _checked:
		return
	_checked = true
	_has_gdext = false
	# Cek apakah GDExtension class terdaftar
	if ClassDB.class_exists("MysticLighting"):
		var use_gdext: bool = bool(ProjectSettings.get_setting("mystic/rendering/use_gdext_lighting", false))
		if use_gdext:
			_has_gdext = true
			print("[LightingCompat] GDExtension MysticLighting aktif (godot++ C++)")
		else:
			print("[LightingCompat] GDExtension tersedia tapi use_gdext_lighting=false, pakai GDScript fallback")
	else:
		print("[LightingCompat] GDExtension tidak ditemukan, pakai GDScript fallback (Lighting.gd) + shader GPU")

static func has_gdext() -> bool:
	_ensure_check()
	return _has_gdext

# --- Image API (CPU, untuk bake offline) ---
static func apply_image(img: Image, rim_add: Color = LightingGD.RIM_ADD, shade_mul: int = LightingGD.SHADE_MUL,
		two_band: bool = true, alpha: int = LightingGD.MASK_ALPHA, gradient: bool = LightingGD.GRADIENT_ENABLED,
		box: Rect2i = Rect2i(-1,-1,-1,-1)) -> Image:
	_ensure_check()
	if _has_gdext:
		# Panggil C++ via ClassDB
		# MysticLighting.apply adalah static, tapi di GDScript kita instantiate dulu atau call static
		# Di GDExtension, method static tetap bisa dipanggil lewat instance
		var ml = ClassDB.instantiate("MysticLighting")
		if ml != null and ml.has_method("apply"):
			# apply mengembalikan Image (in-place tapi juga return)
			return ml.call("apply", img, rim_add, shade_mul, two_band, alpha, gradient, box)
	# Fallback GDScript
	return LightingGD.apply(img, rim_add, shade_mul, two_band, alpha, gradient, box)

static func apply_to_rig_image(img: Image, enabled: bool = true, box: Rect2i = Rect2i(-1,-1,-1,-1)) -> Image:
	_ensure_check()
	if _has_gdext:
		var ml = ClassDB.instantiate("MysticLighting")
		if ml != null and ml.has_method("apply_to_rig"):
			return ml.call("apply_to_rig", img, enabled, LightingGD.RIM_ADD, LightingGD.SHADE_MUL, true, LightingGD.MASK_ALPHA, LightingGD.GRADIENT_ENABLED, box)
	return LightingGD.apply_to_rig(img, enabled, LightingGD.RIM_ADD, LightingGD.SHADE_MUL, true, LightingGD.MASK_ALPHA, LightingGD.GRADIENT_ENABLED, box)

static func apply_to_texture(tex: Texture2D, enabled: bool = true, box: Rect2i = Rect2i(-1,-1,-1,-1)) -> ImageTexture:
	_ensure_check()
	if _has_gdext:
		var ml = ClassDB.instantiate("MysticLighting")
		if ml != null and ml.has_method("apply_to_texture"):
			return ml.call("apply_to_texture", tex, enabled, box)
	return LightingGD.apply_to_texture(tex, enabled, box)

static func contour_masks(img: Image, alpha: int = LightingGD.MASK_ALPHA, width: int = 1) -> Dictionary:
	_ensure_check()
	if _has_gdext:
		var ml = ClassDB.instantiate("MysticLighting")
		if ml != null and ml.has_method("contour_masks"):
			return ml.call("contour_masks", img, alpha, width)
	return LightingGD.contour_masks(img, alpha, width)

static func bbox_of(img: Image, alpha: int = LightingGD.MASK_ALPHA) -> Rect2i:
	_ensure_check()
	if _has_gdext:
		var ml = ClassDB.instantiate("MysticLighting")
		if ml != null and ml.has_method("bbox_of"):
			return ml.call("bbox_of", img, alpha)
	return LightingGD.bbox_of(img, alpha)

static func reset_cache() -> void:
	_ensure_check()
	if _has_gdext:
		var ml = ClassDB.instantiate("MysticLighting")
		if ml != null and ml.has_method("reset_gradient_cache"):
			ml.call("reset_gradient_cache")
			return
	LightingGD.reset_gradient_cache()

# --- Shader API (GPU, untuk runtime) ---
static func shader_params() -> Dictionary:
	# Sama untuk kedua jalur
	return LightingGD.shader_params()

static func create_lighting_material() -> ShaderMaterial:
	_ensure_check()
	if _has_gdext:
		var ml = ClassDB.instantiate("MysticLighting")
		if ml != null and ml.has_method("create_lighting_material"):
			return ml.call("create_lighting_material")
	return LightingGD.create_lighting_material()

static func create_outline_material() -> ShaderMaterial:
	# Untuk kasus yang butuh outline + lighting digabung
	var shader_path: String = str(ProjectSettings.get_setting("mystic/rendering/lighting_shader_path", "res://assets/shaders/lighting_outline.gdshader"))
	if ResourceLoader.exists(shader_path):
		var sh := load(shader_path) as Shader
		if sh != null:
			var mat := ShaderMaterial.new()
			mat.shader = sh
			var p := LightingGD.shader_params()
			mat.set_shader_parameter("light_dir", p["light_dir"])
			mat.set_shader_parameter("rim_add", p["rim_add"] as Color)
			mat.set_shader_parameter("shade_mul", p["shade_mul"])
			mat.set_shader_parameter("band2_ratio", p["band2_ratio"])
			mat.set_shader_parameter("grad_dark", p["grad_dark"])
			mat.set_shader_parameter("grad_light", p["grad_light"])
			mat.set_shader_parameter("grad_sheen", p["grad_sheen"])
			mat.set_shader_parameter("mask_alpha", p["mask_alpha"])
			mat.set_shader_parameter("outline_color", Color(0.05, 0.04, 0.08, 1.0))
			mat.set_shader_parameter("outline_width", 1.0)
			return mat
	# fallback outline biasa
	var outline_shader := load("res://assets/shaders/outline.gdshader") as Shader
	if outline_shader != null:
		var m := ShaderMaterial.new()
		m.shader = outline_shader
		return m
	return null
