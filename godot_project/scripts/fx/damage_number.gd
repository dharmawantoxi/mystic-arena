class_name DamageNumber
extends Label
## Floating damage number that drifts upward and fades.
##
## Driven by [ParticlePool]. Each instance shows one damage value, scales
## up briefly (pop-in), then drifts up + fades out over its lifetime.

## Lifetime in seconds. The pool will free us after this.
@export var lifetime: float = 0.7
## Drift speed (px/s) in world space.
@export var drift: float = 60.0

## Default font size (will scale up to 1.5x on crit).
@export var base_size: int = 18

## Slight horizontal jitter for visual variety.
var _jitter_x: float = 0.0


func _ready() -> void:
	# Hide until we receive a value.
	visible = false
	# Default text style.
	add_theme_color_override("font_outline_color", Color(0, 0, 0, 1))
	add_theme_constant_override("outline_size", 4)
	# Set font size.
	add_theme_font_size_override("font_size", base_size)


func set_value(value: int, crit: bool = false, kind: String = "normal") -> void:
	visible = true
	text = str(value)
	# Colour by damage kind.
	var col := Color(1, 1, 1)
	match kind:
		"skill":
			col = Color(0.65, 0.92, 1.0)
		"ultimate":
			col = Color(1.0, 0.85, 0.4)
		"crit":
			col = Color(1.0, 0.9, 0.4)
		_:
			col = Color(1, 1, 1)
	add_theme_color_override("font_color", col)
	# Scale based on crit.
	var scale := 1.0 + (0.5 if crit else 0.0)
	scale = Vector2(scale, scale)
	# Slight horizontal jitter.
	_jitter_x = randf_range(-8.0, 8.0)
	# Animate: pop up + drift + fade.
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(self, "scale", scale, 0.08).from(Vector2(0.3, 0.3))
	tween.tween_property(self, "position:y", -drift * lifetime, lifetime)
	tween.tween_property(self, "position:x", _jitter_x, lifetime)
	tween.chain().tween_property(self, "modulate:a", 0.0, lifetime * 0.5)
	# Self-release.
	tween.chain().tween_callback(_release_self)


func _release_self() -> void:
	# Reset state for reuse.
	scale = Vector2.ONE
	modulate = Color(1, 1, 1, 1)
	visible = false
	# Hand ourselves back to the pool.
	var pool := get_tree().get_root().get_node_or_null("ParticlePool")
	if pool and pool.has_method("release"):
		pool.release(self)
	else:
		queue_free()


func reset() -> void:
	# Called by the pool when taking a recycled instance.
	scale = Vector2.ONE
	modulate = Color(1, 1, 1, 1)
	visible = false
