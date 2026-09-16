# SylaraCombat.gd — combat & attack feel logic for Sylara (Godot 4.x).
#
# Tanggung jawab:
#   * Mengelola timing attack feel: ANTICIPATION → ATTACK → IMPACT → RECOVERY
#   * Sinkronisasi damage, critical proc, hit-stop, camera shake, dan audio
#   * Perhitungan basic attack (ranged arrow default / melee riposte bila dekat)
class_name SylaraCombat
extends Node

signal attack_hit(target: Node, damage: float, is_crit: bool)
signal damage_dealt(amount: float, dmg_type: String)

const MELEE_THRESHOLD := 65.0
const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

var character: CharacterBody2D = null
var base_damage := 48.0
var attack_range := 180.0
var crit_chance := 0.15
var crit_multiplier := 1.75


func setup(char_node: CharacterBody2D) -> void:
	character = char_node


func is_in_melee_range(target_pos: Vector2) -> bool:
	if character == null:
		return false
	return character.global_position.distance_to(target_pos) <= MELEE_THRESHOLD


func calculate_damage(is_crit: bool = false) -> float:
	var dmg := base_damage
	if is_crit:
		dmg *= crit_multiplier
	return dmg


func execute_attack_impact(target: Node2D, facing: int) -> void:
	if target == null or not is_instance_valid(target):
		return

	var is_crit := randf() < crit_chance
	var dmg := calculate_damage(is_crit)
	var is_melee := is_in_melee_range(target.global_position)

	# 1. Damage delivery
	if target.has_method("take_damage"):
		var team: String = character.get("team") if character != null and "team" in character else "blue"
		target.take_damage(dmg, team)
	elif "hp" in target:
		target.hp -= dmg

	# 2. Impact VFX via VFXManager (Pooled)
	var hit_pos := target.global_position + Vector2(0, -12)
	var impact_col := Pal.WIND_BRIGHT if is_crit else Pal.WIND
	var tier := 1 if is_crit or is_melee else 0
	VFXManager.impact(hit_pos, tier, impact_col)

	# 3. Combat Signals
	attack_hit.emit(target, dmg, is_crit)
	damage_dealt.emit(dmg, "PHYSICAL")
