# GradientText.gd — teks gradasi vertikal (port ui_theme.gradient_text).
#
# pygame merender glif putih lalu mengalikannya (BLEND_RGBA_MULT) dengan
# permukaan gradasi per baris piksel, dan meng-cache hasilnya per
# (font, teks, warna). Godot tidak bisa masking gradasi ke glif dari dalam
# satu `_draw()` (tidak ada clip/scissor di CanvasItem), jadi gradasinya
# dibangun dari PITA (band) yang di-clip: setiap pita adalah Control dengan
# `clip_contents = true` berisi satu Control yang menggambar teks penuh
# dengan warna pita itu. Warna pita berasal dari rumus gradasi pygame
# (`UiTheme.gradient_bands`), jadi hasilnya sama secara visual dan cache-nya
# (node) dibangun sekali per teks — padanan `_GRAD_TEXT_CACHE`.
#
# Dipakai `ScreenTitle` untuk badan judul Cinzel (GOLD_BRIGHT -> (196,138,40))
# dan tersedia untuk teks gradasi lain (mis. judul DEFEAT merah).
extends Control
class_name GradientText

var text: String = ""
var font: Font = null
var font_size: int = 64
var top_color: Color = UiTheme.GOLD_BRIGHT
var bottom_color: Color = Color(196.0 / 255.0, 138.0 / 255.0, 40.0 / 255.0)
## Jumlah pita gradasi (12 pita di judul 64px = langkah ~5px, tak terlihat).
var bands: int = 12
## Outline gelap opsional (digambar lebih dulu oleh Control ini, jadi pita
## gradasi selalu di atasnya — urutan blit pygame `outline_text`).
var outline: bool = false
var outline_color: Color = UiTheme.OUTLINE_DARK
var outline_size: int = 2
var align: int = HORIZONTAL_ALIGNMENT_CENTER

var _band_nodes: Array = []
var _built_key: String = ""


## Node gambar satu pita (anak dari Control ber-clip_contents).
class BandText extends Control:

	var band_text: String = ""
	var band_font: Font = null
	var band_size: int = 16
	var band_color: Color = Color.WHITE
	var baseline: float = 0.0
	var band_align: int = HORIZONTAL_ALIGNMENT_CENTER

	func _draw() -> void:
		if band_font == null or band_text.is_empty():
			return
		draw_string(band_font, Vector2(0, baseline), band_text, band_align,
			size.x, band_size, band_color)


func _init(p_text: String = "", p_size: int = 64, p_font: Font = null) -> void:
	text = p_text
	font_size = p_size
	font = p_font
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func set_text(p_text: String) -> GradientText:
	text = p_text
	_rebuild()
	queue_redraw()
	return self


func set_gradient(p_top: Color, p_bottom: Color, p_bands: int = 12) -> GradientText:
	top_color = p_top
	bottom_color = p_bottom
	bands = maxi(1, p_bands)
	_rebuild()
	queue_redraw()
	return self


func used_font() -> Font:
	if font != null:
		return font
	return UiTheme.title_font()


## Baseline teks di koordinat Control ini (pusat vertikal, seperti
## `UiTheme.draw_text_centered`).
func baseline() -> float:
	var f := used_font()
	var th := f.get_height(font_size)
	return (size.y - th) * 0.5 + f.get_ascent(font_size)


func _ready() -> void:
	_rebuild()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		_rebuild()
		queue_redraw()


func _draw() -> void:
	if outline and not text.is_empty():
		draw_string_outline(used_font(), Vector2(0, baseline()), text, align,
			size.x, font_size, outline_size, outline_color)


## Bangun ulang pita (hanya kalau kunci ukuran/teks/warna berubah — node
## tidak dibuang tiap frame).
func _rebuild() -> void:
	var key := "%s|%d|%d|%f|%f|%s|%s" % [text, font_size, bands, size.x,
		size.y, top_color.to_html(false), bottom_color.to_html(false)]
	if key == _built_key:
		return
	_built_key = key
	for node in _band_nodes:
		(node as Node).queue_free()
	_band_nodes.clear()
	if text.is_empty() or size.y <= 0.0 or size.x <= 0.0:
		return
	var colors := UiTheme.gradient_bands(top_color, bottom_color, bands)
	var n := colors.size()
	var base := baseline()
	for i in range(n):
		var y0 := floorf(size.y * float(i) / float(n))
		var y1 := floorf(size.y * float(i + 1) / float(n))
		if i == n - 1:
			y1 = size.y
		if y1 <= y0:
			continue
		var clip := Control.new()
		clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		clip.clip_contents = true
		clip.position = Vector2(0, y0)
		clip.size = Vector2(size.x, y1 - y0)
		var body := BandText.new()
		body.mouse_filter = Control.MOUSE_FILTER_IGNORE
		body.band_text = text
		body.band_font = used_font()
		body.band_size = font_size
		body.band_color = colors[i]
		body.band_align = align
		body.baseline = base
		body.position = Vector2(0, -y0)
		body.size = Vector2(size.x, size.y)
		clip.add_child(body)
		add_child(clip)
		_band_nodes.append(clip)
