# PygameChip.gd — chip status auto-size (port ui_theme.chip 1:1).
#
# Ikon + label letter-spaced + nilai opsional; tinggi 30px, gradasi
# (32,38,64)->(18,22,40), border aksen 1px, radius = h/2. LEBAR MENGIKUTI
# TEKS (rumus `UiTheme.chip_rect`), jadi label bahasa panjang tidak
# terpotong — perilaku yang sama dengan perbaikan auto-size pygame.
#
# extends Control (BUKAN PanelContainer): audit kartu menu di
# SaveSlot/LevelSelect/MetaShopParityTest menyapu semua PanelContainer di
# bawah `_root`, jadi chip tidak boleh ikut terhitung sebagai kartu.
extends Control
class_name PygameChip

var label_text: String = ""
## Kosong = chip tanpa nilai (pygame `value=None`).
var value_text: String = ""
var accent: Color = UiTheme.GOLD
var icon_name: String = ""
## Warna ikon/nilai opsional; kalau `use_*_color` false, ikut `accent`
## (pygame `icon_color or accent` / `value_color or accent`).
var icon_color: Color = UiTheme.GOLD
var use_icon_color: bool = false
var value_color: Color = UiTheme.GOLD
var use_value_color: bool = false
var font_size: int = 18
var font_weight: String = "body_semibold"
## pygame `align="right"`: `pos` adalah sudut KANAN-atas chip.
var align_right: bool = false


func _init(p_label: String = "", p_value: String = "",
		p_accent: Color = UiTheme.GOLD, p_icon: String = "") -> void:
	label_text = p_label
	value_text = p_value
	accent = p_accent
	icon_name = p_icon
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_refresh_min_size()


## Ganti isi chip (dipanggil saat gold/jumlah berubah).
func set_chip(p_label: String, p_value: String = "",
		p_accent: Color = UiTheme.GOLD, p_icon: String = "") -> PygameChip:
	label_text = p_label
	value_text = p_value
	accent = p_accent
	icon_name = p_icon
	_refresh_min_size()
	queue_redraw()
	return self


func set_value(p_value: String, p_color = null) -> PygameChip:
	value_text = p_value
	if p_color != null:
		value_color = Color(p_color)
		use_value_color = true
	_refresh_min_size()
	queue_redraw()
	return self


func _font() -> Font:
	return UiTheme.font_for_weight(font_weight)


func _refresh_min_size() -> void:
	custom_minimum_size = UiTheme.chip_size(label_text, _font(), font_size,
		icon_name, value_text)


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _draw() -> void:
	var pos := Vector2(size.x, 0) if align_right else Vector2.ZERO
	UiTheme.draw_chip(self, pos, label_text, accent, _font(), font_size,
		icon_name, icon_color if use_icon_color else null,
		value_text if not value_text.is_empty() else null,
		value_color if use_value_color else null,
		"right" if align_right else "left")
