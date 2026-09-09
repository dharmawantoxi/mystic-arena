# MysticPill.gd — tombol aksi kecil (port ui_theme.pill).
# kind: gold | success | danger | locked | owned | neutral | violet | cyan.
extends Button
class_name MysticPill

@export var kind: String = "gold":
	set(v):
		kind = v
		queue_redraw()
@export var icon_name: String = "":
	set(v):
		icon_name = v
		queue_redraw()
@export var letter_gap: bool = true:
	set(v):
		letter_gap = v
		queue_redraw()
@export var font_style: String = "body_bold"
@export var font_size: int = 16

var _hover := false
var _pressed := false
var _last_text := "~~~"


func _init(p_text: String = "", p_kind: String = "gold",
		p_icon: String = "", p_font_size: int = 16,
		p_letter_gap: bool = true) -> void:
	text = p_text
	kind = p_kind
	icon_name = p_icon
	font_size = p_font_size
	letter_gap = p_letter_gap
	_last_text = "~~~" + p_text
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
	button_down.connect(_on_press.bind(true))
	button_up.connect(_on_press.bind(false))
	resized.connect(queue_redraw)


func _on_hover(v: bool) -> void:
	_hover = v
	queue_redraw()


func _on_press(v: bool) -> void:
	_pressed = v
	queue_redraw()


func _process(_delta: float) -> void:
	if text != _last_text:
		_last_text = text
		queue_redraw()


static func _bright(c: Color, amt: float) -> Color:
	return Color(minf(1.0, c.r + amt), minf(1.0, c.g + amt),
		minf(1.0, c.b + amt), c.a)


func _draw() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		return
	var enabled := not disabled
	var hov := _hover and enabled
	var cols: Array = UiTheme.pill_colors(kind)
	var top: Color = cols[0]
	var bot: Color = cols[1]
	var edge: Color = cols[2]
	var tcol: Color = cols[3]
	if hov:
		top = _bright(top, 0.07)
		bot = _bright(bot, 0.055)
	if _pressed and enabled:
		top = top.darkened(0.12)
		bot = bot.darkened(0.12)
	if hov:
		UiTheme.draw_glow(self, rect.get_center(),
			rect.size + Vector2(30, 24), edge, 66.0)
	UiTheme.draw_vgrad(self, rect, top, bot, 7.0)
	draw_style_box(UiTheme.border_style(edge, 2.0 if enabled else 1.0, 7.0),
		rect)
	var f := UiTheme.font(font_style)
	var shown := UiTheme.letter(text) if letter_gap else text
	var label_cx := rect.get_center().x
	if icon_name != "":
		UiTheme.draw_icon(self, icon_name,
			Vector2(rect.position.x + 22, rect.get_center().y),
			edge if enabled else UiTheme.TEXT_FAINT, 0.8)
		label_cx = rect.position.x + 22.0 + (rect.size.x - 22.0) * 0.5
	var bp := UiTheme.baseline_center(f, shown,
		Vector2(label_cx, rect.get_center().y), font_size)
	UiTheme.draw_text_shadow(self, f, shown, font_size,
		tcol if enabled else UiTheme.TEXT_FAINT, bp)
