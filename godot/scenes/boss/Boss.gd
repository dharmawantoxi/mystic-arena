# Boss.gd — Port dari bosses/base_boss.py
# Visual baseline: UnitSilhouette pygame (lebih besar + tanduk). Upgrade
# satu-satu lewat RendererRegistry.BOSS[boss_type].
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
var facing: int = 1
var radius: float = 22.0
var role: String = ""
var fill_color: Color = Color("#8c64dc")
var fill_dark: Color = Color("#4a3278")
var boss_class: String = "mini"

const UnitSilhouetteScript = preload("res://scripts/render/UnitSilhouette.gd")
const RendererRegistry = preload("res://scripts/render/RendererRegistry.gd")
const StatusEffectsScript = preload("res://scripts/systems/StatusEffects.gd")
const TowerBulletScript = preload("res://scenes/tower/TowerBullet.gd")
var silhouette = null
var custom_visual = null
## StatusEffects: boss kena slow/burn/stun menara (paritas TowerDebuffMixin di
## bosses/base_boss.py). Stun boss dipotong 55% supaya tidak di-stunlock.
var status = null
var armor: float = 0.0
var magic_resist: float = 0.0
var combat_timer: float = 0.0
var combat_reset: float = 5.0

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
		armor = float(s.get("armor", 0))
		magic_resist = float(s.get("magic_resist", 0.0))
	status = StatusEffectsScript.new(self)
	add_to_group("bosses")
	role = str(s.get("title", s.get("role", "")))
	boss_class = str(s.get("boss_class", "mini"))
	fill_color = _parse_color(s.get("color", "#8c64dc"), Color("#8c64dc"))
	fill_dark = fill_color.darkened(0.4)
	radius = 26.0 if boss_class == "true" else 22.0
	if shadow != null:
		shadow.visible = false
	setup_visual(s)
	update_ui()
	collision_layer = 2 if team == "blue" else 4
	collision_mask = 4 if team == "blue" else 2

func setup_visual(_s: Dictionary) -> void:
	if sprite:
		sprite.visible = false
	if aura != null:
		aura.emitting = false # partikel = upgrade, bukan baseline pygame
	visual.scale = Vector2.ONE # tscn lama 1.4x untuk kotak placeholder
	z_as_relative = false
	var packed: PackedScene = RendererRegistry.boss_scene(boss_type)
	if packed != null:
		custom_visual = packed.instantiate()
		custom_visual.name = "CustomVisual"
		visual.add_child(custom_visual)
		return
	silhouette = UnitSilhouetteScript.new()
	silhouette.name = "Silhouette"
	visual.add_child(silhouette)
	var ranged := attack_range >= 110.0
	silhouette.configure(
		UnitSilhouetteScript.Kind.BOSS, boss_type, team, fill_color, fill_dark,
		radius, role, dmg_school, ranged, boss_class)

func _physics_process(delta):
	if is_dead:
		return
	if status != null:
		status.tick(delta)
	attack_timer = maxf(0.0, attack_timer - delta)
	combat_timer = maxf(0.0, combat_timer - delta)
	anim_phase += delta * 5.0
	if target == null or not is_instance_valid(target) or bool(target.get("is_dead")):
		target = CombatSystem.nearest_enemy(self, AGGRO_RADIUS)
	if target == null:
		# Tidak ada musuh dalam aggro: dorong ke base lawan (nexus bisa dihancurkan)
		var dest := enemy_base()
		if global_position.distance_to(dest) > 40.0:
			var dir := (dest - global_position).normalized()
			velocity = dir * _eff_speed()
			facing = 1 if dir.x >= 0.0 else -1
			visual.scale.x = facing
			move_and_slide()
			z_index = int(global_position.y)
			_drive_visual(true)
		else:
			z_index = int(global_position.y)
			_drive_visual(false)
		return
	var dist := global_position.distance_to(target.global_position)
	facing = 1 if target.global_position.x >= global_position.x else -1
	visual.scale.x = facing
	var is_moving := false
	if dist <= attack_range:
		velocity = Vector2.ZERO
		try_attack()
	else:
		velocity = (target.global_position - global_position).normalized() * _eff_speed()
		is_moving = true
		move_and_slide()
	z_index = int(global_position.y)
	_drive_visual(is_moving)


func _eff_speed() -> float:
	return move_speed * (status.move_speed_mult() if status != null else 1.0)


func _eff_attack_cd() -> float:
	return status.attack_cd(attack_cooldown) if status != null else attack_cooldown


func enemy_base() -> Vector2:
	var am = get_tree().get_first_node_in_group("arena_map")
	if am != null and am.has_method("get_enemy_base"):
		return am.get_enemy_base(team)
	return Vector2(1180, 100) if team == "blue" else Vector2(100, 620)

func _drive_visual(is_moving: bool) -> void:
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
		custom_visual.drive(anim_phase, act, ap, facing, is_moving, "", 0.016)


static func _parse_color(v, fallback: Color) -> Color:
	if v is Color:
		return v
	var s := str(v).strip_edges()
	if s.is_empty():
		return fallback
	if not s.begins_with("#"):
		s = "#" + s
	return Color(s)


## Dicari lewat CombatSystem supaya nexus/menara ikut jadi target dan unit
## yang sedang Shadow Realm (invis) dilewati.
func find_nearest_enemy() -> Node2D:
	return CombatSystem.nearest_enemy(self, AGGRO_RADIUS)

func try_attack():
	if attack_timer > 0.0 or target == null:
		return
	attack_timer = _eff_attack_cd()
	var dmg := CombatSystem.calc_damage(self, target, damage, dmg_school)
	if attack_range >= 110.0:
		# Boss ranged (Morgath/Vex-like): proyektil sihir, tembus armor
		var b = TowerBulletScript.new()
		b.setup(target, dmg, team, "normal", {}, 380.0,
			fill_color.lightened(0.3), self, dmg_school)
		b.global_position = global_position + Vector2(0, -20)
		GameManager.attach_fx(b)
	else:
		CombatSystem.apply_damage(target, dmg, team, "normal", self, dmg_school)
	GameManager.request_hit_stop(0.045) # boss feel: sedikit lebih lama dari hero

func take_damage(amount: float, from_team: String = "", dmg_type: String = "normal",
		source = null, school: String = ""):
	if is_dead:
		return
	var before := hp
	# CombatSystem yang mengurangi HP + memunculkan damage number (urutan mitigasi
	# identik untuk hero/minion/boss/tower/nexus)
	CombatSystem.apply_damage(self, amount, from_team, dmg_type, source, school)
	if hp < before:
		_flash()
	if hp <= 0:
		die()
	update_ui()


func heal(amount: float) -> void:
	if is_dead:
		return
	CombatSystem.heal_unit(self, amount)
	update_ui()


func _flash() -> void:
	if silhouette != null and is_instance_valid(silhouette):
		silhouette.flash_amount = 1.0
		create_tween().tween_property(silhouette, "flash_amount", 0.0, 0.12)
	elif custom_visual != null and is_instance_valid(custom_visual):
		custom_visual.modulate = Color(1.8, 1.8, 1.8, 1)
		create_tween().tween_property(custom_visual, "modulate", Color(1, 1, 1, 1), 0.12)
	elif sprite:
		sprite.modulate = Color(1.8, 1.8, 1.8, 1)
		create_tween().tween_property(sprite, "modulate", Color(1, 1, 1, 1), 0.12)

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
