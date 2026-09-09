# MysticToggle.gd — toggle pill ON/OFF (port ui_theme.toggle).
extends Button
class_name MysticToggle

signal toggled_on(is_on: bool)

@export var is_on: bool = true:
	set(v):
		is_on = v
		queue_redraw()
@export var font_style: String = "body_bold"
@export var font_size: int = 12

var _hover := false


func _init(p_on: bool = true) -> void:
	is_on = p_on
	text = "ON" if p_on else "OFF"
	focus_mode = Control.FOCUS_NONE
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var empty := StyleBoxEmpty.new()
	add_theme_stylebox_override("normal", empty)
	add_theme_stylebox_override("hover", empty)
	add_theme_stylebox_override("pressed", empty)
	add_theme_stylebox_override("disabled", empty)
	add_theme_stylebox_override("focus", empty)
	var invis := Color(0, 0, 0, 0)
	add_theme_color_override("font_color", invis)
	add_theme_color_override("font_hover_color", invis)
	add_theme_color_override("font_pressed_color", invis)
	add_theme_color_override("font_disabled_color", invis)
	add_theme_color_override("font_shadow_color", invis)
	add_theme_color_override("font_outline_color", invis)
	mouse_entered.connect(_on_hover.bind(true))
	mouse_exited.connect(_on_hover.bind(false))
	pressed.connect(_flip)
	resized.connect(queue_redraw)


func _flip() -> void:
	is_on = not is_on
	text = "ON" if is_on else "OFF"
	toggled_on.emit(is_on)
	queue_redraw()


func set_on(v: bool, silent: bool = true) -> void:
	is_on = v
	text = "ON" if v else "OFF"
	if not silent:
		toggled_on.emit(v)
	queue_redraw()


func _on_hover(v: bool) -> void:
	_hover = v
	queue_redraw()


func _draw() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		return
	var top: Color
	var bot: Color
	var edge: Color
	if is_on:
		top = Color8(92, 214, 118) if _hover else Color8(70, 190, 96)
		bot = Color8(46, 138, 70) if _hover else Color8(34, 116, 58)
		edge = Color8(160, 255, 180) if _hover else Color8(120, 235, 145)
	else:
		top = Color8(92, 96, 118) if _hover else Color8(74, 78, 100)
		bot = Color8(56, 60, 80) if _hover else Color8(44, 48, 68)
		edge = Color8(150, 156, 180) if _hover else Color8(120, 126, 150)
	UiTheme.draw_vgrad(self, rect, top, bot, rect.size.y * 0.5)
	draw_style_box(UiTheme.border_style(edge, 2.0, rect.size.y * 0.5),
		rect)
	var knob := 18.0
	var kx := rect.end.x - knob - 6.0 if is_on else rect.position.x + 6.0
	var ky := rect.get_center().y
	var kc := Vector2(kx, ky)
	draw_circle(kc + Vector2(1, 2), knob * 0.5, Color8(12, 14, 24))
	draw_circle(kc, knob * 0.5, Color8(245, 248, 255))
	UiTheme.draw_ring(self, kc, knob * 0.5, edge, 1.0)
	var lab := "ON" if is_on else "OFF"
	var lx := rect.position.x + rect.size.x * 0.5 + (-8.0 if is_on else 8.0)
	var f := UiTheme.font(font_style)
	var bp := UiTheme.baseline_center(f, lab, Vector2(lx, ky), font_size)
	draw_string(f, bp, lab, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size,
		Color8(210, 255, 220) if is_on else UiTheme.TEXT_BODY)
