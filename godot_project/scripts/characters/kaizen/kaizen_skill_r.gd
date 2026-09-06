class_name KaizenSkillR
extends SkillBase
## Kaizen's R — Tornado Ultimate.
##
## Massive AOE that hits everything in [member range] around the character.
## This is the showcase skill — primary effect is a tall, readable tornado
## shape; secondary sparks orbit; the screen flashes briefly.
##
## "Juice" comes from:
##   * 90 ms hit-stop on impact,
##   * strong camera shake (tier 3),
##   * brief additive screen-flash,
##   * the tornado shape staying on screen for ~1.5 s,
##   * damage popups cascading outward (handled by ParticlePool).

@export var range: float = 150.0
@export var damage_mult: float = 2.0
@export var pull_strength: float = 220.0     ## How hard it pulls enemies inward.
@export var pull_duration: float = 0.4
@export var tier: int = 3


func try_cast(cast_pos: Vector2 = Vector2.ZERO) -> bool:
	if cooldown_remaining > 0.0 or is_casting or is_active:
		return false
	cast_timer = 0.45  ## Long wind-up — the user has to commit to R.
	is_casting = true
	cast_started.emit(self)
	owner_character.stunned = true
	cooldown_remaining = cooldown_max
	cooldown_set.emit(self, cooldown_max)
	# Pre-cast: spawn the tornado visual NOW so it can grow during the cast.
	_spawn_tornado_visual()
	# Schedule the impact.
	var t := get_tree().create_timer(cast_timer, false, false)
	t.timeout.connect(_impact)
	return true


func _spawn_tornado_visual() -> void:
	var pos := owner_character.global_position
	VFXManager.spawn(&"kaizen_r_tornado", pos, 0.0, cast_timer + 1.0)


func _impact() -> void:
	is_casting = false
	owner_character.stunned = false
	var origin := owner_character.global_position
	var amount := int(owner_character.damage * damage_mult)
	# Pull enemies toward origin during the cast — they should already be
	# close when the impact lands.
	_pull_enemies(origin, pull_strength, pull_duration)
	# Damage everything in range.
	var enemies := _enemies_in_range(origin, range)
	for e in enemies:
		owner_character.deal_damage(e, amount)
		ParticlePool.spawn(e.global_position, amount, true, "ultimate")
	# Strong camera shake + hit-stop + flash.
	GameFeel.shake(tier)
	GameFeel.hit_stop(0.09)
	GameFeel.flash(Color(0.7, 0.9, 1.0, 0.18), 0.12)


func _pull_enemies(origin: Vector2, strength: float, duration: float) -> void:
	for c in get_tree().get_nodes_in_group("enemies"):
		if c is CharacterBody2D and is_instance_valid(c):
			var to_origin: Vector2 = origin - (c as Node2D).global_position
			var d := to_origin.length()
			if d < 0.001 or d > range * 1.5:
				continue
			var n := to_origin / d
			# Apply a brief velocity kick — their physics step will integrate.
			(c as CharacterBody2D).velocity = n * strength
			# Then ease them back to zero so they don't fly off.
			var tween := (c as CharacterBody2D).create_tween()
			tween.tween_property(c, "velocity", Vector2.ZERO, duration)


func _enemies_in_range(origin: Vector2, range: float) -> Array:
	var result: Array = []
	for c in get_tree().get_nodes_in_group("enemies"):
		if c is Node2D and is_instance_valid(c):
			var d := (c as Node2D).global_position.distance_to(origin)
			if d <= range:
				result.append(c)
	return result
