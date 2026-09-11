# PygameToggle.gd — sakelar ON/OFF (port ui_theme.toggle 1:1).
#
# Pil 60x26 + knob + label ON/OFF di sisi berlawanan knob. extends Button
# supaya sinyal pressed + keyboard-focus konsisten dengan widget lain.
extends Button
class_name PygameToggle

var is_on: bool = true
var _hover: bool = false


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
	mouse_entered.connect(_set_hover.bind(true))
	mouse_exited.connect(_set_hover.bind(false))
	pressed.connect(_on_pressed_sfx)


func _set_hover(v: bool) -> void:
	_hover = v
	queue_redraw()


func _on_pressed_sfx() -> void:
	AudioManager.play_sfx("ui_click", 0.5)


func set_on(p_on: bool) -> void:
	is_on = p_on
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _draw() -> void:
	# Satu sumber dengan jalur immediate-mode ui_theme.toggle: warna ON/OFF,
	# knob 18px (bayangan + cincin), dan label di sisi berlawanan knob.
	UiTheme.draw_toggle_visual(self, Rect2(Vector2.ZERO, size), is_on,
		UiTheme.body_bold(), 15, _hover and not disabled)
