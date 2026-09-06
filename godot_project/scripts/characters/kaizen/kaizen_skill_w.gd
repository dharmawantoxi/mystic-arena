class_name KaizenSkillW
extends SkillBase
## Kaizen's W — Wind Wall.
##
## Spawns a wall of compressed air in front of the character that
## blocks enemy projectiles for [member wall_duration] seconds. The wall
## does not damage enemies; it is purely defensive.
##
## Implementation: spawn a [WindWall] scene (a wide Area2D) at the
## character's facing. Wind wall is one-shot — not pooled — because at
## most one can exist per character.

@export var wall_scene: PackedScene
@export var wall_lifetime: float = 1.5
@export var wall_offset: float = 80.0        ## Pixels in front of the hero.
@export var wall_width: float = 220.0
@export var wall_height: float = 110.0

## Active WindWall instance (null if none).
var _active_wall: Node = null


func try_cast(cast_pos: Vector2 = Vector2.ZERO) -> bool:
	if not super.try_cast(cast_pos):
		return false
	# W is instant — no cast window.
	_spawn_wall()
	# Active window is just the lifetime, but it doesn't lock the character.
	active_timer = wall_lifetime
	is_active = true
	return true


func _spawn_wall() -> void:
	if wall_scene == null:
		push_warning("KaizenSkillW: wall_scene not assigned")
		return
	var dir := Vector2(owner_character.facing, 0)
	var pos: Vector2 = owner_character.global_position + dir * wall_offset
	# Free the previous wall if one still exists.
	if _active_wall != null and is_instance_valid(_active_wall):
		_active_wall.queue_free()
	_active_wall = wall_scene.instantiate()
	# Add to the world (not the character, so the wall doesn't move with us).
	get_tree().current_scene.add_child(_active_wall)
	_active_wall.global_position = pos
	# Orient and scale the wall along the facing direction.
	if _active_wall is Node2D:
		(_active_wall as Node2D).rotation = dir.angle()
	if _active_wall.has_method("configure"):
		_active_wall.call("configure", wall_width, wall_height, wall_lifetime, owner_character.team)
	# Clean up after the lifetime.
	var t := get_tree().create_timer(wall_lifetime + 0.05, false, false)
	t.timeout.connect(_cleanup_wall)


func _cleanup_wall() -> void:
	if _active_wall != null and is_instance_valid(_active_wall):
		_active_wall.queue_free()
	_active_wall = null
