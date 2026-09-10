# ScreenTitle.gd — judul layar seragam (port ui_theme.screen_title 1:1).
#
# Cinzel 64 gradasi-pendekatan (GOLD_BRIGHT + outline gelap) + glow radial.
# Ornamen garis-wajik-garis TIDAK di sini (pakai Flourish terpisah —
# sebagian layar pygame memakai ornament=False).
extends Control
class_name ScreenTitle

var text: String = ""
var font_size: int = 64
var glow: bool = true
## Bob vertikal halus (khusus judul MAIN MENU pygame: ±3px).
var bob: bool = false

var _t: float = 0.0


func _init(p_text: String = "", p_size: int = 64, p_glow: bool = true,
		p_bob: bool = false) -> void:
	text = p_text
	font_size = p_size
	glow = p_glow
	bob = p_bob
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Tinggi minimum hemat (teks + sedikit napas); glow menggambar di luar
	# rect (clip_contents=false) jadi tidak butuh ruang layout.
	custom_minimum_size = Vector2(0, font_size + 20)
	if bob:
		set_process(true)
	else:
		set_process(false)


func _process(delta: float) -> void:
	_t += delta
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _draw() -> void:
	var cx := size.x * 0.5
	var cy := size.y * 0.5
	if bob:
		cy += sin(_t * 1.2) * 3.0
	var font := UiTheme.title_font()
	if glow:
		var ga := 46.0 / 255.0
		if bob:
			ga = (40.0 + 20.0 * sin(_t * 1.2)) / 255.0
		UiTheme.draw_glow(self,
			Rect2(cx - 310, cy - 62, 620, 150),
			Color(1.0, 205.0 / 255.0, 90.0 / 255.0), ga)
	UiTheme.draw_outline_text(self, font, text, font_size, Vector2(cx, cy))
