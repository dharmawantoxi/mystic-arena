# SylaraHurtbox.gd — Area2D Hurtbox modular untuk penerimaan damage Sylara.
class_name SylaraHurtbox
extends Area2D

signal hit_received(hitbox: Node, damage: float)

@export var is_invulnerable: bool = false
@export var team: String = "blue"

var owner_character: Node2D = null


func _ready() -> void:
	monitoring = true
	monitorable = true


func receive_hit(hitbox: Node) -> bool:
	if is_invulnerable:
		return false
	if "team" in hitbox and hitbox.team == team:
		return false

	var dmg: float = hitbox.damage if "damage" in hitbox else 10.0
	hit_received.emit(hitbox, dmg)

	if owner_character != null and owner_character.has_method("take_damage"):
		owner_character.take_damage(dmg, hitbox.get("team") if "team" in hitbox else "red")
	return true
