# Sylara.gd — modular CharacterBody2D hero controller for Sylara (Godot 4.x).
#
# Mengimplementasikan arsitektur modular lengkap (MASTER PROMPT Section 2):
#   Sylara/
#   ├── Sylara.tscn
#   ├── Sylara.gd
#   ├── Visual / Skeleton (SylaraSkeleton.gd)
#   ├── Renderer (SylaraRenderer.gd)
#   ├── Animation (SylaraAnimator.gd + SylaraPose.gd)
#   ├── Combat (SylaraCombat.gd)
#   ├── Skills (SylaraSkillFX.gd)
#   ├── Hitbox (SylaraHitbox.gd)
#   ├── Hurtbox (SylaraHurtbox.gd)
#   ├── VFX (VFXManager pooled)
#   └── Audio (SylaraAudio.gd)
class_name Sylara
extends CharacterBody2D

signal health_changed(new_hp: float, max_hp: float)
signal character_died
signal skill_used(skill_key: String)

@export var max_hp: float = 620.0
@export var hp: float = 620.0
@export var move_speed: float = 140.0
@export var team: String = "blue"

@onready var visual: Node2D = $Visual
@onready var skeleton: SylaraSkeleton = $Visual/SylaraSkeleton
@onready var combat: SylaraCombat = $Combat
@onready var audio: SylaraAudio = $Audio
@onready var hurtbox: SylaraHurtbox = $Hurtbox

var facing: int = 1
var is_dead := false
var current_action := "idle"
var anim_phase := 0.0
var active_skill_key := ""


func _ready() -> void:
	add_to_group("heroes")
	if combat != null:
		combat.setup(self)
	if hurtbox != null:
		hurtbox.owner_character = self
		hurtbox.team = team

	if skeleton != null:
		skeleton.attack_impact.connect(_on_attack_impact)
		skeleton.skill_cast.connect(_on_skill_cast)


func _physics_process(delta: float) -> void:
	if is_dead:
		return

	anim_phase += delta * 6.0
	var is_moving := velocity.length_squared() > 10.0

	if velocity.x > 5.0:
		facing = 1
	elif velocity.x < -5.0:
		facing = -1

	visual.scale.x = float(facing)

	# Update locomotion
	if is_moving:
		current_action = "run" if velocity.length() > 100.0 else "walk"
		move_and_slide()
	elif current_action in ["walk", "run"]:
		current_action = "idle"

	if skeleton != null:
		skeleton.drive(anim_phase, current_action, 0.0, facing, is_moving,
			active_skill_key, delta)


func take_damage(amount: float, attacker_team: String = "") -> void:
	if is_dead:
		return
	if attacker_team != "" and attacker_team == team:
		return

	hp = maxf(0.0, hp - amount)
	health_changed.emit(hp, max_hp)

	if audio != null:
		audio.play_hit()

	if skeleton != null:
		skeleton.play("hurt", 0.3)

	if hp <= 0.0:
		die()


func die() -> void:
	if is_dead:
		return
	is_dead = true
	current_action = "death"
	velocity = Vector2.ZERO

	if audio != null:
		audio.play_death()

	if skeleton != null:
		skeleton.play("death", 1.5)

	character_died.emit()


func cast_skill(key: String) -> void:
	if is_dead:
		return
	active_skill_key = key
	skill_used.emit(key)
	if audio != null:
		audio.play_skill_cast(key)


func _on_attack_impact() -> void:
	if audio != null:
		audio.play_attack(false)


func _on_skill_cast(key: String) -> void:
	if audio != null:
		audio.play_skill_cast(key)
