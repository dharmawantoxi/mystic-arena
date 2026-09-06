# Hero.gd — Port dari _entity.py Hero class
# Visual baseline: UnitSilhouette (pygame.draw.circle/polygon). Upgrade
# satu-satu lewat RendererRegistry.HERO[hero_type] = PackedScene custom.
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
var radius: float = 16.0 # paritas _entity.Hero.radius
var role: String = ""
var fill_color: Color = Color("#c8c8c8")
var fill_dark: Color = Color("#646464")

# State
var target: Node2D = null
var attack_timer: float = 0.0
var is_dead: bool = false
var facing: int = 1

# Visual nodes (di-assign di _ready)
@onready var sprite: AnimatedSprite2D = $Visual/AnimatedSprite2D
@onready var visual_root: Node2D = $Visual
@onready var shadow: Node2D = $Shadow # Polygon2D ellipse (0 asset)
@onready var hp_bar: ProgressBar = $UI/HPBar
@onready var name_label: Label = $UI/NameLabel
@onready var hit_particles: GPUParticles2D = $FX/HitParticles
@onready var skill_particles: GPUParticles2D = $FX/SkillParticles
@onready var anim_player: AnimationPlayer = $AnimationPlayer

# Renderer: silhouette pygame (default) ATAU scene custom dari registry
const UnitSilhouetteScript = preload("res://scripts/render/UnitSilhouette.gd")
const RendererRegistry = preload("res://scripts/render/RendererRegistry.gd")
var silhouette = null
var custom_visual = null
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
	role = str(s.get("role", ""))
	name = s.get("name", hero_type)
	fill_color = _parse_color(s.get("color", "#c8c8c8"), Color("#c8c8c8"))
	fill_dark = _parse_color(s.get("color_dark", ""), fill_color.darkened(0.35))
	radius = 16.0

func setup_visual():
	# Baseline pygame: kotak/sprite/tulang DIMATIKAN. Silhouette menggambar
	# lewat _draw(). Scene custom (Kaizen Skeleton2D, SpriteFrames HD) hanya
	# hidup kalau didaftarkan di RendererRegistry — upgrade satu-satu.
	if sprite:
		sprite.visible = false
	if shadow:
		shadow.visible = false
	z_as_relative = false
	var packed: PackedScene = RendererRegistry.hero_scene(hero_type)
	if packed != null:
		custom_visual = packed.instantiate()
		custom_visual.name = "CustomVisual"
		visual_root.add_child(custom_visual)
		custom_visual.position = Vector2(0, -6)
		return
	silhouette = UnitSilhouetteScript.new()
	silhouette.name = "Silhouette"
	visual_root.add_child(silhouette)
	var ranged := attack_range >= 110.0
	silhouette.configure(
		UnitSilhouetteScript.Kind.HERO, hero_type, team, fill_color, fill_dark,
		radius, role, dmg_school, ranged)

func _create_procedural_animations():
	# Buat animasi procedural kalau belum ada SpriteFrames anim
	# Idle: subtle scale bob (mirip _head_bob di pygame)
	var idle = Animation.new()
	idle.length = 1.0
	idle.loop_mode = Animation.LOOP_LINEAR
	var track = idle.add_track(Animation.TYPE_VALUE)
	# Path track relatif ke root scene (AnimationPlayer.root_node = hero),
	# jadi "Visual:scale" — BUKAN absolute NodePath (kalau absolute, Godot
	# spam error "Node not found" tiap frame anim).
	idle.track_set_path(track, ^"Visual:scale")
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
		# Push ke base musuh (mirip pygame PUSH) — titiknya diambil dari ArenaMap
		# supaya tidak hardcode dan tetap benar kalau ukuran/lane map berubah.
		var push_target = enemy_base()
		var dir = (push_target - global_position).normalized()
		velocity = dir * move_speed * 0.6
		is_moving = velocity.length() > 5.0
		move_and_slide()
		if sprite.sprite_frames and sprite.sprite_frames.has_animation("walk"):
			sprite.play("walk")

	# Painter's algorithm pygame: unit lebih bawah menutupi yang di atas
	z_index = int(global_position.y)
	_drive_visual(is_moving, delta)

func _drive_visual(is_moving: bool, delta: float) -> void:
	var ap := 0.0
	if attack_timer > 0.0:
		ap = 1.0 - attack_timer / maxf(0.001, attack_cooldown)
	var act := "idle"
	if attack_timer > 0.0:
		act = "attack"
	elif is_moving:
		act = "walk"
	if silhouette != null and is_instance_valid(silhouette) and silhouette.has_method("drive"):
		silhouette.drive(anim_phase, act, ap, facing)
	elif custom_visual != null and is_instance_valid(custom_visual) and custom_visual.has_method("drive"):
		custom_visual.drive(anim_phase, act, ap, facing, is_moving, "", delta)


static func _parse_color(v, fallback: Color) -> Color:
	if v is Color:
		return v
	var s := str(v).strip_edges()
	if s.is_empty():
		return fallback
	if not s.begins_with("#"):
		s = "#" + s
	var c := Color(s)
	if c.a == 0.0 and s != "#00000000":
		return fallback
	return c


func enemy_base() -> Vector2:
	var am = get_tree().get_first_node_in_group("arena_map")
	if am != null and am.has_method("get_enemy_base"):
		return am.get_enemy_base(team)
	return Vector2(1180, 100) if team == "blue" else Vector2(100, 620)

func find_nearest_enemy() -> Node2D:
	var best = null
	var best_dist = 900.0
	# Cari di group "heroes" + "bosses" + "minions" + "towers"
	for group in ["heroes", "bosses", "minions", "towers"]:
		for n in get_tree().get_nodes_in_group(group):
			if n == self or not is_instance_valid(n):
				continue
			if not n.has_method("take_damage"):
				continue
			if n.get("team") == team:
				continue
			# `is_dead` itu properti, BUKAN method — has_method("is_dead") selalu
			# false, jadi mayat yang masih ada di queue_free ikut jadi target.
			if bool(n.get("is_dead")):
				continue
			var d := global_position.distance_to(n.global_position)
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
	# GPU particles = upgrade. Baseline pygame: damage number di take_damage.

func take_damage(amount: float, from_team: String, dmg_type: String = "normal", source = null, school: String = ""):
	if is_dead: return
	# School mitigation (armor/magic_resist) via CombatSystem
	var mitigated = CombatSystem.mitigate_damage(self, amount, school if school != "" else dmg_school)
	hp -= mitigated
	if silhouette != null and is_instance_valid(silhouette):
		silhouette.flash_amount = 1.0
		create_tween().tween_property(silhouette, "flash_amount", 0.0, 0.12)
	elif custom_visual != null and is_instance_valid(custom_visual):
		custom_visual.modulate = Color(1, 0.85, 0.85, 1)
		create_tween().tween_property(custom_visual, "modulate", Color(1, 1, 1, 1), 0.14)
	elif hit_flash_mat:
		hit_flash_mat.set_shader_parameter("flash_amount", 1.0)
		create_tween().tween_property(hit_flash_mat, "shader_parameter/flash_amount", 0.0, 0.12)
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
	# Matikan fisika dulu: mayat tidak boleh menahan langkah unit lain
	set_physics_process(false)
	collision_layer = 0
	collision_mask = 0
	target = null
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

# Hit-stop: dulu `duration * Engine.time_scale` (0.03 * 0.05 = 1.5 ms) dan
# time-scale dipulihkan lewat await DI NODE INI -> kalau hero mati di tengah
# await, Engine.time_scale bisa tertinggal 0.05 (game kelihatan freeze/black).
# Sekarang request ke autoload GameManager yang punya watchdog real-time.
func _hit_stop(duration: float):
	GameManager.request_hit_stop(duration)

# Skill QWER — delegate ke HeroSkills (port dari hero_skills/)
func cast_q(): _cast_skill("q")
func cast_w(): _cast_skill("w")
func cast_e(): _cast_skill("e")
func cast_r(): _cast_skill("r")

func _cast_skill(key: String):
	var skill_node = get_node_or_null("Skills/%s" % key.to_upper())
	if skill_node and skill_node.has_method("cast"):
		skill_node.cast(self, target)
