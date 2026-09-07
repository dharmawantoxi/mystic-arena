# Minion.gd — Port dari minions/ + _entity.Minion (goblin/orc/troll/undead/dark_rider)
# Visual baseline: UnitSilhouette pygame (telinga goblin, taring orc, ...).
# Upgrade satu-satu lewat RendererRegistry.MINION[minion_type].
#
# Update sesi ini: stat dibaca GameManager.minion_type_data() (data/economy.json),
# kena StatusEffects (slow/burn/stun dari menara), memakai CombatSystem untuk
# damage, dan ikut menyerang nexus musuh (sebelumnya berhenti di base lawan).
extends CharacterBody2D

const UnitSilhouetteScript = preload("res://scripts/render/UnitSilhouette.gd")
const RendererRegistry = preload("res://scripts/render/RendererRegistry.gd")
const StatusEffectsScript = preload("res://scripts/systems/StatusEffects.gd")
const TowerBulletScript = preload("res://scenes/tower/TowerBullet.gd")
const FPS := 60.0

@export var minion_type: String = "goblin"
@export var team: String = "blue"
## Jalur asal wave, dipakai AIPlayer untuk menghitung ancaman per lane.
@export var lane: String = "mid"
## Skala HP/damage untuk wave tinggi (paritas minion_scale NEXUS_LEVELS)
@export var stat_scale: float = 1.0

var display_name: String = "Goblin"
var max_hp: float = 45.0
var hp: float = 45.0
var damage: float = 5.0
var move_speed: float = 90.0
var attack_range: float = 25.0
var attack_cooldown: float = 0.75
var gold_reward: int = 8
var radius: float = 9.0
var armor: float = 0.0
var magic_resist: float = 0.0
var dmg_school: String = "physical"

var target: Node2D = null
var attack_timer: float = 0.0
var is_dead: bool = false
var facing: int = 1
var anim_phase: float = 0.0
var status = null

@onready var visual: Node2D = $Visual
@onready var body: Polygon2D = $Visual/Body
@onready var hp_fill: Polygon2D = $UI/HPFill

const AGGRO_RADIUS := 260.0


func _ready():
	apply_minion_data()
	status = StatusEffectsScript.new(self)
	build_visual()
	update_ui()
	# Teriakan spawn khusus goblin (paritas Minion.__init__ _entity.py:5495-5496,
	# volume_mult 0.7, throttle 200 ms). Jenis minion lain lahir tanpa suara —
	# suara serangan mereka baru berbunyi saat memukul (lihat try_attack).
	if minion_type == "goblin":
		AudioManager.play_sfx("goblin_spawn", 0.7)
	# Paritas Hero: layer per tim (blue=2, red=4) supaya barisan saling dorong
	collision_layer = 2 if team == "blue" else 4
	collision_mask = 4 if team == "blue" else 2


func apply_minion_data():
	var s: Dictionary = GameManager.minion_type_data(minion_type)
	if s.is_empty():
		push_warning("[Minion] tipe tidak dikenal: %s" % minion_type)
		return
	display_name = s.get("name", minion_type)
	max_hp = float(s.get("hp", 45)) * stat_scale
	hp = max_hp
	damage = float(s.get("damage", 5)) * stat_scale
	move_speed = float(s.get("speed", 1.5)) * FPS # pygame speed -> px/s (sama dgn Hero)
	attack_range = float(s.get("range", 25)) + 8.0
	attack_cooldown = float(s.get("attack_cooldown", 45)) / FPS
	gold_reward = int(s.get("gold_reward", 8))
	radius = float(s.get("radius", 9))
	armor = float(s.get("armor", 0))
	magic_resist = float(s.get("magic_resist", 0))
	dmg_school = "physical"


## Port blok enemy scaling _core.py:1792-1796 (hanya minion merah, Hard mode):
## max_hp & damage dikali lalu dipotong int persis pygame, speed dikali
## pengali speed (base_speed pygame = move_speed kita, sudah tanpa status).
## Dipanggil Main._on_wave_started SETELAH add_child (stat wave via stat_scale
## sudah diterapkan _ready -> apply_minion_data).
func apply_enemy_scaling(hp_mult: float, dmg_mult: float, speed_mult: float) -> void:
	max_hp = float(int(max_hp * hp_mult))
	hp = max_hp
	damage = float(int(damage * dmg_mult))
	move_speed = move_speed * speed_mult
	update_ui()


# Bangun siluet minion dari radius + warna palette (0 file PNG dibutuhkan)
func build_visual():
	var r := radius
	if body:
		body.visible = false
	var shadow := get_node_or_null(^"Shadow")
	if shadow:
		shadow.visible = false
	hp_fill.color = Color(0.42, 0.9, 0.42, 1) if team == "blue" else Color(0.95, 0.35, 0.3, 1)
	var col := get_node_or_null(^"CollisionShape2D") as CollisionShape2D
	if col != null and col.shape is CircleShape2D:
		(col.shape as CircleShape2D).radius = maxf(6.0, r)
	z_as_relative = false
	var packed: PackedScene = RendererRegistry.minion_scene(minion_type)
	if packed != null:
		custom_visual = packed.instantiate()
		custom_visual.name = "CustomVisual"
		visual.add_child(custom_visual)
		return
	var d: Dictionary = GameManager.minion_type_data(minion_type)
	var fill := _parse_color(d.get("color", "#c8c8c8"), Color("#c8c8c8"))
	silhouette = UnitSilhouetteScript.new()
	silhouette.name = "Silhouette"
	visual.add_child(silhouette)
	var ranged := attack_range >= 80.0
	silhouette.configure(
		UnitSilhouetteScript.Kind.MINION, minion_type, team, fill, fill.darkened(0.35),
		r, display_name, dmg_school, ranged)


var silhouette = null
var custom_visual = null


func _physics_process(delta):
	if is_dead:
		return
	if status != null:
		status.tick(delta)
	attack_timer = maxf(0.0, attack_timer - delta)
	anim_phase += delta * 8.0
	if target == null or not is_instance_valid(target) or bool(target.get("is_dead")):
		target = CombatSystem.nearest_enemy(self, AGGRO_RADIUS)

	var is_moving := false
	var eff_speed := _eff_speed()
	if target != null:
		var dist := global_position.distance_to(target.global_position)
		facing = 1 if target.global_position.x >= global_position.x else -1
		visual.scale.x = facing
		if dist <= attack_range:
			velocity = Vector2.ZERO
			try_attack()
		else:
			is_moving = _move_to(target.global_position, eff_speed)
	else:
		# Tidak ada musuh dalam aggro -> jalan ke base lawan (nexus masuk group
		# "nexus", jadi begitu dekat dia otomatis jadi target dan dihajar)
		var dest := enemy_base()
		if global_position.distance_to(dest) > 24.0:
			is_moving = _move_to(dest, eff_speed)
		else:
			velocity = Vector2.ZERO
	z_index = int(global_position.y)
	_drive_visual(is_moving)


func _move_to(dest: Vector2, speed: float) -> bool:
	if speed <= 1.0:
		velocity = Vector2.ZERO
		return false
	var to := dest - global_position
	if to.length() <= 6.0:
		velocity = Vector2.ZERO
		return false
	velocity = to.normalized() * speed
	facing = 1 if velocity.x >= 0.0 else -1
	visual.scale.x = facing
	move_and_slide()
	return true


func _eff_speed() -> float:
	return move_speed * (status.move_speed_mult() if status != null else 1.0)


func _eff_attack_cd() -> float:
	return status.attack_cd(attack_cooldown) if status != null else attack_cooldown


func _drive_visual(is_moving: bool) -> void:
	var ap := 0.0
	if attack_timer > 0.0:
		ap = 1.0 - attack_timer / maxf(0.001, _eff_attack_cd())
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
	var c := Color(s)
	if c.a == 0.0 and s != "#00000000":
		return fallback
	return c


func enemy_base() -> Vector2:
	var am = get_tree().get_first_node_in_group("arena_map")
	if am != null and am.has_method("get_enemy_base"):
		return am.get_enemy_base(team)
	return Vector2(1180, 100) if team == "blue" else Vector2(100, 620)


func try_attack():
	if attack_timer > 0.0 or target == null:
		return
	attack_timer = _eff_attack_cd()
	# Pukulan SEMUA jenis minion memakai satu suara global (paritas
	# Minion.update _entity.py:5585-5591 — combat_audio.MINION_HIT, volume
	# dasar 0.50, jeda 140 ms). Dulu hanya goblin yang berbunyi.
	AudioManager.play_combat("minion_hit")
	var dmg := CombatSystem.calc_damage(self, target, damage, dmg_school)
	if attack_range >= 80.0:
		# Undead = ranged: proyektil (bisa ditangkis Wind Wall)
		var b = TowerBulletScript.new()
		b.setup(target, dmg, team, "normal", {}, 420.0,
			Color(0.85, 0.85, 0.95), self, dmg_school)
		b.global_position = global_position + Vector2(0, -6)
		GameManager.attach_fx(b)
	else:
		CombatSystem.apply_damage(target, dmg, team, "normal", self, dmg_school)


func take_damage(amount: float, from_team: String = "", dmg_type: String = "normal",
		source = null, school: String = ""):
	if is_dead:
		return
	var before := hp
	CombatSystem.apply_damage(self, amount, from_team, dmg_type, source, school)
	if hp < before:
		_flash()
	update_ui()
	if hp <= 0.0:
		die(from_team)


func _flash() -> void:
	if silhouette != null and is_instance_valid(silhouette):
		silhouette.flash_amount = 1.0
		create_tween().tween_property(silhouette, "flash_amount", 0.0, 0.1)
	elif body:
		body.modulate = Color(1.7, 1.7, 1.7, 1)
		create_tween().tween_property(body, "modulate", Color(1, 1, 1, 1), 0.1)


func heal(amount: float) -> void:
	if is_dead:
		return
	CombatSystem.heal_unit(self, amount)
	update_ui()


func die(killer_team: String = ""):
	is_dead = true
	set_physics_process(false)
	collision_layer = 0
	collision_mask = 0
	target = null
	# Suara kematian GLOBAL semua jenis minion (paritas Minion.take_damage
	# _entity.py:5854-5856, volume_mult 0.7, throttle 120 ms).
	AudioManager.play_sfx("minion_death", 0.7)
	if status != null:
		status.clear()
	GameManager.award_kill(killer_team, gold_reward)
	GameManager.minion_died.emit(self, killer_team)
	var tw := create_tween()
	tw.tween_property(self, "modulate:a", 0.0, 0.3)
	tw.parallel().tween_property(visual, "scale", Vector2(1.3, 0.25), 0.22)
	tw.tween_callback(queue_free)


func update_ui():
	if hp_fill:
		hp_fill.scale.x = clampf(hp / maxf(1.0, max_hp), 0.0, 1.0)
