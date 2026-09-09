# MysticTab.gd — tab kategori (port ui_theme.tab). Pakai toggle_mode +
# ButtonGroup seperti Button biasa; status aktif = button_pressed.
extends Button
class_name MysticTab

@export var accent: Color = UiTheme.GOLD:
	set(v):
		accent = v
		queue_redraw()
@export var font_style: String = "body_semibold"
@export var font_size: int = 16

var _hover := false
var _last_text := "~~~"


func _init(p_text: String = "", p_accent: Color = UiTheme.GOLD,
		p_font_size: int = 16) -> void:
	text = p_text
	accent = p_accent
	font_size = p_font_size
	_last_text = "~~~" + p_text
	toggle_mode = true
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
	toggled.connect(_on_toggled)
	resized.connect(queue_redraw)


func _on_hover(v: bool) -> void:
	_hover = v
	queue_redraw()


func _on_toggled(_on: bool) -> void:
	queue_redraw()


func _process(_delta: float) -> void:
	if text != _last_text:
		_last_text = text
		queue_redraw()


func _draw() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		return
	var active := button_pressed and not disabled
	var hov := _hover and not disabled
	var tcol := accent
	if active:
		UiTheme.draw_vgrad(self, rect, Color8(46, 56, 92),
			Color8(26, 32, 58), 8.0)
		draw_style_box(UiTheme.border_style(accent, 2.0, 8.0), rect)
		draw_rect(Rect2(rect.position.x + 8, rect.end.y - 4,
			rect.size.x - 16, 3), accent)
	else:
		var top := Color8(34, 39, 62) if hov else Color8(22, 26, 44)
		var bot := Color8(20, 24, 42) if hov else Color8(15, 18, 32)
		UiTheme.draw_vgrad(self, rect, top, bot, 8.0)
		draw_style_box(UiTheme.border_style(
			Color8(120, 130, 160) if hov else Color8(72, 80, 106), 1.0,
			8.0), rect)
		tcol = UiTheme.TEXT_BODY if hov else UiTheme.TEXT_DIM
	var f := UiTheme.font(font_style)
	var shown := UiTheme.letter(text)
	var bp := UiTheme.baseline_center(f, shown, rect.get_center(),
		font_size)
	draw_string(f, bp, shown, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size,
		tcol)
