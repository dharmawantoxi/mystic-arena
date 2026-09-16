# SylaraHitbox.gd — Area2D Hitbox modular untuk serangan & proyektil Sylara.
class_name SylaraHitbox
extends Area2D

@export var damage: float = 48.0
@export var damage_type: String = "PHYSICAL"
@export var team: String = "blue"
@export var is_critical: bool = false

var active_targets: Array = []


func _ready() -> void:
	monitoring = true
	monitorable = true
	area_entered.connect(_on_area_entered)


func _on_area_entered(area: Area2D) -> void:
	if area is SylaraHurtbox:
		area.receive_hit(self)
