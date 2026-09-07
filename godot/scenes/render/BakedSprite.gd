# BakedSprite.gd — unit visual dari strip PNG bake renderer pygame.
#
# Fase 5 Opsi A. Satu scene generik untuk 222 unit; identitas unit
# (tekstur, frame, anchor, skala) datang dari manifest
# res://data/baked_units.json lewat BakedUnitDB — bukan 222 file
# SpriteFrames.tres. SpriteFrames dibangun saat configure_baked()
# dengan mengiris strip per frame memakai AtlasTexture.
#
# Kontrak drive() sama dengan KaizenSkeleton.gd supaya Hero.gd /
# Boss.gd tidak perlu tahu bedanya:
#   drive(phase, action, attack_progress, facing, is_moving, skill, delta)
#
# Pemetaan animasi (sumber = pygame):
#   idle/walk -> playback loop pada fps manifest (6 fps hero / 12 boss —
#     fase baru tiap 10/5 frame, _entity.py:1681 + base_boss.py:580).
#   attack    -> frame DIPAKSA dari attack_progress (deterministik),
#     meniru controller pygame yang menurunkan frame serang dari sisa
#     timer, bukan dari jam playback (bosses/level1.py:841-842).
#   skill     -> belum ada pose bake tersendiri (fase lanjutan); badan
#     memakai pose terakhir + FX proyektil Godot (SkillProjectile.gd)
#     yang memang jalur visual skill sejak Fase 5b.
#
# Anchor: origin node = telapak kaki (sama dengan UnitSilhouette.gd).
# Semua frame strip sudah diratakan pada anchor yang sama saat bake,
# jadi satu offset AnimatedSprite2D berlaku untuk semua frame.
extends Node2D

const BakedUnitDB = preload("res://scripts/render/BakedUnitDB.gd")

@onready var sprite: AnimatedSprite2D = $Sprite

var unit_type := ""
var kind := "hero" # "hero" | "boss" — menentukan skala + fps (manifest)
var _built := false
var _attack_frames := 0
var _action := ""


## Dipanggil Hero.gd/Boss.gd setelah instantiate (pola configure()
## UnitSilhouette). p_kind: "hero" = jalur hero lane pygame (di-scale
## _get_hero_scale, heroes/__init__.py:2148), "boss" = jalur boss native
## 1.0 (heroes/__init__.py:2873-2878).
func configure_baked(p_type: String, p_kind: String, p_team: String) -> void:
	var e: Dictionary = BakedUnitDB.entry(p_type)
	if e.is_empty():
		# Registry seharusnya sudah menyaring; guard supaya unit tidak
		# tampil sebagai kotak putih kalau manifest berubah.
		visible = false
		push_warning("[BakedSprite] manifest tanpa entri: " + p_type)
		return
	unit_type = p_type
	kind = p_kind

	var tex: Texture2D = BakedUnitDB.texture(p_type)
	if tex == null:
		visible = false
		return

	var cw: int = int(e.get("frame_w", 0))
	var ch: int = int(e.get("frame_h", 0))
	if cw <= 0 or ch <= 0:
		visible = false
		return

	var fps := int(e.get("fps_boss", 12)) if kind == "boss" \
			else int(e.get("fps_hero", 6))
	var scale_val := float(e.get("boss_scale", 1.0)) if kind == "boss" \
			else float(e.get("hero_scale", 1.0))
	var anims: Dictionary = e.get("anims", {})
	# Strip = grid (bukan satu baris): 24 frame berjajar bisa 6.648 px —
	# melebihi batas tekstur GPU mobile. frames_per_row dari bake.
	var fpr: int = max(1, int(e.get("frames_per_row", 24)))

	var frames := SpriteFrames.new()
	# SpriteFrames baru di Godot 4 sudah berisi satu animasi kosong
	# bernama "default" — dihapus kalau ada (has_animation, buang langsung
	# remove_animation: animasi tak dikenal = error runtime).
	if frames.has_animation(&"default"):
		frames.remove_animation(&"default")
	for anim in ["idle", "walk", "attack"]:
		var spec: Array = anims.get(anim, [0, 0])
		var first: int = int(spec[0])
		var count: int = int(spec[1])
		frames.add_animation(StringName(anim))
		# Loop untuk semua aksi: attack di-pause per-frame oleh drive(),
		# jadi flag loop hanya berarti untuk idle/walk.
		frames.set_animation_loop(StringName(anim), true)
		frames.set_animation_speed(StringName(anim), fps)
		for i in count:
			# Indeks frame global -> (baris, kolom) grid strip.
			var idx := first + i
			var at := AtlasTexture.new()
			at.atlas = tex
			at.region = Rect2((idx % fpr) * cw, (idx / fpr) * ch, cw, ch)
			frames.add_frame(StringName(anim), at)
		if anim == "attack":
			_attack_frames = count

	sprite.sprite_frames = frames
	var anchor: Array = e.get("anchor", [cw / 2, ch])
	# centered=false + offset negatif = titik anchor jatuh tepat di
	# origin node (telapak kaki), apa pun ukuran sel.
	sprite.centered = false
	sprite.offset = Vector2(-float(anchor[0]), -float(anchor[1]))
	sprite.scale = Vector2.ONE * scale_val

	# Pasca-pass pygame hanya berlaku di jalur HERO lane: outline gelap
	# 1 px + rim cahaya (_finish_hd_sprite, heroes/__init__.py:1866+).
	# Jalur boss native sengaja polos (heroes/__init__.py:2849-2878),
	# maka material dimatikan untuk kind=boss.
	if kind == "hero" and sprite.material is ShaderMaterial:
		# PENTING duplicate(): sub_resource .tscn DIKUNCI satu instance
		# bersama seluruh spawn (kecuali local_to_scene). Tanpa ini,
		# set_shader_parameter("rim_color") hero terakhir menimpa rim
		# semua hero lain — bug yang tidak kelihatan oleh gdparse/
		# check_refs karena murni perilaku runtime resource sharing.
		var mat: ShaderMaterial = (sprite.material as ShaderMaterial).duplicate()
		sprite.material = mat
		# Rim hangat/dingin per tim — paritas _HD_RIM_ADD vs
		# _HD_RIM_ADD_RED (heroes/__init__.py:1880-1883).
		var rim := Color("#222030") if p_team == "blue" \
				else Color("#302018")
		mat.set_shader_parameter("rim_color", Vector4(
				rim.r, rim.g, rim.b, 1.0))
	elif kind == "boss":
		# Boss pygame native tanpa outline/rim pass.
		sprite.material = null

	sprite.play(&"idle")
	_built = true
	_action = "idle"


func drive(_phase: float, action: String, attack_progress: float,
		_facing: int, _is_moving: bool, _skill: String,
		_delta: float) -> void:
	if not _built:
		return
	var want := "idle"
	if action == "walk" or action == "attack":
		want = action
	if want != _action:
		_action = want
		sprite.play(StringName(want))
	if _action == "attack" and _attack_frames > 1:
		# Frame deterministik dari progress serangan (0..1) — bukan jam.
		sprite.pause()
		var idx := clampi(int(round(
				clampf(attack_progress, 0.0, 1.0)
				* (_attack_frames - 1))), 0, _attack_frames - 1)
		if sprite.frame != idx:
			sprite.set_frame(idx)
	elif not sprite.is_playing():
		# Kembali dari pause attack ke loop idle/walk.
		sprite.play(StringName(_action))
