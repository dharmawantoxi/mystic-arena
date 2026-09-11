# ScreenTitle.gd — judul layar seragam (port ui_theme.screen_title 1:1).
#
# Cinzel 64 + glow radial 620x150 (alpha 46) + outline gelap + badan gradasi
# emas GOLD_BRIGHT -> (196,138,40). Badan gradasi digambar `GradientText`
# (port `gradient_text` pygame: gradasi per baris piksel di-mask ke glif) —
# sebelumnya didekati warna terang solid.
#
# Ornamen "garis - wajik - garis" (pygame `ornament=True`) dan plate subtitle
# (pygame `sub=`) tersedia tapi MATI secara bawaan: layar menu Godot memasang
# Flourish/plate sendiri sebagai node terpisah, jadi menyalakannya di sini
# akan menggandakan ornamen.
extends Control
class_name ScreenTitle

var text: String = ""
var font_size: int = 64
var glow: bool = true
## Bob vertikal halus (khusus judul MAIN MENU pygame: ±3px).
var bob: bool = false
## Subtitle plate (pygame `sub=`) — Barlow-SemiBold 30 letter-spaced.
var sub_text: String = ""
var sub_color: Color = UiTheme.CYAN_SOFT
## Ornamen garis-wajik-garis di y+52 (pygame `ornament=True`).
var ornament: bool = false
## Badan judul gradasi; false = solid GOLD_BRIGHT (perilaku port lama).
var gradient_body: bool = true
var body_top: Color = UiTheme.GOLD_BRIGHT
var body_bottom: Color = Color(196.0 / 255.0, 138.0 / 255.0, 40.0 / 255.0)

var _t: float = 0.0
var _grad: GradientText = null


func _init(p_text: String = "", p_size: int = 64, p_glow: bool = true,
		p_bob: bool = false, p_sub: String = "",
		p_sub_color: Color = UiTheme.CYAN_SOFT, p_ornament: bool = false,
		p_gradient: bool = true) -> void:
	text = p_text
	font_size = p_size
	glow = p_glow
	bob = p_bob
	sub_text = p_sub
	sub_color = p_sub_color
	ornament = p_ornament
	gradient_body = p_gradient
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_update_min_size()
	if gradient_body:
		_ensure_gradient()
	if bob:
		set_process(true)
	else:
		set_process(false)


## Ganti judul (dipakai layar yang membangun ulang teks, mis. VICTORY/DEFEAT).
func set_title(p_text: String, p_sub: String = "") -> ScreenTitle:
	text = p_text
	sub_text = p_sub
	_update_min_size()
	if _grad != null:
		_grad.set_text(p_text)
	queue_redraw()
	return self


func _update_min_size() -> void:
	# Tinggi minimum hemat (teks + sedikit napas); glow menggambar di luar
	# rect (clip_contents=false) jadi tidak butuh ruang layout. Ornamen dan
	# plate subtitle butuh ruang di bawah pusat judul (y+52 / y+64..y+108).
	var h := float(font_size) + 20.0
	var below := h * 0.5
	if ornament:
		below = maxf(below, 62.0)
	if not sub_text.is_empty():
		below = maxf(below, 108.0)
	custom_minimum_size = Vector2(0, maxf(h, below * 2.0))


func _ensure_gradient() -> void:
	if _grad != null:
		return
	_grad = GradientText.new(text, font_size, UiTheme.title_font())
	_grad.set_gradient(body_top, body_bottom, 12)
	_grad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_grad)
	_sync_gradient()


func _sync_gradient() -> void:
	if _grad == null:
		return
	_grad.position = Vector2(0, _bob_offset())
	_grad.size = Vector2(size.x, size.y)


func _bob_offset() -> float:
	return sin(_t * 1.2) * 3.0 if bob else 0.0


func _process(delta: float) -> void:
	_t += delta
	_sync_gradient()
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		_sync_gradient()
		queue_redraw()


func _draw() -> void:
	var cx := size.x * 0.5
	var cy := size.y * 0.5 + _bob_offset()
	var font := UiTheme.title_font()
	if glow:
		var ga := 46.0 / 255.0
		if bob:
			ga = (40.0 + 20.0 * sin(_t * 1.2)) / 255.0
		UiTheme.draw_glow(self, Rect2(cx - 310, cy - 62, 620, 150),
			Color(1.0, 205.0 / 255.0, 90.0 / 255.0), ga)
	if gradient_body:
		# Hanya outline di sini; badan gradasi digambar anak GradientText
		# (anak digambar SETELAH induk, jadi gradasi selalu di atas outline —
		# urutan blit yang sama dengan ui_theme.outline_text).
		draw_string_outline(font, Vector2(0, _baseline(cy)), text,
			HORIZONTAL_ALIGNMENT_CENTER, size.x, font_size, 2,
			UiTheme.OUTLINE_DARK)
	else:
		UiTheme.draw_outline_text(self, font, text, font_size, Vector2(cx, cy))
	if ornament or not sub_text.is_empty():
		var sub_w := 0.0
		if not sub_text.is_empty():
			sub_w = UiTheme.body_semibold().get_string_size(
				UiTheme.letter(sub_text), HORIZONTAL_ALIGNMENT_LEFT, -1,
				30).x
		var g := UiTheme.screen_title_geom(cx, cy, sub_w)
		if ornament:
			UiTheme.draw_title_ornament(self, g)
		if not sub_text.is_empty():
			UiTheme.draw_title_sub(self, g, sub_text, sub_color, 30)


## Baseline teks (rumus yang sama dengan UiTheme.draw_outline_text).
func _baseline(cy: float) -> float:
	var font := UiTheme.title_font()
	return cy + (font.get_ascent(font_size) - font.get_descent(font_size)) * 0.5
