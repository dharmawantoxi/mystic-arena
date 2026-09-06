class_name KaizenSkillE
extends SkillBase
## Kaizen's E — Sweep.
##
## AOE jump-attack in a wide cone in front of the character. The character
## briefly hops (animated by the animation tree) and lands with a
## ground-shaking sweep.
##
## Damage is applied at the END of the cast window so the impact lines up
## with the landing frame.

@export var range: float = 100.0
@export var half_arc_deg: float = 110.0
@export var damage_mult: float = 1.0
@export var knockback: float = 180.0       ## Pixels of push on hit enemies.


func try_cast(cast_pos: Vector2 = Vector2.ZERO) -> bool:
	if cooldown_remaining > 0.0 or is_casting or is_active:
		return false
	cast_timer = 0.32       ## "jump" window — animation only.
	is_casting = true
	cast_started.emit(self)
	owner_character.stunned = true
	cooldown_remaining = cooldown_max
	cooldown_set.emit(self, cooldown_max)
	# Schedule the landing impact.
	var t := get_tree().create_timer(cast_timer, false, false)
	t.timeout.connect(_impact)
	return true


func _impact() -> void:
	is_casting = false
	owner_character.stunned = false
	var origin := owner_character.global_position
	var dir := Vector2(owner_character.facing, 0)
	var amount := int(owner_character.damage * damage_mult)
	var enemies := _enemies_in_range(origin, range)
	for e in enemies:
		var to_e: Vector2 = e.global_position - origin
		var d := to_e.length()
		if d < 0.001:
			continue
		var n := to_e / d
		var half_arc := half_arc_deg * PI / 180.0
		if n.dot(dir) >= cos(half_arc):
			owner_character.deal_damage(e, amount)
			ParticlePool.spawn(e.global_position, amount, false, "skill")
			# Knockback: push along the direction of the enemy from origin.
			if e is CharacterBody2D:
				(e as CharacterBody2D).velocity = n * knockback
	VFXManager.spawn(&"kaizen_e_sweep", origin, dir.angle(), 0.45)
	GameFeel.shake(1)


func _enemies_in_range(origin: Vector2, range: float) -> Array:
	var result: Array = []
	for c in get_tree().get_nodes_in_group("enemies"):
		if c is Node2D and is_instance_valid(c):
			var d := (c as Node2D).global_position.distance_to(origin)
			if d <= range:
				result.append(c)
	return result
