class_name EnemyDummy
extends Character
## Stationary target for combat testing.
##
## Stands in one place, takes damage, plays a flash on hit, and dies after
## taking [member max_hp] damage. Use a few of these in the demo scene to
## test Kaizen's skills.

## Color of the body (any value; the [code]_ready[/code] assigns it to
## the renderer).
@export var dummy_color: Color = Color(0.6, 0.2, 0.2, 1.0)
## HP value (overrides stats resource if not set).
@export var dummy_hp: int = 600

@onready var visual: Node2D = $Body


func _ready() -> void:
	add_to_group("enemies")
	super._ready()
	max_hp = dummy_hp
	hp = dummy_hp
	speed = 0.0
	if visual:
		_build_visual()


func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	# Dummies don't move, but we still want to integrate any knockback velocity.
	if velocity.length() > 1.0:
		move_and_slide()
		velocity = velocity.move_toward(Vector2.ZERO, 600.0 * delta)


func _build_visual() -> void:
	# Build a simple humanoid silhouette from polygons.
	for c in visual.get_children():
		c.queue_free()
	_make_poly(visual, "Torso", dummy_color, [-16, -8, 16, -8, 18, 20, -18, 20])
	_make_poly(visual, "Head", dummy_color.lightened(0.2),
		[-10, -22, 10, -22, 10, -8, -10, -8])
	_make_poly(visual, "LegL", dummy_color.darkened(0.2),
		[-10, 18, -2, 18, -3, 40, -10, 40])
	_make_poly(visual, "LegR", dummy_color.darkened(0.2),
		[2, 18, 10, 18, 10, 40, 3, 40])
	# Health bar above head (simple triangle).
	_make_poly(visual, "HPLight", Color(0.2, 0.8, 0.3),
		[-12, -30, 12, -30, 12, -27, -12, -27])


func _make_poly(parent: Node, name: String, color: Color, pts: PackedFloat32Array) -> void:
	var p := Polygon2D.new()
	p.name = name
	p.color = color
	var pv := PackedVector2Array()
	for i in range(0, pts.size(), 2):
		pv.append(Vector2(pts[i], pts[i + 1]))
	p.polygon = pv
	parent.add_child(p)


func take_damage(amount: int, source_team: StringName = "", source: Node = null) -> int:
	var actual := super.take_damage(amount, source_team, source)
	if actual > 0:
		_flash()
	return actual


func _flash() -> void:
	# A short white tint to confirm a hit.
	if visual == null:
		return
	var original_modulate := visual.modulate
	visual.modulate = Color(2.0, 2.0, 2.0, 1.0)
	var t := get_tree().create_timer(0.08, false, false)
	t.timeout.connect(func ():
		if is_instance_valid(visual):
			visual.modulate = original_modulate)


func _on_death() -> void:
	# Don't despawn immediately — let the death animation play.
	stunned = true
	# Fall apart: move the visual down + fade.
	if visual:
		var tween := create_tween()
		tween.set_parallel(true)
		tween.tween_property(visual, "position:y", 30.0, 0.6)
		tween.tween_property(visual, "modulate:a", 0.0, 0.6)
		tween.chain().tween_callback(queue_free)
	else:
		var t := get_tree().create_timer(0.6, false, false)
		t.timeout.connect(queue_free)


## Allow knockback from skills.
func apply_stun(duration: float) -> void:
	stunned = true
	var t := get_tree().create_timer(duration, false, false)
	t.timeout.connect(func (): stunned = false)
