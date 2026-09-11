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
#   skill_*   -> Fase 5c: 6 frame/pose dari <type>.skill.png, frame
#     DIPAKSA dari countdown cast (progress = 1-sisa/dur) seperti
#     renderer pygame (mis. _skill_progress heroes/_bundle.py:6807).
#     Prioritas DI ATAS attack; pose yang tidak lolos gerbang bake
#     (statis/rusak) fallback ke attack. FX proyektil Godot
#     (SkillProjectile.gd) tetap jalan di atasnya seperti Fase 5b.
#   rage_*    -> Fase 5c: varian idle/walk/attack dari <type>.rage.png
#     selama flag rage aktif (drakar: 300 frame sejak cast q —
#     paritas rage_active hero_skills/_bundle.py).
#
# Anchor: origin node = telapak kaki (sama dengan UnitSilhouette.gd).
# Semua frame strip sudah diratakan pada anchor yang sama saat bake,
# jadi satu offset AnimatedSprite2D berlaku untuk semua frame.
extends Node2D

const BakedUnitDB = preload("res://scripts/render/BakedUnitDB.gd")
const Lighting = preload("res://scripts/render/Lighting.gd")

@onready var sprite: AnimatedSprite2D = $Sprite
var _lighting_mat: ShaderMaterial = null

var unit_type := ""
var kind := "hero" # "hero" | "boss" — menentukan skala + fps (manifest)
var _built := false
var _attack_frames := 0
var _skill_frames := 0
var _action := ""
# Countdown cast skill (detik, cermin active_skill_timer SkillBook) +
# countdown flag rage. Di-tick di drive() — bukan _process — supaya
# pose tidak maju saat game dijeda (drive hanya dipanggil physics).
var _skill_key := ""
var _skill_t := 0.0
var _skill_dur := 1.0
var _rage_t := 0.0
var _rage_skill := ""
var _rage_dur := 0.0
# Offset per strip (sel skill/rage ukurannya beda dari sel dasar —
# satu AnimatedSprite2D hanya punya satu offset, jadi diganti tiap
# ganti strip, bukan tiap frame).
var _offset_base := Vector2.ZERO
var _offset_skill := Vector2.ZERO
var _offset_rage := Vector2.ZERO


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
		_add_strip_frames(frames, anim, tex, first, count, cw, ch, fpr)
		if anim == "attack":
			_attack_frames = count
	_build_skill_anims(frames, e)
	_build_rage_anims(frames, e)

	sprite.sprite_frames = frames
	var anchor: Array = e.get("anchor", [cw / 2, ch])
	# centered=false + offset negatif = titik anchor jatuh tepat di
	# origin node (telapak kaki), apa pun ukuran sel.
	sprite.centered = false
	_offset_base = Vector2(-float(anchor[0]), -float(anchor[1]))
	sprite.offset = _offset_base
	sprite.scale = Vector2.ONE * scale_val

	# Pasca-pass pygame hanya berlaku di jalur HERO lane: outline gelap
	# 1 px + rim cahaya (_finish_hd_sprite, heroes/__init__.py:1866+).
	# Jalur boss native sengaja polos (heroes/__init__.py:2849-2878),
	# maka material dimatikan untuk kind=boss — KECUALI bila lighting
	# shader aktif (port lighting.py -> godot++), maka boss juga dapat
	# rim+terminator+gradient GPU (Fase Lighting).
	var use_lighting: bool = bool(ProjectSettings.get_setting("mystic/rendering/use_lighting_shader", true))
	var lighting_path: String = str(ProjectSettings.get_setting("mystic/rendering/lighting_shader_path", "res://assets/shaders/lighting_outline.gdshader"))

	if kind == "hero" and sprite.material is ShaderMaterial:
		# PENTING duplicate(): sub_resource .tscn DIKUNCI satu instance
		# bersama seluruh spawn (kecuali local_to_scene). Tanpa ini,
		# set_shader_parameter("rim_color") hero terakhir menimpa rim
		# semua hero lain — bug yang tidak kelihatan oleh gdparse/
		# check_refs karena murni perilaku runtime resource sharing.
		var mat: ShaderMaterial = (sprite.material as ShaderMaterial).duplicate()
		# Jika lighting shader aktif, ganti dengan lighting_outline yang sudah
		# mencakup outline + lighting.py (rim+terminator+gradient) dalam 1 pass
		if use_lighting and ResourceLoader.exists(lighting_path):
			var l_shader := load(lighting_path) as Shader
			if l_shader != null:
				var l_mat := ShaderMaterial.new()
				l_mat.shader = l_shader
				# Paritas lighting.py — shader sekarang vec4 rim_add (source_color)
				var lp := Lighting.shader_params()
				l_mat.set_shader_parameter("light_dir", lp["light_dir"])
				l_mat.set_shader_parameter("rim_add", lp["rim_add"] as Color)
				l_mat.set_shader_parameter("shade_mul", lp["shade_mul"])
				l_mat.set_shader_parameter("band2_ratio", lp["band2_ratio"])
				l_mat.set_shader_parameter("grad_dark", lp["grad_dark"])
				l_mat.set_shader_parameter("grad_light", lp["grad_light"])
				l_mat.set_shader_parameter("grad_sheen", lp["grad_sheen"])
				l_mat.set_shader_parameter("mask_alpha", lp["mask_alpha"])
				# outline dari material lama tetap dipakai
				l_mat.set_shader_parameter("outline_color", Color(0.05, 0.04, 0.08, 1.0))
				l_mat.set_shader_parameter("outline_width", 1.0)
				mat = l_mat
				_lighting_mat = l_mat
		sprite.material = mat
		# Rim hangat/dingin per tim — paritas _HD_RIM_ADD vs
		# _HD_RIM_ADD_RED (heroes/__init__.py:1880-1883).
		# Untuk lighting shader, rim_add sudah di-set dari Lighting.gd,
		# tapi kita tetap adjust sedikit untuk team tint (biru/merah tipis
		# seperti _finish_hd_sprite).
		if _lighting_mat == null:
			var rim := Color("#222030") if p_team == "blue" \
					else Color("#302018")
			mat.set_shader_parameter("rim_color", Vector4(
					rim.r, rim.g, rim.b, 1.0))
		else:
			# Team tint ditambahkan ke rim_add base (30,26,44)
			var base_rim: Color = Lighting.RIM_ADD
			var team_tint := Color("#1a1a2e") if p_team == "blue" else Color("#2e1a1a")
			var final_rim := base_rim + team_tint * 0.35
			_lighting_mat.set_shader_parameter("rim_add", final_rim)
	elif kind == "boss":
		if use_lighting and ResourceLoader.exists(lighting_path):
			# Boss juga dapat lighting (lebih subtle, tanpa outline tebal)
			var l_shader := load(lighting_path) as Shader
			if l_shader != null:
				var l_mat := ShaderMaterial.new()
				l_mat.shader = l_shader
				var lp := Lighting.shader_params()
				l_mat.set_shader_parameter("light_dir", lp["light_dir"])
				l_mat.set_shader_parameter("rim_add", lp["rim_add"] as Color)
				l_mat.set_shader_parameter("shade_mul", lp["shade_mul"])
				l_mat.set_shader_parameter("band2_ratio", lp["band2_ratio"])
				l_mat.set_shader_parameter("grad_dark", lp["grad_dark"])
				l_mat.set_shader_parameter("grad_light", lp["grad_light"])
				l_mat.set_shader_parameter("grad_sheen", lp["grad_sheen"])
				l_mat.set_shader_parameter("mask_alpha", lp["mask_alpha"])
				l_mat.set_shader_parameter("outline_color", Color(0.05, 0.04, 0.08, 0.0))
				l_mat.set_shader_parameter("outline_width", 0.0)
				sprite.material = l_mat
				_lighting_mat = l_mat
		else:
			# Boss pygame native tanpa outline/rim pass.
			sprite.material = null

	sprite.play(&"idle")
	_built = true
	_action = "idle"


## Iris [first, first+count) dari strip grid ke animasi SpriteFrames.
func _add_strip_frames(frames: SpriteFrames, anim: String, tex: Texture2D,
		first: int, count: int, cw: int, ch: int, fpr: int) -> void:
	for i in count:
		# Indeks frame global -> (baris, kolom) grid strip.
		var idx := first + i
		var at := AtlasTexture.new()
		at.atlas = tex
		at.region = Rect2((idx % fpr) * cw, (idx / fpr) * ch, cw, ch)
		frames.add_frame(StringName(anim), at)


## Animasi skill_q/w/e/r dari strip skill (Fase 5c, skema 2). Pose yang
## tidak ada di skill_anims dilewati — drive() fallback ke attack.
func _build_skill_anims(frames: SpriteFrames, e: Dictionary) -> void:
	var stex: Texture2D = BakedUnitDB.texture_skill(unit_type)
	if stex == null:
		return
	var cw: int = int(e.get("skill_frame_w", 0))
	var ch: int = int(e.get("skill_frame_h", 0))
	if cw <= 0 or ch <= 0:
		return
	var fpr: int = max(1, int(e.get("skill_frames_per_row", 8)))
	var anchor: Array = e.get("skill_anchor", e.get("anchor", [cw / 2, ch]))
	_offset_skill = Vector2(-float(anchor[0]), -float(anchor[1]))
	# `key: String` (bukan `key` polos): iterator array literal bertipe Variant,
	# jadi `"skill_" + key` di bawah tidak bisa di-infer oleh `:=`.
	for key: String in ["q", "w", "e", "r"]:
		var spec: Array = BakedUnitDB.skill_anim(unit_type, key)
		if spec.size() < 2:
			continue
		var count: int = int(spec[1])
		if count <= 0:
			continue
		var anim := "skill_" + key
		frames.add_animation(StringName(anim))
		frames.set_animation_loop(StringName(anim), true)
		# Speed = panjang cast (frame dirata-rata ke durasi), tapi
		# drive() memaksa frame dari countdown — speed hanya cadangan
		# kalau anim sempat ter-play tanpa pause (tidak boleh terjadi).
		var dur_f := BakedUnitDB.skill_duration_frames(unit_type, key)
		var speed := float(count) / maxf(dur_f / 60.0, 0.01) \
				if dur_f > 0.0 else 6.0
		frames.set_animation_speed(StringName(anim), speed)
		_add_strip_frames(frames, anim, stex, int(spec[0]), count,
				cw, ch, fpr)
		_skill_frames = maxi(_skill_frames, count)


## Animasi rage_idle/walk/attack dari strip rage (Fase 5c). Tata letak
## strip rage = strip dasar (idle|walk|attack berurutan, 8 frame
## per aksi) karena dibake oleh fungsi yang sama dengan flag
## rage_active menyala (tools/convert_to_godot.py).
func _build_rage_anims(frames: SpriteFrames, e: Dictionary) -> void:
	var rtex: Texture2D = BakedUnitDB.texture_rage(unit_type)
	if rtex == null:
		return
	var cw: int = int(e.get("rage_frame_w", 0))
	var ch: int = int(e.get("rage_frame_h", 0))
	if cw <= 0 or ch <= 0:
		return
	var fpr: int = max(1, int(e.get("rage_frames_per_row", 8)))
	var anchor: Array = e.get("rage_anchor", e.get("anchor", [cw / 2, ch]))
	_offset_rage = Vector2(-float(anchor[0]), -float(anchor[1]))
	var fc: Dictionary = BakedUnitDB.frame_counts()
	var first := 0
	var fps := int(e.get("fps_boss", 12)) if kind == "boss" \
			else int(e.get("fps_hero", 6))
	# `anim: String` — sama seperti _build_skill_anims: tanpa tipe eksplisit
	# `"rage_" + anim` bertipe Variant dan `:=` gagal infer.
	for anim: String in ["idle", "walk", "attack"]:
		var count: int = int(fc.get(anim, 8))
		var ranim := "rage_" + anim
		frames.add_animation(StringName(ranim))
		frames.set_animation_loop(StringName(ranim), true)
		frames.set_animation_speed(StringName(ranim), fps)
		_add_strip_frames(frames, ranim, rtex, first, count, cw, ch, fpr)
		first += count
	var rage: Dictionary = BakedUnitDB.rage_info(unit_type)
	_rage_skill = str(rage.get("skill", ""))
	_rage_dur = float(rage.get("duration", 0.0)) / 60.0


func drive(_phase: float, action: String, attack_progress: float,
	_facing: int, _is_moving: bool, skill: String,
	delta: float) -> void:
	if not _built:
		return
	_tick_skill(skill, delta)
	var want := "idle"
	if action == "walk" or action == "attack":
		want = action
	# Skill DI ATAS attack (paritas pygame: cabang skill digambar
	# sebagai lapisan pose sendiri saat active_skill menyala —
	# heroes/__init__.py:1750-1766). Tanpa pose bake = fallback attack.
	var skill_anim := "skill_" + _skill_key
	if _skill_key != "" \
			and sprite.sprite_frames.has_animation(StringName(skill_anim)):
		want = skill_anim
	elif _rage_t > 0.0 \
			and sprite.sprite_frames.has_animation(
				StringName("rage_" + want)):
		# Varian rage menggantikan pose dasar selama flag aktif.
		want = "rage_" + want
	if want != _action:
		_action = want
		if want.begins_with("skill_"):
			sprite.offset = _offset_skill
		elif want.begins_with("rage_"):
			sprite.offset = _offset_rage
		else:
			sprite.offset = _offset_base
		sprite.play(StringName(want))
	if _action.begins_with("skill_") and _skill_frames > 1:
		# Frame skill dari countdown cast (progress 0->1), meniru
		# renderer pygame — bukan dari jam playback.
		sprite.pause()
		var sprogress := 1.0 - _skill_t / maxf(_skill_dur, 0.001)
		_set_forced_frame(sprogress, _skill_frames)
	elif (_action == "attack" or _action == "rage_attack") \
			and _attack_frames > 1:
		# Frame deterministik dari progress serangan (0..1) — bukan jam.
		sprite.pause()
		_set_forced_frame(attack_progress, _attack_frames)
	elif not sprite.is_playing():
		# Kembali dari pause attack/skill ke loop idle/walk.
		sprite.play(StringName(_action))


## Frame paksa dari progress 0..1 (attack & skill, paritas countdown).
func _set_forced_frame(progress: float, count: int) -> void:
	var idx := clampi(int(round(
			clampf(progress, 0.0, 1.0) * (count - 1))), 0, count - 1)
	if sprite.frame != idx:
		sprite.set_frame(idx)


## Countdown cast + pemicu rage. Cermin active_skill_timer SkillBook
## (keduanya di-tick per physics frame dari durasi manifest yang sama,
## jadi berakhir bersamaan; frame dihitung dari countdown ini karena
## drive() tidak menerima sisa timer).
func _tick_skill(skill: String, delta: float) -> void:
	if skill != _skill_key:
		_skill_key = skill
		if skill == "":
			_skill_t = 0.0
		else:
			var dur_f := BakedUnitDB.skill_duration_frames(
					unit_type, skill)
			_skill_dur = dur_f / 60.0 if dur_f > 0.0 else 0.6
			_skill_t = _skill_dur
			# Cast skill pemicu menyalakan flag rage (drakar q -> 300
			# frame), paritas cast_flags hero_skills/_bundle.py.
			if _rage_skill != "" and skill == _rage_skill:
				_rage_t = _rage_dur
	if _skill_t > 0.0:
		_skill_t = maxf(0.0, _skill_t - delta)
	if _rage_t > 0.0:
		_rage_t = maxf(0.0, _rage_t - delta)
