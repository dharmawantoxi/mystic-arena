# DamageNumber.gd — Port dari _render.FloatingText
extends Label

var velocity := Vector2(0, -90)
var lifetime := 0.75
var is_crit := false

func _ready() -> void:
	add_to_group("floating_text")
	# Berbagi FIFO/cap dengan popup gold boss; visual lama tidak diubah.
	GameManager.world_popups.register_damage_number(self)


func setup(text: String, crit: bool):
	self.text = text
	is_crit = crit
	if crit:
		add_theme_font_size_override("font_size", 22)
		modulate = Color(1, 0.92, 0.25) # gold
		scale = Vector2(1.25, 1.25)
	else:
		add_theme_font_size_override("font_size", 16)
		modulate = Color(1,1,1)
	# shadow
	add_theme_color_override("font_shadow_color", Color(0,0,0,0.8))
	add_theme_constant_override("shadow_offset_x", 1)
	add_theme_constant_override("shadow_offset_y", 1)

func _process(delta):
	position += velocity * delta
	velocity.y *= 0.97
	velocity.x += randf_range(-5,5) * delta
	lifetime -= delta
	modulate.a = clamp(lifetime / 0.35, 0.0, 1.0)
	scale = scale.lerp(Vector2(0.95,0.95) if not is_crit else Vector2(1.15,1.15), delta*3)
	if lifetime <= 0:
		queue_free()
