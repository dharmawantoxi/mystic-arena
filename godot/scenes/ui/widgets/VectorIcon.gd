# VectorIcon.gd — satu ikon vektor ui_theme (26 ikon) sebagai Control.
#
# Dipakai di chip, tab, header section, dan tombol yang dibangun dari
# container biasa. Tombol kustom (PygameButton) memanggil
# UiTheme.draw_icon langsung di _draw()-nya.
extends Control
class_name VectorIcon

var icon_name: String = "play"
var icon_color: Color = Color.WHITE
var icon_scale: float = 1.0


func _init(p_name: String = "play", p_color: Color = Color.WHITE,
		p_scale: float = 1.0) -> void:
	icon_name = p_name
	icon_color = p_color
	icon_scale = p_scale
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	custom_minimum_size = Vector2(24.0 * p_scale, 24.0 * p_scale)


func set_icon(p_name: String, p_color: Color = Color.WHITE,
		p_scale: float = -1.0) -> void:
	icon_name = p_name
	icon_color = p_color
	if p_scale > 0.0:
		icon_scale = p_scale
		custom_minimum_size = Vector2(24.0 * p_scale, 24.0 * p_scale)
	queue_redraw()


func _draw() -> void:
	UiTheme.draw_icon(self, icon_name, size.x * 0.5, size.y * 0.5,
		icon_color, icon_scale)
