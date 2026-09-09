# MysticIcon.gd — ikon vektor (port ui_theme.draw_icon) sebagai Control.
extends Control
class_name MysticIcon

@export var icon_name: String = "star":
	set(v):
		icon_name = v
		queue_redraw()
@export var icon_color: Color = UiTheme.GOLD:
	set(v):
		icon_color = v
		queue_redraw()
@export var icon_scale: float = 1.0:
	set(v):
		icon_scale = v
		custom_minimum_size = Vector2(24, 24) * maxf(0.2, v)
		queue_redraw()


func _init(p_name: String = "star", p_color: Color = UiTheme.GOLD,
		p_scale: float = 1.0) -> void:
	icon_name = p_name
	icon_color = p_color
	icon_scale = p_scale
	custom_minimum_size = Vector2(24, 24) * maxf(0.2, p_scale)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _draw() -> void:
	UiTheme.draw_icon(self, icon_name, size * 0.5, icon_color, icon_scale)
