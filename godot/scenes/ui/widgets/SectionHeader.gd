# SectionHeader.gd — header section (port ui_theme.section_header 1:1).
#
# Ikon vektor s=0.9 di (10, 11) + judul letter-spaced di (28, 0) + garis
# hairline aksen sepanjang `rule_w` di y+14 + garis redup `_dim(color)` di
# y+26 di bawah judul. Tinggi baris 34px (pygame mengembalikan y + 34).
#
# extends Control: semua digambar di _draw() lewat UiTheme supaya geometri
# punya SATU sumber dengan jalur immediate-mode.
extends Control
class_name SectionHeader

var title: String = ""
var icon_name: String = "gear"
var color: Color = UiTheme.CYAN
var font_size: int = 22
var font_weight: String = "body_semibold"
var rule_w: float = 240.0


func _init(p_title: String = "", p_icon: String = "gear",
		p_color: Color = UiTheme.CYAN, p_rule_w: float = 240.0) -> void:
	title = p_title
	icon_name = p_icon
	color = p_color
	rule_w = p_rule_w
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_refresh_min_size()


func set_header(p_title: String, p_icon: String, p_color: Color,
		p_rule_w: float = -1.0) -> SectionHeader:
	title = p_title
	icon_name = p_icon
	color = p_color
	if p_rule_w >= 0.0:
		rule_w = p_rule_w
	_refresh_min_size()
	queue_redraw()
	return self


func _font() -> Font:
	return UiTheme.font_for_weight(font_weight)


func _refresh_min_size() -> void:
	var s := UiTheme.section_header_size(title, _font(), font_size, rule_w)
	custom_minimum_size = Vector2(0, s.y)


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _draw() -> void:
	UiTheme.draw_section_header(self, Vector2.ZERO, title, icon_name, color,
		_font(), font_size, rule_w)
