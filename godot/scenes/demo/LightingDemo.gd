# LightingDemo.gd — showcase migrasi lighting.py -> godot++
# F5 Run Current Scene untuk lihat perbandingan:
#   - Kiri: sprite tanpa lighting
#   - Tengah: shader lighting.gdshader (GPU, 0.04ms)
#   - Kanan: shader lighting_outline.gdshader (outline + lighting 1 pass)
#   - Bawah: CPU Image (Lighting.gd) vs C++ (MysticLighting) kalau GDExtension ada
#
# Kontrol:
#   L = toggle lighting shader
#   G = toggle gradient
#   R = reset cache
#   SPACE = re-apply CPU lighting ke texture kanan bawah

extends Node2D

const Lighting = preload("res://scripts/render/Lighting.gd")
const LightingCompat = preload("res://scripts/render/LightingCompat.gd")

var _use_lighting := true
var _gradient := true
var _time := 0.0

@onready var label_info: Label = $CanvasLayer/Info
@onready var sprites: Array = [$Sprites/NoLighting, $Sprites/Lighting, $Sprites/LightingOutline, $Sprites/CPULighting]

func _ready() -> void:
	print("[LightingDemo] Showcase lighting.py -> godot++")
	print("  L=toggle lighting, G=gradient, R=reset cache, SPACE=re-apply CPU")
	# Load contoh texture unit kalau ada, fallback ke icon
	var tex: Texture2D = null
	if ResourceLoader.exists("res://assets/units/kaizen.png"):
		tex = load("res://assets/units/kaizen.png") as Texture2D
		# Ambil frame pertama dari strip (asumsi 8 frame per baris)
		if tex != null:
			var e: Dictionary = {}
			if FileAccess.file_exists("res://data/baked_units.json"):
				var raw := FileAccess.get_file_as_string("res://data/baked_units.json")
				var parsed = JSON.parse_string(raw)
				if parsed is Dictionary:
					e = parsed.get("units", {}).get("kaizen", {})
			var cw: int = int(e.get("frame_w", 0))
			var ch: int = int(e.get("frame_h", 0))
			if cw > 0 and ch > 0:
				var at := AtlasTexture.new()
				at.atlas = tex
				at.region = Rect2(0,0,cw,ch)
				tex = at
	if tex == null:
		tex = load("res://assets/icon.png") as Texture2D

	for s in sprites:
		if s is Sprite2D:
			s.texture = tex
			s.centered = true

	_setup_materials()
	_apply_cpu_lighting()

func _setup_materials() -> void:
	# NoLighting = tanpa material
	var no_light: Sprite2D = $Sprites/NoLighting
	no_light.material = null

	# Lighting = lighting.gdshader
	var lighting: Sprite2D = $Sprites/Lighting
	var sh1 := load("res://assets/shaders/lighting.gdshader") as Shader
	if sh1 != null:
		var mat := ShaderMaterial.new()
		mat.shader = sh1
		var p := Lighting.shader_params()
		mat.set_shader_parameter("light_dir", p["light_dir"])
		mat.set_shader_parameter("rim_add", Vector3(p["rim_add"].r, p["rim_add"].g, p["rim_add"].b))
		mat.set_shader_parameter("shade_mul", p["shade_mul"])
		mat.set_shader_parameter("band2_ratio", p["band2_ratio"])
		mat.set_shader_parameter("grad_dark", p["grad_dark"])
		mat.set_shader_parameter("grad_light", p["grad_light"])
		mat.set_shader_parameter("grad_sheen", p["grad_sheen"])
		mat.set_shader_parameter("mask_alpha", p["mask_alpha"])
		mat.set_shader_parameter("gradient_enabled", _gradient)
		lighting.material = mat

	# LightingOutline = gabungan
	var lo: Sprite2D = $Sprites/LightingOutline
	var sh2 := load("res://assets/shaders/lighting_outline.gdshader") as Shader
	if sh2 != null:
		var mat2 := ShaderMaterial.new()
		mat2.shader = sh2
		var p := Lighting.shader_params()
		mat2.set_shader_parameter("light_dir", p["light_dir"])
		mat2.set_shader_parameter("rim_add", Vector3(p["rim_add"].r, p["rim_add"].g, p["rim_add"].b))
		mat2.set_shader_parameter("shade_mul", p["shade_mul"])
		mat2.set_shader_parameter("band2_ratio", p["band2_ratio"])
		mat2.set_shader_parameter("grad_dark", p["grad_dark"])
		mat2.set_shader_parameter("grad_light", p["grad_light"])
		mat2.set_shader_parameter("grad_sheen", p["grad_sheen"])
		mat2.set_shader_parameter("mask_alpha", p["mask_alpha"])
		mat2.set_shader_parameter("gradient_enabled", _gradient)
		mat2.set_shader_parameter("outline_color", Color(0.05,0.04,0.08,1))
		mat2.set_shader_parameter("outline_width", 1.5)
		lo.material = mat2

func _apply_cpu_lighting() -> void:
	var cpu: Sprite2D = $Sprites/CPULighting
	if cpu.texture == null:
		return
	var img := cpu.texture.get_image()
	if img == null:
		return
	img = img.duplicate()
	if img.get_format() != Image.FORMAT_RGBA8:
		img.convert(Image.FORMAT_RGBA8)
	# Pakai compat (C++ kalau ada, GDScript kalau tidak)
	var out := LightingCompat.apply_image(img, Lighting.RIM_ADD, Lighting.SHADE_MUL, true, Lighting.MASK_ALPHA, _gradient)
	if out != null:
		var tex := ImageTexture.create_from_image(out)
		cpu.texture = tex
		print("[LightingDemo] CPU lighting applied, has_gdext=%s" % LightingCompat.has_gdext())

func _process(delta: float) -> void:
	_time += delta
	# Animasi bobbing untuk showcase
	for i in sprites.size():
		var s: Node2D = sprites[i]
		s.position.y = 200 + sin(_time * 1.2 + float(i)) * 8.0
	_update_label()

func _update_label() -> void:
	var has_gdext := LightingCompat.has_gdext()
	var txt := """Lighting.py -> Godot++ Showcase
L=toggle lighting (%s)  G=gradient (%s)  R=reset cache  SPACE=re-apply CPU
Shader: lighting.gdshader (GPU 0.04ms) + lighting_outline.gdshader (1 pass)
CPU: Lighting.gd (GDScript) + MysticLighting C++ GDExtension (%s)
Paritas: LIGHT_DIR=(-1,-1) RIM=(30,26,44) SHADE=168 BAND2=0.42 MASK=170 GRAD=205/255/22 STEPS=28
Kiri: No lighting | Tengah: GPU lighting | Kanan: Outline+Lighting | Bawah: CPU Image
""" % ["ON" if _use_lighting else "OFF", "ON" if _gradient else "OFF", "AKTIF" if has_gdext else "fallback GDScript"]
	if label_info:
		label_info.text = txt

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_L:
				_use_lighting = !_use_lighting
				for s in sprites:
					if s is Sprite2D and s != $Sprites/NoLighting and s != $Sprites/CPULighting:
						s.material = null if not _use_lighting else s.material
						if _use_lighting:
							_setup_materials()
			KEY_G:
				_gradient = !_gradient
				_setup_materials()
			KEY_R:
				Lighting.reset_gradient_cache()
				LightingCompat.reset_cache()
				print("[LightingDemo] cache reset")
			KEY_SPACE:
				_apply_cpu_lighting()
