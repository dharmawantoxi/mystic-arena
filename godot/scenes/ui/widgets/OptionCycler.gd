# OptionCycler.gd — setelan berbasis opsi (port ui_theme.option_cycler 1:1).
#
# Label kiri + kotak nilai (lebar MENGIKUTI teks: `max(110, lebar + 26)`
# dibatasi `width - 66`) + dua tombol chevron 24x30 dengan jarak 6px di
# kiri/kanan kotak. Baris setinggi 37px (pygame mengembalikan `vy + vh`
# dengan `vy = y + 7` dan `vh = 30`).
#
# Hit-test memakai rect yang dihitung `UiTheme.cycler_geom` — pola `btns`
# pygame (id -> Rect) dipertahankan: id-nya `<id_base>_prev` / `<id_base>_next`.
# extends Control (bukan container): semua digambar di _draw() supaya
# geometrinya identik dengan pygame, bukan hasil negosiasi layout Godot.
extends Control
class_name OptionCycler

## Dipancarkan setelah nilai berubah (index baru + nilainya).
signal value_changed(index: int, value: Variant)

var label_text: String = ""
var options: Array = []
## Teks tampilan per opsi; kosong -> `str(options[i])`.
var labels: Array = []
var index: int = 0
var id_base: String = "cycler"
var label_font_size: int = 20
var value_font_size: int = 20
var label_font_weight: String = "body_medium"
var value_font_weight: String = "body_semibold"

## Id tombol yang sedang disorot ("" = tidak ada) — padanan `hover` pygame.
var _hover: String = ""
## Rect hit-test hasil gambar terakhir (padanan dict `btns` pygame).
var _btns: Dictionary = {}


func _init(p_label: String = "", p_options: Array = [],
		p_index: int = 0) -> void:
	label_text = p_label
	options = p_options
	index = clampi(p_index, 0, maxi(0, p_options.size() - 1))
	mouse_filter = Control.MOUSE_FILTER_STOP
	custom_minimum_size = Vector2(340, 37)


func set_options(p_options: Array, p_labels: Array = [],
		p_index: int = 0) -> OptionCycler:
	options = p_options
	labels = p_labels
	index = clampi(p_index, 0, maxi(0, p_options.size() - 1))
	queue_redraw()
	return self


func set_index(p_index: int, emit: bool = true) -> void:
	if options.is_empty():
		return
	index = wrapi(p_index, 0, options.size())
	queue_redraw()
	if emit:
		value_changed.emit(index, options[index])


## Putar opsi — paritas handler `<id>_prev` / `<id>_next` pygame (modulo,
## membungkus dua arah).
func cycle(direction: int) -> void:
	if options.is_empty():
		return
	set_index(index + direction)


func value() -> Variant:
	if options.is_empty():
		return null
	return options[wrapi(index, 0, options.size())]


func value_text() -> String:
	if options.is_empty():
		return ""
	var i := wrapi(index, 0, options.size())
	if i < labels.size():
		return str(labels[i])
	return str(options[i])


func label_font() -> Font:
	return UiTheme.font_for_weight(label_font_weight)


func value_font() -> Font:
	return UiTheme.font_for_weight(value_font_weight)


## Rect hit-test kedua chevron (dihitung dari rumus pygame, bukan dari hasil
## gambar — jadi tetap benar sebelum frame pertama).
func hit_rects() -> Dictionary:
	var value_w := value_font().get_string_size(value_text(),
		HORIZONTAL_ALIGNMENT_LEFT, -1, value_font_size).x
	var g := UiTheme.cycler_geom(Vector2.ZERO, size.x, value_w)
	return {
		id_base + "_prev": UiTheme.pyrect(g["prev"]),
		id_base + "_next": UiTheme.pyrect(g["next"]),
		"box": UiTheme.pyrect(g["box"]),
	}


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _draw() -> void:
	if size.x <= 0.0:
		return
	_btns = {}
	UiTheme.draw_option_cycler(self, _btns, id_base, label_text, value_text(),
		Vector2.ZERO, size.x, label_font(), label_font_size, value_font(),
		value_font_size, _hover)


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		var pos := (event as InputEventMouseMotion).position
		var hits := hit_rects()
		var found := ""
		for key in hits:
			if (hits[key] as Rect2).has_point(pos):
				found = str(key)
		if found != _hover:
			_hover = found
			queue_redraw()
		return
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index != MOUSE_BUTTON_LEFT or not mb.pressed:
			return
		var hits := hit_rects()
		for key in hits:
			if (hits[key] as Rect2).has_point(mb.position):
				AudioManager.play_sfx("ui_click", 0.5)
				cycle(-1 if str(key).ends_with("_prev") else 1)
				return


## Pintasan tes/harness: klik chevron tanpa event mouse.
func press(side: String) -> void:
	AudioManager.play_sfx("ui_click", 0.5)
	cycle(-1 if side == "prev" else 1)
