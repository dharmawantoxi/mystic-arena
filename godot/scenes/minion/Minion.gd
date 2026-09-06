# Minion.gd — Port dari minions/ + _entity.Minion (goblin/orc/troll/undead/dark_rider)
# Visual baseline: UnitSilhouette pygame (telinga goblin, taring orc, ...).
# Upgrade satu-satu lewat RendererRegistry.MINION[minion_type].
extends CharacterBody2D

@export var minion_type: String = "goblin"
@export var team: String = "blue"

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

const UnitSilhouetteScript = preload("res://scripts/render/UnitSilhouette.gd")
const RendererRegistry = preload("res://scripts/render/RendererRegistry.gd")
var silhouette = null
var custom_visual = null

@onready var visual: Node2D = $Visual
@onready var body: Polygon2D = $Visual/Body
@onready var hp_fill: Polygon2D = $UI/HPFill

const AGGRO_RADIUS := 260.0

func _ready():
	apply_minion_data()
	build_visual()
	update_ui()
	# Paritas Hero: layer per tim (blue=2, red=4) supaya barisan saling dorong
	collision_layer = 2 if team == "blue" else 4
	collision_mask = 4 if team == "blue" else 2

func apply_minion_data():
	var s: Dictionary = GameManager.MINION_TYPES.get(minion_type, {})
	if s.is_empty():
		push_warning("[Minion] tipe tidak dikenal: %s" % minion_type)
		return
	display_name = s.get("name", minion_type)
	max_hp = float(s.get("hp", 45))
	hp = max_hp
	damage = float(s.get("damage", 5))
	move_speed = float(s.get("speed", 1.5)) * 60.0 # pygame speed -> px/s (sama dgn Hero)
	attack_range = float(s.get("range", 25)) + 8.0
	attack_cooldown = float(s.get("attack_cooldown", 45)) / 60.0
	gold_reward = int(s.get("gold_reward", 8))
	radius = float(s.get("radius", 9))
	armor = float(s.get("armor", 0))
	magic_resist = float(s.get("magic_resist", 0))
	dmg_school = "physical"

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
	var d: Dictionary = GameManager.MINION_TYPES.get(minion_type, {})
	var fill := Color(d.get("color", "#c8c8c8"))
	silhouette = UnitSilhouetteScript.new()
	silhouette.name = "Silhouette"
	visual.add_child(silhouette)
	var ranged := attack_range >= 80.0
	silhouette.configure(
		UnitSilhouetteScript.Kind.MINION, minion_type, team, fill, fill.darkened(0.35),
		r, display_name, dmg_school, ranged)

func _physics_process(delta):
	if is_dead:
		return
	attack_timer = maxf(0.0, attack_timer - delta)
	anim_phase += delta * 8.0
	if target == null or not is_instance_valid(target) or bool(target.get("is_dead")):
		target = find_nearest_enemy()

	var is_moving := false
	if target != null:
		var dist := global_position.distance_to(target.global_position)
		facing = 1 if target.global_position.x >= global_position.x else -1
		visual.scale.x = facing
		if dist <= attack_range:
			velocity = Vector2.ZERO
			try_attack()
		else:
			velocity = (target.global_position - global_position).normalized() * move_speed
			is_moving = true
			move_and_slide()
	else:
		# Tidak ada musuh dalam aggro -> jalan ke base lawan
		var dest := enemy_base()
		if global_position.distance_to(dest) > 24.0:
			velocity = (dest - global_position).normalized() * move_speed
			facing = 1 if velocity.x >= 0.0 else -1
			visual.scale.x = facing
			is_moving = true
			move_and_slide()
		else:
			velocity = Vector2.ZERO
			# TODO Fase 4: ratakan nexus musuh (port _entity.Nexus.take_damage)
	z_index = int(global_position.y)
	_drive_visual(is_moving)

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


func find_nearest_enemy() -> Node2D:
	var best: Node2D = null
	var best_d := AGGRO_RADIUS
	for group in ["heroes", "bosses", "minions", "towers"]:
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

func enemy_base() -> Vector2:
	var am = get_tree().get_first_node_in_group("arena_map")
	if am != null and am.has_method("get_enemy_base"):
		return am.get_enemy_base(team)
	return Vector2(1180, 100) if team == "blue" else Vector2(100, 620)

func try_attack():
	if attack_timer > 0.0 or target == null:
		return
	attack_timer = attack_cooldown
	var dmg := CombatSystem.calc_damage(self, target, damage, dmg_school)
	target.take_damage(dmg, team, "normal", self, dmg_school)

func take_damage(amount: float, from_team: String = "", dmg_type: String = "normal",
		source = null, school: String = ""):
	if is_dead:
		return
	var mitigated := CombatSystem.mitigate_damage(self, amount, school if school != "" else dmg_school)
	hp -= mitigated
	if silhouette != null and is_instance_valid(silhouette):
		silhouette.flash_amount = 1.0
		create_tween().tween_property(silhouette, "flash_amount", 0.0, 0.1)
	elif body:
		body.modulate = Color(1.7, 1.7, 1.7, 1)
		create_tween().tween_property(body, "modulate", Color(1, 1, 1, 1), 0.1)
	if mitigated >= 1.0:
		var num = preload("res://scenes/fx/DamageNumber.tscn").instantiate()
		num.setup(str(int(mitigated)), mitigated > max_hp * 0.35)
		num.global_position = global_position + Vector2(randf_range(-8, 8), -34)
		var host := get_tree().current_scene
		if host != null:
			host.add_child(num)
	update_ui()
	if hp <= 0.0:
		die(from_team)

func die(killer_team: String = ""):
	is_dead = true
	set_physics_process(false)
	collision_layer = 0
	collision_mask = 0
	target = null
	GameManager.award_kill(killer_team, gold_reward)
	GameManager.minion_died.emit(self, killer_team)
	var tw := create_tween()
	tw.tween_property(self, "modulate:a", 0.0, 0.3)
	tw.parallel().tween_property(visual, "scale", Vector2(1.3, 0.25), 0.22)
	tw.tween_callback(queue_free)

func update_ui():
	if hp_fill:
		hp_fill.scale.x = clampf(hp / maxf(1.0, max_hp), 0.0, 1.0)
