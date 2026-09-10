# PygameToggle.gd — sakelar ON/OFF (port ui_theme.toggle 1:1).
#
# Pil 60x26 + knob + label ON/OFF di sisi berlawanan knob. extends Button
# supaya sinyal pressed + keyboard-focus konsisten dengan widget lain.
extends Button
class_name PygameToggle

var is_on: bool = true


func _init(p_on: bool = true) -> void:
	is_on = p_on
	text = ""
	focus_mode = Control.FOCUS_NONE
	mouse_filter = Control.MOUSE_FILTER_STOP
	custom_minimum_size = Vector2(60, 26)
	var _empty := StyleBoxEmpty.new()
	add_theme_stylebox_override("normal", _empty)
	add_theme_stylebox_override("hover", _empty)
	add_theme_stylebox_override("pressed", _empty)
	add_theme_stylebox_override("disabled", _empty)
	add_theme_stylebox_override("focus", _empty)
	mouse_entered.connect(queue_redraw)
	mouse_exited.connect(queue_redraw)
	pressed.connect(_on_pressed_sfx)


func _on_pressed_sfx() -> void:
	AudioManager.play_sfx("ui_click", 0.5)


func set_on(p_on: bool) -> void:
	is_on = p_on
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _draw() -> void:
	var r := Rect2(Vector2.ZERO, size)
	var hover := is_hovered() and not disabled
	var top: Color
	var bot: Color
	var edge: Color
	if is_on:
		top = Color8(92, 214, 118) if hover else Color8(70, 190, 96)
		bot = Color8(46, 138, 70) if hover else Color8(34, 116, 58)
		edge = Color8(160, 255, 180) if hover else Color8(120, 235, 145)
	else:
		top = Color8(92, 96, 118) if hover else Color8(74, 78, 100)
		bot = Color8(56, 60, 80) if hover else Color8(44, 48, 68)
		edge = Color8(150, 156, 180) if hover else Color8(120, 126, 150)
	UiTheme.draw_vgrad(self, r, top, bot, r.size.y * 0.5)
	UiTheme.draw_rr_outline(self, r, edge, r.size.y * 0.5, 2.0)
	# Knob.
	var knob := 18.0
	var kx := r.end.x - knob - 6.0 if is_on else r.position.x + 6.0
	var ky := r.get_center().y
	draw_circle(Vector2(kx + 1, ky + 2), knob * 0.5, Color(0.05, 0.06, 0.09))
	draw_circle(Vector2(kx, ky), knob * 0.5, Color(0.96, 0.97, 1.0))
	draw_arc(Vector2(kx, ky), knob * 0.5, 0, TAU, 24, edge, 1.0)
	# Label di sisi berlawanan knob.
	var font := UiTheme.body_bold()
	var lab := "ON" if is_on else "OFF"
	var lx := r.position.x + r.size.x * 0.5 - 8.0 if is_on \
		else r.position.x + r.size.x * 0.5 + 8.0
	UiTheme.draw_text_centered(self, font, lab, 15,
		Color(0.82, 1.0, 0.86) if is_on else UiTheme.TEXT_BODY,
		Vector2(lx, ky), false)
