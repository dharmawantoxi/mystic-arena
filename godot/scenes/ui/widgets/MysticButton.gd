# MysticButton.gd — tombol menu premium (port ui_theme.button).
#
# Gradasi + aksen kiri + badge ikon + sudut emas + glow hover, digambar
# penuh di _draw(). Teks native Button dibuat transparan (tak terlihat)
# tetapi properti `text` tetap dipakai (tes paritas + aksesibilitas);
# tampilan teks digambar manual dengan clamp posisi ala pygame.
extends Button
class_name MysticButton

@export var accent: Color = UiTheme.GOLD:
	set(v):
		accent = v
		queue_redraw()
@export var icon_name: String = "":
	set(v):
		icon_name = v
		queue_redraw()
@export var letter_gap: bool = false:
	set(v):
		letter_gap = v
		queue_redraw()
@export var font_style: String = "body_bold"
@export var font_size: int = 20

var _hover := false
var _pressed := false
var _last_text := "~~~"


func _init(p_text: String = "", p_accent: Color = UiTheme.GOLD,
		p_icon: String = "", p_font_size: int = 20,
		p_letter_gap: bool = false) -> void:
	text = p_text
	accent = p_accent
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


func _draw() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		return
	var enabled := not disabled
	var hov := _hover and enabled
	# Glow hover (radial di belakang tombol).
	if hov:
		UiTheme.draw_glow(self, rect.get_center(),
			rect.size + Vector2(44, 36), accent, 74.0)
	# Bayangan.
	draw_style_box(UiTheme.shadow_style(12.0, 0.43), rect)
	# Panel tombol.
	var top := Color8(44, 52, 86) if hov else Color8(34, 41, 70)
	var bot := Color8(24, 29, 52) if hov else Color8(17, 21, 38)
	if _pressed and enabled:
		top = Color8(26, 32, 58)
		bot = Color8(13, 16, 30)
	if not enabled:
		top = Color8(30, 32, 44)
		bot = Color8(20, 21, 30)
	UiTheme.draw_vgrad(self, rect, top, bot, 12.0)
	# Sorot tepi atas.
	draw_line(Vector2(rect.position.x + 12, rect.position.y + 1),
		Vector2(rect.end.x - 12, rect.position.y + 1), Color(1, 1, 1, 0.35),
		1.0)
	# Aksen kiri.
	var abar := Rect2(rect.position.x + 6, rect.position.y + 10, 4,
		rect.size.y - 20)
	draw_rect(abar, accent if enabled else Color8(70, 74, 96))
	var soft := accent if enabled else Color8(70, 74, 96)
	soft.a = 0.27
	draw_rect(Rect2(rect.position.x + 4, rect.position.y + 8, 8,
		rect.size.y - 16), soft)
	# Border.
	var bcol := accent if hov else UiTheme.EDGE_GOLD
	if not enabled:
		bcol = Color8(70, 74, 96)
	draw_style_box(UiTheme.border_style(bcol, 2.0 if hov else 1.0, 12.0),
		rect)
	# Sudut emas.
	UiTheme.corner_ticks(self, rect, UiTheme.GOLD, 11.0, 2.0, 2.0)
	# Badge ikon.
	var f := UiTheme.font(font_style)
	var shown := UiTheme.letter(text) if letter_gap else text
	var label_cx := rect.get_center().x
	if icon_name != "":
		var ic := Vector2(rect.position.x + 34, rect.get_center().y)
		draw_circle(ic + Vector2(0, 1), 17.0, Color(0, 0, 0, 0.4))
		draw_circle(ic, 17.0, Color8(12, 14, 26))
		UiTheme.draw_ring(self, ic, 17.0, accent if enabled else Color8(70, 74, 96),
			2.0)
		UiTheme.draw_icon(self, icon_name, ic,
			accent if enabled else UiTheme.TEXT_FAINT, 0.9)
		# Clamp posisi label ala pygame (jangan menimpa badge/tepi).
		var tw := f.get_string_size(shown, HORIZONTAL_ALIGNMENT_LEFT, -1,
			font_size).x
		var left_min := rect.position.x + 56.0
		var right_max := rect.end.x - 10.0
		label_cx = rect.position.x + rect.size.x * 0.5 + 14.0
		if label_cx - tw * 0.5 < left_min:
			label_cx = left_min + tw * 0.5
		if label_cx + tw * 0.5 > right_max:
			label_cx = right_max - tw * 0.5
		if label_cx - tw * 0.5 < left_min:
			label_cx = (left_min + right_max) * 0.5
	# Label (putih + bayangan gelap).
	var tcol := UiTheme.TEXT_WHITE if enabled else UiTheme.TEXT_FAINT
	var bp := UiTheme.baseline_center(f, shown,
		Vector2(label_cx, rect.get_center().y), font_size)
	UiTheme.draw_text_shadow(self, f, shown, font_size, tcol, bp)
