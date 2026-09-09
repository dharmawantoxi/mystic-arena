# MysticTouchButton.gd — tombol sentuh melingkar (port TouchButton pygame).
extends Button
class_name MysticTouchButton

@export var accent: Color = UiTheme.GOLD:
	set(v):
		accent = v
		queue_redraw()
@export var glyph: String = "II":
	set(v):
		glyph = v
		queue_redraw()
@export var badge_count: int = 0:
	set(v):
		badge_count = v
		queue_redraw()
@export var font_size: int = 15

var _hover := false
var _pressed := false


func _init(p_glyph: String = "II", p_size: float = 46.0,
		p_accent: Color = UiTheme.GOLD) -> void:
	glyph = p_glyph
	accent = p_accent
	custom_minimum_size = Vector2(p_size, p_size)
	text = ""
	focus_mode = Control.FOCUS_NONE
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var empty := StyleBoxEmpty.new()
	add_theme_stylebox_override("normal", empty)
	add_theme_stylebox_override("hover", empty)
	add_theme_stylebox_override("pressed", empty)
	add_theme_stylebox_override("disabled", empty)
	add_theme_stylebox_override("focus", empty)
	mouse_entered.connect(_on_hover.bind(true))
	mouse_exited.connect(_on_hover.bind(false))
	button_down.connect(_on_press.bind(true))
	button_up.connect(_on_press.bind(false))
	resized.connect(queue_redraw)


func _on_hover(v: bool) -> void:
	_hover = v
	queue_redraw()


func _on_press(v: bool) -> void:
	_pressed = v
	queue_redraw()


func _draw() -> void:
	var c := size * 0.5
	var r := minf(size.x, size.y) * 0.5
	if r <= 0.0:
		return
	var base := Color8(16, 20, 36, 235)
	if _pressed:
		base = Color8(30, 34, 56, 235)
	elif _hover:
		base = Color8(26, 30, 52, 235)
	draw_circle(c + Vector2(0, 2), r, Color(0, 0, 0, 0.45))
	draw_circle(c, r, base)
	UiTheme.draw_ring(c, r - 1.0, accent, 2.5)
	if glyph == "II":
		var bw := r * 0.16
		var x1 := c.x - bw * 1.2
		var x2 := c.x + bw * 0.2
		draw_rect(Rect2(x1, c.y - r * 0.34, bw, r * 0.68), accent)
		draw_rect(Rect2(x2, c.y - r * 0.34, bw, r * 0.68), accent)
	else:
		var f := UiTheme.font("body_bold")
		var bp := UiTheme.baseline_center(f, glyph, c, font_size)
		draw_string(f, bp, glyph, HORIZONTAL_ALIGNMENT_LEFT, -1,
			font_size, accent)
	if badge_count > 0:
		var bc := Vector2(c.x + r * 0.62, c.y - r * 0.62)
		draw_circle(bc, 11.0, Color8(200, 40, 52))
		UiTheme.draw_ring(bc, 11.0, Color.WHITE, 2.0)
		var f2 := UiTheme.font("body_bold")
		var t := str(mini(badge_count, 99))
		var bp2 := UiTheme.baseline_center(f2, t, bc, 12)
		draw_string(f2, bp2, t, HORIZONTAL_ALIGNMENT_LEFT, -1, 12,
			Color.WHITE)
