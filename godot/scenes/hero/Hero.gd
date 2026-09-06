# Hero.gd — Port dari _entity.py Hero class
# Visual: Skeleton2D + AnimatedSprite2D + Shader + Particles (DRAMATIC UPGRADE dari pygame.draw.polygon)
extends CharacterBody2D

@export var hero_type: String = "kaizen"
@export var team: String = "blue"

# Stats (diisi dari HeroDB)
var max_hp: float = 850
var hp: float = 850
var damage: float = 72
var move_speed: float = 180.0
var attack_range: float = 70.0
var attack_cooldown: float = 0.52 # detik (32/60)
var dmg_school: String = "physical"

# State
var target: Node2D = null
var attack_timer: float = 0.0
var is_dead: bool = false
var facing: int = 1

# Visual nodes (di-assign di _ready)
@onready var sprite: AnimatedSprite2D = $Visual/AnimatedSprite2D
@onready var visual_root: Node2D = $Visual
@onready var shadow: Sprite2D = $Shadow
@onready var hp_bar: ProgressBar = $UI/HPBar
@onready var name_label: Label = $UI/NameLabel
@onready var hit_particles: GPUParticles2D = $FX/HitParticles
@onready var skill_particles: GPUParticles2D = $FX/SkillParticles
@onready var anim_player: AnimationPlayer = $AnimationPlayer

# Kaizen Skeleton2D (Dramatic upgrade — Spine-like GPU bones)
const KaizenSkeletonScene = preload("res://scenes/hero/kaizen/KaizenSkeleton.tscn")
var kaizen_skeleton: Node2D = null
var anim_phase: float = 0.0

# Shader material untuk hit flash + outline (menggantikan hurt_flash_timer di pygame)
var hit_flash_mat: ShaderMaterial

func _ready():
	apply_hero_data()
	setup_visual()
	update_ui()
	# Godot physics: collision layer beda per team (blue=2, red=4)
	collision_layer = 2 if team == "blue" else 4
	collision_mask = 4 if team == "blue" else 2

func apply_hero_data():
	var s = HeroDB.get_balanced_stats(hero_type)
	if s.is_empty():
		push_warning("Unknown hero: %s" % hero_type)
		return
	max_hp = s["hp"]
	hp = max_hp
	damage = s["damage"]
	move_speed = s["speed"] * 60.0 # pygame speed 1.6 -> Godot 96 px/s, scale 60
	attack_range = s["range"]
	attack_cooldown = s["attack_cooldown"] / 60.0
	dmg_school = s.get("dmg_school", "physical")
	name = s.get("name", hero_type)

func setup_visual():
	# === KAIZEN Skeleton2D — case khusus: GPU bones, bukan sprite sheet ===
	if hero_type == "kaizen":
		sprite.visible = false
		kaizen_skeleton = KaizenSkeletonScene.instantiate()
		kaizen_skeleton.name = "KaizenSkeleton"
		visual_root.add_child(kaizen_skeleton)
		kaizen_skeleton.position = Vector2(0, -6)
		shadow.position = Vector2(0, 28)
		shadow.scale = Vector2(1.6, 0.55)
		# skeleton sudah punya hamon shader sendiri; outline fallback tidak perlu
		if anim_player and not anim_player.has_animation("idle"):
			_create_procedural_animations()
		shadow.modulate.a = 0.35
		return

	# === UPGRADE VISUAL DRASTIS vs pygame (hero lain pakai sprite sheet HD) ===
	# 1. AnimatedSprite2D: ganti pygame.draw.* procedural dengan sprite sheet HD
	#    SpriteFrames diisi dari res://assets/heroes/<hero_type>/ (Aseprite export)
	var frames_path = "res://assets/heroes/%s/SpriteFrames.tres" % hero_type
	if ResourceLoader.exists(frames_path):
		sprite.sprite_frames = load(frames_path)
		sprite.play("idle")
	else:
		# Fallback: warna solid + shader (kalau asset belum ada)
		# Tetap terlihat premium karena shader outline + shadow
		sprite.modulate = HeroDB.get_hero_color(hero_type)
		# Buat placeholder texture 64x64
		var img = Image.create(64, 64, false, Image.FORMAT_RGBA8)
		img.fill(HeroDB.get_hero_color(hero_type))
		sprite.sprite_frames = SpriteFrames.new()
		sprite.sprite_frames.add_animation("idle")
		sprite.sprite_frames.add_frame("idle", ImageTexture.create_from_image(img))

	# 2. Outline shader (menggantikan 5x blit outline di pygame)
	#    Shader: res://assets/shaders/outline.gdshader
	if ResourceLoader.exists("res://assets/shaders/outline.gdshader"):
		hit_flash_mat = ShaderMaterial.new()
		hit_flash_mat.shader = load("res://assets/shaders/outline.gdshader")
		hit_flash_mat.set_shader_parameter("outline_color", Color(1,1,1,1) if team=="blue" else Color(1,0.2,0.2,1))
		hit_flash_mat.set_shader_parameter("outline_width", 1.5)
		sprite.material = hit_flash_mat

	# 3. AnimationPlayer: idle bob, walk cycle, attack swing, hurt flash
	#    (menggantikan _update_attack_anim + walk_cycle manual di pygame)
	if anim_player and not anim_player.has_animation("idle"):
		_create_procedural_animations()

	# 4. Shadow + Lighting
	#    Di Godot: PointLight2D + CanvasModulate, bukan ellipse hitam manual
	shadow.modulate.a = 0.35

func _create_procedural_animations():
	# Buat animasi procedural kalau belum ada SpriteFrames anim
	# Idle: subtle scale bob (mirip _head_bob di pygame)
	var idle = Animation.new()
	idle.length = 1.0
	idle.loop_mode = Animation.LOOP_LINEAR
	var track = idle.add_track(Animation.TYPE_VALUE)
	idle.track_set_path(track, "%s:scale" % visual_root.get_path())
	idle.track_insert_key(track, 0.0, Vector2(1,1))
	idle.track_insert_key(track, 0.5, Vector2(1, 1.04))
	idle.track_insert_key(track, 1.0, Vector2(1,1))
	var lib = AnimationLibrary.new()
	lib.add_animation("idle", idle)
	anim_player.add_animation_library("", lib)
	anim_player.play("idle")

func _physics_process(delta):
	if is_dead:
		return
	attack_timer = max(0, attack_timer - delta)
	anim_phase += delta * 6.0  # phase untuk Skeleton2D (breath + stride)

	# AI sederhana: cari target terdekat (port dari Hero._find_hunt_target)
	if not target or not is_instance_valid(target) or target.is_dead:
		target = find_nearest_enemy()

	var is_moving := false
	if target:
		var dist = global_position.distance_to(target.global_position)
		facing = 1 if target.global_position.x > global_position.x else -1
		visual_root.scale.x = facing # flip sprite / skeleton

		if dist <= attack_range:
			velocity = Vector2.ZERO
			is_moving = false
			try_attack()
		else:
			# Move toward target (menggantikan _move_toward pygame)
			var dir = (target.global_position - global_position).normalized()
			velocity = dir * move_speed
			is_moving = true
			if sprite.sprite_frames and sprite.sprite_frames.has_animation("walk"):
				sprite.play("walk")
			move_and_slide()
	else:
		# Push ke base musuh (mirip pygame PUSH)
		var push_target = Vector2(1100, 360) if team=="blue" else Vector2(100, 360)
		var dir = (push_target - global_position).normalized()
		velocity = dir * move_speed * 0.6
		is_moving = velocity.length() > 5.0
		move_and_slide()
		if sprite.sprite_frames and sprite.sprite_frames.has_animation("walk"):
			sprite.play("walk")

	# === Drive Kaizen Skeleton2D setiap frame ===
	if kaizen_skeleton and kaizen_skeleton.has_method("drive"):
		var ap: float = 0.0
		if attack_timer > 0.0:
			ap = 1.0 - attack_timer / attack_cooldown
		var kaizen_action := "idle"
		if attack_timer > 0.0:
			kaizen_action = "attack"
		elif is_moving:
			kaizen_action = "walk"
		kaizen_skeleton.drive(anim_phase, kaizen_action, ap, facing, is_moving, "", delta)

func find_nearest_enemy() -> Node2D:
	var best = null
	var best_dist = 900.0
	# Cari di group "heroes" + "bosses" + "minions"
	for group in ["heroes","bosses","minions","towers"]:
		for n in get_tree().get_nodes_in_group(group):
			if n == self: continue
			if n.team == team: continue
			if n.has_method("is_dead") and n.is_dead: continue
			if not n.has_method("take_damage"): continue
			var d = global_position.distance_to(n.global_position)
			if d < best_dist:
				best_dist = d
				best = n
	return best

func try_attack():
	if attack_timer > 0:
		return
	if not target or target.is_dead:
		return
	attack_timer = attack_cooldown
	# Animasi attack (5x lebih smooth dari pygame 6 frame)
	if hero_type != "kaizen" and sprite.sprite_frames and sprite.sprite_frames.has_animation("attack"):
		sprite.play("attack")
		if not sprite.animation_finished.is_connected(func(): sprite.play("idle")):
			sprite.animation_finished.connect(func(): sprite.play("idle"), CONNECT_ONE_SHOT)
	# Hit-stop + screenshake (menggantikan combat_feel.hit_stop pygame)
	_hit_stop(0.03)
	if get_tree() and get_tree().has_group("camera"):
		get_tree().call_group("camera","add_trauma", 0.15)

	# Damage (hitung crit, lifesteal, dll. via CombatSystem)
	var dmg = CombatSystem.calc_damage(self, target, damage, dmg_school)
	target.take_damage(dmg, team, "normal", self, dmg_school)
	# VFX
	if hit_particles:
		hit_particles.global_position = target.global_position
		hit_particles.emitting = true
		hit_particles.restart()

func take_damage(amount: float, from_team: String, dmg_type: String = "normal", source = null, school: String = ""):
	if is_dead: return
	# School mitigation (armor/magic_resist) via CombatSystem
	var mitigated = CombatSystem.mitigate_damage(self, amount, school if school != "" else dmg_school)
	hp -= mitigated
	# Hit flash shader (menggantikan hurt_flash_timer 8 frame pygame)
	if hit_flash_mat:
		hit_flash_mat.set_shader_parameter("flash_amount", 1.0)
		create_tween().tween_property(hit_flash_mat, "shader_parameter/flash_amount", 0.0, 0.12)
	# Kaizen skeleton flash (GPU modulate, tanpa shader outline)
	if kaizen_skeleton:
		kaizen_skeleton.modulate = Color(1, 0.85, 0.85, 1)
		create_tween().tween_property(kaizen_skeleton, "modulate", Color(1,1,1,1), 0.14)
		# wind puff on hit
		if skill_particles:
			skill_particles.global_position = global_position + Vector2(0, -12)
			skill_particles.emitting = true
			skill_particles.restart()
	# Damage number (menggantikan FloatingText pygame)
	var num = preload("res://scenes/fx/DamageNumber.tscn").instantiate()
	num.setup(str(int(mitigated)), mitigated > max_hp*0.2)
	num.global_position = global_position + Vector2(randf_range(-10,10), -30)
	if get_tree().current_scene:
		get_tree().current_scene.add_child(num)
	else:
		add_child(num)

	if hp <= 0:
		die(source)
	update_ui()

func die(killer = null):
	is_dead = true
	add_to_group("dead")
	# Death animation GPU (bukan fade ellipse manual pygame)
	if anim_player.has_animation("death"):
		anim_player.play("death")
	else:
		var tw = create_tween()
		tw.parallel().tween_property(visual_root, "scale", Vector2(1.4,0.2), 0.25)
		tw.parallel().tween_property(self, "modulate:a", 0.0, 0.35)
		tw.tween_callback(queue_free)
	GameManager.hero_died.emit(self)

func update_ui():
	if hp_bar:
		hp_bar.max_value = max_hp
		hp_bar.value = hp
	if name_label:
		name_label.text = "%s Lv%d" % [name, 1]

func _hit_stop(duration: float):
	Engine.time_scale = 0.05
	await get_tree().create_timer(duration * Engine.time_scale, true, false, true).timeout
	Engine.time_scale = 1.0

# Skill QWER — delegate ke HeroSkills (port dari hero_skills/)
func cast_q(): _cast_skill("q")
func cast_w(): _cast_skill("w")
func cast_e(): _cast_skill("e")
func cast_r(): _cast_skill("r")

func _cast_skill(key: String):
	var skill_node = get_node_or_null("Skills/%s" % key.to_upper())
	if skill_node and skill_node.has_method("cast"):
		skill_node.cast(self, target)
