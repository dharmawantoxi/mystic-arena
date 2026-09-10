# PygameButton.gd — tombol premium port ui_theme.button/pill/tab 1:1.
#
# Tiga mode dalam satu kelas (dipilih via `mode`):
#   MENU — tombol menu utama: gradasi, aksen kiri, badge ikon lingkaran,
#          sudut emas, glow hover (ui_theme.button).
#   PILL — tombol aksi kecil: gold/success/danger/locked/owned/neutral/
#          violet/cyan (ui_theme.pill).
#   TAB  — tab kategori dengan underline aksen saat aktif (ui_theme.tab).
#
# Hover di pygame melebarkan rect (+18/+8); di Godot layout container tidak
# boleh bergeser, jadi rect tetap dan hanya glow + border + gradasi yang
# berubah — tampilan idle 100% sama, hover 99% sama (tanpa inflate).
#
# extends Button (BUKAN BaseButton): audit closed-world UiHudParityTest
# menemukan tombol lewat `c is Button` (ShopPanel.collect_ui_keys) dan
# `var b: Button = panel.find_child(...)` (geometri pause). Style theme
# native dikosongkan total; SEMUA visual digambar di _draw().
extends Button
class_name PygameButton

enum Mode { MENU, PILL, TAB }

var mode: int = Mode.MENU
var label_text: String = ""
var accent: Color = UiTheme.GOLD
var icon_name: String = ""
var pill_kind: String = "gold"
var font_size: int = 20
var font_weight: String = "body_bold"
var use_letter_spacing: bool = false
var icon_scale: float = 0.9


func _init(p_label: String = "", p_accent: Color = UiTheme.GOLD,
		p_mode: int = Mode.MENU) -> void:
	label_text = p_label
	accent = p_accent
	mode = p_mode
	focus_mode = Control.FOCUS_NONE
	mouse_filter = Control.MOUSE_FILTER_STOP
	# Button native tidak menggambar apa pun (teks/style dikosongkan);
	# visual murni dari _draw() di bawah.
	text = ""
	var _empty := StyleBoxEmpty.new()
	add_theme_stylebox_override("normal", _empty)
	add_theme_stylebox_override("hover", _empty)
	add_theme_stylebox_override("pressed", _empty)
	add_theme_stylebox_override("disabled", _empty)
	add_theme_stylebox_override("focus", _empty)
	mouse_entered.connect(queue_redraw)
	mouse_exited.connect(queue_redraw)
	button_down.connect(queue_redraw)
	button_up.connect(queue_redraw)
	pressed.connect(_on_pressed_sfx)


func _on_pressed_sfx() -> void:
	AudioManager.play_sfx("ui_click", 0.5)


## Konstruktor cepat tombol MENU (w/h = ukuran minimum).
static func menu_button(p_label: String, p_accent: Color,
		p_icon: String = "", w: float = 300.0, h: float = 50.0,
		p_font_size: int = 20) -> PygameButton:
	var b := PygameButton.new(p_label, p_accent, Mode.MENU)
	b.icon_name = p_icon
	b.font_size = p_font_size
	b.custom_minimum_size = Vector2(w, h)
	return b


## Konstruktor cepat tombol PILL.
static func pill_button(p_label: String, p_kind: String,
		p_icon: String = "", w: float = 0.0, h: float = 32.0,
		p_font_size: int = 16) -> PygameButton:
	var b := PygameButton.new(p_label, UiTheme.GOLD, Mode.PILL)
	b.pill_kind = p_kind
	b.icon_name = p_icon
	b.font_size = p_font_size
	b.icon_scale = 0.8
	if w > 0.0:
		b.custom_minimum_size = Vector2(w, h)
	else:
		b.custom_minimum_size = Vector2(0, h)
	return b


## Konstruktor cepat tombol TAB (toggle).
static func tab_button(p_label: String, p_accent: Color,
		w: float = 150.0, h: float = 34.0,
		p_font_size: int = 16) -> PygameButton:
	var b := PygameButton.new(p_label, p_accent, Mode.TAB)
	b.font_size = p_font_size
	b.use_letter_spacing = true
	b.toggle_mode = true
	b.custom_minimum_size = Vector2(w, h)
	return b


func set_label(t: String) -> PygameButton:
	label_text = t
	queue_redraw()
	return self


func _draw() -> void:
	match mode:
		Mode.MENU:
			_draw_menu_mode()
		Mode.PILL:
			_draw_pill_mode()
		Mode.TAB:
			_draw_tab_mode()
	if disabled:
		# Lapisan redup merata untuk disabled (di atas segalanya).
		UiTheme.draw_rr(self, Rect2(Vector2.ZERO, size),
			Color(0.02, 0.02, 0.04, 0.55), 8.0)


func _font() -> Font:
	return UiTheme.font_for_weight(font_weight)


func _label() -> String:
	if use_letter_spacing:
		return UiTheme.letter(label_text)
	return label_text


func _text_color_menu() -> Color:
	return UiTheme.TEXT_WHITE


# ── MODE MENU (port ui_theme.button) ──────────────────────────

func _draw_menu_mode() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	var hover := is_hovered() and not disabled
	var pressed_down := is_pressed()
	# Glow hover (radial di belakang tombol).
	if hover:
		UiTheme.draw_glow(self, rect.grow(Vector2(22, 18)), accent,
			74.0 / 255.0)
	# Bayangan.
	UiTheme.draw_shadow(self, rect, 12.0)
	# Panel tombol (gradasi lebih terang saat hover).
	var top := Color("#2c3456") if hover else Color("#222946")
	var bot := Color("#181d34") if hover else Color("#111526")
	if pressed_down:
		top = top.darkened(0.12)
		bot = bot.darkened(0.12)
	UiTheme.draw_vgrad(self, rect, top, bot, 12.0)
	# Sorot tepi atas.
	draw_line(Vector2(rect.position.x + 12, rect.position.y + 1),
		Vector2(rect.end.x - 12, rect.position.y + 1), Color.WHITE, 1.0)
	# Aksen kiri (4px) + glow lembutnya.
	var accent_rect := Rect2(rect.position.x + 6, rect.position.y + 10,
		4, rect.size.y - 20)
	UiTheme.draw_rr(self, accent_rect, accent, 2.0)
	UiTheme.draw_rr(self,
		Rect2(rect.position.x + 4, rect.position.y + 8, 8,
			rect.size.y - 16),
		Color(accent.r, accent.g, accent.b, 70.0 / 255.0), 3.0)
	# Border (aksen saat hover, emas redup saat idle).
	var bcol := accent if hover else UiTheme.EDGE_GOLD
	UiTheme.draw_rr_outline(self, rect, bcol, 12.0, 2.0 if hover else 1.0)
	# Sudut emas.
	UiTheme.draw_corner_ticks(self, rect, UiTheme.GOLD)
	# Badge ikon lingkaran.
	var has_icon := not icon_name.is_empty()
	if has_icon:
		var ic := Vector2(rect.position.x + 34, rect.get_center().y)
		draw_circle(ic + Vector2(0, 0), 17.0, Color("#0c0e1a"))
		draw_arc(ic, 17.0, 0, TAU, 40, accent, 2.0)
		UiTheme.draw_icon(self, icon_name, ic.x, ic.y, accent, icon_scale)
	# Label (clamp: jangan menimpa badge / keluar tepi kanan).
	var font := _font()
	var text := _label()
	var tw := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1,
		font_size).x
	var text_cx := rect.get_center().x
	if has_icon:
		var left_min := rect.position.x + 56.0
		var right_max := rect.end.x - 10.0
		text_cx = rect.position.x + rect.size.x * 0.5 + 14.0
		if text_cx - tw * 0.5 < left_min:
			text_cx = left_min + tw * 0.5
		if text_cx + tw * 0.5 > right_max:
			text_cx = right_max - tw * 0.5
		if text_cx - tw * 0.5 < left_min:
			text_cx = (left_min + right_max) * 0.5
	var tcol := _text_color_menu() if not disabled else UiTheme.TEXT_FAINT
	UiTheme.draw_text_centered(self, font, text, font_size, tcol,
		Vector2(text_cx, rect.get_center().y), true)


# ── MODE PILL (port ui_theme.pill) ───────────────────────────

func _draw_pill_mode() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	var hover := is_hovered() and not disabled
	var cols: Array = UiTheme.pill_colors(pill_kind)
	var top: Color = cols[0]
	var bot: Color = cols[1]
	var edge: Color = cols[2]
	var tcol: Color = cols[3]
	if hover:
		top = Color(minf(1.0, top.r + 18.0 / 255.0),
			minf(1.0, top.g + 18.0 / 255.0),
			minf(1.0, top.b + 18.0 / 255.0))
		bot = Color(minf(1.0, bot.r + 14.0 / 255.0),
			minf(1.0, bot.g + 14.0 / 255.0),
			minf(1.0, bot.b + 14.0 / 255.0))
		UiTheme.draw_glow(self, rect.grow(Vector2(15, 12)), edge,
			66.0 / 255.0)
	if is_pressed():
		top = top.darkened(0.12)
		bot = bot.darkened(0.12)
	UiTheme.draw_vgrad(self, rect, top, bot, 7.0)
	UiTheme.draw_rr_outline(self, rect, edge, 7.0,
		2.0 if not disabled else 1.0)
	var font := _font()
	var text := _label()
	var cx := rect.get_center().x
	if not icon_name.is_empty():
		UiTheme.draw_icon(self, icon_name, rect.position.x + 22,
			rect.get_center().y, edge, icon_scale)
		cx = rect.position.x + 22.0 + (rect.size.x - 22.0) * 0.5
	var final_col := tcol if not disabled else UiTheme.TEXT_FAINT
	UiTheme.draw_text_centered(self, font, text, font_size, final_col,
		Vector2(cx, rect.get_center().y), true)


# ── MODE TAB (port ui_theme.tab) ─────────────────────────────

func _draw_tab_mode() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	var active := button_pressed
	var hover := is_hovered() and not disabled
	var font := _font()
	var text := _label()
	var tcol := accent
	if active:
		UiTheme.draw_vgrad(self, rect, Color("#2e385c"), Color("#1a203a"),
			8.0)
		UiTheme.draw_rr_outline(self, rect, accent, 8.0, 2.0)
		# Underline aksen 3px.
		UiTheme.draw_rr(self,
			Rect2(rect.position.x + 8, rect.end.y - 4, rect.size.x - 16,
				3), accent, 1.0)
		tcol = accent
	else:
		var top := Color("#22273e") if hover else Color("#161a2c")
		var bot := Color("#14182a") if hover else Color("#0f1220")
		UiTheme.draw_vgrad(self, rect, top, bot, 8.0)
		var edge := Color("#7882a0") if hover else Color("#48506a")
		UiTheme.draw_rr_outline(self, rect, edge, 8.0, 1.0)
		tcol = UiTheme.TEXT_BODY if hover else UiTheme.TEXT_DIM
	UiTheme.draw_text_centered(self, font, text, font_size, tcol,
		rect.get_center(), false)
