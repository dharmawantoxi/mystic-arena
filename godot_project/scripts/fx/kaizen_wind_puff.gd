class_name KaizenWindPuff
extends VFXBase
## Small wind puff — used as a secondary particle (e.g. when a projectile
## hits a wind wall, or as a "whoosh" alongside a slash).
##
## A handful of small triangles that drift outward and fade.

@export var color: Color = Color(0.847, 0.949, 1.0)
@export var num_particles: int = 5
@export var speed: float = 60.0


func _animate() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(global_position)
	for i in range(num_particles):
		var p := Polygon2D.new()
		var size := rng.randf_range(2.0, 4.0)
		p.polygon = PackedVector2Array([
			Vector2(-size, -size),
			Vector2(size, -size),
			Vector2(0, size * 1.6),
		])
		p.color = color
		var ang := rng.randf() * TAU
		p.position = Vector2(cos(ang) * 6.0, sin(ang) * 6.0)
		var end := p.position + Vector2(cos(ang), sin(ang)) * speed * lifetime
		p.modulate = Color(1, 1, 1, 0.9)
		add_child(p)
		var tween := create_tween()
		tween.set_parallel(true)
		tween.tween_property(p, "position", end, lifetime)\
			.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
		tween.tween_property(p, "modulate:a", 0.0, lifetime)\
			.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
