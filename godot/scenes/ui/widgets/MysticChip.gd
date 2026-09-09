# MysticChip.gd — chip statistik kecil (port ui_theme.stat_chip).
extends Control
class_name MysticChip

@export var icon_name: String = "star":
	set(v):
		icon_name = v
		queue_redraw()
@export var value_text: String = "":
	set(v):
		value_text = v
		queue_redraw()
@export var accent: Color = UiTheme.GOLD:
	set(v):
		accent = v
		queue_redraw()
@export var font_size: int = 16


func _init(p_icon: String = "star", p_value: String = "",
		p_accent: Color = UiTheme.GOLD, p_size: int = 16) -> void:
	icon_name = p_icon
	value_text = p_value
	accent = p_accent
	font_size = p_size
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(queue_redraw)


func set_value(v: String) -> void:
	value_text = v
	queue_redraw()


func _draw() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		return
	draw_rect(Rect2(rect.position.x + 2, rect.position.y + 2,
		rect.size.x, rect.size.y), Color(0, 0, 0, 0.35))
	UiTheme.draw_vgrad(self, rect, Color8(30, 37, 66),
		Color8(17, 21, 40), 8.0)
	draw_style_box(UiTheme.border_style(accent, 1.0, 8.0), rect)
	UiTheme.draw_icon(self, icon_name,
		Vector2(rect.position.x + 24, rect.get_center().y), accent, 0.8)
	var f := UiTheme.font("body_semibold")
	var bp := UiTheme.baseline_topleft(f,
		Vector2(rect.position.x + 40, rect.position.y + 5), font_size)
	UiTheme.draw_text_shadow(self, f, value_text, font_size,
		UiTheme.TEXT_WHITE, bp)
