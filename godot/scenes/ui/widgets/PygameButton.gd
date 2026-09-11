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
# Ketiga mode di bawah HANYA meneruskan ke UiTheme.draw_*_visual (satu sumber
# geometri/warna dengan jalur immediate-mode ui_theme.py yang dikunci oracle
# tools/test_godot_ui_theme_parity.py).
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
var _hover: bool = false


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
	mouse_entered.connect(_set_hover.bind(true))
	mouse_exited.connect(_set_hover.bind(false))
	button_down.connect(queue_redraw)
	button_up.connect(queue_redraw)
	pressed.connect(_on_pressed_sfx)


func _set_hover(v: bool) -> void:
	_hover = v
	queue_redraw()


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


# ── MODE MENU (port ui_theme.button) ──────────────────────────
#
# Visualnya SATU sumber dengan jalur immediate-mode: UiTheme.draw_button_visual
# (dipakai juga oleh tes paritas). Deviasi yang dipertahankan dari port lama:
# hover TIDAK melebarkan rect (layout container Godot tidak boleh bergeser),
# jadi `rect` dan `base` sama — tampilan idle 100% sama, hover 99% sama.

func _draw_menu_mode() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	UiTheme.draw_button_visual(self, rect, rect, label_text, accent, _font(),
		font_size, icon_name, _hover and not disabled, use_letter_spacing,
		is_pressed(), not disabled, icon_scale)


# ── MODE PILL (port ui_theme.pill) ───────────────────────────

func _draw_pill_mode() -> void:
	UiTheme.draw_pill_visual(self, Rect2(Vector2.ZERO, size), pill_kind,
		_font(), font_size, label_text, _hover and not disabled,
		not disabled, icon_name, use_letter_spacing, is_pressed(), icon_scale)


# ── MODE TAB (port ui_theme.tab) ─────────────────────────────

func _draw_tab_mode() -> void:
	UiTheme.draw_tab_visual(self, Rect2(Vector2.ZERO, size), label_text,
		accent, _font(), font_size, button_pressed, _hover and not disabled)


## Konstruktor cepat tombol BACK (port ui_theme.back_button: 200x42, pill
## netral, ikon panah, Barlow-SemiBold 26, label letter-spaced).
static func back_button(p_label: String = "BACK", w: float = 200.0,
		h: float = 42.0, p_font_size: int = 26) -> PygameButton:
	var b := PygameButton.new(p_label, UiTheme.SLATE, Mode.PILL)
	b.pill_kind = "neutral"
	b.icon_name = "back"
	b.font_size = p_font_size
	b.font_weight = "body_semibold"
	b.use_letter_spacing = true
	b.icon_scale = 0.8
	b.custom_minimum_size = Vector2(w, h)
	return b
