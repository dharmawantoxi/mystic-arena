# Boss.gd — Port dari bosses/base_boss.py
# Visual sama seperti Hero.tscn tapi scale 1.4x + aura + boss bar
extends CharacterBody2D

@export var boss_type: String = "abaddon"
@export var team: String = "red"

# Stats (diisi dari BossDB)
var display_name: String = "Boss"
var max_hp: float = 30000.0
var hp: float = 30000.0
var damage: float = 120.0
var move_speed: float = 60.0
var attack_range: float = 65.0
var attack_cooldown: float = 0.7
var dmg_school: String = "physical"

var target: Node2D = null
var attack_timer: float = 0.0
var is_dead: bool = false
var anim_phase: float = 0.0

@onready var visual: Node2D = $Visual
@onready var sprite: AnimatedSprite2D = $Visual/AnimatedSprite2D
@onready var shadow: Polygon2D = $Shadow
@onready var aura: GPUParticles2D = $FX/Aura
@onready var hp_bar: ProgressBar = $UI/HPBar
@onready var name_label: Label = $UI/NameLabel

const AGGRO_RADIUS := 460.0

func _ready():
	var s: Dictionary = BossDB.get_boss(boss_type)
	if not s.is_empty():
		display_name = s.get("name", boss_type)
		max_hp = float(s.get("hp", 30000))
		hp = max_hp
		damage = float(s.get("damage", 120))
		move_speed = float(s.get("speed", 0.85)) * 60.0
		attack_range = float(s.get("range", 50)) + 15.0
		attack_cooldown = float(s.get("attack_cooldown", 43)) / 60.0
		dmg_school = "magic" if str(s.get("boss_class", "")) == "true" else "physical"
	add_to_group("bosses")
	# Boss scale lebih besar (menggantikan SCALE=1.32 di pygame)
	visual.scale = Vector2(1.4, 1.4)
	if shadow != null:
		shadow.scale = Vector2(1.9, 0.7)
	setup_visual(s)
	update_ui()
	collision_layer = 2 if team == "blue" else 4
	collision_mask = 4 if team == "blue" else 2

func setup_visual(s: Dictionary) -> void:
	# 1. Sprite sheet HD kalau sudah di-import (Fase 5 — import 200+ boss)
	var frames_path = "res://assets/bosses/%s/SpriteFrames.tres" % boss_type
	if ResourceLoader.exists(frames_path):
		sprite.sprite_frames = load(frames_path)
		if sprite.sprite_frames.has_animation("idle"):
			sprite.animation = &"idle"
			sprite.play("idle")
		return
	# 2. Fallback: kotak warna sewarna `color` bosses.json.
	#    Dulu TIDAK ada visual sama sekali di sini -> boss yang di-spawn
	#    `GameManager.spawn_boss()` benar-benar tak terlihat (bagian dari bug
	#    "layar hitam"), meski node-nya ada dan menghajar hero.
	var w := 88
	var h := 104
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	var col := Color(s.get("color", "#8c64dc"))
	var dark := col.darkened(0.45)
	var light := col.lightened(0.35)
	for y in h:
		for x in w:
			var c := col
			if y < h * 0.28:
				c = light # kepala / helm
			elif x < 6 or x > w - 7 or y > h - 8:
				c = dark # siluet + rim
			img.set_pixel(x, y, c)
	var frames := SpriteFrames.new()
	frames.add_animation("idle")
	frames.add_frame("idle", ImageTexture.create_from_image(img))
	sprite.sprite_frames = frames
	sprite.offset = Vector2(0, -h * 0.5)
	sprite.animation = &"idle"
	sprite.play("idle")
	if aura != null:
		aura.color = light

func _physics_process(delta):
	if is_dead:
		return
	attack_timer = maxf(0.0, attack_timer - delta)
	anim_phase += delta * 5.0
	if target == null or not is_instance_valid(target) or bool(target.get("is_dead")):
		target = find_nearest_enemy()
	if target == null:
		return
	var dist := global_position.distance_to(target.global_position)
	visual.scale.x = 1.4 * (1 if target.global_position.x >= global_position.x else -1)
	if dist <= attack_range:
		velocity = Vector2.ZERO
		try_attack()
	else:
		velocity = (target.global_position - global_position).normalized() * move_speed
		move_and_slide()

func find_nearest_enemy() -> Node2D:
	var best: Node2D = null
	var best_d := AGGRO_RADIUS
	for group in ["heroes", "minions", "bosses", "towers"]:
		for n in get_tree().get_nodes_in_group(group):
			if n == self or not is_instance_valid(n) or not (n is Node2D):
				continue
			if not n.has_method("take_damage"):
				continue
			if n.get("team") == team:
				continue
			if bool(n.get("is_dead")):
				continue
			var d := global_position.distance_to((n as Node2D).global_position)
			if d < best_d:
				best_d = d
				best = n as Node2D
	return best

func try_attack():
	if attack_timer > 0.0 or target == null:
		return
	attack_timer = attack_cooldown
	var dmg := CombatSystem.calc_damage(self, target, damage, dmg_school)
	target.take_damage(dmg, team, "normal", self, dmg_school)
	GameManager.request_hit_stop(0.045) # boss feel: sedikit lebih lama dari hero
	if aura != null:
		aura.restart()

func take_damage(amount: float, from_team: String = "", dmg_type: String = "normal",
		source = null, school: String = ""):
	if is_dead:
		return
	var mitigated := CombatSystem.mitigate_damage(self, amount, school if school != "" else dmg_school)
	hp -= mitigated
	# hit flash via shader sama seperti Hero
	var mat = sprite.material as ShaderMaterial
	if mat:
		mat.set_shader_parameter("flash_amount", 1.0)
		create_tween().tween_property(mat, "shader_parameter/flash_amount", 0.0, 0.12)
	else:
		sprite.modulate = Color(1.8, 1.8, 1.8, 1)
		create_tween().tween_property(sprite, "modulate", Color(1, 1, 1, 1), 0.12)
	_spawn_damage_number(mitigated)
	if hp <= 0:
		die()
	update_ui()

func _spawn_damage_number(amount: float) -> void:
	var num = preload("res://scenes/fx/DamageNumber.tscn").instantiate()
	num.setup(str(int(amount)), amount > max_hp * 0.06)
	num.global_position = global_position + Vector2(randf_range(-18, 18), -70)
	var host := get_tree().current_scene
	if host:
		host.add_child(num)
	else:
		add_child(num)

func die():
	is_dead = true
	set_physics_process(false)
	collision_layer = 0
	collision_mask = 0
	target = null
	if aura != null:
		aura.emitting = false
	# Death: scale squash + fade (GPU, bukan ellipse manual)
	var tw := create_tween()
	tw.parallel().tween_property(visual, "scale", Vector2(1.9, 0.18), 0.45).set_trans(Tween.TRANS_BACK)
	tw.parallel().tween_property(self, "modulate:a", 0.0, 0.5)
	tw.tween_callback(queue_free)
	# Drop hero unlock (SaveManager)
	SaveManager.unlock_hero(boss_type)
	print("[Boss] %s mati — tim %s menang wave" % [display_name, "blue" if team == "red" else "red"])

func update_ui():
	if hp_bar:
		hp_bar.max_value = 100.0
		hp_bar.value = clampf(hp / maxf(1.0, max_hp) * 100.0, 0.0, 100.0)
	if name_label:
		name_label.text = "%s  %d/%d" % [display_name, int(maxf(0.0, hp)), int(max_hp)]
