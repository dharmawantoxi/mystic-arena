class_name WindWall
extends Area2D
## Wind Wall projectile blocker.
##
## The wall is a wide Area2D configured as a one-way collider for projectiles.
## It does not damage enemies; it just deletes any projectile that enters it.
##
## Configuration is via [method configure]; the scene default has reasonable
## values so the wall is usable even if configure() is not called.

## Team of the caster. Projectiles from the same team pass through; enemy
## projectiles are destroyed.
var _team: StringName = &"blue"
## Total lifetime in seconds (auto-cleanup timer set by configure()).
var _lifetime: float = 1.5
## Width of the wall in pixels (matches the rect in the scene).
@export var wall_width: float = 220.0
## Height of the wall in pixels.
@export var wall_height: float = 110.0


func configure(width: float, height: float, lifetime: float, team: StringName) -> void:
	wall_width = width
	wall_height = height
	_lifetime = lifetime
	_team = team
	# Resize the collision shape to match.
	var shape_node := get_node_or_null("CollisionShape2D")
	if shape_node and shape_node.shape is RectangleShape2D:
		(shape_node.shape as RectangleShape2D).size = Vector2(width, height)
	# Resize the visual rect.
	var visual := get_node_or_null("Visual")
	if visual is ColorRect:
		(visual as ColorRect).size = Vector2(width, height)
		(visual as ColorRect).position = Vector2(-width * 0.5, -height * 0.5)


func _ready() -> void:
	# Default cleanup if configure() is never called.
	if _lifetime > 0.0:
		var t := get_tree().create_timer(_lifetime + 0.05, false, false)
		t.timeout.connect(queue_free)
	# Set collision layers: wall is on layer 8, projectiles on layer 16.
	# We only want to detect projectiles, so mask = 16.
	collision_layer = 8
	collision_mask = 16
	# Connect the area_entered signal explicitly.
	area_entered.connect(_on_area_entered)


func _on_body_shape_entered(_body_rid, body, _body_shape_index, _local_shape_index) -> void:
	# We use Area2D, so this is the relevant callback for Area2D overlaps.
	pass


func _on_area_entered(area: Area2D) -> void:
	# The projectile registers itself as an Area2D. If it's an enemy
	# projectile, destroy it.
	if not is_instance_valid(area):
		return
	# Projectiles opt-in by having a `is_projectile` property.
	if area.get("is_projectile") != true:
		return
	var proj_team: StringName = area.get("team") if area.get("team") != null else &""
	if proj_team == _team:
		# Same team — pass through.
		return
	# Destroy the projectile.
	if area.has_method("destroy"):
		area.destroy()
	# A tiny puff of wind particles — visual confirmation.
	if Engine.has_singleton("VFXManager") and get_tree().has_node("/root/VFXManager"):
		VFXManager.spawn(&"kaizen_wind_puff", global_position, 0.0, 0.4)
